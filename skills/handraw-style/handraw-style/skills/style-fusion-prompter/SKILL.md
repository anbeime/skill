---
name: style-fusion-prompter
description: 跨媒介“角色视觉语言 × 场景视觉语言”双风格共存融合提示词生成技能。支持融合两套不同视觉风格编号（#001–#368），或融合风格编号与写实风格，并可按需注入图型（170 种）与主题色（36种），严格输出造型解耦、物理光影与叙事共存的高质量生图提示词。
---

# Style Fusion Prompter (跨媒介风格融合提示词生成器)

专注生成**“角色视觉语言 × 场景视觉语言”**共存的高张力、跨媒介双风格融合提示词。坚决反对平庸折中，确保角色与场景两套视觉语言独立鲜明，同时在物理空间、光影、接触与叙事上高度统一。

---

## 核心设计哲学

1. **双语言独立共存，拒绝平庸磨平**：
   - 画面中必须同时存在两套清晰可辨的视觉媒介质感；
   - 角色部分忠实遵循【角色视觉语言】的造型、线条、材质与媒介感；
   - 场景部分忠实遵循【场景视觉语言】的透视、光影、肌理与环境感；
   - 严禁把两者平均磨成普通的混合风格插画，严禁互相完全同化。

2. **缩微摄影视角与尺度反差（核心指令）**：
   - 必须注入“缩微摄影，角色尺寸异常小，场景保持正常尺寸”指令，并放置在提示词较前面的关键位置；
   - 形成极富戏剧性的微缩比例与空间景深：角色如同微型实体生活在正常尺度的真实或插画世界中，极大增强媒介反差与画面趣味。

3. **物理逻辑统一，拒绝贴纸拼贴**：
   - 两种视觉语言保持鲜明反差，但共享**同一个物理世界**：统一的光源方位、色温、天气、环境反射、空气透视；
   - 角色与场景之间必须具备真实可信的物理接触、站立重心、受力传导、前后遮挡与投射阴影；
   - 绝非“把一个角色贴图贴在另一个风格的背景上”，而是角色真正生活在这个场景之中。

4. **叙事瞬间明确，动作逻辑严谨**：
   - 画面必须围绕【主题】形成清晰的叙事时刻，优先保障“谁、在哪里、正在做什么”一目了然；
   - 若存在跑、跳、拉、推、攀爬等动作，重心的支撑与发力方向必须符合物理常识，动作逻辑优于单纯夸张。

5. **主题与风格保真原则（按输入类型精准分流）**：
   - **主题保真**：用户输入的主题是画面的核心灵魂，必须严格保持克制与忠实，**严禁随意扩写复杂的剧情动作、人物外貌、长篇情节或背景故事**。若用户提供简短主题（如“末世异能者”），字段严格使用“末世异能者”或用户原意短语；
   - **风格名称输入（按用户的来，严禁扩写）**：如果用户写的是**风格名称**（如“写实”、“写实风格”、“电影感实拍摄影”、“水墨工笔”、“复古美漫”等任意名称），**完全按照用户的来原样输出**（例如用户指定“写实”，就只输出“写实”），**严禁擅自添枝加叶，严禁扩写任何具体环境场景、景深光影或镜头描述**；
   - **风格编号输入（完整原样复制生图特征，严禁压缩）**：如果用户填了**风格编号**（如 `#018`、`#239`、`240` 等，或由 AI 智能推荐选出的编号），**必须严格按照库内生图标准方式完整展开**：
     `#{number} {generation_name}。参考作者/风格名称：{reference}。核心风格特征：{traits}。`
     **【绝对红线】核心风格特征 `{traits}` 必须直接从 `styles.json` 中逐字逐句完整复制，绝对严禁人为压缩、提炼、总结、删减或改写！**
     （英文对应完整复制为：`#{number} {generation_name}. Reference author/style: {reference}. Core style traits: {traits_en}.`）。

6. **情绪标准化，默认源自拼接器预设库**：
   - 除非用户在需求中明确指定了情绪词，否则【情绪】字段**必须且只能从全库【提示词拼接器】内置的 15 种标准预设中选择**：
     `治愈 (Healing)`、`童趣 (Childlike)`、`松弛 (Relaxed)`、`幽默 (Humorous)`、`诗意 (Poetic)`、`浪漫 (Romantic)`、`活力 (Vibrant)`、`微丧 (Melancholy)`、`孤寂 (Solitary)`、`紧张 (Tense)`、`庄严 (Solemn)`、`荒诞 (Absurd)`、`恐怖 (Eerie)`、`神秘 (Mysterious)`、`激烈 (Intense)`；
   - 严禁自行生造非标复合长句词（如“压抑、肃杀、孤注一掷的狂暴史诗感与生存觉醒”）。

---

## 输入规范与风格解析

### 0. 激活方式与触发词
- **指令激活**：用户发送以 `【风格融合设计】` 或 `风格融合设计` 开头的指令，直接激活本技能；
- **提示词拼装器标准格式**：
  `【风格融合设计】，角色风格：279，场景风格：写实，主题色：C-01，画幅比例：3:4，情绪：治愈，主题：山中的妖精`
  或带有缺省选择：`【风格融合设计】，角色风格：279，场景风格：写实，其他你帮我选择，主题：山中的妖精`。

### 1. 输入维度
用户可提供以下信息（支持自由组合）：
- **角色风格**：风格名称（按用户的来）或全库风格编号（`#001`–`#368`，按生图方式展开）；
- **场景风格**：风格名称（按用户的来，如“写实”、“电影感实拍摄影”）或全库风格编号（`#001`–`#368`，按生图方式展开）；
- **主题**：画面具体主题，生成时必须忠实保留，严禁随意扩充虚构剧情动作；
- **情绪 / 氛围**：默认必须从提示词拼接器 15 种标准预设中选取（治愈 / 童趣 / 松弛 / 幽默 / 诗意 / 浪漫 / 活力 / 微丧 / 孤寂 / 紧张 / 庄严 / 荒诞 / 恐怖 / 神秘 / 激烈），除非用户明确另行指定；
- **（可选）图型**：170 种图型版式编号（`SC-001`–`SC-023`, `IG-001`–`IG-035`, `SB-001`–`SB-071`, `IP-001`–`IP-013`, `EC-001`–`EC-024`）；
- **（可选）主题色**：36 种经典主题色编号（`C-01`–`C-36`）；
- **（可选）画幅比例**：默认 `3:4`，或按需指定（如 `16:9`、`9:16`、`1:1`、`5:2`、`2.35:1`）。

### 2. 智能推荐策略（未指定时）
- **若用户仅给出主题**：由 AI 结合主题语义，在全库 365 种视觉风格与写实风格中**主动推荐一组最具反差美感与张力的【角色风格 × 场景风格】配对**（推荐的编号按生图方式展开），从 15 种预设中挑选最匹配的情绪，推荐 1 款主题色，给出具象化推荐理由后直接输出完整提示词。
- **若用户仅指定角色风格**：保留角色风格（若为名称则按用户的来，若为编号则按生图方式展开），AI 结合主题推荐最具戏剧反差的场景风格。
- **若用户仅指定场景风格**：保留场景风格（若为名称则按用户的来，若为编号则按生图方式展开），AI 结合主题推荐最具契合度的角色风格。

---

> [!IMPORTANT]
> **【核心共存规范段落必须一字不差完整复制】**
> 提示词中从“缩微摄影，角色尺寸异常小，场景保持正常尺寸。画面中必须同时存在两套清晰可辨的视觉语言”至“主题事件明确可读”的整段共存控制指令，是生图模型（如 GPT Image、Midjourney、Flux 等）精准理解双视觉媒介解耦共存与微缩透视的底层核心契约。每次输出风格融合提示词时，**必须一模一样、逐字逐句完整复制附带在提示词后半部分，严禁任何形式的删减、提炼、压缩、篡改或遗漏！**

### 中文标准提示词

```text
生成一幅“角色视觉语言 × 场景视觉语言”共存的跨媒介融合画面。缩微摄影，角色尺寸异常小，场景保持正常尺寸。
- 【角色视觉语言】：{若写名称则按用户的来，若填编号则按生图方式展开：#{number} {generation_name}。参考作者/风格名称：{reference}。核心风格特征：{traits}。}
- 【场景视觉语言】：{若写名称则按用户的来，如：写实；若填编号则按生图方式展开：#{number} {generation_name}。参考作者/风格名称：{reference}。核心风格特征：{traits}。}
- 【主题】：{用户输入的主题，忠实保留，严禁随意扩写大段剧情动作}
- 【情绪】：{默认从15种标准情绪预设库中选取，例如：激烈 / 孤寂 / 紧张；除非用户显式指定}
[- 【图型】：{可选图型编号与排版特征，若无则省略本行}]
[- 【主题色】：{可选主题色编号与名称，若无则省略本行}]
[- 【画幅比例】：{画幅比例，默认 3:4}]

缩微摄影，角色尺寸异常小，场景保持正常尺寸。
画面中必须同时存在两套清晰可辨的视觉语言。
不要把两者平均磨成普通的混合风格插画。
角色部分使用【角色视觉语言】表现，场景部分使用【场景视觉语言】表现。这里的“场景”包括环境空间、地形、建筑、植物、天空、水面、天气、地面、道具以及整体空间氛围。
【角色视觉语言】与【场景视觉语言】都必须忠实保留各自的核心特征，包括但不限于：造型逻辑、比例系统、线条方式、笔触特征、体块组织、几何倾向、材质表达、表面肌理、色彩体系、明暗方式、细节密度、空间处理方式、平面化或立体化程度以及各自独有的媒介感。不要额外强行加入与原风格无关的统一化修饰。
两种视觉语言必须保持明显差异，但共享同一个空间、光源、色温、天气、空气、构图和叙事时刻。
视觉统一应通过遮挡关系、接触关系、投影关系、地面关系、前后空间关系、局部反光、环境综合色和空气透视来完成，而不是把两种视觉语言磨成同一种质感。
角色必须真正存在于场景中，与场景形成自然互动，不能像贴纸一样浮在画面上。角色与场景之间需要有清楚可信的接触、站立、受光、投影、遮挡和空间关系。重点不是“一个角色站在另一个风格的背景前”，而是让角色真正进入并生活在这个场景世界中。
画面必须围绕【主题】形成一个明确的叙事瞬间，优先保证“谁、在哪里、正在做什么”清楚可读。不要为了展示风格而加入大量与主题无关的装饰元素。
如果画面中存在明显动作，如跑、跳、扑、拉、推、攀爬、追逐、搏斗、搬运或其他动态行为，需要保证发力点、重心、支撑关系、接触位置、受力方向、物体运动方向、遮挡和透视合理，动作逻辑优先于单纯夸张效果。
不要生硬拼贴，不要左右分栏，不要上下分区，不要贴纸叠加，不要主体悬浮，不要错误遮挡，不要不同光源互相冲突，不要让角色风格被完全同化成场景风格，也不要让场景风格被完全同化成角色风格。
最终效果应呈现：
- 缩微摄影比例，角色尺寸微小而场景保持正常尺寸
- 两种不同视觉语言自然存在于同一个世界中
- 角色风格与场景风格差异清晰
- 空间与光线逻辑统一
- 角色与场景互动自然
- 主题事件明确可读
```

### English Standard Prompt

```text
Generate a cross-media fusion artwork where "Character Visual Language × Scene Visual Language" coexist. Miniature photography, the character scale is exceptionally small, while the scene maintains normal scale.
- [Character Visual Language]: {If style name is provided, use user's exact name; if style number is provided, expand in generation format: #{number} {generation_name}. Reference author/style: {reference}. Core style traits: {traits_en}.}
- [Scene Visual Language]: {If style name is provided, use user's exact name (e.g., Realistic photography / Cinematic photorealism); if style number is provided, expand in generation format: #{number} {generation_name}. Reference author/style: {reference}. Core style traits: {traits_en}.}
- [Theme]: {User's theme, strictly preserved without arbitrary expansion}
- [Mood]: {Default selected from the 15 standard presets: Healing / Childlike / Relaxed / Humorous / Poetic / Romantic / Vibrant / Melancholy / Solitary / Tense / Solemn / Absurd / Eerie / Mysterious / Intense, unless specified by user}
[- [Layout]: {Layout ID and description, omit if none}]
[- [Theme Color]: {Theme color ID and name, omit if none}]
[- [Aspect Ratio]: {Aspect ratio, default 3:4}]

Miniature photography, the character scale is exceptionally small, while the scene maintains normal scale.
Two clearly distinguishable visual languages must coexist in the image simultaneously.
Do NOT average or blend the two into a generic hybrid illustration.
The character elements must be rendered strictly in [Character Visual Language], while the scene elements must be rendered strictly in [Scene Visual Language]. Here, "scene" includes environmental space, terrain, architecture, vegetation, sky, water, weather, ground, props, and overall spatial ambiance.
Both [Character Visual Language] and [Scene Visual Language] must faithfully retain their respective core characteristics, including but not limited to: modeling logic, proportional systems, linework methods, brushstroke traits, volume organization, geometric tendencies, material expressions, surface textures, color systems, shading/lighting techniques, detail density, spatial treatment, degree of flatness vs. three-dimensionality, and their distinct tactile media sensations. Do NOT artificially force any uniform stylistic modifications irrelevant to each original style.
The two visual languages must maintain noticeable contrast, yet share the exact same space, light source, color temperature, weather, atmosphere, composition, and narrative moment.
Visual unity must be achieved through occlusions, physical contact, contact shadows, ground contact, fore/background depth, subtle bounce light, environmental ambient color, and aerial perspective, rather than blending the two visual languages into an identical material texture.
The character must truly exist and naturally interact within the scene world, rather than floating like a detached sticker. There must be credible physical contact, grounded posture, lighting, cast shadows, occlusions, and depth relationships between the character and the environment. The focus is NOT "a character simply standing in front of a different-styled background", but rather having the character truly inhabit and live within this environment.
The image must center around [Theme] to form a distinct narrative moment, prioritizing clarity of "who, where, and what they are doing". Do NOT introduce clutter or irrelevant decorative elements merely to exhibit the styles.
If dynamic actions are present (e.g., running, jumping, leaping, pulling, pushing, climbing, chasing, wrestling, carrying, or dynamic movements), ensure the center of gravity, support points, contact points, force vectors, motion trajectory, occlusion, and perspective are physically convincing; dynamic logic takes priority over superficial exaggeration.
Do NOT create awkward collages, do NOT split left-right or top-bottom columns, do NOT layer like stickers, do NOT let subjects float, avoid erroneous occlusions and conflicting light sources, do NOT assimilate the character style into the scene style, and do NOT assimilate the scene style into the character style.
The final result should achieve:
- Miniature photography scale contrast: character scale exceptionally small while scene maintains normal scale
- Two distinct visual languages coexisting harmoniously in the same world
- Clear differentiation between character style and scene style
- Unified spatial, perspective, and lighting logic
- Natural, believable physical interaction between character and scene
- Clear, legible thematic narrative event
```

---

## 交付与后续操作引导 (CTA)

每次输出双语风格融合提示词后，主动附带极简双轨引导：

```markdown
---

💡 **风格融合设计方案已就绪！您可以选择：**
1. **【方式 A · 自主生图】**：复制上方提示词，粘贴至您喜爱的生图工具（如 GPT Image 2/2.5、Midjourney、Stable Diffusion 等）直接出图；
2. **【方式 B · 全自动生图】**：直接对我说 **“全自动出图”**，我将调用生图工具为您全自动生成风格融合画面！
```
