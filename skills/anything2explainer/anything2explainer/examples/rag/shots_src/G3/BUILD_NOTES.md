# G3 构建笔记（第 2 章上半：SC11–SC15，S11–S15，帧 1526–2685）

预览合成 `RagG3`（= G0 覆盖层 + 本组）。所有帧号 N = useCurrentFrame()+F0（1 起含端点）。只改了 `src/rag/shots/G3/**`。

## 镜头表

| id | 帧 | 文件 | 内容 / 节拍 |
|---|---|---|---|
| SC11 | 1526–1654 | `SC11.tsx` | 手册 = 知识库。中央翻开的书（`BookIcon`，21 帧缩放入场）+ 上方 Pill「手册」（glitch 1538）；左 `Dial`「RAG 效果」半圆刻度盘 draw-on（1534）→ 指针 easeInOutPow 摆到 50%（1566–1594）+ 橙 Pill「一半」（1592）；1606 Pill 翻转（`|cos|` 12 帧，中点换字换色）→ 紫「知识库」+ TechText Knowledge Base（1614），书页文字线灰→紫 11 帧；右侧 1612 起 三张小 DocIcon → 箭头 → DBIcon（紫顶）+ 灰字「怎么建？」。1646 起整组下摇淡出（9 帧），与 SC12 硬接。流程轨 1655 才出现，本镜头用 y 225–520。 |
| SC12 | 1655–1890 | `SC12.tsx` | 第一步解析。1663 解析器框 + TechText Parsing glitch；1690 四文件图标（`PdfIcon/WebIcon/TableIcon/ScanIcon`，x130，y 232/332/432/532）2 帧错峰自左滑入（powOutRemain 22，Δ300），1704 起四条 `LineArrow` 汇聚到解析器（3 帧错峰，14 帧）；1752 解析器→文档卡 `ArrowH`；1760 `DocCard` 自右滑入（Δ320），1766 起 13 个条目每 2 帧逐行 wipe（标题「第 3 章 差旅报销」/ 7 段落线 / 小标题条 / 3 段落线 / 3×3 表格）；1819/1831/1843 紫标签「标题/段落/表格」glitch + 紫括线。1880 起左/中组左滑淡出，**文档卡留到 1890 末帧**（SC13 承接）。 |
| SC13 | 1891–2054 | `SC13.tsx` | 第二步切块。同一 `DocCard`（几何常量 `DOC_CX/DOC_CY` 自 SC12 导入）1891–1911 easeInOutPow(2.5) 平移到 (640,400) 并放大 1.1；1921 左 `LLMIcon`(100) 缩放入场 + 灰「?」glitch（1925）+ 灰虚线箭头（1927）；1974/1977/1980 三条紫虚线切割线 wipe 10 帧；1990 起四段分离（gap 0→12 局部 px，slideIn 18），2000 起每段边框白→亮紫 11 帧（2 帧错峰）+ 紫柔光，2004 起右上 Exo 2「chunk」glitch。2044 起整组下摇淡出。 |
| SC14 | 2055–2308 | `SC14.tsx` | 切多大。2063 中央「切多大？」glitch（2173 硬切掉）；2098 左栏 220×330 大 `ChunkCard` 自左滑入 + Pill「太大」+ 红 `Cross`（2106）+ `Magnifier` 灰问号（2110）；2133 右栏 14 个碎块（rnd 位置/尺寸/旋转）自栏中心 1 帧错峰散开 + Pill「太小」+ 红叉（2141）；2173 中栏三张标准 `ChunkCard`(150×92) 2 帧错峰缩放入场 + 紫 Pill「常见做法」+ 绿 `Check`（2181）+ 小箭头 + Orbitron 橙数字「≈ 300–800」逐帧随机滚动（2173–2193）→ 2194 硬切「≈ 几百」+ TechText token；2257/2261 相邻卡之间紫半透明重叠带左锚 wipe 8 帧 + 紫 Pill「重叠」。2298 起整组下摇淡出。 |
| SC15 | 2309–2685 | `SC15.tsx` | 语义切块 + 补上下文 −49%。2317 左 400×400 文档树卡自左滑入；2346 起 12 条目每 3 帧逐级 wipe（员工手册 › 第 3 章 差旅报销 › 3.1 住宿上限 / 3.2 交通 …），同时 4 条**等距**灰虚线淡入（对照），2368 起 4 条**沿标题边界**的紫虚线 draw-on（4 帧错峰，12 帧）、灰线淡出；2380 灰字「沿标题边界切，而不是等距」；2394 中 `ChunkCard`(180×100, active) 缩放入场，2400 树中 3.1 段紫高亮 + 紫虚线箭头指向卡片（2404），2402 紫前缀条自卡顶长出（scaleY 12 帧）+ 2412 起打字机「员工手册 › 第 3 章 差旅报销」（1.2 帧/字）；2498 Pill「Anthropic」glitch + 2500 TechText Contextual Retrieval；2572 紫 Pill「BM25」（Exo 2）贴在前缀条右上；2606 橙 72px「−N%」0→49 计数 20 帧（glitch 入）+ 2626 emphasisPulse(1.12)，2620 灰字「Top-20 检索失败率」。末 2 帧不离场（SC16 硬切）。 |

`index.ts`：`SHOTS_G3` 五条首尾相接（1526–1654 / 1655–1890 / 1891–2054 / 2055–2308 / 2309–2685）；`BG_G3 = []`（无星点/雾底覆写）。

## 复用的图元 / 组内补充

- `ui.tsx`：Pill / Box / CText / TechText / ChunkCard / DocIcon / DBIcon / LLMIcon / Svg / LineArrow / ArrowH / Check / Cross + 调色板 + fadeIn/fadeOut/slideUp/scaleIn/exitAccel/stagger。ChunkCard 的 active 样式（亮紫边 + GLOW_PURPLE_S）是本组「chunk」的统一视觉，SC13 的分段 Box 同款 r8/sw2。
- `common`：GlitchIn / glitchOpacity / slideIn / powOutRemain / easeInOutPow / emphasisPulse / rnd / clamp01 / FONT_ORB / FONT_TECH。
- 组内 `g3ui.tsx`（不改 ui.tsx）：`LText`（左对齐文字）、`Bar`（占位线）、`DocCard`（解析产物文档卡，SC12/SC13 共用，可切成 4 段：`split/gap/activeK/tagOp`，内容层在每段内做 −i·90 偏移裁切）、`PdfIcon/WebIcon/TableIcon/ScanIcon`、`BookIcon`、`Dial`、`Magnifier`、`mixColor`（灰→紫插值）、`purpleGlow`。
- 示例文本统一「差旅报销」语境：文档标题「第 3 章 差旅报销」、树「员工手册 › 第 3 章 差旅报销 › 3.1 住宿上限 / 3.2 交通」、前缀条同上。

## 关键参数

- 入场：滑入 `slideUp(n, 300–320)`（22 帧 p2.5）；缩放 `scaleIn`(21)；glitch 12 帧；错峰 2 帧（卡片/图标）、3 帧（汇聚箭头/树条目）、4 帧（切割线/重叠带）。
- 离场：`fadeOut(n, 9–10)` × `translateY(exitAccel(n, 0.9))`（SC11/13/14）；SC12 左组 `translateX(−exitAccel(n, .6))`；SC15 不离场。
- SC13 运镜：`t = easeInOutPow(2.5)((N−1891)/20)`，cx 980→640，s 1→1.1；分离后总高 (360+36)×1.1 ≈ 436 → y 182–618（贴主区边界）。
- 数字：SC14 滚动数字 300–800 为纯视觉随机（研究 §2.3：常见 256–1024 token），终态只显示「几百」；SC15「−49%」「Top-20 检索失败率」「Anthropic」「Contextual Retrieval」「BM25」出自 research §2.3/§2.7（Anthropic 2024，contextual embeddings + contextual BM25 → top-20 失败率 5.7%→2.9%，−49%）。
- 字号：最小 22px（标签 Pill、前缀条、灰说明字）；标题 44px；数字 72px。

## 性能

- 无 feGaussianBlur / blur()；SVG filter 仅 CSS drop-shadow（SC11 峰值 3 个：书、刻度盘、DBIcon；SC12 2 个；其余 ≤1）。单帧 DOM 峰值 ≈ SC12 末段 ~130 节点（含 G0）。
- 30 帧测渲（`npx remotion render build_dev_g3_5 RagG3 /tmp/rag_test_G3 --sequence --image-format=jpeg --frames=a-b --log=error`）：见下「测渲耗时」。

## 测渲耗时

- 2605–2634（SC15 计数段）：30 帧 3.1 s（≈9.7 fps，build_dev_g3_4）。
- 1600–1629（SC11 满画面，书 + 刻度盘 + 右侧示意）：30 帧 3.3 s（≈9.0 fps，build_dev_g3_5）。
- 1995–2024（SC13 四段分离 + 紫柔光 + 运镜）：30 帧 3.6 s（≈8.4 fps，build_dev_g3_5）。
- 三段均远高于 3 fps 红线；`--sequence --image-format=jpeg`，含浏览器启动。最终交付前已删除 `build_dev_g3_*`（磁盘 96%），QC 需要时用 `still.sh RagG3 <帧> <目录> g3_qc` 重建。

## 自检 still 清单（`rag/stills/G3/`）

- SC11：1527 / 1545 / 1575 / 1600 / 1612 / 1630 / 1650 / 1654。发现并修复：刻度盘 p=0 时圆头 dasharray 在 (170,440) 留下一个白点 → 弧线 p≤0 时 opacity 0。
- SC12：1656 / 1670 / 1695 / 1712 / 1765 / 1790 / 1825 / 1850 / 1885 / 1890。无问题；文档卡在 1890 与 SC13 1891 像素一致（同一 DocCard，cx 980，s 1）。
- SC13：1891 / 1900 / 1925 / 1940 / 1978 / 1994 / 2010 / 2030 / 2050 / 2054。分离后顶段上缘 y≈183，离流程轨（160）尚有 20px+。
- SC14：2056 / 2066 / 2100 / 2115 / 2138 / 2150 / 2176 / 2190 / 2200 / 2262 / 2290 / 2305。无问题。
- SC15：2320 / 2350 / 2372 / 2395 / 2410 / 2430 / 2500 / 2575 / 2610 / 2630 / 2660 / 2685。灰字说明「沿标题边界切，而不是等距」中心 y612（墨迹 601–623），未进字幕带（637+）。
- 组界：`boundary_1526.png`（首帧，仅 HUD + 极小的书）/ `boundary_2685.png`（末帧，SC15 全景，供 G4 SC16 硬切参考）。
- 检查项：无内容进入 y<175（SC12–15）/ y>620；无元素穿进度条；颜色均取自调色板；英文拼写 Knowledge Base / Parsing / chunk / token / Anthropic / Contextual Retrieval / BM25 与研究文档一致。

## 与分镜表的差异 / 降级项

- SC11 分镜写「左右两侧各一个小天平/进度」但只描述了左侧刻度盘；右侧改为「三张文档 → 箭头 → 向量库 + 灰字『怎么建？』」小示意，对应字幕「知识库是怎么建的」。刻度盘旁标签用「一半」而非「50%」（避免出现未核实数字）。
- SC12 文件图标放在 x130（分镜 x200），标签放在图标右侧，为四条汇聚箭头留出长度；PDF 图标不写小字「PDF」（会低于 22px 最小字号），改用橙色角标 + 右侧 26px 标签。
- SC13 分离出的四段用与 `ChunkCard` 同款的 Box 样式承载**原文档内容**（而不是替换成 ChunkCard 的随机线条），避免切割瞬间内容跳变。
- SC14 中栏「≈ 几百 token」放在卡片左侧（分镜写右侧），右侧留给「重叠」标签。
- SC15 右栏中心 x 1040（分镜 980），前缀条文案去掉书名号以控制宽度（330px）。

## 对共用层的建议（写给主会话）

- `still.sh` 每次 `npx remotion still` 都会在 `$TMPDIR` 留一份 ~200–340 MB 的 `remotion-webpack-bundle-*`，八组并行时很快写满磁盘（本次 168 份 ≈30 GB，触发 ENOSPC）。建议在脚本末尾追加 `find $TMPDIR -maxdepth 1 -name 'remotion-webpack-bundle-*' -mmin +3 -type d -prune -exec rm -rf {} +`，并约定各组只保留最新一个 `build_dev_<tag>`。另：有人在我 still 进行中删掉了 `build_dev_g3_3`，导致一批 still 中断——清理别组的 build_dev 前请先打招呼。
- 若 ui.tsx 后续要收编：`LText`（左对齐文字）与 `DocCard`（可切块文档卡）对 G4/G5（向量化、检索命中的 chunk）可能有用。
- G4 SC16 首帧 2686 与本组 2685 硬切：SC15 末帧保留全景（无淡出），SC16 请自带入场。

## QC v1 修复（依据 rag/qc/qc_v1_C2.md，2026-09-06）

| QC 条目 | 严重度 | 修法 | 核对 still（`rag/stills/F34/`，bundle tag `g34`） |
|---|---|---|---|
| SC15→SC16 组界 2685\|2686 满→空硬切 + 8 帧空白 | 中 | `SC15.tsx`：整组包一层 div，2674–2685 末 12 帧 `opacity = 1 − (n/12)^1.5`（n = N−2673，2685 归零）+ `exitAccel(n,0.2)` 轻微下摇（末帧 ≈29px，此时 α≈0）。配合 G4 SC16 卡片提前到 2686 自左入场（见 G4 BUILD_NOTES） | 2680 / 2684 / 2685 |
| SC11 1526–1533 刻度盘残留 14px 白短横 | 低 | `g3ui.tsx Dial`：根因是 k=0 刻度线 `show` 条件在 p=0 时为真；改 `p > 0 &&`，并让整个 svg 在 p≤0 时 opacity 0 | 1528 / 1530（画面仅 HUD + 小书，无短横） |
| SC12 1690–1712 标签先于图标入画 | 低 | `SC12.tsx`：标签 opacity 改 `fadeIn(n−4, 6)`，图标右缘入画（n≈5）时标签才开始渐入 | 1693（无孤立文字）/ 1697（PDF 到位、网页半入 + 标签同步） |
| SC13「chunk」紫字压紫边对比低 | 低 | `g3ui.tsx DocCard`：标签改 WHITE（保留紫 text-shadow） | 2010 |
| SC14「token」≈21–22px 边缘、偏暗 | 低 | `SC14.tsx`：fontSize 24→28、PURPLE_LIGHT，cy 358→360 | 2200 |
| SC15 2320–2345 空白树卡停留 26 帧 | 低 | `SC15.tsx`：12 条目 wipe 起点 2346→2322（3 帧错峰，2357 起最后一条）；等距灰线 2346、紫切割线 2368 节拍不变 | 2330（前 3 条已出）/ 2340 / 2350 |

- `npx tsc --noEmit`：通过（全工程零错误）。
- 未修：无。备注：组界离场首版为 8 帧 exitFade（2685 残余 α≈0.57 后硬切），主会话复核后改为 12 帧幂曲线末帧归零，SC16 2686 起自左入场接力。
- 本次改动未新增滤镜/DOM，性能与 v1 一致，未重跑 30 帧测渲。

## 闪烁整改（2026-09-06，用户裁定"不要给每段出现的字都加闪烁，只给重点加"；规则 §8 白名单）
- **改前**：GlitchIn 16 处 + glitchOpacity 8 处 = 24 处闪烁（SC11×5：手册胶囊 1538 / Knowledge Base 1614 / RAG 效果 1540 / 一半 1592 / 怎么建？1628；SC12×1+3：解析器框 1663、标题/段落/表格标签 1819+12k；SC13×1+4：灰「?」1925、四段「chunk」标签 2004+2i；SC14×5：切多大？2063 / 太大 2098 / 太小 2133 / 常见做法 2173 / 重叠 2261；SC15×4+1：沿标题边界 2380 / BM25 2572 / Anthropic 2498 / Contextual Retrieval 2500 / −49% 计数 2606）。
- **改后**：**0 处**（SC11–SC15 全部不在白名单）。GlitchIn → `SoftIn`（ui.tsx，8 帧淡入 + 10px 上浮，f0 不变）；循环/手写的 `glitchOpacity(n)` → `fadeIn(n, 8)`（DocCard `labels`/`tagOp` 数组、SC15 −49% 计数容器）。入场帧全部保持原节拍。
- **保留清单**：无。上表镜头描述里的"glitch"字样均已失效，以本节为准。
- g3ui.tsx 内无内置 GlitchIn，无需加 `glitch?` 开关。
- 自检：`npx tsc --noEmit` 通过；tag x34（`rm -rf build_dev_x34` 后重 bundle）出 20 张 still 到 `RAG/stills/X34/G3/`（每处改动 f0+4 / f0+12：1542/1550、1618/1626、1667/1675、1823/1831、1929/1937、2008/2016、2067/2075、2177/2185、2502/2510、2610/2618），Read 核对：中段半透明 + 略低 2–4px，完成帧位置/尺寸与改前一致。
