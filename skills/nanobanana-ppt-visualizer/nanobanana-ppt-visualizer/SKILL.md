---
name: nanobanana-ppt-visualizer
description: PPT 视觉增强工具，支持多种风格渲染、交互式播放器生成和视频合成。可与 ppt-generator Skill 协同工作，实现从内容规划到视觉呈现的完整流程。
dependency:
  python:
    - pillow>=9.0.0
    - python-dotenv>=0.19.0
---

# PPT 视觉增强工具

## 任务目标
- 本 Skill 用于：为 PPT 内容生成高质量视觉呈现，包括图片渲染、交互式播放器和视频合成
- 能力包含：风格化图片生成、HTML 播放器生成、视频素材管理、FFmpeg 视频合成
- 触发条件：用户需要为 PPT 内容添加视觉效果，或与 ppt-generator Skill 协同工作

## 前置准备
- 依赖说明：scripts 脚本所需的依赖包
  ```
  pillow>=9.0.0
  python-dotenv>=0.19.0
  ```
- 系统依赖：FFmpeg（可选，用于视频合成功能）
  ```bash
  # Ubuntu/Debian
  sudo apt-get install ffmpeg

  # macOS
  brew install ffmpeg
  ```

## 操作步骤

### 标准流程（与 ppt-generator 协同）

#### 步骤 1：获取 PPT 内容（协作模式）
1. 与 ppt-generator Skill 协同：
   - ppt-generator 负责：主题分析、内容规划、结构设计
   - 输出格式：符合规范的 JSON 数据（详见 [references/ppt_structure_guide.md](references/ppt_structure_guide.md)）
2. 接收 JSON 数据，包含：
   - metadata：标题、作者、主题、关键词
   - slides：每页的布局、标题、内容、图片标注

#### 步骤 2：选择视觉风格
1. 扫描 `assets/styles/` 目录，列出可用风格：
   - `gradient-glass.md`：渐变毛玻璃风格（科技感、商务）
   - `vector-illustration.md`：矢量插画风格（温暖、教育）
2. 根据内容主题和场景推荐合适的风格
3. 智能体生成图片描述提示词，参考风格模板

#### 步骤 3：生成视觉素材
1. **图片生成**（使用智能体能力）：
   - 根据每页内容和风格模板，生成图片描述
   - 使用智能体的图像生成能力创建图片
   - 保存为 slide-01.png, slide-02.png 等

2. **可选：视频生成**（需要可灵 AI API）：
   - 如果用户需要视频转场，调用可灵 AI API
   - 生成首页预览视频和页面转场视频
   - 使用 `scripts/video_materials.py` 管理视频素材

#### 步骤 4：生成播放器
1. 调用 `scripts/generate_viewer.py` 生成 HTML 播放器：
   - 支持图片轮播、键盘导航、全屏播放
   - 支持视频+图片混合播放（如果生成了视频）
2. 输出交互式播放器，可直接在浏览器中预览

#### 步骤 5：视频合成（可选）
1. 如果生成了视频素材，调用 `scripts/video_composer.py`：
   - 使用 FFmpeg 合成完整视频
   - 统一分辨率和帧率
   - 输出 full_ppt_video.mp4

### 独立使用模式

当用户直接提供 PPT 内容（JSON 格式）时：

1. 读取用户提供的 JSON 文件或内容
2. 执行步骤 2-5，生成视觉呈现

## 协同工作流程

### 与 ppt-generator Skill 配合

```
用户请求："生成一个关于 AI 产品的 PPT"

┌─────────────────────────────────────────────────────────┐
│  ppt-generator Skill                                    │
├─────────────────────────────────────────────────────────┤
│  1. 主题分析师：分析主题，生成大纲                        │
│  2. 模板设计师：推荐布局                                  │
│  3. 内容策划师：规划内容结构                              │
│  4. 文本创作者：撰写内容                                  │
│  5. 视觉设计师：提供配图建议                              │
│  6. 优化编辑师：优化文本                                  │
│  7. PPT 构建师：生成 JSON 数据                           │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼ 输出 JSON
┌─────────────────────────────────────────────────────────┐
│  nanobanana-ppt-visualizer Skill                        │
├─────────────────────────────────────────────────────────┤
│  1. 接收 JSON 数据                                       │
│  2. 选择视觉风格                                          │
│  3. 生成图片（使用智能体能力）                            │
│  4. 生成 HTML 播放器                                      │
│  5. 可选：视频合成                                        │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼ 输出
              交互式播放器 + 完整视频（可选）
```

### 数据格式兼容性

ppt-generator 输出的 JSON 格式与 nanobanana-ppt-visualizer 完全兼容：

```json
{
  "metadata": {
    "title": "演示文稿标题",
    "author": "作者姓名"
  },
  "slides": [
    {
      "layout": "TitleSlide",
      "title": "封面标题",
      "content": ["副标题"],
      "notes": "备注"
    }
  ]
}
```

## 资源索引
- 图片生成脚本：见 [scripts/generate_viewer.py](scripts/generate_viewer.py)（用途：生成 HTML 播放器和图片管理）
- 视频素材管理：见 [scripts/video_materials.py](scripts/video_materials.py)（用途：管理视频素材）
- 视频合成：见 [scripts/video_composer.py](scripts/video_composer.py)（用途：FFmpeg 视频合成）
- 格式规范：见 [references/ppt_structure_guide.md](references/ppt_structure_guide.md)（用途：JSON 数据格式标准）
- 协同指南：见 [references/collaboration_guide.md](references/collaboration_guide.md)（用途：与 ppt-generator 协同工作指南）
- 风格模板：见 [assets/styles/](assets/styles/)（可选：gradient-glass.md、vector-illustration.md）
- HTML 模板：见 [assets/templates/](assets/templates/)（可选：viewer.html、video_viewer.html）

## 注意事项
- 本 Skill 与 ppt-generator Skill 完全兼容，可以无缝协作
- 图片生成使用智能体的图像生成能力，无需第三方 API
- 视频生成功能需要可灵 AI API（可选），如需使用请配置密钥
- FFmpeg 是可选依赖，仅在使用视频合成功能时需要
- 保持与用户的互动，在关键节点（如风格选择）征求反馈

## 使用示例

### 示例 1：与 ppt-generator 完整协作
- 功能说明：两个 Skill 完整协作，从内容到视觉
- 执行方式：ppt-generator（7 个角色）→ nanobanana-ppt-visualizer（视觉生成）
- 用户指令："生成一个关于 AI 产品的 PPT，使用渐变毛玻璃风格"
- 输出：交互式播放器 + 完整视频（可选）

### 示例 2：基于现有 JSON 生成播放器
- 功能说明：接收 JSON 数据，生成播放器
- 执行方式：nanobanana-ppt-visualizer 独立运行
- 关键参数：JSON 文件路径、风格选择
- 命令：`python scripts/generate_viewer.py --input ./ppt_data.json --style gradient-glass`

### 示例 3：仅生成图片（无视频）
- 功能说明：使用智能体生成 PPT 图片
- 执行方式：智能体（图像生成）+ 脚本（播放器生成）
- 适用场景：快速预览、静态展示
- 输出：HTML 播放器 + 图片文件

### 示例 4：完整视频合成
- 功能说明：合成包含转场的完整视频
- 执行方式：脚本（FFmpeg 合成）
- 前提：已生成图片和视频素材
- 命令：`python scripts/video_composer.py --output ./full_ppt_video.mp4`
