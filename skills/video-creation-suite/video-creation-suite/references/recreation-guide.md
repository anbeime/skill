# 视频二创流程详细指导

## 目录
- [二创核心原则](#二创核心原则)
- [完整工作流](#完整工作流)
- [智能体工作指南](#智能体工作指南)
- [常见问题](#常见问题)

---

## 二创核心原则

### 什么是视频二创?

视频二创是指基于原视频的风格、结构、节奏,创作出内容不同但风格相似的新视频。

**核心特点:**
- ✅ 保持原视频的视觉风格(色调、构图、光影)
- ✅ 保持原视频的节奏和结构
- ✅ 改变具体的场景、人物、细节
- ✅ 生成全新的旁白、音效、字幕

**不是:**
- ❌ 简单的滤镜叠加
- ❌ 原视频的拼接或剪辑
- ❌ 风格完全不同的重新创作

### 二创流程图

```
原视频
  ↓
[阶段1: 反推分析]
  ├─ 抽帧 (关键帧提取)
  ├─ 视觉分析 (场景/人物/构图/光影/色调)
  └─ 风格提取 (视觉特征总结)
  ↓
[阶段2: 素材生成]
  ├─ 新图片 (保持风格,改变内容)
  ├─ 旁白 (根据新场景生成)
  ├─ 音效 (适配新场景)
  ├─ 音乐 (保持风格,可调整)
  └─ 字幕 (匹配旁白)
  ↓
[阶段3: 视频合成]
  ├─ 整合素材
  ├─ 添加转场
  └─ 输出新视频
  ↓
二创视频
```

---

## 完整工作流

### 阶段1: 反推分析

#### 步骤1.1: 视频抽帧

**目标**: 提取原视频的关键帧,作为分析样本

**操作**:
```bash
python scripts/video_frame_extractor.py \
  --input ./input/original_video.mp4 \
  --output ./output/stage1_frames \
  --interval 3 \
  --max_frames 10
```

**参数说明**:
- `--interval`: 抽帧间隔,建议2-5秒
- `--max_frames`: 最大抽帧数,建议8-15帧

**输出**: `./output/stage1_frames/` - 关键帧图片序列

---

#### 步骤1.2: Coze Bot视觉分析

**目标**: 分析每帧的视觉特征,提取风格要素

**操作**:
```bash
python scripts/coze_bot_client.py \
  --image_dir ./output/stage1_frames \
  --prompt "详细分析每帧的:1.场景类型 2.人物特征 3.构图方式 4.光源方向 5.主色调 6.光影效果 7.整体风格(写实/抽象/科技/复古等),输出JSON格式" \
  --output ./output/stage1_analysis.json
```

**输出**: `stage1_analysis.json` - 包含每帧的详细分析

**输出格式**:
```json
{
  "total_images": 10,
  "analyzed_count": 10,
  "analysis": [
    {
      "frame_file": "frame_00001.jpg",
      "description": "场景描述...",
      "scene_type": "室内/室外",
      "person": "人物特征...",
      "composition": "构图方式...",
      "lighting": "光源方向...",
      "color_tone": "主色调...",
      "style": "风格..."
    }
  ]
}
```

---

### 阶段2: 素材生成

#### 步骤2.1: 智能体生成新图片提示词

**智能体: 视觉分析师**

**输入**: `stage1_analysis.json`

**任务**:
1. 提取风格特征(色调、构图、光影)
2. 设计新场景内容(改变但保持风格)
3. 生成图片生成提示词

**输出**: `stage2_prompts/image_prompts.json`

**提示词示例**:
```json
{
  "total_frames": 10,
  "prompts": [
    {
      "frame_id": 1,
      "original_style": "冷灰色调,低角度拍摄,硬质光",
      "new_scene": "类似场景但不同布局",
      "prompt": "生成一个[场景描述]图片,保持[风格特征],要求[具体细节]"
    }
  ]
}
```

---

#### 步骤2.2: 生成新图片

**脚本调用**: `image_generator.py`

**操作**:
```bash
python scripts/image_generator.py \
  --config ./output/stage2_prompts/image_prompts.json \
  --output ./output/stage2_images/
```

**输出**: `./output/stage2_images/` - 新生成的图片序列

**质量要求**:
- 分辨率: 1080P
- 风格一致性: 与原视频风格相似
- 内容差异: 场景细节与原视频不同

---

#### 步骤2.3: 智能体生成旁白

**智能体: 剧本创作师**

**输入**:
- `stage1_analysis.json` (原视频场景)
- `stage2_prompts/image_prompts.json` (新场景设计)

**任务**:
1. 根据新场景编写旁白文本
2. 确保旁白与新图片内容匹配
3. 保持旁白风格与原视频一致

**输出**: `stage2_scripts/narration.txt`

**旁白示例**:
```
[场景1] 在这寂静的夜晚,科技的力量正在悄然改变一切...
[场景2] 光影交错间,我们看到了未来的轮廓...
```

---

#### 步骤2.4: 生成配音

**脚本调用**: `voice_generator.py`

**操作**:
```bash
python scripts/voice_generator.py \
  --script ./output/stage2_scripts/narration.txt \
  --output ./output/stage2_audio/narration.wav
```

**参数可选**:
- `--voice`: 选择音色
- `--api_key`: TTS API密钥

**输出**: `./output/stage2_audio/narration.wav`

---

#### 步骤2.5: 生成音效

**脚本调用**: `audio_generator.py`

**操作**:
```bash
# 生成场景音效
python scripts/audio_generator.py \
  --mode sound_effects \
  --analysis ./output/stage1_analysis.json \
  --output ./output/stage2_audio/sound_effects/

# 生成背景音乐
python scripts/audio_generator.py \
  --mode music \
  --analysis ./output/stage1_analysis.json \
  --output ./output/stage2_audio/background_music.wav
```

**输出**:
- `./output/stage2_audio/sound_effects/` - 场景音效
- `./output/stage2_audio/background_music.wav` - 背景音乐

---

#### 步骤2.6: 生成字幕

**脚本调用**: `subtitle_generator.py`

**操作**:
```bash
python scripts/subtitle_generator.py \
  --script ./output/stage2_scripts/narration.txt \
  --analysis ./output/stage1_analysis.json \
  --output ./output/stage2_subtitles/subtitle.srt
```

**输出**: `./output/stage2_subtitles/subtitle.srt`

---

### 阶段3: 视频合成

#### 步骤3.1: 生成合成配置

**智能体: 视频导演**

**输入**:
- `stage2_images/` - 新图片
- `stage2_analysis.json` - 时间信息
- `stage2_audio/` - 音频素材
- `stage2_subtitles/` - 字幕文件

**任务**:
1. 设计转场效果(淡入淡出/切镜)
2. 匹配音频与视频时长
3. 配置合成参数

**输出**: `stage2_config.json`

**配置示例**:
```json
{
  "images_dir": "./output/stage2_images/",
  "audio_file": "./output/stage2_audio/narration.wav",
  "subtitle_file": "./output/stage2_subtitles/subtitle.srt",
  "background_music": "./output/stage2_audio/background_music.wav",
  "shots": [
    {
      "shot_id": "001",
      "duration": 3.0,
      "transition": "fade"
    }
  ],
  "width": 1920,
  "height": 1080,
  "fps": 25
}
```

---

#### 步骤3.2: 合成视频

**脚本调用**: `video_compositor.py`

**操作**:
```bash
python scripts/video_compositor.py \
  --config ./output/stage2_config.json \
  --output ./output/final/recreated_video.mp4
```

**输出**: `./output/final/recreated_video.mp4` - 完整的二创视频

---

## 智能体工作指南

### 智能体1: 视觉分析师

**职责**:
1. 分析原视频的视觉风格
2. 提取风格特征(色调、构图、光影)
3. 生成新图片提示词

**输入**:
- `stage1_analysis.json` - Coze Bot分析结果

**输出**:
- `stage2_prompts/image_prompts.json` - 图片生成提示词

**核心能力**:
- 理解视觉风格特征
- 保持风格一致性
- 创造新场景内容

---

### 智能体2: 剧本创作师

**职责**:
1. 根据新场景编写旁白
2. 生成字幕文本
3. 确保文案与画面匹配

**输入**:
- `stage2_prompts/image_prompts.json` - 新场景设计
- `stage1_analysis.json` - 原视频风格

**输出**:
- `stage2_scripts/narration.txt` - 旁白文本
- `stage2_scripts/subtitle_text.txt` - 字幕文本

**核心能力**:
- 文案创作
- 场景理解
- 风格匹配

---

### 智能体3: 音效设计师

**职责**:
1. 设计音效方案
2. 选择背景音乐风格
3. 确保音效与场景匹配

**输入**:
- `stage1_analysis.json` - 场景分析
- `stage2_scripts/narration.txt` - 旁白文本

**输出**:
- 音效设计说明
- 背景音乐风格建议

**核心能力**:
- 音效设计
- 风格匹配
- 情绪表达

---

### 智能体4: 视频导演

**职责**:
1. 整合所有素材
2. 设计转场效果
3. 确保整体风格统一

**输入**:
- 所有素材文件
- `stage1_analysis.json` - 原视频风格

**输出**:
- `stage2_config.json` - 合成配置

**核心能力**:
- 整体把控
- 转场设计
- 风格统一

---

## 常见问题

### Q1: 如何确保风格一致性?

**A:** 
1. 在视觉分析阶段,详细提取风格特征
2. 在图片生成时,明确要求保持这些特征
3. 在视频导演阶段,整体把控风格统一

### Q2: 新图片生成质量不理想?

**A:**
1. 优化图片生成提示词,加入更多风格约束
2. 调整生图API参数
3. 尝试不同的生图模型

### Q3: 旁白与画面不匹配?

**A:**
1. 剧本创作师需要参考新场景设计
2. 生成旁白前,先查看新生成的图片
3. 根据图片内容调整旁白文本

### Q4: 音频与视频时长不匹配?

**A:**
1. 视频导演在生成配置时,调整音频时长
2. 或剪辑音频以匹配视频时长
3. 或调整视频时长以匹配音频

### Q5: 转场效果不自然?

**A:**
1. 视频导演设计转场时,考虑场景关系
2. 尝试不同的转场类型
3. 调整转场时长(0.3-0.5秒)
