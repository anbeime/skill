# 与其他 Skill 协同指南

本文档详细说明 `remotion-video-enhancer` Skill 如何与其他 PPT 相关 Skill 协同工作。

## 目录
1. [协同模式概述](#协同模式概述)
2. [与 ppt-generator 协同](#与-ppt-generator-协同)
3. [与 nanobanana-ppt-visualizer 协同](#与-nanobanana-ppt-visualizer-协同)
4. [与 ppt-roadshow-generator 协同](#与-ppt-roadshow-generator-协同)
5. [完整工作流程](#完整工作流程)
6. [数据格式规范](#数据格式规范)

---

## 协同模式概述

`remotion-video-enhancer` Skill 设计为可以与以下 Skill 无缝协同：

| Skill | 输出格式 | 接收方式 | 增强效果 |
|-------|---------|---------|---------|
| ppt-generator | JSON 数据 | 读取 JSON 文件 | Framer Motion 动画 |
| nanobanana-ppt-visualizer | HTML + 图片 | 读取 HTML 或图片 | 增强 HTML 动画或视频转场 |
| ppt-roadshow-generator | 视频文件 | 读取视频 | FFmpeg 视频转场 |

---

## 与 ppt-generator 协同

### 协同流程

```
用户请求："生成一个带高级动画的产品介绍 PPT"

┌─────────────────────────────────────────────────────────┐
│  ppt-generator Skill                                    │
├─────────────────────────────────────────────────────────┤
│  1. 主题分析师：分析主题                                │
│  2. 模板设计师：推荐布局                                │
│  3. 内容策划师：规划内容结构                            │
│  4. 文本创作者：撰写内容                                │
│  5. 视觉设计师：提供配图建议                            │
│  6. 优化编辑师：优化文本                                │
│  7. PPT 构建师：生成 JSON 数据                          │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼ ppt_data.json
┌─────────────────────────────────────────────────────────┐
│  remotion-video-enhancer Skill                         │
├─────────────────────────────────────────────────────────┤
│  1. 动画规划（animation_planner.py）                     │
│     - 生成 animation_plan.json                           │
│  2. HTML 动画生成（html_animations.py）                 │
│     - 应用 Framer Motion 动画                           │
│     - 生成 animated_viewer.html                         │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
                  animated_viewer.html
```

### 数据格式

**ppt-generator 输出（ppt_data.json）**：
```json
{
  "metadata": {
    "title": "产品介绍演示",
    "author": "用户姓名",
    "theme": "科技感"
  },
  "slides": [
    {
      "layout": "TitleSlide",
      "title": "产品名称",
      "content": ["副标题", "产品亮点"],
      "notes": "备注内容"
    },
    {
      "layout": "ContentSlide",
      "title": "核心功能",
      "content": ["功能一", "功能二", "功能三"],
      "notes": "备注内容"
    }
  ]
}
```

**remotion-video-enhancer 接收**：
- 输入：`ppt_data.json`
- 处理：生成动画配置，应用 Framer Motion 动画
- 输出：`animated_viewer.html`

### 使用示例

**步骤 1：ppt-generator 生成内容**
```bash
# ppt-generator 处理后输出
ppt_data.json
```

**步骤 2：remotion-video-enhancer 增强动画**
```bash
# 生成动画配置
python scripts/animation_planner.py \
  --input ./ppt_data.json \
  --style dynamic \
  --output ./animation_plan.json

# 生成带动画的 HTML 播放器
python scripts/html_animations.py \
  --input ./ppt_data.json \
  --animation-plan ./animation_plan.json \
  --template assets/templates/enhanced_viewer.html \
  --output ./animated_viewer.html
```

**步骤 3：在浏览器中打开**
```bash
open animated_viewer.html
# 或直接用浏览器打开文件
```

---

## 与 nanobanana-ppt-visualizer 协同

### 协同流程

```
用户请求："为生成的播放器添加 Framer Motion 动画"

┌─────────────────────────────────────────────────────────┐
│  nanobanana-ppt-visualizer Skill                        │
├─────────────────────────────────────────────────────────┤
│  1. 接收 JSON 数据（来自 ppt-generator）                │
│  2. 选择视觉风格                                        │
│  3. 生成图片（slide-01.png, slide-02.png, ...）         │
│  4. 生成基础 HTML 播放器（viewer.html）                 │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼ viewer.html + slide-*.png
┌─────────────────────────────────────────────────────────┐
│  remotion-video-enhancer Skill                         │
├─────────────────────────────────────────────────────────┤
│  1. 接收 viewer.html                                    │
│  2. 增强 HTML，添加 Framer Motion 动画                 │
│  3. 生成 animated_viewer.html                           │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
                  animated_viewer.html
```

### 两种增强模式

**模式 A：增强现有 HTML 播放器**
- 接收 `viewer.html`
- 添加 Framer Motion 库和动画代码
- 输出 `animated_viewer.html`

**模式 B：从 JSON 重新生成带动画的播放器**
- 接收原始 `ppt_data.json`
- 直接生成带 Framer Motion 动画的播放器
- 输出 `animated_viewer.html`

### 使用示例

**模式 A：增强现有 HTML**
```bash
# 假设已有 viewer.html
python scripts/html_animations.py \
  --input ./ppt_data.json \
  --animation-plan ./animation_plan.json \
  --template assets/templates/enhanced_viewer.html \
  --output-dir ./enhanced_output
```

**模式 B：从 JSON 生成**
```bash
# 使用原始 JSON 数据
python scripts/html_animations.py \
  --input ./ppt_data.json \
  --style dynamic \
  --output ./animated_viewer.html
```

---

## 与 ppt-roadshow-generator 协同

### 协同流程

```
用户请求："为路演视频添加 Remotion 风格转场"

┌─────────────────────────────────────────────────────────┐
│  ppt-roadshow-generator Skill                           │
├─────────────────────────────────────────────────────────┤
│  1-6. 前 6 个角色：分析、规划、内容生成                  │
│  7. 转场设计师：设计页面过渡动画                        │
│  8. 音频设计师：配音、音效、音乐                        │
│  9. 字幕设计师：生成字幕                                │
│  10. 视频合成师：合成基础视频                           │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼ roadshow_video.mp4
┌─────────────────────────────────────────────────────────┐
│  remotion-video-enhancer Skill                         │
├─────────────────────────────────────────────────────────┤
│  1. 动画规划（animation_planner.py）                     │
│     - 分析视频时长                                      │
│     - 生成转场配置                                      │
│  2. 视频转场（video_transitions.py）                     │
│     - 应用 FFmpeg 转场效果                             │
│     - 输出增强视频                                      │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
          enhanced_roadshow_video.mp4
```

### 数据格式

**ppt-roadshow-generator 输出**：
- 视频文件：`roadshow_video.mp4`
- 可选：转场配置（`transitions.json`）

**remotion-video-enhancer 接收**：
- 输入：`roadshow_video.mp4` 或图片目录
- 处理：生成转场配置，应用 FFmpeg 转场
- 输出：`enhanced_roadshow_video.mp4`

### 使用示例

**步骤 1：ppt-roadshow-generator 生成基础视频**
```bash
# ppt-roadshow-generator 处理后输出
roadshow_video.mp4
```

**步骤 2：remotion-video-enhancer 增强转场**
```bash
# 生成动画配置
python scripts/animation_planner.py \
  --input ./images/ \
  --style cinematic \
  --output ./animation_plan.json

# 应用转场效果
python scripts/video_transitions.py \
  --input ./roadshow_video.mp4 \
  --transitions ./animation_plan.json \
  --output ./enhanced_roadshow_video.mp4 \
  --resolution 1920x1080 \
  --fps 30
```

**步骤 3：预览增强视频**
```bash
open enhanced_roadshow_video.mp4
# 或使用视频播放器播放
```

---

## 完整工作流程

### 场景 1：从零开始生成带动画的 PPT

```
1. ppt-generator
   ↓
   ppt_data.json

2. remotion-video-enhancer
   ↓
   animated_viewer.html
```

**执行命令**：
```bash
# 步骤 1：生成 PPT 内容
# ppt-generator 执行...

# 步骤 2：增强动画
python scripts/animation_planner.py \
  --input ./ppt_data.json \
  --style dynamic \
  --output ./animation_plan.json

python scripts/html_animations.py \
  --input ./ppt_data.json \
  --animation-plan ./animation_plan.json \
  --output ./animated_viewer.html
```

---

### 场景 2：生成完整路演视频（含高级转场）

```
1. ppt-generator
   ↓
   ppt_data.json

2. nanobanana-ppt-visualizer
   ↓
   images/ (slide-01.png, ...)

3. ppt-roadshow-generator
   ↓
   roadshow_video.mp4

4. remotion-video-enhancer
   ↓
   enhanced_roadshow_video.mp4
```

**执行命令**：
```bash
# 步骤 1-3：其他 Skill 执行...

# 步骤 4：增强转场
python scripts/video_transitions.py \
  --input ./roadshow_video.mp4 \
  --transitions ./animation_plan.json \
  --output ./enhanced_roadshow_video.mp4 \
  --style cinematic
```

---

### 场景 3：仅增强动画（不重新生成内容）

```
1. 用户已有 animated_viewer.html
   ↓
2. remotion-video-enhancer
   ↓
   增强的 animated_viewer.html
```

**执行命令**：
```bash
# 直接增强现有 HTML
python scripts/html_animations.py \
  --input ./ppt_data.json \
  --animation-plan ./custom_animation.json \
  --output ./enhanced_viewer.html
```

---

## 数据格式规范

### JSON 数据格式（ppt_data.json）

**必需字段**：
- `metadata`：元数据
  - `title`：标题（必需）
  - `author`：作者（可选）
  - `theme`：主题（可选）
- `slides`：幻灯片数组（必需）
  - 每个幻灯片包含：
    - `title`：标题（必需）
    - `content`：内容数组（必需）
    - `notes`：备注（可选）

**示例**：
```json
{
  "metadata": {
    "title": "产品介绍",
    "author": "张三",
    "theme": "科技感"
  },
  "slides": [
    {
      "title": "产品概述",
      "content": ["核心功能", "技术优势", "应用场景"],
      "notes": "开场白"
    },
    {
      "title": "核心功能",
      "content": ["功能一", "功能二", "功能三"],
      "notes": "详细说明"
    }
  ]
}
```

---

### 动画配置格式（animation_plan.json）

**必需字段**：
- `metadata`：元数据
  - `style`：动画风格（必需）
  - `page_count`：页面数量（必需）
- `transitions`：转场配置数组（可选）
- `element_animations`：元素动画配置数组（可选）

**示例**：
```json
{
  "metadata": {
    "style": "dynamic",
    "page_count": 2,
    "transition_count": 2,
    "element_animation_count": 6
  },
  "transitions": [
    {
      "page_index": 1,
      "type": "zoom",
      "duration": 1.5,
      "easing": "ease-out",
      "params": {
        "scale": 1.2,
        "direction": "in"
      }
    },
    {
      "page_index": 2,
      "type": "slide",
      "duration": 1.2,
      "easing": "ease-in-out",
      "params": {
        "direction": "right"
      }
    }
  ],
  "element_animations": [
    {
      "page_index": 1,
      "element": "title",
      "type": "fadeInUp",
      "delay": 0.1,
      "duration": 0.6
    }
  ]
}
```

---

## 注意事项

### 1. 输入文件检查

在使用 `remotion-video-enhancer` 之前，确保：
- JSON 文件格式正确
- 视频文件存在且可读
- 图片文件完整

### 2. 动画风格选择

根据内容类型选择合适的动画风格：
- 商务演示：minimal 或 dynamic
- 产品介绍：dynamic 或 cinematic
- 教育内容：playful
- 艺术展示：cinematic

### 3. 转场时长控制

- 短转场（0.5-1.0 秒）：快节奏内容
- 中等转场（1.0-1.5 秒）：标准内容
- 长转场（1.5-2.0 秒）：电影感内容

### 4. 输出文件管理

- 使用有意义的文件名
- 区分不同版本的输出
- 定期清理临时文件

### 5. 测试和调整

- 生成后预览效果
- 根据反馈调整参数
- 多次测试不同配置

---

## 常见问题

### Q1：如何自定义动画配置？

A：手动编辑 `animation_plan.json`，调整转场类型、时长、参数等。

### Q2：能否同时使用多种转场效果？

A：可以，在 `animation_plan.json` 中配置多个转场，循环使用或按页指定。

### Q3：HTML 动画和视频转场可以同时使用吗？

A：可以，HTML 播放器使用 Framer Motion，视频使用 FFmpeg 转场，互不冲突。

### Q4：如何与现有播放器集成？

A：提供 `ppt_data.json` 和动画配置，`remotion-video-enhancer` 会生成兼容的 HTML 文件。

### Q5：转场效果会影响性能吗？

A：FFmpeg 转场会增加渲染时间，Framer Motion 动画在浏览器端运行，对服务器无影响。
