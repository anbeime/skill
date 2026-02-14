---
name: dream-video-prompt-generator
description: 小省导购员数字人带货版即梦视频提示词生成系统，基于四大智能体协同（提示词生成师、质量管控师、知识库运维师、跨环节适配师），按照"主体+运动+场景+（镜头语言+光影+氛围）"公式输出中英文双版提示词，适配5s短视频。确保人物一致性、视觉连贯性、情绪连贯性，支持知识库智能复用和跨工具适配（Suno音乐、AI绘画），为数字人带货视频提供高质量提示词生成服务。
---

# 小省导购员数字人带货即梦视频提示词生成系统

## 任务目标
- 本 Skill 用于：生成小省导购员数字人带货视频的即梦视频生成提示词
- 能力包含：
  - 四大智能体协同：提示词生成师、质量管控师、知识库运维师、跨环节适配师
  - 提示词公式驱动：主体+运动+场景+（镜头语言+光影+氛围）
  - 中英文双版对应：适配国际AI工具需求
  - 一致性保障：人物一致性、视觉连贯性、情绪连贯性
  - 知识库智能复用：同类需求直接调取，新增需求迭代优化
  - 跨工具适配：联动Suno音乐生成、AI绘画生成
- 触发条件：用户需要生成小省导购员数字人带货视频的提示词

## 前置准备
- 无需特殊依赖
- 准备带货视频信息：
  - 场景类型（产品推荐、价格对比、促销活动等）
  - 情绪基调（热情、专业、亲切、紧迫等）
  - 视频时长（默认5s）
  - 分镜幕次（默认5幕）

## 操作步骤

### 标准工作流程（四大智能体协同）

#### 步骤1：需求对接与知识库核查（智能体3：知识库运维师）
**职责**：优先核查知识库，同类需求直接调取，新需求启动协作

- 需求识别：识别场景类型、情绪基调、分镜幕次
- 知识库核查：查询是否存在同类场景的提示词模板
- 直接复用：如匹配，直接调取并返回提示词
- 新增处理：如不匹配，传递给提示词生成师启动创作

**输出格式**：
```json
{
  "demand_type": "产品推荐/价格对比/促销活动",
  "emotion_tone": "热情/专业/亲切/紧迫",
  "scene_count": 5,
  "knowledge_base_match": "true/false",
  "existing_prompts": "如匹配，返回已存在提示词；如不匹配，返回null"
}
```

---

#### 步骤2：提示词生成（智能体1：提示词生成师）
**职责**：按公式输出即梦提示词，严格遵循一致性

**提示词公式**：
```
主体（主体描述）+ 运动 + 场景（场景描述）+（镜头语言 + 光影 + 氛围）
```

**核心要求**：
- 主体一致性：所有分镜沿用核心角色固定描述
- 情绪适配性：光影、氛围匹配对应幕次情绪
- 中英文双版：生成中英文对照版本
- 细节具体：动作连贯，适配5s短视频
- 延伸细节：规避AI独立生成的上下文断层问题

**输出格式**（每幕）：
```json
{
  "scene_number": 1,
  "scene_name": "场景名称",
  "duration": "5s",
  "chinese_prompt": {
    "subject": "主体描述",
    "movement": "运动描述",
    "scene": "场景描述",
    "shot_language": "镜头语言",
    "light": "光影",
    "atmosphere": "氛围",
    "full_prompt": "完整中文提示词"
  },
  "english_prompt": {
    "subject": "Subject description",
    "movement": "Movement description",
    "scene": "Scene description",
    "shot_language": "Shot language",
    "light": "Light",
    "atmosphere": "Atmosphere",
    "full_prompt": "Complete English prompt"
  },
  "emotion_tone": "适配情绪",
  "consistency_check": {
    "character_description": "与核心角色固定描述一致",
    "visual_elements": "视觉元素连贯",
    "emotion_progression": "情绪递进自然"
  }
}
```

---

#### 步骤3：质量核查（智能体2：质量管控师）
**职责**：核查提示词的景别、光影、情绪匹配度

**核查清单**：
- [ ] 主体一致性：同角色外貌描述统一（年龄、发型、服饰、气质）
- [ ] 景别合理性：镜头语言符合场景需求
- [ ] 光影匹配度：光影适配情绪基调
- [ ] 情绪连贯性：从第一幕到第五幕的情绪递进自然
- [ ] 视觉连贯性：视觉线索贯穿五幕（色调、场景元素）
- [ ] AI出图/视频要求：细节具体，动作连贯，适配5s短视频
- [ ] 中英文对应：中英文版本语义一致

**不通过处理**：
- 如发现不一致问题，反馈给提示词生成师调整
- 最多反馈2次，避免过度迭代

**输出格式**：
```json
{
  "quality_check": "pass/fail",
  "check_results": {
    "character_consistency": "pass",
    "shot_language": "pass",
    "light_matching": "pass",
    "emotion_progression": "pass",
    "visual_coherence": "pass",
    "ai_requirement": "pass",
    "translation_quality": "pass"
  },
  "issues": [],
  "adjustment_needed": "false"
}
```

---

#### 步骤4：知识库归档（智能体3：知识库运维师）
**职责**：归档角色固定描述、提示词模板，支持复用

**归档内容**：
- 核心角色固定描述（小省导购员）
- 五幕情绪提示词模板
- 中英文对照版本
- 场景分类索引

**输出格式**：
```json
{
  "archive_id": "唯一标识",
  "scene_type": "产品推荐/价格对比/促销活动",
  "emotion_tone": "情绪基调",
  "character_profile": {
    "gender": "女性",
    "age": "25岁左右",
    "appearance": "外貌描述",
    "outfit": "服饰描述",
    "temperament": "气质描述"
  },
  "prompt_templates": {
    "scene_1": "第一幕模板",
    "scene_2": "第二幕模板",
    "scene_3": "第三幕模板",
    "scene_4": "第四幕模板",
    "scene_5": "第五幕模板"
  },
  "bilingual_version": "中英文对照版本",
  "tags": ["标签1", "标签2"]
}
```

---

#### 步骤5：跨工具适配（智能体4：跨环节适配师）
**职责**：联动Suno音乐生成、AI绘画，确保提示词同源

**Suno音乐提示词**（每幕对应）：
```json
{
  "scene_number": 1,
  "music_style": "音乐风格",
  "music_prompt": "音乐提示词",
  "emotion_match": "情绪匹配",
  "instrumentation": "乐器配置",
  "tempo": "节奏",
  "duration": "时长"
}
```

**AI绘画提示词**（动作前画面）：
```json
{
  "scene_number": 1,
  "painting_prompt": "绘画提示词",
  "pre_action_description": "动作前画面描述",
  "visual_elements": "视觉元素",
  "composition": "构图",
  "color_palette": "色调"
}
```

**输出格式**：
```json
{
  "cross_tool_prompts": {
    "suno_music": {
      "scene_1": {...},
      "scene_2": {...},
      "scene_3": {...},
      "scene_4": {...},
      "scene_5": {...}
    },
    "ai_painting": {
      "scene_1": {...},
      "scene_2": {...},
      "scene_3": {...},
      "scene_4": {...},
      "scene_5": {...}
    }
  }
}
```

---

### 完整输出示例

```json
{
  "metadata": {
    "scene_type": "产品推荐",
    "emotion_tone": "热情专业",
    "total_duration": "25s（5幕×5s）",
    "character": "小省导购员"
  },
  "scenes": [
    {
      "scene_number": 1,
      "scene_name": "开场吸引",
      "duration": "5s",
      "chinese_prompt": {
        "full_prompt": "主体：25岁左右女性数字人，鹅蛋脸、杏眼带笑、浅棕色齐肩卷发，肤色白皙，唇色淡粉，身穿浅灰色修身西装套裙，内搭白色衬衫，脚踩米色细跟鞋，佩戴银色简约项链，气质专业又亲和，手部姿态优雅自然。运动：缓慢抬手指向右侧，姿态挺拔。场景：现代商务场景，背景是产品展示架，前景摆简约文件。镜头语言：中景固定镜头，背景虚化，顺光拍摄。光影：暖调柔光，明亮清晰。氛围：热情专业，吸引注意力。"
      },
      "english_prompt": {
        "full_prompt": "Subject: 25-year-old female digital human, oval face, almond eyes with smile, light brown shoulder-length curly hair, fair skin, light pink lips, wearing light gray tailored suit skirt, white shirt, beige pumps, simple silver necklace, professional and friendly temperament, elegant hand gestures. Movement: Slowly raise hand pointing to the right, upright posture. Scene: Modern business setting, product display shelf in background, simple documents in foreground. Shot: Medium fixed shot, bokeh background, front light. Light: Warm soft light, bright and clear. Atmosphere: Enthusiastic and professional, attention-grabbing."
      },
      "emotion_tone": "热情专业",
      "suno_music_prompt": "欢快现代音乐，轻快节奏，钢琴+电子乐，纯音乐，营造热情专业的氛围",
      "ai_painting_prompt": "中景，顺光拍摄，现代商务场景暖调柔光，背景产品展示架虚化，前景简约文件；25岁女性数字人（鹅蛋脸、杏眼微笑、浅棕齐肩卷发，浅灰西装套裙+白衬衫+米色细跟鞋，银色项链）姿态挺拔，手势准备指向右侧，神情热情专业，整体画面明亮清晰。"
    }
  ]
}
```

---

## 资源索引

### 必要参考文档

**四大智能体角色定义**：见 [references/agent-roles.md](references/agent-roles.md)
- 4个智能体的详细角色定义、能力边界和协作流程
- 何时读取：需要了解智能体职责和协作逻辑时

**提示词公式详解**：见 [references/prompt-formula.md](references/prompt-formula.md)
- 提示词公式的详细说明、拆解步骤、使用示例
- 何时读取：需要生成提示词时

**一致性保障机制**：见 [references/consistency-guide.md](references/consistency-guide.md)
- 人物一致性、视觉连贯性、情绪连贯性的详细保障机制
- 何时读取：需要确保提示词一致性时

**角色固定描述**：见 [references/character-profile.md](references/character-profile.md)
- 小省导购员的核心角色固定描述
- 何时读取：生成提示词主体描述时

**场景模板**：见 [references/scene-templates.md](references/scene-templates.md)
- 货币场景的五幕模板库
- 何时读取：需要快速生成提示词时

**跨工具适配**：见 [references/cross-tool-adaptation.md](references/cross-tool-adaptation.md)
- Suno音乐生成、AI绘画适配指南
- 何时读取：需要联动其他工具时

### 输出资产

**示例提示词**：见 [assets/examples/sample-prompts.md](assets/examples/sample-prompts.md)
- 完整的场景示例（产品推荐、价格对比、促销活动）
- 何时读取：需要参考具体输出格式时

---

## 注意事项

### 提示词生成原则
- **严格遵循公式**：主体+运动+场景+（镜头语言+光影+氛围）
- **中英文对应**：确保语义一致，适配国际AI工具
- **细节具体**：动作连贯，适配5s短视频时长
- **情绪匹配**：光影、氛围严格匹配情绪基调

### 一致性保障
- **人物一致性**：所有分镜使用相同的核心角色描述
- **视觉连贯性**：设定贯穿五幕的视觉线索（色调、场景元素）
- **情绪连贯性**：从第一幕到第五幕的情绪递进自然

### 知识库使用
- **优先复用**：同类需求直接调取知识库素材
- **增量归档**：新需求创作后必须归档至知识库
- **分类索引**：按场景类型、情绪基调建立索引

### 跨工具适配
- **同源设计**：Suno音乐提示词、AI绘画提示词与即梦提示词同源
- **情绪统一**：确保音乐风格、画面质感与即梦提示词情绪一致
- **格式兼容**：生成符合各工具要求的格式

---

## 使用示例

### 示例1：产品推荐视频提示词

**用户需求**：生成一款5幕产品推荐视频的即梦提示词

**执行方式**：
1. 知识库运维师：核查知识库，发现匹配模板
2. 直接调取：返回已存在的产品推荐提示词模板
3. 跨环节适配师：生成Suno音乐和AI绘画提示词

**关键参数**：
- 场景类型：产品推荐
- 情绪基调：热情专业
- 分镜幕次：5幕
- 视频时长：25秒（5幕×5秒）

### 示例2：价格对比视频提示词

**用户需求**：生成一款5幕价格对比视频的即梦提示词

**执行方式**：
1. 知识库运维师：核查知识库，无匹配模板
2. 提示词生成师：按公式生成新提示词
3. 质量管控师：核查提示词质量
4. 知识库运维师：归档至知识库
5. 跨环节适配师：生成Suno音乐和AI绘画提示词

**关键参数**：
- 场景类型：价格对比
- 情绪基调：客观专业
- 分镜幕次：5幕
- 视频时长：25秒（5幕×5秒）

### 示例3：促销活动视频提示词

**用户需求**：生成一款5幕促销活动视频的即梦提示词

**执行方式**：
1. 知识库运维师：核查知识库，发现相似模板
2. 调取相似模板：基于现有模板微调
3. 提示词生成师：生成定制化提示词
4. 质量管控师：核查提示词质量
5. 知识库运维师：归档新版本
6. 跨环节适配师：生成Suno音乐和AI绘画提示词

**关键参数**：
- 场景类型：促销活动
- 情绪基调：紧迫热情
- 分镜幕次：5幕
- 视频时长：25秒（5幕×5秒）
