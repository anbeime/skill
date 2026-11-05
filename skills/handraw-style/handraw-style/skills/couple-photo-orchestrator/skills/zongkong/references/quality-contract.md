# Universal Quality & Location Contract — 2.24.20

This contract applies to every new project, every new chat/session, every newly-created theme, every theme restart, every reroll, and every downstream artifact.

## A. Quality floor is session-independent

A new session or a restarted theme resets **content**, never **quality**.

Never reduce detail because:
- the conversation is new;
- the user says “重新开一个主题 / 换个主题 / 从头来”;
- there are more participants;
- the document is getting long;
- the same field was detailed in a previous theme.

Every fresh theme must rebuild the complete professional document at the same detail floor. Do not substitute “同上 / 沿用 / 类似前一套 / 其他人类似 / 其余成员自然互动” for fields that are required in the current theme.

If output becomes long, paginate or split into sections. The final saved artifact must still be complete.

## B. Participant detail floor

For every planned participant, preserve the same per-person description depth: identity/role, full outfit, layers/structure, materials, color, shoes, accessories, grooming/hair/makeup where relevant, era/character logic, scene compatibility, props, and avoids.

### Participant Structure Gate
- Couple requests default to two participants: one woman and one man, unless the user explicitly states another composition. Do not ask count/gender again.
- Family/group/multi-person requests must resolve total participant count, gender composition, and relationship/role structure before A/B/C directions. Ask only missing items, once.
- `relationship_description` is mandatory for couples and groups and must persist downstream.

### Direction-card per-person wardrobe floor
- Couple/group A/B/C cards must not contain one merged wardrobe field.
- Couples use separate woman/man wardrobe fields by default. Groups use one wardrobe field per named role or participant ID.
- Shared palette rules may be stated in addition, never instead of individual wardrobe fields.

## C. Progressive location specificity floor

Location detail is **phase-aware**. Do not lock micro-locations during requirement discovery. The workflow deliberately increases spatial precision as the project moves toward shooting.

### Phase 1 — Requirement discovery / confirmation: spacetime anchor only
The goal is to establish a truthful, concrete **spacetime anchor**, not to pre-write the Shot List.

For modern real-world scenes, record enough to establish a real place:
- **outdoor**: city + concrete scenic area / street / route / landmark, or a real named public venue;
- **indoor**: preferably city + real named hotel/building/public interior; if a private apartment is desired but no verifiable property is supplied, use at least a real street/route anchor and label the interior truthfully as conceptual/private;
- district/neighborhood alone is not sufficient for an indoor final location anchor.

Do **not** require room numbers, window positions, stair landings, exact shoreline segments, exact corridor turns, or other micro-locations at this stage.

For historical real-world scenes, add the era/period when it materially changes costume, architecture, props or behavior.

For film / TV / game / literature / other named works, record the source work + a recognizable in-world place + era/chapter/world-state when relevant. Do not require the exact corner, doorway, window or platform yet.

For original fictional worlds, record a named world/city/region + named fictional place + era/world-state. The anchor must be concrete enough to establish the world, but still leave room for later photographic staging.

Generic labels such as “酒店 / 公寓 / 街头 / 海边 / 庭院 / 古镇 / 室内 / 户外 / 影棚” are still insufficient by themselves.

### Phase 2 — Group Look / wardrobe planning: shootable zones, not locked Shot points
After requirements are confirmed, preserve the spacetime anchor and may add **2–4 broad shootable zones** inside it (for example: lobby/public lounge/guest-room living area; lakeside path/tree-lined road/stone steps; courtyard/veranda/interior study).

These are candidate zones, not final Shot coordinates. Do not over-specify exact body placement, exact doorway, exact window bay, exact corridor segment, or exact camera-facing node unless the user explicitly asks.

### Phase 3 — Shot List: exact micro-location
Only at Shot List stage should each Shot choose its own `scene_area` / micro-location inside the confirmed anchor. This is where specific stairs, windows, cloister turns, shoreline points, arcade bays, platforms, or room sub-areas are decided.

Never invent a real street number, hotel, apartment, room number, or venue and present it as factual. If a private apartment/interior is desired but no verified real property is supplied, anchor it to a real city + street/route (not merely a broad district) and label it truthfully as `fictionalized_private_interior` or `conceptual_interior`.

When the runtime has web/search access and the Skill itself proposes a public real venue, verify the venue/name/location before presenting it as `verified_current`. Otherwise use `known_public_place_needs_current_verification`.

## D. Shot-level location inheritance

Every Shot must carry both:
1. the confirmed **spacetime/location anchor** inherited from the Look; and
2. the Shot's newly chosen exact micro-location.

The Shot List is expected to add spatial precision. It must not merely repeat a vague location, but it also must not be constrained by micro-locations that were unnecessarily frozen during discovery.

## E. No-compression language

Forbidden when it replaces required detail:
- 其他人同风格
- 其余人类似
- 剩下的人自然互动
- 同上
- 沿用前文即可
- 场景同前
- 服装统一协调即可

Shared rules are allowed, but individual implementation must still be written.


## F. Direction selection is the only forward confirmation gate

自主模式中，用户对 A/B/C 的选择即视为允许继续完成本主题方案。选择方向后：
- 立即展开完整逐人 Look；
- 保留时空锚点并补充可拍区域；
- 立即进入姿势与情绪规划；
- 立即生成默认 8 Shot；
- 不再设置“Look 再确认一次 / Shot 再确认一次”的阻塞门槛。

用户随后提出修改时按 revision 处理。自主模式实际生图仍需用户明确提出。

抽卡模式则由 AI 自动选择方向并一路完成到 1 张自适应布局八宫格。

## G. Location specificity is monotonic

Once the user has selected or accepted a named venue, street, scenic area, in-world place, or historical place, later artifacts may keep it, refine it, or explicitly replace it. They may not silently generalize it.

Examples of forbidden regressions:
- 上海外滩 W 酒店客房类型空间（参考锚点） → 精品酒店套房
- 厦门鼓浪屿临海老别墅区域 → 海边民宿
- 《红楼梦》大观园·潇湘馆 → 古风庭院

If a named place was only an example/reference rather than the execution venue, preserve it explicitly as `reference_location_anchor` rather than dropping it.

## H. Default world-famous location when the user leaves location blank

For ordinary modern real-world photography, a missing user location is **not** a reason to downgrade to “海边 / 酒店 / 街头 / 民宿 / 公寓” and is not, by itself, a reason to ask another confirmation question.

The Skill must:
1. create a geographically diverse pool of theme-compatible, globally recognizable real places;
2. randomly select one real named place;
3. use it in the first direction draft and preserve it through the detailed confirmation unless the user changes it;
4. keep the selection compatible with privacy, costume, climate, shoot type and relationship mood;
5. choose a different place when the user requests a location reroll.

For outdoor photography, the fallback should normally be a famous landmark / scenic destination / historic urban area / natural landscape. For indoor photography, use a famous named hotel/building/public interior, or a truthful conceptual private interior anchored to a famous real street/area when no verifiable private property is available.

This fallback never overrides explicit user location, historical/period context, a named film/game/anime/literary work, or an original fictional world. Those use their own real or in-world locations.

When web/search is available, verify a self-proposed public real place before calling it current/verified. Never assume photography access or commercial permits.

## I. Interaction mode does not change quality

`user_directed` 与 `card_draw` 共享同一专业 pipeline 与所有质量下限。

- `user_directed`：只在 A/B/C 方向节点要求一次用户选择；之后完整推进文字方案，出图仍需明确请求。
- `card_draw`：AI 自动完成方向、Look、姿势/情绪与 Shot，并直接生成 1 张自适应布局八宫格。
- 抽卡模式不得输出 8 张独立图片作为默认结果。
- 模式不得被包装成首轮 A/B 菜单；A/B/C 只属于方向卡。

## J. Pose / Emotion quality contract

Shot 规划采用分层模型：
`动作意图 → 关键身体力学 → 人物关系/接触 → 情绪动机 → 景别适配`。

- 身体力学只保留当前景别真正决定姿势成立的 2–4 个关键点。
- 可按需涉及脚位、支撑脚/放松脚、脚尖/膝盖方向、重心落点与转移、骨盆、肩线、躯干倾斜/扭转、脊柱延展、手部支撑和环境接触。
- 全身镜头重点脚位、腿部、重心；半身镜头重点肩线、躯干、手；近景/特写不得强行描述镜头外身体部位。
- 做姿势家族语义去重：只更换扶靠物、道具或表面而承重结构 / 身体主轴 / 移动方式 / 接触模式相同，仍视为同一姿势家族。
- 情侣增加接触关系拓扑：主动/回应、身体距离、接触点、身体朝向、重心响应、视线关系。
- 情绪不使用固定 few-shot 或硬编码词表；必须从当前主题、关系、场景和叙事动态生成。


## 宫格生成契约
- 生成 8 宫格 / 6 宫格时不指定单格比例、单格尺寸或整板比例。
- 只要求格数正确、每格清晰独立、整体可读，不出现明显狭长切条。


## Editorial Hairstylist Gate (2.24.20)
- Beauty-prep hair is exploratory only.
- Every formal shoot Look needs a concrete hairstyle design after theme/scene + wardrobe are known; hair length, straight/curly texture, parting, bangs/fringe and silhouette are open design variables unless the user explicitly locks them.
- The design must be executable, not a generic instruction to “optimize hair”.
- Final rendering follows the confirmed hairstyle design unless the user explicitly changes it.


## Formal makeup artist gate
- Every formal shoot must include an Editorial makeup artist plan, whether or not reference beauty-prep was used.
- Makeup planning includes explicit skin optimization plus theme-adaptive makeup design.
- Default skin cleanup: 清透自然妆容，淡化斑点、泛红、肤色不均与临时小瑕疵；轻微弱化黑眼圈/提亮气色 as needed.


## 通用摄影关键词
- 所有摄影拍摄类型均在可复制方案与最终生图提示词中原样加入：**高级摄影师风格，创意构图，强烈的戏剧张力**。
- 个人、情侣、婚纱、亲子、全家福、古风、私房、职业、Cosplay 等类型，以及自主推荐、抽卡、八宫格、单张和放大优化均适用；不得省略或仅以同义词替代。
- 通过机位、空间层次、光影和情绪落实关键词；继续遵守已确认的人物身份、服装、妆发、画幅及 Shot 动作约束。
- 保持现有“先三方案选向 → 八宫格预览 → 按需单张/放大”的交付流程。
