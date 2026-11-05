# 风格指南（视觉体系）

一句话：**黑底幕底（默认点阵波，可选星点 + 底部雾底渐变）**上的白线条 MG。所有图形是「黑填充 + 白描边 2–3px」或「紫/橙纯色块 + 白描边」；中文超粗黑体（Noto Sans SC 900，常 scaleX .8–.85 压窄）；英文技术词紫色粗斜体 Exo 2；常驻顶部紫胶囊 HUD（下面那行英文副标是灰色 22px 小字，不是第二个标题）、底部 44px 白字黑边字幕、半透明章节进度条。参考帧：`examples/rag/frames/ref_*.jpg`（先看再画）。

## 1. 画布与安全区（1280×720@30fps）
| 区域 | 像素 | 说明 |
|---|---|---|
| 黑底 | 全幅 #000 | Main 唯一的不透明黑底；镜头组件**不要**再画不透明黑底 |
| 雾底 Fog | y415→687 线性 #000→#212121，687→720 恒 #212121 | 全片常驻（`common/Fog.tsx`） |
| 星点 StarField | 出生区 0–687，80 颗 2–4px，亮度 35–255 偏暗，漂移 0.4–3.2px/帧，寿命 60–200 帧，逐帧 ±30% 闪烁 | 确定性纯函数（`common/StarField.tsx`）；`BG_Gn` 可按帧区间关掉 `{fog:false, stars:'none'}` |
| 点阵波 DotFieldBg（**默认**，替代 雾底 + 星点） | 设计坐标 960×540 等比放大：点距 48px、半径 2–2.7px、底色 #0b0c11、点色 #cfe0ff，透明度 (0.2 + 0.6k²)×径向边缘衰减，斜向波前约 9.3 s 扫过一遍，叠 .06 静态噪点抗色带 | video-talkcraft `motion-systems/backdrop.tsx` 的 dot-field-wave 移植（`common/DotFieldBg.tsx`）；`config.bg = 'dots'` 启用，与星点雾底互斥；`BG_Gn` 的 `stars:'none'` 同样关掉它；屏幕空间静态纹理，不跟运镜；`frame_metrics.py` 按同一网格把点抠掉再统计 |
| 顶部 HUD 胶囊 | (533,28,216,51) r25.5，紫 #6630F8 填充 + 白 2px 边，33px 700 白字；英文副标 Exo 2 30px 紫在 y≈94 | 覆盖层绘制；换词 8 帧淡入 |
| 流程轨（可选） | 胶囊 top 118 高 44 宽 150，中心 x 240/440/640/840/1040，间小箭头 | 当前步紫、已过 #2A2A2A 底白字、未到黑底灰边灰字 |
| **内容主区** | 无轨的章 y110–620；有轨的章 y175–620；x60–1220 | 关键信息只放这里 |
| 字幕带 | CSS top 637，墨迹 y644–684，44px Noto 700 白 + 4px 黑描边（16+8+4 向 text-shadow 环）居中 | **不放任何内容**；入场轨迹不得穿过 |
| 进度条 | y687–720 半透明：已播 rgba(190,170,250,.52)、未播 rgba(243,243,243,.32)；n−1 根白分隔线；章名 Noto 900 24px skewX(−10°) scaleY(.9)，当前章 α1 其余 .55 | 内容穿过会被提亮，只允许全幅背景/大图形穿过 |
| z 序 | 黑底 < 幕底（Fog + 星点，或 DotFieldBg）< 实拍 < 覆盖层 < 镜头 < 片尾压黑 < 进度条 < aboveBar 镜头 < 字幕 | |

## 2. 调色板（`src/ui.tsx` 常量）
| 名 | 值 | 语义 |
|---|---|---|
| PURPLE | #6630F8 (102,48,248) | 当前重点 / 激活 / 品牌；胶囊、盒、当前步 |
| PURPLE_LIGHT | #A175F1 | 高光端、穿过进度条后的紫、active 卡边 |
| PURPLE_TECH | #6530F4 | Exo 2 英文技术词 |
| PURPLE_DEEP | #5A3AD5 | 曲线、标题硬投影 |
| ORANGE / CORAL | #F05F41 / #F16043 | 指标数字、警示、"另一方"、查询点 |
| RED_DEEP | #EC081F + 双层红柔光 | 深红警示块（幻觉/不靠谱） |
| GREEN | #8FF740 | 绿勾（正确） |
| GREY / GREY_MID / GREY_LINE / GREY_LIGHT | #A0A0A1 / #747474 / #4A4A4A / #D4D4D4 | 非重点文字 / 灰块 / 网格线 / 文本线条 |
| WHITE / 黑 | #FFF / #000 | 文字、描边、箭头 / 填充 |
| MAGENTA / CYAN | #D100D6 / #58FFEE | 只出现在 glitch RGB 错位副本 |
| 柔光 | GLOW_PURPLE（12px/42px 双层）、GLOW_PURPLE_S（24px 8px）、GLOW_ORANGE、GLOW_RED、BLOOM（drop-shadow 3px 白 .5）、TEXT_GLOW | |
**颜色即语义**：紫=重点/我们的、灰=未激活/背景、橙红=指标/警示/对方、白=结构文字、绿=正确。一帧里紫色重点不超过一处大面积。

## 3. 字体（`public/fonts`，全部 OFL；`common/lib.tsx` 的 `Fonts` 在 Main 挂一次）
| 角色 | 族 | 字号/字重/变形 |
|---|---|---|
| 大标题（片名、章节卡、镜头重点词） | Noto Sans SC | 56–96px / 900 / scaleX .85，可加 1px 黑描边 paintOrder stroke |
| HUD 胶囊字 | Noto Sans SC | 33px / 700 / letterSpacing 1 |
| 胶囊/标签 | Noto Sans SC | 24–30px / 600–800 / textDy −2（CJK 墨迹偏低 3–7px 要预扣） |
| 图内说明 | Noto Sans SC | 22–26px / 500–600 / 灰或白；**最小 22px** |
| 字幕 | Noto Sans SC | 44px / 700 / 无压缩 |
| 英文技术词 | Exo 2 Italic | 26–38px / 600–700 / scaleX .8 / 紫；TechText 组件 |
| 宽体展示字（片名缩写、大写词） | Audiowide | 96–150px / 字距 6 / 白 + 紫硬投影 6px |
| 数字/章序号/计数 | Orbitron | 24–110px / 700 / tabular-nums |
| 公式 | Times New Roman Italic | 34–36px 白 + drop-shadow 3px |
| 代码/向量数字 | 等宽 FONT_MONO | 22–24px |

### 3.1 英文片（`config.ts` 的 `lang: 'en'`）
Noto Sans SC 自带完整拉丁字形（实测 wght 100–900 全覆盖），所以**不需要再加字体**：正文、标签、字幕仍用 `FONT_HEAVY`，展示大字用 Audiowide / Orbitron。三条差异由 `lang` 自动生效，别在镜头里手写死值：
- **不压窄**：`SQUEEZE`（`common/lib.tsx`）中文 .85 / 英文 1。拉丁字母 scaleX .85 会明显变形。片头、章节卡已经用它。
- **基线不预扣**：`CText` 的 `dy` 默认取 `TEXT_DY`（中文 −2 / 英文 0）——CJK 行盒的墨迹偏低，拉丁不偏。
- **宽度兜底**：字幕、进度条章名、章节卡标题、片头大字都过 `fitSize()`（`common/textfit.ts`，按实测 em 宽估算，纯函数所以渲染确定）。它只是兜底：超预算说明文案该切，见 `narration-storyboard.md` §5。
- 英文片里 `TechText`（Exo 2 紫斜体）只用于**术语强调**，不要整句用——整段斜体在英文里读起来像引文。
- 一行英文大写词比中文占宽得多：Audiowide 大写平均 .79em、Orbitron .82em、Noto 大写 .67em / 小写 .57em（fontTools 实测）。估宽用 `textW(s, size, EM_WIDE|EM_ORB|EM_TECH, letterSpacing)`；带 `letterSpacing` 的大字（片头、章节卡）要把它传进去——它是固定 px、不随字号缩，`fitSize()` 同样有这个参数。

## 4. 图元目录（`src/ui.tsx`，镜头 `import {…} from '../../ui'`）
| 组件 | 用途 | 关键 props |
|---|---|---|
| `CText` | 墨迹中心定位单行文字 | cx cy size weight color scaleX dy italic shadow |
| `TechText` | Exo 2 紫斜体英文 | cx cy text fontSize scaleX glow |
| `MonoText` | 等宽多行 | x y size |
| `Box` | 黑底白边矩形（fill 可渐变；dashed；glow） | x y w h r sw |
| `Pill` | 全圆角胶囊 + 居中文字 | Box props + text fontSize weight textDy |
| `TagBlock` | 大标签色块（紫/橙/深红）+ 900 字 scaleX .8 + 同色外发光 | x y w h color text |
| `Svg` | 全幅 1280×720 SVG 容器（默认 BLOOM） | children |
| `LineArrow` | 任意方向箭头，p 自根部长出 | x0 y0 x1 y1 p rodW headL headW dashed |
| `ArrowH` | 水平箭头 div 版（左端锚 scaleX） | x y w p dir |
| `Check` / `Cross` | 绿勾 / 红叉 draw-on（p≤0 不渲染） | cx cy size p |
| `DocIcon` | 折角文档 + 文本线条 + 标签 | x y w h lines label accent |
| `DBIcon` | 数据库圆柱 | cx cy w h label accent |
| `ChunkCard` | 文本块卡（active 紫边柔光） | x y w h lines active title |
| `LLMIcon` | 大模型：圆角方块 + 三层神经元点阵 | cx cy size label glow |
| `Trap` | 倒梯形漏斗层，灰↔紫 k 渐变 | cx y wTop wBot h k text |
| `TopCapsule` | 顶部 HUD 胶囊（覆盖层用） | N f0 text w tech glitch |
| `Counter` | tabular 数字 | cx cy value size |
| `SoftIn` | **默认入场**：8 帧淡入 + 10px 上浮（签名同 GlitchIn） | N f0 children len dy |
| `GlitchIn`（common） | 12 帧透明度闪烁入场，rgbSplit/slices 变体 | N f0 seq rgbSplit slices |
| 小工具 | `fadeIn/fadeOut/slideUp/scaleIn/exitAccel/exitFade/stagger/abs` | |
按主题补图元时放进 `ui.tsx`（如样片补了 DocIcon/DBIcon/ChunkCard/LLMIcon），组内特有的放组目录 `gNui.tsx`。参考实现：`examples/rag/shots_src/*/`。

光效 / 高光时刻 / 纵深 / 运镜图元在 `src/fx.tsx`（`import {…} from '../../fx'`）：
| 组件 | 用途 |
|---|---|
| `LightBar` / `LightSweep` | 紫光条横扫（登场型高光时刻开场三轮；**全片 ≤2 处**，只给扫光白名单里的镜头） |
| `TechSub`（`ui.tsx`） | 中英配对的副标：主体下面那行另一种语言，灰色小字（HUD 22px / 章节卡 26px），**不用紫色、不与主体同大小**——紫色只给当前重点，等大同色会读成两个主体 |
| `StageLine` | 中央舞台光线：展宽 → 呼吸 → 节拍帧白闪消失 |
| `GhostText` / `ghostOpacity` | 主角大字的白描边轮廓 10% 预示 |
| `HaloRing` | 主体脚下紫色光环，可分 back / front 夹住主体 |
| `HeroGlow` | 任意矩形主角的双层紫柔光 + 30 帧呼吸 |
| `BigNumber` / `countTo` | Orbitron 大数字 + 紫硬投影 + 计数 |
| `Sparkle` / `GradBall` | 四角小星 / 顶亮底黑小球 |
| `TiltPlane` | 倾斜平面（纵深层） |
| `CameraRig` / `camAt` | 定点推近 / 拉远 / 平移 / 整页滚动 / 承接位移 |
| `SET_PIECE` / `setPiece` | 登场型高光时刻的标准相对帧 |

## 5. 版式规律
- **标题卡**：中心 (640,345–372)，Noto 900 80px scaleX .85 + 下方 3px 白短线 300 宽 + Exo 2 副标 y≈470；章序号 Orbitron 54px 紫在 y268。
- **流程图**：节点 Pill 150×44 或 Box 200×70，间距 200，箭头 38–70 宽 shaft 3 headL 22–24；当前节点紫、已过灰底、未到灰边。
- **卡片阵列**：卡 150×92 r8，列距 24，2 帧错峰入场；≥12 张时缩到 70 宽。
- **左右对比**：左 x≈300–380 / 右 x≈900–1000，各配标签 Pill 在上方 y≈250；中间放 ≈ / vs / + 符号 46–60px。
- **图表卡**：440×300 白边黑底，网格 #4A4A4A 1px，坐标字 15–18px，曲线紫 3px，重点红点。
- **公式**：Times Italic 34px 逐 token 绝对定位，每 3 帧出一个 token；灰小字注参数（k=60）。
- **标签 + 说明**：Pill（紫/橙）在上，Noto 24px 白说明在下 12px。
- **信息层级**：一帧一个焦点；说明字灰 #A0A0A1；数字用 Orbitron 橙。
- **尺寸三档与光**（细则 `composition-and-light.md`）：主角 ≥170px 或大字 ≥96px 且必带光；配角 60–110；标签 22–30。上表里的卡 150×92、Pill 150×44 都是**配角尺寸**，不能当主角用；表现「多」用方点阵列，背景只有幕底（星点或点阵波）。
