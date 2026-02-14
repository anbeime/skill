---
name: remotion-video-enhancer
description: 视频转场与动画增强工具，提取 Remotion 的动画理念，提供高级视频转场效果和 Framer Motion 交互式动画。可与 ppt-generator、nanobanana-ppt-visualizer、ppt-roadshow-generator Skill 协同工作。
dependency:
  python:
    - moviepy>=1.0.3
    - pillow>=9.0.0
  system:
    - ffmpeg
---

# Remotion 视频增强工具

## 任务目标
- 本 Skill 用于：为 PPT 内容和视频添加 Remotion 风格的转场和动画效果
- 能力包含：高级视频转场、Framer Motion 交互式动画、动画序列规划、多媒体增强
- 触发条件：用户需要增强视频转场效果、添加交互式动画、或与其他 PPT Skill 协同

## 前置准备
- 依赖说明：scripts 脚本所需的依赖包
  ```
  moviepy>=1.0.3
  pillow>=9.0.0
  ```
- 系统依赖：FFmpeg（必需，用于视频转场处理）
  ```bash
  # Ubuntu/Debian
  sudo apt-get install ffmpeg

  # macOS
  brew install ffmpeg
  ```

## 操作步骤

### 标准流程（完整动画增强）

#### 步骤 1：接收输入数据
根据协同模式，接收不同输入：
- **来自 ppt-generator**：JSON 格式的 PPT 数据
- **来自 nanobanana-ppt-visualizer**：图片文件或 HTML 播放器
- **来自 ppt-roadshow-generator**：已合成的视频文件
- **用户直接提供**：图片序列、视频文件或 JSON 数据

#### 步骤 2：动画规划与配置
1. 分析输入内容，确定动画类型：
   - 视频转场增强（使用 FFmpeg）
   - HTML 交互式动画（使用 Framer Motion）
   - 混合模式（视频 + HTML）
2. 调用 `scripts/animation_planner.py`：
   ```bash
   python scripts/animation_planner.py \
     --input ./input_data \
     --style dynamic \
     --output ./animation_plan.json
   ```
3. 输出动画配置（animation_plan.json），包含：
   - 每个页面/片段的转场类型
   - 动画时长和缓动曲线
   - 元素入场/出场效果
   - 交互式触发条件

#### 步骤 3：视频转场增强（FFmpeg）
1. 调用 `scripts/video_transitions.py`：
   ```bash
   python scripts/video_transitions.py \
     --input ./video.mp4 \
     --transitions ./animation_plan.json \
     --output ./enhanced_video.mp4
   ```
2. 支持的转场类型：
   - **淡入淡出 (Fade)**：经典淡入淡出效果
   - **滑动 (Slide)**：上下左右滑动
   - **缩放 (Zoom)**：推拉镜头效果
   - **翻转 (Flip)**：3D 翻转效果
   - **旋转 (Rotate)**：旋转过渡
   - **模糊 (Blur)**：模糊过渡
   - **溶解 (Dissolve)**：像素溶解效果
   - **弹性 (Elastic)**：弹性动画
3. 每种转场支持自定义：
   - 转场时长（默认 1-2 秒）
   - 缓动曲线（linear, ease-in, ease-out, ease-in-out, bounce, elastic）
   - 方向（上下左右）

#### 步骤 4：HTML 动画增强（Framer Motion）
1. 调用 `scripts/html_animations.py`：
   ```bash
   python scripts/html_animations.py \
     --input ./ppt_data.json \
     --template enhanced_viewer.html \
     --output ./animated_viewer.html
   ```
2. Framer Motion 动画效果：
   - **页面过渡**：流畅的页面切换动画
   - **元素入场**：标题、内容逐个进场
   - **悬停效果**：鼠标悬停时的反馈动画
   - **点击效果**：点击时的涟漪或缩放效果
   - **滚动效果**：滚动时的视差动画
3. 交互式特性：
   - 键盘导航动画
   - 触摸手势支持
   - 全屏过渡动画
   - 进度条动画

#### 步骤 5：输出增强内容
1. 视频增强输出：`enhanced_video.mp4`
2. HTML 动画输出：`animated_viewer.html`
3. 动画配置：`animation_plan.json`

### 与其他 Skill 协同

#### 与 ppt-generator Skill 协同
```
用户请求："生成一个带高级转场的 PPT 视频"

┌─────────────────────────────────────────────────────────┐
│  ppt-generator Skill                                    │
├─────────────────────────────────────────────────────────┤
│  7 角色协作生成 JSON 数据                                │
│  输出：ppt_data.json                                    │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼ JSON 数据
┌─────────────────────────────────────────────────────────┐
│  remotion-video-enhancer Skill                         │
├─────────────────────────────────────────────────────────┤
│  1. 动画规划（animation_planner.py）                     │
│  2. HTML 动画增强（html_animations.py）                 │
│  3. 输出：animated_viewer.html                          │
└─────────────────────────────────────────────────────────┘
```

#### 与 nanobanana-ppt-visualizer Skill 协同
```
用户请求："为生成的播放器添加 Framer Motion 动画"

┌─────────────────────────────────────────────────────────┐
│  nanobanana-ppt-visualizer Skill                        │
├─────────────────────────────────────────────────────────┤
│  生成 HTML 播放器 + 图片                                  │
│  输出：viewer.html, slide-*.png                          │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼ HTML 文件
┌─────────────────────────────────────────────────────────┐
│  remotion-video-enhancer Skill                         │
├─────────────────────────────────────────────────────────┤
│  1. 使用 Framer Motion 增强 viewer.html                 │
│  2. 添加页面过渡、元素入场、交互效果                      │
│  3. 输出：animated_viewer.html                           │
└─────────────────────────────────────────────────────────┘
```

#### 与 ppt-roadshow-generator Skill 协同
```
用户请求："为路演视频添加高级转场效果"

┌─────────────────────────────────────────────────────────┐
│  ppt-roadshow-generator Skill                           │
├─────────────────────────────────────────────────────────┤
│  10 角色协作生成路演视频                                  │
│  输出：roadshow_video.mp4                                │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼ 视频文件
┌─────────────────────────────────────────────────────────┐
│  remotion-video-enhancer Skill                         │
├─────────────────────────────────────────────────────────┤
│  1. 动画规划（animation_planner.py）                     │
│  2. 视频转场增强（video_transitions.py）                 │
│  3. 应用 Remotion 风格转场                              │
│  4. 输出：enhanced_roadshow_video.mp4                   │
└─────────────────────────────────────────────────────────┘
```

### 独立使用模式

#### 模式 A：仅生成动画配置
```bash
python scripts/animation_planner.py \
  --input ./ppt_data.json \
  --style dynamic \
  --output ./animation_plan.json
```
- 适用于：用户希望手动调整动画参数
- 输出：animation_plan.json

#### 模式 B：仅增强视频转场
```bash
python scripts/video_transitions.py \
  --input ./video.mp4 \
  --transitions ./animation_plan.json \
  --output ./enhanced_video.mp4
```
- 适用于：已有视频，需要增强转场效果
- 输出：enhanced_video.mp4

#### 模式 C：仅生成 HTML 动画
```bash
python scripts/html_animations.py \
  --input ./ppt_data.json \
  --template enhanced_viewer.html \
  --output ./animated_viewer.html
```
- 适用于：需要交互式动画播放器
- 输出：animated_viewer.html

### 可选分支
- **快速模式**：使用默认动画配置，跳过动画规划
- **自定义模式**：用户提供自定义动画配置 JSON
- **批量处理**：一次性处理多个视频或 PPT
- **模板模式**：使用预设动画模板（见 assets/animations/）

## 资源索引
- 动画规划脚本：见 [scripts/animation_planner.py](scripts/animation_planner.py)（用途：生成动画配置）
- 视频转场脚本：见 [scripts/video_transitions.py](scripts/video_transitions.py)（用途：FFmpeg 视频转场）
- HTML 动画脚本：见 [scripts/html_animations.py](scripts/html_animations.py)（用途：Framer Motion 动画）
- 转场效果指南：见 [references/transition_guide.md](references/transition_guide.md)（用途：转场效果详细说明）
- 动画模板：见 [assets/animations/](assets/animations/)（可选：预设动画配置）
- HTML 模板：见 [assets/templates/enhanced_viewer.html](assets/templates/enhanced_viewer.html)（Framer Motion 播放器）
- 协同指南：见 [references/collaboration_guide.md](references/collaboration_guide.md)（与其他 Skill 协同）

## 注意事项
- 本 Skill 不依赖任何第三方 AI API，所有动画使用 FFmpeg 和 Framer Motion 实现
- 视频转场使用 FFmpeg，确保已安装
- HTML 动画使用 Framer Motion CDN，无需安装
- 动画配置 JSON 格式必须符合规范（见 references/transition_guide.md）
- 与其他 Skill 协同时，确保输入格式正确
- 支持批量处理，但建议单个视频不超过 100 页
- Framer Motion 动画仅在现代浏览器中支持

## 使用示例

### 示例 1：与 ppt-generator 协同生成动画播放器
- 功能说明：ppt-generator 生成内容，remotion-video-enhancer 添加动画
- 执行方式：ppt-generator → remotion-video-enhancer（Framer Motion）
- 用户指令："生成一个产品介绍 PPT，使用 Framer Motion 动画"
- 输出：animated_viewer.html

### 示例 2：为路演视频添加高级转场
- 功能说明：增强现有视频的转场效果
- 执行方式：ppt-roadshow-generator → remotion-video-enhancer（FFmpeg 转场）
- 用户指令："为路演视频添加 Remotion 风格的转场"
- 输出：enhanced_roadshow_video.mp4

### 示例 3：自定义动画配置
- 功能说明：用户手动指定动画类型和参数
- 执行方式：用户提供 animation_plan.json → 视频转场
- 配置示例：
  ```json
  {
    "transitions": [
      {"type": "slide", "direction": "right", "duration": 1.5},
      {"type": "zoom", "scale": 1.2, "duration": 1.0}
    ]
  }
  ```
- 输出：按自定义配置增强的视频

### 示例 4：批量处理多个视频
- 功能说明：一次性增强多个视频
- 执行方式：脚本批量处理
- 命令：
  ```bash
  python scripts/video_transitions.py \
    --input-dir ./videos/ \
    --transitions ./animation_plan.json \
    --output-dir ./enhanced_videos/
  ```
- 输出：批量增强的视频文件
