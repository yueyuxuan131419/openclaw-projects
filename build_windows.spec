# -*- mode: python ; coding: utf-8 -*-
# Windows build config - Fix Qt DLL issues

import sys
import os
from pathlib import Path
from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs, collect_submodules

base_dir = os.path.abspath('.')
block_cipher = None

# Collect PyQt6 dependencies
qt_binaries = []
qt_datas = []
qt_hiddenimports = []

try:
    qt_binaries = collect_dynamic_libs('PyQt6')
    qt_datas = collect_all('PyQt6')
    qt_hiddenimports = collect_submodules('PyQt6')
    print(f"Collected {len(qt_binaries)} Qt binaries")
    print(f"Collected {len(qt_datas[0])} Qt data files")
    print(f"Collected {len(qt_hiddenimports)} Qt submodules")
except Exception as e:
    print(f"Warning: Error collecting Qt deps: {e}")

# Add Qt6 DLL paths
import PyQt6
qt6_path = os.path.dirname(PyQt6.__file__)
print(f"Qt6 path: {qt6_path}")

additional_binaries = []
if os.path.exists(qt6_path):
    for dll in ['Qt6Core.dll', 'Qt6Gui.dll', 'Qt6Widgets.dll', 'Qt6Network.dll', 'Qt6Multimedia.dll']:
        dll_path = os.path.join(qt6_path, dll)
        if os.path.exists(dll_path):
            additional_binaries.append((dll_path, '.'))
    
    platforms_path = os.path.join(qt6_path, 'Qt6', 'plugins', 'platforms')
    if os.path.exists(platforms_path):
        additional_binaries.append((platforms_path, 'platforms'))
        print(f"Added platforms: {platforms_path}")
    
    styles_path = os.path.join(qt6_path, 'Qt6', 'plugins', 'styles')
    if os.path.exists(styles_path):
        additional_binaries.append((styles_path, 'styles'))

all_binaries = qt_binaries + additional_binaries

a = Analysis(
    ['main.py'],
    pathex=[base_dir],
    binaries=all_binaries,
    datas=[
        ('audio', 'audio'),
        ('config.py', '.'),
        ('utils.py', '.'),
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
        *qt_hiddenimports,
        *(qt_datas[2] if qt_datas else []),
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
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)