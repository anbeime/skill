---
name: couple-photo-requirements-planner
description: Confirm portrait, couple, family, group, wedding-party, team, cast, travel, period, or cosplay photo requirements and produce complete per-participant Looks, scenes, props, and a confirmed photography handoff for any number of subjects.
version: 2.24.26
---

# Universal People Photo Requirements Planner

## 通用摄影关键词
- 所有摄影拍摄类型均在可复制方案与最终生图提示词中原样加入：**高级摄影师风格，创意构图，强烈的戏剧张力**。
- 个人、情侣、婚纱、亲子、全家福、古风、私房、职业、Cosplay 等类型，以及自主推荐、抽卡、八宫格、单张和放大优化均适用；不得省略或仅以同义词替代。
- 通过机位、空间层次、光影和情绪落实关键词；继续遵守已确认的人物身份、服装、妆发、画幅及 Shot 动作约束。
- 保持现有“先三方案选向 → 八宫格预览 → 按需单张/放大”的交付流程。


本 Skill 已从“固定双人情侣模型”升级为“任意人数人物摄影模型”。情侣只是 `relationship_preset` 的一种，不再是数据结构前提。

同一项目目录可包含多个并行主题。根目录共享所有人物的身份参考；每个 `THEME-xxx` 独立保存需求确认、Group Look、作品世界、场景、逐人服装锁定、Shot、宫格与精修。进入需求收敛前必须先选定当前主题；新建或切换主题不得复用其他主题的服装、地点、提示词或阶段状态。

## Purpose

This skill converts vague or partial ideas into a confirmed creative brief and a complete styling plan for **one or any number of people**.

Supported examples include:
- 单人写真
- 情侣写真 / 订婚照
- 婚纱摄影
- 家庭 / 亲子 / 多代同堂
- 闺蜜 / 兄弟 / 朋友群像
- 伴郎伴娘 / 婚礼派对
- 乐队 / 团队 / 公司形象群像
- 旅行群像
- 古装 / 民国 / 时代群像
- Cosplay / 游戏 / 动漫 / 影视角色群像
- 原创世界观多人角色摄影

It stops before execution-level photography design. Camera position, focal length, per-shot lighting, pose choreography, exact framing, and Shot List belong to `skills/paishe`.

---

# 1. Non-negotiable participant model

## 1.1 Participant count

`participant_count` may be **any positive integer**. Do not silently cap it at 2, 4, 6, or 8.

Every person gets a stable ID for the whole project:
- `P01`
- `P02`
- `P03`
- ...

Each ID may also have a natural-language label such as 新娘、父亲、姐姐、主唱、角色名、朋友A. The ID is the continuity key; the label is for readability.

## 1.2 Detail Floor — 人数增加不能降低单人细节

This is a hard quality rule.

When there are multiple participants:
- 每个人必须有独立人物小节。
- 每个人必须有独立服装全文描述。
- 每个人必须独立说明服装结构、层次、材质、颜色、鞋履、配饰、妆容/整理状态、角色/时代逻辑、场景适配和避免项（适用者写，不适用者明确省略原因）。方向卡的逐人服装草案形成后立即进入 Editorial 专业发型师设计；参考图原发型默认不锁，精修身份参考图中的发型也只作为审美参考。
- 有真人参考图时，原发型不默认属于身份锁定项。每个方向先形成逐人服装草案，随后立即运行独立的 **Editorial 专业发型师设计**：发长、直卷、刘海、分缝、体积与轮廓均可重新设计；刘海策略必须明确。发型确定后，再运行 **Editorial 专业化妆师设计**。A/B/C 展示时妆发已经是该方向的正式结果。
- 不得使用“其他人同风格”“剩下的人类似”“其余成员统一穿搭”“男生们都……”“女生们都……”替代逐人描述。
- 可以共享设计规则，但共享规则之后仍必须逐人落地。
- 人数增加时，允许文档变长；**不允许通过压缩单个人物信息来控制长度**。

If the document becomes long, write it in sections or batches, but the final saved artifact must contain every participant in full. Never solve scale by summarizing later participants.

## 1.3 Identity references

Every uploaded identity reference must be mapped to a participant ID. Do not infer that “two uploaded photos = a couple”.

Recommended structure:

```yaml
participants:
  - id: P01
    label: 新娘
    role: bride
    identity_references: [references/identity/P01-01.png]
  - id: P02
    label: 新郎
    role: groom
    identity_references: [references/identity/P02-01.png]
  - id: P03
    label: 伴娘A
    role: bridesmaid
    identity_references: [references/identity/P03-01.png]
```

Reference photos preserve recognizability only. They are not permission to copy clothing, location, or pose unless the user explicitly asks.

---

# 2. Core interaction philosophy

## 2.0 Mode and direction handling

- `user_directed` 是默认模式，但**不得**把模式展示成用户首轮要选择的菜单。
- 新主题首轮默认直接输出 A/B/C 三张方向卡；A/B/C 只代表方向。全家福/其他多人若 Participant Structure Gate 未补齐，则先一次性确认缺失的人数、性别构成、关系结构。
- A/B = 两个现代现实世界著名地点；C = 一个穿越方向（古代 / 未来现实地标 / 已知作品地点）。
- 用户回复 A/B/C 后，立即展开完整 Look，并继续交给 `paishe` 完成姿势/情绪与 8 Shot，不设置二次确认。
- 只有用户明确说“抽卡”才进入 `card_draw`；B/b/2 不代表抽卡。
- 抽卡模式不展示 A/B/C 让用户选择，由 AI 自动选定合法方向。
- 所有系统生成方向先通过 `few_shot_exclusion_set` Hard Gate。

## 2.0.5 Participant Structure Gate

Before direction generation:
- **Couple**: default to `participant_count=2`, one woman + one man; do not ask count/gender unless the user explicitly indicates a different composition.
- **Family / group / multi-person**: require `participant_count`, gender composition (prefer per-person when roles are known), and relationship/role structure. If any are missing, ask only those missing fields in one compact turn.
- If titles/roles already make sex or relationship unambiguous, infer them and do not repeat the question.
- Save a concise `relationship_description`; it is mandatory for couples and groups and must be inherited by Look and `paishe`.

## 2.1 General interaction
1. 用户可从人数、关系、主题、服装、地点、旅行、文化风格、IP、角色、颜色、氛围或“我不知道”等任意入口进入。
2. 先解析已知信息，不做巨型问卷。
3. 未说明字段通常合理推断；但全家福/其他多人拍摄的总人数、性别构成、关系结构属于 Participant Structure Gate，缺失时必须先补齐。
4. 用户明确条件优先于系统推断。
5. 宽泛请求也必须落到具体时空方向，不能只给“城市日常 / 自然系 / 高级棚拍”等泛风格。
6. 多 Look、多人物仍遵守 Detail Floor。
7. 地点采用 Progressive Location Specificity：方向阶段锁时空锚点，Look 阶段给区域，Shot 阶段给微点位。
8. 方向选择是 forward gate；之后完整方案可直接推进，用户修改属于 revision。

# 3. Chat-first / Project-persistent

普通聊天默认 `chat_first`，**不得要求用户先提供绝对项目目录**。满足人物结构 Gate 后直接执行首轮 A/B/C；情侣默认结构无需补问。

仅当用户明确要求保存工程、使用脚本或指定目录时，进入 `project_persistent`：
- 可以使用原项目目录、Theme、handoff 与验证脚本；
- 目录状态不得改变创意质量或交互规则；
- 不得因为没有目录而阻塞普通聊天方案。

# 4. Requirement parsing

Treat all of these as entry signals, not mandatory categories.

## 4.1 People / relationship entry

Examples:
- “我一个人拍”
- “情侣两个人”
- “一家五口”
- “四个闺蜜”
- “新郎新娘加 6 个伴郎伴娘”
- “一个 7 人乐队”
- “原神 5 人角色群像”

Extract when present:
- participant count
- stable labels / roles
- relationship preset
- hierarchy or central subjects
- whether everyone must appear in every image
- any subgroup logic

For couple requests, default to one woman + one man unless the user says otherwise. For family/group/multi-person requests, gender composition is a required participant-structure field; infer it from explicit role labels when unambiguous and ask only for unresolved members.

## 4.2 Theme / genre entry

Examples:
- “古风一家五口”
- “韩系闺蜜写真”
- “民国四人群像”

Interpret:
- era / cultural system
- formality
- silhouette families
- role differentiation
- group palette system
- scene compatibility

## 4.3 Character / IP / cosplay entry

When a specific work is named, record:
- IP / work
- each participant's character or role if supplied
- fidelity: high fidelity / live-action cinematic / fashion reinterpretation / mood-only
- in-world era and recognizable in-world location

Every participant must belong coherently to that world. Never style one named character accurately and turn the rest into generic modern extras.

## 4.4 Location / travel entry

Location is context, not an instruction to wear local ethnic clothing.

Use this precedence:
1. explicit user location
2. historical time-and-place setting
3. named work / IP world setting
4. original fictional setting
5. **random world-famous real location fallback** for ordinary modern photography when the user gives no location

For period work, place all participants inside a living period-appropriate setting. Do not substitute a present-day museum or reconstruction park unless explicitly requested.

### 4.4.1 Default world-famous-location fallback

If the user gives **no location at all** and the request is ordinary modern real-world photography, do not ask a follow-up only for location. Auto-select it:
- Build a theme-compatible pool of at least 6 globally recognizable real places from multiple countries/regions.
- Randomly choose 1 suitable place from that pool.
- Outdoor requests: prefer famous landmarks, scenic areas, coasts, historic streets, gardens, mountains, lakes, or iconic urban spaces.
- Indoor requests: prefer a named landmark building, iconic hotel, notable public interior, or a truthful conceptual private interior geographically anchored to a famous real street/area.
- Privacy-sensitive indoor genres such as 私房写真 should prefer an iconic hotel/building interior over an exposed public landmark.
- A reroll / “换地点” must choose a different place from the currently locked anchor.
- Do not repeatedly default to the same few cities; diversify geography while preserving photographic fit.

This fallback is subordinate to explicit user location, period/historical setting, named-work world, and original fictional world.

---



# 4.5 Progressive Location Contract — 地点精度随流程递进

这是硬规则，但**需求调研阶段不得过度锁死空间**。地点精度分三层：

1. **需求确认：时空锚点**
2. **Group Look / 换装：可拍区域**
3. **Shot List：具体微点位**

## 4.5.1 需求确认阶段：只锁时空锚点

此阶段只需确认“我们到底在哪个真实世界 / 作品世界 / 原创虚构世界拍”，不要替 Shot List 决定具体站位。

现代现实地点最低要求通常是：
- 若用户未指定地点：先按 **4.4.1** 自动随机选择一个与主题相容的世界著名真实地点，再按以下精度规则记录；不要只因为缺地点而向用户追问。
- **室外**：城市 + 具体景区 / 街道 / 路线 / 地标；或城市 + 真实具名公共场所。
- **室内**：优先城市 + 真实具名酒店 / 建筑 / 公共室内；若用户要私人公寓而没有可核验房源，则至少使用真实街道 / 路线作为地理锚点，并明确标记为概念化私人室内。
- 仅有“巴黎第六区 / 某城市中心 / 某街区”而没有更具体的街道、具名建筑或景区，对室内项目不算完成地点。

室内示例：
- 法国巴黎第六区 Saint-Germain-des-Prés 一带的 Haussmann 公寓语境（概念化私人室内）
- 法国巴黎的 Hôtel Lutetia

户外示例：
- 中国杭州·西湖风景名胜区·孤山 / 北山街一带
- 日本京都·东山地区·八坂塔周边街区

此阶段**不要强制**写：房间号、哪扇窗、哪段走廊、哪级台阶、哪一小段湖岸、人物具体站在哪个转角。

## 4.5.2 历史 / 古风

确认历史地点或历史审美语境，并在服装、建筑、礼仪会受影响时写明时代/时期。需求阶段无需提前确定每个 Shot 的院落转角或室内节点。

## 4.5.3 影视 / 游戏 / 动漫 / 文学作品

需求阶段记录：
- `source_work`
- `in_world_location`：作品中的可辨识地点
- `era_or_period` / chapter / world-state（相关时）

例如：
- 《红楼梦》→ 大观园·潇湘馆 → 大观园居住时期 / 清代小说语境
- 《原神》→ 璃月港·玉京台 → 当前璃月世界状态

此阶段不要求写“竹影院落通向回廊的转角”或“临栏平台左侧”等 Shot 级节点。

## 4.5.4 原创虚构

记录世界/城市/区域 + 具名虚构地点 + 时代/世界状态。必须是明确的虚构时空点，但无需提前锁死微空间。

## 4.5.5 Group Look / 换装阶段：只增加可拍区域

在确认时空锚点后，可以补 2–4 个**可拍区域**，例如“酒店公共休息区 / 客房起居区 / 楼梯空间”，或“潇湘馆竹影院落 / 回廊 / 小轩窗内外”。

这些只是区域候选，不是 Shot 的最终落位。不要把每条 Shot 的空间创意提前写完。

## 4.5.6 Shot List 阶段：才决定 exact micro-location

`paishe` 在每条 Shot 中根据构图、动作、参与人数和叙事，自由选择并写明 `scene_area`。这时才细化到窗边、楼梯转角、廊柱之间、岸线某段、平台临栏位置等。

## 4.5.7 Verification honesty

真实地点不得为了“具体”而伪造门牌、酒店、房号或私人公寓。现实地点可使用：
- `user_supplied`
- `verified_current`
- `known_public_place_needs_current_verification`
- `conceptual_private_interior`

当 Skill 自己推荐现实公共地点（酒店、建筑、景点、街道等）且具备网页搜索能力时，应先核验名称与地点是否真实存在、是否仍可识别；不能核验时必须标记 `known_public_place_needs_current_verification`，不得把猜测写成事实。

# 5. Direction drafts

Direction design obeys the root current 2.24.20 Hard Gates.

### 自主模式
- 新主题第一屏默认直接给 **A/B/C 三张方向卡**，不得先展示模式选择；唯一例外是全家福/其他多人题材的 Participant Structure Gate 尚未补齐。
- A/B：两个现代现实世界著名真实地点，优先跨国家/城市/空间气质。
- C：一个穿越方向，只能来自古代真实时空、未来化现实地标、或已知作品+明确地点。
- 宽泛请求也不能退化为“城市日常 / 自然系 / 高级影楼”等泛风格。
- 三张卡必须先通过 `few_shot_exclusion_set`。
- 用户回复 A/B/C 后立即消费方向，展开完整 Look 并继续 `paishe`；不再增加方向二次确认。

### 抽卡模式
- 仅由用户明确“抽卡”触发。
- 不向用户展示三张卡要求选择。
- 内部生成合法候选并自动选定，通过 Few-shot Hard Gate 后继续完整 Look / 姿势情绪 / 8 Shot / 1 张八宫格。

### 每张方向卡固定字段
- 时空坐标
- 人物身份
- **人物关系描述**（情侣与多人必填）
- 核心场景
- **逐人服装字段**：情侣默认“女方服装 / 男方服装”；多人使用角色名或 P01 / P02 / …，每个人单独一行
- 逐人正式发型（方向展示前已设计）
- 逐人正式妆容（方向展示前已设计；女性默认白皙柔焦影楼精修）
- 色彩 / 光线
- 人物状态
- 摄影语言

方向卡只负责时空与视觉路线，不在此阶段锁死 Shot 级微点位。多人服装即使共享色盘/正式度，也不能合并成一个“服装造型”字段；共享规则只能作为补充。

---

---

## 5.5 Draw-card spacetime engine

In `card_draw` mode, randomization applies only to fields the user has not locked. Preserve participant count, identity references, relationship, required wardrobe/genre, safety/privacy needs and hard avoids.

Choose a compatible spacetime type from:
- `real_contemporary`
- `real_historical`
- `original_fictional`
- `source_work` when coherent and the concrete work location / era can be stated correctly

The draw must produce a concrete Location Card, not only an atmosphere. Real-world draws use real named places and verification rules. Historical draws include era. Source-work draws include `source_work + in_world_location + era/world-state`. Original fictional draws include a named world/region + named place + world state.

Avoid immediate repetition of recently used spacetime cards when alternatives fit equally well.

# 6. Detailed confirmation draft — 不再使用独立简版确认单

The workflow has **one user-facing confirmation gate**, and that gate is the complete Group Look / Couple Look document.

Do **not** output a standalone card that only says “拍摄类型 / 人数 / 服装倾向 / 色彩倾向 / 避免项” and then ask the user to confirm before seeing the full plan. That pattern is considered a quality regression.

## 6.1 When direction drafts were shown

If the user chooses a direction, merges fields from directions, or says an equivalent clear approval such as “就这个 / 选 2 / 用 1 的场景和 3 的衣服”, treat that choice as sufficient broad-direction confirmation. Unless a **critical ambiguity** remains, immediately expand it into the full detailed Group Look in the same next response.

Do not ask the user to confirm the same direction twice.

## 6.2 When no direction draft was needed

If the user's initial request is already coherent enough to design, directly produce the full detailed Group Look. A short factual header may summarize the understood brief, but it must be part of the same detailed document and must never replace the per-participant Look sections.

## 6.3 Brief header inside the detailed document

At the top of the full confirmation draft, include a compact **创意摘要** when useful:
- 拍摄类型 / 用途
- 人数与人物 roster / 关系
- 套数
- 主题 / 世界观
- confirmed / selected location anchor
- source work + in-world place + era/world-state when applicable
- overall visual direction
- palette
- hard avoids

This header is informational only. **Never stop after this header.** Continue immediately into the complete Look.

## 6.4 Location Anchor Preservation Rule — 地点具体度单向不降级

Every location mention that the user selected or accepted must be classified and inherited:
- `execution_location_anchor`: intended actual venue / place;
- `reference_location_anchor`: a named place used as a visual/spatial reference but not claimed as the actual shoot venue;
- `in_world_location_anchor`: a work-world / historical / fictional named place.

If a direction draft says, for example, “以上海外滩 W 酒店客房类型空间为参考”, the detailed confirmation draft must still state that named reference anchor. It may say the final execution venue is another legally shootable hotel, but it may not collapse the wording to merely “精品酒店套房”.

If a selected direction names 鼓浪屿、武康路、玉京台、潇湘馆 or another concrete place, later stages must retain that place unless the user replaces it.

A later stage may:
- keep the anchor unchanged;
- refine it with broader shootable zones;
- explicitly replace it and state the replacement reason.

A later stage may **not** silently downgrade:
- “上海外滩 W 酒店客房类型空间（参考锚点）” → “精品酒店套房”;
- “厦门鼓浪屿临海老别墅区域” → “海边民宿”;
- “《红楼梦》大观园·潇湘馆” → “古风庭院”.

---

# 7. Complete Group Look confirmation document

Generate the complete Group Look immediately once the creative direction is sufficiently resolved. This document itself is the confirmation draft.

For each Look use this order:

1. **LOOK 名称 / 定位** — write a real creative premise, relationship/narrative tone, and why this Look exists.
2. **人物关系描述** — couples/groups must explicitly state the confirmed relationship structure, role hierarchy, and interaction baseline; do not reduce it to one label.
3. **群体设计逻辑** — for one person, write the individual's visual role instead of omitting this section.
4. **P01｜人物标签 — 完整服装**
5. **P02｜人物标签 — 完整服装**
6. Continue until **every participant** is covered
7. **Couple / Group 搭配关系** — palette, silhouette, material, formality, contrast/harmony, shared motifs, intentional differences
8. **场景 Location Card** — must inherit all selected location anchors without regression
9. **场景内可拍区域** — 2–4 broad candidate zones, leaving Shot micro-positioning downstream
10. **道具与归属** — who holds/uses what; shared props; narrative function
11. **视觉锁定** — explicitly list the conditions that downstream shooting may not weaken or replace
12. **硬性避免** — include user avoids plus Look-specific failure modes
13. **与需求的匹配逻辑** when useful

Do not move into camera / pose / Shot List execution.

## 7.1 Per-participant wardrobe contract

Every participant section must read like a professional styling note, not a keyword list. It must cover, where applicable:
- participant ID / label / role
- identity / character / relationship function
- visual role in the group
- garment category and specific structure
- silhouette and proportion
- upper / inner / outer layers
- lower garment / dress / robe structure
- neckline / collar / lapel / sleeve / waist / hem as relevant
- primary and secondary materials
- exact palette role and surface finish
- structural / decorative details
- movement behavior
- shoes
- jewelry / watch / hair accessories / other accessories
- grooming / makeup; hairstyle is finalized by the Editorial hairstylist stage after wardrobe/theme are known
- prop ownership if any
- season / practicality
- scene / era / work-world compatibility
- hard avoids

A field may be not applicable, but the person may never be summarized away.

## 7.2 Group styling relationship contract

After all individuals, explain:
- visual hierarchy
- palette relationship
- material relationship
- silhouette relationship
- formality relationship
- contrast vs harmony
- shared motifs
- intentional differences
- subgroup logic if any
- how the styling avoids uniform/team-photo sameness unless uniformity is intentional

## 7.3 Location Card contract

The Location Card must include:
- location mode
- execution location anchor, if chosen
- reference location anchor, if used
- source work / in-world location, when applicable
- era / period / chapter / world-state, when relevant
- indoor/outdoor
- verification status for real public venues
- 2–4 shootable zones
- environmental material / architecture / weather / spatial cues that matter to the Look
- why the wardrobe works in this location

Do not fabricate access permission. If the user requires a venue with permission, state “需以实际拍摄许可为准” unless permission is actually known.

---

# 8. Group Look continuation rule

选中 A/B/C 后，立即输出完整 Group Look / Couple Look，并将其作为后续摄影规划的视觉锁定来源。

### 自主模式
- 用户对方向的选择即是继续授权。
- 不再等待“整组确认”才进入 Shot List。
- 完整 Look 输出后立即 handoff 给 `skills/paishe` 做姿势/情绪与 8 Shot。
- 用户之后若指出某个 Look / 人物 / 地点 / 服装需要修改，做依赖更新即可。

### 抽卡模式
- AI 自动选择并检查完整 Look，记录 `confirmation_source: ai_auto_confirmed`，继续 Shot pipeline。

禁止重新插入“简版需求确认 → Look 再确认 → Shot 再确认”的旧链路。

# 9. Multi-look rules

For multiple Looks:
- record `look_count` immediately
- plan the full set as a coordinated system
- every Look must include every planned participant unless the user explicitly defines a subgroup-only Look
- each Look should have a distinct role
- differentiate by at least 2–3 of formality, silhouette, culture/era, palette, material, scene, group mood, editorial intensity

Track each Look as `planned / presented / confirmed / needs_revision`.

---

# 10. Scale handling without quality loss

There is no participant-count ceiling in the writing workflow.

For larger groups:
- use participant IDs aggressively for continuity
- split the human-readable document into sections such as P01–P06 / P07–P12 if necessary
- keep one complete roster at the top
- keep one complete wardrobe entry per person
- keep one complete `participant_outfits` entry per person in handoff
- never convert later participants into a group summary
- if several people share a uniform base, write the shared base once **and then list each person's individual variation and full final appearance**

The final saved artifact must be complete even if the chat presentation is paginated.

---



# 10.5 New-session / Restart-theme protocol

When the user starts a new session or says “重新开一个主题 / 换一个主题 / 从头来”:
1. treat it as a fresh creative brief;
2. keep the same Detail Floor and Location Specificity Contract;
3. do not copy old theme content unless the user explicitly wants continuity;
4. do not shorten fields because they were explained before;
5. create a full participant roster, full per-person styling, full spacetime-anchor Location Cards, and full confirmation gates again.

A restarted theme is **not** a “quick mode”.


# 11. Handoff schema

Create `deliverables/requirements-handoff.yaml` after the direction has been selected and the full Look has been built. In `user_directed`, use `confirmation_source: direction_selection`; in `card_draw`, use `confirmation_source: ai_auto_confirmed`. Follow `templates/handoff-schema.yaml`.

Core structure:

```yaml
schema_version: 3
project:
  participant_count: 3
  participants:
    - id: P01
      label: 人物1
    - id: P02
      label: 人物2
    - id: P03
      label: 人物3

looks:
  - id: LOOK-01
    status: confirmed
    participant_looks:
      - participant_id: P01
        label: 人物1
        outfit: {...}
        full_description: ...
      - participant_id: P02
        label: 人物2
        outfit: {...}
        full_description: ...
      - participant_id: P03
        label: 人物3
        outfit: {...}
        full_description: ...
    group_relationship: ...
    visual_lock:
      participant_outfits:
        - participant_id: P01
          label: 人物1
          outfit: 完整、不可替换的服装描述
        - participant_id: P02
          label: 人物2
          outfit: 完整、不可替换的服装描述
        - participant_id: P03
          label: 人物3
          outfit: 完整、不可替换的服装描述
      group_relationship: ...
      work_era_setting: ...
      scene_mood: ...
      hard_avoids: []
```

`visual_lock.participant_outfits` is immutable downstream. Shot prompts may change action, composition and local environment, but may not change participant identities or outfits.

For backward compatibility, downstream code may still read old two-person fields `female_outfit / male_outfit / couple_relationship`, but new projects must write the participant-array schema.

Set `handoff_to_photography_skill.ready: true` when the selected direction has been authorized by A/B/C selection (or legal card-draw auto-selection), every participant Look is complete, and every participant has locked hairstyle_design + makeup_design. Do not ask for a second Look confirmation.

---

# 12. Visual-output boundary

This Skill itself never generates images. Theme-confirmed outfit rerolls go to `skills/huanzhuang`; Shot planning and image stages go to `skills/paishe` / `skills/zongkong`. In `card_draw`, handoff must continue automatically rather than waiting for another user approval.

---

# 13. Response behavior

- Use concise professional Chinese by default.
- Do not expose internal taxonomy unless useful.
- Never re-ask answered questions.
- Preserve user wording where useful.
- One field correction should update only dependent items.
- In multi-person projects, participant IDs must stay stable across all later turns and files.
- **Never trade detail for participant count.**
- **Never trade detail for a new session, a restarted theme, or a reroll.**
- **Never trade a concrete spacetime anchor for atmosphere words; also never over-lock Shot-level micro-locations during discovery.**
### 真人参考图：精修与表情去锁定
- **原始参考图永远是默认身份源**：首次上传的真人原图绑定到对应 `participant_id` 后，后续任何生成图都不得自动改写该映射。
- `meihua` 输出、八宫格、单张、放大图、换装预览都只属于派生参考；只有用户明确说要把某张图作为后续人物参考时，才允许显式提升为 active identity reference。
- 用户只是选择/放大/喜欢某张派生图，不等于授权替换身份参考。
- 参考图只负责锁定身份：脸型、五官结构、年龄感、辨识度；**不把参考图表情当成后续 Shot 的固定模板**。
- 身份锚定描述默认不得把参考图的发型、发长、发色写成必须保持的身份特征；例如不得写“保持短发/长发/某发色印象”，除非用户明确要求保留。
- 除非用户明确要求复刻参考图表情，否则后续 Shot 必须根据各自的动作、关系和情绪动机自由变化嘴型、笑意强弱、眼神方向、视线落点和头部角度。
- 上传真人参考图本身不触发美化询问。只有用户主动要求三宫格参考图美化/精修时才调用 `meihua`；用户确认的放大结果默认只是 **精修美化图**，不会自动成为后续身份参考，除非用户明确要求提升。
- 原参考图发型不属于身份锁；精修身份参考图发型也只作为“找感觉”参考。正式发型在方向卡生成阶段就由 Editorial 专业发型师完成，选向后下游只继承。
- 不再主动询问是否美化参考图。无论是否调用 `meihua`，方向卡生成阶段都必须进入 **Editorial 专业化妆师设计**；女性默认白皙柔焦影楼精修。
- 明确纯男性项目默认不加；用户明确要求自然皮肤 / 原生肤质 / 不要精修时关闭。
- 不再自动展开任何皮肤细节或肤色描述；不得仅凭外貌自行推断族裔触发。


## 2.24.20 Spacetime Pool Hard Gate
- 默认抽卡/推荐池：`real_contemporary / real_historical / future_landmark / source_work`。
- `original_fictional` 不在默认池；仅当用户明确要求原创世界时开启。
- `future_landmark` 必须基于可识别的现实城市/地标未来化，而不是无出处的泛未来城。
- 用户未指定地点时，现实地点随机与人物国籍解耦，并优先追求跨区域、跨文化、跨气候的明显跨度。
- 内部的核验、Few-shot Gate、去重 Gate 不得作为正常用户可见回执输出。


## 2.24.20 Editorial 化妆师节点
- 每个正式 Look 在发型确定后必须输出正式化妆师方案。
- 方案至少包含 skin_optimization / base_makeup / brows_eyes / cheeks_lips / highlight_contour / theme_fit。


## 2.24.21 方向卡妆发前置 Hard Gate
- 每个候选方向先生成逐人服装草案，再调用 `skills/hairstyle`，随后调用 `skills/makeup`。
- A/B/C 展示时，逐人正式发型和正式妆容已确定。
- 用户选向后，完整 Look 只继承并展开，不再次设计妆发。
- 自主模式的 A/B/C 选择就是唯一方向授权，不再追加 Group Look 确认。
- 真人参考图按 participant_id 建立 identity mapping，下游不得串脸。
