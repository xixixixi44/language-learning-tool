# 语言学习工具

基于OpenAI Whisper的离线音频转录学习工具，支持智能分段、波形显示和录音对比功能。

## 功能特点

- ✅ **完全离线运行** - 使用本地Whisper模型，无需API
- ✅ **智能语音分段** - 基于Whisper的word-level时间戳自动分段
- ✅ **多模型支持** - 支持tiny/base/small/medium/large模型切换
- ✅ **语言自动识别** - 90+语言支持，用户可确认
- ✅ **波形图显示** - 直观的音频波形展示
- ✅ **录音对比功能** - 支持用户录音并与原音频对比
- ✅ **实时进度显示** - 分段转录，实时显示结果

## 系统要求

- macOS 10.15+ (支持Apple Silicon和Intel)
- Python 3.8+
- 至少4GB可用内存
- 推荐8GB+内存用于更大的Whisper模型

## 安装步骤

### 1. 安装Python依赖

```bash
# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate


# 升级 pip
pip install --upgrade pip

# 安装依赖
pip install -r requirements.txt

# 运行自检
python3 test_installation.py
```

### 2. 运行程序

```bash
python main.py
```

## 使用说明

### 基本流程

1. **选择音频文件** - 点击"选择音频文件"按钮，支持mp3/wav/m4a格式
2. **选择Whisper模型** - 根据需要选择合适的模型大小
   - `tiny`: 最快，准确度较低（~39MB）
   - `base`: 较快，准确度中等（~74MB）  
   - `small`: 平衡选择，默认推荐（~244MB）
   - `medium`: 较慢，准确度较高（~769MB）
   - `large`: 最慢，准确度最高（~1550MB）

3. **开始转录** - 点击"开始转录"按钮
4. **确认语言** - 系统会自动检测语言并询问确认
5. **查看结果** - 转录会分段显示，每段包含：
   - 时间戳信息
   - 转录文本（可编辑）
   - 原音频波形图和播放功能
   - 录音练习区域

### 录音对比功能

每个音频段落下方都有录音练习区域：

1. 点击"开始录音"进行语音模仿
2. 录音完成后会显示波形图
3. 可以播放对比原音频和自己的录音
4. 通过波形图直观对比发音差异

### 模型下载说明

首次使用时，Whisper会自动下载对应的模型文件：
- 模型存储位置：`~/.cache/whisper/`
- 网络不佳时可能需要较长下载时间
- 建议首次使用时选择较小的模型进行测试

## 故障排除

### 常见问题

**1. PyQt6安装失败**
```bash
# 尝试升级pip
pip install --upgrade pip setuptools wheel
pip install PyQt6
```

**2. pyaudio安装失败**  
```bash
# macOS上可能需要先安装portaudio
brew install portaudio
pip install pyaudio
```

**3. Whisper模型下载慢**
```bash
# 可以手动下载模型到缓存目录
# 或使用代理：
export https_proxy=http://127.0.0.1:7890
python main.py
```

**4. 音频格式不支持**
```bash
# 确保安装了ffmpeg
brew install ffmpeg
```

### 性能优化建议

- 对于较长音频文件，建议使用small或base模型
- 关闭其他占用内存的应用
- 首次运行建议选择较短的音频文件测试

## 技术架构

- **GUI框架**: PyQt6
- **语音识别**: OpenAI Whisper
- **音频处理**: librosa + pydub  
- **波形显示**: matplotlib
- **录音功能**: pyaudio
- **多线程**: QThread (避免界面卡顿)

## 开发计划

### 当前版本 (v1.0)
- [x] 基础转录功能
- [x] 智能分段
- [x] 波形图显示
- [ ] 音频播放功能完善
- [ ] 录音功能实现
- [ ] 错误处理优化

### 未来版本
- [ ] 支持更多音频格式
- [ ] 语音相似度分析
- [ ] 导出功能（SRT字幕等）
- [ ] 快捷键支持
- [ ] 主题切换
- [ ] 移动端适配

## 贡献指南

欢迎提交Issue和Pull Request！

### 开发环境设置

```bash
# 克隆项目
git clone <repository-url>
cd language-learning-tool

# 创建开发环境
python3 -m venv dev-env
source dev-env/bin/activate

# 安装开发依赖
pip install -r requirements.txt
pip install pytest black flake8

# 运行测试
pytest tests/

# 代码格式化
black main.py
flake8 main.py
```

## 许可证

MIT License - 详见LICENSE文件

## 致谢

- [OpenAI Whisper](https://github.com/openai/whisper) - 强大的语音识别模型
- [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) - 优秀的GUI框架
- [librosa](https://librosa.org/) - 音频分析库

## 联系方式

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue
- 发送邮件至开发者

---

**注意**: 本工具仅供学习和研究使用，请遵守相关音频内容的版权法律法规。
