# G4 BUILD_NOTES（第 2 章下半：SC16–SC20 / S16–S20，帧 2686–3662）

预览合成 `RagG4`；帧号 N = useCurrentFrame()+F0（1 起含端点）。第 2 章流程轨（y 112–160）由 G0 绘制，本组内容全部放在 y 175–620。

## 镜头表
| id | 帧 | 文件 | 内容 | 节拍对齐 |
|---|---|---|---|---|
| SC16 向量化 | 2686–2860 | `SC16.tsx` | 左 ChunkCard(active)「文本块」→ 白箭头 draw-on → 中央 Embedding 盒（紫填充 + 白 3px 虚线边 220×110，Exo 2 白字「Embedding」+「模型」）→ 白箭头 → 右侧等宽数字串「[ 0.34, 0.48, … ]」2 帧错峰出现 → 「× 1024 维」Orbitron 计数 384→1024 | 2694 卡片滑入 / 2704 箭头 / 2720 盒 glitch / 2742 箭头 2 / 2779 数字 / 2800 计数 / 2853 起 8 帧淡出+下摇 |
| SC17 向量空间邻居 | 2861–3033 | `SC17.tsx` + `vspace.ts` | 2D 网格（#4A4A4A 1px，x 240–1040 / y 195–595，格 40）自左 wipe；40 个灰点 rnd 顺序 1 帧错峰亮起；三对近点细灰虚线；两紫点「退款流程」「怎么把钱要回来」+ 远点「年假规定」（灰）；紫线段 + 虚线高亮圈 + 「邻居」紫 Pill；角注「2D 投影示意」 | 2869 网格 / 2878 灰点 / 2902 近点连线 / 2931 紫点 + 标签 / 2950 远点 / 2988 连线·圈·「邻居」+ 远点闪一次 / 3026 起 8 帧淡出 |
| SC18 建索引 HNSW | 3034–3298 | `SC18.tsx` | 左：12 点竖列 + 「线性扫描」+ Orbitron「1 0000 0000 ×」，白光标下扫两遍 → 红 Cross → 整列压暗；右：三层平行四边形平面（底→顶 2 帧错峰滑入），点阵 rnd 亮起 + 层内近邻图边，「HNSW」/「Hierarchical NSW」Exo 2 紫；橙色查询路径逐跳 draw-on（顶 4 跳 / 中 7 跳 / 底 11 跳，跳 2 帧、层间下降 3 帧虚线，共 50 帧），目标点紫脉冲 + 光环，「跳转 ×N」Orbitron 计数只计跳转（终值 ×22，对应解说「几十次跳转」） | 3042 列 / 3073 大数 / 3076 扫描 / 3117 Cross / 3130 平面 / 3136 标签 / 3219 路径 / 3269 到达 / 3291 起 8 帧淡出 |
| SC19 向量数据库 + 权限 | 3299–3482 | `SC19.tsx` | 中央 DBIcon w160「向量数据库」（顶面紫）；左侧三张 ChunkCard 自左滑入，贴两枚标签（「来源：员工手册 p.12 / 差旅补充规定 2025」白、「ACL：财务组」橙），沿弧线飞入库（18 帧/张，错峰 12 帧，库轻微脉冲）；库顶「ACL」橙标；右侧两个用户图标（圆头+肩线）「财务组」实线箭头 + 绿勾 /「实习生」灰虚线箭头 + 红叉；3432 库紫柔光脉冲 | 3307 库 / 3312 卡 / 3345 标签 / 3360 飞入 / 3402 ACL / 3405 用户 / 3413–3436 箭头·勾·叉 / 3432 脉冲 / 3475 起 8 帧淡出 |
| SC20 增量更新 | 3483–3662 | `SC20.tsx` | 左 DocIcon「差旅补充规定」+ Orbitron 角标「v1」→ scaleX 翻页 8 帧 →「v2」紫，文中两行改动变紫；中央双弧循环箭头（紫）draw-on 18 帧后每帧 2° 旋转 + 「增量更新」紫 Pill；右 DBIcon「知识库」，库内灰卡「过期」+ 珊瑚色删除线 wipe → 落下淡出 → 新紫卡「v2」自上落入；旁注「只重嵌入改动的块」 | 3491 文档·库 / 3505 翻页 / 3531 箭头·循环·Pill / 3582 过期卡 / 3590 删除线 / 3606 落下 / 3612 新卡 / 3661–3662 整组快速淡出（0.55 → 0.2）接 3663 章节卡 |

相邻镜头首尾相接（2860|2861、3033|3034、3298|3299、3482|3483），无重叠帧。`BG_G4 = []`（不覆写星点/雾底）。

## 复用的图元 / 共用层
- `ui.tsx`：CText / TechText / MonoText / Box / Pill / Svg / LineArrow / Check / Cross / DocIcon / DBIcon / ChunkCard，调色板 PURPLE / PURPLE_LIGHT / PURPLE_TECH / ORANGE / CORAL / GREEN / GREY / GREY_MID / GREY_LINE / GREY_LIGHT / WHITE，GLOW_PURPLE_S / TEXT_GLOW，fadeIn / slideUp / scaleIn / exitAccel / abs。
- `common`：GlitchIn（标签/胶囊/大数/计数入场）、rnd（全部随机：向量分量、灰点、HNSW 点阵与亮起顺序）、kf（扫描光标、维度计数）、emphasisPulse（Embedding 盒、库收卡/权限脉冲、HNSW 目标点）、easeOutCubic / easeInOutPow / powOutRemain / clamp01、FONT_ORB / FONT_HEAVY。
- 组内自建（未改 ui.tsx）：`SC19` UserIcon（圆头 + 肩线 SVG）、`SC20` ArcArrow（弧 + 三角头，dashoffset draw-on）、`SC18` 平行四边形平面 + (u,v)→画布映射。

## 可导出常量（G5 SC23 复用）
`src/rag/shots/G4/vspace.ts`：`VSPACE`（网格范围/格距/seed/两紫点 A、B/远点 FAR/四个标签框/高亮圈）、`VSPACE_POINTS`（40 个灰点 {x,y,order}，拒绝采样避开紫点/远点/标签框，点距 ≥24）、`VSPACE_PAIRS`（三对近点索引）、`vspacePoints()`。SC17.tsx 亦 `export {VSPACE, VSPACE_POINTS}`。G5 直接 `import {VSPACE, VSPACE_POINTS} from '../G4/vspace'` 即得同一分布；若要在 SC23 把「查询点」放进去，建议放 (640,300) 附近（该区无灰点/标签）。

## 关键参数
- 入场：卡片/平面 `slideUp(n,300)`（22 帧 powOutRemain 2.5）+ 10 帧 fadeIn；图标 `scaleIn` 21 帧；标签 `GlitchIn` 12 帧；箭头 `easeOutCubic(n/14–16)` 自根部长出；灰点/点阵 1 帧错峰 8–10 帧缩放。
- 离场：SC16–SC19 末 8 帧线性淡出 + `exitAccel(n,0.5–0.6)` 下摇；SC20 末 2 帧 0.55/0.2（分镜表要求「末 2 帧 exitFade」，6.7%/帧肉眼不可见，改为快淡以让 3663 章节卡干净入场——如需严格 exitFade 改 `exitOp` 一行）。
- SC19 卡片飞入：`e = easeInOutPow(2.2)(t/18)`，dx/dy 线性插值 + 弧拱 `−90·sin(πe)`，scale 1→0.22，e>0.7 淡出；标签用 `GlitchIn style={{overflow:'visible'}}`（否则被卡片容器裁掉）。
- SC18 路径：22 跳（2 帧/跳）+ 2 次下降（3 帧/次）共 24 段 50 帧（3219–3269）；计数只计跳转（终值 22）。点阵 COUNTS=[8,14,26]，底层路径绕目标 (0.86,0.48) 螺旋收敛。
- 滤镜：仅 `drop-shadow ≤6px`（紫点 ×1、扫描光标 ×1、循环箭头 ×1），无 blur/feGaussianBlur/feConvolveMatrix；单帧 DOM 峰值 ≈ SC18（≈ 37 点 + 46 边 + 12 段 + 12 点）< 250 节点。

## 数字 / 术语依据（research/RAG调研.md §2）
- 384 → 1024 维：§2.5「从 384 维（all-MiniLM-L6-v2）到 4096 维；主流 1024–3072」。
- HNSW / Hierarchical NSW、多层图、上层稀疏下层稠密、对数级查询：§2.6。
- 「1 0000 0000」= 上亿（解说词），非具体统计。
- 元数据（来源/页码/ACL）、权限预过滤：§2.4；增量更新只重嵌入改动块：§2.8。
- 示例文本：全局约束的「员工手册 p.12」「差旅补充规定 2025」；SC17 标签「退款流程」「怎么把钱要回来」「年假规定」按分镜表/解说词。

## 自检
- `npx tsc --noEmit`：G4 文件零错误。全工程当前唯一报错来自 G3 `src/rag/shots/G3/SC15.tsx(121,39) TS2774`（非本组）。
- still（`rag/stills/G4/`，共 56 张 + 2 张 boundary）：
  - SC16：2695/2705/2716/2726/2748/2790/2822/2857/2860 —— 卡片、箭头、盒 glitch、数字错峰、计数、离场均在节拍 ±3 帧内；第一版元素整体偏低，已上移 20px。
  - SC17：2870/2884/2915/2940/2960/3000/3020/3030/3033 —— 网格 wipe、灰点、近点连线、紫点标签、圈 + 「邻居」；第一版「年假规定」标签越出网格右缘，已改到远点下方（`LABEL_FAR`）。
  - SC18：3043/3056/3085/3122/3140/3160/3200/3228/3240/3260/3295/3298 —— 扫描、Cross、平面、点阵图边、路径、目标脉冲；第一版左列 x=300 与右侧空隙过大，改 x=360。主会话反馈后路径由 12 段加长到 22 跳（计数终值 ×22），复核 3245/3266/3284（bundle tag g4）。
  - SC19：3308/3318/3332/3350/3368/3381/3396/3412/3428/3445/3478/3482 —— 标签贴附、弧线飞入、ACL 标、用户图标、勾/叉、紫脉冲；无遮挡字幕带（卡片滑入起点在画外左侧）。
  - SC20：3492/3500/3508/3512/3540/3558/3586/3596/3614/3628/3661/3662 —— 翻页、紫改动行、循环箭头、过期卡删除线、新卡落入、末 2 帧淡出；新卡「v2」角标首版 20px 已改 22px。
  - boundary：`boundary_2686_first.png`（本组首帧，内容尚未入场，仅 G0 层）、`boundary_3662_last.png`（末帧 α≈0.2）。
- 字号：正文/标签 22–28px，无 <22px 可读文字（ChunkCard 未用 15px title）。

## 30 帧测渲（协议 §6）
`npx remotion render build_dev_g4_6 RagG4 /tmp/rag_test_G4 --sequence --image-format=jpeg --frames=3229-3258`（SC18 路径 + 三层 + 左列，本组最重区段）：见下方「测渲记录」。

## 测渲记录（`time npx remotion render build_dev_<tag> RagG4 /tmp/rag_test_G4 --sequence --image-format=jpeg --frames=a-b --log=error`）
- build_dev_g4_5，SC18 frames 3229–3258（机器空闲）：30 帧 **2.73 s**（≈11 fps）。
- build_dev_g4_6（最终代码，其他组同时在渲染，本进程 CPU 占比 37–52%）：SC18 3229–3258 → **6.64 s**（≈4.5 fps）；SC19 3399–3428（卡片飞入 + 标签 glitch + 用户图标）→ **10.85 s**（≈2.8 fps）。两段都在协议 4–12 s 区间内；SC19 段无 blur 滤镜，仅 3 处 ≤6px drop-shadow，慢主要是并行争抢，空闲时复测预计 <5 s。
- 旧 bundle 已由主会话统一清除。后续复现 still/测渲请按新规则：`rag/script/still.sh RagG4 <帧> rag/stills/G4 g4`（tag 固定 `g4`，改代码后先 `rm -rf remotion/build_dev_g4`），测渲输出 `/tmp/rag_test_g4` 看完即删；不要直接 `npx remotion still src/index.ts`。

## 未完成 / 降级项
- SC20 末尾用 2 帧快淡（0.55/0.2）替代字面 exitFade（见上）。

## 对共用层 / 其他组的建议
- `still.sh` 每次 bundle 会在 `$TMPDIR` 留一份 `remotion-webpack-bundle-*`（22–66 MB），本次并行构建累计 105 份 + 各组 `build_dev_*`（每份 ~820 MB）把磁盘写满一次（ENOSPC）。建议 still.sh 末尾加 `find $TMPDIR -maxdepth 1 -name 'remotion-webpack-bundle-*' -mmin +3 -exec rm -rf {} +`，各组换 tag 前删旧 bundle。
- `ChunkCard` 的 `title` 为 15px（低于 22px 最小字号），本组未使用；若其他组用到可读标题，建议 ui.tsx 把 title 字号提到 22 或加 `titleSize` prop。
- `DBIcon` 没有 glow/accent 描边参数，本组用外层 div boxShadow + scale 包裹做紫脉冲；若多组需要，可给 DBIcon 加 `glow?: string`。

## QC v1 修复（依据 rag/qc/qc_v1_C2.md，2026-09-06）

| QC 条目 | 严重度 | 修法 | 核对 still（`rag/stills/F34/`，bundle tag `g34`） |
|---|---|---|---|
| SC18 3130–3137 三层平面 slideUp Δ300 叠压字幕文字/进度条 | 中 | `SC18.tsx`：平面 `slideUp(n,300)`→`slideUp(n,80)`（底层起点 y≤635 且 n=0 时 α=0，任意可见帧都在 y<620） | 3132（底层 y≈549–609）/ 3136 / 3140 |
| SC18 3043–3056「线性扫描」Pill 自进度条下方升入 | 中 | `SC18.tsx`：改自左滑入 `translateX(−slideUp(n,320,18))` + 6 帧渐入，y 固定 575–613 | 3050 / 3054 |
| SC16 2694–2699「文本块」卡片穿字幕带/进度条 | 中 | `SC16.tsx`：`B_CARD` 2694→2686（组首帧），改自左滑入 Δ320 / 18 帧 + `fadeIn(n+2,6)`（2686 即露一小截 α≈.33），y 不变；箭头/盒等节拍不变 | 2686 / 2687 / 2690 / 2696 / 2700 |
| G3\|G4 组界 2685\|2686 满→空 | 中 | 与上一条同一改动；G3 SC15 末 8 帧 exitFade + 轻微下摇（见 G3 BUILD_NOTES） | 2685 → 2686 |
| SC18「Hierarchical NSW」≈20px < 22px | 中 | `SC18.tsx`：fontSize 22→26（cx 962→968） | 3136 / 3140 |
| SC16 Embedding 盒白虚线边与分镜/风格指南不一致 | 低 | `SC16.tsx`：去掉 `dashed`，实线白 3px（与 SC13/SC15 紫卡一致） | 2730 |
| SC17「2D 投影示意」#7A7A7A 压网格线、低对比 | 低 | `SC17.tsx`：颜色 GREY_MID→GREY(#A0A0A1)、22→24px，移到网格外右下 (970,608)（墨迹 ≈596–620，未进字幕带） | 3000 |

- `npx tsc --noEmit`：通过。
- 未修：无（SC17「邻居」Pill +16 帧为 OK 级可选项，保持原样）。
- 改动未新增滤镜/DOM，性能与 v1 一致，未重跑 30 帧测渲。

## 闪烁整改（2026-09-06，用户裁定"不要给每段出现的字都加闪烁，只给重点加"；规则 §8 白名单）
- **改前**：GlitchIn 11 处（SC16×1：Embedding 盒 2720；SC17×4：退款流程 2937 / 怎么把钱要回来 2943 / 年假规定 2954 / 邻居 3002；SC18×3：「1 0000 0000 ×」3073 / HNSW 3136 / 跳转计数 3219；SC19×2：卡片双标签 3345+4i（循环）/ 库上 ACL 3402；SC20×1：增量更新 3539）。
- **改后**：**2 处**。保留 = 白名单 **SC16「Embedding」盒（2720）**、**SC18「HNSW」标签（3136，含 Hierarchical NSW 副标）**；其余 9 处 GlitchIn → `SoftIn`（ui.tsx，8 帧淡入 + 10px 上浮，f0 不变；SC17 年假规定保留 `style={{opacity: farOp}}` 闪一次逻辑，SC19 标签 `overflow:'visible'` 照旧）。
- vspace.ts 无图元封装、无内置 GlitchIn，无需加 `glitch?` 开关。上表/动效小节里"标签 GlitchIn 12 帧"的描述已失效，以本节为准。
- 自检：`npx tsc --noEmit` 通过；tag x34 出 13 张 still 到 `RAG/stills/X34/G4/`（2941/2949、3077/3085、3223/3231、3349/3357、3406/3414、3543/3551 + 3140 核对 HNSW 仍为 glitch），Read 核对：淡入正常，位置/尺寸不变。
