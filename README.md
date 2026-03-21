# 🦊 青丘主播替身 v1.0

智能音频替身工具，帮助主播在疲劳时自动播放处理后的录音，规避平台声纹检测。

## ✨ 功能特点

- 🎤 **直播模式**：录制麦克风音频
- 💬 **互动模式**：暂停录制，不干扰主播回答评论
- 🤖 **替身模式**：智能循环播放已录制音频
- 🧠 **智能断句**：在句子边界处断开，语意连贯
- ⏱️ **倒计时提醒**：显示替身剩余时间
- 🔒 **声纹对抗**：微调音调音色，规避平台检测

## 📁 项目结构

```
streamvoice-avatar/
├── main.py                      # 主入口
├── config.py                    # 配置参数
├── utils.py                     # 工具函数
├── audio/                       # 音频模块
│   ├── recorder.py             # 录制模块（支持不限时长）
│   ├── processor.py            # 声纹处理模块
│   ├── player.py               # 播放模块
│   └── sentence_detector.py    # 智能断句模块
├── gui/                         # 界面模块
│   └── main_window.py          # 主窗口
├── build_windows.bat           # Windows 打包脚本
├── build_windows.spec          # Windows 打包配置
├── WINDOWS_README.md           # Windows 使用说明
├── BUILD_GUIDE.md              # 打包指南
└── requirements.txt            # Python 依赖
```

## 🚀 快速开始

### macOS 运行
```bash
cd streamvoice-avatar
pip3 install -r requirements.txt
python3 main.py
```

### Windows 打包
```cmd
cd streamvoice-avatar
build_windows.bat
```

详细说明见 `BUILD_GUIDE.md`

## 🎮 使用流程

```
1. 🎤 直播模式 → 开始录制
   ↓
2. 💬 互动模式 → 回答评论（不录制）
   ↓
3. 🤖 替身模式 → 播放录音（显示倒计时）
   ↓
4. 🎤 直播模式 → 恢复录制（替身内容清空）
```

## 🔧 核心参数

### 声纹对抗（自然微调）
```python
音调偏移: ±0.3 半音      # 几乎察觉不到
共振峰偏移: ±2%          # 微妙音色变化
时间拉伸: ±2%           # 自然语速变化
混响: 轻微空间感
噪声: -65dB（几乎无声）
```

### 智能断句
```python
检测窗口: 5ms            # 精细检测
静音阈值: -35dB         # 灵敏度
最小静音: 0.2秒         # 短停顿
最小句子: 0.8秒         # 短句保留
```

## 📝 模式切换逻辑

| 从 \ 到 | 🎤 直播 | 💬 互动 | 🤖 替身 |
|---------|--------|--------|--------|
| 🎤 直播 | - | 继续 | 继续 |
| 💬 互动 | 不清空 | - | 不清空 |
| 🤖 替身 | **清空** | 不清空 | - |

- **替身 → 直播**：清空旧内容，重新开始录制
- **互动 → 直播**：不清空，继续录制
- **替身 → 互动**：暂停播放，保留播放位置

## ⚠️ 注意事项

1. **Windows 需要虚拟音频线**：
   - 推荐 VB-Cable
   - 下载：https://vb-audio.com/Cable/

2. **首次运行权限**：
   - 需要麦克风权限
   - Windows 防火墙可能提示，请允许

3. **合法使用**：
   - 仅供学习和合法直播场景
   - 请遵守各直播平台规则

## 🔗 依赖库

- PyQt6 - GUI 框架
- sounddevice - 音频输入输出
- soundfile - 音频文件处理
- librosa - 音频分析处理
- numpy - 数值计算

## 📄 许可证

MIT License

---

**免责声明**：本软件仅供技术学习和合法直播场景使用，用户需自行承担使用风险。
