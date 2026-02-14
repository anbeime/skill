# 协同工作指南

本指南说明 nanobanana-ppt-visualizer Skill 与 ppt-generator Skill 如何协同工作，实现从内容规划到视觉呈现的完整流程。

## 协同架构

### 角色分工

| Skill | 角色 | 职责 | 输出 |
|-------|------|------|------|
| **ppt-generator** | 内容生成器 | 主题分析、内容规划、结构设计 | PPT 内容（JSON 格式） |
| **nanobanana-ppt-visualizer** | 视觉增强器 | 图片生成、播放器生成、视频合成 | 交互式播放器、视频 |

### 完整工作流

```
用户请求
  │
  ▼
┌─────────────────────────────────────────────────────────┐
│  第一阶段：内容生成（ppt-generator）                       │
├─────────────────────────────────────────────────────────┤
│  1. 主题分析师：分析主题，生成大纲                        │
│  2. 模板设计师：推荐布局类型                              │
│  3. 内容策划师：规划内容结构                              │
│  4. 文本创作者：撰写详细内容                              │
│  5. 视觉设计师：提供配图建议                              │
│  6. 优化编辑师：优化文本和结构                            │
│  7. PPT 构建师：生成 JSON 数据                           │
└─────────────────────────────────────────────────────────┘
  │
  ▼ 输出 JSON
┌─────────────────────────────────────────────────────────┐
│  第二阶段：视觉呈现（nanobanana-ppt-visualizer）           │
├─────────────────────────────────────────────────────────┤
│  1. 接收 JSON 数据                                       │
│  2. 选择视觉风格                                          │
│  3. 使用智能体生成图片                                    │
│  4. 生成 HTML 播放器                                      │
│  5. 可选：视频合成                                        │
└─────────────────────────────────────────────────────────┘
  │
  ▼ 输出
交互式播放器 + 完整视频（可选）
```

## 数据接口

### ppt-generator 输出格式

ppt-generator 输出的 JSON 格式完全符合 nanobanana-ppt-visualizer 的输入要求：

```json
{
  "metadata": {
    "title": "演示文稿标题",
    "author": "作者姓名",
    "subject": "主题描述",
    "keywords": "关键词"
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

### nanobanana-ppt-visualizer 输入要求

nanobanana-ppt-visualizer 接收与上述格式完全相同的 JSON，无需额外转换。

## 协同使用场景

### 场景 1：完整协作（推荐）

**用户请求**：
```
生成一个关于 AI 产品的 PPT，包含 10 页，使用渐变毛玻璃风格
```

**执行流程**：
1. ppt-generator 执行 7 个角色，生成 PPT 内容（JSON）
2. 传递 JSON 给 nanobanana-ppt-visualizer
3. nanobanana-ppt-visualizer：
   - 选择渐变毛玻璃风格
   - 使用智能体生成 10 张图片
   - 生成 HTML 播放器
   - （可选）合成完整视频

**输出**：
- HTML 播放器（可在浏览器中查看）
- 10 张高质量图片
- （可选）完整视频文件

### 场景 2：先生成内容，后添加视觉

**用户请求**：
```
先帮我生成一个关于市场营销的 PPT 大纲和内容
```

**执行流程**：
1. ppt-generator 生成内容（JSON）
2. 用户确认内容后：
3. 用户继续请求："给这个 PPT 添加视觉效果，使用矢量插画风格"
4. nanobanana-ppt-visualizer 接收 JSON，生成图片和播放器

**优势**：
- 用户可以先确认内容，再决定视觉风格
- 支持迭代优化

### 场景 3：仅使用内容，不生成视觉

**用户请求**：
```
生成一个 PPT 内容大纲，我需要手动编辑
```

**执行流程**：
1. ppt-generator 仅执行内容生成
2. 输出 JSON 文件供用户下载
3. 用户后续可选择是否调用 nanobanana-ppt-visualizer

### 场景 4：基于现有 JSON 生成视觉

**用户请求**：
```
我有一个 PPT 的 JSON 文件，帮我生成图片和播放器
```

**执行流程**：
1. 用户上传或提供 JSON 文件路径
2. nanobanana-ppt-visualizer 独立运行
3. 生成图片和播放器

**适用场景**：
- 用户已有内容，仅需要视觉呈现
- 使用其他工具生成的内容

## 风格协同

### ppt-generator 的视觉建议

ppt-generator 的"视觉设计师"角色会提供图片建议：

```json
{
  "layout": "TitleAndContent",
  "title": "市场分析",
  "content": [
    "市场规模：2023年达到100亿美元",
    "年增长率：15%",
    "[图片：数据分析图表]",
    "[图表：柱状图，展示近五年市场规模]"
  ],
  "notes": "建议使用柱状图展示市场规模增长趋势"
}
```

### nanobanana-ppt-visualizer 的风格选择

nanobanana-ppt-visualizer 支持多种风格：
- **渐变毛玻璃风格**（gradient-glass）：科技感、商务场景
- **矢量插画风格**（vector-illustration）：温暖、教育场景

风格选择建议：
- 商务汇报、科技产品 → 渐变毛玻璃风格
- 教育培训、创意提案 → 矢量插画风格

## API 调用协同

### 图片生成

**ppt-generator**：
- 提供图片描述和建议（自然语言）
- 不实际生成图片

**nanobanana-ppt-visualizer**：
- 接收图片描述
- 使用智能体的图像生成能力创建图片
- 无需第三方 API（如 Google Gemini）

### 视频生成（可选）

**ppt-generator**：
- 不涉及视频生成

**nanobanana-ppt-visualizer**：
- 可选功能：使用可灵 AI API 生成视频
- 需要用户配置 API 密钥
- 如不使用，则跳过视频生成

## 输出文件协同

### 文件命名规范

两个 Skill 使用统一的文件命名规范：

- JSON 数据：`ppt_data.json`
- 图片文件：`slide-01.png`, `slide-02.png`, ...
- HTML 播放器：`index.html` 或 `video_index.html`
- 完整视频：`full_ppt_video.mp4`

### 输出目录结构

```
workspace/
├── ppt_data.json           # ppt-generator 输出
└── outputs/
    ├── 20241215_123456/    # nanobanana-ppt-visualizer 输出（图片模式）
    │   ├── index.html
    │   └── images/
    │       ├── slide-01.png
    │       └── ...
    └── 20241215_123456_video/  # nanobanana-ppt-visualizer 输出（视频模式）
        ├── video_index.html
        ├── videos/
        │   ├── preview.mp4
        │   └── transition_*.mp4
        ├── images/
        │   ├── slide-01.png
        │   └── ...
        └── full_ppt_video.mp4
```

## 最佳实践

### 1. 顺序使用
先调用 ppt-generator 生成内容，再调用 nanobanana-ppt-visualizer 生成视觉。这是最推荐的流程。

### 2. 内容确认
在生成视觉之前，建议用户先确认 ppt-generator 的输出内容，避免重复生成。

### 3. 风格一致性
整个 PPT 应使用统一的风格，nanobanana-ppt-visualizer 会自动确保所有图片风格一致。

### 4. 质量控制
- ppt-generator：确保内容逻辑清晰、文字精炼
- nanobanana-ppt-visualizer：确保图片质量高、播放器流畅

### 5. 性能优化
- 图片生成：建议一次生成所有页面，避免多次调用
- 视频生成：耗时较长，建议在确认内容后再进行

## 故障排查

### 问题 1：JSON 格式不兼容
**症状**：nanobanana-ppt-visualizer 无法解析 ppt-generator 的输出
**解决**：确保使用最新版本的两个 Skill，它们使用统一的 JSON 格式

### 问题 2：图片生成失败
**症状**：智能体无法生成图片
**解决**：
- 检查图片描述是否清晰
- 确认智能体的图像生成功能可用
- 尝试简化图片描述

### 问题 3：播放器无法加载图片
**症状**：HTML 播放器显示空白
**解决**：
- 确认图片文件存在于 `images/` 目录
- 检查图片文件名格式（slide-01.png）
- 确认 HTML 文件与 images 目录在同一级

### 问题 4：视频合成失败
**症状**：FFmpeg 报错
**解决**：
- 确认已安装 FFmpeg
- 检查视频素材是否完整
- 确认所有视频的分辨率和帧率一致

## 总结

ppt-generator 和 nanobanana-ppt-visualizer 两个 Skill 完美互补：
- ppt-generator 专注于内容质量和结构设计
- nanobanana-ppt-visualizer 专注于视觉呈现和用户体验

通过协同工作，可以实现从零开始到最终交付的完整 PPT 生成流程。
