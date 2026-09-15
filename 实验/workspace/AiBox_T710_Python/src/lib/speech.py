#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@file          :speech.py
@Description   :在线语音识别(ASR)+语音合成(TTS)
@Date          :2023/07/23 11:29:42
@Autor         :Leo
@Version       :v1.0
'''
import pyaudio
import wave
import keyboard
import os
import random
import pygame
from pygame.locals import *
from urllib.request import urlopen
from urllib.request import Request
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.parse import quote_plus
import json
import urllib.error
import base64

# 百度语音API密钥
BAIDU_API_KEY = "X298nO3hPZzk7e5NN8TeteEU"
# 百度语音安全密钥
BAIDU_SECRET_KEY = "04azSdARexpX9LYFeVqNAVpAuN7cpJZh"

"""
语音录制类
"""


class AudioRecorder:
    def __init__(self, savePath):
        if savePath == None:
            self.savePath = "/root/Desktop/workspace/AiBox_T710_Python/res/audio/record/temp.wav"  # 录音文件存放地址
        else:
            self.savePath = savePath
        self.sampleRate = 16000  # 采样率,语音信号的频率范围通常更窄（低于8000Hz）
        self.channels = 1  # 音频声道数量
        self.width = 2  # 音频量化位数: 16位
        self.driveIndex = 1  # 麦克驱动号
        self.chunk = 1024  # 缓存中存放帧数
        self.recording = False  # 正在录音标志
        self.frames = []  # 录音数据列表
        self.finish = False  # 录音结束标志
        self.audio = pyaudio.PyAudio()  # 创建音频类实例
        self.stream = None  # 创建音频流对象
        keyboard.on_press_key(
            "space", lambda _: self.startRecord())  # 空格键按下开始录音
        keyboard.on_release_key(
            "space", lambda _: self.stopRecord())  # 释放空格键停止录音
        print("[Info] 按键录制音频程序启动!")

    """
    音频录制
    """

    def AudioRecording(self, audio, count, time, status):
        if self.recording:
            self.frames.append(audio)  # 将音频帧添加到列表中
        return (audio, pyaudio.paContinue)

    """
    开始录音使能
    """

    def startRecord(self):
        if not self.recording:
            print("开始录音...")
            self.frames = []  # 清空音频帧列表
            self.finish = False  # 清录音完成标志
            self.stream = self.audio.open(  # 创建音频流对象
                rate=self.sampleRate,
                format=self.audio.get_format_from_width(self.width),
                channels=self.channels,
                input=True,
                input_device_index=self.driveIndex,
                frames_per_buffer=self.chunk,
                stream_callback=self.AudioRecording)
            self.recording = True

    """
    停止录音并保存音频文件
    """

    def stopRecord(self):
        if self.recording:
            self.recording = False
            self.stream.stop_stream()  # 停止音频流录制
            self.stream.close()

            file = wave.open(self.savePath, 'wb')  # 保存音频文件
            file.setnchannels(self.channels)
            file.setsampwidth(self.audio.get_sample_size(
                self.audio.get_format_from_width(self.width)))
            file.setframerate(self.sampleRate)
            file.writeframes(b''.join(self.frames))
            file.close()
            self.finish = True  # 录音完成!

"""
在线语音识别
"""


class AsrOnline:
    def __init__(self, audioPath):
        self.apiKey = BAIDU_API_KEY  # 百度语音API密钥
        self.secretKey = BAIDU_SECRET_KEY  # 百度语音安全密钥
        if audioPath == None:
            self.audioPath = "/root/Desktop/workspace/AiBox_T710_Python/res/audio/record/temp.wav"  # 录音文件存放地址
        else:
            self.audioPath = audioPath
        self.cuid = '123456PYTHON'
        self.scope = 'audio_voice_assistant_get'  # 云端API语音功能类型
        print("[Info] 在线语音识别功能已启动!")

    """
    语音识别(调用本地音频录制文件)
    return: str: 识别结果
    """

    def speechRecognition(self):

        token = self.fetchToken()  # 获取云端token信息
        if not token:
            return ""

        audio = []  # 音频流数据
        with open(self.audioPath, 'rb') as file:  # 打开本地录音文件
            audio = file.read()

        if len(audio) == 0:
            print('file %s length read 0 bytes' % self.audioPath)  # 音频文件为空
            return ""

        speech = base64.b64encode(audio)  # 格式转换
        speech = str(speech, 'utf-8')  # 中文格式
        params = {'dev_pid': 1537,  # 选择语言及识别模型, DEV_PID=1537: 普通话
                  # "lm_id" : LM_ID,    #测试自训练平台开启此项
                  'format': self.audioPath[-3:],  # 文件格式：pcm/wav/amr，极速版增加m4a格式
                  'rate': 16000,  # 音频采样率(固定频率)
                  'token': token,
                  'cuid': self.cuid,
                  'channel': 1,  # 音频通道数
                  'speech': speech,
                  'len': len(audio)
                  }
        request = json.dumps(params, sort_keys=False)  # 发送请求数据
        response = Request('http://vop.baidu.com/server_api',
                           request.encode('utf-8'))
        response.add_header('Content-Type', 'application/json')
        try:
            result = urlopen(response)
            resAsr = result.read()
        except URLError as err:
            print('asr http response http code : ' + str(err.code))
            resAsr = err.read()

        resAsr = str(resAsr, 'utf-8')
        resJson = json.loads(resAsr)    # 解析JSON数据
        try:
            resAsr = resJson["result"][0]   # 解析语音识别字符
            print("ASR: ", resAsr)
        except KeyError:
            print("[Error] 获取云端识别数据失败, 未检索到result字段")

        return resAsr

    """
    获取云端token信息
    return: False: 账户检验失败, str: token信息
    """

    def fetchToken(self):
        params = {'grant_type': 'client_credentials',
                  'client_id': self.apiKey,
                  'client_secret': self.secretKey}
        request = urlencode(params).encode('utf-8')
        response = Request('http://aip.baidubce.com/oauth/2.0/token',
                           request)  # 获取云端API信息

        try:
            file = urlopen(response)
            result = file.read()
        except urllib.error.HTTPError as err:
            print('token http response http code : ' + str(err.code))
            result = err.read()
        except URLError as err:
            print('token http response http code : ' + str(err.code))
            result = err.read()

        res = json.loads(result.decode())
        if ('access_token' in res.keys() and 'scope' in res.keys()):
            # self.scope = False 忽略检查
            if self.scope and (not self.scope in res['scope'].split(' ')):
                print('[Error] ASR scope is not correct!')
                return False
            return res['access_token']
        else:
            print(
                '[Error] MAYBE API_KEY or SECRET_KEY not correct: access_token or scope not found in token response!')
            return False

"""
音频播放器
"""


class AudioPlayer:
    def __init__(self, musicFolder):
        if musicFolder == None:
            self.musicFolder = "/root/Desktop/workspace/AiBox_T710_Python/res/audio/music"  # 音乐文件存放目录
        else:
            self.musicFolder = musicFolder
        self.musicIndex = 0  # 音乐播放序号
        self.playlist = os.listdir(self.musicFolder)  # 音乐播放列表
        self.musicing = False  # 音乐播放状态
        self.radioing = False  # 当前播放内容: 广播
        self.musicPos = 0  # 记录音乐播放进度
        self.enable = False  # 播放器使能：播放列表>0
        self.volume = 0.5  # 音量
        self.pause = False  # 音频是否人为操作暂停
        if len(self.playlist) > 0:  # 检查播放列表是否为空
            self.enable = True
        keyboard.on_press_key("right", lambda _: self.nextMusic())  # 键盘右键:下一首
        keyboard.on_press_key(
            "left", lambda _: self.previousMusic())  # 键盘左键:上一首
        keyboard.on_press_key("up", lambda _: self.turnUpVolume())  # 键盘上键:增加音量
        keyboard.on_press_key(
            "down", lambda _: self.turnDownVolume())  # 键盘下键:降低音量
        keyboard.on_press_key(
            "space", lambda _: self.pauseMusic())  # 空格键按下暂停播放
        keyboard.on_release_key(
            "space", lambda _: self.resumeMusic())  # 释放空格键继续播放
        keyboard.on_press_key("m", lambda _: self.toggleMusic())  # m键 切换播放/暂停
        keyboard.on_press_key(
            "enter", lambda _: self.pauseMusic())  # 回车键停止播放音乐

        pygame.init()  # 系统播放器初始化
        self.setVolume(self.volume)  # 设置初始化音量
        print("[Info] 音乐播放程序启动!")

    """
    设置播放音量: 0.0 ~ 1.0
    """

    def setVolume(self, volume):
        self.volume = volume
        pygame.mixer.music.set_volume(volume)   # 设置系统音量

    """
    开始播放音乐(随机开始播放)
    """

    def playMusic(self):
        if not self.enable:
            print("[Error] 播放失败, 播放列表为空!")
        if not pygame.mixer.get_init():
            pygame.mixer.init()  # 初始化声音混合器

        self.musicIndex = random.randint(0, len(self.playlist)-1)  # 随机选取音乐
        pygame.mixer.music.load(os.path.join(
            self.musicFolder, self.playlist[self.musicIndex]))  # 加载音乐文件
        pygame.mixer.music.play()  # 开始播放
        self.musicing = True

    def toggleMusic(self):
        """
        切换播放/暂停：如果未播放则开始播放，否则在播放/暂停之间切换
        """
        if not self.enable:
            return
        if not self.musicing:
            self.playMusic()
            return
        # 如果处于人为暂停状态则恢复，否则暂停
        if self.pause:
            self.resumeMusic()
        else:
            self.pauseMusic()

    """
    暂停播放音乐
    """

    def pauseMusic(self):
        if self.musicing and not self.radioing:  # 当前仅播放音乐
            if not pygame.mixer.get_init():
                pygame.mixer.init()  # 初始化声音混合器
            pygame.mixer.music.pause()
            self.pause = True  # 人为操作暂停播放
        elif self.radioing:  # 正在播放广播
            self.radioing = False  # 广播结束
            if not pygame.mixer.get_init():
                pygame.mixer.init()  # 初始化声音混合器
            pygame.mixer.music.pause()
            self.pause = True  # 人为操作暂停播放

    """
    继续播放音乐
    """

    def resumeMusic(self):
        if self.musicing and not self.radioing:  # 当前仅播放音乐
            if not pygame.mixer.get_init():
                pygame.mixer.init()  # 初始化声音混合器
            # pygame.time.wait(100)  # 等待语音识别/合成
            pygame.mixer.music.unpause()
            self.pause = False  # 解除人为操作暂停
        elif self.radioing:  # 正在播放广播
            self.pause = False  # 解除人为操作暂停

    """
    停止播放音乐
    """

    def stopMusic(self):
        if not pygame.mixer.get_init():
            pygame.mixer.init()  # 初始化声音混合器
        pygame.mixer.music.stop()
        self.musicing = False

    """
    播放下一首音乐
    """

    def nextMusic(self):
        if not self.enable:
            print("[Error] 播放失败, 播放列表为空!")

        self.pause = True  # 人为操作暂停
        if not pygame.mixer.get_init():
            pygame.mixer.init()  # 初始化声音混合器

        if self.musicIndex >= len(self.playlist) - 1:
            self.musicIndex = 0
        else:
            self.musicIndex += 1
        pygame.mixer.music.load(os.path.join(
            self.musicFolder, self.playlist[self.musicIndex]))  # 加载音乐文件
        pygame.mixer.music.play()  # 开始播放
        self.musicing = True
        self.pause = False  # 解除人为操作暂停

    """
    播放上一首音乐
    """

    def previousMusic(self):
        if not self.enable:
            print("[Error] 播放失败, 播放列表为空!")

        self.pause = True  # 人为操作暂停
        if not pygame.mixer.get_init():
            pygame.mixer.init()  # 初始化声音混合器

        if self.musicIndex <= 0:
            self.musicIndex = len(self.playlist) - 1
        else:
            self.musicIndex -= 1
        pygame.mixer.music.load(os.path.join(
            self.musicFolder, self.playlist[self.musicIndex]))  # 加载音乐文件
        pygame.mixer.music.play()  # 开始播放
        self.musicing = True
        self.pause = False  # 解除人为操作暂停

    """
    增加播放音量
    """

    def turnUpVolume(self):
        if self.volume > 1.0:
            self.volume = 1.0  # 音量
        else:
            self.volume += 0.1  # 音量
        self.setVolume(self.volume)  # 设置系统播放音量

    """
    降低播放音量
    """

    def turnDownVolume(self):
        if self.volume <= 0:
            self.volume = 0.0  # 音量
        else:
            self.volume -= 0.1  # 音量
        self.setVolume(self.volume)  # 设置系统播放音量

    """
    播放广播音频
    audioPath: 音频文件路径
    """

    def playRadio(self, audioPath):
        self.pause = True  # 人为操作暂停
        if self.musicing:  # 音乐正在播放中
            self.musicPos = pygame.mixer.music.get_pos()  # 获取播放进度
        if not pygame.mixer.get_init():
            pygame.mixer.init()  # 初始化声音混合器

        pygame.mixer.music.load(audioPath)  # 加载音频文件
        pygame.mixer.music.play()  # 开始播放
        self.radioing = True  # 添加广播播放标志
        self.pause = False  # 解除人为操作暂停

    """
    自动恢复音乐播放(广播完成后),实时工作
    """

    def autoResumeMusic(self):
        if self.pause:  # 人为操作暂停音频
            return
        if self.musicing and not self.radioing:  # 仅在播放音乐
            if not pygame.mixer.music.get_busy():
                self.nextMusic()  # 下一首
        elif not self.musicing and self.radioing:  # 仅在播放广播
            if not pygame.mixer.music.get_busy():
                self.radioing = False  # 广播结束
        elif self.musicing and self.radioing:  # 广播和音乐同时播放
            if not pygame.mixer.music.get_busy():
                self.radioing = False  # 广播结束
                # 恢复当前音乐进度继续播放
                if not self.enable:
                    print("[Error] 播放失败, 播放列表为空!")
                if not pygame.mixer.get_init():
                    pygame.mixer.init()  # 初始化声音混合器
                pygame.mixer.music.load(os.path.join(
                    self.musicFolder, self.playlist[self.musicIndex]))  # 加载音乐文件
                pygame.mixer.music.play(self.musicPos)  # 设置播放进度
                self.musicing = True




"""
字符串检索(基于Json文件)
"""


class WordsMatching:
    def __init__(self, jsonPath):
        if jsonPath == None:
            self.jsonPath = "/root/Desktop/workspace/AiBox_T710_Python/res/config/interaction.json"  # Json文件路径
        else:
            self.jsonPath = jsonPath  # Json文件路径
        self.jsonStream = None  # Json数据流
        if os.path.exists(self.jsonPath):
            with open(self.jsonPath, 'r') as file:  # 打开Json文件
                str = file.read()
            self.jsonStream = json.loads(str)
        else:
            print("[Error] 字符匹配Json文件路径错误!")
            return

    """
    字符检索(关键字)
    return: json[type][item]
            1) control,response
            2) chat,response
    """

    def wordsMatching(self, str):
        if self.jsonStream == None:  # 数据库加载失败!
            return

        # control交互类型
        for contrl in self.jsonStream["control"]:
            if len(self.jsonStream["control"][contrl]) > 1:
                for item in self.jsonStream["control"][contrl]["keyword"]:
                    if str.__contains__(item):
                        # 返回type,数据
                        return "control", self.jsonStream["control"][contrl]["response"]
        # chat对话类型
        for chat in self.jsonStream["chat"]:
            if len(self.jsonStream["chat"][chat]) > 1:
                for item in self.jsonStream["chat"][chat]["keyword"]:
                    if str.__contains__(item):
                        # 获取chat内容的长度
                        jsonLen = len(
                            self.jsonStream["chat"][chat]["response"])
                        if jsonLen > 0:  # 对话内容非空
                            randomChat = random.randint(0, jsonLen-1)  # 回复随机内容
                            # 返回type,数据
                            return "chat", self.jsonStream["chat"][chat]["response"][randomChat]

        return "", ""


"""
文字合成语音(百度在线语音库)
"""


class TtsOnline:
    def __init__(self, audioPath):
        if audioPath == None:
            self.audioPath = "/root/Desktop/workspace/AiBox_T710_Python/res/audio/tts/temp.mp3"  # 语音合成文件存放地址
        else:                           
            self.audioPath = audioPath  # 语音合成文件存放地址
        self.apiKey = BAIDU_API_KEY  # 百度语音API密钥
        self.secretKey = BAIDU_SECRET_KEY  # 百度语音安全密钥
        self.cuid = '123456PYTHON'
        self.scope = 'audio_voice_assistant_get'  # 云端API语音功能类型
        self.person = 0  # 播音员: 1)基础音库：0:度小美，1:度小宇，3为度逍遥，4为:度丫丫;
        # 2)精品音库：5:度小娇，103:度米朵，106:度博文，110:度小童，111:度小萌，默认:度小美
        self.speed = 6  # 语速，取值0-15，默认为5中语速
        self.pitch = 5  # 音调，取值0-15，默认为5中语调
        self.volume = 5  # 音量，取值0-9，默认为5中音量
        self.format = 3  # 语音文件格式(3：mp3(default) 4： pcm-16k 5： pcm-8k 6. wav)
        print("[Info] 在线语音合成功能已启动!")
    """
    获取云端token信息
    return: False: 账户检验失败, str: token信息
    """

    def fetchToken(self):
        params = {'grant_type': 'client_credentials',
                  'client_id': self.apiKey,
                  'client_secret': self.secretKey}
        request = urlencode(params).encode('utf-8')
        response = Request('http://aip.baidubce.com/oauth/2.0/token',
                           request)  # 获取云端API信息

        try:
            file = urlopen(response)
            result = file.read()
        except urllib.error.HTTPError as err:
            print('token http response http code : ' + str(err.code))
            result = err.read()
        except URLError as err:
            print('token http response http code : ' + str(err.code))
            result = err.read()

        res = json.loads(result.decode())
        if ('access_token' in res.keys() and 'scope' in res.keys()):
            # self.scope = False 忽略检查
            if self.scope and (not self.scope in res['scope'].split(' ')):
                print('[Error] ASR scope is not correct!')
                return False
            return res['access_token']
        else:
            print(
                '[Error] MAYBE API_KEY or SECRET_KEY not correct: access_token or scope not found in token response!')
            return False

    """
    在线语音合成
    """

    def speechTransfer(self, text):
        token = self.fetchToken()  # 获取云端token信息
        if not token:
            return False

        text = quote_plus(text)  # 两次编码
        params = {'tok': token, 'tex': text, 'per': self.person, 'spd': self.speed, 'pit': self.pitch,
                  'vol': self.volume, 'aue': self.format, 'cuid': self.cuid, 'lan': 'zh', 'ctp': 1}  # lan ctp 固定参数
        data = urlencode(params)
        response = Request('http://tsn.baidu.com/text2audio',
                           data.encode('utf-8'))  # 发送请求                                  数据
        error = False
        try:
            res = urlopen(response)
            result = res.read()
            headers = dict((name.lower(), value)
                           for name, value in res.headers.items())
            error = ('content-type' not in headers.keys()
                     or headers['content-type'].find('audio/') < 0)
        except URLError as err:
            print('asr http response http code : ' + str(err.code))
            result = err.read()
            error = True

        if not error:  # 语音合成成功!
            with open(self.audioPath, 'wb') as file:
                file.write(result)
            return self.audioPath
        else:
            return False


"""
UT: 单元测试
"""
if __name__ == "__main__":
    audioRecorder = AudioRecorder(None)  # 启动按键录音功能
    audioPlayer = AudioPlayer(None)  # 启动音乐播放功能
          
    asrOnlie = AsrOnline(None)  # 实例化在线语音识别功能的类，默认参数None
    ttsOnline = TtsOnline(None)  # 实例化文字合成语音功能的类，默认参数为None
    wordsMatching = WordsMatching(None)  # 实例化字符串检索功能的类，默认参数为None

    while True:
        if audioRecorder.finish:  # 录音完成
            res = asrOnlie.speechRecognition()  # 启动在线语音识别
            if len(res) > 0:  # 语音识别结果有效
                type, response = wordsMatching.wordsMatching(res)
                print("wordMatch: ", type, " | ", response)
                if type == "chat":
                    audioPath = ttsOnline.speechTransfer(response)  # 在线语音合成mp3
                    if audioPath != False:  # 语音合成成功
                        audioPlayer.playRadio(audioPath)  # 立即播放语音
            audioRecorder.finish = False  # 清录音完成标志

        audioPlayer.autoResumeMusic()  # 自动切换音频播放状态
