# 在笔记本上运行实验箱（模拟器模式）📋

快速步骤（Windows）:

1. 打开 PowerShell，切换到项目根目录
2. 创建并安装依赖（只需一次）:
   .\scripts\setup_venv.ps1
3. 激活虚拟环境并运行（每次打开新 shell）:
   .\venv\Scripts\Activate.ps1
   .\scripts\run_panel_sim.ps1

说明:
- 启动脚本会设置环境变量 `PANEL_SIM=1`，程序会启用 `src/lib/simulators.py` 提供的 `FakeUart` 与 `FakeCamera`，无需物理硬件。
- 如果你希望连接真实设备，不要设置 `PANEL_SIM`，程序将尝试使用物理串口和摄像头。
- 常见依赖已列在 `requirements.txt` 中（opencv-python, numpy, Pillow, pygame, pyserial, keyboard, pyaudio, pytest, requests）。+
+注意：仓库包含一个 `src/panel(1).py`，它目前看上去包含重复或损坏代码（缩进错误）。请使用 `src/panel.py` 作为运行入口；如果你想我修复 `panel(1).py` 我也可以进一步处理。
小提示 💡:
- Windows 上安装 `pyaudio` 可能需要对应的 wheel，或使用 `pipwin` 安装。
- 模拟相机会优先使用 `res/images/panel/` 下的图片作为帧序列。可把一些样例图片放到该目录来测试显示效果。

运行和测试示例:
- 运行面板（模拟器模式）: 先激活 venv，然后执行 `.\scripts\run_panel_sim.ps1`
- 运行单元测试: 激活 venv 后运行 `pytest -q`
