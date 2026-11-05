# 《RAG 与知识库》构建 agent 协议（原创 MG 片，非复刻）

> **这是样片当时的原始派单文件，仅作归档参考，不要照它派单**：现行版是 `reference/agent-build-rules.md`（单目录布局，并补齐了主体尺寸 / 光 / 运镜规则）。留着它是因为 `分镜表.md`、`交付说明.md`、各组 `BUILD_NOTES.md`、`qc/qc_v3_final.md` 都在引用它的 **§8 闪烁白名单**——那是这份文件今天唯一还有用的部分。原文中的绝对路径已删除。

工程：Remotion 4 + React 19 + TS，1280×720@30fps。当时是**两个目录**：Remotion 工程目录（本片镜头在其 `src/rag/` 下）与成片资料目录（下文的 RAG/，放调研、解说词、分镜表、stills、QC）。新片是单目录，两者合一。

## 0. 必读
1. `RAG/STYLE_GUIDE.md` — 视觉风格与图元/动效词汇（配 `RAG/style_ref/*.jpg` 参考帧，**先看图再写代码**）。
2. `RAG/分镜表.md` — 你负责的组（Gn）每个镜头的帧区间、节拍（字幕块起始帧）、画面内容、动效描述。帧区间以此为准；画面描述是导演意图，坐标为参考值，可在保证版式安全区与风格的前提下微调。**同一章两组之间要复用同一套示例文本与图元样式**（见分镜表末「全局约束」）。
3. `RAG/script/timeline.md` — 每句解说词的帧区间与字幕切分（字幕由共用层自动渲染，**镜头里不要再画字幕**）。
4. `RAG/research/RAG调研.md` — 画面上出现的任何数字/术语/英文拼写必须能在此文档找到依据；不得自创数据。

## 1. 工程约定
- 帧号 **N = useCurrentFrame() + F0**（F0 = 该镜头 ShotDef.from；1 起含端点）。分镜表、timeline 里的帧号都是 N。
- 构建组 G1–G8（每章两组，各 5–7 个镜头；G0 是主会话的覆盖层：片头/章节卡/顶部 HUD/流程轨/片尾，构建组不要画这些）。每个镜头一个组件文件 `src/rag/shots/Gn/SCxx.tsx`；`src/rag/shots/Gn/index.ts` 导出 `SHOTS_Gn: ShotDef[]`（{id,from,to,Comp,layer?}，数组顺序即层序）与 `BG_Gn: BgSpec[]`（星点/雾底覆写，见下）。**只改 `src/rag/shots/Gn/**`**，不改 Main/Root/common/其他组；共用层要改的写进 `src/rag/shots/Gn/BUILD_NOTES.md` 并在最终回复里提出。
- 本片图元库 `src/rag/ui.tsx`（从 `'../../ui'` 导入）：调色板 PURPLE/PURPLE_LIGHT/PURPLE_TECH/ORANGE/CORAL/RED_DEEP/GREEN/GREY/GREY_LINE/WHITE、GLOW_*/BLOOM/TEXT_GLOW；`CText/TechText/MonoText/Box/Pill/TagBlock/Svg/LineArrow/ArrowH/Check/Cross/DocIcon/DBIcon/ChunkCard/LLMIcon/TopCapsule/Counter`；动效小工具 `fadeIn/fadeOut/slideUp/scaleIn/exitAccel/exitFade/stagger/abs`。**优先用这些**，保证八个组画风一致；缺什么就在自己组目录里补，不改 ui.tsx（要加进 ui.tsx 的写进 BUILD_NOTES）。
- 共用层从 `'../../common'` 导入：`GlitchIn`（12 帧 glitch 入场）、`kf/stepKf/slideIn/powOutRemain/expOut/powIn/easeInOutPow/cubicBezier/BEZ_SCALE_IN/emphasisPulse/rnd`、`StarField/Fog`、`FONT_HEAVY/FONT_TECH/FONT_WIDE/FONT_ORB/FONT_MONO/FONT_SERIF`、`DirBlur`、`SubtitleLine/strokeShadow`（描边字样式复用，不是画字幕）、`TOTAL_FRAMES/CHAPTER_STARTS/SENTENCES`。字体已由 Main 全局加载（Noto Sans SC 100–900、Exo 2 Italic、Audiowide、Orbitron），组件内**不要**再 delayRender 加载字体。
- 全片常驻层由 Main 渲染：黑底 < 雾底 Fog(y415→720 #000→#212121) < 星点 StarField < 你的镜头 < 进度条(y687–720 半透明) < `layer:'aboveBar'` 镜头 < 字幕。**镜头组件不要画不透明黑底**（会盖掉雾底和星点）；确需纯黑/无星（如片头第一帧、强调黑场）用 `BG_Gn: [{from,to,fog:false,stars:'none'}]`。
- 推荐系统片的图元库可以 **import 复用**：`src/recsys/shots/R2/ui.tsx`（Pill/TechText/ArrowRight/ArrowV/Trap/BoxLabel/Line/StackIcon/PlayIcon）、`R1/common.tsx`、`R4/util.tsx`、`R5/util.tsx`、`R6/ui.tsx`（具体见 STYLE_GUIDE 图元目录）。要改行为就复制到自己组目录再改，不要改 recsys 源文件。
- 随机只用 `rnd(...seeds)`（确定性），禁 `Math.random`。所有动画都是 N 的纯函数（不要用 useState/useEffect 做动画）。

## 2. 版面安全区
- 顶部 HUD 胶囊 (533,28,216,51) 与第 2、3 章的流程轨（y 112–160）由 G0 绘制，**构建组不要画**，也不要把内容放进 y<100（第 1、4 章）/ y<175（第 2、3 章）。
- 内容主区：第 1、4 章 **y 110–620**，第 2、3 章 **y 175–620**（x 60–1220）。字幕带 **y637–690 不放任何需要阅读的内容**；进度条 y687–720 只允许全幅背景/大图形穿过（会被条体提亮，这是原片风格，允许）。
- 最小字号 22px；正文标签 26–34px；标题 44–72px；英文技术词用 FONT_TECH（斜体，`scaleX 0.8–0.9`）。

## 3. 动效与节奏（细节见 STYLE_GUIDE）
- 入场三选一：GlitchIn 12 帧模板（标题/胶囊/关键词）、自下滑入 `y = yEnd + Δ·powOutRemain(n,22,2.5)`（Δ≈300，图形/卡片）、21 帧缩放入场 `s = s0+(1−s0)·BEZ_SCALE_IN(n/21)`（图标）。列表/卡片阵列按 **2 帧错峰**。
- 线条/箭头 draw-on：SVG `clipPath` rect 或 stroke-dasharray，箭头**自根部长出**，16–28 帧。
- 强调：`emphasisPulse(n,{peak:1.11})`，灰→紫 11 帧变色，柔光 `box-shadow 0 0 24px 8px rgba(102,45,248,.6)`。
- 离场：幂缓入 `Δ = c·t^2`（t 帧）下摇/左滑 + 每帧 6.7% 淡出（约 15 帧）；或与下一镜头硬切。相邻镜头之间**不留空白帧**（背景层常驻，允许 0–3 帧的重叠）。
- 节拍：元素入场对齐解说词的**字幕块起始帧**（timeline.md 里每个 ｜ 块），关键词出现不晚于对应字幕块起始 +3 帧、不早于 −6 帧。
- 镜头机位：静态镜头为主；长镜头可用"世界坐标 + 定点缩放"（scale 1↔1.33，30–40 帧 easeInOutPow(2.5)）做推近。

## 4. 性能红线（违反会让整片渲染慢 10–50 倍）
- 禁 `feConvolveMatrix`；`filter: blur()`/feGaussianBlur σ≥1（σ<0.8 在 Chromium 中无效）；SVG filter 加 `colorInterpolationFilters="sRGB"`。
- 单帧 DOM 节点 ≤ 600、SVG filter 实例 ≤ 6、OffthreadVideo ≤ 1。粒子/网格用纯函数按 N 生成，不要每帧 new 大数组以外的东西。
- 完工前跑 30 帧测渲测 fps（见 §6），低于 3 fps 要找原因。

## 5. 自检（必须做，写进 BUILD_NOTES）
- `npx tsc --noEmit` 通过（在 remotion 目录）。
- 每个镜头至少出 **6 张 still**：入场首帧+1、入场中段、入场完成、中间关键帧、离场中段、末帧。命令：`RAG/script/still.sh RagGn <帧号,逗号分隔> <输出目录> gN`（**tag 固定为本组 gN，一个组只留一个 bundle**；改代码后 `rm -rf remotion/build_dev_gN` 再跑；bundle 已精简为 ≈110MB，仍不要堆多个）。**禁止**直接 `npx remotion still src/index.ts …`（每次在 $TMPDIR 生成临时 bundle，曾把磁盘写满）。测渲输出到 /tmp/rag_test_gN，看完即删。still.sh 的输出目录**用绝对路径**（脚本内部会 cd 到 remotion/）。输出到 `RAG/stills/Gn/`。**用 Read 看图**，检查：文字是否被字幕带/进度条/HUD 遮挡、是否溢出画布、颜色是否符合调色板、英文拼写、数字与调研一致、元素是否在字幕块起始帧 ±6 内出现。
- 与相邻组的组界帧：本组第一个镜头的首帧与最后一个镜头的末帧各出一张 still 放 `RAG/stills/Gn/boundary_*.png`。

## 6. 30 帧测渲
```
# 在 Remotion 工程目录下执行
npx remotion render build_dev_<tag> RagGn /tmp/rag_test_Gn --sequence --image-format=jpeg --frames=<a>-<a+29> --log=error
```
用 `time` 计时，30 帧应在 4–12 s；把耗时写进 BUILD_NOTES。

## 7. 交付
- `src/rag/shots/Gn/index.ts` 的 `SHOTS_Gn`/`BG_Gn` 填完，覆盖分镜表全部镜头。
- `src/rag/shots/Gn/BUILD_NOTES.md`：镜头表（id/帧/文件/内容）、复用的图元、关键参数、测渲耗时、自检 still 清单与发现、未完成/降级项、对共用层的建议。
- 最终回复只需：完成的镜头数、tsc 结果、测渲 fps、still 目录、需要主会话决定的事项。**边做边写盘**（每完成 1–2 个镜头就更新 index.ts 与 BUILD_NOTES），不要攒到最后。

## 8. 闪烁（GlitchIn）使用白名单（用户裁定 2026-09-06："不要给每段出现的字都加闪烁，只给重点加"）
- **每个镜头最多 1 处 glitch，且只用于该镜头的重点词**（下表）；其余一切文字/标签/胶囊/数字/图标入场一律用 `SoftIn`（`ui.tsx`，8 帧淡入 + 10px 上浮，签名与 GlitchIn 相同可直接替换）或 fadeIn/slideUp/scaleIn。HUD 换词由 G0 用 SoftIn。
- 白名单：片头「RAG 与知识库」、章节卡标题；SC02「知识截止」/ SC03「读不到私有数据」/ SC04「幻觉」（三个短板标签）；SC06「开卷考试」；SC08「RAG」大字；SC16「Embedding」盒；SC18「HNSW」；SC23「语义检索」；SC25「混合检索」；SC26「Cross-Encoder 重排」；SC28「Lost in the Middle」；SC30「RAG 的价值」；SC33「RAGAS」；SC35「RAG」大字；SC36「GraphRAG」；SC37「Agentic RAG」；SC38「Multimodal RAG」；SC42「闭卷 → 开卷」；SC44「知识库 = 护城河」。**不在表内的镜头（SC01/05/07/09/10/11/12/13/14/15/17/19/20/21/22/24/27/29/31/32/34/39/40/41/43）一处 glitch 都不要。**
- 用 `rgbSplit/slices` 的重口味 glitch 只允许片头、三张章节卡标题、SC08、SC35、SC44。
