"""
StreamVoice Avatar - 直播声纹替身工具

使用方法:
    1. 安装依赖: pip install -r requirements.txt
    2. 运行程序: python main.py
    3. 或使用打包后的 exe 文件

打包为 exe:
    pyinstaller build.spec

目录结构:
    streamvoice-avatar/
    ├── main.py              # 主入口
    ├── config.py            # 配置
    ├── utils.py             # 工具函数
    ├── audio/
    │   ├── recorder.py      # 录制模块
    │   ├── processor.py     # 处理模块
    │   └── player.py        # 播放模块
    ├── gui/
    │   └── main_window.py   # 主界面
    ├── requirements.txt     # 依赖列表
    └── build.spec          # PyInstaller 配置

作者: OpenClaw
版本: 1.0.0
"""
