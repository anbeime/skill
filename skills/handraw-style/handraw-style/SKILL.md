---
name: handdraw-style-prompter
description: Turn a 001–368 hand-drawn and realistic style number and image theme into bilingual prompts, using model capability data to decide when core traits and a numbered reference image are required.
---

# Hand-drawn Style Prompter

This is the install entrypoint for the complete hand-drawn style package.
The package root contains the `images/` gallery and numbered reference assets;
the operational contract is [skills/handdraw-style-prompter/SKILL.md](skills/handdraw-style-prompter/SKILL.md).

Before handling a request, read that Skill file completely. Resolve every
gallery and reference-image path from this installed package root. Install this
repository at path `.` so the `images/` directory and the nested Skill are
kept together.

Read [package dependencies](DEPENDENCIES.md) before claiming that an installed
Skill can generate or render media. Bundled source/resources and separately
installed tools/services are distinct; never rely on the author's workstation.

Video production, narration and rendering are maintained in the separate `handraw-video` project. This package remains focused on static images, including article and video cover images.

## Post-generation sharing across all routes

Before parsing any new creative request, capture the user's original creative
message verbatim, including whitespace and line breaks, in `original-request.txt`
inside the local output directory. Follow-up selections and enlargement commands
inherit the original request for that creative task. Do not substitute generated
prompts, conversation history, environment context or credential messages.
After selecting the actual style and layout, record their canonical IDs. Public
sharing keeps the original request verbatim and appends only compact actual-ID
tags, such as `【画风：FA-013 】` and, only when used, `【图型：IG-038 】`.
Omit note headings, explanations and unused/unrecorded fields. Supply IDs with
`--style` / `--layout` (repeat for multiple IDs), or `--no-style` / `--no-layout`
when unused. Missing historical IDs mean unrecorded, not unused. Do not infer
IDs from generated images or include intermediate/expanded prompts.
The share destination is the website's work square: create a free `kind=work`
entry through `/studio/api/entries`, with actual style/layout asset references.
Do not substitute a forum post or return a forum topic URL as a work receipt.

After delivering verified generated images from any routed Skill, follow
[conversation sharing](skills/community-share/references/conversation-sharing.md)
to prepare a local draft and show the returned **分享到网站** Markdown link.
The link opens a loopback preview page with a real HTML publish button in local
Codex and Claude clients. Do not assume host directives render as buttons. When
a local service cannot run, offer an honest text trigger instead. Preparing a
draft and opening its preview never publish. Publish only after the user clicks
the page's publish button or explicitly requests sharing.
Resolve these resources from this installed package root, not a flattened
`.agents/skills` entry. Put the share action before the required gallery footer.

## Request routing index

When the user asks to illustrate an article, plan article illustrations, choose
insertion points, or write prompts for article images, read and invoke
[article-illustration-planner](skills/article-illustration-planner/SKILL.md)
before handling the request. Use the hand-drawn style rules in
[handdraw-style-prompter](skills/handdraw-style-prompter/SKILL.md) for style-number
resolution and prompt construction.

When the user asks to design a poster, generate poster prompts, or create structured poster prompts, read and invoke
[poster-prompt-generator](skills/poster-prompt-generator/SKILL.md), actively recommending cohesive style and theme color pairings from the visual style library (#001–#368) and theme color library (C-01–C-36).

When the user asks to design an article cover, video cover, generate cover prompts, create a WeChat official account cover, design an X/social cover for an article, or design a video cover from subtitle files/transcripts (例如“给文章做封面”、“文章封面设计”、“视频封面设计”、“视频封面”、“字幕做封面”、“公众号封面”、“X文章头图”), read and invoke
[article-cover-designer](skills/article-cover-designer/SKILL.md) before handling the request. It extracts a ~200-word summary, infers target audience, sets the business scenario (article or video cover), injects style (#001–#368) and theme color (C-01–C-36), and applies the fixed prompt instruction ("先设计隐喻再出图，主标题明显，小字少或者没有小字。 其他你帮我设计。"；若是视频封面或输入字幕文件，自动注入“视频封面设计，网感强，吸引人眼球”)。

When the user asks to blend, merge, or fuse two styles, generate a cross-media fusion prompt, or create a "character visual language × scene visual language" artwork (例如“【风格融合设计】”、“风格融合设计”、“风格融合”、“融合两种风格”、“角色与场景风格融合”、“双风格融合”、“跨媒介风格融合”), read and invoke
[style-fusion-prompter](skills/style-fusion-prompter/SKILL.md) before handling the request. It supports fusing two style numbers (#001–#368), or a style number with a realistic style, optionally injects layouts (SC-*/IG-*) and theme colors (C-01–C-36), and applies the strict dual visual language coexistence template.

When the user asks to design an IP character, build a Character Bible or IP Design Manual, generate standard IP cards (例如“IP形象设计”、“角色设计手册”、“设计三视图与周边”、“IP-01至IP-18卡片”), read and invoke
[ip-designer](skills/ip-designer/SKILL.md) before handling the request. It supports 5 layers (Strategy, Character, Visual, System, Commercial) across 18 standard cards (6-card basic, 10-card standard, or 18-card full edition).

When the user asks to manage, add, query, replace, or delete assets in the custom library (例如“添加到角色库”、“保存到道具库/场景库”、“替换角色基准图”、“修改资产名称/标签”、“初始化/挂载图库目录”、“查看图库清单”), read and invoke
[custom-asset-manager](skills/custom-asset-manager/SKILL.md) before handling the request. It manages the full lifecycle of custom character (CH-*), prop (PR-*), and scene (SCN-*) assets with zero Git conflicts.

When the user asks to plan a photo shoot, create a photography project, generate shot lists, design couple/wedding/family/portrait/cosplay photography plans, or draw card for a themed shoot (例如“拍摄企划”、“情侣照”、“婚纱照”、“写真”、“全家福”、“Cosplay拍摄”、“抽卡”、“8宫格”、“摄影分镜”), read and invoke
[couple-photo-orchestrator](skills/couple-photo-orchestrator/SKILL.md) before handling the request. It orchestrates the full pipeline from direction selection through Look design, scene micro-zones, pose-emotion planning, Share Card compilation, and 8-shot adaptive grid generation.

When the user asks to share creations, post to any forum category, publish images or bilingual prompts to the community/forum, login/bind website account, view published posts, edit/delete community topics, deploy or sync static gallery pages and assets to the cloud, or update the website (例如“发到论坛”、“社区发帖”、“手绘风发帖”、“发到创作交流/好用的工具/手绘skill/综合大厅”、“分享作品到社区”、“查看我的帖子”、“删除我的帖子”、“绑定手绘风账号”、“发布静态页面到社区”、“同步画廊”、“更新网站”、“部署静态页”), read and invoke
[community-share](skills/community-share/SKILL.md) before handling the request. It provides a dual publishing engine for both Discourse forum interaction (ID 4–9) and static gallery cloud deployment (syncing HTML, 365 styles, and WebP assets to tencent-vm / CDN with optional forum update announcements).

When the user asks to add or import a named or text-defined visual style to the style library, register positive visual traits, or generate representative sample tiles for a new style (例如“添加画风”、“录入风格”、“新增手绘风格”、“自定义风格入库”), read and invoke
[style-library-importer](skills/style-library-importer/SKILL.md) before handling the request. It processes style names and filtered positive traits, generates clean representative images, assigns the next style number, and updates metadata and contact sheets. 严格遵守特征提取铁律：严禁从示意图/参考图中解析提取任何具体人物、服装、动作、道具或场景地貌写入特征（traits），特征只保留纯粹的媒介、光影、色彩与艺术视觉语言。

When the user supplies an X/Twitter tweet link and asks to scrape, import, or convert tweet AI styles or `--sref` images into the numbered style library (例如“抓取推文画风”、“推文风格入库”、“导入Twitter风格”、“把这条推特录入到风格库”), read and invoke
[tweet-style-importer](skills/tweet-style-importer/SKILL.md) before handling the request. It automatically extracts full-resolution images, generates 4-grid reference and clean single tiles, configures mandatory reference passing, and rebuilds the library. 严格遵循内容解耦规范，严禁将推文原图的画面具体主体内容写入特征描述。

When the user asks to add a new visual layout or composition structure to the layout gallery (such as social cards, infographics, comic storyboards, IP cards, or e-commerce layouts; 例如“添加排版图型”、“录入新版式”、“导入排版”、“新增Layout”), read and invoke
[layout-library-importer](skills/layout-library-importer/SKILL.md) before handling the request. It losslessly converts the reference image to WebP, records category metadata, creates bilingual prompt files, and updates the layout gallery.

When the user asks to analyze the commercial application of a style, write or update style business guides, plan business use cases/products, or audit missing business documents (例如“商业应用”、“风格商业分析”、“商业指南”、“适合什么生意”、“商业落地”、“变现策划”、“business指南”、“补充商业文档”), read and invoke
[style-business-analyzer](skills/style-business-analyzer/SKILL.md) before handling the request. It authors gold-standard 5-module business guides in `business/{number}.md` with deep insights, product portfolios, and layout/color synergy.



## Default mode

Default to creating prompts only. Do not call an image-generation tool unless the user explicitly asks to generate, render, or preview an image.

### Automatic Style and Theme Color Recommendation Policy (默认智能推荐风格与主题色)

不管生成什么图片或提示词，**默认情况下如果用户没有指定风格和主题色，必须自动推荐最优的风格与主题色组合**，严禁因用户缺少编号而中断或拒绝生成：

> [!IMPORTANT]
> **【核心准则：每次由 AI 实时动态判断，严禁写死/机械套用】**
> - **实时动态研判**：严禁在记忆、规则或提示词中维护任何“主题关键词 -> 固定风格编号/颜色编号”的静态死板映射（例如严禁一见节气/传统就推 268、一见自然就推 266、一见科技就推 011/054、一见生活就推 018）。
> - **全库开放式匹配**：每次推荐必须由 AI 结合当前用户具体主题的深层语境、精神内核、视觉隐喻与画面构图，在全库 365 种视觉风格（#001–#368）与 36 种经典主题色（C-01–C-36）中进行**实时、开放式的审美推理与动态搭配**。
> - **激发全库多样性**：同一个主题在不同设计视角下具备多维的美学可能性（如“菜园”既可以是水墨写意、也可以是田园木刻版画、粗粒油画棒、或包豪斯几何构成）。每次推荐都应根据具体切入点构思，充分展现全库 368 种画风与 36 种色彩的丰富生命力。
> - **美学理由具象化**：AI 给出的美学推荐理由必须紧扣当前主题的视觉隐喻和画面构图，说明为什么该画风的笔触/质感与该色彩的情绪能完美传达这一主题，杜绝套话。

1. **风格与主题色均未指定**：根据用户输入的主题语义、情感基调、受众与使用场景，由 AI 实时动态从 365 种视觉风格与 36 种经典单色库中推荐 1 组契合度最高的【风格编号 (#001–#368) + 主题色编号 (C-01–C-36)】组合。主题色数量不设死限，依据画面层次灵活决定单色统领、双色搭配（主色+点缀色）或三色调和，简述 1 句具象化美学推荐理由，并直接输出完整生图提示词（或执行出图）。
2. **仅指定风格，未指定主题色**：严格保留用户指定的风格，根据该风格与画面主题，由 AI 实时动态推荐最协调的【主题色 (C-01–C-36)】搭配（可为单色或多色组合）。
3. **仅指定主题色，未指定风格**：严格保留用户指定的主题色，根据色彩调性与画面主题，由 AI 实时动态推荐 1 款最契合的【视觉风格 (#001–#368)】搭配。
4. **两者皆指定**：完全遵照用户指定的内容输出。

## Style activation policy

Use the same capability decision for prompt-only and explicit image-generation requests. Resolve the selected/current model (or model family) against `skills/handdraw-style-prompter/references/model_capabilities.json`; if no model is specified, default to `gpt-image-2` (the calibrated baseline model of this library). Only use the default unknown capability fallback when the user explicitly requests an uncalibrated third-party model. The decision uses the indexed author name plus the generated style name and is not based on the author's fame or life status.

- `name_activation=strong`: use only the indexed author name, generated style name, and theme. (Specifically for styles like #042 Beatrix Potter, #011 David Shrigley, #269 Socialist Realist Propaganda Poster, and other strong-activation styles: the model understands the aesthetic natively; output only the reference author and style name, and STRICTLY DO NOT output core traits, local image file paths, or reference-isolation blocks.)
- Otherwise, include every available positive core trait with the author/style name and theme.
- If name plus traits is not strongly activated, also require the configured reference asset. For explicit generation, pass it through `referenced_image_paths`. In `pure-image` prompt-only output, write the local asset path and reference-isolation instruction inside both prompts for the user to upload manually. In `graphic-text` prompt-only output, do not place a path, upload instruction, or isolation block inside either copyable prompt; show the resolved reference image to the user outside the prompts instead. Assets live under the installed package root in numbered 200-style buckets: for example, #217 uses `images/individual/201-400/217_grid.webp`.
- If no positive core trait exists and name is not strongly activated, use the author/style name, theme, and reference image.
- If the model identifier or its capability entry is unavailable, treat it as `unknown`, include any available positive traits, and require the image as the safe fallback.
- Use `python skills/handdraw-style-prompter/scripts/resolve_reference.py --model <model> --style <number>` when a deterministic decision check is useful. The script prints JSON and never guesses an unknown model's capability.
- The resolver reports `activation_source` as `name+style`, `name+style+traits`, `name+style+traits+reference-image`, or `name+style+reference-image`, plus filtered `prompt_traits` and the local `reference_path` when required.

- Resolve the style number to its configured reference asset relative to the installed package root. The normal fallback is `images/individual/{bucket}/{number}.webp` (for example, `048` maps to `images/individual/001-200/048.webp`); a matching `{number}_grid.webp` in the same bucket takes priority.
- When a reference image is required, inject the following reference-isolation block into `pure-image` prompt-only output and every actual image-generation prompt. Do not inject it into a `graphic-text` copyable prompt; the actual image-generation prompt still receives it together with the attached asset.

  Chinese: `所附图片仅用于参考画风。只提取参考图的风格特征，例如线条、笔触、媒介、材质、色彩倾向和整体视觉语言；不要使用、复制或延续参考图中的任何主体、人物、动物、服装、道具、动作、姿态、场景、背景、构图、布局、文字或故事。最终画面内容完全以用户提供的主题为准。`

  English: `Use the attached image only as a style reference. Extract only its stylistic qualities, such as linework, brushwork, medium, material texture, color tendencies, and overall visual language. Do not use, copy, or carry over any subject, person, animal, clothing, prop, action, pose, setting, background, composition, layout, text, or story from the reference image. The user's written theme is the sole source for the image content.`

- The user's theme is the sole source for subjects and narrative; the reference image must never override or add content to the theme.
- Include only positive visible traits; filter clauses containing `避免`, `不要`, `不准`, or `禁止` and do not copy the traits field mechanically.
- If the numbered image is missing or cannot be passed, report that limitation and provide the normal text prompts; never invent or substitute a reference image.
- After generation, identify whether the numbered reference image was used. If used, identify its number. Do not imply generation when the user requested prompts only.

## Session initialization

On the first turn in the current Codex task/thread where this Skill is invoked, perform both initialization actions before handling the user's request. This applies to **任何首次请求**, including opening the gallery, browsing the index, requesting prompts, or requesting image generation:

1. If this task has not already displayed the gallery, dynamically resolve the absolute `file://` URI to `skills/handdraw-style-prompter/gallery/index.html` based on the current workspace or installed package root, and call `mcp__codex_app__open_in_codex` in a browser tab with `target.type="browser"` and that URL. Never open `gallery/index.html` as `target.type="file"`, in an editor, or as a file preview.
2. Include the exact standalone status line `当前处于纯图模式，可切换为图文模式。` in the same final reply, even when the request produces no prompt.
3. Continue with the user's request after the browser call; opening the gallery must not block prompt generation or an explicitly requested image-generation follow-up. If the same first reply would also add the pure-image mode note, show this status line only once.
4. Do not repeat the browser call or this first-session status notice on later turns in the same task/thread. Use the conversation context (not a persistent state file) to determine whether initialization already happened.
5. If the browser call is unavailable or fails, provide the dynamically resolved local `file://` fallback link, then continue normally.

This initialization applies only when this Skill is invoked for the first time in a task/thread; unrelated conversations must not open the gallery.

## Inputs

For style-only work, if the style number (`001`–`368`) is omitted, automatically recommend an optimal style and theme color combination based on theme semantics. For layout work, require a layout ID (`SC-001` or `IG-001`); if style and/or theme color are omitted, automatically recommend harmonious ones. Accept optional theme color (`C-01`–`C-36` or color name), aspect ratio, subject constraints, text requirements, and a mode. When the user requests a prompt (e.g. specifying a style and/or layout) without providing a theme, do NOT pause or halt to ask for a theme—immediately output the complete prompt with a clear placeholder (such as `【请在此输入画面主题，或在生图模型中垫入你的照片】` / `[Enter theme here, or attach your photo in the image AI]`). If a supplied number, layout ID, or color ID is invalid, ask the user to choose a valid indexed value; do not invent one. Do not add an aspect ratio when none was supplied.

Users can browse `skills/handdraw-style-prompter/gallery/index.html` for numbered style contact sheets, `skills/handdraw-style-prompter/gallery/layouts.html` for layout thumbnails, and `skills/handdraw-style-prompter/gallery/colors.html` for classic monochrome theme colors. The authoritative style content is `styles_200_reorganized.md`; `skills/handdraw-style-prompter/references/styles.json` is a generated index and must be refreshed with `python skills/handdraw-style-prompter/scripts/build_library.py` after Markdown changes. Layout metadata is `skills/handdraw-style-prompter/references/layouts.json`; each entry's bilingual prompt file under `skills/handdraw-style-prompter/references/layouts/` is the authoritative layout content and the layout gallery is refreshed with `python skills/handdraw-style-prompter/scripts/build_layout_gallery.py`. Monochrome color metadata is `skills/handdraw-style-prompter/references/colors.json` and refreshed with `python skills/handdraw-style-prompter/scripts/build_color_gallery.py`.

## Layout workflows

- A layout ID selects composition and text structure, not illustration style. Use its prompt file verbatim in the selected output language, then append the user's theme as the only source of subject matter and copy.
- **排版图型的两大架构分类 (Dual Architecture of Layout Patterns)**：
  本库全部 170 种排版图型在底层设计与执行机制上明确划分为两大类：
  1. **确定性静态排版（纯文本直接拼接型 · Static Templates）**：
     - 包括绝大多数常规图型（如 `SC-001`~`SC-023` 社媒卡、`IG-001`~`IG-035` 信息图、`SB-001`~`SB-071` 漫画分镜、`IP-001`~`IP-013` IP设计、`EC-001`~`EC-024` 电商）。
     - 构图拓扑关系单一固定，生图模型能直白无误地理解。处理方式为拿来即用，直接提取其 prompt 模板并拼接指定画风与主题输出。
  2. **高维动态解析型排版（Skill 级动态解析决策型 · Generative Frameworks）**：
     - 代表图型为 `SC-021`（自适应双拼照片转译社媒卡）。
     - 该类图型不是单一路线的固定线框，而是高度抽象的“跨媒介视觉构图与空间语法系统”。生图模型不具备自主解析多选菜单的能力，若直接平铺备选清单，模型会因语义冲突退化为机械照搬原片全景背景。
     - **执行机制**：必须由 AI 助手充当设计总监（Art Director）进行前置解析与动态决策：
       - **比例驱动切分原则（严禁死板切分，完全由目标画幅比例决定）**：竖版画幅（如 3:4、9:16、1:2 等）默认采用上下 1:1 纵向堆叠双拼（上方摄影/下方手绘），顺应手机端自上而下的视觉动势与故事自然向下延展；横版画幅（如 16:9、4:3、5:2、21:9 等）默认采用左右 1:1 横向并排双拼（左侧摄影/右侧手绘），呈现独立艺术杂志跨页质感；方版画幅（1:1）自适应切分或服从用户显式指定；
       - **七大核心转译类型体系（Type 01 ~ Type 07）**：若用户未显式指定构图类型，由 AI 结合画面主题推荐最契合的 1 种类型（或按顺序轮替抽卡），并为选定的唯一类型生成单义、排他的执行提示词：
         * `【类型 01 · 视线锚点跨界续绘型 (Visual Anchor Continuation)】`：单一核心动态锚点（水/路/光/手势）跨越中缝边界流淌进入暖象牙纸手绘区域，在下方衍生绘本互动故事与极简黑线小人；
         * `【类型 02 · 撕纸裂变第二世界型 (Torn-Paper Second World)】`：不规则手工物理撕纸毛边接缝，现实穿透撕纸后物理规则超现实突变（水变布匹/光可手捧/影子成阶梯），暖象牙纸与克制拼贴；
         * `【类型 03 · 越界破框型 (Boundary Break / Out-of-Bounds)】`：几何色块/容器承托，主体关键部位（头/手/枝叶）突破色块边缘伸出，形成空间穿透感；
         * `【类型 04 · 微缩浮岛型 (Miniature Diorama / Floating Island)】`：主体微缩为 10%–25% 纸面小景，单抹色带或微基座承托，四周大片静谧空旷留白；
         * `【类型 05 · 记忆图谱平铺型 (Memory Knolling / Fragment Collage)】`：居中放置手绘主体，留白中错落平铺 3–6 枚带 NO. 编号的原图记忆特征贴纸；
         * `【类型 06 · 经典悬浮落地型 (Suspended / Grounded Hero)】`：主体尺度适中（占 40%–55%），底部仅用一条极简手绘地面摩擦线提示空间支撑；
         * `【类型 07 · 正负形咬合型 (Gestalt Positive-Negative Interlock)】`：主体高度提炼为几何剪影，与背景正负形相互转换咬合；
       - **背景强力净化指令**：坚决剔除原片石墙、马路、树木等环境杂质，确保艺术转译侧四周 40%–80% 纯净负空间与呼吸边距；
       - **强制交互点选输出规范**：每当使用或输出 SC-021 提示词时，在提示词文本末尾，**必须固定附带 7 大可选类型索引清单**（标明当前已采用类型，并提示用户回复编号如“换成 02”即可一键换装），赋予用户随时点选调整的机会。
- **传图与改图规则（无需强制传图，完全支持用户传图与改图）**：无论使用 `SC-021`（自适应双拼照片转译社媒卡）还是其他任何风格/图型，用户传图均属**可选行为**：
  - **用户未传图时**：完全支持纯文本直出。AI 助手直接将排版规则与指定风格特征拼接为完整提示词（若未提供主题则提供直观占位符），绝不阻断对话或强制要求用户必须传图，由生图模型原生自主生成写实画面与风格转译。
  - **用户传图 / 改图时（写实改手绘 / 垫图转风格）**：完全支持！当用户上传照片或参考图要求“改图”、“改风格”、“转手绘”时，为了防止生图模型在写实照片表面机械叠加滤镜，提示词中**必须使用以下固定转绘重绘指令**：
    `【请只提取人物的五官特征和姿态，场景轮廓，在画风上严格按 选择的风格重新画，不要在原照片上加质感。】`
    （英文对应：`[Extract only the character's facial features and posture, and the scene contours. Strictly redraw from scratch according to the selected style; do not add texture or filters onto the original photo.]`）
    AI 助手提取参考图的核心特征（人物外貌特征、姿态、服装轮廓、场景概貌）作为主题描述，并无条件附带上述固定指令，强制生图模型在手绘维度从零重新绘制，彻底杜绝写实滤镜与照片微表面保留。
  - 核心原则在于：最终的像素级视觉绘制与画风转译始终由生图模型（如 GPT Image、Midjourney、Flux 等）原生完成。
- When a layout ID is selected, automatically use graphic-text mode even if the user did not name a mode (except for E-commerce layouts `EC-*`: e-commerce layouts do not append the generic graphic-text suffix, and do not stitch a visual style unless explicitly requested by the user). For standard layouts, the layout prompt and the fixed graphic-text suffix are additive (stacked): append the fixed generic graphic-text suffix verbatim at the end of the prompt to combine concrete layout rules with graphic-text semantic guidance. In layout requests, never append the pure-image mode notice `当前处于纯图模式，可切换为图文模式。`, and never include reference-image file paths or upload instructions inside the copyable prompt.
- If the user also supplies a style number, combine the selected style's author/style label, permitted positive traits, and reference-image policy with the layout prompt (for e-commerce layouts, only stitch style if the user explicitly specified a style number). A style reference image may influence only rendering style; it must not override the selected layout, text structure, or theme.
- Return a single complete layout-combination prompt in the language of the user's theme. Chinese characters select Chinese; otherwise use English. Treat mixed input as Chinese. Existing style-only requests retain their normal bilingual output.
- The layout gallery is browse-only: it has no prompt input form. It shows a numbered thumbnail, opens a large preview on click, and copies the canonical Chinese layout prompt on request.

## Prompt modes

Default to `pure-image`. Accept `纯图模式` / `图文模式` in conversation and `--mode pure-image|graphic-text` in the CLI.

- `pure-image`: preserve the current prompt workflow. After the normal reply, add the small note `当前处于纯图模式，可切换为图文模式。`.
- `graphic-text`: preserve the user's theme exactly after `主题：` / `Theme:`. Do not expand, paraphrase, interpret, or add scene elements, characters, actions, metaphors, emotional explanations, or theme commentary. Append the following text verbatim to the end of both the Chinese and English prompts. Do not translate, trim, normalize, rewrite, label, or reorder any character in it. The exact final prompt, including this suffix, is sent unchanged to the image AI when generation is requested. When a reference asset is required, display that image outside the copyable prompts; do not expose its local path, upload instruction, or reference-isolation block in either prompt.

  `【如果主题直白包含画面元素那就按主题出图，文案由你来升华，但是不要直接描述画面。 如果主题比较概念化，那么文案和主题尽量保持一致，如果文案较长由你提炼，由你先设计画面隐喻（人类和非人类都行）再出图   。    文字参与构图，图文一体】`

## Output

For a valid request, return these parts:

0. (若触发智能推荐) 推荐组合说明：
   - 标注推荐的风格与主题色（例如：`💡 智能推荐组合：风格 #{编号} · {generation_name} + 主题色 {id} · {name_zh} ({name_en})`）；
   - 给出 1 句简明美学推荐理由；
   - 提示用户若有偏好的其他编号可随时说明替换。
1. Selected style: number and generated style name. Include core traits inside the two copyable prompts when the resolved activation policy requires them; do not create a separate core-visual-traits section.
2. Chinese prompt: begin the copyable prompt itself with `风格名称：{generation_name}。`（重要规则：生成的提示词内容内部严禁包含任何编号，包括风格编号如 `#018`、图型编号如 `SC-021` / `SC-001`、色彩编号如 `C-01` 等，直接使用自然语言名称，避免生图模型误将编号代码作为文字绘制到画面中）；when a theme color is applied, include `主题色：{name_zh}（{name_en}）。`（不含色彩编号）；describe only the user's theme and constraints explicitly provided by the user, and always include the indexed author/style name as a short `参考作者/风格名称` label. When required, append filtered positive traits as `核心风格特征：...`；当用户要求改图/垫图转画风时，在画面要求后必须追加：`【请只提取人物的五官特征和姿态，场景轮廓，在画风上严格按 选择的风格重新画，不要在原照片上加质感。】`（其中“选择的风格”可根据所选风格名称具体实例化）。In `pure-image` mode, append a required reference image's local path and reference-isolation instruction. In `graphic-text` mode, preserve the theme verbatim, append the exact fixed suffix from Prompt modes at the end, and show any required reference image outside the prompt instead. Traits describe rendering style only and must not replace or alter the user's subjects, actions, setting, or story.
3. English prompt: begin the copyable prompt itself with `Style name: {generation_name}.` (Strictly omit any numeric or alphanumeric IDs such as `#018`, `SC-021`, or `C-01` from the prompt text); when a theme color is applied, include `Theme color: {name_en}.`; describe only the same theme and user-provided constraints, and always include the indexed author/style name as `Reference author/style name`. When required, append the same traits as `Core style traits: ...`; when the user requests an image redraw/style transfer from an uploaded photo, append: `[Extract only the character's facial features and posture, and the scene contours. Strictly redraw from scratch according to the selected style; do not add texture or filters onto the original photo.]` (where "selected style" may be replaced by the chosen style's English name). In `pure-image` mode, append a required reference image's local path and reference-isolation instruction. In `graphic-text` mode, preserve the theme verbatim, append the exact fixed Chinese suffix at the end, and show any required reference image outside the prompt instead. Do not append generic composition advice, quality claims, negative prompts, or the fixed style anchor.
4. A brief note: the prompt can be pasted into any image AI; generation is controlled by that AI.

Do not invent visual traits, extra style descriptions, generic quality/composition language, or default avoid-list wording. Include each entry's original reference author/style name from the index in both prompts as requested; this is an index label, not a claim about the person or an instruction to imitate them. Never use fame or life status as a proxy for model capability.

In `pure-image` mode, describe only concrete visible content implied by the theme—subjects, actions, objects, environment, and mood when needed. In `graphic-text` mode, use the user's theme verbatim and leave all semantic expansion to the fixed suffix. In both modes, leave composition, layout, visual richness, quality, and rendering decisions to the image AI unless a layout ID was explicitly selected. Respect a user-specified text requirement but do not invent copy.

## Utilities

- From the installed package root, rebuild the derived index and gallery: `python skills/handdraw-style-prompter/scripts/build_library.py`
- Rebuild the layout gallery: `python skills/handdraw-style-prompter/scripts/build_layout_gallery.py`
- Rebuild the color gallery: `python skills/handdraw-style-prompter/scripts/build_color_gallery.py`
- Split contact sheets into numbered single images: `python skills/handdraw-style-prompter/scripts/split_contact_sheets.py`
- Validate all source/index/gallery invariants: `python skills/handdraw-style-prompter/scripts/validate_library.py`
- Produce a deterministic CLI prompt draft: `python skills/handdraw-style-prompter/scripts/prompt_style.py --style 18 --theme "秋天的第一杯奶茶"`
- Produce a layout-combination draft: `python skills/handdraw-style-prompter/scripts/prompt_style.py --layout SC-001 --style 18 --theme "秋天的第一杯奶茶"`
- Produce a color-combination draft: `python skills/handdraw-style-prompter/scripts/prompt_style.py --style 18 --color C-01 --theme "秋天的第一杯奶茶"`
- Resolve image-reference policy: `python skills/handdraw-style-prompter/scripts/resolve_reference.py --model <model> --style 18`

The CLI is a convenience check. For normal conversational use, write natural bilingual prompts rather than echoing its template mechanically.


## Personal resources and community collections

When the user asks for 我的画风、我的图型、我的收藏、同步收藏、个人画风/图型 or importing a community resource package, read [personal-library](skills/personal-library/SKILL.md). Official entries remain unchanged; user-created and community-acquired entries live in the separate user library. Never upload personal resources without an explicit sharing request.
