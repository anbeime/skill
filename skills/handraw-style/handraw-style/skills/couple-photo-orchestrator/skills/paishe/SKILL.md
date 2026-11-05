---
name: couple-photo-shooting-planner
description: Turn confirmed one-person or multi-person portrait styling handoffs into detailed eight-shot plans, numbered grids, and selected detail-render briefs without reducing per-participant specificity.
version: 2.24.26
---

# 任意人数人物摄影与 8 宫格 Shot 板

## 通用摄影关键词
- 所有摄影拍摄类型均在可复制方案与最终生图提示词中原样加入：**高级摄影师风格，创意构图，强烈的戏剧张力**。
- 个人、情侣、婚纱、亲子、全家福、古风、私房、职业、Cosplay 等类型，以及自主推荐、抽卡、八宫格、单张和放大优化均适用；不得省略或仅以同义词替代。
- 通过机位、空间层次、光影和情绪落实关键词；继续遵守已确认的人物身份、服装、妆发、画幅及 Shot 动作约束。
- 保持现有“先三方案选向 → 八宫格预览 → 按需单张/放大”的交付流程。


用于选定 `THEME-xxx` 的 confirmed styling handoff。支持单人、情侣、家庭、朋友群像、婚礼派对、团队、角色群像与任意人数。

## 入口条件

只有以下条件全部满足才可开始：
- `look_group_confirmation.status: confirmed`
- `handoff_to_photography_skill.ready: true`
- 所有待拍 Look 为 `confirmed`

每次建立 Shot 板必须冻结该 Look 的：
- 完整 participant roster
- 每个人各自服装
- 人物关系描述（情侣/多人必填，包含角色层级与互动基础）
- 群体搭配 / 人物关系
- 作品 / 时代语境
- 场景 Location Anchor（真实/作品/虚构时空锚点 + 必要作品/时代信息；微点位由 Shot 自己决定）
- 避免项

这些都是不可替换的视觉锁定。


## 模式感知

读取当前 `interaction_mode`：

- `user_directed`：方向一旦由用户选中，直接完成姿势/情绪规划与 8 Shot，不再等待 Shot 二次确认；只有实际生图仍需用户明确提出。
- `card_draw`：完整生成 8 条并自动审阅，不等待用户，随后直接生成 **1 张自适应布局八宫格结果**。默认不得生成 8 张独立图。

抽卡模式绝不能跳过 Shot List 或用“随机动作”替代逐人调度。

每一次实际图片输出后，除非用户明确说“只出图 / 不要文案”，都必须生成可直接发布、可复刻、可带来二次调用的传播型分享文案。自主模式与抽卡模式使用完全相同的传播标准。

分享文案属于**外部传播内容**，不是内部状态回执。不得在图片后追加“当前处于抽卡模式 / 切换自主模式 / 新卡已生成 / 抽卡结果”等工作流提示，也不得把这些提示混进分享文案。

默认分享结构固定为：`【分享文案】` → 1–2 句情绪/画面钩子 → 强制可见标题 `复刻提示词` + 可复制调用句 → 4–7 个逐个带 `#` 的 Hashtag → 1 句行动 CTA。复刻提示词以 `@当前Skill名` 开头，浓缩当前拍摄类型、时空/地点、关键场景/时代、主色/造型、人物关系情绪与摄影气质，并保留必要自由度（例如“动作随机”），但不得写成长 Prompt 或暴露内部字段。CTA 必须动态生成，目的是让外部读者愿意继续抽卡、选时空或用自己的关键词复刻。传播模板见 `templates/share-copy.md`。

## 类型路由

- 2 人且 relationship preset 为情侣：可参考 `qinglv.txt`
- 仅 2 人、且中心为婚礼新人并以婚纱仪式为核心：可参考 `hunsha.txt`
- 1 人或 3 人以上群像（包括新人 + 伴郎伴娘 / 家庭）：优先参考 `qunxiang.txt`，再叠加婚礼仪式语义；不得让 `hunsha.txt` 的双人结构覆盖多人 roster

模板只是摄影语言参考；真正约束来自 confirmed handoff。

## Pose & Emotion Planning

在 8 Shot 前先执行 `references/pose-emotion-contract.md`。姿势按“动作意图 → 关键身体力学 → 人物关系/接触 → 情绪动机 → 景别适配”规划。情侣/多人必须读取并继承上游 `relationship_description`，Shot 级接触与距离变化不能与已确认关系结构冲突。

- 每 Shot 只写当前景别需要的 2–4 个关键身体力学点。
- 全身才重点写脚位/承重/重心；半身、近景不强写不可见部位。
- 情侣必须规划接触拓扑。
- 8 Shot 做姿势家族语义去重。
- 情绪动态生成，不使用固定 few-shot / 固定情绪词库。

## Shot List 固定为 8 条

每个待拍 Look 直接设计恰好 8 条 Shot。

每条基础字段：
- `title`
- `purpose`
- `action_event`：当前镜头正在发生的事件
- `pose_structure`：姿势结构，不只是姿势标签
- `key_support_weight`：当前景别真正必要的承重 / 重心 / 支撑信息
- `relationship_contact`：人物之间或人与环境的接触关系
- `emotion_motivation`：从当前主题与事件生成的情绪动机，不套固定词表
- `gaze`：视线关系
- `framing_adaptation`：姿势如何服从当前景别
- `purpose`
- `location_context`：完整地点锚点，不能只写‘室内/街头/庭院’
- `scene_area`：该具名地点内的本 Shot 微观位置
- `era_or_world_context`：历史/作品题材必填；现代现实可写 contemporary
- `interaction`
- `shot_size`
- `composition`
- `lighting`
- `continuity`
- `avoids`
- `prompt`

新 schema 还必须写：
- `participants_present`: 本 Shot 出镜人物 ID 列表
- `participant_directions`: **每个出镜人物恰好一条**逐人调度

`participant_directions` 至少说清该人的动作 / 身体朝向 / 视线表情 / 手部或道具关系中与本 Shot 有关的内容。

### 多人 Detail Floor

当 confirmed roster > 2 人时：
- `participants_present` 必填。
- `participant_directions` 必填。
- 每个出镜人物必须逐人描述，不能写“其他人自然互动”“其余人站在后面”等压缩词。
- 8 条 Shot 的并集必须覆盖所有 confirmed participants。
- 默认至少有 1 条完整群像 Shot，除非用户明确要求全组不合影。
- 可以安排 subgroup / solo Shot，但必须明确谁出现、谁不出现。
- 同一 Shot 中不得增人、漏掉声明出镜的人、复制人或交换服装。

人数越多，Shot 文档可以越长；不能降低逐人调度质量。



### Shot Location Floor

地点在 Shot 阶段**开始增加微观精度**，同时不得丢失前期确认的时空锚点。

每条 Shot 必须同时回答：
1. **这是哪里**：继承 confirmed Look 的时空锚点；
2. **在这个地点的哪里拍**：由本 Shot 新决定 `scene_area`，写到具体空间节点；
3. **处于什么时代/作品状态**：历史、古风、影视、游戏、文学等必须写 `era_or_world_context`。

例如 confirmed scene 只锁“法国巴黎第六区 Saint-Germain-des-Prés 的 Hôtel Lutetia”，Shot 阶段再分别把不同镜头落到“公共沙龙靠高窗区域 / 楼梯转角 / 客房起居区”等具体节点。前期不需要提前决定这些节点。

作品题材不能从“《红楼梦》大观园·潇湘馆”退化成“古风庭院”。


## Shot 差异

每条相对其他 Shot 至少改变三项：
- 互动微事件
- 参与者组合
- 景别 / 构图
- 空间层次
- 光线
- 环境元素

同一标准互动一组内最多一次。

## 冻结服装

脚本会把 `visual_lock.participant_outfits` 自动写入每一条最终 prompt 与 continuity。

Shot 只能改变动作、机位、构图、光线与环境细节，不得改写任一人物服装。

具名作品 / 游戏 / 动漫 / 历史主题必须保持每个人在世界中的身份逻辑，不能让部分人退化成无语境现代装。

## 文字审阅

保存为 `SHOTBOARD-xxx.md/.yaml`。自主模式直接把完整 8 Shot 展示给用户但不设置阻塞式二次确认；用户明确要出图时进入宫格生成。抽卡模式由 AI 自动检查差异度、姿势家族、人物覆盖、地点继承、动作合理性与视觉记忆点后直接生成宫格。用户在任一模式下都可随后修改任意 Shot 或“再来一批”。

## 自适应 8 宫格

自主模式只有用户明确提出出图后，才把 8 条完整 prompt 编译成一次生成的一张无编号自适应 8 宫格；抽卡模式自动进入此步骤。两种模式默认都只生成 **1 张八宫格**，不一次生成 8 张独立图。

每格必须严格遵循：
- 该格 `participants_present`
- 该格每人的 `participant_directions`
- 每人的 locked outfit
- 人数与身份
- 场景 / 世界观

不得跨格合并人物、服装、动作或道具。模型不得生成文字数字。`register-grid` 只负责叠加准确编号。

### 八宫格生成硬约束
- 生成八宫格时不指定单格比例、单格尺寸或整板比例。
- 只要求恰好 8 格；每格清晰独立、可单独阅读，不出现明显窄条、切条或过度拥挤。
- 不规定列数/行数；AI 自由安排整体布局。
- Post-generation QA：格数错误、边界不清、出现明显狭长切条或整体难读时直接重生成。

### 真人参考图：精修与表情去锁定
### Identity Lock v2｜多格人脸一致性
- 真人项目生成 8 宫格时，不能只在总提示词开头写一次“same person”。必须先生成高优先级 Identity Lock，再在**每一格**的 Shot Prompt 前重新注入本格的身份参考。
- 每格都直接从该 participant 当前合法的 active identity reference 恢复人脸；默认是最初上传原图。禁止让 Panel 2 继承 Panel 1 的生成脸、Panel 3 继承 Panel 2 的生成脸，以此类推。
- 明确禁止 panel-to-panel face evolution / identity interpolation / face averaging。
- 锁定几何包括：脸型和长宽比、额头比例、眼型眼距、眉位、鼻梁/鼻宽/鼻尖、颧骨、嘴宽/唇比例、下颌/下巴、年龄印象和辨识度。妆容、皮肤、表情、灯光只改变表面状态，不改这些身份几何。
- Face Readability Gate：全身、远景、行走、背身回望、倒影等镜头，只要计划露脸，就必须保证真实脸足够清楚、足够大、可识别。
- 背身回望默认让头部及必要上半身转到足以读清完整脸；倒影只是次要元素，真实人物脸是主身份锚点，倒影不得扭曲五官。
- 以上规则不改变 2.24.23 的发型边界：canonical 原图只锁脸，正式发型始终执行锁定的 `hairstyle_design`。

- **身份源不可自动漂移**：每位人物最初上传的原图始终是默认 canonical identity reference。多轮对话后的八宫格、单张 Shot、放大图、精修图或其他 AI 生成图都不得自动替代它。
- **原图只锁脸，不锁发型**：canonical identity reference 只用于保持脸型、核心五官、年龄印象和识别度；原图中的发长、直卷、刘海、分缝、体积、轮廓与发色质感必须默认忽略。正式发型只执行已锁定的 `hairstyle_design`。
- 若某张后续生成图需要用于保持姿势/构图/场景，仅作为 composition reference；最终生图仍必须同时使用原始真人图锁定身份。
- 实际图像工具调用时，如果会话里同时存在原始上传图与后续生成图，身份参考必须显式优先选择原始上传图；不能采用“最近一张图”策略。
- 只有用户明确要求“以后用这张做人物参考”等，才允许切换 active identity reference。
- 参考图只负责锁定身份：脸型、五官结构、年龄感、辨识度；**不把参考图表情当成后续 Shot 的固定模板**。
- 身份锚定不得把参考图发型、发长或发色写成必须保持的身份特征；除非用户明确要求保留。
- 除非用户明确要求复刻参考图表情，否则后续 Shot 必须根据各自的动作、关系和情绪动机自由变化嘴型、笑意强弱、眼神方向、视线落点和头部角度。
- 最终生图必须执行方向阶段已经锁定并由 Look 继承的 **Editorial 专业发型师设计**，不得再用一句“根据脸型自行优化发型”取代正式发型设计。
- 原参考图发型不属于身份锚点；精修身份参考图发型也不自动锁正式拍摄发型。
- 无论是否调用参考图美化，最终生图必须执行方向阶段已经锁定并由 Look 继承的 **Editorial 专业化妆师设计**；最终生图严格执行已确认的皮肤优化与正式妆面。
- 明确纯男性项目默认不加；用户明确要求自然皮肤 / 原生肤质 / 不要精修时关闭。
- 不再自动展开任何皮肤细节或肤色描述；不得仅凭外貌自行推断族裔触发。



## 2.24.20 正式妆发执行
- 已确认正式发型可包含与参考图完全不同的发长、直卷、刘海与轮廓；最终渲染必须执行，不要偷偷回退到参考图发型。
- 已确认正式化妆师方案必须进入 Shot Board / detail render prompt，包含皮肤优化与主题妆面。


## 2.24.21 Share Card Compiler Hard Gate
- Share Card 是图片渲染前的正式节点，不再依赖“图片完成后补文案”。
- Shot List 完成后、调用任何图片生成之前，先编译 `story_card_name / share_hook / reproduction_prompt / share_hashtags / share_cta` 并保存为 ready。
- 用户明确“只出图 / 不要文案”时，把 Share Card 标记为 skipped；ready 或 skipped 才允许进入图片渲染。
- 默认用户可见顺序：先显示 Share Card，再触发图片生成；因此图片工具结束后无需追加文字。
