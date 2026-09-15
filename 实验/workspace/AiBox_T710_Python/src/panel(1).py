#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@file       : panel.py
@Description: 串口通信数据面板（整合人脸关键点检测）
@Date       : 2023/07/11 15:40:53
@Autor      : Hjc
@Version    : v1.0
"""
import os
import time
# Use shared UART implementation and utilities from lib
from lib.uart import Uart
from lib.utils import res_path, project_root
import cv2
from PIL import Image, ImageFont, ImageDraw
import numpy as np
import json
import base64
from urllib.request import urlopen, Request
from urllib.error import URLError
from urllib.parse import urlencode, quote_plus
import urllib.error
import random
import pygame
import signal
import pyaudio
import keyboard
import wave

# The inlined UART/constants and sensor/robot classes were removed to avoid duplication.
# Use the authoritative implementation in `src/lib/uart.py` instead.

# short helper: repo root
BASE_DIR = project_root()

# Inline UART implementation removed — use `lib.uart.Uart` from `src/lib/uart.py` instead.
# If you need a local replacement, prefer creating a helper in `src/lib/simulators.py`.

# --- uart 内联结束 ---
import cv2

# --- uart 内联结束 ---
import cv2
import time
from datetime import datetime
from ai.objectDetection import *
import os
import sys
from PIL import Image, ImageDraw, ImageFont
import numpy as np
import signal
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),"./faceDetection")))
# 新增：导入人脸关键点检测类
from faceLandmark import FaceKeyPoint

# --- 从 lib/speech.py 整合过来的依赖与类 ---
import pyaudio
import wave
import keyboard
import os
# 基准路径（项目根目录），使用 lib.utils.project_root() 初始化的 BASE_DIR
import random
import pygame
from pygame.locals import *
from urllib.request import urlopen, Request
from urllib.error import URLError
from urllib.parse import urlencode, quote_plus
import json
import urllib.error
import base64

# 百度语音API密钥（如需请替换）
BAIDU_API_KEY = "X298nO3hPZzk7e5NN8TeteEU"
BAIDU_SECRET_KEY = "04azSdARexpX9LYFeVqNAVpAuN7cpJZh"


class AudioRecorder:
    def __init__(self, savePath):
        if savePath == None:
            self.savePath = res_path('res','audio','record','temp.wav')
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
            self.audioPath = res_path('res','audio','record','temp.wav')
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
            self.musicFolder = "../res/audio/music"
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
            keyboard.on_press_key("m", lambda _: self.toggleMusic())
            keyboard.on_press_key("enter", lambda _: self.pauseMusic())
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

    def toggleMusic(self):
        """
        切换播放/暂停：如果未播放则开始播放，否则在播放/暂停之间切换
        """
        if not self.enable:
            return
        if not getattr(self, 'audio_available', False):
            return
        if not self.musicing:
            self.playMusic()
            return
        if self.pause:
            self.resumeMusic()
        else:
            self.pauseMusic()

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
            self.jsonPath = "../res/config/interaction.json"
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
            self.audioPath = res_path('res','audio','tts','temp.mp3')
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
        # 使用项目根路径构造资源路径，兼容在实验箱上运行
        try:
            self.font = ImageFont.truetype(res_path('res','utils','QingNingYouYuan.ttf'), 30)
        except Exception:
            self.font = ImageFont.load_default()

        # 初始化人脸关键点检测模型（使用 res_path）
        self.face_detector = FaceKeyPoint(
            res_path('res','models','faceDetection'),
            res_path('res','models','faceLandmark')
        )
        self.face_threshold = 0.5  # 人脸检测置信度阈值
        # 语音模块初始化（从 lib/speech.py 整合），资源路径使用 res_path
        try:
            self.audioRecorder = AudioRecorder(None)
            self.audioPlayer = AudioPlayer(None)
            self.asr = AsrOnline(None)
            self.ttsOnline = TtsOnline(None)
            self.wordsMatching = WordsMatching(res_path('res','config','interaction.json'))
        except Exception as e:
            print("[Warning] 语音模块初始化失败:", e)

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
        # 1. 进行人脸检测
        face_res = self.face_detector.detector.render(frame)
        
        # 2. 进行关键点检测
        landmark_res = self.face_detector.render(frame, face_res, self.face_threshold)
        
        # 3. 绘制检测结果（方框和关键点）
        frame_with_landmark = self.face_detector.drawBox(frame, landmark_res)
        
        return frame_with_landmark

    def showError(self, frame, img):
        """
        显示错误代码信息
        """
        if uart.sensors.errorCode !=0:
            errorLogo = cv2.imread(res_path('res','images','panel','errorcode.png'))
            errorLogo = cv2.resize(errorLogo,(158,158))
            img[28:28+158,229:229+158] = errorLogo  # 绘制错误代码标志

            errorCode = uart.sensors.errorCode    # 接收错误代码
            if errorCode > 0:
                for i in range(11, -1, -1):        # 遍历错误代码
                    if errorCode - 2**i >= 0:
                        errorCode = errorCode - 2**i
                        self.error[i] = 1
                    else:
                        self.error[i] = 0

            frame = Image.fromarray(frame)  # 将数组转换成图像
            draw = ImageDraw.Draw(frame)    # 创建绘图对象

            for i in range(12):
                if self.error[i]:  # 打印光强传感器错误提示
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

                    draw.text((30, 30*i+20), txt, font=self.font, fill=(0, 0, 255))  # 显示文本

            frame = np.array(frame)  # 将图片转换为数组格式
        img[200:200+480,597:597+640] = frame        # 将视频绘制到实验箱图片上
        return img

    def showData(self, img):
        """
        显示串口接收到的数据
        """
        # 检测串口数据是否正常发送
        if uart.connect:
            connect = cv2.imread(res_path('res','images','panel','data.png'))
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
    uart = Uart("/dev/ttyUSB0")
    uart.start()#开启串口通信接收子线程
    signal.signal(signal.SIGINT, uart.stop)  # 定义软件退出信号量

    # 开启摄像头
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
    uart.robotArmMoveit(uart.robotArm.Movement.photoTrans)  # 初始化机械臂位置
    while uart.running:
        # 读取摄像头数据
        ret, frame = capture.read()

        # 检查是否成功读取视频帧
        if not ret:
            break

        frame = cv2.flip(frame, 1)  # 画面水平翻转
        
        # 新增：处理人脸关键点检测
        frame = panel.process_face_landmark(frame)

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
        img_path = res_path('res','images','panel','AiBox.png')
        img = cv2.imread(img_path)  # 读取实验箱图片
        if img is None:
            print('[Error] 读取实验箱图片失败:', img_path)
            # 创建一张空白底图以避免后续 resize 失败
            img = np.zeros((1080, 1920, 3), dtype=np.uint8)
        else:
            img = cv2.resize(img, (1920, 1080))  # 调整图片大小
        img = panel.showError(frame,img)  # 显示摄像头视频和错误代码提示
        img = panel.showData(img)# 显示传感器数据
        cv2.imshow("Video", img)
        if cv2.waitKey(1) == 27:  # 按ESC退出程序
            break

    # 释放资源
    uart.stop(0, 0)  # 串口线程退出
    capture.release()
    cv2.destroyAllWindows()