#!/bin/bash

# 语言学习工具安装脚本
# 适用于macOS系统

echo "=== 语言学习工具安装脚本 ==="
echo ""

# 检查系统
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "⚠ 此脚本为macOS优化，其他系统请手动安装"
fi

# 检查Homebrew
echo "检查Homebrew..."
if command -v brew >/dev/null 2>&1; then
    echo "✓ Homebrew已安装"
else
    echo "⚠ 未检测到Homebrew"
    echo "是否安装Homebrew？这将有助于安装系统依赖"
    read -p "(y/N): " install_brew
    if [[ $install_brew == "y" || $install_brew == "Y" ]]; then
        echo "安装Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        if [[ $? -ne 0 ]]; then
            echo "✗ Homebrew安装失败"
            exit 1
        fi
        echo "✓ Homebrew安装完成"
    fi
fi

# 检查Python
echo ""
echo "检查Python..."
python_version=$(python3 --version 2>&1)
if [[ $? -eq 0 ]]; then
    echo "✓ 检测到Python: $python_version"
    
    # 检查Python版本是否满足要求
    version_check=$(python3 -c "import sys; print(sys.version_info >= (3, 8))")
    if [[ $version_check == "True" ]]; then
        echo "✓ Python版本满足要求"
    else
        echo "⚠ Python版本过低，建议升级到3.8+"
    fi
else
    echo "✗ 未检测到Python3"
    if command -v brew >/dev/null 2>&1; then
        echo "使用Homebrew安装Python..."
        brew install python@3.11
    else
        echo "请从官网下载安装Python: https://www.python.org/"
        exit 1
    fi
fi

# 安装系统依赖
echo ""
echo "安装系统依赖..."

if command -v brew >/dev/null 2>&1; then
    echo "安装FFmpeg和PortAudio..."
    brew install ffmpeg portaudio
    
    if [[ $? -eq 0 ]]; then
        echo "✓ 系统依赖安装完成"
    else
        echo "⚠ 部分系统依赖安装失败，请手动安装"
    fi
else
    echo "⚠ 无法自动安装系统依赖，请手动安装："
    echo "  - FFmpeg: 用于音频格式转换"
    echo "  - PortAudio: 用于录音功能"
fi

# 创建虚拟环境
echo ""
echo "创建Python虚拟环境..."
if [[ -d "venv" ]]; then
    echo "⚠ 虚拟环境已存在，跳过创建"
else
    python3 -m venv venv
    if [[ $? -eq 0 ]]; then
        echo "✓ 虚拟环境创建完成"
    else
        echo "✗ 虚拟环境创建失败"
        exit 1
    fi
fi

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✓ 虚拟环境已激活"
else
    echo "✗ 虚拟环境激活失败"
    exit 1
fi

# 更新pip
echo ""
echo "更新pip..."
pip install --upgrade pip setuptools wheel

# 安装Python依赖
echo ""
echo "安装Python依赖包..."
echo "这可能需要几分钟时间..."

# 特殊处理pyaudio安装
echo "安装pyaudio..."
pip install pyaudio
if [[ $? -ne 0 ]]; then
    echo "⚠ pyaudio安装失败，尝试使用编译选项..."
    pip install --global-option='build_ext' \
        --global-option='-I/opt/homebrew/include' \
        --global-option='-L/opt/homebrew/lib' pyaudio
fi

# 安装其他依赖
echo "安装其他依赖包..."
pip install -r requirements.txt

if [[ $? -eq 0 ]]; then
    echo "✓ Python依赖安装完成"
else
    echo "✗ 部分依赖安装失败，请检查错误信息"
    echo "可以尝试单独安装失败的包"
fi

# 下载Whisper模型
echo ""
echo "预下载Whisper模型..."
echo "这将下载small模型（约244MB），请耐心等待..."

python3 -c "
import whisper
try:
    model = whisper.load_model('small')
    print('✓ small模型下载完成')
except Exception as e:
    print(f'⚠ 模型下载失败: {e}')
    print('可以在首次使用时自动下载')
"

# 设置执行权限
echo ""
echo "设置执行权限..."
chmod +x run_app.sh

# 创建桌面快捷方式（可选）
echo ""
read -p "是否创建桌面快捷方式？(y/N): " create_shortcut
if [[ $create_shortcut == "y" || $create_shortcut == "Y" ]]; then
    desktop_path="$HOME/Desktop"
    if [[ -d "$desktop_path" ]]; then
        cat > "$desktop_path/语言学习工具.command" << EOF
#!/bin/bash
cd "$(dirname "\$0")/../../$(basename "$PWD")"
source venv/bin/activate
python3 main.py
EOF
        chmod +x "$desktop_path/语言学习工具.command"
        echo "✓ 桌面快捷方式已创建"
    else
        echo "⚠ 未找到桌面目录，跳过快捷方式创建"
    fi
fi

# 安装完成
echo ""
echo "=========================="
echo "✓ 安装完成！"
echo ""
echo "启动方法："
echo "1. 命令行启动: ./run_app.sh"
echo "2. Python启动: source venv/bin/activate && python3 main.py"
if [[ -f "$HOME/Desktop/语言学习工具.command" ]]; then
    echo "3. 双击桌面快捷方式"
fi
echo ""
echo "使用说明："
echo "- 首次运行会自动下载所需的Whisper模型"
echo "- 支持mp3/wav/m4a格式的音频文件"
echo "- 建议先用较短的音频文件测试功能"
echo ""
echo "如遇问题，请查看README.md或提交Issue"
echo "=========================="
