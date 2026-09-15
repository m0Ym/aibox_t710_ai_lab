import struct
import pytest
import sys
import os
# Ensure 'src' is on PYTHONPATH so 'lib' package can be imported during tests
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from lib.uart import Uart, USB_ADDR_ODI, USB_ADDR_TRANS, USB_FRAME_HEAD


class DummySerial:
    def __init__(self):
        self.last_write = None

    def write(self, data):
        self.last_write = data


def test_transDataFrame_odi_parsing():
    uart = Uart(port=None)
    # Prepare a fake recBuff where addr==USB_ADDR_ODI and payload heartRate=60, sop2=100
    uart.recBuff = [b'\x00'] * 30
    uart.recBuff[1] = USB_ADDR_ODI
    uart.recBuff[3] = bytes([60])
    uart.recBuff[4] = bytes([100])
    uart.len = 6  # arbitrary len >= needed
    uart.recFinish = True

    uart.transDataFrame()

    assert uart.sensors.heartRate == 60
    assert uart.sensors.sop2 == 100


def test_transmitFrame_writes_correct_checksum():
    uart = Uart(port=None)
    uart.running = True
    dummy = DummySerial()
    uart.serial = dummy

    data = struct.pack('<f', 0.05)
    addr = USB_ADDR_TRANS
    uart.transmitFrame(addr, data)

    # Reconstruct expected frame
    length = (len(data) + 4).to_bytes(1, byteorder='little', signed=False)
    frame = USB_FRAME_HEAD + addr + length + data
    check = sum(frame) % 256
    expected = frame + bytes([check]) + b'\x00'

    assert dummy.last_write == expected
