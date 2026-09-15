#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys
import os
import time
import struct

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.panel9999 import Panel


def test_robot_arm():
    print("=== 机械臂综合测试开始 ===")
    
    try:
        # 创建Panel实例
        panel = Panel()
        
        # 初始化串口
        if not panel.initSerial():
            print("串口初始化失败，无法继续测试")
            return
        
        print("串口初始化成功")
        time.sleep(0.5)
        
        print("=== 测试1：单个舵机控制 ===")
        # 测试舵机1
        servo_id = 1
        angles = [300, 700, 500]
        
        for angle in angles:
            print(f"设置舵机 {servo_id} 到角度 {angle}")
            panel.setArmAngle(servo_id, angle)
            time.sleep(2)  # 等待舵机移动
        
        time.sleep(1)
        
        print("=== 测试2：动作组控制 - stand ===")
        print("执行stand动作")
        panel.robotArmMoveit(panel.robotArm.Movement.stand)
        
        # 等待动作完成
        while panel.getArmActionsBusy():
            print("动作执行中...")
            time.sleep(0.5)
        
        print("动作执行完成")
        time.sleep(1)
        
        print("=== 测试3：动作组控制 - reset ===")
        print("执行reset动作")
        panel.robotArmMoveit(panel.robotArm.Movement.reset)
        
        # 等待动作完成
        while panel.getArmActionsBusy():
            print("动作执行中...")
            time.sleep(0.5)
        
        print("动作执行完成")
        
        print("=== 机械臂综合测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
    finally:
        # 清理资源
        if 'panel' in locals():
            panel.serialThread.stop()
            panel.heartThread.stop()
            panel.serial.close()


if __name__ == "__main__":
    test_robot_arm()
