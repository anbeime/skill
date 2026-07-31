---
name: douyin-video-download
description: 抖音视频批量下载工具。支持单视频、批量下载、自动去重、无水印下载，智能选择最优下载方式（yt-dlp/Playwright）。
version: 1.1.2
---

# 抖音视频下载器 (安全加固版)

> 强大的抖音视频批量下载工具，支持无水印、1080P 高清下载。

## 功能特性

- ✅ **安全加固**: 使用 `child_process.spawn` 处理外部调用，彻底杜绝命令注入风险。
- ✅ **高清无水印**: 自动解析 1080P 直连，移除水印。
- ✅ **稳定下载**: 采用多后端自动切换技术（内置解析引擎 + 社区公认工具），确保高成功率。
- ✅ **批量处理**: 支持从文本文件读取链接批量下载。

## 安装

### 1. 安装依赖

```bash
# 进入技能目录
cd ~/.openclaw/workspace/skills/douyin-video-download

# 安装 Node.js 依赖
npm install

# 安装 Playwright Chromium 浏览器二进制文件 (仅需一次)
# 提示: 如果在受限网络环境下，请确保已配置好 npm 镜像
npx playwright install chromium
```

### 2. 安装外部工具 (可选但推荐)

- **yt-dlp**: 提供最佳下载体验和更高的稳定性。
  - **Linux/macOS**: `sudo curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o /usr/local/bin/yt-dlp && sudo chmod a+rx /usr/local/bin/yt-dlp`
  - **Windows**: 从 [yt-dlp releases](https://github.com/yt-dlp/yt-dlp/releases) 下载 `.exe` 并添加到 PATH。

## 使用

### 单视频下载

```bash
# 使用分享链接
node scripts/download.js "https://v.douyin.com/xxxxx"

# 使用完整链接
node scripts/download.js "https://www.douyin.com/video/123456"
```

### 批量下载

```bash
# 从文件读取链接列表
node scripts/download.js --batch links.txt

# links.txt 格式（每行一个链接，支持 # 注释）
https://v.douyin.com/xxxxx
# 这是另一个视频
https://v.douyin.com/yyyyy
```

### 高级选项

```bash
# 指定输出目录
node scripts/download.js "https://v.douyin.com/xxxxx" --output ./videos

# 指定文件名
node scripts/download.js "https://v.douyin.com/xxxxx" --filename myvideo

# 并发下载数量 (批量模式)
node scripts/download.js --batch links.txt --concurrent 3
```

## 供应链与安全性说明

- **浏览器二进制文件**: Playwright 会下载 Chromium 浏览器。如果对安全性有极高要求，可以通过环境变量 `EXECUTABLE_PATH` 指定本地已安装的 Chrome 路径（需修改代码支持）。
- **npm 镜像**: 如果您位于中国大陆，建议使用腾讯云或阿里云镜像以加速安装。
- **隐私**: 本工具仅访问抖音公开页面，不涉及用户登录信息。

## 作者

Leo & Neo (Startup Partners)
