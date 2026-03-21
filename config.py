"""StreamVoice Avatar - 直播声纹替身程序"""

import os
from pathlib import Path

# 版本信息
VERSION = "1.0.0"
APP_NAME = "青丘主播替身"

# 音频配置
AUDIO_CONFIG = {
    "sample_rate": 44100,
    "channels": 1,
    "chunk_duration": 0.1,  # 100ms 块
    "mp3_bitrate": "128k",
}

# 声纹对抗处理参数 - 调小幅度，保持自然
VOICE_MASK_CONFIG = {
    "pitch_shift_range": (-0.3, 0.3),      # 半音范围 ±0.3（更自然）
    "formant_shift_range": (-0.02, 0.02),  # 共振峰偏移 ±2%（微妙变化）
    "time_stretch_range": (0.98, 1.02),    # 时间拉伸 ±2%
    "reverb_room_size": 0.08,              # 混响房间大小（轻微）
    "noise_floor_db": -65,                 # 微扰噪声 dB（更低）
}

# 去重配置
DEDUP_CONFIG = {
    "position_jitter": 5,        # 位置随机偏移 ±5秒
    "min_segment": 2,            # 最小片段 2秒
    "max_segment": 5,            # 最大片段 5秒
    "crossfade_duration": 0.03,  # 淡入淡出 30ms
}

# 路径配置
APP_DIR = Path.home() / ".streamvoice-avatar"
TEMP_DIR = APP_DIR / "temp"
CONFIG_FILE = APP_DIR / "config.json"

# 创建目录
def ensure_dirs():
    APP_DIR.mkdir(exist_ok=True)
    TEMP_DIR.mkdir(exist_ok=True)

ensure_dirs()
