"""工具函数"""

import numpy as np
import hashlib
import time
from typing import Tuple


def get_audio_hash(audio_data: np.ndarray) -> str:
    """获取音频指纹（用于去重）"""
    # 降采样 + 量化，生成音频指纹
    downsampled = audio_data[::100]  # 100倍降采样
    quantized = np.round(downsampled * 100).astype(np.int16)
    data_bytes = quantized.tobytes()
    return hashlib.md5(data_bytes).hexdigest()[:16]


def calculate_similarity(hash1: str, hash2: str) -> float:
    """计算两个音频指纹的相似度 (0-1)"""
    if hash1 == hash2:
        return 1.0
    # 汉明距离
    b1 = bytes.fromhex(hash1)
    b2 = bytes.fromhex(hash2)
    xor = bytes(a ^ b for a, b in zip(b1, b2))
    distance = sum(bin(byte).count('1') for byte in xor)
    max_distance = len(b1) * 8
    return 1 - (distance / max_distance)


def generate_random_params(seed: int = None) -> dict:
    """生成随机变声参数"""
    import random
    if seed is not None:
        random.seed(seed)
    
    from config import VOICE_MASK_CONFIG as cfg
    
    return {
        "pitch_shift": random.uniform(*cfg["pitch_shift_range"]),
        "formant_shift": random.uniform(*cfg["formant_shift_range"]),
        "time_stretch": random.uniform(*cfg["time_stretch_range"]),
        "reverb_wet": random.uniform(0.08, 0.15),
    }


def format_time(seconds: float) -> str:
    """格式化时间显示"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


def apply_fade(audio: np.ndarray, fade_duration: int, sample_rate: int) -> np.ndarray:
    """应用淡入淡出"""
    fade_samples = int(fade_duration * sample_rate)
    if len(audio) < fade_samples * 2:
        return audio
    
    # 淡入
    fade_in = np.linspace(0, 1, fade_samples)
    audio[:fade_samples] *= fade_in
    
    # 淡出
    fade_out = np.linspace(1, 0, fade_samples)
    audio[-fade_samples:] *= fade_out
    
    return audio
