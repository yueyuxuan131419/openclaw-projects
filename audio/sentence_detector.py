"""音频分析工具 - 检测句子边界"""

import numpy as np
from typing import List, Tuple


def detect_silence_points(audio: np.ndarray, sample_rate: int, 
                         silence_threshold_db: float = -35,
                         min_silence_duration: float = 0.2,
                         min_sentence_duration: float = 0.8) -> List[int]:
    """
    检测音频中的静音点（句子边界）
    
    Args:
        audio: 音频数据
        sample_rate: 采样率
        silence_threshold_db: 静音阈值（dB），低于此值视为静音
        min_silence_duration: 最小静音时长（秒），短于此值的静音不视为句子边界
        min_sentence_duration: 最小句子时长（秒），短于此值的句子被忽略
    
    Returns:
        静音点的样本索引列表（可作为断句位置）
    """
    # 计算音频的 RMS 能量（每 5ms 一个窗口，更精细）
    window_size = int(0.005 * sample_rate)  # 5ms
    hop_size = window_size  # 无重叠，更快速
    
    # 计算每个窗口的能量
    energies = []
    positions = []
    
    for i in range(0, len(audio) - window_size, hop_size):
        window = audio[i:i + window_size]
        # RMS 能量
        rms = np.sqrt(np.mean(window ** 2))
        # 转换为 dB
        db = 20 * np.log10(rms + 1e-10)
        
        energies.append(db)
        positions.append(i)
    
    if len(energies) == 0:
        return []
    
    # 平滑能量曲线（去除毛刺）
    smoothed_energies = []
    smooth_window = 5
    for i in range(len(energies)):
        start = max(0, i - smooth_window // 2)
        end = min(len(energies), i + smooth_window // 2 + 1)
        smoothed_energies.append(np.mean(energies[start:end]))
    
    # 查找静音段
    silence_points = []
    in_silence = False
    silence_start = 0
    
    min_silence_samples = int(min_silence_duration * sample_rate / hop_size)
    min_sentence_samples = int(min_sentence_duration * sample_rate / hop_size)
    
    for i, (pos, db) in enumerate(zip(positions, smoothed_energies)):
        if db < silence_threshold_db:
            if not in_silence:
                in_silence = True
                silence_start = i
        else:
            if in_silence:
                in_silence = False
                silence_end = i
                silence_duration = silence_end - silence_start
                
                if silence_duration >= min_silence_samples:
                    # 这是一个有效的静音段，取中点作为断句位置
                    mid_idx = (silence_start + silence_end) // 2
                    silence_points.append(positions[mid_idx])
    
    # 过滤掉太短的句子
    filtered_points = []
    prev_point = 0
    
    for point in silence_points:
        if point - prev_point >= min_sentence_samples * hop_size:
            filtered_points.append(point)
            prev_point = point
    
    return filtered_points


def split_by_sentences(audio: np.ndarray, sample_rate: int) -> List[Tuple[int, int]]:
    """
    将音频按句子分割
    
    Returns:
        句子区间的列表，每个元素为 (start_sample, end_sample)
    """
    boundaries = detect_silence_points(audio, sample_rate)
    
    if len(boundaries) == 0:
        return [(0, len(audio))]
    
    sentences = []
    start = 0
    
    for boundary in boundaries:
        if boundary - start > int(0.5 * sample_rate):  # 至少0.5秒
            sentences.append((start, boundary))
            start = boundary
    
    # 添加最后一段
    if len(audio) - start > int(0.5 * sample_rate):
        sentences.append((start, len(audio)))
    
    return sentences


def find_next_sentence_boundary(audio: np.ndarray, start_pos: int, sample_rate: int,
                               target_duration: float = 15.0) -> int:
    """
    从指定位置开始，找到下一个合适的句子边界
    
    Args:
        audio: 音频数据
        start_pos: 起始位置（样本）
        target_duration: 目标时长（秒），尽量在这个时长附近断句
    
    Returns:
        断句位置（样本索引）
    """
    target_samples = int(target_duration * sample_rate)
    min_samples = int(5 * sample_rate)  # 最少5秒
    max_samples = int(30 * sample_rate)  # 最多30秒
    
    remaining = audio[start_pos:]
    if len(remaining) == 0:
        return start_pos
    
    # 在剩余音频中检测所有句子边界
    boundaries = detect_silence_points(remaining, sample_rate)
    
    # 转换为绝对位置
    boundaries = [start_pos + b for b in boundaries]
    
    # 默认用目标时长
    best_boundary = start_pos + min(len(remaining), target_samples)
    
    # 找到最接近目标时长的边界
    for boundary in boundaries:
        duration = boundary - start_pos
        
        if duration < min_samples:
            continue
        
        if duration <= max_samples:
            # 在合理范围内，选择最接近目标的
            if abs(duration - target_samples) < abs(best_boundary - start_pos - target_samples):
                best_boundary = boundary
        else:
            # 超过最大时长，使用这个边界（必须断开了）
            if best_boundary == start_pos + min(len(remaining), target_samples):
                best_boundary = boundary
            break
    
    # 如果没有找到合适的边界，就用目标时长或音频结尾
    if best_boundary == start_pos:
        best_boundary = min(start_pos + target_samples, len(audio))
    
    return min(best_boundary, len(audio))
