@echo off
chcp 65001 >nul
echo ==========================================
echo   青丘主播替身 - Windows 打包脚本
echo ==========================================
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/5] 检查 Python 版本...
python --version

echo.
echo [2/5] 安装依赖...
python -m pip install --upgrade pip
pip install PyQt6==6.6.1 sounddevice==0.4.6 soundfile==0.12.1 librosa==0.10.1 numpy==1.26.3 pyinstaller==6.3.0

echo.
echo [3/5] 清理旧构建...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "__pycache__" rmdir /s /q "__pycache__"
for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"

echo.
echo [4/5] 开始打包...
python -m PyInstaller build_windows.spec --clean --noconfirm

echo.
echo [5/5] 打包完成！
if exist "dist\青丘主播替身.exe" (
    echo ✅ 成功: dist\青丘主播替身.exe
    echo.
    echo 使用说明:
    echo 1. 将整个 dist 文件夹复制到目标电脑
    echo 2. 运行 青丘主播替身.exe
    echo 3. 首次运行会请求麦克风权限，请点击"允许"
) else (
    echo ❌ 打包失败，请检查错误信息
)

echo.
pause
