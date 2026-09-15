#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.panel6666 import Uart

def test_simple_arm():
    print("=== 简单机械臂测试开始 ===")
    
    try:
        # 创建Uart实例
        uart = Uart('/dev/ttyUSB0')
        
        # 初始化串口
        uart.start()
        print("串口初始化成功")
        time.sleep(1)
        
        # 启动心跳线程
        uart.startHeart()
        time.sleep(0.5)
        
        # 测试系统重置
        print("执行系统重置...")
        uart.systemReset()
        time.sleep(2)
        
        # 测试单个舵机控制（更详细的调试信息）
        print("\n=== 测试单个舵机控制 ===")
        servo_id = 1
        test_angles = [400, 600, 500]
        
        for angle in test_angles:
            print(f"\n控制舵机 {servo_id} 到角度 {angle}")
            # 构建数据并打印（手动调试）
            import struct
            data = struct.pack(">B", servo_id) + struct.pack(">H", angle)
            print(f"手动构建数据: {data.hex()}")
            # 调用setArmAngle
            uart.setArmAngle(servo_id, angle)
            time.sleep(2)  # 等待舵机移动
        
        # 测试动作组控制
        print("\n=== 测试动作组控制 (stand) ===")
        uart.robotArmMoveit(uart.robotArm.Movement.stand)
        
        # 等待动作完成
        while uart.getArmActionsBusy():
            print("动作执行中...")
            time.sleep(1)
        
        print("动作执行完成")
        
        print("\n=== 简单机械臂测试完成 ===")
        
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
    test_simple_arm()