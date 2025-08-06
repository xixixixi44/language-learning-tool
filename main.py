#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语言学习工具 - 基于Whisper的离线语音转录学习应用
支持音频分段转录、波形显示、录音对比功能
"""

import sys
import os
import threading
import time
from pathlib import Path
from typing import List, Dict, Tuple, Optional

import whisper
import librosa
import numpy as np
from pydub import AudioSegment
import matplotlib
matplotlib.use("qtagg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, 
    QWidget, QPushButton, QLabel, QFileDialog, QComboBox,
    QProgressBar, QScrollArea, QFrame, QTextEdit, QMessageBox,
    QSplitter, QGroupBox
)
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QTimer
from PyQt6.QtGui import QFont, QPixmap

# 导入音频处理模块（需要将audio_player.py放在同一目录）
try:
    from audio_player import AudioManager
except ImportError:
    print("警告: 未找到audio_player模块，音频播放功能将不可用")
    AudioManager = None


class AudioSegment:
    """音频片段类，包含转录文本、时间戳、音频数据等"""
    def __init__(self, text: str, start_time: float, end_time: float, 
                 audio_data: np.ndarray, sample_rate: int):
        self.text = text
        self.start_time = start_time
        self.end_time = end_time
        self.audio_data = audio_data
        self.sample_rate = sample_rate
        self.user_recording = None  # 用户录音数据


class WhisperWorker(QThread):
    """Whisper转录工作线程"""
    progress_updated = pyqtSignal(int)  # 进度更新信号
    segment_completed = pyqtSignal(object)  # 段落完成信号
    language_detected = pyqtSignal(str, float)  # 语言检测信号
    transcription_finished = pyqtSignal()  # 转录完成信号
    error_occurred = pyqtSignal(str)  # 错误信号

    def __init__(self, audio_path: str, model_size: str = "small"):
        super().__init__()
        self.audio_path = audio_path
        self.model_size = model_size
        self.model = None
        self.is_running = True

    def run(self):
        try:
            # 加载Whisper模型
            self.model = whisper.load_model(self.model_size)
            
            # 加载音频文件
            audio_data, sample_rate = librosa.load(self.audio_path, sr=16000)
            
            # 执行转录，获取word-level时间戳
            result = self.model.transcribe(
                self.audio_path,
                word_timestamps=True,
                verbose=False
            )
            
            # 发送语言检测信号
            detected_language = result.get('language', 'unknown')
            language_confidence = 0.9  # Whisper没有直接提供置信度，使用估计值
            self.language_detected.emit(detected_language, language_confidence)
            
            # 处理分段
            segments = self._process_segments(result, audio_data, sample_rate)
            
            # 逐个发送完成的段落
            for i, segment in enumerate(segments):
                if not self.is_running:
                    break
                    
                self.segment_completed.emit(segment)
                progress = int((i + 1) / len(segments) * 100)
                self.progress_updated.emit(progress)
                
                # 模拟处理时间，避免界面卡顿
                self.msleep(100)
            
            self.transcription_finished.emit()
            
        except Exception as e:
            self.error_occurred.emit(str(e))

    def _process_segments(self, result: Dict, audio_data: np.ndarray, 
                         sample_rate: int) -> List[AudioSegment]:
        """处理Whisper结果，创建音频段落"""
        segments = []
        
        for segment_data in result['segments']:
            start_time = segment_data['start']
            end_time = segment_data['end']
            text = segment_data['text'].strip()
            
            # 提取对应的音频片段
            start_sample = int(start_time * sample_rate)
            end_sample = int(end_time * sample_rate)
            segment_audio = audio_data[start_sample:end_sample]
            
            # 创建AudioSegment对象
            audio_segment = AudioSegment(
                text=text,
                start_time=start_time,
                end_time=end_time,
                audio_data=segment_audio,
                sample_rate=sample_rate
            )
            
            segments.append(audio_segment)
        
        return segments

    def stop(self):
        """停止转录任务"""
        self.is_running = False


class WaveformWidget(QWidget):
    """波形图显示组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(10, 2))
        self.canvas = FigureCanvas(self.figure)
        
        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
    def plot_waveform(self, audio_data: np.ndarray, sample_rate: int, 
                     title: str = "波形图"):
        """绘制波形图"""
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        
        # 创建时间轴
        time_axis = np.linspace(0, len(audio_data) / sample_rate, len(audio_data))
        
        # 绘制波形
        ax.plot(time_axis, audio_data, 'b-', linewidth=0.5)
        ax.set_title(title, fontsize=10)
        ax.set_xlabel('时间 (秒)')
        ax.set_ylabel('振幅')
        ax.grid(True, alpha=0.3)
        
        # 设置紧凑布局
        self.figure.tight_layout()
        self.canvas.draw()


class AudioSegmentWidget(QFrame):
    """单个音频段落的显示组件"""
    def __init__(self, segment: AudioSegment, parent=None):
        super().__init__(parent)
        self.segment = segment
        self.audio_manager = AudioManager() if AudioManager else None
        
        self.setFrameStyle(QFrame.Shape.Box)
        self.setStyleSheet("QFrame { border: 1px solid gray; margin: 5px; }")
        
        self._setup_ui()
        
    def _setup_ui(self):
        """设置界面布局"""
        layout = QVBoxLayout()
        
        # 时间信息
        time_label = QLabel(f"时间: {self.segment.start_time:.1f}s - {self.segment.end_time:.1f}s")
        time_label.setFont(QFont("Arial", 9))
        layout.addWidget(time_label)
        
        # 转录文本
        text_edit = QTextEdit()
        text_edit.setPlainText(self.segment.text)
        text_edit.setMaximumHeight(80)
        text_edit.setFont(QFont("Arial", 11))
        layout.addWidget(text_edit)
        
        # 原音频控制
        original_group = QGroupBox("原音频")
        original_layout = QVBoxLayout()
        
        # 原音频波形图
        self.original_waveform = WaveformWidget()
        self.original_waveform.plot_waveform(
            self.segment.audio_data, 
            self.segment.sample_rate, 
            "原音频波形"
        )
        self.original_waveform.setMaximumHeight(120)
        original_layout.addWidget(self.original_waveform)
        
        # 播放按钮
        self.play_button = QPushButton("播放原音频")
        self.play_button.clicked.connect(self._play_original)
        original_layout.addWidget(self.play_button)
        
        original_group.setLayout(original_layout)
        layout.addWidget(original_group)
        
        # 用户录音控制
        recording_group = QGroupBox("录音练习")
        recording_layout = QVBoxLayout()
        
        # 用户录音波形图（初始为空）
        self.user_waveform = WaveformWidget()
        self.user_waveform.setMaximumHeight(120)
        recording_layout.addWidget(self.user_waveform)
        
        # 录音控制按钮
        button_layout = QHBoxLayout()
        self.record_button = QPushButton("开始录音")
        self.record_button.clicked.connect(self._toggle_recording)
        button_layout.addWidget(self.record_button)
        
        self.play_user_button = QPushButton("播放录音")
        self.play_user_button.clicked.connect(self._play_user_recording)
        self.play_user_button.setEnabled(False)
        button_layout.addWidget(self.play_user_button)
        
        recording_layout.addLayout(button_layout)
        recording_group.setLayout(recording_layout)
        layout.addWidget(recording_group)
        
        self.setLayout(layout)
    
    def _play_original(self):
        """播放原音频"""
        if not self.audio_manager:
            QMessageBox.warning(self, "警告", "音频播放功能不可用")
            return
            
        if not self.audio_manager.is_playing():
            self.play_button.setText("停止播放")
            self.audio_manager.play_audio(
                self.segment.audio_data, 
                self.segment.sample_rate,
                callback=self._stop_playing
            )
        else:
            self.audio_manager.stop_playback()
            self._stop_playing()
    
    def _stop_playing(self):
        """停止播放"""
        self.play_button.setText("播放原音频")
    
    def _toggle_recording(self):
        """切换录音状态"""
        if not self.audio_manager:
            QMessageBox.warning(self, "警告", "录音功能不可用")
            return
            
        if not self.audio_manager.is_recording():
            self._start_recording()
        else:
            self._stop_recording()
    
    def _start_recording(self):
        """开始录音"""
        self.record_button.setText("停止录音")
        self.audio_manager.start_recording(callback=self._on_recording_finished)
    
    def _stop_recording(self):
        """停止录音"""
        self.record_button.setText("开始录音")
        self.audio_manager.stop_recording()
    
    def _on_recording_finished(self, audio_data: np.ndarray, sample_rate: int):
        """录音完成回调"""
        # 保存用户录音数据
        self.segment.user_recording = {
            'data': audio_data,
            'sample_rate': sample_rate
        }
        
        # 显示用户录音波形
        self.user_waveform.plot_waveform(
            audio_data, 
            sample_rate, 
            "用户录音波形"
        )
        
        # 启用播放按钮
        self.play_user_button.setEnabled(True)
        self.record_button.setText("重新录音")
    
    def _play_user_recording(self):
        """播放用户录音"""
        if not self.audio_manager or not self.segment.user_recording:
            return
            
        if not self.audio_manager.is_playing():
            self.play_user_button.setText("停止播放")
            self.audio_manager.play_audio(
                self.segment.user_recording['data'],
                self.segment.user_recording['sample_rate'],
                callback=self._stop_user_playing
            )
        else:
            self.audio_manager.stop_playback()
            self._stop_user_playing()
    
    def _stop_user_playing(self):
        """停止播放用户录音"""
        self.play_user_button.setText("播放录音")


class LanguageSelectionDialog(QMessageBox):
    """语言选择确认对话框"""
    def __init__(self, detected_language: str, confidence: float, parent=None):
        super().__init__(parent)
        self.setWindowTitle("语言识别确认")
        self.setText(f"检测到语言: {detected_language} (置信度: {confidence:.2f})")
        self.setInformativeText("是否确认使用此语言进行转录？")
        self.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        self.setDefaultButton(QMessageBox.StandardButton.Yes)


class MainWindow(QMainWindow):
    """主窗口类"""
    def __init__(self):
        super().__init__()
        self.whisper_worker = None
        self.audio_segments = []
        self.current_model_size = "small"
        
        self.setWindowTitle("语言学习工具 - Whisper离线转录")
        self.setGeometry(100, 100, 1200, 800)
        
        self._setup_ui()
        
    def _setup_ui(self):
        """设置主界面"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        
        # 顶部控制面板
        control_panel = self._create_control_panel()
        layout.addWidget(control_panel)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # 状态标签
        self.status_label = QLabel("请选择音频文件开始转录")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)
        
        # 音频段落显示区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)
        
        central_widget.setLayout(layout)
    
    def _create_control_panel(self) -> QWidget:
        """创建控制面板"""
        panel = QWidget()
        layout = QHBoxLayout()
        
        # 文件选择按钮
        self.file_button = QPushButton("选择音频文件")
        self.file_button.clicked.connect(self._select_file)
        layout.addWidget(self.file_button)
        
        # 模型选择
        layout.addWidget(QLabel("Whisper模型:"))
        self.model_combo = QComboBox()
        self.model_combo.addItems(["tiny", "base", "small", "medium", "large"])
        self.model_combo.setCurrentText("small")
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        layout.addWidget(self.model_combo)
        
        # 开始转录按钮
        self.transcribe_button = QPushButton("开始转录")
        self.transcribe_button.clicked.connect(self._start_transcription)
        self.transcribe_button.setEnabled(False)
        layout.addWidget(self.transcribe_button)
        
        # 清除结果按钮
        self.clear_button = QPushButton("清除结果")
        self.clear_button.clicked.connect(self._clear_results)
        layout.addWidget(self.clear_button)
        
        layout.addStretch()
        panel.setLayout(layout)
        return panel
    
    def _select_file(self):
        """选择音频文件"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择音频文件", "", "音频文件 (*.mp3 *.wav *.m4a)"
        )
        
        if file_path:
            self.audio_file_path = file_path
            self.file_button.setText(f"已选择: {Path(file_path).name}")
            self.transcribe_button.setEnabled(True)
            self.status_label.setText(f"已选择音频文件: {Path(file_path).name}")
    
    def _on_model_changed(self, model_size: str):
        """模型大小改变"""
        self.current_model_size = model_size
    
    def _start_transcription(self):
        """开始转录"""
        if not hasattr(self, 'audio_file_path'):
            return
            
        # 清除之前的结果
        self._clear_results()
        
        # 禁用控制按钮
        self.transcribe_button.setEnabled(False)
        self.file_button.setEnabled(False)
        self.model_combo.setEnabled(False)
        
        # 显示进度条
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("正在转录音频...")
        
        # 启动Whisper工作线程
        self.whisper_worker = WhisperWorker(self.audio_file_path, self.current_model_size)
        self.whisper_worker.progress_updated.connect(self.progress_bar.setValue)
        self.whisper_worker.segment_completed.connect(self._on_segment_completed)
        self.whisper_worker.language_detected.connect(self._on_language_detected)
        self.whisper_worker.transcription_finished.connect(self._on_transcription_finished)
        self.whisper_worker.error_occurred.connect(self._on_error)
        self.whisper_worker.start()
    
    def _on_language_detected(self, language: str, confidence: float):
        """处理语言检测结果"""
        dialog = LanguageSelectionDialog(language, confidence, self)
        result = dialog.exec()
        
        if result == QMessageBox.StandardButton.No:
            # 用户拒绝了检测的语言，这里可以添加手动选择语言的功能
            self.status_label.setText(f"用户拒绝了检测的语言: {language}")
    
    def _on_segment_completed(self, segment: AudioSegment):
        """处理完成的音频段落"""
        self.audio_segments.append(segment)
        
        # 创建段落显示组件
        segment_widget = AudioSegmentWidget(segment)
        self.scroll_layout.addWidget(segment_widget)
        
        # 滚动到最新添加的段落
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )
    
    def _on_transcription_finished(self):
        """转录完成"""
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"转录完成！共生成 {len(self.audio_segments)} 个音频段落")
        
        # 重新启用控制按钮
        self.transcribe_button.setEnabled(True)
        self.file_button.setEnabled(True)
        self.model_combo.setEnabled(True)
    
    def _on_error(self, error_message: str):
        """处理错误"""
        self.progress_bar.setVisible(False)
        self.status_label.setText(f"转录出错: {error_message}")
        
        QMessageBox.critical(self, "错误", f"转录过程中出现错误:\n{error_message}")
        
        # 重新启用控制按钮
        self.transcribe_button.setEnabled(True)
        self.file_button.setEnabled(True)
        self.model_combo.setEnabled(True)
    
    def _clear_results(self):
        """清除转录结果"""
        # 清除所有段落组件
        for i in reversed(range(self.scroll_layout.count())):
            child = self.scroll_layout.itemAt(i).widget()
            if child:
                child.setParent(None)
        
        self.audio_segments.clear()
        self.status_label.setText("已清除所有结果")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用信息
    app.setApplicationName("语言学习工具")
    app.setApplicationVersion("1.0.0")
    
    # 创建主窗口
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
