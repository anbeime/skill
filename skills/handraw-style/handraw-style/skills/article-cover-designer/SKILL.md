---
name: article-cover-designer
description: 极简高效的文章与视频封面设计技能。根据输入文章或视频字幕文件自动提炼200字核心摘要、推算受众群体、默认输出微信公众号标准 2.35:1 超宽画幅封面（兼顾X 5:2与安全留白），或按需匹配小红书(3:4)、B站/YouTube/短视频(16:9/9:16)场景；深度协同全库 365 种视觉风格与36种经典配色；视频封面模式自动注入“视频封面设计，网感强，吸引人眼球”，并结合“先设计隐喻再出图，主标题明显，小字少或者没有小字”核心指令，一键输出高质量结构化封面生图提示词。
---

# Article Cover Designer (文章与视频封面设计器)

极简高效地将文章或视频字幕转换为高审美、高转化、高吸睛度的封面生图提示词。

---

## 核心设计原则

彻底摒弃冗长复杂的理论陈述，只保留生图模型（如 GPT Image 2/2.5、Midjourney 等）最需要的**核心业务与设计字段**：

1. **核心摘要**：提炼 **200 字左右** 的核心论点、剧情主线或背景逻辑；
2. **受众推算**：根据内容推算出 **精准目标受众**；
3. **业务场景与默认画幅**：
   - **文章封面（默认场景）**：**默认比例严格锁定为 `2.35:1` 超宽画幅**（微信公众号官方头条封面标准 `2.35:1` / `900×383`，同时完美兼容 X 文章封面 `5:2` / `2.5:1`）；
     - **安全区防裁切准则**：所有视觉隐喻核心与 3D/艺术大标题必须严格聚集在中央水平安全区内，上下两端各留出至少 12% 的呼吸感与安全空白，坚决杜绝因平台信息流自动裁剪导致削顶或削底；
     - 仅当用户明确说明为小红书时，才切换为小红书图文封面（`3:4`）；
   - **视频封面**：当用户明确要求做**视频封面/缩略图**，或输入**字幕文件**（`.srt`、`.vtt`、字幕逐字稿/时间轴文本）时，自动识别为 **`视频封面`**（横屏推荐 `16:9`，竖屏短视频推荐 `9:16` 或 `3:4`）；
4. **风格与配色注入**：从全库 **365 种视觉风格**（`#001`–`#368`）与 **36 种经典配色**（`C-01`–`C-36`）中匹配或由 AI 推荐；
5. **固定设计指令**：
   - **普通文章封面**：注入 **“先设计隐喻再出图，主标题明显，小字少或者没有小字。 其他你帮我设计。”** 让模型原生自主构图与排版；
   - **视频封面 / 字幕输入**：必须在提示词中注入 **“视频封面设计，网感强，吸引人眼球。先设计隐喻再出图，主标题明显，小字少或者没有小字。 其他你帮我设计。”** 强化视觉冲击力与点击吸睛度。

---

## 工作流与操作步骤

### 输入识别与场景判定
- **文章输入**：用户提供文章文本、Markdown 内容或本地文章路径（如 `D:\path\to\article.md`）-> 启用【文章封面模式】，**默认画幅为 2.35:1**；
- **视频 / 字幕输入**：用户明确说明是“视频封面/缩略图/B站封面/YouTube封面/短视频封面”，或提供字幕文件（如 `.srt`, `.vtt`, `.txt` 字幕, 包含时间轴的台词逐字稿）-> **自动判定为【视频封面模式】**（默认画幅 16:9）；
- （可选）指定风格编号（`001`–`368`）及主题色编号（`C-01`–`C-36`）。若未指定，由 AI 结合内容智能推荐最优搭配。

### 执行流程
1. **提炼 200 字核心摘要**：概括核心事件/核心观点、因果逻辑与认知启示（若是字幕，提取视频核心主题与亮点）；
2. **推算受众画像**：结合知识深度与诉求，输出 1–2 句话精准受众定位；
3. **确定业务场景与画幅**：
   - **公众号文章封面（默认）**：**默认画幅严格设定为 `2.35:1`**（超宽画幅，适配微信头条与 X 5:2，上下预留安全留白）；
   - **小红书图文封面**：`3:4`；
   - **视频封面（横屏，如 B站/YouTube/视频号横屏）**：`16:9`；
   - **视频封面（竖屏，如 抖音/快手/小红书/视频号竖屏）**：`9:16` 或 `3:4`；
4. **注入风格与色彩**：输出推荐的具体风格（如 `#018 · Minimal Deadpan Dialogue Cartoon`）与主题色（如 `C-01 经典蓝`）及推荐理由；
5. **组装标准提示词**：按照规定模板直接输出中英文提示词（若是视频/字幕场景，严格包含 **“视频封面设计，网感强，吸引人眼球”**）。

---

## 标准提示词输出模板

### 模式 A：文章封面（默认：2.35:1 超宽画幅）

#### 中文提示词：
```text
文章摘要：{200字左右的核心摘要}。
受众：{推算出的核心受众}
业务场景：公众号文章封面（默认 2.35:1 超宽画幅，兼容 X 文章 5:2）。

画幅与构图规范：超宽画幅比例 2.35:1。所有视觉核心隐喻与主标题大字必须居中收拢在中央水平安全带内，上下两端保持充足的安全留白，严禁贴边，防止平台信息流展示时被裁切。
风格：{风格编号及名称，如 #018 Minimal Deadpan Dialogue Cartoon}
主题色：{主题色编号及名称，如 C-01 经典蓝}
先设计隐喻再出图，主标题明显，小字少或者没有小字。 其他你帮我设计。

请设计文章封面
```

#### English Prompt：
```text
Article Summary: {200-word concise summary in English}.
Audience: {Inferred target audience in English}.
Scenario: WeChat Official Account Article Cover (Default 2.35:1 ultra-wide aspect ratio, compatible with X Article 5:2).

Framing & Layout Specs: 2.35:1 ultra-wide aspect ratio. Keep all core visual metaphors and bold main title strictly centered within the horizontal safe zone, with ample safety margins on top and bottom to prevent cropping.
Style: {Style ID and Name}
Theme Color: {Theme Color ID and Name}
Design a visual metaphor first, then generate the image. Ensure the main title is bold and prominent, with few or no small text. Pick the rest of the design for me.

Please design the article cover.
```

---

### 模式 B：视频封面 / 字幕输入（视频封面或字幕文件触发）

> **生效条件**：
> 1. 用户明确说明需要“视频封面”、“视频缩略图”、“B站封面”、“YouTube封面”、“短视频封面”；
> 2. 或用户输入为字幕文件（`.srt`、`.vtt`、包含时间轴的逐字稿字幕）。
> 
> **提示词强制要求**：提示词中必须写：**视频封面设计，网感强，吸引人眼球**。

#### 中文提示词：
```text
视频摘要：{根据视频字幕或内容提炼的200字核心摘要}。
受众：{推算出的核心受众}
业务场景：视频封面 (16:9) / 竖屏短视频封面 (9:16 或 3:4)。

风格：{风格编号及名称，如 #018 Minimal Deadpan Dialogue Cartoon}
主题色：{主题色编号及名称，如 C-01 经典蓝}
视频封面设计，网感强，吸引人眼球。先设计隐喻再出图，主标题明显，小字少或者没有小字。 其他你帮我设计。

请设计视频封面
```

#### English Prompt：
```text
Video Summary: {200-word concise summary extracted from subtitles/video content in English}.
Audience: {Inferred target audience in English}.
Scenario: {Video Cover / Thumbnail (16:9) / Short Video Cover (9:16 or 3:4)}.

Style: {Style ID and Name}
Theme Color: {Theme Color ID and Name}
Video cover design, high clickability and viral internet appeal, visually captivating and eye-catching. Design a visual metaphor first, then generate the image. Ensure the main title is bold and prominent, with few or no small text. Pick the rest of the design for me.

Please design the video cover.
```

---

## 生图引擎适配与后处理规范 (Post-Processing SOP)

若调用的生图底层引擎（如 DALL-E 3、FPBrowser2API、ChatGPT 图像原生接口）仅支持固定的预设尺寸（如 `1792×1024` 或 `1344×768` 等 16:9 尺寸）：
1. **提示词强约束**：必须在 Prompt 中显式声明 `2.35:1 居中水平带安全区构图，上下留白`；
2. **自动化 2.35:1 后处理裁剪**：脚本/自动化工具下载原图后，默认自动按照中心轴居中裁剪为精确的 **2.35:1**（例如将 `1659×948` 居中裁切为 `1659×705`，或输出标准 `1672×711` / `2350×1000`），再落盘交付给文章发布工作流，确保微信公众平台与 X 平台读取时绝对不被意外裁切。

---

## 交付与后续操作引导 (CTA)

输出提示词后，主动出具极简双轨引导：

```markdown
---

💡 **封面设计方案已完成！您可以选择：**
1. **【方式 A · 自主生图】**：复制上方提示词，前往您常用的生图工具出图；
2. **【方式 B · 全自动生图】**：直接对我说 **“全自动出图”**，我将调用生图工具为您全自动生成默认 2.35:1 规范封面图片！
```
