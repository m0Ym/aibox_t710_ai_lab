#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys
import os
import time
import serial
import struct

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.panel6666 import USB_ADDR_ARM_SERVO, USB_FRAME_HEAD

def calculate_checksum(frame):
    """计算校验和"""
    checksum = 0
    for byte in frame:
        checksum = (checksum + byte) & 0xFF
    return checksum

def send_servo_command(ser, servo_id, angle):
    """直接发送舵机控制命令到串口"""
    # 构建数据部分：舵机ID(1字节) + 角度(2字节)
    data = struct.pack(">B", servo_id) + struct.pack(">H", angle)
    
    # 计算帧长度：帧头(1) + 地址(1) + 长度(1) + 数据(n) = 3 + n
    frame_length = len(data) + 3
    
    # 构建帧头部分：帧头 + 地址 + 长度
    frame_header = USB_FRAME_HEAD + USB_ADDR_ARM_SERVO + frame_length.to_bytes(1, byteorder='big')
    
    # 完整帧（帧头 + 数据）
    frame = frame_header + data
    
    # 计算校验和
    checksum = calculate_checksum(frame)
    
    # 最终发送的帧：完整帧 + 校验和 + 00结束字节
    final_frame = frame + checksum.to_bytes(1, byteorder='big') + bytes.fromhex('00')
    
    print(f"\n发送舵机{servo_id}角度{angle}的命令：")
    print(f"  数据部分: {data.hex()}")
    print(f"  帧长度: {frame_length}")
    print(f"  帧头部分: {frame_header.hex()}")
    print(f"  完整帧(无校验): {frame.hex()}")
    print(f"  校验和: {checksum:02X}")
    print(f"  最终发送帧: {final_frame.hex()}")
    print(f"  发送字节数: {len(final_frame)}")
    
    # 发送数据
    try:
        bytes_sent = ser.write(final_frame)
        ser.flush()
        print(f"  实际发送字节数: {bytes_sent}")
        return True
    except Exception as e:
        print(f"  发送失败: {e}")
        return False

def test_single_servo():
    print("=== 单个舵机直接控制测试开始 ===")
    
    serial_port = '/dev/ttyUSB0'
    baud_rate = 115200
    
    try:
        # 打开串口
        ser = serial.Serial(serial_port, baud_rate, timeout=1)
        print(f"成功打开串口: {serial_port}")
        
        # 测试系统重置
        print("\n=== 发送系统重置命令 ===")
        reset_addr = bytes.fromhex("38")
        reset_frame = USB_FRAME_HEAD + reset_addr + b'\x03'  # 无数据帧，长度3
        reset_checksum = calculate_checksum(reset_frame)
        reset_final = reset_frame + reset_checksum.to_bytes(1, byteorder='big') + bytes.fromhex('00')
        print(f"发送重置命令: {reset_final.hex()}")
        ser.write(reset_final)
        ser.flush()
        time.sleep(2)  # 等待系统重置完成
        
        # 测试舵机1的多个角度
        print("\n=== 测试舵机1的角度控制 ===")
        servo_id = 1
        angles = [300, 700, 500]  # 测试的角度值
        
        for angle in angles:
            success = send_servo_command(ser, servo_id, angle)
            if success:
                print(f"  命令发送成功，等待3秒让舵机移动...")
                time.sleep(3)
            else:
                print(f"  命令发送失败")
        
        # 测试舵机2
        print("\n=== 测试舵机2的角度控制 ===")
        servo_id = 2
        angles = [400, 600, 500]
        
        for angle in angles:
            success = send_servo_command(ser, servo_id, angle)
            if success:
                print(f"  命令发送成功，等待3秒让舵机移动...")
                time.sleep(3)
            else:
                print(f"  命令发送失败")
        
        print("\n=== 单个舵机直接控制测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 关闭串口
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print(f"已关闭串口: {serial_port}")

if __name__ == "__main__":
    test_single_servo()