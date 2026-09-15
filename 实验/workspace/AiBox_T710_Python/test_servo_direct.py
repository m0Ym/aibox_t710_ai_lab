#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys
import os
import time
import struct
import serial
import threading

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.panel9999 import USB_FRAME_HEAD, USB_ADDR_ARM_SERVO


def transmit_frame(ser, addr, data):
    """直接发送数据帧到串口"""
    # 构建帧头+地址+长度+数据
    if data is None:
        frame_length = 4  # 帧头(1) + 地址(1) + 长度(1) + 校验和(1) = 4
        frame = USB_FRAME_HEAD + addr
    else:
        frame_length = len(data) + 3  # 帧头(1) + 地址(1) + 长度(1) + 数据(n) = 3 + n
        frame = USB_FRAME_HEAD + addr + data
    
    # 添加长度字段
    frame = frame[:2] + struct.pack(">B", frame_length) + frame[2:]
    
    # 计算校验和
    checksum = sum(frame) & 0xFF
    
    # 完整帧：帧头+地址+长度+数据+校验和+00
    full_frame = frame + struct.pack(">B", checksum) + b'\x00'
    
    print(f"发送帧: {full_frame.hex()}")
    
    # 发送数据
    ser.write(full_frame)
    ser.flush()


def test_single_servo_direct():
    print("=== 直接单个舵机测试开始 ===")
    
    try:
        # 直接打开串口
        ser = serial.Serial(
            port='/dev/ttyUSB0',  # 根据实际情况修改串口
            baudrate=115200,
            timeout=1,
            parity=serial.PARITY_NONE,
            stopbits=1
        )
        
        print("串口打开成功")
        time.sleep(0.5)
        
        # 测试单个舵机
        servo_id = 1  # 测试舵机1
        angles = [300, 700, 500]  # 测试的角度值
        
        for angle in angles:
            print(f"设置舵机 {servo_id} 到角度 {angle}")
            
            # 构建数据流：舵机ID(1字节) + 角度(2字节，大端)
            data = struct.pack(">B", servo_id) + struct.pack(">H", angle)
            
            # 发送数据帧
            transmit_frame(ser, USB_ADDR_ARM_SERVO, data)
            
            time.sleep(2)  # 等待舵机移动
        
        print("=== 直接单个舵机测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
    finally:
        # 关闭串口
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("串口已关闭")


if __name__ == "__main__":
    test_single_servo_direct()
