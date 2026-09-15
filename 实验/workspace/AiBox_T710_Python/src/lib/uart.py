#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@file          :uart.py
@Description   :串口通信(上下位机),协议编解码校验
@Date          :2023/07/12 14:38:53
@Autor         :Leo
@Version       :v1.0
"""
import threading
try:
    import serial
except Exception:
    serial = None
import time
import struct
import signal


# 通信地址定义
USB_FRAME_HEAD = bytes.fromhex("42")  # 通信序列帧头
USB_FRAME_LENMAX = 30  # 通信序列字节最长长度
USB_FRAME_LENMIN = 4  # 通信序列字节最短长度

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
        self.errorCode = 0  # 错误代码： 0~u32
        self.adcInfra = 0  # 红外距离: 0~65535
        self.rangeLaser = 0  # 激光距离: 0~65535
        self.humi = 0.0  # 湿度：
        self.temp = 0.0  # 温度：
        self.sop2 = 0  # 血氧饱和度：0~100%
        self.heartRate = 0  # 心率: 0~120次/分
        self.rfid = False    # 电磁数据
        self.co2 = 400  # co2浓度: 0~65535 ppm
        self.tvoc = 0  # tvoc浓度: 0~65535 mg/m3
        self.imu = self.Imu()  # 惯性传感器数据
        self.ges = self.Gesture()  # 手势传感器数据
        self.btn = self.Button()  # 按键时长
        self.knob = self.Knob()  # 旋转编码器
        self.illume = 0  # 光强: 0~65535
        self.adcMic = 0  # 音量: 0~65535
        self.rangeRadar = 0  # 毫米波距离
        self.keyCount = -1  # 键盘数值:0~999999999
        self.transSpeed = 0.0  # 传送台速度:-0.1~0.1m/s

    class Imu:
        """
        惯性传感器数据
        """

        def __init__(self):
            self.accx = 0  # X轴加速度: 0~65535
            self.accy = 0  # Y轴加速度: 0~65535
            self.accz = 0  # Z轴加速度: 0~65535
            self.gyrox = 0  # X轴角速度: 0~65535
            self.gyroy = 0  # Y轴角速度: 0~65535
            self.gyroz = 0  # Z轴角速度: 0~65535
            self.pitch = 0.0  # 俯仰角：-180.0°~180.0°
            self.roll = 0.0  # 翻滚角：-180.0°~180.0°
            self.yaw = 0.0  # 偏航角：-180.0°~180.0°

    class Gesture:
        """
        手势传感器数据
        """

        def __init__(self):
            self.gesture = 0  # 手势序号：1~9序号标识9中手势
            self.gesBrightness = 0  # 手势光强：0~255
            self.gesAreaDet = 0  # 手势探测面积：0~900

    class Button:
        """
        按键时长
        """

        def __init__(self):
            self.btnPressA = 0  # 按键时间:0~65535
            self.btnPressB = 0  # 按键时间:0~65535
            self.btnPressC = 0  # 按键时间:0~65535

    class Knob:
        """
        旋转编码器
        """

        def __init__(self):
            self.btnPress = 0  # 按键时间:0~65535
            self.count = 0  # 累计计数:0~65535


class RobotArm:
    """
    机械手臂
    """

    def __init__(self):
        self.action = False  # 动作组使能
        self.timeSpent = 0  # 动作组总耗时: ms
        self.timeStart = time.time()  # 记录动作组开始的系统时间: s(float)
        # 机械手臂动作: 直立
        self.actionStand = ([500, 125, 500, 500, 500, 490, 0],  # 动作1
                            [500, 500, 500]  # 补全错误信息
                            # 动作组（关节1, 关节2, 关节3, 关节4, 关节5, 关节6, 等待时长:ms）
                            )
        # 机械手臂动作: 拍照(传送台)
        self.actionPhotoTrans = ([500, 500, 470, 1000, 650, 500, 0],  # 动作1
                                #  [500, 500, 470, 1000, 650, 500, 1000],  # 动作: 爪子上升
                                #  [500, 500, 470, 1000, 650, 500, 0]  # 动作2
                                 # 动作组（关节1, 关节2, 关节3, 关节4, 关节5, 关节6,  等待时长:ms）
                                 )
        # 机械手臂动作: 抓取物品(传送台,距离机械臂近)
        self.actionGrapTransA = ([500, 500, 460, 1000, 700, 500, 1000],  # 动作: 张开爪子
                                 [500, 500, 110, 900, 700, 500, 1000],  # 动作: 到达物品位置
                                 [665, 500, 110, 900, 700, 500, 1000],  # 动作: 夹取物品
                                 [665, 500, 110, 900, 700, 500, 0],  # 动作: 升起
                                 # 动作组（关节1, 关节2, 关节3, 关节4, 关节5, 关节6,  等待时长:ms）
                                 )
        # 机械手臂动作: 抓取物品(传送台,距离机械臂远)
        self.actionGrapTransB = ([500, 500, 460, 1000, 700, 500, 1000],  # 动作: 张开爪子
                                 [500, 500, 120, 870, 640, 500, 1000],  # 动作: 到达物品位置
                                 [665, 500, 120, 870, 640, 500, 1000],  # 动作: 夹取物品
                                 [665, 500, 150, 870, 750, 500, 0],  # 动作: 升起
                                 # 动作组（关节1, 关节2, 关节3, 关节4, 关节5, 关节6,  等待时长:ms）
                                 )
        # 机械手臂动作: 放置物品(仓库A)
        self.actionPlaceSiteA = ([665, 500, 60, 720, 600, 930, 1000],  # 动作: 旋转到位置A
                                 [665, 500, 170, 870, 600, 930, 1000],  # 动作: 爪子下降
                                 [500, 500, 170, 870, 600, 930, 1000],  # 动作: 放置物品
                                 [500, 500, 60, 720, 600, 930, 0],  # 动作: 爪子上升
                                 # 动作组（关节1, 关节2, 关节3, 关节4, 关节5, 关节6,  等待时长:ms）
                                 )
        # 机械手臂动作: 放置物品(仓库B)
        self.actionPlaceSiteB = ([665, 500, 60, 720, 600, 830, 1000],  # 动作: 旋转到位置B
                                 [665, 500, 160, 870, 600, 830, 1000],  # 动作: 爪子下降
                                 [500, 500, 160, 870, 600, 830, 1000],  # 动作: 放置物品
                                 [500, 500, 50, 700, 600, 830, 0],  # 动作: 爪子上升
                                 # 动作组（关节1, 关节2, 关节3, 关节4, 关节5, 关节6,  等待时长:ms）
                                 )
        # 机械手臂动作: 放置物品(仓库C)
        self.actionPlaceSiteC = ([665, 500, 90, 700, 680, 960, 1000],  # 动作: 旋转到位置C
                                 [665, 500, 70, 870, 680, 960, 1000],  # 动作: 爪子下降
                                 [500, 500, 70, 870, 680, 960, 1000],  # 动作: 放置物品
                                 [500, 500, 90, 700, 680, 960, 0],  # 动作: 爪子上升
                                 # 动作组（关节1, 关节2, 关节3, 关节4, 关节5, 关节6,  等待时长:ms）
                                 )
        # 机械手臂动作: 放置物品(仓库D)
        self.actionPlaceSiteD = ([665, 500, 50, 700, 620, 820, 1000],  # 动作: 旋转到位置D
                                 [665, 500, 60, 820, 620, 820, 1000],  # 动作: 爪子下降
                                 [500, 500, 60, 820, 620, 820, 1000],  # 动作: 放置物品
                                 [500, 500, 50, 700, 620, 820, 0],  # 动作: 爪子上升
                                 # 动作组（关节1, 关节2, 关节3, 关节4, 关节5, 关节6,  等待时长:ms）
                                 )
        # 机械手臂动作: 放置物品(操作台)
        self.actionPlaceDesk = ([665, 500, 95, 800, 640, 130, 1500],  # 动作: 旋转到操作台
                                [665, 500, 95, 850, 640, 130, 1200],  # 动作: 爪子下降
                                [500, 500, 95, 850, 640, 130, 1000],  # 动作: 放置物品
                                [500, 500, 95, 800, 640, 130, 0],  # 动作: 爪子上升
                                # 动作组（关节1, 关节2, 关节3, 关节4, 关节5, 关节6,  等待时长:ms）
                                )
        # 机械手臂动作: 复位
        self.actionReset = ([665, 125, 500, 500, 400, 490, 1000],  # 动作: 旋转到操作台
                            [665, 125, 500, 500, 200, 490, 0],  # 动作: 爪子上升
                            # 动作组（关节1, 关节2, 关节3, 关节4, 关节5, 关节6,  等待时长:ms）
                            )

    class Movement:
        stand = 0  # 直立
        photoTrans = 1  # 拍照(传送台)
        grapTransA = 2  # 抓取物品(传送台,距离机械臂近)
        grapTransB = 3  # 抓取物品(传送台,距离机械臂远)
        placeSiteA = 9  # 放置物品(仓库A)
        placeSiteB = 10  # 放置物品(仓库B)
        placeSiteC = 11  # 放置物品(仓库C)
        placeSiteD = 12  # 放置物品(仓库D)
        placeDesk = 13  # 放置物品(操作台)
        reset = 14  # 机械臂复位(放置到传送台)


class Uart:
    """
    定义串口通信类
    """

    def __init__(self, port):
        """
        初始化串口
        """
        self.port = port  # 串口名称
        self.baudRate = 115200  # 波特率
        self.serial = None  # 初始化串口对象
        self.thread = None  # 串口线程
        self.threadHeart = None # 串口线程心跳
        self.running = False  # 串口是否运行
        self.recStart = False  # 数据接收开始标志
        self.recIndex = 0  # 接收序列号
        self.recFinish = False  # 接收并校验成功标志
        self.len = 0  # 帧长
        self.recBuff = [0] * USB_FRAME_LENMAX  # 临时接收数据区
        self.timeHart = time.time()  # 记录心跳信号发送时间：s(float)
        self.connect = False  # 通信连接标志
        self.timeDrop = time.time()  # 记录通信掉线时间
        self.sensors = Sensors()  # 初始化传感器数据类
        self.robotArm = RobotArm()  # 初始化机械手臂类

    def start(self):
        """
        开启串口通信接收子线程
        """
        self.serial = serial.Serial(
            self.port,
            int(self.baudRate),
            timeout=1,
            parity=serial.PARITY_NONE,
            stopbits=1,
        )
        # 创建子线程并启动
        self.thread = threading.Thread(target=self.serialThread)
        self.running = True
        print("[Info] uart receive thread start!")
        self.thread.start()

    
    def startHeart(self):
        """
        开启串口心跳子线程
        """
        # 创建子线程并启动
        self.threadHeart = threading.Thread(target=self.heartThread)
        print("[Info] uartHeart receive thread start!")
        self.threadHeart.start()

    def stop(self, signum, frame):
        """
        停止进程
        """
        self.setTransSpeed(0.0)  # 停止传送带转动
        self.setRelaySwitch(False, False, False)  # 关闭继电器
        self.robotArmMoveit(self.robotArm.Movement.reset)  # 机械臂复位(放置在传送台)
        # 停止子线程
        self.running = False
        self.thread.join()
        # 关闭串口
        if self.serial:
            self.serial.close()
        print("[Info] uart thread is closed!")
        print("[Info] 串口通信多线程停止, 停止运行传送台, 关闭继电器!!!")

    def serialThread(self):
        """
        串口接收多线程
        """
        time.sleep(0.5)
        # 判断串口是否运行
        while self.running:
            # 判断串口是否可读
            if self.serial.in_waiting > 0:
                data = self.serial.read(1)
                self.receiveHandle(data)

    def heartThread(self):
        """
        串口心跳发送多线程
        """
        time.sleep(0.5)
        # 判断串口是否运行
        while self.running:
            self.transmitSysHeart()

    def receiveHandle(self, data):
        """
        串口接收数据,协议校验
        """
        # 判断串口是否运行
        if self.running == False:
            return
        # 如果接收到的字节是帧头且串口没有开始接收
        if data == USB_FRAME_HEAD and not self.recStart:
            self.recStart = True
            self.recBuff[0] = data
            self.recBuff[2] = USB_FRAME_LENMIN
            self.recIndex = 1
        elif self.recIndex == 2:
            self.recBuff[2] = data
            self.recIndex += 1
            self.len = int.from_bytes(data, byteorder="big", signed=False)
            if self.len > USB_FRAME_LENMAX or self.len < USB_FRAME_LENMIN:  # 判断帧长是否合理
                self.recBuff[2] = USB_FRAME_LENMIN
                self.recIndex = 0
                self.recStart = False
        elif self.recStart and self.recIndex < USB_FRAME_LENMAX:  # 连续接收数据帧
            if data == USB_FRAME_HEAD and self.recIndex == 1:
                self.recIndex = 1
            else:
                self.recBuff[self.recIndex] = data
                self.recIndex += 1

        if (
            self.recIndex >= USB_FRAME_LENMAX or self.recIndex >= self.len
        ) and self.recIndex > USB_FRAME_LENMIN:
            check = int(0)  # 数据校验

            for i in range(self.len - 1):  # 校验和（Byte）
                check += int.from_bytes(self.recBuff[i],
                                        byteorder="big", signed=False)

            check = int(check % 256)
            if check == int.from_bytes(
                self.recBuff[self.len - 1], byteorder="big", signed=False
            ):  # 数据校验
                self.recFinish = True
                self.recIndex = 0
                self.recStart = False
                self.recLength = USB_FRAME_LENMAX
                self.timeDrop = time.time()  # 刷新通信掉线时间
                self.connect = True  # 通信连接成功标志
                self.transDataFrame()  # 接收成功，数据回响

    def transDataFrame(self):
        """
        串口通信帧数据解析,C语言与Python转换标准:
        ----------------------------------------------------------------
        字符    C类型	                Python类型	           标准大小
        x	    填充字节	            无对应值	             []3
        c	    char	                长度为1的bytes	         1
        b	    signed char	            integer	                1
        B	    unsigned char	        integer	                1
        ?	    _Bool	                bool	                1
        h	    short	                integer	                2
        H	    unsigned char	        integer	                2
        i	    int	                    integer	                4
        I	    unsigned int	        integer	                4
        l	    long	                integer	                4
        L	    unsigned long	        integer	                4
        q	    long long	            nteger	                8
        Q	    unsigned long long      integer	                8
        n	    ssize_t	                integer	                []4
        N	    size_t	                integer	                []4
        e	    []5	                    float	                2
        f	    float	                float	                4
        d	    double	                float	                8
        s	    char[]	                bytes	                []6
        p	    char[]	                bytes	                []7
        P	    void*	                integer	                []8
        -----------------------------------------------------------------
        """
        if self.recFinish:
            self.recFinish = False  # 数据转换完成
            if self.recBuff[1] == USB_ADDR_ERRORCODE:   # 错误代码
                self.sensors.errorCode = struct.unpack(
                    "H", self.recBuff[3] + self.recBuff[4],)[0]
            elif self.recBuff[1] == USB_ADDR_ODI:  # 血氧
                self.sensors.heartRate = int.from_bytes(
                    self.recBuff[3], byteorder="big", signed=False
                )
                self.sensors.sop2 = int.from_bytes(
                    self.recBuff[4], byteorder="big", signed=False
                )
            elif self.recBuff[1] == USB_ADDR_BUTTON:  # 按键
                if self.recBuff[3] == bytes.fromhex("01"):  # 按键A
                    self.sensors.btn.btnPressA = struct.unpack(
                        "H", self.recBuff[4] + self.recBuff[5],)[0]  # 按下时长
                elif self.recBuff[3] == bytes.fromhex("02"):  # 按键B
                    self.sensors.btn.btnPressB = struct.unpack(
                        "H", self.recBuff[4] + self.recBuff[5],)[0]  # 按下时长
                elif self.recBuff[3] == bytes.fromhex("03"):  # 按键C
                    self.sensors.btn.btnPressC = struct.unpack(
                        "H", self.recBuff[4] + self.recBuff[5],)[0]  # 按下时长

            elif self.recBuff[1] == USB_ADDR_INFRA:  # 红外距离
                self.sensors.adcInfra = struct.unpack(
                    "H", self.recBuff[3] + self.recBuff[4],)[0]
            elif self.recBuff[1] == USB_ADDR_LASER:  # 激光测距
                self.sensors.rangeLaser = struct.unpack(
                    "H",
                    self.recBuff[3] + self.recBuff[4],)[0]
            elif self.recBuff[1] == USB_ADDR_THI:  # 温度湿度
                self.sensors.humi = struct.unpack(
                    "f", self.recBuff[3] + self.recBuff[4] + self.recBuff[5] + self.recBuff[6],)[0]  # 湿度
                self.sensors.temp = struct.unpack(
                    "f", self.recBuff[7] + self.recBuff[8] + self.recBuff[9] + self.recBuff[10],)[0]  # 温度
            elif self.recBuff[1] == USB_ADDR_IMU_EULER:  # IMU姿态角数据
                self.sensors.imu.pitch = struct.unpack(
                    "f", self.recBuff[3] + self.recBuff[4] + self.recBuff[5] + self.recBuff[6],)[0]  # 俯仰角
                self.sensors.imu.roll = struct.unpack(
                    "f", self.recBuff[7] + self.recBuff[8] + self.recBuff[9] + self.recBuff[10],)[0]  # 横滚角
                self.sensors.imu.yaw = struct.unpack(
                    "f", self.recBuff[11] + self.recBuff[12] + self.recBuff[13] + self.recBuff[14],)[0]  # 偏航角
            elif self.recBuff[1] == USB_ADDR_IMU_ACC:  # IMU原始数据
                self.sensors.imu.accx = struct.unpack(
                    "h", self.recBuff[3] + self.recBuff[4],)[0]  # X轴加速度
                self.sensors.imu.accy = struct.unpack(
                    "h", self.recBuff[5] + self.recBuff[6],)[0]  # Y轴加速度
                self.sensors.imu.accz = struct.unpack(
                    "h", self.recBuff[7] + self.recBuff[8],)[0]  # Z轴加速度
                self.sensors.imu.gyrox = struct.unpack(
                    "h", self.recBuff[9] + self.recBuff[10],)[0]  # X轴角速度
                self.sensors.imu.gyroy = struct.unpack(
                    "h", self.recBuff[11] + self.recBuff[12],)[0]  # Y轴角速度
                self.sensors.imu.gyroz = struct.unpack(
                    "h", self.recBuff[13] + self.recBuff[14],)[0]  # Z轴角速度
            elif self.recBuff[1] == USB_ADDR_RFID:  # 电磁感应
                self.sensors.rfid = True
            elif self.recBuff[1] == USB_ADDR_AQI:  # 空气质量
                self.sensors.co2 = struct.unpack(
                    "H", self.recBuff[3] + self.recBuff[4],)[0]  # co2浓度
                if self.sensors.co2 < 400:
                    self.sensors.co2 = 400
                elif self.sensors.co2 > 999:
                    self.sensors.co2 = 999
                self.sensors.tvoc = struct.unpack(
                    "H", self.recBuff[5] + self.recBuff[6],)[0]  # tvoc浓度
                if self.sensors.tvoc < 0:
                    self.sensors.tvoc = 0
                elif self.sensors.tvoc > 999:
                    self.sensors.tvoc = 999
            elif self.recBuff[1] == USB_ADDR_GES:  # 手势检测
                gesture = int.from_bytes(
                    self.recBuff[3], byteorder="big", signed=False)  # 手势序号
                if gesture >= 1 and gesture <= 9:
                    self.sensors.ges.gesture = gesture
                self.sensors.ges.gesBrightness = int.from_bytes(
                    self.recBuff[4], byteorder="big", signed=False)  # 光强
                self.sensors.ges.gesAreaDet = struct.unpack(
                    "H", self.recBuff[5] + self.recBuff[6],)[0]  # 探测面积
            elif self.recBuff[1] == USB_ADDR_CLI:  # 光强
                self.sensors.illume = struct.unpack(
                    "H", self.recBuff[3] + self.recBuff[4],)[0]  # 光照强度
            elif self.recBuff[1] == USB_ADDR_MIC:  # 音量测量
                self.sensors.adcMic = struct.unpack(
                    "H", self.recBuff[3] + self.recBuff[4],)[0]  # 音量
            elif self.recBuff[1] == USB_ADDR_RADAR:  # 毫米波
                self.sensors.rangeRadar = struct.unpack(
                    "H", self.recBuff[3] + self.recBuff[4],)[0]  # 距离
            elif self.recBuff[1] == USB_ADDR_KEYBOARD:  # 矩阵键盘
                self.sensors.keyCount = struct.unpack(
                    "I", self.recBuff[3] + self.recBuff[4] + self.recBuff[5] + self.recBuff[6],)[0]  # 键值
            elif self.recBuff[1] == USB_ADDR_KNOB_NUM:  # 旋钮累计值
                self.sensors.knob.count = struct.unpack(
                    "h", self.recBuff[3] + self.recBuff[4],)[0]
            elif self.recBuff[1] == USB_ADDR_KNOB_BTN:  # 旋钮按键时长
                self.sensors.knob.btnPress = struct.unpack(
                    "H", self.recBuff[3] + self.recBuff[4],)[0]
                self.sensors.knob.count = 0  # 收到旋钮按键, 清除累计数据
            elif self.recBuff[1] == USB_ADDR_TRANS:  # 传送台速度
                self.sensors.transSpeed = struct.unpack(
                    "f", self.recBuff[3] + self.recBuff[4] + self.recBuff[5] + self.recBuff[6],)[0]  # 传送台速度

    def transmitFrame(self, addr, data):
        """
        串口发送帧数据转换
        addr: 通信地址
        data: 数据流
        """
        # 判断串口是否运行
        if self.running == False:
            return

        if data == None:
            frame = (
                USB_FRAME_HEAD  # 帧头
                + addr  # 地址
                + (4).to_bytes(1, byteorder="little", signed=False))  # 帧长
        elif len(data) > 0:
            frame = (
                USB_FRAME_HEAD  # 帧头
                + addr  # 地址
                + (len(data) + 4).to_bytes(1,
                                           byteorder="little", signed=False)  # 帧长
                + data  # 数据
            )

        check = int(0)
        for i in frame:
            check += i
            check = int(check % 256)
        frame = frame + check.to_bytes(1, byteorder="little", signed=False)
        self.serial.write(frame + bytes.fromhex("00"))

    def setTransSpeed(self, speed):
        """
        传送台速度控制
        speed: -0.1~0.1m/s
        """
        if speed > 0.1:  # 限制传送台最大速度=0.1m/s
            print("[Warning] 限制传送台最大速度0.1m/s,当前设置速度:", str(speed), "m/s")
            speed = 0.1
        elif speed < -0.1:  # 限制传送台最大速度=0.1m/s
            print("[Warning] 限制传送台最大速度-0.1m/s,当前设置速度:", str(speed), "m/s")
            speed = -0.1

        self.transmitFrame(USB_ADDR_TRANS, struct.pack("<f", speed))

    def setBuzzerAudio(self, audio):
        """
        蜂鸣器音效设置
        audio=1: 确认/OK
        audio=2: 报警/Warnning
        audio=3: 完成/Finish
        audio=4: 提示/Ding
        audio=5: 开机/Systemstart
        """
        if audio < 1 or audio > 5:
            print("[Error] 蜂鸣器音效设置错误,请选择1~5种模式!")
            return
        self.transmitFrame(USB_ADDR_BUZZER, struct.pack("<B", audio))

    def setArmAngle(self, id, angle):
        """
        设置机械臂的角度
        id: 舵机ID号(至下而上1~6)
        angle: 角度(0~1000表示0~240°)
        """
        if id < 1 or id > 6:
            print("[Error] 机械臂ID输入错误, 当前ID: ", str(id))
            return
        if angle < 0 or angle > 1000:
            print("[Error] 机械臂角度输入错误, 当前角度: ", str(angle))
            return
        stream = struct.pack("<B", id) + struct.pack("<H", angle)
        self.transmitFrame(USB_ADDR_ARM_SERVO, stream)

    def setArmActions(self, actions):
        """
        设置机械臂的动作组(最多10组动作)
        actions: 动作组(0~1000表示0~240°)
        """
        self.robotArm.timeSpent = 0  # 动作组累计耗时: ms
        for i in range(len(actions)):
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
                self.robotArm.timeSpent += actions[i][6]  # 统计时长
                self.robotArm.timeSpent += 300  # 增加每组动作的冗余时长
                stream = struct.pack("<B", i+1) + struct.pack("<H", actions[i][0]) + struct.pack("<H", actions[i][1]) + struct.pack("<H", actions[i][2]) + struct.pack(
                    "<H", actions[i][3]) + struct.pack("<H", actions[i][4]) + struct.pack("<H", actions[i][5]) + struct.pack("<H", actions[i][6])
                self.transmitFrame(USB_ADDR_ARM_ACTIONS, stream)
                time.sleep(0.03)  # Delay 30ms防止下位机数据解析错误
                self.robotArm.timeStart = time.time()  # 记录动作组开始的系统时间: s(float)

    def getArmActionsBusy(self):
        """
        获取机械手臂动作组状态(True/False: 繁忙/空闲)
        """
        thisTime = time.time()
        # 动作组总耗时检测
        if (thisTime - self.robotArm.timeStart)*1000 > self.robotArm.timeSpent:
            return False
        else:
            return True

    def robotArmMoveit(self, action):
        """
        机械手臂动作控制
        """
        # 直立
        if action == self.robotArm.Movement.stand:
            self.setArmActions(self.robotArm.actionStand)
        # 传送台拍照
        elif action == self.robotArm.Movement.photoTrans:
            self.setArmActions(self.robotArm.actionPhotoTrans)
        # 抓取物品(传送台,距离机械臂近)
        elif action == self.robotArm.Movement.grapTransA:
            self.setArmActions(self.robotArm.actionGrapTransA)
        # 抓取物品(传送台,距离机械臂远)
        elif action == self.robotArm.Movement.grapTransB:
            self.setArmActions(self.robotArm.actionGrapTransB)
        # 放置物品(仓库A)
        elif action == self.robotArm.Movement.placeSiteA:
            self.setArmActions(self.robotArm.actionPlaceSiteA)
        # 放置物品(仓库B)
        elif action == self.robotArm.Movement.placeSiteB:
            self.setArmActions(self.robotArm.actionPlaceSiteB)
        # 放置物品(仓库C)
        elif action == self.robotArm.Movement.placeSiteC:
            self.setArmActions(self.robotArm.actionPlaceSiteC)
        # 放置物品(仓库D)
        elif action == self.robotArm.Movement.placeSiteD:
            self.setArmActions(self.robotArm.actionPlaceSiteD)
        # 放置物品(操作台)
        elif action == self.robotArm.Movement.placeDesk:
            self.setArmActions(self.robotArm.actionPlaceDesk)
        # 复位(放置传送台上)
        elif action == self.robotArm.Movement.reset:
            self.setArmActions(self.robotArm.actionReset)

    def setRgbColors(self, colorA, colorB, colorC, colorD, colorE):
        """
        设置RGB灯的颜色
        color: 灯珠颜色(0~0xFFFFFF表示一种颜色,24色)
        """
        # 灯珠A的颜色
        colorA = bytes(struct.pack("<I", colorA))
        colorA = [colorA[i:i+3] for i in range(0, len(colorA), 3)][0]  # 取低24位
        # 灯珠B的颜色
        colorB = bytes(struct.pack("<I", colorB))
        colorB = [colorB[i:i+3] for i in range(0, len(colorB), 3)][0]
        # 灯珠C的颜色
        colorC = bytes(struct.pack("<I", colorC))
        colorC = [colorC[i:i+3] for i in range(0, len(colorC), 3)][0]
        # 灯珠D的颜色
        colorD = bytes(struct.pack("<I", colorD))
        colorD = [colorD[i:i+3] for i in range(0, len(colorD), 3)][0]
        # 灯珠E的颜色
        colorE = bytes(struct.pack("<I", colorE))
        colorE = [colorE[i:i+3] for i in range(0, len(colorE), 3)][0]

        self.transmitFrame(USB_ADDR_RGB_NOR,
                           colorA + colorB+colorC+colorD+colorE)

    def setRgbBlink(self, time):
        """
        设置RGB灯为闪烁模式(灯珠颜色同 "setRgbColors")
        time: 闪烁时间间隔(ms) >50ms
        """
        if time <= 50:
            print("[Error] RGB灯闪烁间隔时长输入错误, 当前频率: ", str(time), "ms")
            return
        self.transmitFrame(USB_ADDR_RGB_BLINK, struct.pack("<H", time))

    def setRgbFlow(self, time):
        """
        设置RGB灯为流水灯模式(灯珠颜色同 "setRgbColors")
        time: 流水时间间隔(ms) >50ms
        """
        if time < 50:
            print("[Error] RGB灯流水间隔时长输入错误, 当前频率: ", str(time), "ms")
            return
        self.transmitFrame(USB_ADDR_RGB_FLOW, struct.pack("<H", time))

    def setRelaySwitch(self, relayA, relayB, relayC):
        """
        设置继电器开断
        relay: True/False → 开/关
        """
        relay = 0
        if relayA:
            relay |= 1
        if relayB:
            relay |= 2
        if relayC:
            relay |= 4
        self.transmitFrame(USB_ADDR_RELAY, struct.pack("<B", relay))

    def setDotScale(self, dot, scale):
        """
        设置LED点阵显示音阶图案
        dot: LED点阵编号(1/2/3 → 左/右/全部)
        scale: buff[8] / 从左到右8组LED音阶高度数据(数据=0~8) scale = [1, 3, 5, 7, 7, 5, 3, 1]
        """
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
        """
        设置LED点阵显示常规图案
        dot: LED点阵编号(1/2/3 → 左/右/全部)
        scale: buff[8] / 从左到右8组LED每列8颗灯珠是否亮二进制 (数据=0~255)image = [255, 255, 255, 255, 255, 255, 255, 255]
        """
        if dot < 1 or dot > 3:
            print("[Error] LED点阵编号输入错误!!!")
            return
        stream = struct.pack("<B", dot)
        for i in range(0, 8):
            stream += struct.pack("<B", image[i])

        self.transmitFrame(USB_ADDR_DOT_NOR, stream)

    def transmitSysHeart(self):
        """
        发送系统心跳(下位机掉线检测时间5s, 掉线后不主动上传数据)
        """
        thisTime = time.time()  # 获取系统时间：s(float)
        if thisTime - self.timeHart > 1:  # 自动1s发送一次心跳信号
            self.transmitFrame(USB_ADDR_HEART, None)
            self.timeHart = thisTime

    def comStatusCheck(self):
        """
        通信连接状态检测(5秒掉线检测)
        """
        if self.connect:
            thisTime = time.time()  # 获取系统时间：s(float)
            if thisTime - self.timeDrop > 5:  # 5s掉线检测
                self.connect = False

    def systemReset(self):
        """
        系统复位(灯光等外设复位)
        """
        self.transmitFrame(USB_ADDR_RESET, None)

"""
串口通信测试
"""
if __name__ == "__main__":
    # 串口通信
    uart = Uart("/dev/ttyUSB0")
    uart.start()
    signal.signal(signal.SIGINT, uart.stop)  # 定义软件退出信号量

    index = 0
    while uart.running:
        uart.transmitSysHeart()  # 发送心跳信号
        time.sleep(0.2)
        # index += 1
        # if index == 10:
        #     uart.robotArmMoveit(uart.robotArm.Movement.stand)
        #     print("机械手臂控制")

        if index == 0:
            uart.robotArmMoveit(uart.robotArm.Movement.photoTrans)  # 机械手臂动作控制
            index += 1
        elif index == 1:
            if not uart.getArmActionsBusy():  # 获取机械手臂动作组状态
                uart.robotArmMoveit(
                    uart.robotArm.Movement.grapTransB)  # 机械手臂动作控制
                index += 1
        elif index == 2:
            if not uart.getArmActionsBusy():  # 获取机械手臂动作组状态
                uart.robotArmMoveit(
                    uart.robotArm.Movement.placeDesk)  # 机械手臂动作控制
                index += 1
        elif index == 3:
            if not uart.getArmActionsBusy():  # 获取机械手臂动作组状态
                uart.robotArmMoveit(
                    uart.robotArm.Movement.photoTrans)  # 机械手臂动作控制
                index += 1
