---
name: kb-to-mpt
description: 知易知识库 → 短视频 流水线。把 knowledge_cards（蓝/绿/红卡）批量生成书摘/知识类短视频（复用 MoneyPrinterTurbo），并提供本地 faster-whisper 转写桥，把任意视频转文字入库成为脚本源。触发：用户想"把书/知识库做成视频""批量产出书摘视频""把视频转写进知识库"。
version: 1.0.0
author: TOPGO
tags:
  - video
  - knowledge-base
  - money-printer-turbo
  - whisper
  - automation
license: MIT
---

# 知易知识库 → 短视频 流水线 (kb-to-mpt)

## 任务目标

- 把**知易 `knowledge_cards`** 直接变成可渲染的短视频脚本，推给本地 **MoneyPrinterTurbo (MPT)** 批量生成书摘/知识类视频（口播 + 字幕 + 素材 + BGM）。
- 提供 **faster-whisper 本地转写桥**，把任意视频（B站/YouTube/TikTok）下载音频 → 转文字 → 切片成蓝卡入库，成为上一步的脚本源。
- 复用而非重复造轮子：MPT 就是"书本视频 skill"本体（E 盘已部署），本技能只做**知识库 ↔ 视频生成**的编排桥。

## 能力包含

1. `kb_to_mpt.py` — 读知识库卡片 → 组装 `video_script` + `video_terms` → `POST /api/v1/videos` 推 MPT。
2. `transcribe_fw.py` — faster-whisper（项目机器人同款 STT）转写音频 → `.vtt`/`.txt`，供入库。
3. 配套：`build_naval_cards.py`（范例：书摘视频转写 → 建专题蓝卡）与 `ingest_video_material.py`（vtt → 蓝卡通用入库）。

## 触发条件

- "把这本书/这个专题做成视频""批量产出书摘视频""知识库怎么变成视频"。
- "把这个视频转写进知识库当素材""下载视频字幕入库"。

## 使用方式

### 前置环境

| 依赖 | 说明 | 准备 |
|------|------|------|
| MoneyPrinterTurbo | 视频生成引擎（`C:/E/MoneyPrinterTurbo-main`，默认 `:8080`） | 真机跑 `webui.bat` 启动 |
| ffmpeg | 音频解码（whisper 需要） | `winget install ffmpeg`，或复用知易内置 `_bin/ffmpeg.exe` |
| faster-whisper | 转写引擎（CT2 格式权重） | 见下方"权重准备" |
| 知易 DB | `C:/D/zhiyi/backend/data/antinet.db` | 已有 |

**权重准备（一次性，绕开 huggingface_hub 沙箱限制，直接目录加载）：**
把 `Systran/faster-whisper-<size>` 仓库的 `model.bin + config.json + tokenizer.json + vocabulary.txt`
放到 `C:/D/zhiyi/data/whisper_models/<size>/`，`transcribe_fw.py` 即以目录路径直接加载，不再触发任何下载。
推荐 `small`（中文可用，~461MB）；`base` 更快但中文弱。

### A. 知识库 → 视频（MPT 批量出片）

```bash
# 1) 某专题全部卡片 → 一条视频（dry-run 先看文案）
python kb_to_mpt.py --project-id <PID> --dry-run

# 2) 按关键词搜卡片生成（如"纳瓦尔宝典"）
python kb_to_mpt.py --search "纳瓦尔" --subject "纳瓦尔宝典精读" --dry-run

# 3) 真机启 MPT 后实际上传生成
python kb_to_mpt.py --project-id <PID> --mpt-url http://127.0.0.1:8080
```

MPT 收到 `video_subject` + `video_script`（卡片拼装的连贯口播）+ `video_terms`（标题抽词作素材关键词），自动产出高清短视频。

### B. 视频 → 知识库（转写入库，成为脚本源）

```bash
# 1) 下载音频（用 yt-dlp 技能；B站 bestaudio 无需 ffmpeg）
python yt-dlp-video-downloader/scripts/run_yt_dlp.py -f bestaudio \
  -o "material/audio/%(id)s.%(ext)s" "<视频URL>"

# 2) faster-whisper 本地转写
python transcribe_fw.py "material/audio/<BV>.m4a" --out material/audio --model small --lang zh

# 3) 切片成蓝卡入库（通用 vtt→卡）
python ingest_video_material.py material/audio --url "<视频URL>" --project-id <PID>

# 或：书摘类按段落建专题（范例脚本）
python build_naval_cards.py material/audio/<BV>.txt
```

## 完整流水线（书 → 视频矩阵）

```
书/视频 → [yt-dlp 下载音频] → [transcribe_fw 转写] → [build_* 建蓝卡专题]
   → [kb_to_mpt 组装脚本] → [MPT 渲染成片] → 发布分发(ai-trend-publish)
```

循环复用：换一本书/一个专题，只改 `--project-id` 或 `--search`，即可批量产出下一支视频。

## 注意

- 真机渲染需 GPU + 显示器；沙箱无 GPU 时只能准备脚本与知识库，渲染在真机完成。
- 外发/发布前遵守平台规则与 AGENTS.md §3 数据不出域；批量内容注意原创性与版权。
- `kb_to_mpt.py` 的 DB 路径硬编码为 `C:/D/zhiyi/backend/data/antinet.db`，知易项目用户即开即用。
