# anything2explainer

[![Claude Code](https://img.shields.io/badge/Claude%20Code-skill-D97757?logo=anthropic&logoColor=white)](https://claude.com/claude-code)
[![Codex](https://img.shields.io/badge/Codex-skill-000000)](https://openai.com/codex)
[![Remotion](https://img.shields.io/badge/Remotion-4.0-0B84F3)](https://remotion.dev)
[![License](https://img.shields.io/badge/license-PolyForm%20Noncommercial-informational)](LICENSE)

[English](README.md) | **简体中文**

**给一个主题，产出一条带配音的科普讲解视频。** anything2explainer 是一个 [Claude Code](https://claude.com/claude-code) / [Codex](https://openai.com/codex) skill：输入任意主题，输出一条黑底 MG（motion graphics）风格的讲解视频，带 TTS 配音、字幕和章节进度条，中文或英文都行。画面全部由 [Remotion](https://remotion.dev)（React + TypeScript）代码绘制，不用素材库，不用视频生成模型，也不使用任何现有视频的帧。

它不是一个 CLI。仓库里装的是让 AI 编程 agent 把片子做出来的整套方法：可编译的 Remotion 模板工程、图元与光效库、配音/分镜/渲染/量化质检工具、风格与动效规范、多 agent 分工协议，以及一条完整样片作为质量标尺。

**中文版**——《RAG 与知识库》v2，4′54″，44 句 / 1490 字，点阵波幕底（`bg: 'dots'`），配音走"自带 TTS"路径（火山引擎语音合成 2.0 + 强制对齐）：

https://github.com/user-attachments/assets/5c213990-cbba-439e-8371-fbb3aa348e05

**英文版**——*RAG & Knowledge Bases*，5′02″，44 句 / 785 词，kokoro-82m `am_liam` 自然语速：

https://github.com/user-attachments/assets/e2771c68-a28c-4459-ac5a-a5b685181eeb

两版共用一套分镜和 44 个镜头，英文版按英文配音逐镜头重排帧号。中文原版（4′35″，星点幕底，8 个构建 agent 并行 40 分钟 + 两轮 QC）的全套过程文件在 [`examples/rag/`](examples/rag/)（调研 → 解说词 → 分镜表 → 镜头源码 → QC 报告 → 交付说明），成片帧在 [`examples/rag/frames/`](examples/rag/frames/)。

## 它做什么

- **输入**：一个主题（"讲一下向量数据库"），或一篇想改成视频的文章/文档。时长和语言由你定。
- **输出**：1280×720 的 H.264 MP4，配音与字幕按词边界对齐，带章节卡、顶部 HUD 和底部章节进度条；同时交付全套过程文件（带出处的调研文档、解说词、分镜表、逐镜头源码、QC 报告）。
- **怎么做**：agent 先做带出处的调研，写解说词，生成配音和帧级时间轴，逐镜头写分镜，再派多个构建 agent 并行写 Remotion 组件（一个镜头一个文件）；渲染后由 QC agent 按书面判据逐帧检查，修完再交付。
- **耗时**：按时长约 1–3 小时，大部分时间是 agent 并行构建镜头。全程只在四个确认点问你。

## 成片规格

| | |
|---|---|
| 画幅 / 帧率 | 1280×720 @ 30fps，H.264 |
| 时长 | 由你定（见下表），2–8 分钟都能做 |
| 语言 | 中文或英文（`src/config.ts` 的 `lang`）；排版、字幕长度预算、配音默认值随它切换 |
| 视觉 | 黑底，幕底二选一：点阵波（默认，移植自 video-talkcraft 的 dot-field-wave），或星点 + 雾底渐变（`src/config.ts` 的 `bg`）；白线条图形 + 紫色重点；超粗黑体大字 |
| 常驻层 | 44px 白字黑边字幕、底部章节进度条、顶部胶囊 HUD、可选流程轨、片尾署名 `built by Anything2Explainer skill`（`config.builtBy`，设为 `''` 去掉） |
| 配音 | 中文 edge-tts `zh-CN-YunxiNeural`（云希，男声，原速不加速 ≈5.5 字/秒）/ 英文 kokoro-82m `am_liam`（Liam，男声）；也可用你自己的 TTS 或成品配音 |

时长决定内容丰富程度与全流程规模：

| 时长 | 中文字数 | 英文词数 | 句 / 镜头数 | 构建 agent | 产出耗时 | 磁盘 |
|---|---|---|---|---|---|---|
| 2–3 分钟 | 650–880 | 280–420 | 24–32 | 4–6 | ≈1 小时 | ≈2GB |
| 3–5 分钟（样片档） | 1100–1400 | 420–700 | 40–50 | 8 | ≈2 小时 | ≈2GB |
| 5–8 分钟 | 1650–2200 | 700–1150 | 60–80 | 10–14 | ≈2–3 小时 | ≈3GB |

章数按内容定、受时长约束：<3 分钟单章（不出章节卡），3–5 分钟 3–4 章且每章 ≥60 s，5–8 分钟 4–6 章；进度条按解说词声明的章数等宽分段。解说词用空行分段，一段就是一个镜头：段内句间只隔 10 帧、段末 30 帧，停顿落在画面切换处，每个镜头末拍落位后能停 1–1.5 s 再切；成片比纯语音长 5–8% 是设计内的。

## 安装

```bash
git clone https://github.com/Vincentwei1021/anything2explainer.git
ln -s "$PWD/anything2explainer" ~/.claude/skills/anything2explainer   # Claude Code
ln -s "$PWD/anything2explainer" ~/.codex/skills/anything2explainer    # Codex
```

依赖：

```bash
# Node ≥18（模板 npm install 会装 remotion 4.0.507 / react 19）
brew install ffmpeg          # 抽帧 / 转码，必需

python3 -m venv ~/.venvs/a2e && source ~/.venvs/a2e/bin/activate
pip install 'edge-tts==7.2.8' numpy pillow scipy   # 建议固定 edge-tts 版本：它跟着微软端点变，升级常有破坏性（7.2.0 起词边界要显式请求，脚本已处理）

# 只做英文片时再装（kokoro-82m 本地推理）
pip install kokoro soundfile && brew install espeak-ng
```

`scipy` 只给质检脚本 `frame_metrics.py` 用。脚本是 zsh + Python 3，在 macOS 上开发与验证；Linux 应可用，Windows 未测试。

### Linux / 树莓派（ARM）

已在树莓派 5（ARM64、Debian trixie、Python 3.13）上跑通。与 macOS 有三处不同：

```bash
sudo apt install zsh espeak-ng                 # 脚本是 #!/bin/zsh；espeak-ng 供 kokoro/piper 的 G2P

# Remotion 没有 linux-arm64 的无头浏览器 → 指向系统 Chromium：
sudo apt install chromium                       # 或 chromium-browser
export REMOTION_BROWSER_EXECUTABLE=/usr/bin/chromium   # 由 template/remotion.config.ts 读取（macOS 上无副作用）
```

**Linux/ARM 上的配音。** 默认英文引擎 `kokoro` 在 ARM/Python 3.13 上很难装：它固定了旧版 numpy（无 aarch64/py3.13 轮子，只能源码编译，会失败），且依赖 spaCy → `blis`（无 aarch64 轮子、编译不过）。补了两个能干净安装的本地引擎，用 `TTS_ENGINE` 指定，二者都走既有的“逐字幕块合成”路径：

```bash
# kokoro_onnx —— 音色自然，onnxruntime（不依赖 torch/spaCy）。模型与声音库从
#   github.com/thewh1teagle/kokoro-onnx 的 releases 下（kokoro-v1.0.onnx、voices-v1.0.bin）
pip install kokoro-onnx
TTS_ENGINE=kokoro_onnx KOKORO_ONNX_MODEL=…/kokoro-v1.0.onnx KOKORO_ONNX_VOICES=…/voices-v1.0.bin \
  KOKORO_ONNX_VOICE=am_michael python3 scripts/tts_build.py

# piper —— 最快的本地引擎，音色偏机械，作树莓派原生兜底。语音 .onnx 从 github.com/rhasspy/piper 下
pip install piper-tts
TTS_ENGINE=piper PIPER_MODEL=…/en_US-ryan-medium.onnx python3 scripts/tts_build.py
```

`edge` 引擎（自然、免费、有词级边界）在 Linux 上也能用，且不需要本地模型——它是调微软云端接口：`TTS_ENGINE=edge VOICE=en-US-AndrewNeural python3 scripts/tts_build.py`。

## 用法

在 Claude Code 或 Codex 里直接说要做什么，skill 会被触发：

> 讲一下向量数据库，做成一条讲解视频

> Make me an explainer video about vector databases.

它会按 `SKILL.md` 的 9 个阶段走：

1. **建项目**：从模板复制出 Remotion 工程。
2. **调研**（1 个 agent）：带出处的调研文档，含数字与比喻清单，每条带 URL。
3. **解说词与时间轴**：写文案，TTS 配音，按词边界生成帧级时间轴和字幕表。
4. **分镜**：每镜头一行，写帧区间、节拍、画面、动效、主角与光。
5. **覆盖层与图元**：片头、章节卡、HUD、流程轨，外加 2–5 个主题图标。
6. **打样**（1 个 agent）：先做第一组镜头，渲 30 秒样片给你看风格。
7. **并行构建**：其余各组，每个 agent 5–7 个镜头，写纯函数 Remotion 组件。
8. **渲染**：整片渲染并跑量化帧指标。
9. **QC 与修复**：每章一个 QC agent，按组派修复 agent，复验后写交付说明。

也可以手动跑模板：

```bash
template/scripts/new_project.sh ~/work/my-video myslug
cd ~/work/my-video
# 1. research/调研.md          2. script/narration.txt → python3 scripts/tts_build.py
# 3. script/storyboard_src.md → python3 scripts/render_storyboard.py     4. 改 src/config.ts
# 5. src/shots/G1..Gn          6. scripts/preview.sh 30（前 30 秒样片）
# 7. VER=v1 scripts/render.sh + python3 scripts/frame_metrics.py         8. QC → 修 → v2/v3
```

## 四个确认点

流程会在这四处停下来等你回话，不会闷头做完（细节见 `SKILL.md`）：

1. **时长与语言**：写文案之前。时长决定句数、镜头数和并行 agent 数，也就决定内容能铺多丰富；语言决定 `src/config.ts` 的 `lang`，进而影响排版、字幕预算和默认音色。
2. **解说词定稿**：配音之前。定稿后帧号会被每个镜头硬编码，改一个字全片重对位，这是最便宜的干预点。
3. **配音**：跑 TTS 之前问一句你有没有偏好的 TTS；没有就用默认（中文 edge-tts 云希、英文 kokoro-82m Liam）。也可以直接给成品配音，自己按逐句时间轴填 `timeline.ts`。
4. **前 30 秒样片**：只建完第一个构建组就渲 30 秒给你看风格。在这里改一次是 1 个组的成本，整片渲完再改是全部组。

## 和其他工具的区别

| 工具类型 | 产出什么 | anything2explainer 的不同 |
|---|---|---|
| 视频生成模型（Sora、Veo、可灵、即梦） | 按提示词生成的画面 | 确定性代码而不是像素：画面上每个数字都能追溯到来源 URL，任何一帧都能通过改一个镜头文件修好 |
| 数字人 / 口播工具（HeyGen、Synthesia） | 一个数字人读稿 | 没有主播；用 MG 图形把机制画出来，解说词驱动画面 |
| 直接手写 Remotion / Motion Canvas | 一块可编程的视频画布 | 在画布之上给出整套方法：调研 → 解说词 → 分镜 → 并行构建 → QC，附风格规范、动效词表和一条可对标的样片 |
| Manim | Python 数学动画 | agent 驱动的端到端流水线，字幕按 TTS 对齐，带章节与 QC；技术栈是 React / TypeScript 而不是 Python |

## 常见问题

**支持哪些 AI 编程 agent？**
为 Claude Code 和 Codex 编写，也只在这两个上跑过。skill 本身就是 Markdown 加一个 Remotion 工程，任何能读 `SKILL.md` 式 skill 目录、能执行 shell 命令的 agent 理论上都能照着做。

**需要 GPU 吗？**
不需要。Remotion 用无头 Chromium 在 CPU 上渲染。中文默认配音 edge-tts 是调微软云端接口；英文默认 kokoro-82m 是 8200 万参数的小模型，本地 CPU 就能跑。

**能用自己的声音或别的 TTS 吗？**
可以。把成品音频放到 `public/assets/<slug>/audio.wav`，按 `tts_build.py` 文件头的格式手填 `src/common/timeline.ts` 和 `subs.ts`，后续流程不变。

**能换视觉风格吗？**
只做这一种风格，是有意为之，唯一的开关是幕底：`src/config.ts` 的 `bg`（默认 `'dots'` 点阵波，可选 `'stars'` 星点雾底）。其他要换就改 `reference/style-guide.md` 和 `src/ui.tsx`，镜头代码只用这些图元。

**渲染结果可复现吗？**
可以。所有动画都是帧号的纯函数，随机数带种子，文字排版靠计算而不测 DOM，重渲一遍帧完全一样。

**能商用吗？**
工具包本身是 PolyForm Noncommercial 许可：非商业使用免费，商业使用需事先获得作者授权。用它做出来的视频归你自己。见[许可](#许可)。

**能做竖屏（9:16）吗？**
目前不能。模板和全部安全区规则都按 1280×720 横屏设计。

**支持哪些语言？**
中文和英文。各有自己的语速模型、字幕预算与默认音色。两版成片都嵌在本页顶部；`examples/rag/` 里的过程文件是中文版的。

## 仓库结构

```
SKILL.md                  流程主文档：9 个阶段、四个确认点、质量标尺
reference/                写给主会话与 agent 的规范
  style-guide.md            安全区、调色板、字体、图元目录、版式规律
  motion-vocabulary.md      入场/强调/光效/离场/运镜的公式与帧数
  composition-and-light.md  主体尺寸三档、光跟主角、高光时刻编排、量化判据
  narration-storyboard.md   解说词写法、配音参数、分镜令牌、镜头设计模式表
  research-brief.md         研究员 prompt 与事实规则
  agent-build-rules.md      构建 agent 协议
  agent-qc-rules.md         QC agent 协议
  prompts.md                研究/构建/QC/修复/复验/终检六种 prompt 模板
  lessons.md                三部片子踩过的坑与根因
template/                 可编译的 Remotion 4 项目（用 scripts/new_project.sh 复制）
  src/common/               雾底、星点、点阵波、glitch、缓动、字幕、进度条、实拍层
  src/ui.tsx  src/fx.tsx    图元与调色板 / 光效·纵深·运镜图元
  src/overlay/              片头、章节卡、HUD、流程轨、片尾
  scripts/                  配音、分镜、still、测渲、前 N 秒样片、整片渲染、量化质检
  public/fonts/             四款字体 + OFL 许可
examples/rag/             样片全套过程文件与成片帧
examples/contrast/        6 组正例/反例帧对照（构图与光的标尺）
```

## 致谢

视觉风格的灵感与标尺来自抖音创作者 **@图灵宇宙** 的科普视频——黑底、白线条配紫色重点、超粗黑体大字这套语言是从他的片子里学来的。本项目所有画面均由代码原创绘制，不使用其任何帧、素材或工程文件；如有不妥请开 issue 告知。

## 原创性

- **画面全部代码绘制**，不使用任何现有视频的帧或片段；可选的实拍 B-roll 只允许免版权来源，并要求登记 MANIFEST（sha256 / 来源 URL / 许可 / 用途）。
- **事实有出处**：画面上出现的每个数字、年份、机构、英文术语都必须能在该片的调研文档里找到来源 URL，没核实的不上画面也不进配音。

## 许可

工具包本身：[PolyForm Noncommercial 1.0.0](LICENSE)——非商业使用免费，商业使用需事先获得作者授权。**用它做出来的视频归你自己**。
模板内四款字体（Noto Sans SC / Orbitron / Exo 2 / Audiowide）按 SIL OFL 1.1 单独授权，版权与许可全文见 [`template/public/fonts/LICENSE.md`](template/public/fonts/LICENSE.md)。
Remotion 自身对公司用户另有授权要求，见 [remotion.dev/license](https://remotion.dev/license)。

## 已知限制

- 中英文都支持（`lang: 'zh' | 'en'`），各有自己的语速、字幕块预算（每块 16 字 / 48 字符）与默认音色。两版成片都嵌在上方；`examples/rag/` 的过程文件是中文版的。只做这一种视觉风格，幕底二选一（`bg: 'stars' | 'dots'`），其他要换就改 `reference/style-guide.md` + `src/ui.tsx`。
- 不适用：复刻某条现有视频、真人口播、以实拍为主的片子。
- 解说词一旦配音定稿就不能改词（镜头代码里硬编码帧号），改词等于全片重对位。
- 并行构建对机器有要求：多个 agent 同时跑 Remotion bundle，建议预留 ≥5GB 磁盘；tmux pane 有上限，超过 12 个要分波派。

## Star History

<a href="https://www.star-history.com/?type=date&repos=Vincentwei1021%2Fanything2explainer">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=Vincentwei1021/anything2explainer&type=date&theme=dark&legend=top-left" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=Vincentwei1021/anything2explainer&type=date&legend=top-left" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=Vincentwei1021/anything2explainer&type=date&legend=top-left" />
 </picture>
</a>
