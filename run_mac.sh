#!/bin/bash
# Mac 一键安装运行脚本

echo "🎙️ StreamVoice Avatar - Mac 安装脚本"
echo "========================================"

# 进入项目目录
cd "$(dirname "$0")"

echo ""
echo "📦 步骤1: 检查 Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装: https://www.python.org/downloads/"
    exit 1
fi
python3 --version

echo ""
echo "📦 步骤2: 安装依赖（使用国内镜像加速）..."
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
if [ $? -ne 0 ]; then
    echo "⚠️ 国内镜像失败，尝试官方源..."
    pip3 install -r requirements.txt
fi

echo ""
echo "📦 步骤3: 检查 libsndfile..."
if ! command -v brew &> /dev/null; then
    echo "⚠️ 未安装 Homebrew，如果运行报错请手动安装:"
    echo "   brew install libsndfile"
else
    brew install libsndfile 2>/dev/null || echo "✓ libsndfile 已安装"
fi

echo ""
echo "🚀 步骤4: 启动程序..."
echo "⚠️ 注意: 首次运行会请求麦克风权限，请点击'允许'"
echo ""
python3 main.py
