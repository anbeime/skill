# G7 构建笔记（第 4 章上半：SC31–SC37，S31–S37，帧 5742–6990）

预览合成 `RagG7`；只改 `src/rag/shots/G7/**`。所有动画为 N 的纯函数（`N = useCurrentFrame() + F0`），随机仅 `rnd`。

## 镜头表
| id | 帧 | 文件 | 内容 |
|---|---|---|---|
| SC31 好不好？ | 5742–5821 | SC31.tsx | 5 枚小 Pill 迷你流水线（问题→检索→重排→生成→回答，y380）2 帧错峰 GlitchIn + 箭头自根部长出；5778 Orbitron 紫「?」缩放入场 + 脉冲；5782 起 Pill 依次闪紫。不离场。 |
| SC32 拆成两半 | 5822–5946 | SC32.tsx | 承接 SC31 几何（问号上浮淡出 12 帧）；5830 从「重排｜生成」之间裂开 ±80px（easeInOutPow 16 帧）+ 中缝白竖线闪 + 中间箭头淡出；5869 紫虚线框 draw-on +「检索质量」+ 绿勾；5907 橙虚线框 +「生成质量」+ 绿勾。不离场。 |
| SC33 指标与 RAGAS | 5947–6212 | SC33.tsx | 5947–5961 两框从 SC32 几何变形为高框，流水线上移成框内表头、绿勾淡出；5953 左列 Recall@k/MRR/nDCG 三枚 MetricPill 2 帧错峰滑入；6043 右列 Faithfulness/Answer Relevancy/Context Precision/Context Recall（后两枚灰）；6108「RAGAS」紫 Pill glitch + 两侧横线外长 + 灰小字全称。6198 起加速下摇 + 淡出。 |
| SC34 忠实度 > 流畅度 | 6213–6406 | SC34.tsx | 答复卡（差旅报销语境三行）打字机 1.2 帧/字 + 绿标「流畅」(6255)；来源卡「员工手册 p.12：住宿标准每天 500 元」滑入，引线 draw-on → 红叉 (6286) +「证据错误」红标 (6290)；6323 天平缩放入场，6344 梁向「忠实度」倾斜 12°（easeOutCubic 21 帧）+ 紫亮，底部灰字「忠实度 > 流畅度」。6395 起 12 帧淡出。 |
| SC35 进化 | 6407–6450 | SC35.tsx | 6413「RAG」Audiowide 120px GlitchIn（slices 20 / rgbSplit 8）；6427 起三枚灰 Pill（GraphRAG / Agentic RAG / 多模态 RAG）2 帧错峰从大字右缘飞出成扇形 + 灰箭头。不离场（SC36 硬切）。 |
| SC36 GraphRAG | 6451–6709 | SC36.tsx | 三张 DocIcon 滑入；6457「GraphRAG」Exo 2 + 6469「Microsoft Research, 2024」；6496 箭头，6497 起 14 节点按 rnd 序 1 帧错峰亮起、6508 起 19 条边 draw-on、6518 标签「公司 A」「产品 X」「合作」；6574 三个社区紫径向渐变圆缩放入场 + 6580 三张「社区摘要 ①②③」卡 glitch + 6590 虚线连线；6608 问句 Pill「这批文档整体讲了什么？」自右滑入 + 6618 三支箭头指向摘要卡；6677「全局问题」紫 Pill glitch + 脉冲。6696 起加速下摇 + 淡出。 |
| SC37 Agentic RAG | 6710–6990 | SC37.tsx | 6716「Agentic RAG」；6720 中心 LLMIcon；6760 环（r170）上三节点「检索 / 评估够不够 / 改写问题」缩放入场，6766 出口节点「回答」，6772 弧形箭头 draw-on，6784 灰虚线出口；6808 轮次计数「第 N 轮」(Orbitron 数字 + 三点)；6810 起橙球沿环跑 3 圈（角度 kf 含停顿），到「评估」停 8 帧闪红叉两次（6820 / 6858），第三次 6896 变绿勾 → 6904 沿出口滑到「回答」，回答变紫 + 脉冲；6879「Deep Research」紫 Pill；6963「=」glitch + Deep Research 脉冲。不离场（SC38 硬切）。 |

`BG_G7 = []`（全部用默认雾底 + 星点）。

## 复用的图元 / 组内新增
- `../../ui`：Pill / Box / CText / TechText / Svg / LineArrow / ArrowH / Check / Cross / DocIcon / LLMIcon + 调色板 + fadeIn/fadeOut/slideUp/scaleIn/exitAccel。
- `../../common`：GlitchIn / kf / slideIn / emphasisPulse / easeInOutPow / easeOutCubic / rnd / FONT_TECH / FONT_ORB / FONT_WIDE / FONT_HEAVY。
- 组内 `g7ui.tsx`（未改 ui.tsx）：
  - `PIPE/pipeX/arrowX/PipePill/PipeArrow`：SC31–33 共用迷你流水线几何（x0 170，w 140，h 56，gap 60，cy 380；SPLIT_DX 80）。
  - `DashFrame`：圆角虚线框，draw-on 用 `conic-gradient` mask 沿周长顺时针揭示（无 SVG filter）。
  - `CornerTag` / `MetricPill`（Exo 2 紫英文 + Noto 白中文，dim 灰态）/ `QMark`（Orbitron「?」）。
  - `Balance` + `Pan` + `GradBall`：沿用 R6 SC025 天平造型缩小版（支点 (900,300)、半梁 150、吊线 82）。
  - `exitOut(ex,len)`：幂缓入下摇 1.2·t² + 6.7%/帧淡出，末 6 帧线性收 0（保证硬切前为全透明）。
  - `mixHex/flash/lerp/EASE`。
- 可考虑并入 ui.tsx 的：`DashFrame`（虚线框 draw-on）、`MetricPill`（中英双语 Pill）、`Balance`（其它组若再用天平）。

## 关键参数
- 节拍对齐：各元素入场 = 字幕块起始 −2 帧（GlitchIn 12 帧在 +10 处稳定）；列表 2 帧错峰；箭头/边 draw-on 12–16 帧；缩放入场 21 帧；虚线框 20 帧。
- 英文拼写依据 research/RAG调研.md §4.1/4.2/5.1/5.2：Recall@k、MRR（平均倒数排名）、nDCG（归一化折损累计增益）、Faithfulness 忠实度、Answer Relevancy 答案相关性、Context Precision 上下文精确率、Context Recall 上下文召回率、RAGAS = Retrieval-Augmented Generation Assessment、GraphRAG + Microsoft Research, 2024、Agentic RAG、Deep Research。画面无其他数字。
- 示例文本沿用全局约束「差旅报销」：答复「住宿上限每天 600 元[1]，一线城市 800 元[2]。超出部分请先向部门审批。」；来源卡「来源 [1] · 员工手册 p.12 / 住宿标准：每天 500 元」（与答复矛盾，用于「证据是错的」）。
- 性能：无 SVG filter（BLOOM 为 CSS drop-shadow）；每镜头 ≤2 个全幅 Svg；单帧 DOM 最多约 SC36 ≈ 150 节点、SC33 ≈ 120；GlitchIn 仅 SC35 用 rgbSplit（1 个 filter 实例）。

## 自检
- `npx tsc --noEmit`：通过（每镜头写完各跑一次，最终 0 错误）。
- still 目录：`rag/stills/G7/`（f_NNNN.png，共 73 张；组界 `boundary_5742_SC31_first.png`、`boundary_6990_SC37_last.png`）。
  - SC31：5743/5752/5760/5779/5790/5806/5821 ✓ 「?」Orbitron 正常，Pill 依次闪紫。
  - SC32：5823/5831/5838/5846/5871/5882/5912/5946 ✓；发现并修复：Check 在 p=0 时因 round linecap 露出绿点 → 未开始 draw-on 不渲染。
  - SC33：5948/5955/5962/5975/6050/6070/6112/6130/6205/6212 ✓ 变形连续；RAGAS 灰小字 y606 在字幕带 (637) 之上。
  - SC34：6220/6232/6258/6282/6292/6310/6330/6350/6375/6400/6406 ✓ 天平向忠实度倾斜、紫亮。
  - SC35：6408/6414/6420/6428/6434/6442/6450 ✓。
  - SC36：6452/6460/6470/6500/6510/6530/6580/6590/6600/6615/6635/6680/6700/6709 ✓；发现：顶部标签 y135 与 G0 HUD 副标 (y≈96) 过近 → 下移到 y158/196（SC37 同步到 y160）。
  - SC37：6717/6724/6762/6770/6790/6812/6822/6838/6862/6880/6897/6910/6925/6965/6990 ✓ 球停顿/红叉/绿勾/轮次/「=」均对拍。
- 字幕带 y637–690 与进度条 y687+：内容最低点 SC34「忠实度 > 流畅度」y≈600、SC33 灰小字 y≈617；离场下摇期间（SC33 6198–6212、SC36 6696–6709）内容会淡出着穿过字幕带（协议允许的加速离场）。

## 30 帧测渲（§6）
见文末「测渲记录」。

## 设计偏离 / 待主会话决定
> 2026-09-06 主会话已确认：以下 1–4 项全部按现状保留，G7 不再改动，等待成片 QC。

1. **SC37 环形拓扑**：分镜写「四节点顺时针同环」，但「回答」在环上会让球每圈都路过它、语义不通；改为三节点循环（检索→评估够不够→改写问题）+「回答」作为评估通过后的右侧出口分支。如需严格四节点同环可改 `RING` 表。
2. **SC33 指标中文**：MRR / nDCG 补了调研文档中的中文全称（平均倒数排名 / 归一化折损累计增益），Context Precision / Context Recall 也补了中文并作灰态（旁白未提及）。
3. **SC34 来源卡文案**：为表现「证据是错的」，来源卡写「住宿标准：每天 500 元」与答复 600 元矛盾——这是示例语境内的虚构数字，不是事实数据；若不希望画面出现 500，可改为无关内容（如「餐饮补贴」）。
4. **顶部标签与 G0 HUD**：第 4 章 G0 的 HUD 带英文副标（y≈96），我把组内顶部英文标签放在 y158–160；若 G0 副标位置有变，可再调。
5. 上下文：本次构建期间磁盘一度写满（ENOSPC）导致 bundle 失败，已通知主会话；`build_dev_g7_*` 旧包已删，`build_dev_g7_6` 完工后也已删除，主会话 QC 请用新 tag 重新 bundle。

## 测渲记录
（由 `time npx remotion render build_dev_g7_6 RagG7 /tmp/rag_test_G7 --sequence --image-format=jpeg --frames=… --log=error` 得出）
- SC36 6580–6609（30 帧）：4.63 s（≈6.5 fps，30 张 jpeg）
- SC37 6850–6879（30 帧）：5.19 s（≈5.8 fps，30 张 jpeg）

## QC v1 修复（2026-09-06，依据 rag/qc/qc_v1_C4.md §1；bundle tag `g78`，still 见 `rag/stills/F78/`）
只改 `src/rag/shots/G7/**`；`npx tsc --noEmit` 通过。

| QC 条目 | 严重度 | 修法 | 核对 still |
|---|---|---|---|
| SC35→SC36 6450｜6451 硬切落到空帧 | 中 | SC35 末 6 帧 `exitOut(N−6444, 6)`（下摇 1.2·ex² + 淡出，6450 恰为 0）；三处「硬切」（SC35/SC37/SC39）统一采用「前一镜头末 6–8 帧 exitOut」而非提前下一镜头入场（下一镜头的关键词节拍不能再提前 6 帧以上） | 6446 / 6448 / 6450（主区 >60 亮度像素 353 ≈ 星点基线）/ 6451 |
| SC37→SC38 6990｜6991 组界硬切落到空帧 | 中 | SC37 末 8 帧 `exitOut(N−6982, 8)`，6990 恰为 0；G8 SC38 6999 入场 | 6985 / 6988 / 6990（301）/ 6991（310） |
| SC33 角标「检索质量 / 生成质量」字号小 | 中 | `CornerTag` 默认 130×34/22px → 156×40/26px；SC32 角标 y 318→312（避免压到流水线 Pill 顶 352）、SC33 角标 y 133→130 | 5882 / 5913 / 5975 |
| SC36 节点标签「公司 A / 产品 X」16–17px、「合作」15px | 中 | 20→23px（weight 700，y −26，双层黑影）；「合作」19→22px（y 276）；与相邻节点/边不撞 | 6530 |
| SC32 DashFrame conic mask 露出扇形填充 | 低 | 填充层与描边层分开：conic mask 只作用于虚线描边，填充 opacity = p 线性淡入 | 5875 / 5913 |
| SC33 nDCG 从框底外滑入 | 低 | 两列 MetricPill 滑入 Δ 90→30（框内） | 5958 |
| SC33 RAGAS 灰小字偏暗 | 低 | 颜色 GREY → #C8C8C8（22px 不变） | 6130 |
| SC34 来源卡首行 18px、底部结论字灰 | 低 | 首行 18→20px；「忠实度 > 流畅度」灰→白（「>」仍紫）+ 微光 | 6300 / 6375 |
| SC37 轮次数字换位 12 帧 glitch 中间空档 | 低 | 第 2/3 轮数字改 6 帧短序列 `[0.6,1,0.5,1,0.8,1]`（无全灭帧）；首轮仍 12 帧 | 6851 / 6889 |

**未修**（2 条低项）：
- SC32 5872–5877 角标 glitch 与虚线框 draw-on 不同步：角标延后 4 帧会使「检索质量」可见帧到 5876（节拍 5869 +7，超 +3 容差）；改 fadeIn 又与全片「标签 GlitchIn」词汇不一致，保留。
- SC35/G0 6415–6425 HUD「进阶」与「RAG」glitch 同帧全灭：属 G0 HUD 换词方式（建议 G0 用 2 帧交叉淡入或把 HUD glitch 错开 4 帧），G7 不动；「RAG」6413 已是节拍 −2，再提前会超 −6。

另：G7 `exitOut` 现在被 SC33/SC35/SC36/SC37 四处共用；G8 `shared.tsx` 复制了同式 `exitOut`，两组离场曲线一致。

## 闪烁整改（2026-09-06，用户裁定「不要给每段出现的字都加闪烁，只给重点加」，依据 AGENT_RAG_BUILD_RULES §8）
只改 `src/rag/shots/G7/**`；非重点入场一律换 `ui.tsx` 的 `SoftIn`（8 帧淡入 + 10px 上浮，容器同为 absolute inset:0，几何/入场帧 f0 均不变）。`npx tsc --noEmit`：G7 无错误（当时仅 G1/SC05 有他组在改的 `GlitchIn` 未定义报错）。bundle tag `x78`，still 见 `rag/stills/X78/`（每处 f0+4 / f0+12 各一张 + 7 张拼版 `sheet_G7_*.png`）。

| 计数 | GlitchIn 代码处 | 运行时实例 |
|---|---|---|
| 改前 | 15 | 21（SC31 循环 ×5、SC36 卡片循环 ×3） |
| 改后 | 4 | 4 |

**保留（白名单）**：SC33「RAGAS」Pill（6108）、SC35「RAG」大字（6413，保留 slices 20 / rgbSplit 8）、SC36「GraphRAG」（6457）、SC37「Agentic RAG」（6716）。

**换成 SoftIn**：
- SC31 5 枚流水线 Pill（5748 起 2 帧错峰）
- SC32 角标「检索质量」（5871）/「生成质量」（5909）
- SC33 RAGAS 灰小字全称（6108；从 RAGAS 的 GlitchIn 里拆出来单独 SoftIn，Pill 仍 glitch）
- SC34 「流畅」绿 Pill（6255）/「证据错误」红 Pill（6290）
- SC36 三张「社区摘要」卡（6580 起 4 帧错峰）/「全局问题」Pill（6677，脉冲不变）
- SC37 「Deep Research」Pill（6879）/「=」（6963）/ 轮次计数「第 N 轮」+ 三点（6808）/ 轮次数字（6808 / 6848 / 6886，`len 6, dy 6` 短淡入；原 `GLITCH_SHORT` 序列已删）

核对 still：5752/5760、5875/5883、6112/6120、6259/6267、6294/6302、6584/6592、6681/6689、6812/6820、6852/6860、6883/6891、6967/6975 —— f0+4 均为半透明中段、f0+12 完全到位，位置与尺寸与改前一致。SC35 未动。
之前「未修」里的「SC32 角标 glitch 与虚线框 draw-on 不同步」一条随本次改 SoftIn 自然消解（淡入无全灭帧）。
