#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@file          :tracking.py
@Description   :目标跟踪
@Date          :2023/07/31 10:25:47
@Autor         :Hjc
@Version       :v1.0
'''
import numpy as np
import cv2
from time import time
from numba import jit

"""
目标选择类
"""

class SelectTarget:
    def __init__(self):
        self.selectingObject = False        # 初始化选取对象
        self.initTracking = False           # 初始化跟踪
        self.tracking = False               # 初始化行进间跟踪
        self.lossing = False                # 目标丢失
        self.originX, self.originY = -1, -1 # 初始化起点坐标
        self.endX, self.endY = -1, -1       # 初始化终点坐标
        self.width, self.height = 0, 0      # 初始化宽度和高度
        self.displayWidth, self.displayHeight = 150, 150 # 重叠显示区域的大小
        self.duration = 0.01                # 持续时间
        self.boxedImage = None              # 初始化被框圈出的图像

    """
    鼠标控制
    """
    def mouseControl(self, event, x, y, flags, param):
        # 事件 按下鼠标左键
        if event == cv2.EVENT_LBUTTONDOWN:
            self.selectingObject = True      # 选取对象
            self.tracking = False          # 行进间跟踪
            self.originX, self.originY = x, y# 记录起点
            self.endX, self.endY = x, y      # 初始化终点

        # 事件 鼠标移动
        elif event == cv2.EVENT_MOUSEMOVE:
            # 记录终点
            self.endX, self.endY = x, y

        # 释放鼠标左键
        elif event == cv2.EVENT_LBUTTONUP:
            self.selectingObject = False   # 不再选取对象
            # 过滤较小的选区
            if (abs(x - self.originX) > 10 and abs(y - self.originY) > 10):
                self.width, self.height = abs(x - self.originX), abs(y - self.originY)
                self.originX, self.originY = min(x, self.originX), min(y, self.originY)
                self.initTracking = True # 初始化跟踪
                # 将被框圈出的图像保存到变量中
                self.boxedImage = frame[self.originY:self.originY+self.height, self.originX:self.originX+self.width].copy()
            else:
                self.tracking = False  # 结束行进间跟踪

        # 按下鼠标右键
        elif event == cv2.EVENT_RBUTTONDOWN:
            self.tracking = False    # 结束行进间跟踪
            if (self.width > 0):
                self.originX, self.originY = x - self.width // 2, y - self.height // 2
                self.initTracking = True
    """
    状态显示
    根据当前状态进行图像绘制
    """
    def showState(self, tracker, frame):
        displayX = frame.shape[1] - select.displayWidth - 10  # 右上角 x 坐标
        displayY = 10
        # 已经选取对象
        if (self.selectingObject):
            # 绘制矩形
            cv2.rectangle(frame, (self.originX, self.originY), (self.endX, self.endY), (0, 255, 255), 1)
            hint = "Release the mouse after selecting the target."
            cv2.putText(frame, hint, (0, 20), cv2.FONT_HERSHEY_TRIPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
            self.lossing = False
        # 初始化跟踪对象
        elif (self.initTracking):
            cv2.rectangle(frame, (self.originX, self.originY), (self.originX + self.width, self.originY + self.height), (0, 255, 255), 2)

            tracker.init([self.originX, self.originY, self.width, self.height], frame)
            # 关闭初始化跟踪选项
            self.initTracking = False
            # 开启目标跟踪
            self.tracking = True
        # 目标跟踪已开启
        elif (self.tracking):
            preTime = time()
            # 获取边框
            boundingbox = tracker.update(frame)
            startTime = time()

            boundingbox = list(map(int, boundingbox))
            # 绘制边框
            cv2.rectangle(frame, (boundingbox[0], boundingbox[1]),
                          (boundingbox[0] + boundingbox[2], boundingbox[1] + boundingbox[3]), (0, 255, 255), 1)
            
            # 在图像上叠加显示被框圈出的图像
            if self.boxedImage is not None:
                # 调整被框圈出的图像的尺寸
                boxedImageResized = cv2.resize(self.boxedImage, (self.displayWidth, self.displayHeight))
                # 在图像上添加被框圈出的图像
                frame[displayY:displayY+self.displayHeight, displayX:displayX+self.displayWidth] = cv2.addWeighted(frame[displayY:displayY+self.displayHeight, displayX:displayX+self.displayWidth], 0.1, boxedImageResized, 0.8, 0)
                hint = "Selected target"
                cv2.putText(frame, hint, (frame.shape[1] - 150, self.displayHeight + 25), cv2.FONT_HERSHEY_TRIPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
                resolution = "Resolution: {}x{}".format(640, 480)
                cv2.putText(frame, resolution, (frame.shape[1] - 180, self.displayHeight + 45), cv2.FONT_HERSHEY_TRIPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)

            # 计算帧率
            self.duration = 0.8 * self.duration + 0.2 * (startTime - preTime)
            fps = "FPS: {:.2f}".format(1 / self.duration)
            cv2.putText(frame, fps, (frame.shape[1] - 640, 20), cv2.FONT_HERSHEY_TRIPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
            # 显示正在跟踪
            hint = "Tracking."
            cv2.putText(frame, hint, (frame.shape[1] - 400, 20), cv2.FONT_HERSHEY_TRIPLEX, 0.5, (255, 0, 0), 1, cv2.LINE_AA)#图片、文字、位置、类型、大小、颜色、粗细

            # 跟踪目标丢失之后重新选择需要跟踪的目标
            if tracker.lossCount >= 10:
                tracker.lossCount = 0
                self.tracking = False
                self.lossing = True
        elif (self.lossing):
            hint = "Please reselect the target."
            cv2.putText(frame, hint, (frame.shape[1] - 640, 20), cv2.FONT_HERSHEY_TRIPLEX, 0.5, (0, 0, 255), 1, cv2.LINE_AA)
        else:
            hint = "Selecting the target."
            cv2.putText(frame, hint, (frame.shape[1] - 640, 20), cv2.FONT_HERSHEY_TRIPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)

        return frame


"""
KCF算法类
"""

class KCF:

    """
    初始化跟踪器的各种参数和标志
    """

    def __init__(self, hog=True, fixedWindow=True, multiscale=False):
        self.lossCount = 0
        self.lambdar = 0.0001   # 规则化
        self.padding = 2.5   # 目标周围的额外区域
        self.sigmaFactor = 0.125   # 高斯目标带宽
        self.fhog = Fhog() # 初始化特征值计算类
        if(hog):  # HOG 特征
            # VOT
            self.interpFactor = 0.012   # 线性插值因子自适应
            self.sigma = 0.6  # 高斯核带宽
            self.cellSize = 4   # HOG 细胞大小
            self.hogfeatures = True

        else:  # 原始灰度图像, 又名CSK跟踪器
            self.interpFactor = 0.075# 线性插值因子自适应
            self.sigma = 0.2# 高斯核带宽
            self.cellSize = 1 # HOG 细胞大小
            self.hogfeatures = False

        if(multiscale):
            self.templateSize = 96   # 模板大小
            self.scaleStep = 1.05   # 多尺度估计的尺度步进
            self.scaleWeight = 0.96   # 降低其他量表的检测分数的权重以增加稳定性
        
        elif(fixedWindow):
            self.templateSize = 96# 模板大小
            self.scaleStep = 1# 多尺度估计的尺度步进
        
        else:
            self.templateSize = 1# 模板大小
            self.scaleStep = 1# 多尺度估计的尺度步进

        self.tmplSize = [0,0]  # cv::Size, [width,height]  #[int,int]
        self.roi = [0.,0.,0.,0.]  # cv::Rect2f, [x,y,width,height]  #[float,float,float,float]
        self.sizePatch = [0,0,0]  #[int,int,int]
        self.scale = 1.   # float
        self.alphaf = None  
        self.prob = None 
        self.tmpl = None  
        self.hann = None  
    
    """
    用于初始化跟踪器，设置初始目标区域、提取初始图像特征，并进行训练。
    """

    def init(self, roi, image):
        self.roi = list(map(float, roi))
        assert(roi[2]>=0 and roi[3]>=0)

        self.tmpl = self.getFeatures(image, 1)

        self.prob = self.gaussianPeak(self.sizePatch[0], self.sizePatch[1])
        self.alphaf = np.zeros((self.sizePatch[0], self.sizePatch[1], 2), np.float32)
        self.train(self.tmpl, 1.0)

    """
    函数用于训练跟踪器，更新目标模板 tmpl 和滤波器 alphaf.
    """

    def train(self, x, trainFactor):
        k = self.gaussianCorrelation(x, x)
        alphaf = self.complexDivision(self.prob, self.fftd(k)+self.lambdar)

        self.tmpl = (1-trainFactor)*self.tmpl + trainFactor*x
        self.alphaf = (1-trainFactor)*self.alphaf + trainFactor*alphaf

    """
    用于更新跟踪器的状态，并返回更新后的目标区域。
    """

    def update(self, image):
        if(self.roi[0]+self.roi[2] <= 0):  self.roi[0] = -self.roi[2] + 1
        if(self.roi[1]+self.roi[3] <= 0):  self.roi[1] = -self.roi[2] + 1
        if(self.roi[0] >= image.shape[1]-1):  self.roi[0] = image.shape[1] - 2
        if(self.roi[1] >= image.shape[0]-1):  self.roi[1] = image.shape[0] - 2

        cx = self.roi[0] + self.roi[2]/2.
        cy = self.roi[1] + self.roi[3]/2.

        loc, peakValue = self.detect(self.tmpl, self.getFeatures(image, 0, 1.0))

        if(self.scaleStep != 1):
            # 以较小的规模进行测试
            newLoc1, newPeakValue1 = self.detect(self.tmpl, self.getFeatures(image, 0, 1.0/self.scaleStep))
            # 进行更大规模的测试
            newLoc2, newPeakValue2 = self.detect(self.tmpl, self.getFeatures(image, 0, self.scaleStep))

            if(self.scaleWeight*newPeakValue1 > peakValue and newPeakValue1>newPeakValue2):
                loc = newLoc1
                peakValue = newPeakValue1
                self.scale /= self.scaleStep
                self.roi[2] /= self.scaleStep
                self.roi[3] /= self.scaleStep
            elif(self.scaleWeight*newPeakValue2 > peakValue):
                loc = newLoc2
                peakValue = newPeakValue2
                self.scale *= self.scaleStep
                self.roi[2] *= self.scaleStep
                self.roi[3] *= self.scaleStep
        
        self.roi[0] = cx - self.roi[2]/2.0 + loc[0]*self.cellSize*self.scale
        self.roi[1] = cy - self.roi[3]/2.0 + loc[1]*self.cellSize*self.scale

        if(self.roi[0]<=-10 or self.roi[1]<=-10 or (self.roi[0]+self.roi[2])>640 or (self.roi[1]+self.roi[3])>480): 
            self.lossCount += 1
        if(self.roi[0] >= image.shape[1]-1):  self.roi[0] = image.shape[1] - 1
        if(self.roi[1] >= image.shape[0]-1):  self.roi[1] = image.shape[0] - 1
        if(self.roi[0]+self.roi[2] <= 0):  self.roi[0] = -self.roi[2] + 2
        if(self.roi[1]+self.roi[3] <= 0):  self.roi[1] = -self.roi[3] + 2
        assert(self.roi[2]>0 and self.roi[3]>0)

        x = self.getFeatures(image, 0, 1.0)
        self.train(x, self.interpFactor)

        return self.roi

    """
    用于进行子像素级别的峰值定位。
    它采用左边、中心和右边三个位置的响应值作为参数，并计算出峰值的子像素偏移量。
    通过在峰值附近进行子像素级别的插值来提高精确度，以便更准确地估计目标的位置。
    """

    def subPixelPeak(self, left, center, right):
        divisor = 2*center - right - left   #float
        return (0 if abs(divisor)<1e-3 else 0.5*(right-left)/divisor)

    """
    创建一个与目标大小相匹配的Hanning窗函数矩阵, 以便在目标特征提取时应用窗函数以减小频谱泄露的影响。
    """

    def hanningMats(self):
        hann2t, hann1t = np.ogrid[0:self.sizePatch[0], 0:self.sizePatch[1]]

        hann1t = 0.5 * (1 - np.cos(2*np.pi*hann1t/(self.sizePatch[1]-1)))
        hann2t = 0.5 * (1 - np.cos(2*np.pi*hann2t/(self.sizePatch[0]-1)))
        hann2d = hann2t * hann1t

        if(self.hogfeatures):
            hann1d = hann2d.reshape(self.sizePatch[0]*self.sizePatch[1])
            self.hann = np.zeros((self.sizePatch[2], 1), np.float32) + hann1d
        else:
            self.hann = hann2d
        self.hann = self.hann.astype(np.float32)

    """
    创建一个二维高斯峰，用作相关滤波器的目标响应模板。
    """
    
    def gaussianPeak(self, sizey, sizex):
        syh, sxh = sizey/2, sizex/2
        sigma = np.sqrt(sizex*sizey) / self.padding * self.sigmaFactor
        mult = -0.5 / (sigma*sigma)
        y, x = np.ogrid[0:sizey, 0:sizex]
        y, x = (y-syh)**2, (x-sxh)**2
        res = np.exp(mult * (y+x))
        return self.fftd(res)
    
    """
    用于计算两个特征图 x1 和 x2 的高斯相关性。
    """
    
    def gaussianCorrelation(self, x1, x2):
        if(self.hogfeatures):
            c = np.zeros((self.sizePatch[0], self.sizePatch[1]), np.float32)
            for i in range(self.sizePatch[2]):
                x1aux = x1[i, :].reshape((self.sizePatch[0], self.sizePatch[1]))
                x2aux = x2[i, :].reshape((self.sizePatch[0], self.sizePatch[1]))
                caux = cv2.mulSpectrums(self.fftd(x1aux), self.fftd(x2aux), 0, conjB = True)
                caux = self.real(self.fftd(caux, True))
                c += caux
            c = self.rearrange(c)
        else:
            c = cv2.mulSpectrums(self.fftd(x1), self.fftd(x2), 0, conjB = True)   # 'conjB=' is necessary!
            c = self.fftd(c, True)
            c = self.real(c)
            c = self.rearrange(c)

        if(x1.ndim==3 and x2.ndim==3):
            d = (np.sum(x1[:,:,0]*x1[:,:,0]) + np.sum(x2[:,:,0]*x2[:,:,0]) - 2.0*c) / (self.sizePatch[0]*self.sizePatch[1]*self.sizePatch[2])
        elif(x1.ndim==2 and x2.ndim==2):
            d = (np.sum(x1*x1) + np.sum(x2*x2) - 2.0*c) / (self.sizePatch[0]*self.sizePatch[1]*self.sizePatch[2])

        d = d * (d>=0)
        d = np.exp(-d / (self.sigma*self.sigma))

        return d
    
    """
    从输入图像中提取特征，并返回特征图 FeaturesMap。
    """
    
    def getFeatures(self, image, inithann, scale_adjust=1.0):
  
        extractedRoi = [0,0,0,0]   #[int,int,int,int]
        cx = self.roi[0] + self.roi[2]/2  #float
        cy = self.roi[1] + self.roi[3]/2  #float

        if(inithann):
            paddedW = self.roi[2] * self.padding
            paddedH = self.roi[3] * self.padding

            if(self.templateSize > 1):
                if(paddedW >= paddedH):
                    self.scale = paddedW / float(self.templateSize)
                else:
                    self.scale = paddedH / float(self.templateSize)
                self.tmplSize[0] = int(paddedW / self.scale)
                self.tmplSize[1] = int(paddedH / self.scale)
            else:
                self.tmplSize[0] = int(paddedW)
                self.tmplSize[1] = int(paddedH)
                self.scale = 1.

            if(self.hogfeatures):
                self.tmplSize[0] = int(self.tmplSize[0]) // (2*self.cellSize) * 2*self.cellSize + 2*self.cellSize
                self.tmplSize[1] = int(self.tmplSize[1]) // (2*self.cellSize) * 2*self.cellSize + 2*self.cellSize
            else:
                self.tmplSize[0] = int(self.tmplSize[0]) // 2 * 2
                self.tmplSize[1] = int(self.tmplSize[1]) // 2 * 2

        extractedRoi[2] = int(scale_adjust * self.scale * self.tmplSize[0])
        extractedRoi[3] = int(scale_adjust * self.scale * self.tmplSize[1])
        extractedRoi[0] = int(cx - extractedRoi[2]/2)
        extractedRoi[1] = int(cy - extractedRoi[3]/2)

        z = self.subwindow(image, extractedRoi, cv2.BORDER_REPLICATE)
        if(z.shape[1]!=self.tmplSize[0] or z.shape[0]!=self.tmplSize[1]):
            z = cv2.resize(z, tuple(self.tmplSize))

        if(self.hogfeatures):
            mapp = {'sizeX':0, 'sizeY':0, 'numFeatures':0, 'map':0}
            mapp = self.fhog.getFeatureMaps(z, self.cellSize, mapp)

            mapp = self.fhog.normalizeAndTruncate(mapp, 0.2)

            mapp = self.fhog.PCAFeatureMaps(mapp)

            self.sizePatch = list(map(int, [mapp['sizeY'], mapp['sizeX'], mapp['numFeatures']]))
            FeaturesMap = mapp['map'].reshape((self.sizePatch[0]*self.sizePatch[1], self.sizePatch[2])).T   
        else:
            if(z.ndim==3 and z.shape[2]==3):
                FeaturesMap = cv2.cvtColor(z, cv2.COLOR_BGR2GRAY)   # z:(sizePatch[0], sizePatch[1], 3)  FeaturesMap:(sizePatch[0], sizePatch[1])   #np.int8  #0~255
            elif(z.ndim==2):
                FeaturesMap = z   #(sizePatch[0], sizePatch[1]) #np.int8  #0~255
            FeaturesMap = FeaturesMap.astype(np.float32) / 255.0 - 0.5
            self.sizePatch = [z.shape[0], z.shape[1], 1]
        
        if(inithann):
            self.hanningMats()  # 创建矩阵

        FeaturesMap = self.hann * FeaturesMap

        return FeaturesMap

    """
    函数用于执行目标检测, 给定目标模板 z 和待检测图像特征x.
    """

    def detect(self, z, x):
        k = self.gaussianCorrelation(x, z)
        res = self.real(self.fftd(self.complexMultiplication(self.alphaf, self.fftd(k)), True))#逆傅里叶变换得到实数域的响应结果 res。

        _, pv, _, pi = cv2.minMaxLoc(res)   # pv:float  pi:tuple of int   利用 cv2.minMaxLoc 函数找到 res 的最大值 pv 及其位置 pi
        p = [float(pi[0]), float(pi[1])]   # cv::Point2f, [x,y]  #[float,float]

        if(pi[0]>0 and pi[0]<res.shape[1]-1):
            p[0] += self.subPixelPeak(res[pi[1],pi[0]-1], pv, res[pi[1],pi[0]+1])
        if(pi[1]>0 and pi[1]<res.shape[0]-1):
            p[1] += self.subPixelPeak(res[pi[1]-1,pi[0]], pv, res[pi[1]+1,pi[0]])#调用 subPixelPeak 函数进行亚像素精确定位，得到更准确的目标位置 p。

        p[0] -= res.shape[1] / 2.
        p[1] -= res.shape[0] / 2.

        return p, pv
    
    """
    FFT和逆FFT变换
    """

    def fftd(self, img, backwards=False):    
        return cv2.dft(np.float32(img), flags = ((cv2.DFT_INVERSE | cv2.DFT_SCALE) if backwards else cv2.DFT_COMPLEX_OUTPUT))  
    
    """
    获取实部和虚部  
    """  

    def real(self, img):
        return img[:,:,0]
    def imag(self, img):
        return img[:,:,1]
    
    """
    复数乘法和除法  
    """     

    def complexMultiplication(self, a, b):
        res = np.zeros(a.shape, a.dtype)
        res[:,:,0] = a[:,:,0]*b[:,:,0] - a[:,:,1]*b[:,:,1]
        res[:,:,1] = a[:,:,0]*b[:,:,1] + a[:,:,1]*b[:,:,0]
        return res
    def complexDivision(self, a, b):
        res = np.zeros(a.shape, a.dtype)
        divisor = 1. / (b[:,:,0]**2 + b[:,:,1]**2)
        res[:,:,0] = (a[:,:,0]*b[:,:,0] + a[:,:,1]*b[:,:,1]) * divisor
        res[:,:,1] = (a[:,:,1]*b[:,:,0] + a[:,:,0]*b[:,:,1]) * divisor
        
        return res
    
    """
    重新排列图像
    """

    def rearrange(self, img):
        #return np.fft.fftshift(img, axes=(0,1))
        assert(img.ndim==2)
        imgNew = np.zeros(img.shape, img.dtype)
        xh, yh = img.shape[1]//2, img.shape[0]//2
        imgNew[0:yh,0:xh], imgNew[yh:img.shape[0],xh:img.shape[1]] = img[yh:img.shape[0],xh:img.shape[1]], img[0:yh,0:xh]
        imgNew[0:yh,xh:img.shape[1]], imgNew[yh:img.shape[0],0:xh] = img[yh:img.shape[0],0:xh], img[0:yh,xh:img.shape[1]]
        
        return imgNew

    """
    辅助函数用于矩形坐标计算和限制
    """

    # 给定一个矩形的坐标（左上角的x、y坐标以及宽度和高度），返回矩形的右下角x坐标。
    def x2(self, rect):
        return rect[0] + rect[2]
    # 给定一个矩形的坐标，返回矩形的右下角y坐标
    def y2(self, rect):
        return rect[1] + rect[3]
    # 限制矩形的大小，确保其不超过给定的限制。如果矩形超过限制的边界，则将其调整为限制的边界。
    def limit(self, rect, limit):
        if(rect[0]+rect[2] > limit[0]+limit[2]):
            rect[2] = limit[0]+limit[2]-rect[0]
        if(rect[1]+rect[3] > limit[1]+limit[3]):
            rect[3] = limit[1]+limit[3]-rect[1]
        if(rect[0] < limit[0]):
            rect[2] -= (limit[0]-rect[0])
            rect[0] = limit[0]
        if(rect[1] < limit[1]):
            rect[3] -= (limit[1]-rect[1])
            rect[1] = limit[1]
        if(rect[2] < 0):
            rect[2] = 0
        if(rect[3] < 0):
            rect[3] = 0

        return rect
    
    """
    计算给定原始矩形和限制矩形之间的边界大小。返回一个四元组，表示边界的左、上、右、下的大小。
    """
    def getBorder(self, original, limited):
        res = [0,0,0,0]
        res[0] = limited[0] - original[0]
        res[1] = limited[1] - original[1]
        res[2] = self.x2(original) - self.x2(limited)
        res[3] = self.y2(original) - self.y2(limited)
        assert(np.all(np.array(res) >= 0))
        
        return res
    
    """
    从图像中提取给定窗口位置的子窗口。如果窗口超出图像边界，则使用指定的边界类型进行填充。返回提取的子窗口。
    """
    def subwindow(self, img, window, borderType=cv2.BORDER_CONSTANT):
        cutWindow = [x for x in window]
        self.limit(cutWindow, [0,0,img.shape[1],img.shape[0]])   # modify cutWindow
        assert(cutWindow[2]>0 and cutWindow[3]>0)
        border = self.getBorder(window, cutWindow)
        res = img[cutWindow[1]:cutWindow[1]+cutWindow[3], cutWindow[0]:cutWindow[0]+cutWindow[2]]

        if(border != [0,0,0,0]):
            res = cv2.copyMakeBorder(res, border[1], border[3], border[0], border[2], borderType)
        
        return res

"""
特征提取
"""

# constant
NUM_SECTOR = 9
FLT_EPSILON = 1e-07

class Fhog:
    def __init__(self):
        pass

    # 它使用KCF（Kernelized Correlation Filter）算法计算输入图像的特征图。
    # 它对图像应用滤波操作以获得梯度信息，计算梯度的方向，并基于梯度的方向和幅度构建特征图。
    def getFeatureMaps(self, image, k, mapp):
        kernel = np.array([[-1.,  0., 1.]], np.float32)

        height = image.shape[0]
        width = image.shape[1]
        assert(image.ndim==3 and image.shape[2])
        numChannels = 3 #(1 if image.ndim==2 else image.shape[2])

        sizeX = width // k
        sizeY = height // k
        px = 3 * NUM_SECTOR
        p = px
        stringSize = sizeX * p

        mapp['sizeX'] = sizeX
        mapp['sizeY'] = sizeY
        mapp['numFeatures'] = p
        mapp['map'] = np.zeros((mapp['sizeX']*mapp['sizeY']*mapp['numFeatures']), np.float32)

        dx = cv2.filter2D(np.float32(image), -1, kernel)   # np.float32(...) is necessary
        dy = cv2.filter2D(np.float32(image), -1, kernel.T)

        arg_vector = np.arange(NUM_SECTOR+1).astype(np.float32) * np.pi / NUM_SECTOR
        boundary_x = np.cos(arg_vector) 
        boundary_y = np.sin(arg_vector)
        r, alfa = func1(dx, dy, boundary_x, boundary_y, height, width, numChannels) #with @jit

        
        nearest = np.ones((k), np.int)
        nearest[0:k//2] = -1

        w = np.zeros((k, 2), np.float32)
        a_x = np.concatenate((k/2 - np.arange(k/2) - 0.5, np.arange(k/2,k) - k/2 + 0.5)).astype(np.float32)
        b_x = np.concatenate((k/2 + np.arange(k/2) + 0.5, -np.arange(k/2,k) + k/2 - 0.5 + k)).astype(np.float32)
        w[:, 0] = 1.0 / a_x * ((a_x*b_x) / (a_x+b_x))
        w[:, 1] = 1.0 / b_x * ((a_x*b_x) / (a_x+b_x))

        mapp['map'] = func2(dx, dy, boundary_x, boundary_y, r, alfa, nearest, w, k, height, width, sizeX, sizeY, p, stringSize) #with @jit

        return mapp

    """
    规范化
    """
    def normalizeAndTruncate(self, mapp, alfa):
        sizeX = mapp['sizeX']
        sizeY = mapp['sizeY']
        p = NUM_SECTOR
        xp = NUM_SECTOR * 3
        pp = NUM_SECTOR * 12
        idx = np.arange(0, sizeX*sizeY*mapp['numFeatures'], mapp['numFeatures']).reshape((sizeX*sizeY, 1)) + np.arange(p)
        partOfNorm = np.sum(mapp['map'][idx] ** 2, axis=1) ### ~0.0002s
        sizeX, sizeY = sizeX-2, sizeY-2
        newData = func3(partOfNorm, mapp['map'], sizeX, sizeY, p, xp, pp) #with @jit
        newData[newData > alfa] = alfa
        mapp['numFeatures'] = pp
        mapp['sizeX'] = sizeX
        mapp['sizeY'] = sizeY
        mapp['map'] = newData

        return mapp

    """
    PCA特征图
    """
    def PCAFeatureMaps(self, mapp):
        sizeX = mapp['sizeX']
        sizeY = mapp['sizeY']
        p = mapp['numFeatures']
        pp = NUM_SECTOR * 3 + 4
        yp = 4
        xp = NUM_SECTOR
        nx = 1.0 / np.sqrt(xp*2)
        ny = 1.0 / np.sqrt(yp)
        newData = func4(mapp['map'], p, sizeX, sizeY, pp, yp, xp, nx, ny) #with @jit
        mapp['numFeatures'] = pp
        mapp['map'] = newData
        return mapp
    
@jit
def func1(dx, dy, boundary_x, boundary_y, height, width, numChannels):
    r = np.zeros((height, width), np.float64)
    alfa = np.zeros((height, width, 2), np.int64)

    for j in range(1, height-1):
        for i in range(1, width-1):
            c = 0
            x = dx[j, i, c]
            y = dy[j, i, c]
            r[j, i] = np.sqrt(x*x + y*y)

            for ch in range(1, numChannels):
                tx = dx[j, i, ch]
                ty = dy[j, i, ch]
                magnitude = np.sqrt(tx*tx + ty*ty)
                if(magnitude > r[j, i]):
                    r[j, i] = magnitude
                    c = ch
                    x = tx
                    y = ty

            mmax = boundary_x[0]*x + boundary_y[0]*y
            maxi = 0

            for kk in range(0, NUM_SECTOR):
                dotProd = boundary_x[kk]*x + boundary_y[kk]*y
                if(dotProd > mmax):
                    mmax = dotProd
                    maxi = kk
                elif(-dotProd > mmax):
                    mmax = -dotProd
                    maxi = kk + NUM_SECTOR

            alfa[j, i, 0] = maxi % NUM_SECTOR
            alfa[j, i, 1] = maxi
    return r, alfa

@jit
def func2(dx, dy, boundary_x, boundary_y, r, alfa, nearest, w, k, height, width, sizeX, sizeY, p, stringSize):
    mapp = np.zeros((sizeX*sizeY*p), np.float64)
    for i in range(sizeY):
        for j in range(sizeX):
            for ii in range(k):
                for jj in range(k):
                    if((i * k + ii > 0) and (i * k + ii < height - 1) and (j * k + jj > 0) and (j * k + jj < width  - 1)):
                        mapp[i*stringSize + j*p + alfa[k*i+ii,j*k+jj,0]] +=  r[k*i+ii,j*k+jj] * w[ii,0] * w[jj,0]
                        mapp[i*stringSize + j*p + alfa[k*i+ii,j*k+jj,1] + NUM_SECTOR] +=  r[k*i+ii,j*k+jj] * w[ii,0] * w[jj,0]
                        if((i + nearest[ii] >= 0) and (i + nearest[ii] <= sizeY - 1)):
                            mapp[(i+nearest[ii])*stringSize + j*p + alfa[k*i+ii,j*k+jj,0]] += r[k*i+ii,j*k+jj] * w[ii,1] * w[jj,0]
                            mapp[(i+nearest[ii])*stringSize + j*p + alfa[k*i+ii,j*k+jj,1] + NUM_SECTOR] += r[k*i+ii,j*k+jj] * w[ii,1] * w[jj,0]
                        if((j + nearest[jj] >= 0) and (j + nearest[jj] <= sizeX - 1)):
                            mapp[i*stringSize + (j+nearest[jj])*p + alfa[k*i+ii,j*k+jj,0]] += r[k*i+ii,j*k+jj] * w[ii,0] * w[jj,1]
                            mapp[i*stringSize + (j+nearest[jj])*p + alfa[k*i+ii,j*k+jj,1] + NUM_SECTOR] += r[k*i+ii,j*k+jj] * w[ii,0] * w[jj,1]
                        if((i + nearest[ii] >= 0) and (i + nearest[ii] <= sizeY - 1) and (j + nearest[jj] >= 0) and (j + nearest[jj] <= sizeX - 1)):
                            mapp[(i+nearest[ii])*stringSize + (j+nearest[jj])*p + alfa[k*i+ii,j*k+jj,0]] += r[k*i+ii,j*k+jj] * w[ii,1] * w[jj,1]
                            mapp[(i+nearest[ii])*stringSize + (j+nearest[jj])*p + alfa[k*i+ii,j*k+jj,1] + NUM_SECTOR] += r[k*i+ii,j*k+jj] * w[ii,1] * w[jj,1]
    return mapp

@jit
def func3(partOfNorm, mappmap, sizeX, sizeY, p, xp, pp):
    newData = np.zeros((sizeY*sizeX*pp), np.float64)
    for i in range(1, sizeY+1):
        for j in range(1, sizeX+1):
            pos1 = i * (sizeX+2) * xp + j * xp
            pos2 = (i-1) * sizeX * pp + (j-1) * pp

            valOfNorm = np.sqrt(partOfNorm[(i    )*(sizeX + 2) + (j    )] +
                                partOfNorm[(i    )*(sizeX + 2) + (j + 1)] +
                                partOfNorm[(i + 1)*(sizeX + 2) + (j    )] +
                                partOfNorm[(i + 1)*(sizeX + 2) + (j + 1)]) + FLT_EPSILON
            newData[pos2:pos2+p] = mappmap[pos1:pos1+p] / valOfNorm
            newData[pos2+4*p:pos2+6*p] = mappmap[pos1+p:pos1+3*p] / valOfNorm

            valOfNorm = np.sqrt(partOfNorm[(i    )*(sizeX + 2) + (j    )] +
                                partOfNorm[(i    )*(sizeX + 2) + (j + 1)] +
                                partOfNorm[(i - 1)*(sizeX + 2) + (j    )] +
                                partOfNorm[(i - 1)*(sizeX + 2) + (j + 1)]) + FLT_EPSILON
            newData[pos2+p:pos2+2*p] = mappmap[pos1:pos1+p] / valOfNorm
            newData[pos2+6*p:pos2+8*p] = mappmap[pos1+p:pos1+3*p] / valOfNorm

            valOfNorm = np.sqrt(partOfNorm[(i    )*(sizeX + 2) + (j    )] +
                                partOfNorm[(i    )*(sizeX + 2) + (j - 1)] +
                                partOfNorm[(i + 1)*(sizeX + 2) + (j    )] +
                                partOfNorm[(i + 1)*(sizeX + 2) + (j - 1)]) + FLT_EPSILON
            newData[pos2+2*p:pos2+3*p] = mappmap[pos1:pos1+p] / valOfNorm
            newData[pos2+8*p:pos2+10*p] = mappmap[pos1+p:pos1+3*p] / valOfNorm

            valOfNorm = np.sqrt(partOfNorm[(i    )*(sizeX + 2) + (j    )] +
                                partOfNorm[(i    )*(sizeX + 2) + (j - 1)] +
                                partOfNorm[(i - 1)*(sizeX + 2) + (j    )] +
                                partOfNorm[(i - 1)*(sizeX + 2) + (j - 1)]) + FLT_EPSILON
            newData[pos2+3*p:pos2+4*p] = mappmap[pos1:pos1+p] / valOfNorm
            newData[pos2+10*p:pos2+12*p] = mappmap[pos1+p:pos1+3*p] / valOfNorm
    return newData

@jit
def func4(mappmap, p, sizeX, sizeY, pp, yp, xp, nx, ny):
    newData = np.zeros((sizeX*sizeY*pp), np.float64)
    for i in range(sizeY):
        for j in range(sizeX):
            pos1 = (i*sizeX + j) * p
            pos2 = (i*sizeX + j) * pp

            for jj in range(2 * xp):  # 2*9
                newData[pos2 + jj] = np.sum(mappmap[pos1 + yp*xp + jj : pos1 + 3*yp*xp + jj : 2*xp]) * ny
            for jj in range(xp):  # 9
                newData[pos2 + 2*xp + jj] = np.sum(mappmap[pos1 + jj : pos1 + jj + yp*xp : xp]) * ny
            for ii in range(yp):  # 4
                newData[pos2 + 3*xp + ii] = np.sum(mappmap[pos1 + yp*xp + ii*xp*2 : pos1 + yp*xp + ii*xp*2 + 2*xp]) * nx
    return newData

if __name__ == '__main__':

    capture = cv2.VideoCapture("/dev/video0")   # 可以设置摄像头
    # 设置视频流的分辨率为640x480
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    # #### 代码填空开始处 #### #  
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)            
    """            
        代码填空提示，代码仅一行：   
        1. 设置窗口高度为480，使用capture调用set设立窗口高度。
        2. 参数一共两个，第一个参数为cv2.CAP_PROP_FRAME_HEIGHT，第二个参数为设定的数值。
    """              
    # #### 代码填空结束处 #### #  

    select = SelectTarget()# 初始化目标选择类

    # #### 代码填空开始处 #### #              
    """            
        代码填空提示，代码仅一行：
        1. 实例化KCF类，变量命名为tracker。
        2. KCF追踪器的参数可以设置为False或True，分别表示贪婪、固定窗口和多尺度的开启或关闭
    """  
    tracker = KCF()            
    # #### 代码填空结束处 #### #  
    
    # 指定窗口名
    cv2.namedWindow('tracking', cv2.WINDOW_NORMAL)
    # 可调整显示大小
    cv2.resizeWindow('tracking', 1280, 960)
    # 设置鼠标回调 (名称, 回调函数)
    cv2.setMouseCallback('tracking', select.mouseControl)

    # 循环取流(是否开启)
    while (capture.isOpened()):
        # (是否成功,图片)
        ret, frame = capture.read()

        if not ret:
            break
        
        select.showState(tracker, frame)  # 启动KCF算法并将状态显示
        cv2.imshow('tracking', frame)

        if cv2.waitKey(1) == 27:# 按ESC退出程序
            break

    # 释放
    capture.release()
    # 销毁
    cv2.destroyAllWindows()
