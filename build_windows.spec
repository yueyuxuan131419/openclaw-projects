# -*- mode: python ; coding: utf-8 -*-
# Windows 打包配置

import sys
import os
from pathlib import Path

# 项目根目录
base_dir = os.path.abspath('.')

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[base_dir],
    binaries=[],
    datas=[
        # 包含音频模块
        ('audio', 'audio'),
        # 包含配置文件
        ('config.py', '.'),
        ('utils.py', '.'),
    ],
    hiddenimports=[
        'sounddevice',
        'soundfile',
        'librosa',
        'numpy',
        'PyQt6',
        'PyQt6.sip',
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'audio.recorder',
        'audio.processor',
        'audio.player',
        'audio.sentence_detector',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # 排除不必要的模块，减小体积
        'matplotlib',
        'pandas',
        'scipy',
        'sklearn',
        'torch',
        'tensorflow',
        'PIL',
        'cv2',
        'IPython',
        'jupyter',
        'pytest',
        'tkinter',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='青丘主播替身',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 使用 UPX 压缩
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Windows 特定选项
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
