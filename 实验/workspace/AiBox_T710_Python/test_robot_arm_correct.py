#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys
import os
import time

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.panel6666 import Uart


def test_robot_arm():
    print("=== 机械臂综合测试开始 ===")
    
    try:
        # 创建Uart实例（正确的串口通信类）
        uart = Uart('/dev/ttyUSB0')
        
        # 初始化串口
        uart.start()
        print("串口初始化成功")
        time.sleep(1)  # 给串口一些初始化时间
        
        # 启动心跳线程
        uart.startHeart()
        time.sleep(0.5)
        
        print("=== 测试1：单个舵机控制 ===")
        # 测试舵机1
        servo_id = 1
        angles = [300, 700, 500]
        
        for angle in angles:
            print(f"设置舵机 {servo_id} 到角度 {angle}")
            uart.setArmAngle(servo_id, angle)
            time.sleep(3)  # 等待舵机移动
        
        time.sleep(2)
        
        print("=== 测试2：动作组控制 - stand ===")
        print("执行stand动作")
        uart.robotArmMoveit(uart.robotArm.Movement.stand)
        
        # 等待动作完成
        while uart.getArmActionsBusy():
            print("动作执行中...")
            time.sleep(0.5)
        
        print("动作执行完成")
        time.sleep(2)
        
        print("=== 测试3：动作组控制 - reset ===")
        print("执行reset动作")
        uart.robotArmMoveit(uart.robotArm.Movement.reset)
        
        # 等待动作完成
        while uart.getArmActionsBusy():
            print("动作执行中...")
            time.sleep(0.5)
        
        print("动作执行完成")
        
        print("=== 机械臂综合测试完成 ===")
        
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
    test_robot_arm()