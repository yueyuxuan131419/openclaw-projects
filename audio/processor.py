"""音频处理模块 - 声纹对抗处理"""

import numpy as np
import random
from typing import Optional
from dataclasses import dataclass

try:
    import librosa
    HAS_LIBROSA = True
except ImportError:
    HAS_LIBROSA = False

from config import AUDIO_CONFIG, VOICE_MASK_CONFIG, DEDUP_CONFIG
from utils import apply_fade


@dataclass
class ProcessingParams:
    """处理参数"""
    pitch_shift: float = 0.0          # 半音
    formant_shift: float = 0.0        # 比例
    time_stretch: float = 1.0         # 倍数
    reverb_wet: float = 0.1           # 0-1
    noise_db: float = -60.0           # dB


class VoiceProcessor:
    """声纹对抗处理器"""
    
    def __init__(self):
        self.sample_rate = AUDIO_CONFIG["sample_rate"]
        self.last_params: Optional[ProcessingParams] = None
    
    def generate_random_params(self, seed: Optional[int] = None) -> ProcessingParams:
        """生成随机处理参数"""
        if seed is not None:
            random.seed(seed)
        
        cfg = VOICE_MASK_CONFIG
        
        params = ProcessingParams(
            pitch_shift=random.uniform(*cfg["pitch_shift_range"]),
            formant_shift=random.uniform(*cfg["formant_shift_range"]),
            time_stretch=random.uniform(*cfg["time_stretch_range"]),
            reverb_wet=random.uniform(0.08, 0.15),
            noise_db=cfg["noise_floor_db"] + random.uniform(-3, 3),
        )
        
        self.last_params = params
        return params
    
    def pitch_shift(self, audio: np.ndarray, n_steps: float) -> np.ndarray:
        """音调偏移（保持时长）"""
        if not HAS_LIBROSA or abs(n_steps) < 0.1:
            return audio
        
        try:
            # 使用 phase vocoder 进行音调偏移
            return librosa.effects.pitch_shift(
                audio, 
                sr=self.sample_rate, 
                n_steps=n_steps,
                bins_per_octave=12
            )
        except Exception as e:
            print(f"音调偏移失败: {e}")
            return audio
    
    def formant_shift(self, audio: np.ndarray, shift_ratio: float) -> np.ndarray:
        """共振峰偏移（改变音色，不改变音调）"""
        if abs(shift_ratio) < 0.01:
            return audio
        
        # 使用重采样模拟共振峰偏移
        # 升高音调后降采样 = 共振峰上移
        # 降低音调后升采样 = 共振峰下移
        
        if not HAS_LIBROSA:
            return audio
        
        try:
            # 小幅音调变化
            temp_shift = shift_ratio * 2  # 转换为半音范围
            pitched = librosa.effects.pitch_shift(
                audio, sr=self.sample_rate, n_steps=temp_shift
            )
            
            # 时间拉伸恢复原音调感
            rate = 2 ** (temp_shift / 12)
            stretched = librosa.effects.time_stretch(pitched, rate=rate)
            
            # 截断或填充到原长度
            if len(stretched) > len(audio):
                return stretched[:len(audio)]
            else:
                result = np.zeros_like(audio)
                result[:len(stretched)] = stretched
                return result
        except Exception as e:
            print(f"共振峰偏移失败: {e}")
            return audio
    
    def add_reverb(self, audio: np.ndarray, room_size: float = 0.12) -> np.ndarray:
        """添加简单混响"""
        if room_size <= 0:
            return audio
        
        # 简化的 Schroeder 混响
        delay_samples = int(0.02 * self.sample_rate)  # 20ms 延迟
        
        # 早期反射
        reverb = np.zeros_like(audio)
        gain = room_size * 0.3
        
        for i, delay in enumerate([1, 2, 3, 5]):
            d = delay * delay_samples
            if d < len(audio):
                g = gain * (0.6 ** i)
                reverb[d:] += audio[:-d] * g
        
        # 混合
        wet = room_size
        return audio * (1 - wet) + reverb * wet
    
    def add_noise(self, audio: np.ndarray, noise_db: float = -60) -> np.ndarray:
        """添加微扰噪声（干扰声纹识别）"""
        # 计算信号能量
        signal_power = np.mean(audio ** 2)
        signal_db = 10 * np.log10(signal_power + 1e-10)
        
        # 计算噪声功率
        noise_power_db = signal_db + noise_db
        noise_power = 10 ** (noise_power_db / 10)
        
        # 生成高斯噪声
        noise = np.random.normal(0, np.sqrt(noise_power), len(audio))
        
        return audio + noise
    
    def time_stretch(self, audio: np.ndarray, rate: float) -> np.ndarray:
        """时间拉伸（改变语速，不改变音调）"""
        if abs(rate - 1.0) < 0.01 or not HAS_LIBROSA:
            return audio
        
        try:
            stretched = librosa.effects.time_stretch(audio, rate=rate)
            
            # 调整到原长度
            if len(stretched) > len(audio):
                return stretched[:len(audio)]
            else:
                result = np.zeros_like(audio)
                result[:len(stretched)] = stretched
                return result
        except Exception as e:
            print(f"时间拉伸失败: {e}")
            return audio
    
    def process(self, audio: np.ndarray, params: Optional[ProcessingParams] = None) -> np.ndarray:
        """
        完整处理流程
        
        处理顺序很重要：
        1. 共振峰偏移（改变音色）
        2. 音调偏移（改变音高）
        3. 时间拉伸（改变节奏）
        4. 混响（模糊声纹）
        5. 微扰噪声（干扰声纹提取）
        """
        if params is None:
            params = self.generate_random_params()
        
        result = audio.copy()
        
        # 1. 共振峰偏移（核心声纹对抗）
        if abs(params.formant_shift) > 0.001:
            result = self.formant_shift(result, params.formant_shift)
        
        # 2. 音调微调
        if abs(params.pitch_shift) > 0.1:
            result = self.pitch_shift(result, params.pitch_shift)
        
        # 3. 时间拉伸（随机语速）
        if abs(params.time_stretch - 1.0) > 0.01:
            result = self.time_stretch(result, params.time_stretch)
        
        # 4. 混响
        if params.reverb_wet > 0:
            result = self.add_reverb(result, params.reverb_wet)
        
        # 5. 微扰噪声（对抗声纹检测）
        result = self.add_noise(result, params.noise_db)
        
        # 防止削波
        max_val = np.max(np.abs(result))
        if max_val > 0.95:
            result = result * (0.95 / max_val)
        
        return result
    
    def process_segment(self, audio: np.ndarray, use_fade: bool = False) -> np.ndarray:
        """处理单个片段（可选淡入淡出）"""
        params = self.generate_random_params()
        processed = self.process(audio, params)
        
        # 只在需要时应用淡入淡出
        if use_fade:
            fade_duration = DEDUP_CONFIG["crossfade_duration"]
            processed = apply_fade(processed, fade_duration, self.sample_rate)
        
        return processed
