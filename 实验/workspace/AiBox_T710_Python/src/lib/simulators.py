#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Helper simulators for running the panel app on a laptop without hardware.

Usage: set environment variable PANEL_SIM=1 before running `src/panel.py`

This module monkeypatches `lib.uart.Uart` with `FakeUart` and `cv2.VideoCapture`
with `FakeCamera` when `enable_simulation()` is called.
"""
import os
import threading
import time
import random
import glob
import cv2
import numpy as np


class _Sensors:
    def __init__(self):
        # initialize common sensor fields used by panel
        self.errorCode = 0
        self.heartRate = 72
        self.sop2 = 98
        class Btn: pass
        self.btn = Btn()
        self.btn.btnPressA = False
        self.btn.btnPressB = False
        self.btn.btnPressC = False
        self.adcInfra = 200
        self.rangeLaser = 100
        self.humi = 40.0
        self.temp = 24.5
        class IMU: pass
        self.imu = IMU()
        self.imu.pitch = 0
        self.imu.roll = 0
        self.imu.yaw = 0
        self.imu.accx = 0
        self.imu.accy = 0
        self.imu.accz = 0
        self.imu.gyrox = 0
        self.imu.gyroy = 0
        self.co2 = 400
        self.tvoc = 10
        class Ges: pass
        self.ges = Ges()
        self.ges.gesture = -1
        self.ges.gesBrightness = 100
        self.ges.gesAreaDet = 0
        self.illume = 300
        self.adcMic = 0
        self.rangeRadar = 0
        self.keyCount = 0
        class Knob: pass
        self.knob = Knob()
        self.knob.count = 0
        self.knob.btnPress = False
        self.transSpeed = 0.0


class FakeUart:
    """A minimal UART-like object that provides `sensors` and `connect`.
    It periodically updates sensor values in background thread so panel UI can show changing values.
    The class provides a small subset of the real Uart API used by `panel.py` so it can be
    substituted transparently in simulation mode.
    """
    def __init__(self, port=None, baudRate=115200):
        self.port = port
        self.baudRate = baudRate
        self.connect = True
        self.sensors = _Sensors()
        self.running = True
        # provide a minimal RobotArm placeholder with Movement constants used by panel
        class _Move:
            photoTrans = 1
        class _RobotArm:
            Movement = _Move()
        self.robotArm = _RobotArm()

        self._thread = threading.Thread(target=self._update_loop, daemon=True)
        self._thread.start()

    def _update_loop(self):
        while self.running:
            # random small variations
            self.sensors.heartRate = max(40, min(120, int(self.sensors.heartRate + random.randint(-2, 2))))
            self.sensors.sop2 = max(90, min(100, int(self.sensors.sop2 + random.randint(-1, 1))))
            self.sensors.temp = round(self.sensors.temp + random.uniform(-0.1, 0.1), 1)
            self.sensors.humi = round(self.sensors.humi + random.uniform(-0.3, 0.3), 1)
            self.sensors.adcInfra = (self.sensors.adcInfra + random.randint(-5, 5)) % 1024
            self.sensors.rangeLaser = max(0, self.sensors.rangeLaser + random.randint(-2, 2))
            self.sensors.co2 = max(300, self.sensors.co2 + random.randint(-5, 5))
            self.sensors.tvoc = max(0, self.sensors.tvoc + random.randint(-1, 1))
            self.sensors.ges.gesture = random.choice([-1, -1, -1, 1, 2, 3, 4])
            self.sensors.ges.gesBrightness = random.randint(0, 255)
            self.sensors.ges.gesAreaDet = random.randint(0, 100)
            time.sleep(0.5)

    # Compatibility shim: panel calls start()/stop(), robotArmMoveit(), transmitSysHeart(), comStatusCheck(), etc.
    def start(self):
        # already running by default; keep for API compatibility
        self.running = True

    def stop(self, signum=None, frame=None):
        # act as a signal handler compatible stop
        self.running = False
        # attempt to join the background thread if it's alive
        try:
            if hasattr(self, '_thread') and self._thread.is_alive():
                self._thread.join(timeout=1.0)
        except Exception:
            pass

    def robotArmMoveit(self, *args, **kwargs):
        return True

    def transmitSysHeart(self):
        return True

    def comStatusCheck(self):
        return True

    def setTransSpeed(self, speed):
        return True

    def setRelaySwitch(self, a, b, c):
        return True

    def transmitFrame(self, addr, data):
        # mimic a transmission ack
        # panel may call this; we keep it no-op
        return True

    def close(self):
        self.running = False


class FakeCamera:
    """A simple VideoCapture replacement that cycles through images in res/images/sample or uses a blank frame.
    """
    def __init__(self, source=0):
        self.files = []
        sample_dir = os.path.join(os.path.abspath(os.path.join(__file__, '..', '..')), 'res', 'images', 'panel')
        # look for common sample directories
        for pattern in [os.path.join(sample_dir, '*.png'), os.path.join(sample_dir, '*.jpg')]:
            self.files.extend(glob.glob(pattern))
        self.idx = 0
        self.width = 640
        self.height = 480

    def read(self):
        if self.files:
            path = self.files[self.idx % len(self.files)]
            img = cv2.imread(path)
            if img is None:
                frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            else:
                frame = cv2.resize(img, (self.width, self.height))
            self.idx += 1
            return True, frame
        else:
            # blank frame
            frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
            cv2.putText(frame, 'SIM CAMERA', (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 2, (255,255,255), 3)
            return True, frame

    def isOpened(self):
        return True

    def set(self, prop, value):
        # Accept common OpenCV VideoCapture property changes (frame size / fps)
        try:
            # OpenCV uses integer property IDs; we match known ones for better behavior
            if prop == cv2.CAP_PROP_FRAME_WIDTH:
                self.width = int(value)
            elif prop == cv2.CAP_PROP_FRAME_HEIGHT:
                self.height = int(value)
            elif prop == cv2.CAP_PROP_FPS:
                self.fps = value
        except Exception:
            pass
        return True

    def release(self):
        return


def enable_simulation():
    """Apply monkeypatches so the rest of the app uses simulated devices.
    Call this early (before `Uart()` instances are created or `cv2.VideoCapture` used).
    """
    # monkeypatch lib.uart.Uart
    try:
        import importlib
        uart_mod = importlib.import_module('lib.uart')
        uart_mod.Uart = FakeUart
    except Exception:
        # silently ignore if lib.uart cannot be imported
        pass

    # monkeypatch cv2.VideoCapture
    try:
        cv2.VideoCapture = lambda src=0: FakeCamera(src)
    except Exception:
        pass


if __name__ == '__main__':
    print('simulators module loaded. call enable_simulation() to activate.')
