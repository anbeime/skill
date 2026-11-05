---
name: handraw-skill
display_name: 手绘skill
display_name_en: Handraw Style Skill
description: 内置300多个画风，图型，主题色。支持纯图模式，图文模式，可以给文章做封面，批量制作插图。可以批量制作海报，漫画，小红书组图。信息图，ip设计稿，电商图甚至真人摄影都随意拿捏。
description_zh: 内置300多个画风，图型，主题色。支持纯图模式，图文模式，可以给文章做封面，批量制作插图。可以批量制作海报，漫画，小红书组图。信息图，ip设计稿，电商图甚至真人摄影都随意拿捏。
description_en: Built-in 300+ styles, layouts, and theme colors. Supports pure image mode, text-and-image mode, article covers, batch illustrations, posters, comics, Xiaohongshu card sets, infographics, IP designs, e-commerce visuals, and realistic photography.
version: 1.0.3
author: "牙仔"
examples_zh:
  - "风格：FA-013 主题：猫咪在咖啡馆喝咖啡"
  - "图型：SC-008 风格：FB-020 配色：C-15 主题：秋日桂花野餐"
  - "写实摄影 FI-001 主题：雨夜赛博朋克街头"
examples_en:
  - "Style: FA-013 Theme: A cat drinking coffee in a cafe"
  - "Layout: SC-008 Style: FB-020 Color: C-15 Theme: Autumn picnic under osmanthus tree"
  - "Realistic style FI-001 Theme: Cyberpunk street on a rainy night"
---

# Hand-drawn Style Prompter

Default to creating prompts only. Do not call an image-generation tool unless the user explicitly asks to generate, render, or preview an image.

## Conversation share action after image delivery

Before parsing a creative request, preserve the user's original creative message verbatim. After image generation, prepare a share action to the website's work square. Share the original user instruction, appending only the canonical style and layout IDs actually used as compact tags after the original instruction, e.g. `【画风：FA-013 】` and `【图型：IG-038 】`. Omit unused categories, note headings, and explanations; never invent an ID or add intermediate design fields. Prompt-only responses and reference images do not get this action.

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

Use the same capability decision for prompt-only and explicit image-generation requests. Resolve the selected/current model (or model family) against `references/model_capabilities.json`; if no model is specified, default to `gpt-image-2` (the calibrated baseline model of this library). Only use the default unknown capability fallback when the user explicitly requests an uncalibrated third-party model. The decision uses the indexed author name plus the generated style name and is not based on the author's fame or life status.

- `name_activation=strong`: use only the indexed author name, generated style name, and theme. (Specifically for styles like #042 Beatrix Potter, #011 David Shrigley, #269 Socialist Realist Propaganda Poster, and other strong-activation styles: the model understands the aesthetic natively; output only the reference author and style name, and STRICTLY DO NOT output core traits or reference-isolation blocks.)
- Otherwise, compile and output every available positive core trait with the author/style name and theme directly from `references/styles.json`.
- If name plus traits is not strongly activated, also require the configured reference asset. For explicit generation, pass it through `referenced_image_paths`. In `pure-image` prompt-only output, write the local asset path and reference-isolation instruction inside both prompts for the user to upload manually ("Use the attached image only as a style reference. The user's written theme is the sole source for the image content."). In `graphic-text` prompt-only output, do not place a path, upload instruction, or isolation block inside either copyable prompt; show the resolved reference image to the user outside the prompts instead. Assets live under the installed package root in categorized folders: for example, FF-001 uses `images/individual/FF/FF-001_grid.webp`, single-image styles use `images/individual/{category}/{number}.webp`.
- If no positive core trait exists and name is not strongly activated, use the author/style name, theme, and reference image.
- Use `python scripts/resolve_reference.py --model <model> --style <number>` when a deterministic decision check is useful. The script prints JSON and never guesses an unknown model's capability.
- When a reference image or photo is attached, inject the following reference-isolation block into the prompt:

  Chinese: `所附图片仅用于参考画风。只提取参考图的风格特征，例如线条、笔触、媒介、材质、色彩倾向和整体视觉语言；不要使用、复制或延续参考图中的任何主体、人物、动物、服装、道具、动作、姿态、场景、背景、构图、布局、文字或故事。最终画面内容完全以用户提供的主题为准。`

  English: `Use the attached image only as a style reference. Extract only its stylistic qualities, such as linework, brushwork, medium, material texture, color tendencies, and overall visual language. Do not use, copy, or carry over any subject, person, animal, clothing, prop, action, pose, setting, background, composition, layout, text, or story from the reference image. The user's written theme is the sole source for the image content.`

- The user's theme is the sole source for subjects and narrative; the reference image must never override or add content to the theme.
- Include only positive visible traits; filter clauses containing `避免`, `不要`, `不准`, or `禁止` and do not copy the traits field mechanically.
- If the numbered image is missing or cannot be passed, report that limitation and provide the normal text prompts; never invent or substitute a reference image.
- After generation, identify whether the numbered reference image was used. If used, identify its number. Do not imply generation when the user requested prompts only.

## Session initialization

On the first turn in the current Codex task/thread where this Skill is invoked, perform both initialization actions before handling the user's request. This applies to **任何首次请求**, including opening the gallery, browsing the index, requesting prompts, or requesting image generation:

1. If this task has not already displayed the gallery, dynamically resolve the absolute `file://` URI to `gallery/index.html` based on this Skill's directory in the current environment, and call `mcp__codex_app__open_in_codex` in a browser tab with `target.type="browser"` and that URL. Never open `gallery/index.html` as `target.type="file"`, in an editor, or as a file preview.
2. Include the exact standalone status line `当前处于纯图模式，可切换为图文模式。` in the same final reply, even when the request produces no prompt.
3. Continue with the user's request after the browser call; opening the gallery must not block prompt generation or an explicitly requested image-generation follow-up. If the same first reply would also add the pure-image mode note, show this status line only once.
4. Do not repeat the browser call or this first-session status notice on later turns in the same task/thread. Use the conversation context (not a persistent state file) to determine whether initialization already happened.
5. If the browser call is unavailable or fails, provide the dynamically resolved local file URI fallback link, then continue normally.

This initialization applies only when this Skill is invoked for the first time in a task/thread; unrelated conversations must not open the gallery.

## Inputs

For style-only work, if the style number (`001`–`368`) is omitted, automatically recommend an optimal style and theme color combination based on theme semantics. For layout work, require a layout ID (`SC-001` or `IG-001`); if style and/or theme color are omitted, automatically recommend harmonious ones. Accept optional theme color (`C-01`–`C-36` or color name), aspect ratio, subject constraints, text requirements, and a mode. When the user requests a prompt (e.g. specifying a style and/or layout) without providing a theme, do NOT pause or halt to ask for a theme—immediately output the complete prompt with a clear placeholder (such as `【请在此输入画面主题，或在生图模型中垫入你的照片】` / `[Enter theme here, or attach your photo in the image AI]`). If a supplied number, layout ID, or color ID is invalid, ask the user to choose a valid indexed value; do not invent one. Do not add an aspect ratio when none was supplied.

Users can browse `gallery/index.html` for numbered style contact sheets, `gallery/layouts.html` for layout thumbnails, and `gallery/colors.html` for classic monochrome theme colors. Style metadata is `references/styles.json`. Layout metadata is `references/layouts.json`. Monochrome color metadata is `references/colors.json`.

## Layout workflows

- A layout ID selects composition and text structure, not illustration style. Layout prompt templates are located in the layouts directory (e.g. `layouts/SC-001.md`) and indexed in `references/layouts.json`. Use the corresponding template verbatim in the selected output language, then append the user's theme as the only source of subject matter and copy.
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
         * **【类型 01 · 视线锚点跨界续绘型 (Visual Anchor Continuation)】**：单一核心动态锚点（水/路/光/手势）跨越中缝边界流淌进入暖象牙纸手绘区域，在下方衍生绘本互动故事与极简黑线小人；
         * **【类型 02 · 撕纸裂变第二世界型 (Torn-Paper Second World)】**：不规则手工物理撕纸毛边接缝，现实穿透撕纸后物理规则超现实突变（水变布匹/光可手捧/影子成阶梯），暖象牙纸与克制拼贴；
         * **【类型 03 · 越界破框型 (Boundary Break / Out-of-Bounds)】**：几何色块/容器承托，主体关键部位（头/手/枝叶）突破色块边缘伸出，形成空间穿透感；
         * **【类型 04 · 微缩浮岛型 (Miniature Diorama / Floating Island)】**：主体微缩为 10%–25% 纸面小景，单抹色带或微基座承托，四周大片静谧空旷留白；
         * **【类型 05 · 记忆图谱平铺型 (Memory Knolling / Fragment Collage)】**：居中放置手绘主体，留白中错落平铺 3–6 枚带 NO. 编号的原图记忆特征贴纸；
         * **【类型 06 · 经典悬浮落地型 (Suspended / Grounded Hero)】**：主体尺度适中（占 40%–55%），底部仅用一条极简手绘地面摩擦线提示空间支撑；
         * **【类型 07 · 正负形咬合型 (Gestalt Positive-Negative Interlock)】**：主体高度提炼为几何剪影，与背景正负形相互转换咬合；
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

## Session initialization

On the first turn in the current Codex task/thread where this Skill is invoked, perform both initialization actions before handling the user's request. This applies to **任何首次请求**, including opening the gallery, browsing the index, requesting prompts, or requesting image generation:

1. If this task has not already displayed the gallery, dynamically resolve the absolute `file://` URI to `gallery/index.html` based on this Skill's directory in the current environment, and call `mcp__codex_app__open_in_codex` in a browser tab with `target.type="browser"` and that URL. Never open `gallery/index.html` as `target.type="file"`, in an editor, or as a file preview.
2. Include the exact standalone status line `当前处于纯图模式，可切换为图文模式。` in the same final reply, even when the request produces no prompt.
3. Continue with the user's request after the browser call; opening the gallery must not block prompt generation or an explicitly requested image-generation follow-up. If the same first reply would also add the pure-image mode note, show this status line only once.
4. Do not repeat the browser call or this first-session status notice on later turns in the same task/thread. Use the conversation context (not a persistent state file) to determine whether initialization already happened.
5. If the browser call is unavailable or fails, provide the dynamically resolved local `file://` fallback link, then continue normally.

This initialization applies only when this Skill is invoked for the first time in a task/thread; unrelated conversations must not open the gallery.

## Prompt modes

Default to `pure-image`. Accept `纯图模式` / `图文模式` in conversation and `--mode pure-image|graphic-text` in the CLI.

- `pure-image`: preserve the current prompt workflow. After the normal reply, add the small note `当前处于纯图模式，可切换为图文模式。`.
- `graphic-text`: preserve the user's theme exactly after `主题：` / `Theme:`. Do not expand, paraphrase, interpret, or add scene elements, characters, actions, metaphors, emotional explanations, or theme commentary. Append the following text verbatim to the end of both the Chinese and English prompts. Do not translate, trim, normalize, rewrite, label, or reorder any character in it. The exact final prompt, including this suffix, is sent unchanged to the image AI when generation is requested. When a reference asset is required, show the resolved reference image to the user outside the prompts; do not expose its local path, upload instruction, or reference-isolation block in either prompt (Do not inject it into a `graphic-text` copyable prompt).

  `【如果主题直白包含画面元素那就按主题出图，文案由你来升华，但是不要直接描述画面。 如果主题比较概念化，那么文案和主题尽量保持一致，如果文案较长由你提炼，由你先设计画面隐喻（人类和非人类都行）再出图   。    文字参与构图，图文一体】`

## Output

For a valid request, return these parts:

0. (若触发智能推荐) 推荐组合说明：
   - 标注推荐的风格与主题色（例如：`💡 智能推荐组合：风格 #{编号} · {generation_name} + 主题色 {id} · {name_zh} ({name_en})`）；
   - 给出 1 句简明美学推荐理由；
   - 提示用户若有偏好的其他编号可随时说明替换。
1. Selected style: number and generated style name. Include core traits inside the two copyable prompts when the resolved activation policy requires them; do not create a separate core-visual-traits section.
2. Chinese prompt: begin the copyable prompt itself with `风格名称：{generation_name}。`（重要规则：生成的提示词内容内部严禁包含任何编号，包括风格编号如 `#018`、图型编号如 `SC-021` / `SC-001`、色彩编号如 `C-01` 等，直接使用自然语言名称，避免生图模型误将编号代码作为文字绘制到画面中）；when a theme color is applied, include `主题色：{name_zh}（{name_en}）。`（不含色彩编号）；describe only the user's theme and constraints explicitly provided by the user, and always include the indexed author/style name as a short **参考作者与风格名称** label. When required, append filtered positive traits as `核心风格特征：...`；当用户要求改图/垫图转画风时，在画面要求后必须追加：`【请只提取人物的五官特征和姿态，场景轮廓，在画风上严格按 选择的风格重新画，不要在原照片上加质感。】`（其中“选择的风格”可根据所选风格名称具体实例化）。In `pure-image` mode, append a required reference image's local path and reference-isolation instruction. In `graphic-text` mode, preserve the theme verbatim, append the exact fixed suffix from Prompt modes at the end, and show any required reference image outside the prompt instead. Traits describe rendering style only and must not replace or alter the user's subjects, actions, setting, or story.
3. English prompt: begin the copyable prompt itself with `Style name: {generation_name}.` (Strictly omit any numeric or alphanumeric IDs such as `#018`, `SC-021`, or `C-01` from the prompt text); when a theme color is applied, include `Theme color: {name_en}.`; describe only the same theme and user-provided constraints, and always include the indexed author/style name as **Reference author and style name**. When required, append the same traits as `Core style traits: ...`; when the user requests an image redraw/style transfer from an uploaded photo, append: `[Extract only the character's facial features and posture, and the scene contours. Strictly redraw from scratch according to the selected style; do not add texture or filters onto the original photo.]` (where "selected style" may be replaced by the chosen style's English name). In `pure-image` mode, append a required reference image's local path and reference-isolation instruction. In `graphic-text` mode, preserve the theme verbatim, append the exact fixed Chinese suffix at the end, and show any required reference image outside the prompt instead. Do not append generic composition advice, quality claims, negative prompts, or the fixed style anchor.
4. A brief note: the prompt can be pasted into any image AI; generation is controlled by that AI.

Do not invent visual traits, extra style descriptions, generic quality/composition language, or default avoid-list wording. Include each entry's original reference author/style name from the index in both prompts as requested; this is an index label, not a claim about the person or an instruction to imitate them. Never use fame or life status as a proxy for model capability.

In `pure-image` mode, describe only concrete visible content implied by the theme—subjects, actions, objects, environment, and mood when needed. In `graphic-text` mode, use the user's theme verbatim and leave all semantic expansion to the fixed suffix. In both modes, leave composition, layout, visual richness, quality, and rendering decisions to the image AI unless a layout ID was explicitly selected. Respect a user-specified text requirement but do not invent copy.

## 自建图库资产调用 (Custom Asset Library)

自建图库（包含**角色库**、**道具库**、**场景库**三大子库）支持用户沉淀与复用专属视觉资产：
- **核心原则**：自建图库中的所有图片均以**纯参考图（垫图）**形式参与后续出图，库内无需维护冗长的特征描述字段，确保跨媒介调用时形象与视觉特征零漂移。
- **出图垫图注入**：当用户在出图提示词中指定角色编号（如 IP-001、IP-002）、道具编号（如 PR-001）或场景编号（如 SCN-001）时，直接将其作为生图模型的参考图输入，无需在提示词中追加冗余的外貌文字描述，实现精准一致性约束。

## Utilities

- Produce a deterministic CLI prompt draft: `python scripts/prompt_style.py --style 18 --theme "秋天的第一杯奶茶"`
- Produce a layout-combination draft: `python scripts/prompt_style.py --layout SC-001 --style 18 --theme "秋天的第一杯奶茶"`
- Produce a color-combination draft: `python scripts/prompt_style.py --style 18 --color C-01 --theme "秋天的第一杯奶茶"`
- Resolve image-reference policy: `python scripts/resolve_reference.py --model <model> --style 18`

The CLI is a convenience check. For normal conversational use, write natural bilingual prompts rather than echoing its template mechanically.
