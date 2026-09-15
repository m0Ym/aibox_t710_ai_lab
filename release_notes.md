# v1.0.0 初始发布

## 内容

AiBox T710 嵌入式人工智能实验课程代码与报告：

- **目标检测**：四色方块识别（PicoDet）、目标追踪
- **人脸检测与关键点**：MTCNN / PaddleDetection 人脸检测 + 68 点关键点
- **人体姿态估计**：PP-PicoDet 行人检测 + TinyPose 关键点
- **语音交互**：PyAudio 录音 + 离线 ASR + TTS
- **相机标定**：棋盘格内外参标定与畸变校正
- **机械臂控制**：UART 串口舵机控制，抓方块动作序列
- **综合面板**：pygame GUI 集成所有功能，支持笔记本模拟器模式（`PANEL_SIM=1`）
- 实验报告（Word）

## 技术栈

Python 3 + OpenCV + PaddlePaddle + pygame + pyserial + PyAudio + pytest

## 已排除

- 模型权重文件（`res/models/`、`res/custommodels/`，需自行下载）
- 训练数据集与标定图片（体积大、含实验人员照片）
- 课程课件 PDF（版权归课程方）
- 虚拟环境、`__pycache__`、临时音频
