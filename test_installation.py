#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
安装测试脚本
验证所有依赖是否正确安装
"""

import sys
import subprocess
from pathlib import Path

def test_import(module_name, description=""):
    """测试模块导入"""
    try:
        __import__(module_name)
        print(f"✓ {module_name} - {description}")
        return True
    except ImportError as e:
        print(f"✗ {module_name} - {description} - 错误: {e}")
        return False
    except Exception as e:
        print(f"⚠ {module_name} - {description} - 警告: {e}")
        return True

def test_whisper():
    """测试Whisper模型"""
    try:
        import whisper
        print("测试Whisper模型加载...")
        # 尝试加载最小的模型
        model = whisper.load_model("tiny")
        print("✓ Whisper模型加载成功")
        return True
    except Exception as e:
        print(f"✗ Whisper模型加载失败: {e}")
        return False

def test_audio_devices():
    """测试音频设备"""
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        
        print("音频输入设备:")
        input_devices = []
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxInputChannels'] > 0:
                input_devices.append(info['name'])
                print(f"  - {info['name']}")
        
        print("音频输出设备:")
        output_devices = []
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info['maxOutputChannels'] > 0:
                output_devices.append(info['name'])
                print(f"  - {info['name']}")
        
        p.terminate()
        
        if input_devices and output_devices:
            print("✓ 音频设备检测成功")
            return True
        else:
            print("⚠ 未检测到完整的音频设备")
            return False
            
    except Exception as e:
        print(f"✗ 音频设备检测失败: {e}")
        return False

def test_file_structure():
    """测试文件结构"""
    required_files = [
        "main.py",
        "audio_player.py", 
        "requirements.txt",
        "README.md"
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
    
    if missing_files:
        print(f"✗ 缺少文件: {', '.join(missing_files)}")
        return False
    else:
        print("✓ 所有必需文件存在")
        return True

def test_ffmpeg():
    """测试FFmpeg"""
    try:
        result = subprocess.run(['ffmpeg', '-version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✓ FFmpeg已安装: {version_line}")
            return True
        else:
            print("✗ FFmpeg命令执行失败")
            return False
    except FileNotFoundError:
        print("✗ 未找到FFmpeg命令")
        return False
    except Exception as e:
        print(f"✗ FFmpeg测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("=== 语言学习工具安装测试 ===")
    print(f"Python版本: {sys.version}")
    print("")
    
    # 测试结果统计
    tests_passed = 0
    total_tests = 0
    
    # 测试Python模块
    print("1. 测试Python依赖包:")
    modules_to_test = [
        ("PyQt6", "GUI框架"),
        ("whisper", "语音识别"),
        ("librosa", "音频分析"),
        ("numpy", "数值计算"),
        ("matplotlib", "图形绘制"),
        ("pyaudio", "音频录制"),
        ("pydub", "音频处理"),
        ("scipy", "科学计算"),
        ("soundfile", "音频文件处理")
    ]
    
    for module, desc in modules_to_test:
        if test_import(module, desc):
            tests_passed += 1
        total_tests += 1
    
    print("")
    
    # 测试Whisper
    print("2. 测试Whisper模型:")
    if test_whisper():
        tests_passed += 1
    total_tests += 1
    print("")
    
    # 测试音频设备
    print("3. 测试音频设备:")
    if test_audio_devices():
        tests_passed += 1
    total_tests += 1
    print("")
    
    # 测试FFmpeg
    print("4. 测试FFmpeg:")
    if test_ffmpeg():
        tests_passed += 1
    total_tests += 1
    print("")
    
    # 测试文件结构
    print("5. 测试文件结构:")
    if test_file_structure():
        tests_passed += 1
    total_tests += 1
    print("")
    
    # 显示测试结果
    print("=== 测试结果 ===")
    print(f"通过: {tests_passed}/{total_tests}")
    
    if tests_passed == total_tests:
        print("✓ 所有测试通过！应用应该可以正常运行")
        print("")
        print("下一步:")
        print("运行 ./run_app.sh 或 python3 main.py 启动应用")
        return True
    else:
        print("⚠ 部分测试失败，可能影响应用功能")
        print("")
        print("建议:")
        failed_tests = total_tests - tests_passed
        
        if failed_tests <= 2:
            print("- 失败项目较少，可以尝试运行应用")
            print("- 部分功能可能不可用")
        else:
            print("- 请检查安装过程是否有错误")
            print("- 运行 pip install -r requirements.txt 重新安装依赖")
            print("- 确保系统依赖（FFmpeg、PortAudio）已正确安装")
        
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        sys.exit(1)
