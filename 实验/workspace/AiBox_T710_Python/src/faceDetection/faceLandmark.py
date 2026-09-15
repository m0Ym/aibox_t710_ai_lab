#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""
@file          :faceLandmark.py
@Description   :人脸关键点检测模型
@Date          :2023/07/25 21:30:43
@Autor         :HC
@Version       :v1.0
"""
import yaml
import cv2
import numpy as np
from ppnc import PPNCPredictor

class FaceKeyPoint:
    """
    人脸关键点检测类
    读取配置文件并进行模型推理和绘制
    path1: 人脸检测模型所在的文件夹路径
    path2: 人脸关键点检测模型所在的文件夹路径
    """
    def __init__(self, path1, path2):

        # 读取人脸检测模型
        self.config = {
            "mode": "normal",
            "model_dir": path1,
            "model_file": "ppnc.tar"
        }

        # 读取yml文件配置模型参数
        with open(path1 + "/infer_cfg.yml", "r",) as f:
            self.inferYml = yaml.safe_load(f)
        self.configs = [self.config]

        # 读取人脸关键点检测模型
        self.config = {
            "mode": "normal",
            "model_dir": path2,
            "model_file": "ppnc.tar"
        }
        self.configs.append(self.config)
        self.model = PPNCPredictor(self.configs[1])
        self.model.load()
        self.detector = Detector(self.configs[0], inferYml=self.inferYml)

    def preprocess(self, img):
        """
        图像预处理函数
        """
        img = cv2.resize(img, (96, 96), interpolation=cv2.INTER_AREA)
        img = np.transpose(img, (2, 0, 1))
        img = img.astype("float32", copy=False)
        return {"inputs": np.expand_dims(img, axis=0)}

    def render(self, img, res, threshold):
        """
        模型预测函数
        对图像进行预测并输出预测结果
        """
        """
        提取框中的图像
        threshold: 置信度阈值
        """
        imgs = []
        boxes = []
        for box in res["boxes"]:
            if box[1] < threshold:
                continue
            xmin, ymin, xmax, ymax = box[2:]
            subImg = img[int(ymin): int(ymax), int(xmin): int(xmax)]
            imgs.append(subImg)
            boxes.append(box[2:])
        kpts = []
        for i in imgs:
            if i.shape[0] > 0 and i.shape[1] > 0:  # 数据保护, 人脸检测的边框出边界后将不进行人脸关键点预测
                inp = self.preprocess(i)
                self.model.set_inputs(inp)
                self.model.run()
            n = self.model.predictor.get_num_outputs()
            res = [self.model.get_output(i) for i in range(n)]
            kpts.append(res[0])

        """
        将每个方框(0,1)中的归一化kpts转换回原始图像
        参数:
        res (dict类型):
        Res ["boxes"]: (n,4)原始图像的xmin, ymin, xmax, ymax
        Res ["kpts"]:(n,30)每两个点代表图像中的一个点, 但归一化为(0,1)
        返回:
        与res相同的字典, 但有转换框
        """
        if len(boxes) > 0:
            res = {"kpts": np.concatenate(kpts), "boxes": np.stack(boxes)}
            boxes = res["boxes"]
            w = np.expand_dims(boxes[:, 3]-boxes[:, 1], axis=-1)
            h = np.expand_dims(boxes[:, 2]-boxes[:, 0], axis=-1)
            res["kpts"][:, 0::2] = res["kpts"][:, 0::2] * \
                h+np.expand_dims(boxes[:, 0], -1)
            res["kpts"][:, 1::2] = res["kpts"][:, 1::2] * \
                w+np.expand_dims(boxes[:, 1], -1)
        else:
            res = {"kpts": [], "boxes": []}

        return res

    def drawBox(self, img, res):
        """
        绘制识别的方框
        img: 图像
        res: 预测结果
        """
        kpts = res["kpts"]
        for i, kpt in enumerate(kpts):
            for x, y in zip(kpt[0::2], kpt[1::2]):
                cv2.drawMarker(
                    img,
                    (int(x), int(y)),
                    (0, 255, 0),
                    markerType=2,
                    markerSize=6,
                    thickness=1,
                )
            xmin, ymin, xmax, ymax = res["boxes"][i]
            cv2.rectangle(
                img, (int(xmin), int(ymin)), (int(
                    xmax), int(ymax)), (0, 255, 255)
            )
        return img

class Detector(object):
    """ 
    检测器
    初始化一个具有PPNC加速的模型并读取配置文件
    """
    def __init__(self, config, inferYml):
        self.model = PPNCPredictor(config)
        self.model.load()
        self.preprocessOps = []
        for opInfo in inferYml["Preprocess"]:
            newOpInfo = opInfo.copy()
            opType = newOpInfo.pop("type")
            self.preprocessOps.append(eval(opType)(**newOpInfo))

    def preprocess(self, imFile):
        """
        图像预处理
        传入图像并处理
        """
        imInfo = {
            "scale_factor": np.array([1.0, 1.0], dtype=np.float32),
            "im_shape": None,
        }

        """
        将图像信息处理成RGB
        Args:
            imFile :输入可以是图像地址或numpy类型的图像
            imInfo :图像信息
        Returns:
            im :  解码后的图像
            imInfo: 处理后的图像信息
        """
        if isinstance(imFile, str):
            with open(imFile, 'rb') as f:
                imRead = f.read()
            data = np.frombuffer(imRead, dtype='uint8')
            im = cv2.imdecode(data, 1)  # BGR mode, but need RGB mode
            im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        else:
            im = imFile
            im = cv2.cvtColor(im, cv2.COLOR_BGR2RGB)
        imInfo['im_shape'] = np.array(im.shape[:2], dtype=np.float32)
        imInfo['scale_factor'] = np.array([1., 1.], dtype=np.float32)

        for operator in self.preprocessOps:
            im, imInfo = operator(im, imInfo)
        res = {**imInfo, "image": im.astype("float32")}
        return {i: np.expand_dims(res[i], axis=0) for i in res.keys()}

    def postprocess(self, result):
        """
        图像后处理
        传入预测结果并处理
        """
        npBoxesNum = result["boxesNum"]
        assert isinstance(
            npBoxesNum, np.ndarray
        ), "`npBoxesNum` should be a `numpy.ndarray`"
        result = {k: v for k, v in result.items() if v is not None}
        return result

    def render(self, img):
        """
        模型预测
        返回预测结果信息
        """
        img = self.preprocess(img)
        self.model.set_inputs(img)
        self.model.run()
        n = self.model.predictor.get_num_outputs()
        res = [self.model.get_output(i) for i in range(n)]

        res = {"boxes": res[0], "boxesNum": res[1]}
        res = self.postprocess(res)
        return res

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
    def __init__(
        self,
    ):
        super(Permute, self).__init__()

    def __call__(self, im, imInfo):
        im = im.transpose((2, 0, 1)).copy()
        return im, imInfo


"""
UT: 人脸关键点检测模型测试
"""
if __name__ == "__main__":

    # 加载模型文件, 需要根据情况修改路径
    faceLandMark = FaceKeyPoint(
        "/root/Desktop/workspace/AiBox_T710_Python/res/models/faceDetection", "/root/Desktop/workspace/AiBox_T710_Python/res/models/faceLandmark")

    # 设置摄像头
    capture = cv2.VideoCapture("/dev/video0")   # 可以设置摄像头
    capture.set(cv2.CAP_PROP_FPS, 30)           # 设置视频的读取速率以及分辨率
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
        frame = cv2.flip(frame, 1)  # 画面水平翻转
        # #### 代码填空开始处 #### #              
        """            
            代码填空提示：  返回人脸检测结果，开启人脸关键点检测 
            1. 代码一共两行；
            2. 使用人脸检测模型对视频帧进行人脸检测，并返回检测结果。
            3. 使用关键点检测模型对视频帧进行关键点检测，并返回检测结果，填写参数一共三个：frame图像、人脸检测结果、阈值为0.5
        """              
        # #### 代码填空结束处 #### #
        res = faceLandMark.detector.render(frame)   # 人脸检测
        res = faceLandMark.render(frame, res, 0.5)  # 关键点检测  

        frame = faceLandMark.drawBox(frame, res)    # 绘制检测结果

        cv2.imshow("Video", frame)

        if cv2.waitKey(1) == 27:       # 按ESC退出程序
            break
    capture.release()
    cv2.destroyAllWindows()
