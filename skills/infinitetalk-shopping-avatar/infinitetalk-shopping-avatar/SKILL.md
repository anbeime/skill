---
name: infinitetalk-shopping-avatar
description: 专为InfiniteTalk项目设计的小省导购员数字人带货提示词生成技能，基于四大智能体协同（提示词生成师、质量管控师、知识库运维师、跨环节适配师），生成适配Image-to-Video模式的结构化提示词（角色固定特征+动作时序+场景环境+音频匹配+光影氛围+技术约束），支持9:16竖屏、5s/幕、音频同步（Suno+chinese-wav2vec2-base）、一致性管控（角色/视觉/情绪），直接对接模型推理流程
---

# InfiniteTalk小省导购员数字人带货提示词生成

## 任务目标
- 本技能用于：为InfiniteTalk项目生成小省导购员数字人带货视频的结构化提示词，直接对接模型推理流程
- 能力包含：
  - 生成适配InfiniteTalk Image-to-Video模式的分镜化提示词
  - 帧级动作时序描述（5s/幕，精确到秒级）
  - 音频同步匹配（Suno音乐 + chinese-wav2vec2-base编码）
  - 一致性管控（角色/视觉/情绪三大维度）
  - 跨工具集成（Suno、AI绘画、InfiniteTalk）
- 触发条件：用户需要生成小省导购员数字人带货视频，使用InfiniteTalk模型进行推理

## 前置准备
- 依赖说明：本技能基于智能体自然语言能力，无需Python依赖
- 环境准备：
  - InfiniteTalk模型环境（已安装，包含chinese-wav2vec2-base编码器）
  - TeaCache + int8量化配置（已配置）
  - 角色参考图（9:16比例，分辨率≥1080×1920）

## 操作步骤

### 标准流程

#### 1. 提示词生成
提示词生成师负责生成适配InfiniteTalk的结构化提示词：

**输入信息**：
- 场景类型（产品推荐/价格对比/促销活动等）
- 商品信息
- 情绪基调
- 五幕情绪递进

**生成流程**：
1. 读取 [references/infinitetalk-parameters.md](references/infinitetalk-parameters.md)，确认核心参数配置
2. 读取 [references/prompt-structure.md](references/prompt-structure.md)，遵循提示词结构规范
3. 读取 [references/scene-templates-infinitetalk.md](references/scene-templates-infinitetalk.md)，调取场景模板
4. 生成五幕提示词，每幕包含：
   - 角色固定特征（严格遵循固定描述）
   - 动作时序（5s内帧级描述，精确到秒级）
   - 场景环境（背景、前景、道具）
   - 音频匹配（语音类型+音乐风格+音频对齐规则）
   - 光影/氛围（色温、光照类型、情绪基调）
   - 技术约束（构图比例、景深、动作强度等）

**输出格式**：
- 中文提示词（可直接作为InfiniteTalk推理脚本的`prompt`参数）
- 参数配置表（duration、aspect_ratio、motion_strength、face_consistency等）

#### 2. 质量核查
质量管控师负责核查提示词质量：

**核查维度**：
1. **技术参数匹配度**：
   - 时长：每幕5s，总时长25s
   - 分辨率/比例：1080×1920（9:16竖版）
   - 动作连贯性：5s内帧级动作描述流畅
   - 角色一致性：严格匹配固定特征描述

2. **角色一致性**：
   - 外貌特征：脸型、眼睛、发型、肤色、唇色
   - 服饰描述：上衣、鞋子、配饰
   - 气质特征：专业亲和、手部姿态

3. **音频匹配性**：
   - 语音类型：语速、语气与情绪匹配
   - 音乐风格：与场景情绪匹配
   - 音频对齐：动作节奏与音乐/语音同步

4. **光影可实现性**：
   - 色温：4000K-5500K范围
   - 光照类型：侧光、顺光、顶光、逆光
   - 光影效果：明暗对比、景深、虚化程度

**核查结果**：
- 通过（pass）：传递给知识库运维师归档
- 不通过（fail）：生成问题清单，反馈给提示词生成师调整（最多2次）

#### 3. 知识库归档
知识库运维师负责归档提示词和知识库更新：

**归档内容**：
- 角色固定特征模板
- 五幕情绪-光影映射表
- 音频风格-动作匹配库
- 场景模板库

**归档格式**：
- JSON格式（便于程序调用）
- 包含完整元数据（场景类型、情绪基调、参数配置）

#### 4. 跨工具集成
跨环节适配师负责跨工具集成和音频/图片适配：

**音频集成**：
1. Suno音乐生成：
   - 提取情绪关键词，生成音乐风格描述
   - 导出为16kHz单声道wav格式
   - 确保时长5s/幕，与提示词严格对齐

2. chinese-wav2vec2-base编码：
   - 使用chinese-wav2vec2-base对音频进行特征编码
   - 生成音频特征文件

3. 导购员语音生成：
   - 根据每幕情绪调整语速/语气
   - 与音乐时长严格对齐（5s/幕）
   - 确保唇形同步

**图片集成**：
1. AI绘画生成：
   - 使用AI绘画生成「动作前画面」
   - 裁剪为9:16比例，分辨率≥1080×1920
   - 保留角色完整特征（无遮挡）

2. 参考图适配：
   - 作为InfiniteTalk的`init_image`参数输入
   - 确保角色固定特征与提示词一致

**InfiniteTalk推理对接**：
1. 加载模型（基础配置）
2. 单幕生成（以第一幕为例）
3. 保存视频（5s/幕）
4. 五幕拼接（总时长25s）

### 可选分支

- 当场景类型为产品推荐：执行 [references/scene-templates-infinitetalk.md](references/scene-templates-infinitetalk.md) 中的产品推荐场景模板
- 当场景类型为价格对比：执行价格对比场景模板
- 当场景类型为促销活动：执行促销活动场景模板
- 当需要跨工具集成：执行 [references/cross-tool-integration.md](references/cross-tool-integration.md) 中的集成方案

## 资源索引

- 核心参数配置：见 [references/infinitetalk-parameters.md](references/infinitetalk-parameters.md)（何时读取：生成提示词前确认参数配置）
- 提示词结构规范：见 [references/prompt-structure.md](references/prompt-structure.md)（何时读取：生成提示词时遵循结构规范）
- 场景模板库：见 [references/scene-templates-infinitetalk.md](references/scene-templates-infinitetalk.md)（何时读取：根据场景类型调取模板）
- 一致性管控规则：见 [references/consistency-rules-infinitetalk.md](references/consistency-rules-infinitetalk.md)（何时读取：质量核查时遵循规则）
- 跨工具集成方案：见 [references/cross-tool-integration.md](references/cross-tool-integration.md)（何时读取：跨工具集成时参考方案）
- 完整示例输出：见 [assets/examples/sample-prompts-infinitetalk.md](assets/examples/sample-prompts-infinitetalk.md)（何时读取：参考完整示例）

## 注意事项

- 严格遵循角色固定特征描述，所有五幕提示词使用相同描述
- 动作时序必须精确到秒级，确保5s内动作连贯
- 音频匹配必须与动作节奏同步，确保唇形同步
- 光影描述必须可实现，色温在4000K-5500K范围内
- 技术约束必须匹配InfiniteTalk能力，确保生成效果
- 充分利用智能体的自然语言能力和分析推理能力，避免为简单任务编写脚本

## 使用示例

### 示例1：产品推荐场景提示词生成

**功能说明**：生成产品推荐场景的五幕提示词

**执行方式**：提示词生成师（智能体自然语言生成）

**关键参数**：
- 场景类型：产品推荐
- 情绪基调：热情专业
- 五幕情绪递进：热情神秘→专业详细→专注生动→自信有力→鼓励坚决
- 技术参数：9:16竖屏、5s/幕、1080×1920分辨率

**输出**：五幕中文提示词、参数配置表

### 示例2：质量核查

**功能说明**：核查提示词质量

**执行方式**：质量管控师（智能体分析推理）

**核查维度**：技术参数匹配度、角色一致性、音频匹配性、光影可实现性

**输出**：质检报告（pass/fail）、问题清单（如不通过）

### 示例3：跨工具集成

**功能说明**：Suno音乐→InfiniteTalk音频对接

**执行方式**：跨环节适配师（智能体理解+自然语言指导）

**关键步骤**：
1. Suno生成16kHz单声道wav音频
2. chinese-wav2vec2-base编码
3. 导购员语音生成（语速/语气匹配情绪）
4. InfiniteTalk推理对接

**输出**：音频编码文件、视频生成结果

## 四大智能体角色职责

### 提示词生成师
- **核心职责**：按提示词结构输出InfiniteTalk专用提示词
- **输入**：场景类型、商品信息、情绪基调
- **输出**：分幕提示词文本、参数配置表
- **关键能力**：理解InfiniteTalk技术参数、创作帧级动作时序描述

### 质量管控师
- **核心职责**：核查提示词与InfiniteTalk能力匹配度
- **核查维度**：动作连贯性、角色一致性、光影可实现性
- **输出**：质检报告、提示词修正建议
- **关键能力**：分析推理、技术约束匹配度评估

### 知识库运维师
- **核心职责**：归档提示词和知识库更新
- **归档内容**：角色固定特征模板、情绪-光影映射表、音频风格-动作匹配库
- **输出**：知识库检索接口（JSON格式）
- **关键能力**：结构化归档、元数据管理

### 跨环节适配师
- **核心职责**：跨工具集成（Suno、AI绘画、InfiniteTalk）
- **集成步骤**：音频适配、图片适配、InfiniteTalk推理对接
- **输出**：音频编码文件、视频生成结果
- **关键能力**：跨工具理解、格式适配、流程集成
