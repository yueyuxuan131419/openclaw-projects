# 🚀 GitHub 自动推送使用说明

## 快速开始（3步搞定）

### 第 1 步：配置 GitHub
```bash
setup-github-push
```
按提示输入：
- GitHub 用户名
- GitHub Token（从 https://github.com/settings/tokens 生成）
- 仓库名称（默认: openclaw-projects）

### 第 2 步：推送代码
```bash
cd /Users/apple/.openclaw/workspace/streamvoice-avatar
push
```

### 第 3 步：下载 EXE
1. 等待 5-10 分钟
2. 打开 `https://github.com/你的用户名/你的仓库/actions`
3. 下载 `青丘主播替身-Windows.zip`

---

## 命令说明

| 命令 | 用途 |
|-----|------|
| `setup-github-push` | 首次配置 GitHub 连接 |
| `push` | 推送当前项目到 GitHub |
| `push 项目名` | 推送指定项目 |

---

## GitHub Token 获取步骤

1. 打开 https://github.com/settings/tokens
2. 点击 **Generate new token (classic)**
3. 勾选 **`repo`** 权限
4. 点击 **Generate token**
5. **立即复制**生成的 Token（只显示一次！）

---

## 常见问题

### Q: 提示 "未配置 GitHub"
运行 `setup-github-push` 完成首次配置

### Q: 推送失败
- 检查 Token 是否正确
- 检查仓库是否存在
- 检查网络连接

### Q: 如何更新代码后重新打包？
修改代码 → 运行 `push` → 等待 GitHub Actions 完成 → 下载新 exe

---

## 流程图

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  push 推送  │────▶│ GitHub 打包 │────▶│  下载 exe   │
│   (1分钟)   │     │ (5-10分钟)  │     │   (1分钟)   │
└─────────────┘     └─────────────┘     └─────────────┘
```

---

## 备用方案

如果 GitHub 不方便，还可以用：
- 腾讯云 Cloud Studio（在线 IDE）
- Gitpod（浏览器中打包）

详见 `GITHUB_BUILD_GUIDE.md`
