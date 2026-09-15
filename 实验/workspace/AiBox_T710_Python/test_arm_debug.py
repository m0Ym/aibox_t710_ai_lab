#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys
import os
import time
import serial

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.panel6666 import Uart, USB_ADDR_ARM_SERVO, USB_ADDR_ARM_ACTIONS, USB_FRAME_HEAD

def test_arm_debug():
    print("=== 机械臂详细调试测试开始 ===")
    
    try:
        # 1. 直接测试串口连接
        print("\n1. 测试串口连接...")
        test_serial = serial.Serial('/dev/ttyUSB0', 115200, timeout=1)
        if test_serial.is_open:
            print("串口直接打开成功!")
            test_serial.close()
        else:
            print("串口直接打开失败!")
        
        # 2. 创建Uart实例并详细调试
        print("\n2. 创建Uart实例...")
        uart = Uart('/dev/ttyUSB0')
        
        # 3. 初始化串口并验证
        print("\n3. 初始化串口...")
        uart.start()
        time.sleep(1)
        
        if uart.serial is not None and uart.serial.is_open:
            print("Uart串口初始化成功!")
            print(f"串口端口: {uart.serial.port}")
            print(f"波特率: {uart.serial.baudrate}")
        else:
            print("Uart串口初始化失败!")
            return
        
        # 4. 启动心跳线程
        print("\n4. 启动心跳线程...")
        uart.startHeart()
        time.sleep(0.5)
        
        # 5. 手动构建并发送舵机控制命令（最底层调试）
        print("\n5. 手动构建并发送舵机控制命令...")
        servo_id = 1
        angle = 500
        
        # 构建原始数据
        import struct
        data = struct.pack(">B", servo_id) + struct.pack(">H", angle)
        print(f"原始数据: {data.hex()}")
        print(f"数据长度: {len(data)} 字节")
        
        # 构建完整的UART帧
        frame_length = len(data) + 3  # 帧头+地址+长度+数据
        print(f"帧长度: {frame_length}")
        
        # 构建帧
        frame = USB_FRAME_HEAD + USB_ADDR_ARM_SERVO + frame_length.to_bytes(1, byteorder='big') + data
        print(f"构建的帧(无校验): {frame.hex()}")
        
        # 计算校验和
        checksum = 0
        for byte in frame:
            checksum = (checksum + byte) & 0xFF
        print(f"校验和: {checksum:02X}")
        
        # 完整帧（包含校验和和结束字节）
        full_frame = frame + checksum.to_bytes(1, byteorder='big') + bytes.fromhex('00')
        print(f"完整帧(含校验和): {full_frame.hex()}")
        print(f"完整帧长度: {len(full_frame)} 字节")
        
        # 直接使用serial发送（绕过Uart类的方法）
        print("\n6. 直接使用serial发送命令...")
        try:
            bytes_sent = uart.serial.write(full_frame)
            uart.serial.flush()
            print(f"发送成功! 发送了 {bytes_sent} 字节")
            print(f"发送的字节: {full_frame.hex()}")
        except Exception as e:
            print(f"直接发送失败: {e}")
        
        # 等待并检查是否有响应
        print("\n7. 检查响应...")
        time.sleep(1)
        if uart.serial.in_waiting > 0:
            response = uart.serial.read(uart.serial.in_waiting)
            print(f"接收到响应: {response.hex()}")
        else:
            print("没有收到响应")
        
        # 8. 测试多个舵机
        print("\n8. 测试多个舵机...")
        for servo_id in range(1, 7):
            print(f"\n控制舵机 {servo_id} 到角度 500")
            uart.setArmAngle(servo_id, 500)
            time.sleep(1)
        
        # 9. 测试系统重置
        print("\n9. 测试系统重置...")
        uart.systemReset()
        time.sleep(2)
        
        print("\n=== 机械臂详细调试测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # 清理资源
        if 'uart' in locals():
            uart.running = False
            if uart.serial:
                uart.serial.close()

if __name__ == "__main__":
    test_arm_debug()