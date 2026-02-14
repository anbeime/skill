---
name: video-frame-extractor
description: 视频反推工具,支持视频抽帧、视觉模型分析、提示词生成,适用于视频创作参考、内容提取、场景分析
dependency:
  python:
    - opencv-python>=4.8.0
    - pillow>=10.0.0
    - requests>=2.28.0
---

# 视频反推工具 - 抽帧与视觉分析

## 任务目标
- 本Skill用于: 从视频中提取关键帧,使用视觉模型分析每帧内容,生成结构化描述和提示词
- 能力包含:
  - 视频抽帧(支持间隔抽帧、均匀采样)
  - 视觉模型API调用(支持GPT-4V/Claude-3.5-Sonnet等)
  - 批量图片分析
  - 结构化结果输出(JSON格式)
- 触发条件: 用户需要分析视频内容、提取分镜参考、生成创作提示词

## 前置准备
- 依赖说明:
  ```
  opencv-python>=4.8.0
  pillow>=10.0.0
  requests>=2.28.0
  ```

- 视觉模型配置:
  需要配置视觉模型API密钥(如GPT-4V、Claude-3.5-Sonnet),环境变量格式:
  ```bash
  export VISION_API_KEY="your_api_key"
  export VISION_API_BASE="https://api.openai.com/v1"  # 或其他API地址
  export VISION_MODEL="gpt-4-vision-preview"  # 模型名称
  ```

- Coze Bot配置(推荐):
  使用您发布的Coze Bot API进行视觉分析,环境变量格式:
  ```bash
  export COZE_BOT_ID="7572557757883383858"  # 您的Bot ID
  export COZE_API_KEY="cztei_qHZQ0A5OSJjsmfZWmVb8bqu2BTbtB240YGbDYLhZpsIr8jER4aL4Aevyii8rnKfNs"  # 您的API Key
  ```

  Coze Bot的优势: 集成了官方抽帧插件和视觉模型,无需额外配置

## 操作步骤

### 标准流程

**步骤1: 视频抽帧**
- 输入: 视频文件路径或URL
- 调用脚本: `scripts/video_frame_extractor.py`
- 参数:
  - `--input`: 视频文件路径或URL
  - `--output`: 输出图片目录
  - `--interval`: 抽帧间隔(秒),默认1秒抽1帧
  - `--max_frames`: 最大抽帧数,默认10帧
- 输出: 抽取的图片序列

```bash
# 示例: 抽取视频关键帧
python scripts/video_frame_extractor.py \
  --input ./input/video.mp4 \
  --output ./output/frames \
  --interval 3 \
  --max_frames 10
```

**步骤2: 视觉分析**

**方案A: 使用Coze Bot API(推荐)**
- 输入: 抽帧图片目录
- 调用脚本: `scripts/coze_bot_client.py`
- 参数:
  - `--image_dir`: 图片目录
  - `--prompt`: 分析提示词(可选)
  - `--output`: 输出JSON文件路径
- 输出: 每张图片的描述和分析结果

```bash
# 示例: 使用Coze Bot分析抽帧图片
python scripts/coze_bot_client.py \
  --image_dir ./output/frames \
  --prompt "分析场景内容、人物状态、构图特点,适合AI视频创作" \
  --output ./output/analysis.json
```

**方案B: 使用其他视觉模型API**
- 输入: 抽帧图片目录
- 调用脚本: `scripts/visual_analyzer.py`
- 参数:
  - `--input`: 图片目录或单张图片路径
  - `--output`: 分析结果JSON文件路径
  - `--prompt`: 分析提示词(可选,默认分析场景/人物/构图)
- 输出: 每张图片的描述和分析结果

```bash
# 示例: 使用GPT-4V分析抽帧图片
python scripts/visual_analyzer.py \
  --input ./output/frames \
  --output ./output/analysis.json \
  --prompt "分析场景内容、人物状态、构图特点,适合AI视频创作"
```

**步骤3: 结果整合**
- 智能体读取分析结果JSON
- 根据分析结果生成提示词
- 可用于视频创作参考或分镜设计

### 可选参数

**抽帧参数:**
- `--interval`: 抽帧间隔(秒),越小抽帧越密集
- `--max_frames`: 最大抽帧数,控制输出数量
- `--start_time`: 开始时间(秒)
- `--end_time`: 结束时间(秒)
- `--resolution`: 输出图片分辨率,默认1080P

**分析参数:**
- `--prompt`: 自定义分析提示词
- `--detail`: 分析详细程度(brief/standard/detailed)
- `--batch_size`: 批量分析大小,默认5张

## 资源索引
- 必要脚本:
  - [scripts/video_frame_extractor.py](scripts/video_frame_extractor.py) - 视频抽帧工具
  - [scripts/coze_bot_client.py](scripts/coze_bot_client.py) - Coze Bot API调用工具(推荐)
  - [scripts/visual_analyzer.py](scripts/visual_analyzer.py) - 其他视觉模型API调用工具
- 领域参考:
  - [references/analysis-guide.md](references/analysis-guide.md) - 视觉分析指导与提示词模板

## 注意事项
- 视觉模型API密钥需提前配置,否则无法调用分析功能
- 抽帧间隔和最大帧数需根据视频时长合理设置
- 视觉分析结果依赖模型能力,不同模型输出格式可能不同
- 建议先用小规模抽帧测试,确认效果后再大规模处理

## 使用示例

### 示例1: 完整反推流程(使用Coze Bot)
```bash
# 1. 抽取视频关键帧
python scripts/video_frame_extractor.py \
  --input ./input/source_video.mp4 \
  --output ./output/frames \
  --interval 2 \
  --max_frames 8

# 2. 使用Coze Bot分析抽帧内容
python scripts/coze_bot_client.py \
  --image_dir ./output/frames \
  --prompt "详细描述场景、人物、构图,适合AI视频创作参考" \
  --output ./output/analysis.json

# 3. 智能体读取analysis.json,生成创作提示词
# 智能体将根据分析结果组织内容,生成可用于AI创作的提示词
```

### 示例2: 仅抽帧(不分析)
```bash
python scripts/video_frame_extractor.py \
  --input ./input/video.mp4 \
  --output ./output/frames \
  --interval 5 \
  --max_frames 5
```

### 示例3: 单张图片分析
```bash
# 使用Coze Bot
python scripts/coze_bot_client.py \
  --image ./output/frames/frame_00001.jpg \
  --prompt "分析这张图片的场景风格和构图"

# 或使用其他视觉模型
python scripts/visual_analyzer.py \
  --input ./output/frames/ \
  --output ./analysis.json \
  --prompt "分析场景风格和构图"
```

## 输出格式

**抽帧输出:**
```
./output/frames/
├── frame_00001.jpg
├── frame_00002.jpg
├── frame_00003.jpg
└── ...
```

**分析输出(JSON):**
```json
{
  "total_frames": 10,
  "analysis": [
    {
      "frame_file": "frame_00001.jpg",
      "timestamp": "00:00:00",
      "description": "场景描述内容...",
      "elements": ["人物", "背景", "道具"],
      "style": "风格描述..."
    },
    {
      "frame_file": "frame_00002.jpg",
      "timestamp": "00:00:03",
      "description": "场景描述内容...",
      "elements": ["人物", "背景", "道具"],
      "style": "风格描述..."
    }
  ]
}
```

## 技术说明

**抽帧技术:**
- 使用OpenCV的VideoCapture读取视频
- 按时间间隔均匀采样关键帧
- 支持多种视频格式(MP4/MOV/AVI等)

**视觉分析:**
- 支持Coze Bot API(推荐,已集成抽帧和视觉模型)
- 支持主流视觉模型API(GPT-4V/Claude-3.5-Sonnet等)
- 批量处理,提升效率
- 结构化输出,便于后续处理

**Coze Bot优势:**
- 集成官方抽帧插件,抽帧质量高
- 内置视觉模型,无需额外配置
- 一站式服务,抽帧+分析一体化
- 支持流式响应,实时获取结果

**性能优化:**
- 可配置抽帧间隔,减少冗余帧
- 批量API调用,减少请求次数
- 结果缓存,避免重复分析
