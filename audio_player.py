#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
音频播放模块
提供音频播放和录音功能
"""

import numpy as np
import pyaudio
import threading
import time
from typing import Optional, Callable
from PyQt6.QtCore import QObject, pyqtSignal


class AudioPlayer(QObject):
    """音频播放器类"""
    playback_finished = pyqtSignal()
    playback_started = pyqtSignal()
    playback_error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.is_playing = False
        self.audio_stream = None
        self.p = pyaudio.PyAudio()
        self.playback_thread = None

    def play_audio(self, audio_data: np.ndarray, sample_rate: int = 16000):
        """播放音频数据"""
        if self.is_playing:
            self.stop_playback()

        try:
            # 确保音频数据是正确的格式
            if audio_data.dtype != np.float32:
                audio_data = audio_data.astype(np.float32)
            
            # 归一化音频数据
            if np.max(np.abs(audio_data)) > 1.0:
                audio_data = audio_data / np.max(np.abs(audio_data))

            self.playback_thread = threading.Thread(
                target=self._play_audio_thread,
                args=(audio_data, sample_rate)
            )
            self.playback_thread.daemon = True
            self.playback_thread.start()

        except Exception as e:
            self.playback_error.emit(f"播放出错: {str(e)}")

    def _play_audio_thread(self, audio_data: np.ndarray, sample_rate: int):
        """音频播放线程"""
        try:
            self.is_playing = True
            self.playback_started.emit()

            # 打开音频流
            stream = self.p.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=sample_rate,
                output=True,
                frames_per_buffer=1024
            )

            # 分块播放音频
            chunk_size = 1024
            for i in range(0, len(audio_data), chunk_size):
                if not self.is_playing:
                    break
                
                chunk = audio_data[i:i + chunk_size]
                # 确保chunk的长度
                if len(chunk) < chunk_size:
                    chunk = np.pad(chunk, (0, chunk_size - len(chunk)), 'constant')
                
                stream.write(chunk.tobytes())

            stream.stop_stream()
            stream.close()

        except Exception as e:
            self.playback_error.emit(f"播放线程出错: {str(e)}")
        finally:
            self.is_playing = False
            self.playback_finished.emit()

    def stop_playback(self):
        """停止播放"""
        self.is_playing = False
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=1.0)

    def __del__(self):
        """析构函数"""
        try:
            self.stop_playback()
            self.p.terminate()
        except:
            pass


class AudioRecorder(QObject):
    """音频录音器类"""
    recording_started = pyqtSignal()
    recording_finished = pyqtSignal(np.ndarray, int)  # audio_data, sample_rate
    recording_error = pyqtSignal(str)

    def __init__(self, sample_rate: int = 16000):
        super().__init__()
        self.sample_rate = sample_rate
        self.is_recording = False
        self.audio_data = []
        self.p = pyaudio.PyAudio()
        self.recording_thread = None

    def start_recording(self):
        """开始录音"""
        if self.is_recording:
            return

        try:
            self.audio_data = []
            self.recording_thread = threading.Thread(target=self._recording_thread)
            self.recording_thread.daemon = True
            self.recording_thread.start()
        except Exception as e:
            self.recording_error.emit(f"录音启动失败: {str(e)}")

    def _recording_thread(self):
        """录音线程"""
        try:
            self.is_recording = True
            self.recording_started.emit()

            # 打开音频流
            stream = self.p.open(
                format=pyaudio.paFloat32,
                channels=1,
                rate=self.sample_rate,
                input=True,
                frames_per_buffer=1024
            )

            while self.is_recording:
                try:
                    data = stream.read(1024, exception_on_overflow=False)
                    audio_chunk = np.frombuffer(data, dtype=np.float32)
                    self.audio_data.extend(audio_chunk)
                except Exception as e:
                    print(f"录音数据读取错误: {e}")
                    break

            stream.stop_stream()
            stream.close()

            # 转换为numpy数组
            if self.audio_data:
                audio_array = np.array(self.audio_data, dtype=np.float32)
                self.recording_finished.emit(audio_array, self.sample_rate)
            else:
                self.recording_error.emit("录音数据为空")

        except Exception as e:
            self.recording_error.emit(f"录音过程出错: {str(e)}")
        finally:
            self.is_recording = False

    def stop_recording(self):
        """停止录音"""
        self.is_recording = False
        if self.recording_thread and self.recording_thread.is_alive():
            self.recording_thread.join(timeout=2.0)

    def __del__(self):
        """析构函数"""
        try:
            self.stop_recording()
            self.p.terminate()
        except:
            pass


class AudioManager(QObject):
    """音频管理器，统一管理播放和录音"""
    def __init__(self):
        super().__init__()
        self.player = AudioPlayer()
        self.recorder = AudioRecorder()
        
        # 连接信号
        self.player.playback_finished.connect(self._on_playback_finished)
        self.player.playback_error.connect(self._on_playback_error)
        self.recorder.recording_finished.connect(self._on_recording_finished)
        self.recorder.recording_error.connect(self._on_recording_error)
        
        self.current_callback = None

    def play_audio(self, audio_data: np.ndarray, sample_rate: int = 16000, 
                   callback: Optional[Callable] = None):
        """播放音频"""
        self.current_callback = callback
        self.player.play_audio(audio_data, sample_rate)

    def stop_playback(self):
        """停止播放"""
        self.player.stop_playback()

    def start_recording(self, callback: Optional[Callable] = None):
        """开始录音"""
        self.current_callback = callback
        self.recorder.start_recording()

    def stop_recording(self):
        """停止录音"""
        self.recorder.stop_recording()

    def _on_playback_finished(self):
        """播放完成回调"""
        if self.current_callback:
            self.current_callback()

    def _on_playback_error(self, error_msg: str):
        """播放错误回调"""
        print(f"播放错误: {error_msg}")

    def _on_recording_finished(self, audio_data: np.ndarray, sample_rate: int):
        """录音完成回调"""
        if self.current_callback:
            self.current_callback(audio_data, sample_rate)

    def _on_recording_error(self, error_msg: str):
        """录音错误回调"""
        print(f"录音错误: {error_msg}")

    def is_playing(self) -> bool:
        """是否正在播放"""
        return self.player.is_playing

    def is_recording(self) -> bool:
        """是否正在录音"""
        return self.recorder.is_recording

    def __del__(self):
        """析构函数"""
        try:
            self.stop_playback()
            self.stop_recording()
        except:
            pass
