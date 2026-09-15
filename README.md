# AiBox T710 嵌入式人工智能实验项目

> 人工智能应用与实践课程的实验代码，基于 AiBox T710 嵌入式 AI 实验箱，
> 涵盖目标检测、人脸检测与关键点、人体姿态估计、语音识别与交互、相机标定、
> 机械臂控制等实验，Python + OpenCV + PaddlePaddle + pygame。

## 项目简介

本仓库收录课程中完成的实验代码与报告。核心运行环境为 AiBox T710 实验箱（ARM Linux），
同时提供笔记本模拟器模式（`PANEL_SIM=1`），无需硬件即可在 PC 上运行面板程序。

### 主要实验

| 实验 | 说明 |
|------|------|
| **彩色方块目标检测** | 四色（蓝/橙/紫/黄）方块颜色识别与分类，PicoDet 模型 |
| **人脸检测与关键点** | MTCNN / PaddleDetection 人脸检测 + 68 点关键点定位 |
| **人体姿态估计** | PP-PicoDet 行人检测 + TinyPose 关键点估计 |
| **手写数字识别** | MNIST 分类实验 |
| **语音识别与交互** | 麦克风录音 + 离线 ASR + TTS 播报 |
| **相机标定** | 棋盘格标定，内外参计算与畸变校正 |
| **机械臂控制** | UART 串口通信，舵机角度控制，抓方块动作序列 |
| **综合面板** | pygame GUI 集成以上所有功能，模拟实验箱界面 |

## 目录结构

```
人工智能应用与实践/
├── 实验/
│   ├── cameraCalibration.py       # 相机标定
│   ├── objectDetection.py         # 彩色方块目标检测
│   ├── tracking.py                # 目标追踪
│   ├── Panel资源/                 # 面板 UI 素材
│   └── workspace/
│       └── AiBox_T710_Python/     # 核心工程
│           ├── src/
│           │   ├── panel.py        # 主面板程序（pygame GUI）
│           │   ├── lib/           # 串口/语音/模拟/工具库
│           │   ├── ai/            # 目标检测
│           │   ├── faceDetection/ # 人脸检测与关键点
│           │   ├── poseDetection/ # 姿态估计
│           │   ├── tools/         # 标定/数据划分/图像采集
│           │   └── panel/        # 面板子模块
│           ├── scripts/          # 辅助脚本
│           ├── tests/           # pytest 单元测试
│           ├── res/
│           │   ├── config/      # 交互配置
│           │   ├── images/panel/# 面板 UI 图片
│           │   └── models/       # 模型文件（已 gitignore）
│           ├── requirements.txt
│           └── README_SIM.md     # 模拟器运行说明
└── README.md
```

## 快速开始

### 笔记本模拟器模式（无需硬件）

```powershell
cd 实验\workspace\AiBox_T710_Python
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 模拟器模式运行面板（使用 FakeUart / FakeCamera）
$env:PANEL_SIM=1
python src/panel.py
```

### 连接真实实验箱

不设置 `PANEL_SIM` 环境变量，程序将通过物理串口（pyserial）和摄像头（OpenCV）连接 AiBox T710。

### 运行测试

```powershell
pytest -q
```

## 技术栈

| 组件 | 技术 |
|------|------|
| 语言 | Python 3.12 |
| 视觉 | OpenCV (cv2)、Pillow |
| AI 推理 | PaddlePaddle / PicoDet / TinyPose（模型文件未入库） |
| 面板 GUI | pygame |
| 语音 | PyAudio（录音）、离线 ASR、TTS |
| 通信 | pyserial（UART 控制机械臂） |
| 测试 | pytest |

## 版权与脱敏说明

- **模型文件**（`res/models/`、`res/custommodels/`）体积较大且为第三方预训练权重，已通过 `.gitignore` 排除；
- **数据集**（训练图片、标注文件）含实验环境照片，已排除；
- **标定图片**（棋盘格照片，含实验人员身影）已排除；
- **课程课件 PDF**（`考试/` 目录）为授课材料，版权归课程方所有，未入库；
- **临时音频**（录音、TTS）已排除；
- 面板 UI 图片（`res/images/panel/`）为实验箱配套素材，保留。

## 已知限制

- 模型权重未入库，`objectDetection`、`faceDetection`、`poseDetection` 等推理功能需自行下载对应模型；
- 串口与摄像头功能需在 AiBox T710 硬件或模拟器模式下运行；
- `src/panel(1).py` 为早期备份，可能有缩进问题，运行请使用 `src/panel.py`；
- 部分 deploy 脚本路径为 AI Studio 云端路径（`/home/aistudio/...`），需按本地环境修改。
