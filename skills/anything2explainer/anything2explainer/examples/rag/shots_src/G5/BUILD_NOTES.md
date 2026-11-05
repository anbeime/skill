# G5 构建记录（第 3 章上半：SC21–SC25 / S21–S25，帧 3708–4676）

预览合成 `RagG5`（= G0 覆盖层 + 本组）。所有镜头 `N = useCurrentFrame() + F0`，纯函数动画，随机只用 `rnd`。

## 镜头表
| id | 帧 | 文件 | 内容 / 节拍 |
|---|---|---|---|
| SC21 提问的那一刻 | 3708–3821 | `SC21.tsx` | 左上 DBIcon「知识库」缩放入场(3710) + 绿勾 draw-on(3716)；聊天输入框 720×80 @(640,420) slideUp(3718)，光标 8 帧一闪；3741 起每 2 帧 1 字打出「差旅报销的上限是多少？」；打完(3763)发送按钮灰→紫 11 帧 + emphasisPulse；右上考卷 3775 缩放入场、3783 封面 scaleX 翻开 + 「考试开始」glitch。末帧不离场（SC22 硬切，流程轨 3822 出现）。y 范围 246–460（本镜头无流程轨，可用 y 110–620）。 |
| SC22 理解问题 | 3822–4056 | `SC22.tsx` | 左 (240,400) 用户气泡「报销上限？」slideUp(3824)；3865 边框闪灰 14 帧后定为灰边 + 灰字「原话含糊」；三条分支箭头（beat−6 起 14 帧 draw-on）→ 三卡 GlitchIn：3909「改写」差旅费报销标准与上限 / Query Rewriting；3948「拆分」住宿上限？交通上限？/ Multi-Query；3982「假想答案」灰底斜体「差旅住宿每天不超过…」/ HyDE；4020 三线汇合到 (900,400) → 箭头 → DBIcon「知识库」缩放入场(4026)。4045 起 12 帧下摇+线性淡出离场。主区 y 213–587。 |
| SC23 语义检索 | 4057–4225 | `SC23.tsx` + `vspace.tsx` | 坐标平面 wipe（18 帧左→右）+ 40 灰点 1 帧错峰亮起(4059)；问句 Pill「差旅报销上限？」自左滑入(4065) → ArrowH(4079) → 紫「Embedding」盒 glitch(4085)；4093 橙查询点自盒中沿二次贝塞尔弧飞入 (620,390)，落点涟漪；4137 紫圈 r90 draw-on 14 帧，三近邻点每 6 帧依次灰→紫放大，牵引线 + 标签「报销标准 §3 / 住宿上限 / 交通补贴」glitch；4192 右上「语义检索」紫 Pill + Exo 2「Dense Retrieval」。4214 起 12 帧离场。 |
| SC24 盲区：精确匹配 | 4226–4414 | `SC24.tsx` | 问句 Pill「型号 X-2000B 的保修期？」自左滑入(4234)，X-2000B Orbitron 橙字；4282 橙高亮块 HL_W 21 帧左锚展宽 + glitch，字变白；4260 三张结果卡 2 帧错峰 slideUp，右上 Orbitron 灰分数 0.83/0.81/0.79 20 帧计数；4300 右侧「X-2000B 保修 2 年」灰卡淡入 40% + ±1.4° 轻晃；4377/4383/4389 红叉依次 8 帧 draw-on，「漏掉了」灰字 glitch(4380)。4403 起 12 帧离场。 |
| SC25 混合检索 + RRF | 4415–4676 | `SC25.tsx` | 4423 中央紫 Pill「混合检索」+「Hybrid Search」glitch；4492 左列「向量检索」Pill 自左滑入 + 4 卡（排名 1–4）2 帧错峰 slideUp；4526 右列橙 Pill「BM25」+ 4 卡，其中「X-2000B 保修 2 年」橙边高亮；4594 八张卡沿弧线（bez2，20 帧 easeInOutPow 2.5，按融合名次 2 帧错峰）汇入中央 5 槽（重复的 §3 与两张淘汰卡飞行后段淡出），到位后白边→亮紫边 11 帧、名次改为融合名次；同帧公式逐 token（每 3 帧）出现：`score(d) = Σ_r 1/(k + rank_r(d))`（Times New Roman Italic 34/30，Σ 46），其下灰字「RRF · k = 60」(4618)。末帧不离场（SC26 硬切）。 |

`index.ts`：`SHOTS_G5` 5 条首尾相接（3708–3821 / 3822–4056 / 4057–4225 / 4226–4414 / 4415–4676），`BG_G5 = []`（无背景覆写）。

## 复用的图元 / 组内新增
- `ui.tsx`：Box / Pill / CText / TechText / Svg / LineArrow / ArrowH / Check / Cross / DBIcon / DocIcon / 调色板 / slideUp / scaleIn / fadeIn / fadeOut / exitAccel / stagger / GLOW_PURPLE_S / PILL_SHADOW。
- `common`：GlitchIn / rnd / clamp01 / powOutRemain / BEZ_SCALE_IN / easeOutCubic / easeInOutPow / emphasisPulse / FONT_HEAVY / FONT_TECH / FONT_ORB / FONT_SERIF。
- 组内 `g5util.tsx`（可考虑迁入 ui.tsx）：`mixHex`（hex 混色）、`mixK`（灰→紫 11 帧曲线 MIX）、`hlW`（R3 HL_W 21 帧左锚展宽）、`bez2`（二次贝塞尔）、`DrawLine` / `DrawCircle`（SVG dasharray draw-on）、`Anchor`（中心锚缩放/位移包裹，transformOrigin 0 0）。
- 组内 `vspace.tsx`：`VSPACE`（网格 x 240–1040 步 40 / y 190–600 步 41，seed 17，40 灰点，中心 (620,390) r110 挖空，点间距 ≥26）、`VGREY`（点表）、`VNEIGHBORS`（3 枚近邻点 (572,338)/(690,420)/(580,452)）、`VectorPlane`（网格 clipPath wipe + 灰点 1 帧错峰亮起）。

## 关键参数
- 离场统一：`opacity = fadeOut(n,12)`，`dy = 0.6·n²`（SC22/23/24，在句尾前 ~10 帧起，末帧全透明后 return null）。
- 入场：GlitchIn 12 帧（卡片/标签/标题）；slideUp Δ300/260/220（框/卡）；自侧边滑入 `Δ·powOutRemain(n,22,2.5)`（Pill）；scaleIn 21 帧（DBIcon）。
- 分数计数：`easeOutCubic((n−4)/20)` × 目标值，toFixed(2)。
- 文本语境统一「差旅报销」：问句「差旅报销的上限是多少？」；结果「差旅报销标准 §3 / 住宿上限说明 / 交通补贴规定 / 差旅补充规定 2025」。X-2000B 为 S24/S25 的精确匹配示例（分镜表指定）。
- 事实依据（research/RAG调研.md）：Query Rewriting / Multi-Query / HyDE（§3.1）；BM25、RRF 公式 `Σ_r 1/(k+rank_r(d))`、k=60（§2.7，Cormack 等 SIGIR 2009）；「Hybrid search」「Dense retrieval」「Reciprocal Rank Fusion (RRF)」见 §8 术语表。SC24 的相似度分 0.83/0.81/0.79 为分镜表给定的示意值（非调研数字）。

## 自检
- `npx tsc --noEmit` 通过（最后一次：SC24/SC25 注册后）。
- 30 帧测渲：`npx remotion render build_dev_g5_6 RagG5 /tmp/rag_test_G5 --sequence --image-format=jpeg --frames=4136-4165`（SC23 网格+40 点+圆圈，最重镜头）**10.0 s / 30 帧 ≈ 3.0 fps**，在 4–12 s 区间。
- still（`rag/stills/G5/`，共 50 张 + 2 张组界）：
  - SC21：3709/3720/3735/3752/3770/3790/3821 —— 3720 输入框 slideUp 途中穿过字幕带（允许的入场路径）；3752 打字中；3790 考卷翻开、发送键紫脉冲；3821 末帧不离场。
  - SC22：3827/3840/3870/3915/3955/3990/4030/4050/4056 —— 3870 气泡已灰化；3990 三卡到位（底卡下缘 587 < 620）；4030 DBIcon 缩放中；4050 离场中；4056 末帧全透明。
  - SC23：4058/4066/4075/4090/4102/4112/4145/4160/4175/4200/4220/4225 —— 4075 网格 wipe 完成、点亮起中；4102 橙点飞行中；4160 圈 + 近邻变紫；4200 全部标签 + 语义检索；4220 离场中。
  - SC24：4227/4240/4268/4290/4320/4380/4392/4408/4414 —— 4290 高亮块展宽中；4320 漏掉卡 40% 淡入；4392 红叉依次 draw-on；4414 末帧 ≈8% 残影（下一帧 SC25 空场入场）。
  - SC25：4416/4430/4500/4535/4560/4600/4610/4612/4625/4630/4650/4676 —— 首版「Hybrid Search」副标与融合列第 1 卡重叠、「融合结果」字压在 Σ 上 → 已改：融合列下移至 cy 296–480（pitch 46）、删去「融合结果」字、公式中心 556、RRF 字 606（下缘 616 < 620）。4630/4676 复核通过。
  - 组界：`boundary_3708_first.png`（SC21 首帧仅背景，章节卡 3707 已出、HUD 由 G0 在 3716 起）/ `boundary_4676_last.png`（SC25 末帧满画面，供 G6 SC26 硬切衔接）。
- 检查项：无内容进入 y<175（第 3 章）/ y>620；无溢出画布；紫/橙/灰语义符合调色板；英文拼写核对（Query Rewriting / Multi-Query / HyDE / Embedding / Dense Retrieval / Hybrid Search / BM25 / RRF）；元素均在字幕块起始 −6…+3 内出现。

## 未完成 / 降级
- 无降级。SC21 storyboard 的「「开始」考卷小图标翻开」实现为封面 scaleX 翻页（8 帧）+ 左侧翻开页 6 帧展开。

## 需主会话决定 / 对共用层的建议
1. **VSPACE 统一**：开工时 `G4/SC17.tsx` 不存在，向量平面在 `G5/vspace.tsx` 实现并导出 `VSPACE / VGREY / VNEIGHBORS / VectorPlane`。建议 G4 的 SC17 直接 `import {VectorPlane, VNEIGHBORS} from '../G5/vspace'`（把 VNEIGHBORS 作为灰点传 `extra`，再叠自己的两枚紫点 (600,380)/(650,400)，二者都在挖空区 r110 内，不会与灰点撞）；或由主会话把 vspace.tsx 挪到 `src/rag/` 共用位置。
2. 「语义检索」的英文副标用了术语表里的 **Dense Retrieval**（调研文档无 "Semantic Search" 原文）；若想更口语可改为 Semantic Search，需先在调研补依据。
3. `g5util.tsx` 的 `mixHex / mixK / hlW / DrawLine / DrawCircle / Anchor` 是通用件，可迁入 `ui.tsx` 供其他组用。
4. 渲染中途遇到 **磁盘满（ENOSPC）**：`$TMPDIR/remotion-webpack-bundle-*` 累积 6+ GB，已清理（>3 分钟的）；各组 `build_dev_*` 也各 0.8 GB，建议主会话定期清理。按主会话新规则：still 只用 `rag/script/still.sh`，tag 固定 `g5`（精简 bundle ≈117 MB），改代码后 `rm -rf remotion/build_dev_g5` 再跑；旧的 `build_dev_g5_*` 已删除。已用新 bundle 复核 3790/4650 两帧。
5. `rag/script/still.sh` 在我使用期间被并发修改（加了 `--public-dir public_rag`，一次出现 "command not found: --out-dir" 的临时断行），bundle 与 still 仍成功；主会话请复核脚本当前状态。

## QC v1 修复（rag/qc/qc_v1_C3.md · G5 条目，2026-09-06）
still：`rag/stills/F56/`（tag `g56`，与 G6 共用一个 bundle）；`npx tsc --noEmit` 通过。
| QC 条目 | 严重度 | 处理 | 复核 still |
|---|---|---|---|
| SC25→SC26 组界 4676\|4677 | 中 | SC25 新增 `T_EXIT=4664`：12 帧下摇 `0.6·n²` + 线性淡出，4676 全透明（原「末 2 帧不离场」改掉）；SC26 侧由 G6 把入场提前到 4685 承接 | 4670（半透明下摇中）/ 4676（空场） |
| SC23 4093 橙点被盒子盖住 | 中 | 查询点 + 落点涟漪移出 `VectorPlane`，改画在 Embedding 盒之上的独立 `<Svg bloom={false}>`；4094 起在盒内可见长出，4096 已明显，4101 飞出盒外 | 4093 / 4096 / 4101 |
| SC21 3718–3723 输入框穿字幕带 | 低 | `slideUp Δ 300→240`，`opacity = fadeIn(n−3, 6)`：3718–3721 不可见，3722 首次可见时框底 ≤605（<637） | 3720（不可见）/ 3724（框 488–568） |
| SC22 4040 Exo 2 副标 <22px | 低 | Query Rewriting / Multi-Query / HyDE 19→24px（右对齐宽度系数 9.2→11.6/字，cy 上移 1）；「知识库」标签 22→24（SC21/SC22） | 4040 |
| SC23 4205「Embedding」<22px | 低 | Embedding 21→24；Dense Retrieval 22→24（cy 269，与 Pill 不撞） | 4205 |
| SC24 4390 红叉压标题 | 低 | 叉 72→60，叉心 y 400→418（卡片中下部灰线区）；标题 ink 356–378 完整可读。附带：相似度分 17→18、徽标 64→70 宽 | 4398 |
| SC25 4660 RRF / 序号字号 | 低 | 「RRF · k = 60」20→24（cy 605，下缘 617 <620）；卡序号 Orbitron 20→22 | 4660 |
| SC21 3800「知识库」「考试开始」≈21px | 低 | 22→24 | 3724 |
| 半角 ? → 全角 ？ | 低 | **无需修**：G5 全部问句源码已是全角「？」（grep 无半角 `?` 文本）；QC 观感来自 Noto Sans SC 全角问号左对齐字形 | — |
- 未修：无。SC25 离场期间（4665–4675）公式/RRF 字随整镜下摇短暂进入 y>620 属离场路径，与 SC22/23/24 一致。

## 闪烁整改（用户裁定 2026-09-06「不要给每段出现的字都加闪烁，只给重点加」· RULES §8）
- 改前 **14 处 `GlitchIn`** + 1 处手写闪烁（SC22 气泡边框/字色 14 帧 rnd 白灰闪）；改后 **2 处 `GlitchIn`**，其余全部换 `SoftIn`（ui.tsx，8 帧淡入 + 10px 上浮），入场帧 f0 一律不变。
- 保留（白名单）：**SC23「语义检索」紫 Pill**（4192）、**SC25「混合检索」大 Pill**（4423）。两处原本与英文副标（Dense Retrieval / Hybrid Search）同包在一个 GlitchIn 里，现拆开：Pill 仍 glitch，副标改 SoftIn（同帧）。
- 换掉的：SC21「考试开始」(3783)；SC22「原话含糊」(3865)、三张改写/拆分/假想答案卡 (3909/3948/3982)；SC23「Embedding」盒 (4085)、三近邻标签 (4149/4155/4161)；SC24 X-2000B 橙高亮块 (4282，`SoftIn dy=0` 纯淡入 + 原 HL_W 展宽)、「漏掉了」(4380)；SC25「Hybrid Search」(4423)、「RRF · k = 60」(4618)。
- SC22 手写闪烁：气泡边框 + 「报销上限？」字色原为 3865 起 14 帧 `rnd` 白/灰随机闪，改为 11 帧白→灰平滑变色（`mixK`/`mixHex`，与发送按钮同曲线），语义（"原话含糊 → 变灰"）与节拍不变。
- 组内图元（g5util / vspace）本身不含 GlitchIn，无需加开关。
- `npx tsc --noEmit` 通过。still：`rag/stills/X56/`（tag `x56`，与 G6 共用一个 bundle），每处改动出入场中段 f0+4 与完成 f0+12 两张：3787/3795、3869/3877、3913/3921、4089/4097、4153/4161、4196/4204、4286/4294、4384/4392、4427/4435、4622/4630。
- still 复核结论（Read 逐张看过 20 张）：所有 SoftIn 处 f0+4 约 80% 透明度、位置略低 ~2px，f0+12 完全到位，尺寸/坐标与改前一致，未穿字幕带；3869/3877 气泡边框与「报销上限？」由白平滑转灰，无闪；4196/4427 白名单 Pill 仍呈 glitch 序列（n=4 处半透），其英文副标已为软淡入。无需回修。
