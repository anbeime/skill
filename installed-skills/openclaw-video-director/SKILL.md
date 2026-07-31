---
name: openclaw-video-director
description: |
  OpenClaw（龙虾）AI 视频编导技能。将 OpenClaw 改造为全自动视频制作助手，支持语音/文字指令驱动的视频生成全流程。
  TRIGGER when: 用户提到 OpenClaw、龙虾、AI编导、AI自动做视频、AI视频制作、视频自动化、Seedance、AI漫剧、视频脚本生成、AI剪辑 等。
  DO NOT TRIGGER when: 纯 ffmpeg 命令使用（用视频截帧技能）、通用视频剪辑软件操作、与 OpenClaw 无关的视频制作。
description_zh: "OpenClaw AI 视频编导 — 全自动视频制作技能"
description_en: "OpenClaw AI Video Director — Fully automated video production skill"
license: MIT
metadata:
  category: ai-video
  version: "1.0.0"
  sources:
    - B站视频 BV195XrBBEax「我把OPENCLAW改造成了全自动做视频的龙虾编导！」by AI先生李豪
    - OpenClaw 官方文档 openclaw-docs.dx3n.cn
    - OpenClaw 101 教程站 openclaw101.dev
    - 腾讯云「OpenClaw + 轻量服务器打造全自动视频流水线」
    - cooyue.cn「用 OpenClaw 做视频：从创意到发布完整流程」
---

# OpenClaw AI 视频编导技能

## 概述

OpenClaw（社区昵称"小龙虾"）是一款开源 AI Agent 框架，GitHub 26万+ Star。通过安装视频专用 Skills，可以实现**从一句话描述到完整视频成品**的全自动化流程。

核心能力：语音/文字输入 → AI 脚本生成 → AI 生图/视频 → AI 剪辑合成 → 成品输出。

---

## 一、OpenClaw 是什么

| 项目 | 说明 |
|------|------|
| **全称** | OpenClaw |
| **昵称** | 小龙虾（因图标为红螯龙虾） |
| **类型** | 开源 AI Agent 框架（MIT 协议） |
| **GitHub** | 26万+ Star，2025 年发布，2026 年爆火 |
| **核心定位** | 本地优先的 AI 执行框架，支持 200+ 大模型接入 |
| **运行平台** | Windows (WSL)、macOS、Linux、树莓派、Docker |
| **技能生态** | ClawHub 技能市场，5400+ 社区技能 |

### 核心架构

```
用户指令 (Telegram/微信/手机App/命令行)
    ↓
Gateway（网关）→ 路由到对应 Agent
    ↓
Brain（大脑）→ 调用大语言模型推理
    ↓
Skills（技能）→ 执行具体任务（生图/视频/剪辑/...）
    ↓
Memory（记忆）→ 混合检索（BM25 + 向量搜索）
```

---

## 二、环境准备与安装

### 2.1 系统要求

| 项目 | 最低配置 | 推荐配置 |
|------|----------|----------|
| **CPU** | i5 / Ryzen 5 | i7 / Ryzen 7 |
| **内存** | 8GB | 16GB+ |
| **GPU** | 非必须（可用云端 API） | NVIDIA GPU（本地推理） |
| **磁盘** | 20GB | 50GB+ |
| **网络** | 需要访问 AI API | 带宽 ≥5Mbps |

### 2.2 基础工具安装

```bash
# Node.js（OpenClaw 运行环境）
# 前往 https://nodejs.org 下载安装 LTS 版本

# FFmpeg（视频处理核心）
sudo apt install ffmpeg          # Linux
brew install ffmpeg              # macOS
winget install FFmpeg             # Windows

# yt-dlp（视频下载）
pip install yt-dlp

# Whisper（字幕生成，可选）
pip install openai-whisper
```

### 2.3 安装 OpenClaw

**方式一：快速安装脚本（推荐新手）**
```bash
# 官方一键安装
curl -fsSL https://get.openclaw.sh | bash
```

**方式二：手动部署**
```bash
git clone https://github.com/openclaw/openclaw.git
cd openclaw
pnpm install && pnpm build
pnpm onboard    # 交互式配置向导
```

**方式三：Docker 部署**
```bash
docker run -d -p 8080:8080 \
  -v /data/openclaw:/app/data \
  openclaw/openclaw:latest
```

**方式四：云平台一键部署**
- 阿里云、腾讯云 Lighthouse、DigitalOcean、Hostinger 均支持

### 2.4 配置 AI 模型

```bash
# 运行配置向导
openclaw configure
```

支持的模型提供商：
- OpenAI (GPT-4o / GPT-o3)
- Anthropic (Claude)
- Google (Gemini)
- 阿里云百炼 (Qwen)
- 本地模型 (Ollama)
- 200+ 其他模型

---

## 三、视频制作技能安装

### 3.1 核心视频技能

从 ClawHub 技能市场安装视频制作相关技能：

```bash
# 视频下载技能
npx clawhub@latest install YouTubeDownloader

# 智能剪辑技能
npx clawhub@latest install SmartClip

# AI 视频生成技能（Seedance 2.0）
npx clawhub@latest install seedance-video-gen

# AI 漫剧生成技能
npx clawhub@latest install ai-comic-drama

# 字幕生成技能
npx clawhub@latest install whisper-subtitle

# 视频压缩技能
npx clawhub@latest install video-compressor
```

### 3.2 ⚠️ 安全提醒

> **重要：安装第三方技能前务必审查源码！**
> ClawHub 技能市场已发现数百个恶意技能，存在数据窃取风险。
> - 优先使用官方或经过社区审核的技能
> - 检查技能的 `package.json` 和脚本内容
> - 不要安装来源不明的技能

### 3.3 MCP 服务配置（可选增强）

编辑 OpenClaw 配置文件，注册 MCP 服务：

```json
{
  "mcp": {
    "servers": {
      "douyin": {
        "command": "node",
        "args": ["/path/to/douyin-mcp/dist/index.js"]
      }
    }
  }
}
```

---

## 四、全自动视频制作流程

### 4.1 完整工作流

```
┌─────────────────────────────────────────────────────┐
│                 用户输入（语音/文字）                    │
│         "帮我做一个30秒的AI科技短视频"                    │
└─────────────────────┬───────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│ Step 1: 选题策划                                      │
│  - 分析热门趋势，确定选题方向                           │
│  - 输出：选题方案 + 目标平台适配建议                     │
└─────────────────────┬───────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│ Step 2: 脚本生成                                      │
│  - AI 生成结构化口播脚本                               │
│  - 口语化表达，每句 ≤ 15 字                            │
│  - 标注画面匹配点                                     │
│  - 输出：完整脚本 + 分镜描述                            │
└─────────────────────┬───────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│ Step 3: 素材生成                                      │
│  - AI 图片生成（Midjourney/SD/通义万相）               │
│  - AI 视频片段生成（Seedance 2.0/可灵/Sora）           │
│  - BGM 匹配 + 配音生成（ElevenLabs/ChatTTS）           │
│  - 输出：视频素材 + 图片素材 + 音频素材                  │
└─────────────────────┬───────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│ Step 4: 智能剪辑合成                                   │
│  - 画面转场检测 + 情绪分析                              │
│  - 自动剪辑精彩片段                                    │
│  - 添加字幕（Whisper 生成 SRT）                        │
│  - 特效 + 转场 + 水印处理                              │
│  - 输出：完整视频文件                                   │
└─────────────────────┬───────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────┐
│ Step 5: 多平台发布适配                                 │
│  - 抖音版（≤ 1 分钟，竖屏 9:16）                       │
│  - B站版（可更长，横屏 16:9）                           │
│  - 小红书版（图文笔记 + 短视频）                         │
│  - 输出：各平台适配版本 + 优化标题/标签                   │
└─────────────────────────────────────────────────────┘
```

### 4.2 关键命令参考

| 用途 | 命令 |
|------|------|
| 下载视频 | `yt-dlp -f best "视频链接"` |
| 提取音频 | `ffmpeg -i video.mp4 -vn audio.wav` |
| 生成字幕 | `whisper audio.wav --language Chinese --output_format srt` |
| 视频压缩 | `ffmpeg -i input.mp4 -c:v libx264 -crf 23 output.mp4` |
| 视频裁剪 | `ffmpeg -i input.mp4 -ss 00:00:10 -to 00:01:00 -c copy output.mp4` |
| 合并视频 | `ffmpeg -f concat -safe 0 -i list.txt -c copy merged.mp4` |
| 添加字幕 | `ffmpeg -i video.mp4 -vf subtitles=sub.srt output.mp4` |
| 生成封面 | AI 图片生成模型或 Midjourney |

### 4.3 SmartClip 配置示例

```yaml
# smart-clip.yaml
output_duration: [15, 30, 60]    # 输出时长选项（秒）
subtitle_lang: zh-CN              # 字幕语言
remove_watermark: true            # 去水印
transition_style: smooth          # 转场风格
bgm_volume: 0.3                   # 背景音乐音量
```

---

## 五、手机端语音操控（AI 编导模式）

这是视频 BV195XrBBEax 的核心内容——通过手机语音操控 OpenClaw 自动做视频。

### 5.1 设置步骤

1. **部署 OpenClaw 到云服务器**（推荐腾讯云 Lighthouse 2核4G，¥74/月）
2. **配置手机接入**：通过 Telegram Bot / 微信 / 飞书机器人连接
3. **安装视频技能包**：YouTubeDownloader + SmartClip + seedance-video-gen + whisper-subtitle
4. **配置 AI 模型 API Key**：至少配置一个文本模型 + 一个图片/视频生成模型

### 5.2 语音指令示例

```
# 指令 1：生成视频脚本
"帮我写一个30秒的科技类短视频脚本，主题是AI改变生活"

# 指令 2：生成视频素材
"根据刚才的脚本，帮我生成每个镜头的画面，用AI画图"

# 指令 3：生成视频片段
"把这些画面生成5秒的视频片段"

# 指令 4：自动剪辑合成
"把所有片段剪辑成一个完整视频，加上字幕和BGM"

# 指令 5：一键发布适配
"帮我适配成抖音版本，生成竖屏封面"
```

### 5.3 一键全自动模式

配置自动化任务后，可以实现完全无人值守：

```yaml
# 自动化任务配置示例
tasks:
  - name: "每日AI短视频生成"
    schedule: "0 9 * * *"    # 每天早上9点
    actions:
      - generate_script:
          topic: "科技热点"
          duration: 30
          platform: "douyin"
      - generate_assets:
          style: "tech"
          resolution: "1080x1920"
      - auto_edit:
          subtitle: true
          bgm: true
          watermark: false
      - export:
          formats: ["mp4", "cover.jpg"]
```

---

## 六、AI 漫剧专用流程

OpenClaw 支持全自动 AI 漫剧生成，适合故事类内容创作。

### 6.1 漫剧生成流程

```
故事构思 → 分镜脚本 → 角色设定（保持一致性）→ 场景生成 → 角色动态合成 → 字幕配音 → 成片输出
```

### 6.2 角色一致性方案

```yaml
# config.yaml - 角色预设
characters:
  - name: "主角小明"
    description: "20岁男生，短发，穿蓝色卫衣"
    reference_image: "xiaoming_ref.png"
    style: "anime"
  - name: "女主小红"
    description: "19岁女生，长发，穿粉色连衣裙"
    reference_image: "xiaohong_ref.png"
    style: "anime"
```

### 6.3 漫剧服务器配置

| 项目 | 要求 |
|------|------|
| CPU | i7 / Ryzen 7 以上 |
| 内存 | 16GB+（推荐 32GB） |
| GPU | NVIDIA GPU（CUDA 支持） |
| 存储 | 50GB+ SSD |
| 模型 | Atlas Cloud 免费额度 或 本地 SD/SDXL |

---

## 七、平台集成配置

### 7.1 Telegram Bot 接入

```bash
# 在 OpenClaw 配置中添加 Telegram
openclaw configure
# 选择 Telegram → 输入 Bot Token（从 @BotFather 获取）
```

### 7.2 微信接入

```bash
# 通过 WeChat MCP 或第三方桥接服务
openclaw configure
# 选择 WeChat → 按提示配置
```

### 7.3 飞书机器人

```bash
openclaw configure
# 选择 Feishu → 输入 App ID 和 App Secret
```

---

## 八、常见问题排查

### 8.1 性能问题

| 问题 | 解决方案 |
|------|----------|
| 视频生成太慢 | 先用 60 秒短视频测试；确保 GPU 驱动正常；关闭其他占用内存的程序 |
| 角色不一致 | 在 config 中预设人物描述，或上传参考图 |
| API 额度不足 | 优先用免费额度，或切换到本地模型 |
| 内存不足 | 增加 swap 空间；减少并发任务数 |

### 8.2 安全加固

1. **及时更新**：始终保持 OpenClaw 最新版本
2. **审查技能**：绝不安装未经验证的第三方技能
3. **网络隔离**：避免将实例直接暴露在公网
4. **最小权限**：以最小必要权限运行
5. **API 支出限制**：设置 API 调用预算上限

---

## 九、成本估算

| 项目 | 费用 |
|------|------|
| OpenClaw 本体 | 免费（开源 MIT） |
| 云服务器（腾讯云 Lighthouse 2核4G） | ≈ ¥74/月 |
| AI 模型 API（按需） | ≈ ¥10-100/月（取决于使用量） |
| 域名（可选） | ≈ ¥50/年 |
| **总计** | ≈ ¥100-200/月 |

---

## 十、使用此技能时的指引

当用户触发此技能时，按以下优先级响应：

1. **如果用户想从头搭建**：引导走「第二章 环境准备与安装」→ 「第三章 视频技能安装」
2. **如果用户已有 OpenClaw，想做视频**：直接跳到「第三章 技能安装」→ 「第四章 制作流程」
3. **如果用户想做 AI 漫剧**：跳到「第六章 AI 漫剧专用流程」
4. **如果用户想语音操控**：跳到「第五章 手机端语音操控」
5. **如果用户遇到问题**：跳到「第八章 常见问题排查」

### 推荐对话模板

```
用户：我想用 OpenClaw 自动做视频
助手：太好了！我帮你梳理一下。你目前的阶段是？
  1. 还没安装 OpenClaw，从零开始
  2. 已安装 OpenClaw，想加装视频技能
  3. 已有视频技能，想实现全自动流程
  4. 遇到了具体问题需要排查

请告诉我你的情况，我针对性地帮你。
```
