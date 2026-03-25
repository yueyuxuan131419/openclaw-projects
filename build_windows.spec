# -*- mode: python ; coding: utf-8 -*-
# Windows 打包配置 - 修复 Qt DLL 问题

import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs, collect_submodules

# 项目根目录
base_dir = os.path.abspath('.')

block_cipher = None

# ===== 关键修复：收集 PyQt6 所有依赖 =====
qt_binaries = []
qt_datas = []
qt_hiddenimports = []

# 收集所有 Qt6 相关的 DLL 和数据文件
try:
    qt_binaries = collect_dynamic_libs('PyQt6')
    qt_datas = collect_all('PyQt6')
    qt_hiddenimports = collect_submodules('PyQt6')
    print(f"✓ 收集到 {len(qt_binaries)} 个 Qt 二进制文件")
    print(f"✓ 收集到 {len(qt_datas[0])} 个 Qt 数据文件")
    print(f"✓ 收集到 {len(qt_hiddenimports)} 个 Qt 子模块")
except Exception as e:
    print(f"⚠ 收集 Qt 依赖时出错: {e}")

# 手动添加 Qt6 核心 DLL 路径（备选方案）
import PyQt6
qt6_path = os.path.dirname(PyQt6.__file__)
print(f"Qt6 安装路径: {qt6_path}")

# 添加额外的 binaries（确保 DLL 被包含）
additional_binaries = []
if os.path.exists(qt6_path):
    # 添加 Qt6*.dll 文件
    for dll in ['Qt6Core.dll', 'Qt6Gui.dll', 'Qt6Widgets.dll', 'Qt6Network.dll', 'Qt6Multimedia.dll']:
        dll_path = os.path.join(qt6_path, dll)
        if os.path.exists(dll_path):
            additional_binaries.append((dll_path, '.'))
    
    # 添加 platforms 文件夹（关键！）
    platforms_path = os.path.join(qt6_path, 'Qt6', 'plugins', 'platforms')
    if os.path.exists(platforms_path):
        additional_binaries.append((platforms_path, 'platforms'))
        print(f"✓ 添加 platforms 文件夹: {platforms_path}")
    
    # 添加 styles 文件夹
    styles_path = os.path.join(qt6_path, 'Qt6', 'plugins', 'styles')
    if os.path.exists(styles_path):
        additional_binaries.append((styles_path, 'styles'))

# 合并所有 binaries
all_binaries = qt_binaries + additional_binaries

a = Analysis(
    ['main.py'],
    pathex=[base_dir],
    binaries=all_binaries,
    datas=[
        # 包含音频模块
        ('audio', 'audio'),
        # 包含配置文件
        ('config.py', '.'),
        ('utils.py', '.'),
        # 包含 Qt 数据文件
        *(qt_datas[0] if qt_datas else []),
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
        'PyQt6.QtNetwork',
        'PyQt6.QtMultimedia',
        'PyQt6.QtMultimediaWidgets',
        # 添加所有 Qt 子模块
        *qt_hiddenimports,
        *qt_datas[2] if qt_datas else [],
        # 音频模块
        'audio.recorder',
        'audio.processor',
        'audio.player',
        'audio.sentence_detector',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
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
    name='QingqiuAvatar',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # 禁用 UPX 压缩（可能导致 DLL 问题）
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # 临时开启控制台窗口以便查看错误信息
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
