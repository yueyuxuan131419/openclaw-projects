# ⚡ 最简单的一键打包方案

## 推荐：GitHub Actions 自动打包（零配置）

### 仅需 3 步：

#### 第 1 步：创建 GitHub 仓库
- 打开 https://github.com/new
- 输入仓库名：`qingqiu-anchor-avatar`
- 点击 **Create repository**

#### 第 2 步：推送代码
在 macOS 终端执行：

```bash
cd /Users/apple/.openclaw/workspace/streamvoice-avatar
./push_to_github.sh
```

或手动执行：
```bash
cd /Users/apple/.openclaw/workspace/streamvoice-avatar
git init
git add .
git commit -m "v1.0"
git remote add origin https://github.com/你的用户名/qingqiu-anchor-avatar.git
git push -u origin main
```

#### 第 3 步：下载 EXE
- 等待 5-10 分钟
- 打开 `https://github.com/你的用户名/qingqiu-anchor-avatar/actions`
- 下载 `青丘主播替身-Windows.zip`
- 解压即可使用！

---

## 流程图

```
推送代码 ──→ GitHub 自动打包 ──→ 下载 EXE ──→ 直接使用
  (1分钟)       (5-10分钟)         (1分钟)
```

---

## 优势

✅ **零配置** - 不需要在 Windows 上安装任何东西  
✅ **自动化** - 推送代码后自动打包  
✅ **免费** - GitHub Actions 免费额度足够用  
✅ **可重复** - 更新代码后重新推送即可重新打包  

---

## 详细说明

查看 `GITHUB_BUILD_GUIDE.md` 获取完整指南。

---

## 备用方案

如果 GitHub 不方便：

1. **腾讯云 Cloud Studio** - 在线 IDE 打包
2. **Gitpod** - 浏览器中打包  
3. **预配置脚本** - 在 Windows 上快速配置环境

详见 `GITHUB_BUILD_GUIDE.md`
