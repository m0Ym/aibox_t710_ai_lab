#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@file          :test_full_functionality.py
@Description   :完整功能测试脚本
@Date          :2023/12/24
@Author        :AI Assistant
@Version       :v1.0
"""
import time
import sys
import os

# 添加src目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from panel6666 import Panel

def test_full_functionality():
    print("=" * 50)
    print("开始机械臂完整功能测试")
    print("=" * 50)
    
    panel = Panel()
    
    try:
        # 1. 测试串口初始化
        print("\n1. 测试串口初始化...")
        if not panel.initSerial():
            print("[ERROR] 串口初始化失败")
            return False
        print("[SUCCESS] 串口初始化成功")
        
        # 2. 测试系统复位
        print("\n2. 测试系统复位...")
        panel.systemReset()
        print("[SUCCESS] 系统复位命令发送成功")
        time.sleep(2)
        
        # 3. 测试单个舵机控制
        print("\n3. 测试单个舵机控制...")
        print("   控制舵机1到500位置")
        panel.setArmAngle(servo_id=1, angle=500)
        time.sleep(1)
        print("[SUCCESS] 单个舵机控制命令发送成功")
        
        # 4. 测试机械臂动作组控制
        print("\n4. 测试机械臂动作组控制...")
        print("   执行直立动作")
        panel.robotArmMoveit(panel.robotArm.Movement.stand)
        print("[SUCCESS] 动作组命令发送成功")
        
        # 5. 测试心跳信号（间接测试）
        print("\n5. 测试心跳信号...")
        print("   等待3秒，观察是否有心跳相关日志")
        time.sleep(3)
        print("[INFO] 心跳测试完成")
        
        # 6. 测试传感器数据接收
        print("\n6. 测试传感器数据接收...")
        print("   等待2秒，观察是否有传感器数据接收")
        time.sleep(2)
        # 尝试获取一些传感器数据
        print(f"   红外传感器值: {panel.sensors.adcInfra}")
        print(f"   温度值: {panel.sensors.temp}")
        print(f"   湿度值: {panel.sensors.humi}")
        print("[INFO] 传感器数据接收测试完成")
        
        print("\n" + "=" * 50)
        print("所有功能测试完成！")
        print("=" * 50)
        return True
        
    except Exception as e:
        print(f"\n[ERROR] 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # 7. 测试串口关闭
        print("\n7. 测试串口关闭...")
        panel.close()
        print("[SUCCESS] 串口关闭成功")

if __name__ == "__main__":
    test_full_functionality()