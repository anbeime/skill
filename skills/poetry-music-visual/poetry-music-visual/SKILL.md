---
name: poetry-music-visual
description: 为古诗词提供配图与配乐的全流程创作指导；支持深度解析诗词意境、生成画面描述、提供配乐创作蓝图（Suno格式）；适用于诗词可视化、MV创作、文化传播等场景
---

# 古诗词配图配乐创作指导

## 任务目标
- 本 Skill 用于：将古诗词转化为视觉与听觉双重艺术形式
- 能力包含：
  1. 深度解析古诗词的意象、情感、表现手法及文化背景
  2. 生成与诗词意境契合的配图场景描述
  3. 提供纯音乐配乐创作蓝图（Suno 格式的风格标签+结构指令）
  4. 整合视觉与听觉元素，确保艺术风格的统一性
- 触发条件：用户需要为古诗词配图、配乐或制作诗词MV

## 操作步骤

### 1. 诗词深度解析
根据用户提供的信息（标题、作者、内容）进行多维度分析：
- **意象识别**：提取诗中核心意象（如月、山、水、花、鸟等）
- **情感基调**：判断主色调（宁静、激昂、忧伤、豪迈等）
- **时空背景**：理解创作年代、季节、时辰、地理环境
- **表现手法**：分析修辞手法（比兴、象征、虚实结合等）
- **文化内涵**：关联历史背景、作者生平、社会文化

### 2. 配图场景设计
生成2-3组配图方案，每组包含：
- **核心画面**：主场景描述（构图、色调、主体元素）
- **细节元素**：辅助意象的视觉呈现
- **氛围营造**：光线、天气、质感等细节
- **风格建议**：中国风、水墨、油画、现代插画等

生成规范：
- 使用描述性语言，确保画面可被图像生成模型理解
- 控制在100-150字/场景，突出关键视觉元素
- 避免抽象词汇，使用具象化表达

### 3. 配乐创作蓝图（Suno 格式）

生成纯音乐创作指导，严格遵循以下格式：

#### 3.1 歌曲风格（Style of Music）
生成精准标签，用逗号分隔，需包含以下维度：
- **核心曲风** (Genre)：Orchestral, Cinematic, Ambient, Electronic, Neo-classical, China-Chic (国潮), World Music 等
- **情绪氛围** (Mood & Atmosphere)：Epic, Calm, Melancholic, Mysterious, Uplifting, Dreamy, Space 等
- **核心乐器** (Instrumentation)：Piano, Guzheng, Erhu, Flute, Strings, Harp, Atmospheric Pads 等
- **时代/节奏** (Era & Rhythm)：Traditional, Modern, Mid-tempo, Slow Build, Rubato (自由节奏), 4/4 Beat 等

示例：
```
China-Chic, Cinematic, Ambient, Dreamy, Mysterious, Guzheng, Erhu, Pipa, Strings, Atmospheric Pads, Traditional Chinese Instruments, Modern Fusion, Slow Build, Rubato
```

#### 3.2 音乐结构与导演指令（Lyrics）
使用 Suno 可识别的结构标签，通过括号()添加器乐和氛围指令：

**结构标签**：
- [Intro]：前奏，设定基调
- [Verse]：主歌，引入主题旋律
- [Chorus]：副歌，情感高潮部分
- [Bridge]：桥段，提供对比或转折
- [Instrumental Solo]：器乐独奏
- [Outro]：尾奏，自然收束

**导演指令示例**：
- 指导乐器：(Guzheng enters with gentle plucking), (Erhu melody fades in)
- 描述动态：(Music gradually swells), (Tempo slows down to dreamy pace)
- 添加音效：(Sound of gentle wind and distant birds), (Soft rain drops)

**完整示例**：
```
[Intro]

[Verse 1]
(Soft Guzheng plucking creates a mysterious atmosphere)
(Minimal strings provide a subtle backdrop)

[Chorus]
(Main theme emerges with fuller instrumentation)
(Harp and flutes join, creating an expansive cinematic feel)

[Instrumental Solo]
(Erhu takes center stage with a poignant melody)
(Strings and atmospheric pads provide support)

[Bridge]
(Music softens, becomes more reflective)
(Subtle wind chimes in the background)

[Final Chorus]
(Full orchestral texture returns)
(Guzheng and Erhu intertwine)

[Outro]
(Music gradually fades)
(Leaving only a soft wind effect)
```

### 4. 整合与优化
- **风格一致性检查**：确保配图风格与配乐风格协调
- **节奏匹配**：配图的视觉节奏与音乐结构对应
- **情绪递进**：视觉与听觉的情绪曲线保持同步

## 资源索引
- 配图参考：[references/poetry-imagery.md](references/poetry-imagery.md)（常见意象的视觉表现方式）
- 配乐参考：[references/music-style-guide.md](references/music-style-guide.md)（不同情绪的音乐风格搭配）
- 输出模板：[assets/output-templates.md](assets/output-templates.md)（标准输出格式）

## 注意事项
- **智能体职责**：
  - 配图：直接使用智能体的图像生成能力
  - 配乐：提供创作蓝图，供外部音乐生成服务（如 Suno）使用
- **语言风格**：使用优美文雅的表达，营造与诗词文化协调的氛围
- **输出格式**：配图描述与配乐蓝图清晰分隔，便于后续使用
- **用户引导**：询问用户是否需要：
  - 生成实际配图（智能体可直接完成）
  - 调整配图风格（中国风、现代插画等）
  - 修改配乐情绪（宁静、激昂等）
  - 了解诗词的历史背景或作者生平

## 使用示例

### 示例1：李白《静夜思》
**配图方案**：
- 核心画面：夜晚窗前，一轮明月高悬，月光洒在床前，诗人凝视着窗外的月亮
- 细节元素：窗棂的木纹、地面如霜的月光、远处的树影
- 氛围营造：冷色调（蓝色、银白），柔和的光线，静谧宁静
- 风格建议：中国水墨风，留白意境

**配乐蓝图**：
```
Style of Music:
China-Chic, Ambient, Melancholic, Dreamy, Guzheng, Flute, Strings, Atmospheric Pads, Slow Build, Rubato

[Intro]

[Verse 1]
(Gentle Guzheng plucking, slow and contemplative)
(Soft atmospheric pads create a dreamy night atmosphere)

[Chorus]
(Flute melody enters with a nostalgic tone)
(Strings provide a subtle harmonic support)

[Bridge]
(Music becomes slightly more emotional)
(The full texture of strings and Guzheng)

[Outro]
(Guzheng melody gradually fades)
(Leaving only the sound of soft wind)
```

### 示例2：王维《山居秋暝》
**配图方案**：
- 核心画面：秋日傍晚的山林，空山新雨后，明月松间照，清泉石上流，浣女在溪边洗衣服，渔舟在荷花塘中归
- 细节元素：松树上的月光、清澈的溪流、浣女的身影、渔舟划过荷塘的涟漪
- 氛围营造：暖色调（金黄、橙色），柔和的夕阳光，宁静而生动
- 风格建议：传统山水画风格，注重意境

**配乐蓝图**：
```
Style of Music:
China-Chic, Cinematic, Calm, Uplifting, Pipa, Guzheng, Dizi, Strings, Percussion, Mid-tempo, Rubato

[Intro]

[Verse 1]
(Gentle Pipa picking, mimicking flowing water)
(Soft Dizi melody, like birds singing in the forest)

[Chorus]
(Fuller instrumentation with Guzheng and strings)
(The feeling of autumn evening, peaceful and warm)

[Instrumental Solo]
(Dizi takes a brief melodic solo)
(Representing the flowing water and natural sounds)

[Bridge]
(Music becomes slightly more rhythmic)
(Light percussion like water drums or woodblocks)

[Final Chorus]
(Full ensemble returns with warm harmonies)
(Capturing the joy and tranquility of mountain life)

[Outro]
(Music gradually softens)
(Like the evening settling into night)
```

## 使用流程建议
1. 用户输入古诗词信息
2. 智能体执行步骤1-3，生成完整创作指导
3. 询问用户是否需要：
   - 生成实际配图（智能体直接完成）
   - 使用配乐蓝图在音乐生成平台（如 Suno）创作音乐
   - 调整任何部分以更符合预期
4. 如需迭代，基于用户反馈优化配图描述或配乐蓝图
