#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@file       : panel.py
@Description: 串口通信数据面板（整合人脸关键点检测）
@Date       : 2023/07/11 15:40:53
@Autor      : Hjc
@Version    : v1.0
"""
import threading
import serial
import struct
import os
import random
import time
import pygame
import keyboard
# --- uart 内联结束 ---
import cv2
import time
from datetime import datetime
from ai.objectDetection import *
import os
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import signal
# 新增：导入人脸关键点检测类
from faceLandmark import FaceKeyPoint
# 使用库中的 uart 实现（避免与文件内联的 Uart 类混淆）

# --- 从 lib/speech.py 整合过来的依赖与类 ---
import pyaudio
import wave
import keyboard
import os
# 基准路径（项目根目录）
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
import random
import pygame
from pygame.locals import *
from urllib.request import urlopen, Request
from urllib.error import URLError
from urllib.parse import urlencode, quote_plus
import json
import urllib.error
import base64

import atexit
import os
import signal

def cleanup_hardware():
    """强制清理硬件资源"""
    print("强制清理硬件资源...")
    os.system("sudo fuser -k /dev/ttyUSB0 2>/dev/null")
    os.system("sudo fuser -k /dev/deepCamera 2>/dev/null")
    time.sleep(2)

# 注册退出清理
atexit.register(cleanup_hardware)

# 捕获信号
def signal_handler(signum, frame):
    cleanup_hardware()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
signal.signal(signal.SIGTERM, signal_handler) # kill命令

# 百度语音API密钥（如需请替换）
BAIDU_API_KEY = "X298nO3hPZzk7e5NN8TeteEU"
BAIDU_SECRET_KEY = "IiwoOCRSR590XQe08a6Fc3vZPaP4wBgz"


# --- 来自 src/lib/uart.py 的串口常量与类（已内联） ---
# 通信地址定义
USB_FRAME_HEAD = bytes.fromhex("42")  # 通信序列帧头
USB_FRAME_LENMAX = 30  # 通信序列字节最长长度
USB_FRAME_LENMIN = 3  # 通信序列字节最短长度 (帧头+地址+长度, 无数据)

# 通信地址
USB_ADDR_ERRORCODE = bytes.fromhex("01")  # 错误代码
USB_ADDR_INFRA = bytes.fromhex("02")  # 红外传感器数据
USB_ADDR_LASER = bytes.fromhex("03")  # 激光测距传感器数据
USB_ADDR_THI = bytes.fromhex("04")  # 温度湿度传感器数据
USB_ADDR_ODI = bytes.fromhex("05")  # 心率血氧传感器数据
USB_ADDR_IMU_EULER = bytes.fromhex("06")  # IMU欧拉角数据
USB_ADDR_IMU_ACC = bytes.fromhex("07")  # IMU加速度数据
USB_ADDR_RFID = bytes.fromhex("08")  # 无线射频识别传感器数据（RFID）
USB_ADDR_AQI = bytes.fromhex("09")  # 空气质量传感器数据
USB_ADDR_GES = bytes.fromhex("0A")  # 手势传感器数据
USB_ADDR_CLI = bytes.fromhex("0B")  # 环境光强传感器数据
USB_ADDR_MIC = bytes.fromhex("0C")  # 音量传感器数据
USB_ADDR_RADAR = bytes.fromhex("0D")  # 毫米波传感器数据
USB_ADDR_BUTTON = bytes.fromhex("14")  # 按键
USB_ADDR_KEYBOARD = bytes.fromhex("15")  # 矩阵键盘
USB_ADDR_KNOB_NUM = bytes.fromhex("16")  # 旋钮累计值
USB_ADDR_KNOB_BTN = bytes.fromhex("17")  # 旋钮复位
USB_ADDR_TRANS = bytes.fromhex("18")  # 传送台速度
USB_ADDR_BUZZER = bytes.fromhex("19")  # 蜂鸣器
USB_ADDR_ARM_ACTIONS = bytes.fromhex("1A")  # 机械手臂
USB_ADDR_ARM_SERVO = bytes.fromhex("1B")  # 机械手臂动作帧长
USB_ADDR_RGB_NOR = bytes.fromhex("1C")  # RGB颜色
USB_ADDR_RGB_BLINK = bytes.fromhex("1D")  # RGB闪烁时长
USB_ADDR_RGB_FLOW = bytes.fromhex("1E")  # RGB流水时长
USB_ADDR_RELAY = bytes.fromhex("1F")  # 继电器
USB_ADDR_DOT_SCALE = bytes.fromhex("20")  # LED字符显示
USB_ADDR_DOT_NOR = bytes.fromhex("21")  # LED音阶显示
USB_ADDR_HEART = bytes.fromhex("37")  # 心跳信号
USB_ADDR_RESET = bytes.fromhex("38")  # 复位信号


class Sensors:
    """
    传感器数据类
    """

    def __init__(self):
        self.errorCode = 0
        self.adcInfra = 0
        self.rangeLaser = 0
        self.humi = 0.0
        self.temp = 0.0
        self.sop2 = 0
        self.heartRate = 0
        self.rfid = False
        self.co2 = 400
        self.tvoc = 0
        self.imu = self.Imu()
        self.ges = self.Gesture()
        self.btn = self.Button()
        self.knob = self.Knob()
        self.illume = 0
        self.adcMic = 0
        self.rangeRadar = 0
        self.keyCount = -1
        self.transSpeed = 0.0

    class Imu:
        def __init__(self):
            self.accx = 0
            self.accy = 0
            self.accz = 0
            self.gyrox = 0
            self.gyroy = 0
            self.gyroz = 0
            self.pitch = 0.0
            self.roll = 0.0
            self.yaw = 0.0

    class Gesture:
        def __init__(self):
            self.gesture = 0
            self.gesBrightness = 0
            self.gesAreaDet = 0

    class Button:
        def __init__(self):
            self.btnPressA = 0
            self.btnPressB = 0
            self.btnPressC = 0

    class Knob:
        def __init__(self):
            self.btnPress = 0
            self.count = 0


class RobotArm:
    def __init__(self):
        self.action = False
        self.timeSpent = 0
        self.timeStart = time.time()
        self.actionStand = ([500, 125, 500, 500, 500, 490, 1000], [500, 500, 500, 500, 500, 500, 0])
        self.actionPhotoTrans = ([500, 500, 470, 1000, 650, 500, 0],)
        self.actionGrapTransA = ([500, 500, 460, 1000, 700, 500, 1000], [500, 500, 110, 900, 700, 500, 1000], [665, 500, 110, 900, 700, 500, 1000], [665, 500, 110, 900, 700, 500, 0])
        self.actionGrapTransB = ([500, 500, 460, 1000, 700, 500, 1000], [500, 500, 120, 870, 640, 500, 1000], [665, 500, 120, 870, 640, 500, 1000], [665, 500, 150, 870, 750, 500, 0])
        self.actionPlaceSiteA = ([665, 500, 60, 720, 600, 930, 1000], [665, 500, 170, 870, 600, 930, 1000], [500, 500, 170, 870, 600, 930, 1000], [500, 500, 60, 720, 600, 930, 0])
        self.actionPlaceSiteB = ([665, 500, 60, 720, 600, 830, 1000], [665, 500, 160, 870, 600, 830, 1000], [500, 500, 160, 870, 600, 830, 1000], [500, 500, 50, 700, 600, 830, 0])
        self.actionPlaceSiteC = ([665, 500, 90, 700, 680, 960, 1000], [665, 500, 70, 870, 680, 960, 1000], [500, 500, 70, 870, 680, 960, 1000], [500, 500, 90, 700, 680, 960, 0])
        self.actionPlaceSiteD = ([665, 500, 50, 700, 620, 820, 1000], [665, 500, 60, 820, 620, 820, 1000], [500, 500, 60, 820, 620, 820, 1000], [500, 500, 50, 700, 620, 820, 0])
        self.actionPlaceDesk = ([665, 500, 95, 800, 640, 130, 1500], [665, 500, 95, 850, 640, 130, 1200], [500, 500, 95, 850, 640, 130, 1000], [500, 500, 95, 800, 640, 130, 0])
        self.actionReset = ([665, 125, 500, 500, 400, 490, 1000], [665, 125, 500, 500, 200, 490, 0])

    class Movement:
        stand = 0
        photoTrans = 1
        grapTransA = 2
        grapTransB = 3
        placeSiteA = 9
        placeSiteB = 10
        placeSiteC = 11
        placeSiteD = 12
        placeDesk = 13
        reset = 14


class Uart:
    def __init__(self, port):
        self.port = port
        self.baudRate = 115200
        self.serial = None
        self.thread = None
        self.threadHeart = None
        self.running = False
        self.recStart = False
        self.recIndex = 0
        self.recFinish = False
        self.len = 0
        self.recBuff = [b''] * USB_FRAME_LENMAX
        self.timeHart = time.time()
        self.connect = False
        self.timeDrop = time.time()
        self.sensors = Sensors()
        self.robotArm = RobotArm()

    def start(self):
        self.serial = serial.Serial(
            self.port,
            int(self.baudRate),
            timeout=1,
            parity=serial.PARITY_NONE,
            stopbits=1,
        )
        self.thread = threading.Thread(target=self.serialThread)
        self.running = True
        print("[Info] uart receive thread start!")
        self.thread.start()

        # 报告串口信息
        try:
            print(f"[Info] UART opened on {self.port} @ {self.baudRate}")
            if self.serial:
                try:
                    print(f"[Info] serial port info: {self.serial.portstr}")
                except Exception:
                    pass
        except Exception:
            pass
    
    def initSerial(self):
        """初始化串口，兼容测试脚本"""
        try:
            self.start()
            return True
        except Exception as e:
            print(f"[Error] initSerial failed: {e}")
            return False

    def startHeart(self):
        self.threadHeart = threading.Thread(target=self.heartThread)
        print("[Info] uartHeart receive thread start!")
        self.threadHeart.start()

    def stop(self, signum, frame):
        self.setTransSpeed(0.0)
        self.setRelaySwitch(False, False, False)
        self.robotArmMoveit(self.robotArm.Movement.reset)
        self.running = False
        self.thread.join()
        if self.serial:
            self.serial.close()
        print("[Info] uart thread is closed!")
        print("[Info] 串口通信多线程停止, 停止运行传送台, 关闭继电器!!!")
    
    def close(self):
        """关闭串口，兼容测试脚本"""
        try:
            self.running = False
            if hasattr(self, 'thread') and self.thread.is_alive():
                self.thread.join(timeout=1.0)
            if hasattr(self, 'threadHeart') and self.threadHeart and self.threadHeart.is_alive():
                self.threadHeart.join(timeout=1.0)
            if self.serial:
                self.serial.close()
                print("[Info] Serial port closed successfully")
        except Exception as e:
            print(f"[Error] Error closing serial port: {e}")

    def serialThread(self):
        time.sleep(0.5)
        while self.running:
            if self.serial.in_waiting > 0:
                data = self.serial.read(1)
                self.receiveHandle(data)

    def heartThread(self):
        time.sleep(0.5)
        while self.running:
            self.transmitSysHeart()

    def receiveHandle(self, data):
        if self.running == False:
            return
        if data == USB_FRAME_HEAD and not self.recStart:
            self.recStart = True
            self.recBuff[0] = data
            self.recIndex = 1
        elif self.recIndex == 1:
            # 保存地址字段
            self.recBuff[1] = data
            self.recIndex += 1
        elif self.recIndex == 2:
            self.recBuff[2] = data
            self.recIndex += 1
            self.len = int.from_bytes(data, byteorder="big", signed=False)
            if self.len > USB_FRAME_LENMAX or self.len < USB_FRAME_LENMIN:
                self.recIndex = 0
                self.recStart = False
        elif self.recStart and self.recIndex < USB_FRAME_LENMAX:
            if data == USB_FRAME_HEAD and self.recIndex == 1:
                self.recIndex = 1
            else:
                self.recBuff[self.recIndex] = data
                self.recIndex += 1

        if (
            self.recIndex >= USB_FRAME_LENMAX or self.recIndex >= self.len
        ) and self.recIndex >= USB_FRAME_LENMIN:
            check = int(0)
            for i in range(self.len - 1):
                check += int.from_bytes(self.recBuff[i], byteorder="big", signed=False)
            check = int(check % 256)
            if check == int.from_bytes(self.recBuff[self.len - 1], byteorder="big", signed=False):
                self.recFinish = True
                self.recIndex = 0
                self.recStart = False
                self.recLength = USB_FRAME_LENMAX
                self.timeDrop = time.time()
                self.connect = True
                self.transDataFrame()

    def transDataFrame(self):
        if self.recFinish:
            self.recFinish = False
            # 打印接收帧的地址/长度用于排查
            try:
                raw_addr = self.recBuff[1]
                if isinstance(raw_addr, (bytes, bytearray)):
                    addr_hex = raw_addr.hex()
                else:
                    addr_hex = format(int(raw_addr), '02x')
                print(f"[UART DEBUG] Received frame addr=0x{addr_hex} len={self.len}")
            except Exception:
                print("[UART DEBUG] Received frame (addr unknown)")

            if self.recBuff[1] == USB_ADDR_ERRORCODE:
                self.sensors.errorCode = struct.unpack("H", b''.join(self.recBuff[3:5]),)[0]
                print(f"[UART DEBUG] errorCode={self.sensors.errorCode}")
            elif self.recBuff[1] == USB_ADDR_ODI:
                self.sensors.heartRate = int.from_bytes(self.recBuff[3], byteorder="big", signed=False)
                self.sensors.sop2 = int.from_bytes(self.recBuff[4], byteorder="big", signed=False)
                print(f"[UART DEBUG] heartRate={self.sensors.heartRate} sop2={self.sensors.sop2}")
            elif self.recBuff[1] == USB_ADDR_BUTTON:
                if self.recBuff[3] == bytes.fromhex("01"):
                    self.sensors.btn.btnPressA = struct.unpack("H", b''.join(self.recBuff[4:6]),)[0]
                    print(f"[UART DEBUG] btnA={self.sensors.btn.btnPressA}")
                elif self.recBuff[3] == bytes.fromhex("02"):
                    self.sensors.btn.btnPressB = struct.unpack("H", b''.join(self.recBuff[4:6]),)[0]
                    print(f"[UART DEBUG] btnB={self.sensors.btn.btnPressB}")
                elif self.recBuff[3] == bytes.fromhex("03"):
                    self.sensors.btn.btnPressC = struct.unpack("H", b''.join(self.recBuff[4:6]),)[0]
                    print(f"[UART DEBUG] btnC={self.sensors.btn.btnPressC}")
            elif self.recBuff[1] == USB_ADDR_INFRA:
                self.sensors.adcInfra = struct.unpack("H", b''.join(self.recBuff[3:5]),)[0]
                print(f"[UART DEBUG] adcInfra={self.sensors.adcInfra}")
            elif self.recBuff[1] == USB_ADDR_LASER:
                self.sensors.rangeLaser = struct.unpack("H", b''.join(self.recBuff[3:5]),)[0]
                print(f"[UART DEBUG] rangeLaser={self.sensors.rangeLaser}")
            elif self.recBuff[1] == USB_ADDR_THI:
                self.sensors.humi = struct.unpack("f", b''.join(self.recBuff[3:7]),)[0]
                self.sensors.temp = struct.unpack("f", b''.join(self.recBuff[7:11]),)[0]
                print(f"[UART DEBUG] humi={self.sensors.humi} temp={self.sensors.temp}")
            elif self.recBuff[1] == USB_ADDR_IMU_EULER:
                self.sensors.imu.pitch = struct.unpack("f", b''.join(self.recBuff[3:7]),)[0]
                self.sensors.imu.roll = struct.unpack("f", b''.join(self.recBuff[7:11]),)[0]
                self.sensors.imu.yaw = struct.unpack("f", b''.join(self.recBuff[11:15]),)[0]
                print(f"[UART DEBUG] pitch={self.sensors.imu.pitch} roll={self.sensors.imu.roll} yaw={self.sensors.imu.yaw}")
            elif self.recBuff[1] == USB_ADDR_IMU_ACC:
                self.sensors.imu.accx = struct.unpack("h", b''.join(self.recBuff[3:5]),)[0]
                self.sensors.imu.accy = struct.unpack("h", b''.join(self.recBuff[5:7]),)[0]
                self.sensors.imu.accz = struct.unpack("h", b''.join(self.recBuff[7:9]),)[0]
                self.sensors.imu.gyrox = struct.unpack("h", b''.join(self.recBuff[9:11]),)[0]
                self.sensors.imu.gyroy = struct.unpack("h", b''.join(self.recBuff[11:13]),)[0]
                self.sensors.imu.gyroz = struct.unpack("h", b''.join(self.recBuff[13:15]),)[0]
                print(f"[UART DEBUG] accx={self.sensors.imu.accx} accy={self.sensors.imu.accy} accz={self.sensors.imu.accz}")
            elif self.recBuff[1] == USB_ADDR_RFID:
                self.sensors.rfid = True
                print("[UART DEBUG] rfid=True")
            elif self.recBuff[1] == USB_ADDR_AQI:
                self.sensors.co2 = struct.unpack("H", b''.join(self.recBuff[3:5]),)[0]
                if self.sensors.co2 < 400:
                    self.sensors.co2 = 400
                elif self.sensors.co2 > 999:
                    self.sensors.co2 = 999
                self.sensors.tvoc = struct.unpack("H", b''.join(self.recBuff[5:7]),)[0]
                if self.sensors.tvoc < 0:
                    self.sensors.tvoc = 0
                elif self.sensors.tvoc > 999:
                    self.sensors.tvoc = 999
                print(f"[UART DEBUG] co2={self.sensors.co2} tvoc={self.sensors.tvoc}")
            elif self.recBuff[1] == USB_ADDR_GES:
                gesture = int.from_bytes(self.recBuff[3], byteorder="big", signed=False)
                if gesture >= 1 and gesture <= 9:
                    self.sensors.ges.gesture = gesture
                self.sensors.ges.gesBrightness = int.from_bytes(self.recBuff[4], byteorder="big", signed=False)
                self.sensors.ges.gesAreaDet = struct.unpack("H", b''.join(self.recBuff[5:7]),)[0]
                print(f"[UART DEBUG] ges={self.sensors.ges.gesture} brightness={self.sensors.ges.gesBrightness} area={self.sensors.ges.gesAreaDet}")
            elif self.recBuff[1] == USB_ADDR_CLI:
                self.sensors.illume = struct.unpack("H", b''.join(self.recBuff[3:5]),)[0]
                print(f"[UART DEBUG] illume={self.sensors.illume}")
            elif self.recBuff[1] == USB_ADDR_MIC:
                self.sensors.adcMic = struct.unpack("H", b''.join(self.recBuff[3:5]),)[0]
                print(f"[UART DEBUG] adcMic={self.sensors.adcMic}")
            elif self.recBuff[1] == USB_ADDR_RADAR:
                self.sensors.rangeRadar = struct.unpack("H", b''.join(self.recBuff[3:5]),)[0]
                print(f"[UART DEBUG] rangeRadar={self.sensors.rangeRadar}")
            elif self.recBuff[1] == USB_ADDR_KEYBOARD:
                self.sensors.keyCount = struct.unpack("I", b''.join(self.recBuff[3:7]),)[0]
                print(f"[UART DEBUG] keyCount={self.sensors.keyCount}")
            elif self.recBuff[1] == USB_ADDR_KNOB_NUM:
                self.sensors.knob.count = struct.unpack("h", b''.join(self.recBuff[3:5]),)[0]
                print(f"[UART DEBUG] knob.count={self.sensors.knob.count}")
            elif self.recBuff[1] == USB_ADDR_KNOB_BTN:
                self.sensors.knob.btnPress = struct.unpack("H", b''.join(self.recBuff[3:5]),)[0]
                self.sensors.knob.count = 0
                print(f"[UART DEBUG] knob.btnPress={self.sensors.knob.btnPress}")
            elif self.recBuff[1] == USB_ADDR_TRANS:
                self.sensors.transSpeed = struct.unpack("f", b''.join(self.recBuff[3:7]),)[0]
                print(f"[UART DEBUG] transSpeed={self.sensors.transSpeed}")

    def transmitFrame(self, addr, data):
        print(f"[DEBUG] transmitFrame called, addr: {addr.hex()}, data: {data.hex() if data else 'None'}")
        
        if self.running == False:
            print(f"[DEBUG] transmitFrame: running is False, skipping")
            return

        if data is None:
            frame_length = 4  # 帧头(1) + 地址(1) + 长度(1) + 数据(0) = 4
            frame = (
                USB_FRAME_HEAD
                + addr
                + frame_length.to_bytes(1, byteorder="little", signed=False))
        else:
            frame_length = len(data) + 4  # 帧头(1) + 地址(1) + 长度(1) + 数据(n) + 校验和(1) = 4 + n
            frame = (
                USB_FRAME_HEAD
                + addr
                + frame_length.to_bytes(1, byteorder="little", signed=False)
                + data
            )
        
        print(f"[DEBUG] transmitFrame: 帧构建前 (帧头+地址+长度+数据): {frame.hex()}")

        # 计算校验和
        check = 0
        for byte in frame:
            check = (check + byte) & 0xFF
        
        # 添加校验和和额外的00字节
        frame = frame + check.to_bytes(1, byteorder="little", signed=False) + bytes.fromhex("00")
        
        print(f"[DEBUG] transmitFrame: 完整帧 (含校验和+额外字节): {frame.hex()}")
        print(f"[DEBUG] transmitFrame: 帧长度: {len(frame)} 字节")

        # 发送数据
        try:
            if self.serial is None:
                print(f"[DEBUG] transmitFrame: serial is None")
            else:
                print(f"[DEBUG] transmitFrame: 开始发送数据")
                bytes_sent = self.serial.write(frame)
                self.serial.flush()
                print(f"[DEBUG] transmitFrame: 发送成功，发送字节数: {bytes_sent}")
        except Exception as e:
            print(f"[DEBUG] transmitFrame: 发送失败: {e}")


    def setTransSpeed(self, speed):
        if speed > 0.1:
            print("[Warning] 限制传送台最大速度0.1m/s,当前设置速度:", str(speed), "m/s")
            speed = 0.1
        elif speed < -0.1:
            print("[Warning] 限制传送台最大速度-0.1m/s,当前设置速度:", str(speed), "m/s")
            speed = -0.1

        self.transmitFrame(USB_ADDR_TRANS, struct.pack("<f", speed))

    def setBuzzerAudio(self, audio):
        if audio < 1 or audio > 5:
            print("[Error] 蜂鸣器音效设置错误,请选择1~5种模式!")
            return
        self.transmitFrame(USB_ADDR_BUZZER, struct.pack("<B", audio))

    def setArmAngle(self, id, angle):
        if id < 1 or id > 6:
            print("[Error] 机械臂ID输入错误, 当前ID: ", str(id))
            return
        if angle < 0 or angle > 1000:
            print("[Error] 机械臂角度输入错误, 当前角度: ", str(angle))
            return
        stream = struct.pack("<B", id) + struct.pack("<H", angle)
        self.transmitFrame(USB_ADDR_ARM_SERVO, stream)

    def setArmActions(self, actions):
        print(f"[DEBUG] setArmActions called with actions: {actions}")
        self.robotArm.timeSpent = 0
        
        # 计算总时间并设置开始时间
        for i in range(len(actions)):
            if len(actions[i]) > 6:
                self.robotArm.timeSpent += actions[i][6]
                self.robotArm.timeSpent += 300
        
        # 在发送第一个动作前设置开始时间
        self.robotArm.timeStart = time.time()
        
        # 发送所有动作
        for i in range(len(actions)):
            print(f"[DEBUG] Processing action {i+1}/{len(actions)}, action: {actions[i]}")
            if len(actions[i]) > 6:
                if i > 9:
                    print("[Error] 机械臂动作组序号输入错误, 当前序号: ", str(i+1))
                    return
                if actions[i][0] < 0 or actions[i][0] > 1000:
                    print("[Error] 机械臂角度输入错误, 当前角度: ", str(actions[i][0]))
                    return
                if actions[i][1] < 0 or actions[i][1] > 1000:
                    print("[Error] 机械臂角度输入错误, 当前角度: ", str(actions[i][1]))
                    return
                if actions[i][2] < 0 or actions[i][2] > 1000:
                    print("[Error] 机械臂角度输入错误, 当前角度: ", str(actions[i][2]))
                    return
                if actions[i][3] < 0 or actions[i][3] > 1000:
                    print("[Error] 机械臂角度输入错误, 当前角度: ", str(actions[i][3]))
                    return
                if actions[i][4] < 0 or actions[i][4] > 1000:
                    print("[Error] 机械臂角度输入错误, 当前角度: ", str(actions[i][4]))
                    return
                if actions[i][5] < 0 or actions[i][5] > 1000:
                    print("[Error] 机械臂角度输入错误, 当前角度: ", str(actions[i][5]))
                    return
                if actions[i][6] < 0:
                    actions[i][6] = 0
                elif actions[i][6] > 10000:
                    actions[i][6] = 10000
                
                # 构建数据流
                stream = struct.pack("<B", i+1) + struct.pack("<H", actions[i][0]) + struct.pack("<H", actions[i][1]) + struct.pack("<H", actions[i][2]) + struct.pack("<H", actions[i][3]) + struct.pack("<H", actions[i][4]) + struct.pack("<H", actions[i][5]) + struct.pack("<H", actions[i][6])
                print(f"[DEBUG] 构建的数据流: {stream} (十六进制: {stream.hex()})")
                
                # 发送数据帧
                print(f"[DEBUG] 调用 transmitFrame, 地址: {USB_ADDR_ARM_ACTIONS.hex()}, 数据: {stream.hex()}")
                self.transmitFrame(USB_ADDR_ARM_ACTIONS, stream)
                time.sleep(0.03)
                print(f"[DEBUG] 动作 {i+1} 发送完成")
            else:
                print(f"[DEBUG] 动作 {i+1} 长度不足，跳过")

    def getArmActionsBusy(self):
        thisTime = time.time()
        if (thisTime - self.robotArm.timeStart)*1000 > self.robotArm.timeSpent:
            return False
        else:
            return True

    def robotArmMoveit(self, action):
        print(f"[DEBUG] robotArmMoveit called with action: {action}")
        if action == self.robotArm.Movement.stand:
            print(f"[DEBUG] Executing action: stand, actions: {self.robotArm.actionStand}")
            self.setArmActions(self.robotArm.actionStand)
        elif action == self.robotArm.Movement.photoTrans:
            print(f"[DEBUG] Executing action: photoTrans, actions: {self.robotArm.actionPhotoTrans}")
            self.setArmActions(self.robotArm.actionPhotoTrans)
        elif action == self.robotArm.Movement.grapTransA:
            print(f"[DEBUG] Executing action: grapTransA, actions: {self.robotArm.actionGrapTransA}")
            self.setArmActions(self.robotArm.actionGrapTransA)
        elif action == self.robotArm.Movement.grapTransB:
            print(f"[DEBUG] Executing action: grapTransB, actions: {self.robotArm.actionGrapTransB}")
            self.setArmActions(self.robotArm.actionGrapTransB)
        elif action == self.robotArm.Movement.placeSiteA:
            print(f"[DEBUG] Executing action: placeSiteA, actions: {self.robotArm.actionPlaceSiteA}")
            self.setArmActions(self.robotArm.actionPlaceSiteA)
        elif action == self.robotArm.Movement.placeSiteB:
            print(f"[DEBUG] Executing action: placeSiteB, actions: {self.robotArm.actionPlaceSiteB}")
            self.setArmActions(self.robotArm.actionPlaceSiteB)
        elif action == self.robotArm.Movement.placeSiteC:
            print(f"[DEBUG] Executing action: placeSiteC, actions: {self.robotArm.actionPlaceSiteC}")
            self.setArmActions(self.robotArm.actionPlaceSiteC)
        elif action == self.robotArm.Movement.placeSiteD:
            print(f"[DEBUG] Executing action: placeSiteD, actions: {self.robotArm.actionPlaceSiteD}")
            self.setArmActions(self.robotArm.actionPlaceSiteD)
        elif action == self.robotArm.Movement.placeDesk:
            print(f"[DEBUG] Executing action: placeDesk, actions: {self.robotArm.actionPlaceDesk}")
            self.setArmActions(self.robotArm.actionPlaceDesk)
        elif action == self.robotArm.Movement.reset:
            print(f"[DEBUG] Executing action: reset, actions: {self.robotArm.actionReset}")
            self.setArmActions(self.robotArm.actionReset)
        else:
            print(f"[DEBUG] Unknown action: {action}")

    def setRgbColors(self, colorA, colorB, colorC, colorD, colorE):
        colorA = bytes(struct.pack("<I", colorA))
        colorA = [colorA[i:i+3] for i in range(0, len(colorA), 3)][0]
        colorB = bytes(struct.pack("<I", colorB))
        colorB = [colorB[i:i+3] for i in range(0, len(colorB), 3)][0]
        colorC = bytes(struct.pack("<I", colorC))
        colorC = [colorC[i:i+3] for i in range(0, len(colorC), 3)][0]
        colorD = bytes(struct.pack("<I", colorD))
        colorD = [colorD[i:i+3] for i in range(0, len(colorD), 3)][0]
        colorE = bytes(struct.pack("<I", colorE))
        colorE = [colorE[i:i+3] for i in range(0, len(colorE), 3)][0]

        self.transmitFrame(USB_ADDR_RGB_NOR, colorA + colorB+colorC+colorD+colorE)

    def setRgbBlink(self, time_ms):
        if time_ms <= 50:
            print("[Error] RGB灯闪烁间隔时长输入错误, 当前频率: ", str(time_ms), "ms")
            return
        self.transmitFrame(USB_ADDR_RGB_BLINK, struct.pack("<H", time_ms))

    def setRgbFlow(self, time_ms):
        if time_ms < 50:
            print("[Error] RGB灯流水间隔时长输入错误, 当前频率: ", str(time_ms), "ms")
            return
        self.transmitFrame(USB_ADDR_RGB_FLOW, struct.pack("<H", time_ms))

    def setRelaySwitch(self, relayA, relayB, relayC):
        relay = 0
        if relayA:
            relay |= 1
        if relayB:
            relay |= 2
        if relayC:
            relay |= 4
        self.transmitFrame(USB_ADDR_RELAY, struct.pack("<B", relay))

    def setDotScale(self, dot, scale):
        if len(scale) != 8:
            print("[Error] LED音阶数据输入异常!!!")
            return
        if dot < 1 or dot > 3:
            print("[Error] LED点阵编号输入错误!!!")
            return
        for i in range(0, 8):
            if scale[i] < 0 or scale[i] > 8:
                print("[Error] LED音阶数据输入异常!!!")
                return

        stream = struct.pack("<B", dot)
        for i in range(0, 4):
            data = (scale[i*2] << 4) | scale[i*2+1]
            stream += struct.pack("<B", data)

        self.transmitFrame(USB_ADDR_DOT_SCALE, stream)

    def setDotImage(self, dot, image):
        if dot < 1 or dot > 3:
            print("[Error] LED点阵编号输入错误!!!")
            return
        stream = struct.pack("<B", dot)
        for i in range(0, 8):
            stream += struct.pack("<B", image[i])

        self.transmitFrame(USB_ADDR_DOT_NOR, stream)

    def transmitSysHeart(self):
        thisTime = time.time()
        if thisTime - self.timeHart > 1:
            self.transmitFrame(USB_ADDR_HEART, None)
            self.timeHart = thisTime

    def comStatusCheck(self):
        if self.connect:
            thisTime = time.time()
            if thisTime - self.timeDrop > 5:
                self.connect = False

    def systemReset(self):
        self.transmitFrame(USB_ADDR_RESET, None)



class AudioRecorder:
    def __init__(self, savePath):
        if savePath == None:
            self.savePath = os.path.join(BASE_DIR, 'res', 'audio', 'record', 'temp.wav')
        else:
            self.savePath = savePath
        self.sampleRate = 16000
        self.channels = 1
        self.width = 2
        self.driveIndex = 1
        self.chunk = 1024
        self.recording = False
        self.frames = []
        self.finish = False
        self.audio = pyaudio.PyAudio()
        self.stream = None
        try:
            self.audio = pyaudio.PyAudio()
        except Exception as e:
            print("[Warning] pyaudio init failed:", e)
            self.audio = None
        self.stream = None
        if self.audio is not None:
            try:
                keyboard.on_press_key("space", lambda _: self.startRecord())
                keyboard.on_release_key("space", lambda _: self.stopRecord())
            except Exception:
                print("[Warning] keyboard registration failed; audio hotkeys disabled")
        else:
            print("[Warning] AudioRecorder disabled due to missing audio backend")

    def AudioRecording(self, audio, count, time, status):
        if self.recording:
            self.frames.append(audio)
        return (audio, pyaudio.paContinue)

    def startRecord(self):
        if self.audio is None:
            return
        if not self.recording:
            self.frames = []
            self.finish = False
            self.stream = self.audio.open(
                rate=self.sampleRate,
                format=self.audio.get_format_from_width(self.width),
                channels=self.channels,
                input=True,
                input_device_index=self.driveIndex,
                frames_per_buffer=self.chunk,
                stream_callback=self.AudioRecording)
            self.recording = True

    def stopRecord(self):
        if self.audio is None:
            return
        if self.recording:
            self.recording = False
            self.stream.stop_stream()
            self.stream.close()
            # ensure directory exists
            save_dir = os.path.dirname(self.savePath)
            if save_dir and not os.path.exists(save_dir):
                os.makedirs(save_dir, exist_ok=True)
            file = wave.open(self.savePath, 'wb')
            file.setnchannels(self.channels)
            file.setsampwidth(self.audio.get_sample_size(
                self.audio.get_format_from_width(self.width)))
            file.setframerate(self.sampleRate)
            file.writeframes(b''.join(self.frames))
            file.close()
            self.finish = True


class AsrOnline:
    def __init__(self, audioPath):
        self.apiKey = BAIDU_API_KEY
        self.secretKey = BAIDU_SECRET_KEY
        if audioPath == None:
            self.audioPath = os.path.join(BASE_DIR, 'res', 'audio', 'record', 'temp.wav')
        else:
            self.audioPath = audioPath
        self.cuid = '123456PYTHON'
        self.scope = 'audio_voice_assistant_get'

    def speechRecognition(self):
        token = self.fetchToken()
        if not token:
            return ""

        with open(self.audioPath, 'rb') as file:
            audio = file.read()

        if len(audio) == 0:
            return ""

        speech = base64.b64encode(audio)
        speech = str(speech, 'utf-8')
        params = {'dev_pid': 1537,
                  'format': self.audioPath[-3:],
                  'rate': 16000,
                  'token': token,
                  'cuid': self.cuid,
                  'channel': 1,
                  'speech': speech,
                  'len': len(audio)
                  }
        request = json.dumps(params, sort_keys=False)
        response = Request('http://vop.baidu.com/server_api',
                           request.encode('utf-8'))
        response.add_header('Content-Type', 'application/json')
        try:
            result = urlopen(response)
            resAsr = result.read()
        except URLError as err:
            try:
                resAsr = err.read()
            except Exception:
                return ""

        resAsr = str(resAsr, 'utf-8')
        resJson = json.loads(resAsr)
        try:
            resAsr = resJson["result"][0]
            print("ASR: ", resAsr)
        except Exception:
            print("[Error] 获取云端识别数据失败")
            return ""

        return resAsr

    def fetchToken(self):
        params = {'grant_type': 'client_credentials',
                  'client_id': self.apiKey,
                  'client_secret': self.secretKey}
        request = urlencode(params).encode('utf-8')
        response = Request('http://aip.baidubce.com/oauth/2.0/token',
                           request)
        try:
            file = urlopen(response)
            result = file.read()
        except urllib.error.HTTPError as err:
            print('token http response http code : ' + str(err.code))
            try:
                result = err.read()
            except Exception:
                return False
        except URLError as err:
            print('token http response http code : ' + str(err))
            try:
                result = err.read()
            except Exception:
                return False

        res = json.loads(result.decode())
        if ('access_token' in res.keys() and 'scope' in res.keys()):
            if self.scope and (not self.scope in res['scope'].split(' ')):
                print('[Error] ASR scope is not correct!')
                return False
            return res['access_token']
        else:
            print('[Error] MAYBE API_KEY or SECRET_KEY not correct!')
            return False


class AudioPlayer:
    def __init__(self, musicFolder):
        if musicFolder == None:
            self.musicFolder = "/root/Desktop/workspace/AiBox_T710_Python/res/audio/music"
        else:
            self.musicFolder = musicFolder
        self.musicIndex = 0
        try:
            self.playlist = os.listdir(self.musicFolder)
        except Exception:
            self.playlist = []
        self.musicing = False
        self.radioing = False
        self.musicPos = 0
        self.enable = False
        self.volume = 0.5
        self.pause = False
        if len(self.playlist) > 0:
            self.enable = True
        try:
            keyboard.on_press_key("right", lambda _: self.nextMusic())
            keyboard.on_press_key("left", lambda _: self.previousMusic())
            keyboard.on_press_key("up", lambda _: self.turnUpVolume())
            keyboard.on_press_key("down", lambda _: self.turnDownVolume())
            keyboard.on_release_key("m", lambda _: self.resumeMusic())
            keyboard.on_press_key("enter", lambda _: self.pauseMusic())
            keyboard.on_press_key("s",lambda _: self.playMusic())
        except Exception:
            print("[Warning] keyboard registration failed for AudioPlayer; hotkeys disabled")

        # 初始化 pygame mixer，若失败则禁用音频功能
        self.audio_available = False
        try:
            pygame.init()
            try:
                pygame.mixer.init()
                self.audio_available = True
                self.setVolume(self.volume)
            except Exception as e:
                print("[Warning] pygame.mixer init failed:", e)
                self.audio_available = False
        except Exception as e:
            print("[Warning] pygame init failed:", e)
            self.audio_available = False

    def setVolume(self, volume):
        self.volume = volume
        if not getattr(self, 'audio_available', False):
            return
        try:
            pygame.mixer.music.set_volume(volume)
        except Exception:
            pass

    def playMusic(self):
        if not self.enable or not getattr(self, 'audio_available', False):
            return
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
            except Exception:
                return
        self.musicIndex = random.randint(0, len(self.playlist)-1)
        pygame.mixer.music.load(os.path.join(
            self.musicFolder, self.playlist[self.musicIndex]))
        pygame.mixer.music.play()
        self.musicing = True

    def pauseMusic(self):
        if not getattr(self, 'audio_available', False):
            return
        if self.musicing and not self.radioing:
            try:
                pygame.mixer.music.pause()
            except Exception:
                pass
            self.pause = True
        elif self.radioing:
            self.radioing = False
            try:
                pygame.mixer.music.pause()
            except Exception:
                pass
            self.pause = True

    def resumeMusic(self):
        if not getattr(self, 'audio_available', False):
            return
        if self.musicing and not self.radioing:
            try:
                pygame.mixer.music.unpause()
            except Exception:
                pass
            self.pause = False
        elif self.radioing:
            self.pause = False

    def stopMusic(self):
        if not getattr(self, 'audio_available', False):
            return
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        self.musicing = False

    def nextMusic(self):
        if not self.enable or not getattr(self, 'audio_available', False):
            return
        self.pause = True
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
            except Exception:
                return
        if self.musicIndex >= len(self.playlist) - 1:
            self.musicIndex = 0
        else:
            self.musicIndex += 1
        pygame.mixer.music.load(os.path.join(
            self.musicFolder, self.playlist[self.musicIndex]))
        pygame.mixer.music.play()
        self.musicing = True
        self.pause = False

    def previousMusic(self):
        if not self.enable or not getattr(self, 'audio_available', False):
            return
        self.pause = True
        if not pygame.mixer.get_init():
            try:
                pygame.mixer.init()
            except Exception:
                return
        if self.musicIndex <= 0:
            self.musicIndex = len(self.playlist) - 1
        else:
            self.musicIndex -= 1
        pygame.mixer.music.load(os.path.join(
            self.musicFolder, self.playlist[self.musicIndex]))
        pygame.mixer.music.play()
        self.musicing = True
        self.pause = False

    def turnUpVolume(self):
        if self.volume > 1.0:
            self.volume = 1.0
        else:
            self.volume += 0.1
        self.setVolume(self.volume)

    def turnDownVolume(self):
        if self.volume <= 0:
            self.volume = 0.0
        else:
            self.volume -= 0.1
        self.setVolume(self.volume)

    def playRadio(self, audioPath):
        self.pause = True
        if self.musicing:
            try:
                self.musicPos = pygame.mixer.music.get_pos()
            except Exception:
                self.musicPos = 0
        if not pygame.mixer.get_init():
            pygame.mixer.init()
        pygame.mixer.music.load(audioPath)
        pygame.mixer.music.play()
        self.radioing = True
        self.pause = False

    def autoResumeMusic(self):
        if self.pause:
            return
        if self.musicing and not self.radioing:
            if not pygame.mixer.music.get_busy():
                self.nextMusic()
        elif not self.musicing and self.radioing:
            if not pygame.mixer.music.get_busy():
                self.radioing = False
        elif self.musicing and self.radioing:
            if not pygame.mixer.music.get_busy():
                self.radioing = False
                if not self.enable:
                    return
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                pygame.mixer.music.load(os.path.join(
                    self.musicFolder, self.playlist[self.musicIndex]))
                pygame.mixer.music.play(self.musicPos)
                self.musicing = True


class WordsMatching:
    def __init__(self, jsonPath):
        if jsonPath == None:
            self.jsonPath = "/root/Desktop/workspace/AiBox_T710_Python/res/config/interaction.json"
        else:
            self.jsonPath = jsonPath
        self.jsonStream = None
        if os.path.exists(self.jsonPath):
            with open(self.jsonPath, 'r', encoding='utf-8') as file:
                s = file.read()
            self.jsonStream = json.loads(s)
        else:
            print("[Error] 字符匹配Json文件路径错误: ", self.jsonPath)

    def wordsMatching(self, s):
        if self.jsonStream == None:
            return "", ""
        for contrl in self.jsonStream.get("control", {}):
            if len(self.jsonStream["control"][contrl]) > 1:
                for item in self.jsonStream["control"][contrl]["keyword"]:
                    if s.__contains__(item):
                        return "control", self.jsonStream["control"][contrl]["response"]
        for chat in self.jsonStream.get("chat", {}):
            if len(self.jsonStream["chat"][chat]) > 1:
                for item in self.jsonStream["chat"][chat]["keyword"]:
                    if s.__contains__(item):
                        jsonLen = len(self.jsonStream["chat"][chat]["response"])
                        if jsonLen > 0:
                            randomChat = random.randint(0, jsonLen-1)
                            return "chat", self.jsonStream["chat"][chat]["response"][randomChat]
        return "", ""


class TtsOnline:
    def __init__(self, audioPath):
        if audioPath == None:
            self.audioPath = os.path.join(BASE_DIR, 'res', 'audio', 'tts', 'temp.mp3')
        else:
            self.audioPath = audioPath
        self.apiKey = BAIDU_API_KEY
        self.secretKey = BAIDU_SECRET_KEY
        self.cuid = '123456PYTHON'
        self.scope = 'audio_voice_assistant_get'
        self.person = 0
        self.speed = 6
        self.pitch = 5
        self.volume = 5
        self.format = 3

    def fetchToken(self):
        params = {'grant_type': 'client_credentials',
                  'client_id': self.apiKey,
                  'client_secret': self.secretKey}
        request = urlencode(params).encode('utf-8')
        response = Request('http://aip.baidubce.com/oauth/2.0/token',
                           request)
        try:
            file = urlopen(response)
            result = file.read()
        except urllib.error.HTTPError as err:
            try:
                result = err.read()
            except Exception:
                return False
        except URLError as err:
            try:
                result = err.read()
            except Exception:
                return False

        res = json.loads(result.decode())
        if ('access_token' in res.keys() and 'scope' in res.keys()):
            if self.scope and (not self.scope in res['scope'].split(' ')):
                print('[Error] TTS scope is not correct!')
                return False
            return res['access_token']
        else:
            print('[Error] MAYBE API_KEY or SECRET_KEY not correct!')
            return False

    def speechTransfer(self, text):
        token = self.fetchToken()
        if not token:
            return False
        text = quote_plus(text)
        params = {'tok': token, 'tex': text, 'per': self.person, 'spd': self.speed, 'pit': self.pitch,
                  'vol': self.volume, 'aue': self.format, 'cuid': self.cuid, 'lan': 'zh', 'ctp': 1}
        data = urlencode(params)
        response = Request('http://tsn.baidu.com/text2audio', data.encode('utf-8'))
        error = False
        try:
            res = urlopen(response)
            result = res.read()
            headers = dict((name.lower(), value)
                           for name, value in res.headers.items())
            error = ('content-type' not in headers.keys()
                     or headers['content-type'].find('audio/') < 0)
        except URLError as err:
            try:
                result = err.read()
            except Exception:
                return False
            error = True

        if not error:
            out_dir = os.path.dirname(self.audioPath)
            if out_dir and not os.path.exists(out_dir):
                os.makedirs(out_dir, exist_ok=True)
            with open(self.audioPath, 'wb') as file:
                file.write(result)
            return self.audioPath
        else:
            return False

# --- 整合结束 ---

class Panel:
    """
    面板数据显示类（含人脸关键点检测功能）
    """
    def __init__(self) -> None:
        self.speedTrans = 0.0    # 初始化传送台速度
        self.fps = 0             # 初始化FPS
        self.gestur = None       # 初始化手势标志
        self.button = self.Button()  # 初始化按钮状态
        self.error = [0] * 12    # 初始化错误代码状态
        # 以脚本目录为基准构造资源路径，兼容在实验箱上运行
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.font = ImageFont.truetype(
            os.path.join(base_dir, 'res', 'utils', 'QingNingYouYuan.ttf'), 30)  # 系统日志

        # 新增：初始化人脸关键点检测模型（使用相对路径，适配 AiBox_T710）
        try:
            self.face_detector = FaceKeyPoint(
                os.path.join(base_dir, 'res', 'models', 'faceDetection'),
                os.path.join(base_dir, 'res', 'models', 'faceLandmark')
            )
            self.face_threshold = 0.5  # 人脸检测置信度阈值
        except Exception as e:
            print('[Warning] 人脸关键点模型初始化失败:', e)
            self.face_detector = None
            self.face_threshold = 0.5
        # 语音模块初始化（从 lib/speech.py 整合）
        try:
            self.audioRecorder = AudioRecorder(None)
            self.audioPlayer = AudioPlayer(None)
            self.asr = AsrOnline(None)
            self.ttsOnline = TtsOnline(None)
            self.wordsMatching = WordsMatching(os.path.join(base_dir, 'res', 'config', 'interaction.json'))
        except Exception as e:
            print("[Warning] 语音模块初始化失败:", e)

        # 机械臂跟踪相关参数（使机械臂根据检测到的人脸位置摆动）
        self.last_arm_move_time = 0.0
        self.arm_move_interval = 0.2  # 最小移动间隔（秒）
        self.base_servo_id = 1         # 底座水平旋转舵机编号（如需调整，可改为实际编号）
        self.tilt_servo_id = 2         # 俯仰舵机编号
        # 每个舵机的安全范围（基于人工智能嵌入式实验箱建议）
        # 格式: servo_id: (min, max)
        self.servo_limits = {
            1: (600, 700),
            2: (0, 1000),
            3: (60, 940),
            4: (60, 940),
            5: (150, 700),
            6: (0, 1000),
        }
        # 初始角度取各舵机范围中点
        self.current_base_angle = int((self.servo_limits[self.base_servo_id][0] + self.servo_limits[self.base_servo_id][1]) / 2)
        self.current_tilt_angle = int((self.servo_limits[self.tilt_servo_id][0] + self.servo_limits[self.tilt_servo_id][1]) / 2)
        # 平滑步进（每次最多改变的角度）
        self.arm_step = 30

        # 机械臂初始化状态（用于 UI 显示）
        # status: 'idle'|'initializing'|'ok'|'failed'
        self.robot_init_status = 'idle'
        self.robot_init_time = 0.0
        self.robot_init_msg = ''
        # 人脸检测频率（每 N 帧运行一次，减少主循环负载）
        self.face_interval = 5

    class Button:
        """
        按钮状态
        """
        def __init__(self):
            self.buttonA = False
            self.buttonB = False
            self.buttonC = False

    # 新增：人脸关键点检测处理方法
    def process_face_landmark(self, frame):
        """处理人脸关键点检测并绘制结果"""
        # 如果模型初始化失败则跳过人脸检测
        if not hasattr(self, 'face_detector') or self.face_detector is None:
            return frame

        # 1. 进行人脸检测
        face_res = self.face_detector.detector.render(frame)

        # 2. 进行关键点检测
        landmark_res = self.face_detector.render(frame, face_res, self.face_threshold)

        # 3. 绘制检测结果（方框和关键点）
        frame_with_landmark = self.face_detector.drawBox(frame, landmark_res)

        # 4. 根据检测到的人脸位置控制机械臂（简单的左右和上下摆动）
        try:
            boxes = landmark_res.get("boxes", [])
            if len(boxes) > 0:
                # 只使用第一个检测到的人脸
                xmin, ymin, xmax, ymax = boxes[0]
                h, w = frame.shape[:2]
                cx = (xmin + xmax) / 2.0
                cy = (ymin + ymax) / 2.0

                # 使用每个舵机的限制范围进行映射并夹紧目标值
                try:
                    bmin, bmax = self.servo_limits.get(self.base_servo_id, (200, 800))
                    tmin, tmax = self.servo_limits.get(self.tilt_servo_id, (200, 800))
                except Exception:
                    bmin, bmax = (200, 800)
                    tmin, tmax = (200, 800)

                target_base = int(bmin + (cx / w) * (bmax - bmin))
                target_tilt = int(tmin + (1.0 - (cy / h)) * (tmax - tmin))

                # 夹紧到允许范围内
                target_base = max(bmin, min(bmax, target_base))
                target_tilt = max(tmin, min(tmax, target_tilt))

                now = time.time()
                if now - self.last_arm_move_time >= self.arm_move_interval:
                    # 平滑移动：限制每次步长
                    step = self.arm_step
                    if abs(target_base - self.current_base_angle) > step:
                        self.current_base_angle += step if target_base > self.current_base_angle else -step
                    else:
                        self.current_base_angle = target_base

                    if abs(target_tilt - self.current_tilt_angle) > step:
                        self.current_tilt_angle += step if target_tilt > self.current_tilt_angle else -step
                    else:
                        self.current_tilt_angle = target_tilt

                    # 发送舵机指令（若全局 uart 可用）
                    if 'uart' in globals() and getattr(uart, "running", False):
                        try:
                            uart.setArmAngle(self.base_servo_id, int(self.current_base_angle))
                            uart.setArmAngle(self.tilt_servo_id, int(self.current_tilt_angle))
                        except Exception as e:
                            print("[Warning] 机械臂跟踪命令发送失败:", e)
                    self.last_arm_move_time = now
        except Exception as e:
            print("[Warning] 人脸跟踪控制出错:", e)

        return frame_with_landmark

    def init_robot_arm(self, action=None, wait_for_uart=True):
        """初始化机械臂到指定动作（默认 photoTrans）。

        把机械臂初始化封装为 Panel 的方法，以便在主函数里明确调用，避免在构造函数中直接触发硬件动作被后续重新初始化覆盖。
        action: 机械臂动作枚举，例如 uart.robotArm.Movement.photoTrans
        wait_for_uart: 若串口线程尚未运行，是否等待短时间直到可用
        返回: bool 成功或失败
        """
        # 设置为初始化中状态
        self.robot_init_status = 'initializing'
        self.robot_init_time = time.time()
        self.robot_init_msg = ''
        success = False

        print(f"[DEBUG] 开始初始化机械臂，uart.running={getattr(uart, 'running', False)}")

        # 默认动作为 photoTrans（抓取/传送前位）
        if action is None:
            try:
                action = uart.robotArm.Movement.photoTrans
                print(f"[DEBUG] 使用默认动作: {action}")
            except Exception as e:
                action = None
                self.robot_init_msg = str(e)
                print(f"[DEBUG] 获取默认动作失败: {e}")

        if 'uart' in globals() and action is not None:
            try:
                # 如果串口线程已运行则立即发送，否则短等待直到串口可用或超时
                if getattr(uart, 'running', False):
                    print(f"[DEBUG] 串口已运行，发送动作命令: {action}")
                    uart.robotArmMoveit(action)
                    success = True
                    print(f"[DEBUG] 机械臂初始化命令发送成功")
                elif wait_for_uart:
                    print(f"[DEBUG] 等待串口运行，超时时间: 3秒")
                    timeout = time.time() + 3.0
                    while time.time() < timeout:
                        if getattr(uart, 'running', False):
                            print(f"[DEBUG] 串口已运行，发送动作命令: {action}")
                            uart.robotArmMoveit(action)
                            success = True
                            print(f"[DEBUG] 机械臂初始化命令发送成功")
                            break
                        print(f"[DEBUG] 等待串口运行... 当前时间: {time.time()}, 超时时间: {timeout}")
                        time.sleep(0.1)
                    if not success:
                        print(f"[DEBUG] 等待串口超时")
            except Exception as e:
                self.robot_init_msg = str(e)
                print("[Warning] 初始化机械臂失败:", e)
        else:
            self.robot_init_msg = 'uart 未就绪或 action 未给定'
            print(f"[Warning] 无法初始化机械臂: uart 未就绪或 action 未给定, uart in globals={('uart' in globals())}, action={action}")

        if success:
            self.robot_init_status = 'ok'
            self.robot_init_time = time.time()
            self.robot_init_msg = 'initialized'
            print(f"[DEBUG] 机械臂初始化成功")
        else:
            # 若尚处于 initializing，则标记为 failed
            if self.robot_init_status == 'initializing':
                self.robot_init_status = 'failed'
                self.robot_init_time = time.time()
                print(f"[DEBUG] 机械臂初始化失败")
        return success

    def showError(self, frame, img):
        """
        显示错误代码信息
        """
        # 如果没有错误则直接绘制视频帧到大图片位置
        # 缓存 errorLogo 以避免每帧磁盘 I/O
        if not hasattr(self, '_error_logo'):
            try:
                self._error_logo = cv2.imread(os.path.join(BASE_DIR, 'res', 'images', 'panel', 'errorcode.png'))
                if self._error_logo is not None:
                    self._error_logo = cv2.resize(self._error_logo, (158, 158))
            except Exception:
                self._error_logo = None

        # 准备视频块（确保大小 480x640）
        try:
            vf = cv2.resize(frame, (640, 480))
        except Exception:
            vf = cv2.resize(frame.copy(), (640, 480)) if frame is not None else np.zeros((480,640,3), dtype=np.uint8)

        if uart.sensors.errorCode != 0:
            if self._error_logo is not None:
                img[28:28+158,229:229+158] = self._error_logo

            errorCode = uart.sensors.errorCode
            if errorCode > 0:
                for i in range(11, -1, -1):
                    if errorCode - 2**i >= 0:
                        errorCode = errorCode - 2**i
                        self.error[i] = 1
                    else:
                        self.error[i] = 0

            # 使用 OpenCV 直接绘制文本到视频帧，避免 PIL 转换开销
            for i in range(12):
                if self.error[i]:
                    if i == 0:
                        txt = "环境光强传感器故障"
                    elif i == 1:
                        txt = "激光测距传感器故障"
                    elif i == 2:
                        txt = "温湿度传感器故障"
                    elif i == 3:
                        txt = "心率血氧传感器故障"
                    elif i == 4:
                        txt = "空气质量传感器故障"
                    elif i == 5:
                        txt = "电磁感应传感器故障"
                    elif i == 6:
                        txt = "惯性检测传感器故障"
                    elif i == 7:
                        txt = "手势检测传感器故障"
                    elif i == 8:
                        txt = "毫米波雷达传感器故障"
                    elif i == 9:
                        txt = "无线通信传感器故障"
                    elif i == 10:
                        txt = "板间通信故障"
                    elif i == 11:
                        txt = "传送台模组故障"
                    cv2.putText(vf, txt, (10, 30*(i+1)), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,0,255), 2)

        # 将视频块绘制到面板图片上
        img[200:200+480,597:597+640] = vf
        return img

    def showData(self, img):
        """
        显示串口接收到的数据
        """
        # 检测串口数据是否正常发送
        if uart.connect:
            connect = cv2.imread('/root/Desktop/workspace/AiBox_T710_Python/res/images/panel/data.png')
            connect = cv2.resize(connect,(158,158))
            img[22:22+158,35:35+158] = connect

        # 激光测距
        cv2.putText(img,str(uart.sensors.rangeLaser),(230, 307),cv2.FONT_HERSHEY_SIMPLEX,1,(216, 187, 129),3)

        # 红外传感器
        cv2.putText(img,str(uart.sensors.adcInfra),(200, 405),cv2.FONT_HERSHEY_SIMPLEX,2,(11, 65, 228),3,)

        # 毫米波
        cv2.putText(img,str(uart.sensors.rangeRadar),(245, 525),cv2.FONT_HERSHEY_SIMPLEX,1.5,(49, 125, 237),3,)

        # 光强
        cv2.putText(img,str(uart.sensors.illume),(260 if uart.sensors.illume-1000<0 else 250, 647),cv2.FONT_HERSHEY_SIMPLEX,1.5,(107, 255, 255),3,)

        # 音量
        cv2.putText(img,str(uart.sensors.adcMic),(230, 760),cv2.FONT_HERSHEY_SIMPLEX,1.5,(219, 150, 18),3,)

        # co2
        cv2.putText(img,str(uart.sensors.co2),(210, 970),cv2.FONT_HERSHEY_SIMPLEX,1.5,(255, 249, 205),3,)

        # tvoc2
        cv2.putText(img,str(uart.sensors.tvoc),(210, 1040),cv2.FONT_HERSHEY_SIMPLEX,1.5,(255, 249, 205),3,)

        # 传送台速度
        cv2.putText(img,str(round(self.speedTrans,2)),(1630, 105),cv2.FONT_HERSHEY_SIMPLEX,1.5,(145, 203, 105),3)

        # 机械臂初始化状态（右上角）
        try:
            status_map = {'ok':'OK','initializing':'INIT','failed':'FAIL','idle':'IDLE'}
            st = status_map.get(self.robot_init_status, self.robot_init_status)
            if self.robot_init_status == 'ok':
                st_color = (0,255,0)
            elif self.robot_init_status == 'initializing':
                st_color = (0,255,255)
            elif self.robot_init_status == 'failed':
                st_color = (0,0,255)
            else:
                st_color = (200,200,200)
            time_str = '' if self.robot_init_time == 0 else datetime.fromtimestamp(self.robot_init_time).strftime('%H:%M:%S')
            cv2.putText(img, f"机械臂:{st} {time_str}", (1430, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.8, st_color, 2)
        except Exception:
            pass

        # 湿度
        cv2.putText(img,str(round(uart.sensors.humi,1)),(1540, 235),cv2.FONT_HERSHEY_SIMPLEX,1,(233, 160, 0),3,)

        # 温度
        cv2.putText(img,str(round(uart.sensors.temp,1)),(1540, 295),cv2.FONT_HERSHEY_SIMPLEX,1,(233, 160, 0),3,)

        # 心率
        cv2.putText(img,str(uart.sensors.heartRate),(1540 if uart.sensors.heartRate-100<0 else 1535, 415),cv2.FONT_HERSHEY_SIMPLEX,1,(143, 193, 163),3)

        # 血氧饱和度
        cv2.putText(img,str(uart.sensors.sop2),(1560 if uart.sensors.sop2-100<0 else 1535, 493),cv2.FONT_HERSHEY_SIMPLEX,1.5,(143, 193, 163),3)

        # 判断手势序号
        if uart.sensors.ges.gesture == 1:self.gestur = 'UP'
        elif uart.sensors.ges.gesture == 2:self.gestur = 'DOWN'
        elif uart.sensors.ges.gesture == 3:self.gestur = 'LEFT'
        elif uart.sensors.ges.gesture == 4:self.gestur = 'RIGHT'
        elif uart.sensors.ges.gesture == -1:self.gestur = self.gestur
        else: self.gestur = 'None'
        uart.sensors.ges.gesture = -1

        # 手势序号
        cv2.putText(img,self.gestur,(1761, 355),cv2.FONT_HERSHEY_SIMPLEX,1.5,(0, 157, 222),3,)

        # 手势光强
        cv2.putText(img,str(uart.sensors.ges.gesBrightness),(1761, 418),cv2.FONT_HERSHEY_SIMPLEX,1,(0, 157, 222),3,)

        # 手势探测面积
        cv2.putText(img,str(uart.sensors.ges.gesAreaDet),(1761, 485),cv2.FONT_HERSHEY_SIMPLEX,1,(0, 157, 222),3)

        # X轴加速度
        cv2.putText(img,str(uart.sensors.imu.accx),(1457, 570),cv2.FONT_HERSHEY_SIMPLEX,1,(219, 150, 18),3)

        # X轴角速度
        cv2.putText(img,str(uart.sensors.imu.gyrox),(1617, 570),cv2.FONT_HERSHEY_SIMPLEX,1,(219, 150, 18),3)

        # Y轴加速度
        cv2.putText(img,str(uart.sensors.imu.accy),(1457, 645),cv2.FONT_HERSHEY_SIMPLEX,1,(219, 150, 18),3)

        # Y轴角速度
        cv2.putText(img,str(uart.sensors.imu.gyroy),(1617, 645),cv2.FONT_HERSHEY_SIMPLEX,1,(219, 150, 18),3)

        # Z轴加速度
        cv2.putText(img,str(uart.sensors.imu.accz),(1457, 710),cv2.FONT_HERSHEY_SIMPLEX,1,(219, 150, 18),3)

        # Z轴角速度
        cv2.putText(img,str(uart.sensors.imu.gyroz),(1617, 710),cv2.FONT_HERSHEY_SIMPLEX,1,(219, 150, 18),3)

        # 俯仰角
        cv2.putText(img,str(round(uart.sensors.imu.pitch,1)),(1460, 785),cv2.FONT_HERSHEY_SIMPLEX,0.9,(219, 150, 18),3)

        # 横滚角
        cv2.putText(img,str(round(uart.sensors.imu.roll,1)),(1620, 785),cv2.FONT_HERSHEY_SIMPLEX,0.9,(219, 150, 18),3)

        # 偏航角
        cv2.putText(img,str(round(uart.sensors.imu.yaw,1)),(1799, 785),cv2.FONT_HERSHEY_SIMPLEX,0.9,(219, 150, 18),3)

        # 键盘值
        cv2.putText(img,str(uart.sensors.keyCount),(1595, 918),cv2.FONT_HERSHEY_SIMPLEX,0.8,(68, 75, 123),3)

        # 如果旋钮被按下则清空数值
        if uart.sensors.knob.btnPress != 0:
            uart.sensors.knob.count = 0
            uart.sensors.knob.btnPress = 0

        # 旋钮值
        cv2.putText(img,str(uart.sensors.knob.count),(1620, 1018),cv2.FONT_HERSHEY_SIMPLEX,1,(68, 75, 123),3)

        # 如果按键A被按下则UI开关打开
        if self.button.buttonA == True:
            cv2.circle(img, (1800, 857), 20, (15, 37, 240), -1)
        elif self.button.buttonA == False:
            cv2.circle(img, (1873, 857), 20, (15, 37, 240), -1)

        # 如果按键B被按下则UI开关二打开
        if self.button.buttonB == True:
            cv2.circle(img, (1800, 939), 20, (77, 181, 224), -1)
        elif self.button.buttonB == False:
            cv2.circle(img, (1873, 939), 20, (77, 181, 224), -1)

        # 如果按键C被按下则UI开关三打开
        if self.button.buttonC == True:
            cv2.circle(img, (1800, 1022), 20, (157, 109, 83), -1)
        elif self.button.buttonC == False:
            cv2.circle(img, (1873, 1022), 20, (157, 109, 83), -1)

        # 控制继电器开关
        uart.setRelaySwitch(self.button.buttonA, self.button.buttonB, self.button.buttonC)

        # 按钮值
        if uart.sensors.btn.btnPressA != 0:
            self.button.buttonA = bool(1-self.button.buttonA)
            uart.sensors.btn.btnPressA = 0
            uart.sensors.btn.btnPressB = 0
            uart.sensors.btn.btnPressC = 0

        elif uart.sensors.btn.btnPressB != 0:
            self.button.buttonB = bool(1-self.button.buttonB)
            uart.sensors.btn.btnPressA = 0
            uart.sensors.btn.btnPressB = 0
            uart.sensors.btn.btnPressC = 0

        elif uart.sensors.btn.btnPressC != 0:
            self.button.buttonC = bool(1-self.button.buttonC)
            uart.sensors.btn.btnPressA = 0
            uart.sensors.btn.btnPressB = 0
            uart.sensors.btn.btnPressC = 0

        if uart.sensors.keyCount == 0:
            uart.sensors.keyCount = -1
            if self.speedTrans == 0.0:
                self.speedTrans = -0.02
            elif self.speedTrans != 0.0:
                self.speedTrans = 0.0
            uart.setTransSpeed(self.speedTrans)  # 控制传送台速度
        return img

'''
UT: 下位机传感器数据测试
'''
if __name__ == "__main__":
    # 开启数据接收串口
    # 使用 lib.uart 中的实现以便复用库函数
    uart = Uart("/dev/ttyUSB0")
    try:
        if hasattr(uart, 'serial') and uart.serial:
            uart.serial.close()
            time.sleep(0.5)
    except:
        pass
    
    try:
        uart.start()  # 开启串口通信接收子线程
    except Exception as e:
        print("[Error] 无法启动串口线程:", e)

    signal.signal(signal.SIGINT, uart.stop)  # 定义软件退出信号量

    # 开启摄像头，若 /dev/deepCamera 无法打开则回退到 /dev/video0 再回退到默认设备0
    capture = cv2.VideoCapture("/dev/deepCamera")


    capture.set(cv2.CAP_PROP_FPS, 50)  # 设置视频的读取速率
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    # 创建窗口
    cv2.namedWindow("Video", cv2.WINDOW_NORMAL)

    # 将窗口铺满屏幕
    cv2.setWindowProperty('Video', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    # 初始化面板数据显示类
    panel = Panel()

    time.sleep(1)#等待下位机初始化完成!
    # 使用 Panel 的方法初始化机械臂，避免在 Panel.__init__ 中直接触发硬件动作
    panel.init_robot_arm()  # 初始化机械臂位置

    # 预加载面板背景图，避免每帧从磁盘读取
    img_path = os.path.join(BASE_DIR, 'res', 'images', 'panel', 'AiBox.png')
    base_img = cv2.imread(img_path)
    if base_img is None:
        print('[Error] 读取实验箱图片失败:', img_path)
        base_img = np.zeros((1080, 1920, 3), dtype=np.uint8)
    else:
        base_img = cv2.resize(base_img, (1920, 1080))

    loop_counter = 0
    while uart.running:
        # 读取摄像头数据
        ret, frame = capture.read()

        # 检查是否成功读取视频帧
        if not ret:
            break

        frame = cv2.flip(frame, 1)  # 画面水平翻转
        
        # 新增：处理人脸关键点检测（按频率限制，减少主循环负载）
        try:
            face_interval = getattr(panel, 'face_interval', 3)
            if (loop_counter % face_interval) == 0:
                frame = panel.process_face_landmark(frame)
        except Exception as e:
            print('[Warning] 人脸检测出错:', e)

        # 新增：处理语音识别/合成（若检测到录音完成）
        try:
            if hasattr(panel, 'audioRecorder') and panel.audioRecorder.finish:
                res = panel.asr.speechRecognition()
                if len(res) > 0:
                    ttype, response = panel.wordsMatching.wordsMatching(res)
                    print("wordMatch:", ttype, "|", response)
                    if ttype == "chat":
                        audioPath = panel.ttsOnline.speechTransfer(response)
                        if audioPath:
                            panel.audioPlayer.playRadio(audioPath)
                panel.audioRecorder.finish = False
        except Exception as e:
            print("[Warning] 语音处理出错:", e)

        # 新增：让播放器在每次循环中尝试恢复音乐播放
        try:
            if hasattr(panel, 'audioPlayer'):
                panel.audioPlayer.autoResumeMusic()
        except Exception:
            pass

        uart.transmitSysHeart()  # 发送系统心跳
        uart.comStatusCheck()  # 通信连接状态检测
        img = base_img.copy()
        img = panel.showError(frame,img)  # 显示摄像头视频和错误代码提示
        img = panel.showData(img)# 显示传感器数据
        cv2.imshow("Video", img)
        key = cv2.waitKey(1) & 0xFF  # 按键处理（非阻塞）
        if key == 27:  # 按ESC退出程序
            break
        # 如果按下 t 则运行机械臂自检测试（避免在循环中阻塞的 input）
        if key == ord('t'):
            print("开始发送")
            try:
                uart.setArmAngle(1,500)
                time.sleep(0.5)
                print("finish init")
            except Exception as e:
                print(f"fail to init:{e}")
            print("开始发送单舵机中点角度命令（1..6）...")
            for sid in range(1, 7):
                try:
                    if hasattr(panel, 'servo_limits') and sid in panel.servo_limits:
                        mn, mx = panel.servo_limits[sid]
                        ang = (mn + mx) // 2
                    else:
                        ang = 500
                    try:
                        uart.setArmAngle(sid, ang)
                        print(f"已发送: setArmAngle({sid}, {ang})")
                    except Exception as e:
                        print(f"发送舵机 {sid} 命令失败: {e}")
                except Exception as e:
                    print(f"计算舵机 {sid} 角度失败: {e}")
                time.sleep(0.25)
            print("机械臂自检测试完成。")

            loop_counter += 1

            # 释放资源
    try:
        uart.robotArmMoveit(uart.robotArm.Movement.reset)
        time.sleep(1.0)
        uart.setTransSpeed(0.0)
        uart.setRelaySwitch(False, False, False)
        time.sleep(0.5)

    except Exception as e:
        print(f"warning, fail to clean up:{e}")

    uart.stop(0, 0)  # 串口线程退出
    time.sleep(0.5)
    capture.release()
    cv2.destroyAllWindows()
    print('finish cleaning up')