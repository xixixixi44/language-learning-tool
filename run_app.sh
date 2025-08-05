#!/bin/bash

# 语言学习工具启动脚本
# 适用于macOS系统

echo "=== 语言学习工具启动脚本 ==="
echo "检查系统环境..."

# 检查Python版本
python_version=$(python3 --version 2>&1)
if [[ $? -eq 0 ]]; then
    echo "✓ 检测到Python: $python_version"
else
    echo "✗ 未检测到Python3，请先安装Python 3.8+"
    exit 1
fi

# 检查是否在虚拟环境中
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✓ 检测到虚拟环境: $VIRTUAL_ENV"
else
    echo "⚠ 建议使用虚拟环境运行"
    read -p "是否继续？(y/N): " continue_without_venv
    if [[ $continue_without_venv != "y" && $continue_without_venv != "Y" ]]; then
        echo "退出启动"
        exit 1
    fi
fi

# 检查依赖是否安装
echo "检查依赖包..."

missing_packages=()

# 检查关键依赖
packages=("PyQt6" "whisper" "librosa" "numpy" "matplotlib" "pyaudio")
for package in "${packages[@]}"; do
    python3 -c "import $package" 2>/dev/null
    if [[ $? -ne 0 ]]; then
        missing_packages+=($package)
    fi
done

if [[ ${#missing_packages[@]} -gt 0 ]]; then
    echo "✗ 缺少以下依赖包:"
    for package in "${missing_packages[@]}"; do
        echo "  - $package"
    done
    echo ""
    echo "请运行以下命令安装依赖："
    echo "pip install -r requirements.txt"
    echo ""
    read -p "是否现在安装？(y/N): " install_now
    if [[ $install_now == "y" || $install_now == "Y" ]]; then
        echo "安装依赖包..."
        pip install -r requirements.txt
        if [[ $? -ne 0 ]]; then
            echo "✗ 依赖安装失败"
            exit 1
        fi
        echo "✓ 依赖安装完成"
    else
        echo "请手动安装依赖后重新运行"
        exit 1
    fi
else
    echo "✓ 所有依赖包已安装"
fi

# 检查FFmpeg
echo "检查FFmpeg..."
ffmpeg -version >/dev/null 2>&1
if [[ $? -eq 0 ]]; then
    echo "✓ FFmpeg已安装"
else
    echo "⚠ 未检测到FFmpeg"
    echo "建议安装FFmpeg以获得更好的音频支持："
    echo "brew install ffmpeg"
fi

# 检查音频文件
if [[ ! -f "audio_player.py" ]]; then
    echo "⚠ 未找到audio_player.py文件"
    echo "音频播放功能可能不可用"
fi

# 创建必要的目录
mkdir -p logs
mkdir -p temp

# 启动应用
echo ""
echo "启动语言学习工具..."
echo "按 Ctrl+C 退出"
echo "=========================="

python3 main.py

echo ""
echo "应用已退出"
