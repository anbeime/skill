# G2 构建笔记（第 1 章下半：SC06–SC10 / S06–S10，N 744–1480）

预览合成 `RagG2`（含 G0 覆盖层）。全部动画是 `N = useCurrentFrame() + F0` 的纯函数；无 useState/useEffect/Math.random。

## 1. 镜头表

| id | 帧 | 文件 | 内容 | 节拍（字幕块起始 → 元素入场帧） |
|---|---|---|---|---|
| SC06 开卷考试 | 744–870 | `SC06.tsx` | 考卷 (280,175,300,380) +「闭卷」灰章（旋转 −8°，压在卷角）+ 灯泡；828 起右侧翻开的书 (850,335) 280×180 + 大字「开卷考试」64px/900/scaleX .8 白字紫描边 | 752 → 750 考卷 slideUp、752 灯泡闪现、762「闭卷」glitch；828 → 828 书 21 帧缩放 + Cross 划掉「闭卷」、830 大字 GlitchIn(rgbSplit 6)；865–870 六帧下摇淡出 |
| SC07 手册流程预告 | 871–1012 | `SC07.tsx` | 三步横排（中轴 y 380）：5 张 DocIcon 扇形堆「资料」→ 箭头 → 书 + 紫胶囊「知识库」→ 箭头 → 答复气泡「住宿上限每天 600 元[1] / 一线城市 800 元[2]」+「作答」；上方问句气泡「差旅报销的上限是多少？」 | 879 → 879 文档 2 帧错峰、890「资料」、893 箭头①（16 帧）、905 书、918「知识库」；956 → 940 气泡 glitch、956 落到书上（Δ112/22）、978 右页紫条 wipe；995 → 995 箭头②、998 答复气泡弹出、1000 [1][2] +「作答」glitch。末帧无离场（SC08 光条硬切） |
| SC08 主角登场 RAG | 1013–1129 | `SC08.tsx` | 清场；「RAG」Audiowide 150px 白 + 紫硬投影 (+6,+6) (640,330)；「检索增强生成」48px/900/scaleX .8 (640,452)；三小胶囊 Retrieval/Augmented/Generation（Exo 2 紫斜体、首字母白）y 520 | 1021 → 1015 三道紫光条扫过（16 帧，2 帧错峰，α .3）、1031 中央呼吸紫光线、1048 第二轮光条；1080 → 1080「RAG」GlitchIn(rgbSplit 8, slices 20) + 光线白闪 3 帧、1092 emphasisPulse 1.11；1096 → 1096 中文副标 slideUp(Δ80)、1104/1106/1108 三胶囊 glitch；1124–1129 六帧淡出 |
| SC09 2020 论文 | 1130–1328 | `SC09.tsx` | 左 论文卡 (140,140,380,460)：标题三行 Times 22/700「Retrieval-Augmented Generation / for Knowledge-Intensive / NLP Tasks」+「Lewis et al. · NeurIPS 2020」灰 + 摘要灰线两栏 + 小柱状图；右「2020」Orbitron 96 (860,300)、胶囊「Facebook AI Research」(690,376,340,50)、大号 Exo 2 两行 Retrieval-Augmented / Generation (860,495/545) | 1138 → 1138 年份 glitch + 2016→2020 每 3 帧 +1；1152 → 1146 论文卡 slideUp、1152 胶囊 glitch；1211 → 1211 标题下紫下划线 draw-on 14 帧；1238 → 1238/1248/1258 三词 11 帧灰→紫、1238 大号英文 slideUp(Δ160)；1323–1328 六帧淡出 |
| SC10 检索 + 生成 = 靠证据 | 1329–1480 | `SC10.tsx` | 上半「检索」「生成」200×70 胶囊（中心 y 247）自两侧滑入 380/900 → 靠拢 470/810 → 3px 白线自边缘长到中点 + 紫接头 + 白闪；下半左 LLMIcon + 灰胶囊「记忆」(300/433,445)，白箭头 →，下半右 三 DocIcon（首行紫）+ 紫胶囊「证据」+ 绿勾 | 1337 → 1337 滑入(Δ520/22)、1362 靠拢 18 帧、1380 连线 16 帧、1392 接头、1396 白闪 4 帧；1413 → 1413 记忆组淡入、1421 起 11 帧变灰 + 下沉 12px；1454 → 1450 箭头、1454/56/58 文档、1458「证据」glitch、1462 绿勾 12 帧；1479–1480 exitFade（接 G0 章节卡 1481） |

组界：首镜头 SC06 首帧 744 为空帧（SC05 硬切后 6 帧留白，750 考卷进入）；末镜头 SC10 末帧 1480 整组 exitFade 到 0.87。`BG_G2 = []`（不覆写星点/雾底）。

## 2. 复用的图元 / 共用层

- `ui.tsx`：`CText / Pill / Box / TechText / Svg / LineArrow / Check / Cross / DocIcon / LLMIcon`；调色板 `PURPLE / PURPLE_LIGHT / PURPLE_TECH / GREY / GREY_LIGHT / GREY_MID / WHITE / TEXT_GLOW / BLOOM_SOFT`；动效 `fadeIn / slideUp / scaleIn / stagger / exitFade`。
- `common`：`GlitchIn / glitchOpacity / stepKf / powOutRemain / easeInOutPow / emphasisPulse / clamp01`，字体 `FONT_TECH / FONT_WIDE(Audiowide) / FONT_ORB(Orbitron) / FONT_SERIF(Times)`。
- 组内新增 `parts.tsx`（ui.tsx 里没有的 RAG 语义图形）：
  - `ExamPaper`：白边黑底竖卡「试 卷」+ 分隔线 + 圆圈序号题目行。
  - `BookIcon`：翻开的两页书（SVG 路径，弧形页缘 + 书脊 + 底部厚度），`s` 中心缩放、`hl/hlLine` 右页某行紫条 wipe。
  - `Bubble`：黑底白边圆角对话气泡 + 尾巴（down/left/right），`text` 或 children。
  - `LightBar`：横向紫光条（透明→紫→白芯→紫→透明 + 紫柔光），SC08 扫光。
  - `Bulb`：白线灯泡（泡体内发光紫、螺口、三道光芒）。
  - `StepPill`：步骤小胶囊 130×44 26px（黑底白边 / `active` 紫底 / `grey` 灰）。
  - `mixHex(a,b,k)`：颜色线性混合（灰→紫、白→灰 11 帧变色）。

## 3. 关键参数

- 入场：slideUp Δ300/22（考卷、论文卡）、Δ80/Δ160（副标/大号英文，避免穿过其它行）；缩放入场 `0.2 + 0.8·BEZ_SCALE_IN(n/21)`（书、文档、答复气泡 .6→1 /10 帧）；GlitchIn 默认序列，标题类加 `rgbSplit 6–8`、「RAG」再加 `slices 20`。
- 错峰：文档堆 / 三胶囊 / 三文档一律 2 帧。
- 箭头：`LineArrow p` 12–16 帧自根部长出；书页高亮 12 帧左锚 wipe；下划线 14 帧左锚。
- 强调：「RAG」`emphasisPulse(peak 1.11)`；三词灰→紫 `mixHex(GREY_LIGHT, PURPLE_LIGHT, k)` 11 帧、间隔 10 帧。
- 离场：SC06 六帧 `1−n/6` + `2.5·n²` 下摇；SC08 / SC09 六帧线性淡出；SC10 末 2 帧 `exitFade`。
- 字号：最小 22px（气泡正文、论文标题/作者行、引用角标 [1][2] 与正文同号 22px 紫粗体）；胶囊 26–34px；大字 48 / 64 / 96 / 150。
- 安全区：所有可读内容 y 110–600、x 140–1200；HUD 区 y<100 未放内容；穿越字幕带的只有 slideUp 过程中的卡片（非停留）。

## 4. 自检

- `npx tsc --noEmit` 通过（每加一个镜头跑一次，最终一次通过）。
- 30 帧测渲（协议 §6）：`npx remotion render build_dev_g2 RagG2 /tmp/rag_test_g2 --sequence --image-format=jpeg --frames=1080-1109`（N 1081–1110，SC08「RAG」rgbSplit+slices 段，本组最重）：精简 bundle（tag `g2`，117 MB）**3.44 s / 30 帧 ≈ 8.7 fps**；此前完整 bundle 3.97 s ≈ 7.6 fps（红线 3 fps，目标区间 4–12 s ✓）。输出已删。
- still 清单（`rag/stills/G2/`，共 47 帧 + 2 组界）：
  - SC06：744 745 756 772 800 836 850 868
  - SC07：872 886 900 925 945 966 990 1005 1012
  - SC08：1014 1022 1029 1060 1081 1086 1100 1108 1112 1127
  - SC09：1131 1141 1150 1168 1218 1245 1262 1300 1326
  - SC10：1330 1345 1358 1372 1388 1397 1420 1436 1460 1470 1478 1480
  - 组界：`boundary_first_744.png`、`boundary_last_1480.png`
- 看图发现并已修：
  1. SC07 末尾「作答」胶囊 / 引用角标 glitch 原定 1006/1008 起，在镜头末帧 1012 仍处于闪烁态 → 提前到 1000，答复气泡弹出缩到 10 帧，1012 前全部落定。
  2. SC08「检索增强生成」原 Δ120 自下滑入时穿过三胶囊行（1100 帧与 Retrieval/Augmented 重叠）→ 改 Δ80，胶囊 glitch 推后到 1104/1106/1108。
  3. SC10 上排胶囊 y 220 与下排 y 455 之间空带过大 → 上排下移到 247、下排上移到 445。
- 事实核对：论文名《Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks》、Lewis et al.、NeurIPS 2020、Facebook AI Research，均见 `research/RAG调研.md §1`；年份 2016→2020 仅为计数动效（终值 2020 为事实）。示例文本按全局约束：问句「差旅报销的上限是多少？」、答复「住宿上限每天 600 元[1] / 一线城市 800 元[2]」。
- 节拍：所有关键词元素在对应字幕块起始帧 [−6, +3] 内出现（SC07 问句气泡 940 为"预置"元素，956 才飞向书，属铺垫而非关键词）。

## 5. 降级 / 未做

- SC06 storyboard 里「灯泡在 LLMIcon 位置闪一下（可选）」：SC06 已清场无 LLMIcon，改为灯泡在考卷上方 (430,138) 闪现 → 786 淡出。
- SC07 storyboard 的问句气泡「问题」改为实际示例问句（全局约束 2），答复气泡按示例答复两行。
- SC09 论文标题 storyboard 写 Times 20px，协议最小字号 22px → 用 22px 三行。
- SC10 「⊐ 连接线」简化为两段 3px 白线自胶囊边缘长到中点 + 紫接头 r10 + 白闪，未做完整 ⊐ 括线（两胶囊同轴，括线没有可包的对象）。
- 30 帧测渲用的是 SC08 段；SC09（论文卡约 40 个 div）与 SC10 未单独计时，DOM 均 <150 节点，无 SVG filter（只有 GlitchIn 的 2 个 feColorMatrix 在 rgbSplit 闪烁期内）。

## 6. 对 ui.tsx / 共用层的建议

1. `Bubble`（对话气泡 + 尾巴）与 `BookIcon`（翻开的书）建议进 ui.tsx：第 3 章「生成 / 引用」和第 4 章「回到开卷比喻」（S42）都会再用；G2 版在 `shots/G2/parts.tsx`，可直接搬。
2. `mixHex(a,b,k)` 建议进 ui.tsx 动效小工具区：灰→紫 / 白→灰 变色在各组都需要。
3. `Pill` 建议加 `italic?` 与 `textStyle?` 透传（SC08 三胶囊要 Exo 2 斜体 + 首字母另色，只能用 Box 手写内层）。
4. `DocIcon` / `LLMIcon` 建议加 `style?`（或 `rotate?/scale?`）透传：做扇形堆 / 中心缩放入场时目前要包一层 div。
5. `LightBar` 若第 4 章片尾/进阶段也要"扫光"转场，可进 ui.tsx。
6. 工程层面：`build_dev_<tag>` 原每个 ~820 MB，8 组并行 + `$TMPDIR/remotion-webpack-bundle-*` 曾把磁盘撑满（ENOSPC）。主会话已改 still.sh 为精简 bundle（`--public-dir public_rag`，≈117 MB）并定规则：本组只用 tag `g2`，改代码后 `rm -rf remotion/build_dev_g2` 再跑；不要直接 `npx remotion still src/index.ts`。本组已按新规则重验（f_1262 + 30 帧测渲），旧 `build_dev_g2_*` 均已删除。

## 7. QC v1 修复（qc_v1_C1.md · G2 条目）
| 条目 | 根因 | 修法 | 复核帧（`rag/stills/F12/`） |
|---|---|---|---|
| 【中】SC08 1021–1079「今天的主角」近黑屏 2 秒 | 两轮光条 α .3/.2、白芯被整体透明度压没；呼吸线 α .32±.14；1015–1079 无其他元素 | ① `parts.tsx` `LightBar` 重做：紫渐隐底条 + 独立白芯层（h×.4、白 boxShadow）+ 紫柔光；② 扫光改三轮连续 `T_SWEEPS=[1017,1035,1053]`（轮距 18、单轮含错峰 20 帧 → 首尾相接），α .6/.55/.55；③ 呼吸线提到 .45±.15；④ 1050 起「RAG」150px Audiowide **白描边透明填充**轮廓以 0.10±0.02 不透明度隐现（12 帧淡入，紫 textShadow 雾），1080 glitch 闪烁期保留作底，1092 起撤掉 | 1030（单条尾巴）、1044（三条中段，白芯清晰）、1055（轮廓开始隐现 + 第三轮光条）、1066、1075（轮廓 ~10% + 呼吸线）、1085（glitch 空帧时轮廓垫底，无"黑一下"） |
| 【低】SC07 1000–1012「作答」胶囊"灰底灰字" | 并非 grey 变体——`StepPill` 默认就是黑底白边；实际是 glitch 1000 起、12 帧闪烁到 1012（镜头末帧）才落定，整段处于 ≤.75 半透明，看起来像灰 | `T_PILL3` 1000→996（箭头② 995 之后 1 帧），1008 落定，1008–1012 五帧实心白 | 1000（闪烁中 .5）、1010（实心白，与「资料」同级） |
| 【低】SC09 1211–1237「提出这个名字」仅 3px 下划线、1167–1240 静止 73 帧 | 节拍只绑在下划线 draw-on | 标题块 `emphasisPulse(N−1211,{peak 1.06, up 8, hold 4, down 10})` + 三词 Retrieval/Augmented/Generation 1211/1215/1219 依次 12 帧三角白闪（GREY_LIGHT→WHITE→GREY_LIGHT + 白 textShadow）；与 1238 起灰→紫互不重叠（`Word` 新增 `f` 参数） | 1215（Retrieval 白闪 + 放大）、1219（Augmented）、1225（Generation） |
| 【低】SC06 752–758 考卷 slideUp 穿字幕带 | Δ300 → 卡底起点 855，n≤8 帧内均在 y>637 且 opacity 已到 1 | Δ300→**Δ130**（卡底起点 685，n=4 已到 634 离开字幕带，此时 fadeIn(8) 仅 .5） | 754（卡底 634、半透明）、758（完全在带外） |
| 【低】SC09 1151–1158 论文卡 slideUp 穿字幕带 | 同上，Δ300 卡底起点 900 | Δ300→**Δ90**（卡底起点 690，n=6 到 640、n=7 离开；带内停留时 opacity ≤ .875，只有 3px 底边框） | 1152（n=6，底边 640 擦过带顶）、1156（带外） |
| 【低】SC06 772–827 长静止 56 帧 | 灯泡 786 淡出后无任何动作到 828 | 灯泡 770 起 20 帧周期呼吸（glow .56↔1：泡体紫填充 + 光芒透明度），826 起 8 帧淡出让位给 828 的书 | 790 / 810（呼吸峰值；谷值在 780/800/820） |

- 未修（G2 范围内）：无。G0 章节卡前空拍（1481–1486）属 G0，未碰。
- tsc 通过；帧区间、index.ts 未改；`LightBar` 只有 SC08 使用，新增 `core?` 默认 true。DOM/filter 无新增 SVG filter（SC02 的 drop-shadow 为 CSS filter，仅闪烁 10 帧内 ≤3 个）。
- still 用 tag `g12`（`build_dev_g12`），输出 `rag/stills/F12/`（22 张：G2 17 + G1 5）。

## 8. 闪烁整改（用户裁定 2026-09-06「不要给每段出现的字都加闪烁，只给重点加」· 协议 §8）
- **改前 12 处 / 15 实例**：SC06「闭卷」章 GlitchIn 762、「开卷考试」GlitchIn 830（rgbSplit 6）、灯泡 7 帧 `stepKf` 手写闪现 752；SC07「资料」890 /「知识库」918 / 问句气泡 940 /「作答」996 四处 GlitchIn + 引用角标 [1][2] `glitchOpacity` 1000；SC08「RAG」GlitchIn 1080（rgbSplit 8 / slices 20）+ 三胶囊 GlitchIn 1104/1106/1108（循环 1 处 3 实例）；SC09 年份 GlitchIn 1138 + 「Facebook AI Research」GlitchIn 1152；SC10「证据」GlitchIn 1458。
- **改后 2 处**（每镜头 ≤1）：
  | 镜头 | 保留 glitch | 说明 |
  |---|---|---|
  | SC06 | 「开卷考试」大字（830） | 白名单。去掉 `rgbSplit={6} seed={6}`（§8：rgbSplit/slices 仅片头/SC08/SC35/SC44）→ 12 帧纯透明度模板 |
  | SC08 | 「RAG」大字（1080） | 白名单重口味四处之一，**原样保留** rgbSplit 8 / slices 20 |
- **改为 SoftIn**（ui.tsx，8 帧淡入 + 10px 上浮，f0 不变）：SC06「闭卷」762；SC07「资料」890 /「知识库」918 / 问句气泡 940 /「作答」996（1004 落定，比原 1008 早 4 帧，仍在箭头② 995 之后）；SC08 三胶囊 1104/1106/1108；SC09 年份 1138 /「Facebook AI Research」1152；SC10「证据」1458。
- **改为 fadeIn 8**：SC07 引用角标 [1][2]（1000）；SC06 灯泡（752，原 `BULB_SEQ` 7 帧闪现；glow 仍 4 帧后点亮、770 起呼吸不变）。
- 组内图元（parts.tsx StepPill/Bubble/LightBar/Bulb）本身不内置 GlitchIn，闪烁都是镜头外层包的，因此**不需要**加 `glitch?` 开关；parts.tsx 未改。SC07/SC09/SC10 现为零 glitch。
- tsc 通过；帧区间 / index.ts 未改；still tag `x12`（`build_dev_x12`），输出 `rag/stills/X12/`：
  756（灯泡淡入中）、766/774（闭卷 SoftIn 中/完成）、834/842（开卷考试 glitch 中/落定）、894/902（资料）、922/930（知识库）、944/952（问句气泡）、1000/1004/1008（作答 + 引用角标）、1108/1116（三胶囊）、1142/1150（年份）、1156/1164（FAIR 胶囊）、1462/1470（证据）。
- still 复核（Read 全部 22 张）：SoftIn 处 f0+4 半透明、f0+12 落定，位置/尺寸与改前一致；灯泡 756 平滑淡入（无闪烁）；「开卷考试」834 为 0.5 档纯透明度、842 实心、无 RGB 错位；「RAG」1080 段未动；SC08 三胶囊 1108 呈 2 帧错峰淡入、1116 三枚齐；引用角标 [1][2] 1004 淡入中、1008 实心。22 张 50 s 出齐。
