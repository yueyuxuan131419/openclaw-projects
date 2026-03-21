#!/bin/bash
# 一键推送到 GitHub 自动打包

echo "🚀 青丘主播替身 - GitHub 自动打包"
echo "======================================"
echo ""

# 检查是否已初始化 git
if [ ! -d ".git" ]; then
    echo "📦 初始化 Git 仓库..."
    git init
    git add .
    git commit -m "Initial commit"
fi

# 提示用户输入 GitHub 信息
echo ""
echo "请先在 https://github.com/new 创建仓库"
echo ""
read -p "请输入你的 GitHub 用户名: " USERNAME
read -p "请输入仓库名称 (默认: qingqiu-anchor-avatar): " REPO_NAME
REPO_NAME=${REPO_NAME:-qingqiu-anchor-avatar}

echo ""
echo "选择推送方式:"
echo "1) HTTPS (需要密码/Token)"
echo "2) SSH (需要配置密钥)"
read -p "请选择 [1/2]: " PROTOCOL

if [ "$PROTOCOL" = "2" ]; then
    REMOTE_URL="git@github.com:${USERNAME}/${REPO_NAME}.git"
else
    REMOTE_URL="https://github.com/${USERNAME}/${REPO_NAME}.git"
fi

# 添加远程仓库
echo ""
echo "🔗 添加远程仓库..."
git remote remove origin 2>/dev/null
git remote add origin "$REMOTE_URL"

# 推送代码
echo ""
echo "📤 推送代码到 GitHub..."
git branch -M main
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ 推送成功！"
    echo ""
    echo "📋 下一步操作:"
    echo "1. 打开 https://github.com/${USERNAME}/${REPO_NAME}"
    echo "2. 点击 Actions 标签"
    echo "3. 等待打包完成（约 5-10 分钟）"
    echo "4. 下载 Artifacts 中的 exe 文件"
    echo ""
    echo "打包完成后访问:"
    echo "https://github.com/${USERNAME}/${REPO_NAME}/actions"
else
    echo ""
    echo "❌ 推送失败，请检查:"
    echo "1. 仓库是否已创建"
    echo "2. 用户名和仓库名是否正确"
    echo "3. 是否有推送权限"
fi
