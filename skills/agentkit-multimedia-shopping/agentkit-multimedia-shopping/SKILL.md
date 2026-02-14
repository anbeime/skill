---
name: agentkit-multimedia-shopping
description: 基于ByteDance agentkit-samples多媒体用例的小省导购员数字人带货视频生成技能，整合多模态内容生成能力（图像、视频、音频），支持AI绘画、语音合成、视频生成，与小省导购员人设融合，9:16竖屏适配，直接对接带货视频生成流程
dependency:
  python:
    - Pillow>=10.0.0
    - requests>=2.28.0
    - numpy>=1.24.0
  system:
    - echo "Skill已加载"
---

# AgentKit多媒体小省导购员数字人带货

## 任务目标
- 本技能用于：基于ByteDance agentkit-samples多媒体用例，生成小省导购员数字人带货视频的多模态内容
- 能力包含：
  - AI绘画生成（小省导购员角色形象、场景背景）
  - 语音合成（导购员语音、背景音乐）
  - 视频生成（多模态组合）
  - 工作流编排（图像→音频→视频→成片）
- 触发条件：用户需要生成小省导购员数字人带货视频，使用agentkit-samples的多媒体能力

## 前置准备

### 依赖说明
本技能依赖以下Python包：
```
Pillow>=10.0.0
requests>=2.28.0
numpy>=1.24.0
```

### 环境准备
1. 安装agentkit-samples（如需要）
2. 准备API凭证（如涉及第三方服务调用）
3. 准备小省导购员角色固定特征描述

### 前置知识
- 了解ByteDance agentkit-samples多媒体用例的基本功能
- 了解AI绘画、语音合成、视频生成的基本原理
- 了解9:16竖屏视频规格

## 操作步骤

### 标准流程

#### 1. 角色形象生成
使用AI绘画生成小省导购员角色形象：

**输入信息**：
- 角色固定特征（脸型、发型、服饰、气质）
- 场景类型（商务场景）
- 情绪基调（热情、专业、亲切）

**生成流程**：
1. 读取 [references/character-profile.md](references/character-profile.md)，获取小省导购员角色固定特征
2. 调用 [scripts/generate_character.py](scripts/generate_character.py) 生成角色形象
3. 裁剪为9:16比例，分辨率≥1080×1920
4. 保存参考图（供InfiniteTalk使用）

**输出**：角色参考图（9:16竖屏）

#### 2. 场景背景生成
使用AI绘画生成场景背景：

**输入信息**：
- 场景类型（商务会议室、书房、洽谈室、大厅、办公室）
- 情绪基调（冷调、暖调、中性）
- 光影描述（侧光、顺光、顶光、逆光）

**生成流程**：
1. 读取场景模板，选择对应场景类型
2. 调用 [scripts/generate_scene.py](scripts/generate_scene.py) 生成场景背景
3. 裁剪为9:16比例，分辨率≥1080×1920
4. 保存场景参考图

**输出**：场景参考图（9:16竖屏）

#### 3. 语音合成
使用TTS生成导购员语音：

**输入信息**：
- 话术内容（带货文案）
- 语音类型（语速、语气）
- 情绪基调（热情、专业、亲切）

**生成流程**：
1. 准备话术内容（符合小省导购员人设）
2. 调用 [scripts/generate_voice.py](scripts/generate_voice.py) 合成语音
3. 导出为16kHz单声道wav格式
4. 保存语音文件（供InfiniteTalk使用）

**输出**：语音文件（16kHz单声道wav）

#### 4. 背景音乐生成
使用音乐生成工具生成背景音乐：

**输入信息**：
- 情绪基调（热情、专业、紧迫、亲切）
- 音乐风格（管弦乐、钢琴、弦乐）
- 时长（5秒/幕）

**生成流程**：
1. 根据情绪基调选择音乐风格
2. 调用 [scripts/generate_music.py](scripts/generate_music.py) 生成音乐
3. 导出为16kHz单声道wav格式
4. 保存音乐文件（供InfiniteTalk使用）

**输出**：音乐文件（16kHz单声道wav）

#### 5. 视频生成
使用多模态组合生成视频：

**输入信息**：
- 角色参考图（9:16竖屏）
- 场景参考图（9:16竖屏）
- 语音文件（16kHz单声道wav）
- 音乐文件（16kHz单声道wav）
- 提示词（InfiniteTalk专用）

**生成流程**：
1. 读取InfiniteTalk专用提示词（使用infinitetalk-shopping-avatar Skill生成）
2. 调用 [scripts/generate_video.py](scripts/generate_video.py) 生成视频
3. 生成5幕视频（每幕5秒）
4. 拼接完整视频（总时长25秒）

**输出**：完整视频（25秒，9:16竖屏）

### 可选分支

- 当仅需生成角色形象：执行步骤1
- 当仅需生成场景背景：执行步骤2
- 当仅需生成语音：执行步骤3
- 当仅需生成背景音乐：执行步骤4
- 当仅需生成视频：执行步骤1-5

## 资源索引

- 角色固定特征：见 [references/character-profile.md](references/character-profile.md)（何时读取：生成角色形象时）
- 场景模板：见 [references/scene-templates.md](references/scene-templates.md)（何时读取：生成场景背景时）
- 工具使用说明：见 [references/tool-usage-guide.md](references/tool-usage-guide.md)（何时读取：使用工具时）
- 示例输出：见 [assets/examples/sample-output.md](assets/examples/sample-output.md)（何时读取：参考示例输出）

## 注意事项

- **角色一致性**：所有生成的角色形象必须严格遵循角色固定特征
- **分辨率匹配**：所有图像必须为9:16竖屏，分辨率≥1080×1920
- **音频格式**：所有音频必须为16kHz单声道wav格式
- **情绪适配**：语音和音乐必须与场景情绪匹配
- **工作流顺序**：严格按照图像→音频→视频的顺序生成
- **与InfiniteTalk协同**：使用infinitetalk-shopping-avatar Skill生成提示词

## 使用示例

### 示例1：生成完整带货视频

**功能说明**：生成小省导购员数字人带货视频的完整流程

**执行方式**：
1. 生成角色形象（调用generate_character.py）
2. 生成场景背景（调用generate_scene.py）
3. 合成导购员语音（调用generate_voice.py）
4. 生成背景音乐（调用generate_music.py）
5. 生成视频（调用generate_video.py，结合InfiniteTalk提示词）

**关键参数**：
- 角色固定特征：严格遵循character-profile.md
- 场景类型：商务场景
- 情绪基调：热情专业
- 分辨率：1080×1920（9:16竖屏）
- 音频格式：16kHz单声道wav

**输出**：完整带货视频（25秒，9:16竖屏）

### 示例2：仅生成角色参考图

**功能说明**：仅生成小省导购员角色参考图

**执行方式**：调用generate_character.py

**关键参数**：
- 角色固定特征：严格遵循character-profile.md
- 情绪基调：热情专业
- 分辨率：1080×1920（9:16竖屏）

**输出**：角色参考图（9:16竖屏）

## 工作流总结

```
角色固定特征描述
    ↓
AI绘画生成（角色形象+场景背景）
    ↓
语音合成（导购员语音+背景音乐）
    ↓
InfiniteTalk提示词生成（使用infinitetalk-shopping-avatar Skill）
    ↓
多模态视频生成（图像+音频+提示词）
    ↓
完整带货视频（25秒，9:16竖屏）
```

## 与InfiniteTalk的协同

本技能与`infinitetalk-shopping-avatar` Skill协同工作：

1. **本技能**：生成多模态内容（图像、音频）
2. **infinitetalk-shopping-avatar Skill**：生成InfiniteTalk专用提示词
3. **InfiniteTalk**：使用多模态内容和提示词生成视频

协同流程：
```
本技能生成角色参考图 → infinitetalk-shopping-avatar生成提示词 → InfiniteTalk生成视频
本技能生成语音文件 → chinese-wav2vec2-base编码 → InfiniteTalk使用
本技能生成音乐文件 → chinese-wav2vec2-base编码 → InfiniteTalk使用
```
