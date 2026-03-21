"""音频录制模块 - 环形缓冲区录制"""

import queue
import threading
import numpy as np
import sounddevice as sd
import soundfile as sf
from io import BytesIO
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable

from config import AUDIO_CONFIG, TEMP_DIR


class AudioRecorder:
    """音频录制器 - 不限时长录制"""
    
    def __init__(self, on_buffer_update: Optional[Callable] = None):
        self.sample_rate = AUDIO_CONFIG["sample_rate"]
        self.channels = AUDIO_CONFIG["channels"]
        self.chunk_duration = AUDIO_CONFIG["chunk_duration"]
        
        # 初始分配1分钟的缓冲区，会自动扩容
        self.initial_duration = 60  # 初始1分钟
        self.buffer_duration = self.initial_duration
        
        # 计算缓冲区大小
        self.max_samples = int(self.buffer_duration * self.sample_rate)
        self.chunk_samples = int(self.chunk_duration * self.sample_rate)
        
        # 环形缓冲区
        self.buffer = np.zeros(self.max_samples, dtype=np.float32)
        self.write_pos = 0
        self.total_recorded = 0
        
        # 状态
        self.is_recording = False
        self.stream = None
        self._thread = None
        self._stop_event = threading.Event()
        
        # 回调
        self.on_buffer_update = on_buffer_update
        
        # 音频队列（用于实时处理）
        self.audio_queue = queue.Queue(maxsize=100)
    
    def _audio_callback(self, indata, frames, time_info, status):
        """音频流回调 - 支持动态扩容"""
        if status:
            print(f"音频状态: {status}")
        
        # 获取单声道数据
        audio_chunk = indata[:, 0].copy()
        chunk_size = len(audio_chunk)
        
        # 检查是否需要扩容（当已录制接近缓冲区大小时）
        if self.total_recorded + chunk_size > self.max_samples * 0.9:
            # 扩容50%
            new_duration = self.buffer_duration * 1.5
            new_max_samples = int(new_duration * self.sample_rate)
            
            # 创建新缓冲区并复制旧数据
            new_buffer = np.zeros(new_max_samples, dtype=np.float32)
            
            # 复制已有数据
            if self.total_recorded > 0:
                valid_samples = min(self.total_recorded, self.max_samples)
                if self.write_pos >= valid_samples:
                    new_buffer[:valid_samples] = self.buffer[self.write_pos - valid_samples:self.write_pos]
                else:
                    # 数据环绕
                    tail_len = valid_samples - self.write_pos
                    new_buffer[:tail_len] = self.buffer[-tail_len:]
                    new_buffer[tail_len:valid_samples] = self.buffer[:self.write_pos]
                
                self.write_pos = valid_samples
            
            self.buffer = new_buffer
            self.max_samples = new_max_samples
            self.buffer_duration = new_duration
            print(f"缓冲区扩容至: {self.buffer_duration/60:.1f} 分钟")
        
        # 写入缓冲区（追加模式，不覆盖）
        if self.write_pos + chunk_size <= self.max_samples:
            self.buffer[self.write_pos:self.write_pos + chunk_size] = audio_chunk
        else:
            # 绕回缓冲区开头（环形）
            first_part = self.max_samples - self.write_pos
            self.buffer[self.write_pos:] = audio_chunk[:first_part]
            self.buffer[:chunk_size - first_part] = audio_chunk[first_part:]
        
        self.write_pos = (self.write_pos + chunk_size) % self.max_samples
        self.total_recorded += chunk_size
        
        # 放入队列供其他模块使用
        try:
            self.audio_queue.put_nowait(audio_chunk)
        except queue.Full:
            pass
        
        # 通知更新
        if self.on_buffer_update:
            self.on_buffer_update()
    
    def start(self, input_device: Optional[int] = None) -> bool:
        """开始录制"""
        if self.is_recording:
            return True
        
        try:
            self.stream = sd.InputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.float32,
                blocksize=self.chunk_samples,
                callback=self._audio_callback,
                device=input_device
            )
            self.stream.start()
            self.is_recording = True
            self._stop_event.clear()
            return True
        except Exception as e:
            print(f"启动录制失败: {e}")
            return False
    
    def stop(self):
        """停止录制"""
        self.is_recording = False
        self._stop_event.set()
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
    
    def get_buffer_duration(self) -> float:
        """获取当前缓冲区有效时长（秒）"""
        valid_samples = min(self.total_recorded, self.max_samples)
        return valid_samples / self.sample_rate
    
    def get_buffer_percentage(self) -> float:
        """获取缓冲区填充百分比（以30分钟为参考）"""
        reference_duration = 30 * 60  # 30分钟作为参考
        return min(100, (self.get_buffer_duration() / reference_duration) * 100)
    
    def get_recent_audio(self, duration: float) -> np.ndarray:
        """获取最近指定时长的音频"""
        samples_needed = int(duration * self.sample_rate)
        samples_available = min(samples_needed, min(self.total_recorded, self.max_samples))
        
        if samples_available == 0:
            return np.array([], dtype=np.float32)
        
        # 从 write_pos 向前读取
        result = np.zeros(samples_available, dtype=np.float32)
        
        if self.write_pos >= samples_available:
            result = self.buffer[self.write_pos - samples_available:self.write_pos].copy()
        else:
            # 需要绕回缓冲区末尾
            first_part = samples_available - self.write_pos
            result[:first_part] = self.buffer[-first_part:]
            result[first_part:] = self.buffer[:self.write_pos]
        
        return result
    
    def get_random_segment(self, segment_duration: float, jitter: float = 0) -> np.ndarray:
        """获取随机位置的音频片段"""
        available_duration = self.get_buffer_duration()
        if available_duration < segment_duration:
            return np.array([], dtype=np.float32)
        
        import random
        
        # 随机位置（考虑 jitter）
        max_start = available_duration - segment_duration - jitter
        if max_start <= 0:
            start_offset = 0
        else:
            start_offset = random.uniform(0, max_start)
        
        # 加上随机 jitter
        if jitter > 0:
            start_offset += random.uniform(-jitter, jitter)
            start_offset = max(0, min(start_offset, available_duration - segment_duration))
        
        return self.get_audio_at_position(start_offset, segment_duration)
    
    def get_audio_at_position(self, start_pos: float, duration: float) -> np.ndarray:
        """从指定位置（秒）获取音频片段"""
        available_duration = self.get_buffer_duration()
        
        if start_pos >= available_duration or duration <= 0:
            return np.array([], dtype=np.float32)
        
        # 限制不超出范围
        duration = min(duration, available_duration - start_pos)
        
        start_sample = int(start_pos * self.sample_rate)
        end_sample = start_sample + int(duration * self.sample_rate)
        
        # 从缓冲区读取
        samples_available = min(self.total_recorded, self.max_samples)
        
        # 计算实际读取位置（考虑环形缓冲区）
        # 数据是从 write_pos 向前 samples_available 个样本
        buffer_start = (self.write_pos - samples_available) % self.max_samples
        
        actual_start = (buffer_start + start_sample) % self.max_samples
        actual_end = (buffer_start + end_sample) % self.max_samples
        
        if actual_start < actual_end:
            return self.buffer[actual_start:actual_end].copy()
        else:
            # 绕回
            first_part = self.buffer[actual_start:].copy()
            second_part = self.buffer[:actual_end].copy()
            return np.concatenate([first_part, second_part])
    
    def get_all_audio(self) -> np.ndarray:
        """获取所有已录制的音频（连续的一段）"""
        valid_samples = min(self.total_recorded, self.max_samples)
        
        if valid_samples == 0:
            return np.array([], dtype=np.float32)
        
        result = np.zeros(valid_samples, dtype=np.float32)
        
        if self.write_pos >= valid_samples:
            # 数据连续
            result = self.buffer[self.write_pos - valid_samples:self.write_pos].copy()
        else:
            # 数据环绕
            tail_len = valid_samples - self.write_pos
            result[:tail_len] = self.buffer[-tail_len:]
            result[tail_len:] = self.buffer[:self.write_pos]
        
        return result
    
    def save_buffer_to_file(self, filepath: Optional[Path] = None) -> Path:
        """保存当前缓冲区到文件"""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = TEMP_DIR / f"buffer_{timestamp}.mp3"
        
        audio_data = self.get_recent_audio(self.get_buffer_duration())
        
        if len(audio_data) > 0:
            sf.write(str(filepath), audio_data, self.sample_rate, format='MP3', 
                    subtype='MPEG_LAYER_III', bitrate=AUDIO_CONFIG["mp3_bitrate"])
        
        return filepath
