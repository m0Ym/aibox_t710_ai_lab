#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@file          :objectDetection.py
@Description   :目标检测模型
@Date          :2023/07/25 15:30:26
@Autor         :HC
@Version       :v1.0
"""
import yaml
import cv2
import numpy as np
from ppnc import PPNCPredictor

class Detection:
    """
    人脸/目标检测类
    读取配置文件并进行模型推理和绘制
    path: 模型文件夹的路径.
    threshold: 模型预测的置信度
    """
    def __init__(self, path):

        # 读取人脸/目标检测模型
        self.config = {
            "mode": "normal",
            "model_dir": path,
            "model_file": "ppnc.tar"
        }
        self.result = []  # AI检测结果类

        # 读取yml文件配置模型参数
        with open(path + "/infer_cfg.yml", "r",) as f:
            self.inferYml = yaml.safe_load(f)
        self.model = PPNCPredictor(self.config)  # 加载模型路径
        self.model.load()                        # 加载模型
        self.preprocessOps = []                  # 加载模型配置
        # 读取yml文件中的"Preprocess"预处理配置
        for opInfo in self.inferYml["Preprocess"]:
            newOpInfo = opInfo.copy()
            opType = newOpInfo.pop("type")
            self.preprocessOps.append(eval(opType)(**newOpInfo))

    class Result:
        """
        AI检测结果
        """
        score = 0.0  # 置信度: 0.0~1.0
        lable = ""  # 标签
        xMin = 0  # 目标检测坐标: 左上x
        yMin = 0  # 目标检测坐标: 左上y
        xMax = 0  # 目标检测坐标: 右下x
        yMax = 0  # 目标检测坐标: 右下y

    def preprocess(self, im):
        """
        图像预处理函数
        将图像信息处理成RGB
        Args:
            im :输入可以是图像地址或numpy类型的图像
            imInfo: 处理后的图像信息
        """
        imInfo = {
            "scale_factor": np.array([1.0, 1.0], dtype=np.float32),
            "im_shape": None,
        }
        if isinstance(im, str):
            with open(im, 'rb') as f:
                imRead = f.read()
            data = np.frombuffer(imRead, dtype='uint8')
            im = cv2.imdecode(data, 1)
            im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        else:
            im = im
            im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        imInfo['im_shape'] = np.array(im.shape[:2], dtype=np.float32)
        imInfo['scale_factor'] = np.array([1., 1.], dtype=np.float32)
        for operator in self.preprocessOps:
            im, imInfo = operator(im, imInfo)
        res = {**imInfo, "image": im.astype("float32")}

        return {i: np.expand_dims(res[i], axis=0) for i in res.keys()}

    def postprocess(self, result):
        """
        图像后处理函数
        控制预测结果的数据类型
        """
        npBoxesNum = result["boxesNum"]
        assert isinstance(
            npBoxesNum, np.ndarray
        ), "`npBoxesNum` should be a `numpy.ndarray`"
        result = {k: v for k, v in result.items() if v is not None}
        return result

    def render(self, images):
        """
        模型预测函数
        对图像进行预测并输出预测结果
        """
        images = self.preprocess(images)   # 图像预处理
        self.model.set_inputs(images)
        self.model.run()
        n = self.model.predictor.get_num_outputs()
        res = [self.model.get_output(i) for i in range(n)]
        res = {"boxes": res[0], "boxesNum": res[1]}
        res = self.postprocess(res)    # 图像后处理

        self.result = []  # 数据清除
        for data in res["boxes"]:
            result = self.Result()
            if int(data[0]) < len(self.inferYml["label_list"]):  # 标签
                result.lable = self.inferYml["label_list"][int(data[0])]
            result.score = data[1]  # 置信度
            # 坐标
            result.xMin, result.yMin, result.xMax, result.yMax = data[2:]
            result.xMin = int(result.xMin)
            result.yMin = int(result.yMin)
            result.xMax = int(result.xMax)
            result.yMax = int(result.yMax)
            self.result.append(result)

        return self.result

    def drawBox(self, img, threshold):
        """
        绘制识别的方框
        img: 图像
        res: 预测结果
        threshold: 置信度阈值
        """
        for result in self.result:
            if result.score < threshold:
                continue
            if result.lable == "person" or result.lable == "face":
                cv2.rectangle(img, (result.xMin, result.yMin),
                            (result.xMax, result.yMax), (0, 0, 255))
            else:
                cv2.rectangle(img, (result.xMin, result.yMin),
                            (result.xMax, result.yMax), (0, 255, 255))
            cv2.putText(
                img,
                result.lable,
                (int(result.xMin), int((result.yMax-result.yMin)/2) if result.yMin == 0 else int(result.yMin)),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
            )
        return img

class Resize(object):
    """
    调整图像进入模型时的大小
    """
    def __init__(self, target_size, keep_ratio=True, interp=cv2.INTER_LINEAR):
        if isinstance(target_size, int):
            target_size = [target_size, target_size]
        self.target_size = target_size
        self.keep_ratio = keep_ratio
        self.interp = interp

    def __call__(self, im, imInfo):
        assert len(self.target_size) == 2
        assert self.target_size[0] > 0 and self.target_size[1] > 0
        im_channel = im.shape[2]
        imScaleY, imScaleX = self.generateScale(im)
        im = cv2.resize(
            im,
            None,
            None,
            fx=imScaleX,
            fy=imScaleY,
            interpolation=self.interp)
        imInfo['im_shape'] = np.array(im.shape[:2]).astype('float32')
        imInfo['scale_factor'] = np.array(
            [imScaleY, imScaleX]).astype('float32')
        return im, imInfo

    def generateScale(self, im):
        origin_shape = im.shape[:2]
        im_c = im.shape[2]
        if self.keep_ratio:
            imSizeMin = np.min(origin_shape)
            imSizeMax = np.max(origin_shape)
            targeSizeMin = np.min(self.target_size)
            targeSizeMaz = np.max(self.target_size)
            imScale = float(targeSizeMin) / float(imSizeMin)
            if np.round(imScale * imSizeMax) > targeSizeMaz:
                imScale = float(targeSizeMaz) / float(imSizeMax)
            imScaleX = imScale
            imScaleY = imScale
        else:
            resizeH, resizeW = self.target_size
            imScaleY = resizeH / float(origin_shape[0])
            imScaleX = resizeW / float(origin_shape[1])
        return imScaleY, imScaleX


class NormalizeImage(object):
    """
    将图像归一化, 方便计算特征值
    """
    def __init__(self, mean, std, is_scale=True, normType="mean_std"):
        self.mean = mean
        self.std = std
        self.is_scale = is_scale
        self.normType = normType

    def __call__(self, im, imInfo):
        im = im.astype(np.float32, copy=False)
        if self.is_scale:
            scale = 1.0 / 255.0
            im *= scale

        if self.normType == "mean_std":
            mean = np.array(self.mean)[np.newaxis, np.newaxis, :]
            std = np.array(self.std)[np.newaxis, np.newaxis, :]
            im -= mean
            im /= std
        return im, imInfo

class Permute(object):
    """
    重新排列图像, 调整图像维度(HWC-->CHW)
    """
    def __init__(self,):
        super(Permute, self).__init__()

    def __call__(self, im, imInfo):
        im = im.transpose((2, 0, 1)).copy()
        return im, imInfo


"""
UT: 人脸/目标检测模型测试
"""

if __name__ == "__main__":

    # 可以修改模型文件夹来切换开启的模型(仅支持目标检测模型)
    # 加载模型文件, 需要根据情况修改路径
    object = Detection("../../res/models/objectDetection")

    # 设置摄像头
    capture = cv2.VideoCapture("/dev/deepCamera")   # 可以设置摄像头
    capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    # 创建窗口
    cv2.namedWindow("Video", cv2.WINDOW_NORMAL)
    # 将窗口铺满屏幕
    cv2.setWindowProperty(
        'Video', cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
    while True:

        ret, frame = capture.read()      # 读取视频
        
        # 检查是否成功读取视频帧
        if not ret:
            break

        # #### 代码填空开始处 #### #  
        res = object.render(frame)
        frame = object.drawBox(frame, 0.8)
        # #### 代码填空结束处 #### # 
        
        cv2.imshow("Video", frame)

        if cv2.waitKey(1) == 27:  # 按ESC退出程序
            break
    capture.release()
    cv2.destroyAllWindows()
