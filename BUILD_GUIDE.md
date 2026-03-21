# Windows 打包指南

由于当前环境是 macOS，需要在 Windows 电脑上执行打包。

## 📋 打包步骤

### 1. 准备 Windows 电脑
- Windows 10 或 Windows 11
- 已安装 Python 3.10 或 3.11

### 2. 复制项目文件
将整个 `streamvoice-avatar` 文件夹复制到 Windows 电脑，确保包含以下文件：
```
streamvoice-avatar/
├── main.py
├── config.py
├── utils.py
├── build_windows.bat          ← 打包脚本
├── build_windows.spec         ← 打包配置
├── audio/
│   ├── __init__.py
│   ├── recorder.py
│   ├── processor.py
│   ├── player.py
│   └── sentence_detector.py
└── gui/
    ├── __init__.py
    └── main_window.py
```

### 3. 运行打包脚本
在 Windows 上打开命令提示符（CMD）或 PowerShell：

```cmd
cd streamvoice-avatar
build_windows.bat
```

或手动执行：
```cmd
cd streamvoice-avatar

# 安装依赖
pip install PyQt6 sounddevice soundfile librosa numpy pyinstaller

# 打包
pyinstaller build_windows.spec --clean --noconfirm
```

### 4. 获取打包结果
打包完成后，在 `dist` 文件夹中会生成：
```
dist/
├── 青丘主播替身.exe    ← 主程序
├── ...                ← 依赖文件
```

### 5. 测试运行
在打包的电脑上先测试运行：
1. 进入 `dist` 文件夹
2. 双击 `青丘主播替身.exe`
3. 确保能正常启动和使用

### 6. 分发使用
将整个 `dist` 文件夹压缩成 zip，即可分发给其他 Windows 用户使用。

---

## 🔧 可能遇到的问题

### 问题1：pip 安装速度慢
**解决**：使用国内镜像
```cmd
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple PyQt6 sounddevice soundfile librosa numpy pyinstaller
```

### 问题2：打包后的 exe 太大
**解决**：这是正常的，包含了 Python 解释器和所有依赖。可以使用 UPX 压缩减小体积。

### 问题3：在某些电脑上无法运行
**解决**：
- 确保目标电脑安装了 Visual C++ Redistributable
- 下载地址：https://aka.ms/vs/17/release/vc_redist.x64.exe

---

## 📦 文件清单

打包后的程序可以在以下环境运行：
- Windows 10 (64位)
- Windows 11 (64位)
- 无需安装 Python
- 无需安装其他依赖

---

## 🚀 快速测试命令

在 Windows 上测试前，建议先运行：
```cmd
cd streamvoice-avatar
python main.py
```

如果能正常运行，再进行打包。
