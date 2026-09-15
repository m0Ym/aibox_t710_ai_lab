# AiBox T710 Embedded AI Lab

> AI experiments on the AiBox T710 embedded board: object detection, face detection & landmarks,
> pose estimation, speech recognition, camera calibration, and robotic arm control.
> Python · OpenCV · PaddlePaddle · pygame.

## Features

| Experiment | Description |
|------------|-------------|
| **Object detection** | Four-color (blue/orange/purple/yellow) block classification with PicoDet |
| **Face detection & landmarks** | MTCNN / PaddleDetection + 68-point facial landmark localization |
| **Pose estimation** | PP-PicoDet pedestrian detection + TinyPose keypoint estimation |
| **Handwriting recognition** | MNIST classification |
| **Speech interaction** | PyAudio recording + offline ASR + TTS playback |
| **Camera calibration** | Chessboard calibration, intrinsics/extrinsics, undistortion |
| **Robotic arm control** | UART serial, servo angle control, pick-and-place sequences |
| **Integrated panel** | pygame GUI combining all modules, with laptop simulator mode |

## Quick Start

### Simulator mode (no hardware needed)

```powershell
cd 实验\workspace\AiBox_T710_Python
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

$env:PANEL_SIM=1
python src/panel.py
```

### Real hardware

Do not set `PANEL_SIM`; the program connects via physical serial port and camera.

### Run tests

```powershell
pytest -q
```

## Project Structure

```
├── 实验/
│   ├── cameraCalibration.py       # Camera calibration
│   ├── objectDetection.py         # Color block detection
│   ├── tracking.py                # Object tracking
│   └── workspace/
│       └── AiBox_T710_Python/     # Core project
│           ├── src/
│           │   ├── panel.py        # Main pygame GUI
│           │   ├── lib/           # Serial / speech / simulators
│           │   ├── ai/            # Object detection
│           │   ├── faceDetection/ # Face detection & landmarks
│           │   ├── poseDetection/ # Pose estimation
│           │   ├── tools/         # Calibration / data tools
│           │   └── panel/         # Panel submodules
│           ├── scripts/
│           ├── tests/
│           └── requirements.txt
└── README.md
```

## Tech Stack

Python 3 · OpenCV · PaddlePaddle (PicoDet / TinyPose) · pygame · pyserial · PyAudio · pytest

## Notes

- Model weights are not included; download them separately to run inference features.
- `deploy.py` scripts reference AI Studio cloud paths (`/home/aistudio/...`); adjust locally.
- Compiled backups (`panel(1).py`, etc.) are kept for reference; use `panel.py`.

## License

MIT
