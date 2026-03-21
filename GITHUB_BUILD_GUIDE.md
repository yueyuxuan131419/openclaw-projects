# 🚀 免配置 Windows 打包指南

## 方法一：GitHub Actions 自动打包（推荐）

### 步骤 1：创建 GitHub 仓库

1. 打开 https://github.com/new
2. 仓库名称：`qingqiu-anchor-avatar`（或任意名称）
3. 选择 **Public**（公开）或 **Private**（私有）
4. 点击 **Create repository**

### 步骤 2：上传代码

在 macOS 终端执行：

```bash
cd /Users/apple/.openclaw/workspace/streamvoice-avatar

# 初始化 git
git init
git add .
git commit -m "Initial commit"

# 添加你的 GitHub 仓库地址（替换 YOUR_USERNAME）
git remote add origin https://github.com/YOUR_USERNAME/qingqiu-anchor-avatar.git

# 推送代码
git branch -M main
git push -u origin main
```

### 步骤 3：等待自动打包

1. 打开 GitHub 仓库页面
2. 点击 **Actions** 标签
3. 看到 `Build Windows EXE` 工作流正在运行
4. 等待约 5-10 分钟

### 步骤 4：下载 EXE

1. 工作流完成后，点击 **Actions** → 最新的运行记录
2. 底部 **Artifacts** 部分
3. 下载 `青丘主播替身-Windows.zip`
4. 解压即可使用！

---

## 方法二：腾讯云 Cloud Studio（在线 IDE）

如果不想用 GitHub，可以用腾讯云的在线开发环境：

1. 打开 https://cloudstudio.net/
2. 注册/登录（可用微信扫码）
3. 创建新工作空间 → 选择 **Python** 模板
4. 上传项目文件（拖拽上传）
5. 在终端执行：

```bash
pip install pyinstaller
pyinstaller build_windows.spec
```

6. 下载 `dist/青丘主播替身.exe`

---

## 方法三：Gitpod（浏览器中打包）

1. 打开 https://gitpod.io/
2. 用 GitHub 账号登录
3. 创建新工作空间
4. 上传代码
5. 在终端执行打包命令
6. 下载生成的 exe

---

## 方法四：找一台已配置好的 Windows 电脑

如果以上都不想用，可以用这个一键配置脚本在 Windows 上快速配置：

### 创建文件 `setup.bat`：

```bat
@echo off
echo 正在安装依赖...

# 下载并安装 Python（如果未安装）
python --version > nul 2>&1
if errorlevel 1 (
    echo 正在下载 Python...
    curl -o python-installer.exe https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe
    python-installer.exe /quiet InstallAllUsers=0 PrependPath=1
    del python-installer.exe
)

# 安装依赖
python -m pip install --upgrade pip
pip install PyQt6 sounddevice soundfile librosa numpy pyinstaller

echo 安装完成！
pause
```

双击运行即可自动配置环境。

---

## 推荐方案

| 方案 | 难度 | 速度 | 推荐度 |
|-----|-----|-----|-------|
| GitHub Actions | ⭐ 最简单 | 5-10分钟 | ⭐⭐⭐⭐⭐ |
| 腾讯云 Cloud Studio | ⭐⭐ 简单 | 10分钟 | ⭐⭐⭐⭐ |
| Gitpod | ⭐⭐ 简单 | 10分钟 | ⭐⭐⭐ |
| Windows 配置 | ⭐⭐⭐ 麻烦 | 20分钟 | ⭐⭐ |

**强烈建议用 GitHub Actions**，完全零配置，推送代码自动打包！

---

## 常见问题

### Q1: GitHub Actions 打包失败？
- 检查 `.github/workflows/build.yml` 文件是否正确
- 检查代码是否完整推送到 GitHub
- 查看 Actions 日志排查错误

### Q2: 下载的 exe 被杀毒软件拦截？
- 这是 PyInstaller 打包的常见问题
- 将 exe 添加到杀毒软件白名单
- 或暂时关闭杀毒软件

### Q3: 想更新版本怎么办？
- 修改代码后再次 `git push`
- GitHub Actions 会自动重新打包
- 下载新的 Artifact 即可

---

## 快速开始（GitHub Actions）

最简单的步骤：

```bash
# 1. 在 GitHub 创建仓库（网页操作）

# 2. 推送代码
cd /Users/apple/.openclaw/workspace/streamvoice-avatar
git init
git add .
git commit -m "v1.0"
git remote add origin https://github.com/你的用户名/仓库名.git
git push -u origin main

# 3. 等待 5-10 分钟

# 4. 在 GitHub Actions 页面下载 exe
```

搞定！🎉
