"""音频播放模块 - 直接播放长音频"""

import queue
import threading
import numpy as np
import sounddevice as sd
from typing import Optional, Callable

from config import AUDIO_CONFIG


class AudioPlayer:
    """音频播放器 - 支持长音频直接播放"""
    
    def __init__(self, on_playback_state_change: Optional[Callable] = None):
        self.sample_rate = AUDIO_CONFIG["sample_rate"]
        self.channels = AUDIO_CONFIG["channels"]
        
        # 播放队列 - 存放大段音频而不是小块
        self.playback_queue = queue.Queue(maxsize=5)  # 减少容量，存放大段
        
        # 当前播放的音频段
        self.current_audio = None
        self.current_pos = 0
        
        # 状态
        self.is_playing = False
        self.stream = None
        self._lock = threading.Lock()
        
        # 回调
        self.on_playback_state_change = on_playback_state_change
    
    def _playback_callback(self, outdata, frames, time_info, status):
        """播放回调 - 从当前音频段读取"""
        if status:
            print(f"播放状态: {status}")
        
        with self._lock:
            # 如果当前没有音频或已播放完，从队列取新的
            if self.current_audio is None or self.current_pos >= len(self.current_audio):
                try:
                    self.current_audio = self.playback_queue.get_nowait()
                    self.current_pos = 0
                    print(f"开始播放新段，长度: {len(self.current_audio)/self.sample_rate:.1f}秒")
                except queue.Empty:
                    outdata.fill(0)
                    return
            
            # 从当前位置读取数据
            remaining = len(self.current_audio) - self.current_pos
            
            if remaining >= frames:
                # 数据足够
                outdata[:, 0] = self.current_audio[self.current_pos:self.current_pos + frames]
                self.current_pos += frames
            else:
                # 数据不够，复制剩余部分，其余补零
                outdata[:remaining, 0] = self.current_audio[self.current_pos:]
                outdata[remaining:, 0] = 0
                self.current_pos = len(self.current_audio)
    
    def start(self, output_device: Optional[int] = None) -> bool:
        """开始播放"""
        if self.is_playing:
            return True
        
        try:
            # 使用较大的块大小以减少回调次数
            blocksize = 2048  # 约 46ms @ 44.1kHz
            
            self.stream = sd.OutputStream(
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype=np.float32,
                blocksize=blocksize,
                callback=self._playback_callback,
                device=output_device
            )
            self.stream.start()
            self.is_playing = True
            
            # 清空状态
            with self._lock:
                self.current_audio = None
                self.current_pos = 0
            
            self.clear_queue()
            
            if self.on_playback_state_change:
                self.on_playback_state_change(True)
            
            return True
        except Exception as e:
            print(f"启动播放失败: {e}")
            return False
    
    def stop(self):
        """停止播放"""
        self.is_playing = False
        
        with self._lock:
            self.current_audio = None
            self.current_pos = 0
        
        self.clear_queue()
        
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        
        if self.on_playback_state_change:
            self.on_playback_state_change(False)
    
    def queue_audio(self, audio: np.ndarray, block: bool = True, timeout: float = 30.0) -> bool:
        """将完整音频段加入播放队列
        
        Args:
            audio: 完整音频数据（不分割）
            block: 是否阻塞等待
            timeout: 阻塞超时时间
        """
        try:
            self.playback_queue.put(audio.copy(), block=block, timeout=timeout)
            return True
        except queue.Full:
            print("警告: 播放队列已满")
            return False
    
    def clear_queue(self):
        """清空播放队列"""
        with self._lock:
            self.current_audio = None
            self.current_pos = 0
        
        while not self.playback_queue.empty():
            try:
                self.playback_queue.get_nowait()
            except queue.Empty:
                break
