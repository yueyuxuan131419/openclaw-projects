"""GUI 主窗口 - 青丘主播替身"""

import sys
import random
import numpy as np
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QPushButton, QProgressBar, QComboBox,
    QGroupBox, QMessageBox, QApplication
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QFont

import sounddevice as sd

from config import APP_NAME, VERSION, AUDIO_CONFIG
from audio.recorder import AudioRecorder
from audio.processor import VoiceProcessor
from audio.player import AudioPlayer
from audio.sentence_detector import find_next_sentence_boundary
from utils import format_time


class PlaybackWorker(QThread):
    """后台播放工作线程 - 智能断句顺序播放（支持暂停/继续）"""
    
    error_occurred = pyqtSignal(str)
    segment_played = pyqtSignal(float)
    
    def __init__(self, recorder: AudioRecorder, processor: VoiceProcessor, player: AudioPlayer, start_pos: int = 0):
        super().__init__()
        self.recorder = recorder
        self.processor = processor
        self.player = player
        self.running = False
        self.current_pos = start_pos  # 当前播放位置（样本）
        self.paused = False
    
    def get_current_position(self) -> int:
        """获取当前播放位置（用于暂停后恢复）"""
        return self.current_pos
    
    def run(self):
        """播放循环 - 在句子边界处断开，顺序播放"""
        self.running = True
        
        while self.running:
            if not self.player.is_playing:
                break
            
            try:
                total_duration = self.recorder.get_buffer_duration()
                if total_duration < 5:
                    self.msleep(100)
                    continue
                
                # 获取全部音频
                full_audio = self.recorder.get_all_audio()
                if len(full_audio) == 0:
                    self.msleep(100)
                    continue
                
                # 如果已经到结尾，从头开始
                if self.current_pos >= len(full_audio):
                    self.current_pos = 0
                
                # 智能断句：找到下一个句子边界
                end_pos = find_next_sentence_boundary(
                    full_audio, 
                    self.current_pos, 
                    self.recorder.sample_rate,
                    target_duration=random.uniform(10, 18)  # 10-18秒目标，更短的句子
                )
                
                # 确保至少取2秒
                min_end = self.current_pos + int(2 * self.recorder.sample_rate)
                end_pos = max(end_pos, min_end)
                
                # 提取这一段
                audio_segment = full_audio[self.current_pos:end_pos]
                
                if len(audio_segment) < self.recorder.sample_rate * 2:
                    # 剩余太少，从头开始
                    self.current_pos = 0
                    continue
                
                # 发送段信息
                segment_duration = len(audio_segment) / self.recorder.sample_rate
                self.segment_played.emit(segment_duration)
                
                # 处理并播放
                processed = self.processor.process(audio_segment)
                success = self.player.queue_audio(processed, block=True, timeout=60.0)
                
                if success:
                    # 推进位置
                    self.current_pos = end_pos
                else:
                    print("排队音频失败")
                    
            except Exception as e:
                self.error_occurred.emit(str(e))
                self.msleep(100)
    
    def stop(self):
        """停止播放"""
        self.running = False
        self.wait(1000)


class MainWindow(QMainWindow):
    """主窗口"""
    
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle(f"{APP_NAME} v{VERSION}")
        self.setMinimumSize(550, 450)
        
        # 音频组件
        self.recorder = AudioRecorder(on_buffer_update=self.on_buffer_update)
        self.processor = VoiceProcessor()
        self.player = AudioPlayer(on_playback_state_change=self.on_playback_state_change)
        
        # 播放工作线程
        self.playback_worker = None
        self.saved_playback_position = 0  # 保存播放位置（用于暂停后继续）
        
        # 状态
        self.is_recording = False
        self.is_playing = False
        self.total_recorded_duration = 0  # 录制总时长（用于倒计时）
        self.remaining_time = 0  # 剩余时间
        self.previous_mode = None  # 记录上一个模式（'live', 'interact', 'avatar'）  # 剩余时间
        
        self.init_ui()
        self.init_timer()
        self.refresh_devices()
    
    def init_ui(self):
        """初始化界面"""
        central = QWidget()
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # 标题
        title = QLabel("🦊 青丘主播替身")
        title_font = QFont()
        title_font.setPointSize(18)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        subtitle = QLabel("智能音频替身 - 主播休息好帮手")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet("color: gray;")
        layout.addWidget(subtitle)
        
        layout.addSpacing(20)
        
        # 设备选择
        device_group = QGroupBox("音频设备")
        device_layout = QVBoxLayout(device_group)
        
        # 输入设备
        input_layout = QHBoxLayout()
        input_layout.addWidget(QLabel("麦克风:"))
        self.input_combo = QComboBox()
        self.input_combo.setMinimumWidth(300)
        input_layout.addWidget(self.input_combo)
        device_layout.addLayout(input_layout)
        
        # 输出设备
        output_layout = QHBoxLayout()
        output_layout.addWidget(QLabel("输出到:"))
        self.output_combo = QComboBox()
        self.output_combo.setMinimumWidth(300)
        output_layout.addWidget(self.output_combo)
        device_layout.addLayout(output_layout)
        
        layout.addWidget(device_group)
        
        # 录制状态
        status_group = QGroupBox("录制状态")
        status_layout = QVBoxLayout(status_group)
        
        # 录制指示器
        self.record_indicator = QLabel("⭕ 未录制")
        self.record_indicator.setStyleSheet("color: gray; font-size: 14px;")
        status_layout.addWidget(self.record_indicator)
        
        # 时长显示
        self.time_label = QLabel("已录制: 00:00")
        self.time_label.setStyleSheet("font-size: 16px;")
        status_layout.addWidget(self.time_label)
        
        # 进度条
        self.buffer_progress = QProgressBar()
        self.buffer_progress.setRange(0, 100)
        self.buffer_progress.setValue(0)
        self.buffer_progress.setTextVisible(True)
        self.buffer_progress.setFormat("录制进度: %p%")
        status_layout.addWidget(self.buffer_progress)
        
        layout.addWidget(status_group)
        
        # 主控制按钮区域 - 三个按钮
        button_layout = QHBoxLayout()
        
        # 直播模式按钮
        self.live_button = QPushButton("🎤 直播")
        self.live_button.setMinimumHeight(60)
        self.live_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #1565C0;
            }
            QPushButton:checked {
                background-color: #0D47A1;
                border: 3px solid #FFC107;
            }
        """)
        self.live_button.setCheckable(True)
        self.live_button.clicked.connect(self.on_live_mode_clicked)
        button_layout.addWidget(self.live_button)
        
        # 互动模式按钮
        self.interact_button = QPushButton("💬 互动")
        self.interact_button.setMinimumHeight(60)
        self.interact_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:pressed {
                background-color: #E65100;
            }
            QPushButton:checked {
                background-color: #BF360C;
                border: 3px solid #FFC107;
            }
        """)
        self.interact_button.setCheckable(True)
        self.interact_button.clicked.connect(self.on_interact_mode_clicked)
        button_layout.addWidget(self.interact_button)
        
        # 替身模式按钮
        self.avatar_button = QPushButton("🤖 替身")
        self.avatar_button.setMinimumHeight(60)
        self.avatar_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-size: 14px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
            QPushButton:checked {
                background-color: #2E7D32;
                border: 3px solid #FFC107;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.avatar_button.setCheckable(True)
        self.avatar_button.clicked.connect(self.on_avatar_mode_clicked)
        button_layout.addWidget(self.avatar_button)
        
        layout.addLayout(button_layout)
        
        # 当前模式
        self.mode_label = QLabel("当前状态: ⏸️ 待机中")
        self.mode_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.mode_label.setStyleSheet("font-size: 14px; color: gray;")
        layout.addWidget(self.mode_label)
        
        # 替身模式倒计时显示
        self.countdown_label = QLabel("")
        self.countdown_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.countdown_label.setStyleSheet("font-size: 18px; color: #f44336; font-weight: bold;")
        self.countdown_label.hide()
        layout.addWidget(self.countdown_label)
        
        # 说明文字
        hint = QLabel("直播=录制 | 互动=暂停 | 替身=播放")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color: gray; font-size: 12px;")
        layout.addWidget(hint)
        
        layout.addStretch()
        
        # 底部按钮
        bottom_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("刷新设备")
        self.refresh_btn.clicked.connect(self.refresh_devices)
        bottom_layout.addWidget(self.refresh_btn)
        
        bottom_layout.addStretch()
        
        self.about_btn = QPushButton("关于")
        self.about_btn.clicked.connect(self.show_about)
        bottom_layout.addWidget(self.about_btn)
        
        layout.addLayout(bottom_layout)
    
    def init_timer(self):
        """初始化定时器"""
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self.update_status)
        self.update_timer.start(500)
        
        # 倒计时定时器（每秒更新）
        self.countdown_timer = QTimer()
        self.countdown_timer.timeout.connect(self.update_countdown)
    
    def refresh_devices(self):
        """刷新设备列表"""
        self.input_combo.clear()
        self.output_combo.clear()
        
        try:
            devices = sd.query_devices()
            
            default_input = sd.default.device[0]
            for i, dev in enumerate(devices):
                if dev['max_input_channels'] > 0:
                    name = f"{dev['name']}"
                    self.input_combo.addItem(name, i)
                    if i == default_input:
                        self.input_combo.setCurrentIndex(self.input_combo.count() - 1)
            
            default_output = sd.default.device[1]
            for i, dev in enumerate(devices):
                if dev['max_output_channels'] > 0:
                    name = f"{dev['name']}"
                    self.output_combo.addItem(name, i)
                    if i == default_output:
                        self.output_combo.setCurrentIndex(self.output_combo.count() - 1)
        
        except Exception as e:
            QMessageBox.warning(self, "错误", f"无法获取音频设备: {e}")
    
    def on_buffer_update(self):
        """缓冲区更新回调"""
        pass
    
    def on_playback_state_change(self, playing: bool):
        """播放状态变化回调"""
        self.is_playing = playing
    
    def update_status(self):
        """更新状态显示"""
        if self.recorder.is_recording:
            self.record_indicator.setText("🔴 录制中")
            self.record_indicator.setStyleSheet("color: red; font-size: 14px;")
        else:
            self.record_indicator.setText("⭕ 未录制")
            self.record_indicator.setStyleSheet("color: gray; font-size: 14px;")
        
        duration = self.recorder.get_buffer_duration()
        self.time_label.setText(f"已录制: {format_time(duration)}")
        
        percentage = min(100, (duration / (30 * 60)) * 100)
        self.buffer_progress.setValue(int(percentage))
        
        if percentage < 30:
            self.buffer_progress.setStyleSheet("QProgressBar::chunk { background-color: #ff9800; }")
        elif percentage < 80:
            self.buffer_progress.setStyleSheet("QProgressBar::chunk { background-color: #2196F3; }")
        else:
            self.buffer_progress.setStyleSheet("QProgressBar::chunk { background-color: #4CAF50; }")
        
        # 更新按钮状态
        has_recorded = duration > 0
        self.avatar_button.setEnabled(has_recorded)

    def update_countdown(self):
        """更新倒计时显示"""
        if self.remaining_time > 0:
            self.remaining_time -= 1
            self.countdown_label.setText(f"⏱️ 剩余: {format_time(self.remaining_time)}")
            
            # 剩余时间少于1分钟时变红色闪烁
            if self.remaining_time < 60:
                self.countdown_label.setStyleSheet("font-size: 18px; color: #f44336; font-weight: bold; background-color: #FFEBEE;")
            elif self.remaining_time < 180:
                self.countdown_label.setStyleSheet("font-size: 18px; color: #FF9800; font-weight: bold;")
        else:
            # 时间到了
            self.countdown_label.setText("⏱️ 时间到！请切回直播模式")
            self.countdown_label.setStyleSheet("font-size: 18px; color: white; font-weight: bold; background-color: #f44336;")
    
    def unckeck_all_buttons(self):
        """取消所有按钮的选中状态"""
        self.live_button.setChecked(False)
        self.live_button.setText("🎤 直播")
        
        self.interact_button.setChecked(False)
        self.interact_button.setText("💬 互动")
        
        self.avatar_button.setChecked(False)
        self.avatar_button.setText("🤖 替身")
        
        # 恢复设备选择
        self.input_combo.setEnabled(True)
        self.output_combo.setEnabled(True)
    
    def on_live_mode_clicked(self):
        """直播模式按钮点击"""
        if self.live_button.isChecked():
            # 切换到直播模式
            was_avatar = self.previous_mode == 'avatar'
            
            self.stop_avatar_mode()
            self.stop_interact_mode()
            
            # 只有从替身模式切换过来时才清空
            # 从互动模式切换不清空
            if was_avatar:
                self.reset_recorder()
                print("从替身模式切换，清空录制内容")
            elif self.recorder.get_buffer_duration() == 0:
                # 首次进入也清空（其实没有内容）
                self.reset_recorder()
            
            self.start_live_mode()
            self.previous_mode = 'live'
        else:
            self.stop_live_mode()
    
    def on_interact_mode_clicked(self):
        """互动模式按钮点击"""
        if self.interact_button.isChecked():
            # 切换到互动模式
            self.stop_avatar_mode()
            self.stop_live_mode()
            self.start_interact_mode()
            self.previous_mode = 'interact'
        else:
            self.stop_interact_mode()
    
    def on_avatar_mode_clicked(self):
        """替身模式按钮点击"""
        if self.avatar_button.isChecked():
            # 切换到替身模式
            self.stop_live_mode()
            self.stop_interact_mode()
            self.start_avatar_mode()
            self.previous_mode = 'avatar'
        else:
            self.stop_avatar_mode()
    
    def reset_recorder(self):
        """重置录制器，清空所有已录制音频"""
        self.recorder.stop()
        from audio.recorder import AudioRecorder
        self.recorder = AudioRecorder(on_buffer_update=self.on_buffer_update)
        print("录制器已重置，音频已清空")
        self.total_recorded_duration = 0
    
    def start_live_mode(self):
        """开始直播模式（录制）"""
        self.unckeck_all_buttons()
        
        input_idx = self.input_combo.currentData()
        if self.recorder.start(input_idx):
            self.live_button.setChecked(True)
            self.live_button.setText("🎤 直播中")
            self.mode_label.setText("当前状态: 🎤 直播录制中")
            self.mode_label.setStyleSheet("font-size: 14px; color: #2196F3;")
            self.countdown_label.hide()
            
            # 禁用其他按钮
            self.interact_button.setEnabled(True)
            self.avatar_button.setEnabled(False)
        else:
            self.live_button.setChecked(False)
            QMessageBox.critical(self, "错误", "无法启动音频录制")
    
    def stop_live_mode(self):
        """停止直播模式"""
        self.recorder.stop()
        
        # 保存录制时长（用于倒计时）
        self.total_recorded_duration = self.recorder.get_buffer_duration()
        
        self.unckeck_all_buttons()
        
        has_recorded = self.recorder.get_buffer_duration() > 0
        if has_recorded:
            self.mode_label.setText("当前状态: ⏸️ 已暂停（有录制内容）")
            self.mode_label.setStyleSheet("font-size: 14px; color: #FF9800;")
        else:
            self.mode_label.setText("当前状态: ⏸️ 待机中")
            self.mode_label.setStyleSheet("font-size: 14px; color: gray;")
        
        self.avatar_button.setEnabled(has_recorded)
    
    def start_interact_mode(self):
        """开始互动模式（不录制、不播放）"""
        self.unckeck_all_buttons()
        
        # 确保录制和播放都停止
        self.recorder.stop()
        
        self.interact_button.setChecked(True)
        self.interact_button.setText("💬 互动中")
        self.mode_label.setText("当前状态: 💬 互动模式（不录制）")
        self.mode_label.setStyleSheet("font-size: 14px; color: #FF9800;")
        self.countdown_label.hide()
        
        # 互动模式下可以切换到其他模式
        self.live_button.setEnabled(True)
        has_recorded = self.recorder.get_buffer_duration() > 0
        self.avatar_button.setEnabled(has_recorded)
    
    def stop_interact_mode(self):
        """停止互动模式"""
        self.unckeck_all_buttons()
        
        has_recorded = self.recorder.get_buffer_duration() > 0
        if has_recorded:
            self.mode_label.setText("当前状态: ⏸️ 已暂停（有录制内容）")
            self.mode_label.setStyleSheet("font-size: 14px; color: #FF9800;")
        else:
            self.mode_label.setText("当前状态: ⏸️ 待机中")
            self.mode_label.setStyleSheet("font-size: 14px; color: gray;")
        
        self.avatar_button.setEnabled(has_recorded)
    
    def start_avatar_mode(self):
        """开始替身模式"""
        if self.recorder.get_buffer_duration() < 5:
            QMessageBox.warning(self, "提示", "请先录制至少5秒音频")
            self.avatar_button.setChecked(False)
            return
        
        self.unckeck_all_buttons()
        
        output_idx = self.output_combo.currentData()
        if not self.player.start(output_idx):
            QMessageBox.critical(self, "错误", "无法启动音频输出")
            self.avatar_button.setChecked(False)
            return
        
        # 使用保存的位置继续播放（如果有）
        self.playback_worker = PlaybackWorker(
            self.recorder, self.processor, self.player, 
            start_pos=self.saved_playback_position
        )
        self.playback_worker.error_occurred.connect(self.on_playback_error)
        self.playback_worker.start()
        
        self.avatar_button.setChecked(True)
        self.avatar_button.setText("🤖 替身的播放中")
        self.mode_label.setText("当前状态: 🤖 替身播放中")
        self.mode_label.setStyleSheet("font-size: 14px; color: #4CAF50;")
        
        # 启动倒计时
        self.remaining_time = int(self.total_recorded_duration)
        if self.remaining_time == 0:
            self.remaining_time = int(self.recorder.get_buffer_duration())
        self.countdown_label.setText(f"⏱️ 剩余: {format_time(self.remaining_time)}")
        self.countdown_label.setStyleSheet("font-size: 18px; color: #4CAF50; font-weight: bold;")
        self.countdown_label.show()
        self.countdown_timer.start(1000)  # 每秒更新
        
        # 设备选择禁用
        self.input_combo.setEnabled(False)
        self.output_combo.setEnabled(False)
    
    def stop_avatar_mode(self):
        """停止替身模式"""
        # 保存当前播放位置（用于继续播放）
        if self.playback_worker:
            self.saved_playback_position = self.playback_worker.get_current_position()
            self.playback_worker.stop()
            self.playback_worker = None
        
        self.player.stop()
        
        # 停止倒计时
        self.countdown_timer.stop()
        
        self.unckeck_all_buttons()
        
        has_recorded = self.recorder.get_buffer_duration() > 0
        if has_recorded:
            self.mode_label.setText("当前状态: ⏸️ 已暂停（有录制内容）")
            self.mode_label.setStyleSheet("font-size: 14px; color: #FF9800;")
        else:
            self.mode_label.setText("当前状态: ⏸️ 待机中")
            self.mode_label.setStyleSheet("font-size: 14px; color: gray;")
        
        self.countdown_label.hide()
        self.avatar_button.setEnabled(has_recorded)
    
    def on_playback_error(self, error_msg: str):
        """播放错误处理"""
        print(f"播放错误: {error_msg}")
    
    def show_about(self):
        """显示关于对话框"""
        QMessageBox.about(self, "关于", f"""
<h2>青丘主播替身 v{VERSION}</h2>
<p>智能音频替身工具</p>
<p>功能特点：</p>
<ul>
<li>🎤 直播模式：录制麦克风音频</li>
<li>💬 互动模式：暂停录制，回答评论</li>
<li>🤖 替身模式：循环播放已录制音频</li>
<li>智能断句：在句子边界处断开</li>
<li>倒计时提醒：显示替身剩余时间</li>
</ul>
<p style='color: gray; font-size: 11px;'>⚠️ 仅供合法直播场景使用，请遵守平台规则</p>
        """)
    
    def closeEvent(self, event):
        """关闭事件"""
        self.stop_avatar_mode()
        self.stop_live_mode()
        self.stop_interact_mode()
        
        event.accept()
