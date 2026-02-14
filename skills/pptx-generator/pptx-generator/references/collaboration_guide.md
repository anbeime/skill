# 与其他 Skill 协同指南

本文档详细说明 `pptx-generator` Skill 如何与其他 PPT 相关 Skill 协同工作。

## 目录
1. [协同模式概述](#协同模式概述)
2. [与 ppt-generator 协同](#与-ppt-generator-协同)
3. [与 nanobanana-ppt-visualizer 协同](#与-nanobanana-ppt-visualizer-协同)
4. [完整工作流程](#完整工作流程)
5. [数据格式兼容性](#数据格式兼容性)

---

## 协同模式概述

`pptx-generator` Skill 是 PPT 工具链中的**关键环节**，负责将 JSON 数据转换为标准的 .pptx 文件。

### PPT 工具链

```
1. ppt-generator (JSON 数据生成)
         ↓
2. pptx-generator (PPTX 文件生成) ← 关键环节
         ↓
3. nanobanana-ppt-visualizer (视觉增强，可选)
         ↓
4. ppt-roadshow-generator (视频生成，可选)
         ↓
5. remotion-video-enhancer (动画增强，可选)
```

### 协同关系表

| Skill | 输出 | 接收 | 用途 |
|-------|------|------|------|
| ppt-generator | JSON | pptx-generator | 内容生成 |
| pptx-generator | .pptx | nanobanana-ppt-visualizer | 文件生成 |
| nanobanana-ppt-visualizer | 图片 + HTML | ppt-roadshow-generator | 视觉增强 |
| ppt-roadshow-generator | 视频 | remotion-video-enhancer | 视频生成 |
| remotion-video-enhancer | 增强视频 | 用户 | 动画增强 |

---

## 与 ppt-generator 协同

### 协同流程

```
用户请求："生成一个 PPT 文件"

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
│  pptx-generator Skill                                  │
├─────────────────────────────────────────────────────────┤
│  1. JSON 验证（json_validator.py）                     │
│     - 验证 JSON 格式                                    │
│     - 检查必需字段                                      │
│  2. PPTX 构建（pptx_builder.py）                       │
│     - 创建演示文稿                                      │
│     - 添加幻灯片                                        │
│     - 应用布局和样式                                    │
│     - 添加内容（文本、内容）                              │
│  3. PPTX 验证（pptx_validator.py）                     │
│     - 验证文件完整性                                    │
│     - 检查幻灯片数量                                    │
│  4. 输出 .pptx 文件                                   │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼ presentation.pptx
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

**pptx-generator 接收并处理**：
- 输入：`ppt_data.json`
- 处理：验证、构建、生成 .pptx
- 输出：`presentation.pptx`

### 使用示例

**步骤 1：ppt-generator 生成 JSON**
```bash
# ppt-generator 执行后输出
ppt_data.json
```

**步骤 2：pptx-generator 生成 PPTX**
```bash
# 验证 JSON
python scripts/json_validator.py --input ./ppt_data.json

# 生成 PPTX
python scripts/pptx_builder.py --input ./ppt_data.json --output ./presentation.pptx

# 验证 PPTX
python scripts/pptx_validator.py --input ./presentation.pptx
```

**步骤 3：在 PowerPoint 中打开**
```bash
# 使用 PowerPoint 打开
open presentation.pptx  # macOS
# 或
xdg-open presentation.pptx  # Linux
```

---

## 与 nanobanana-ppt-visualizer 协同

### 协同流程

```
用户请求："生成 PPT 文件和图片"

1. ppt-generator → ppt_data.json
2. pptx-generator → presentation.pptx
3. nanobanana-ppt-visualizer → 图片 + HTML 播放器
```

### 两种使用模式

**模式 A：仅生成 PPTX 文件**
- 适用于：需要 .pptx 文件进行编辑
- 流程：ppt-generator → pptx-generator

**模式 B：生成 PPTX + 图片 + HTML 播放器**
- 适用于：需要多种格式输出
- 流程：ppt-generator → pptx-generator → nanobanana-ppt-visualizer

### 使用示例

**模式 A：仅生成 PPTX**
```bash
# 步骤 1：ppt-generator 生成 JSON
# ...

# 步骤 2：pptx-generator 生成 PPTX
python scripts/pptx_builder.py \
  --input ./ppt_data.json \
  --output ./presentation.pptx
```

**模式 B：生成 PPTX + 图片**
```bash
# 步骤 1：ppt-generator 生成 JSON
# ...

# 步骤 2：pptx-generator 生成 PPTX
python scripts/pptx_builder.py \
  --input ./ppt_data.json \
  --output ./presentation.pptx

# 步骤 3：nanobanana-ppt-visualizer 生成图片
# nanobanana-ppt-visualizer 执行...
```

---

## 完整工作流程

### 场景 1：仅生成 PPTX 文件

```
用户请求："生成一个 PPT 文件"

ppt-generator (7 角色协作)
    ↓
pptx-generator (生成 .pptx)
    ↓
presentation.pptx
```

**执行步骤**：
1. ppt-generator 生成 JSON
2. pptx-generator 生成 .pptx
3. 用户在 PowerPoint 中打开编辑

### 场景 2：生成 PPTX + 图片 + HTML 播放器

```
用户请求："生成 PPT 文件和网页播放器"

ppt-generator (7 角色协作)
    ↓
pptx-generator (生成 .pptx)
    ↓
nanobanana-ppt-visualizer (生成图片 + HTML)
    ↓
presentation.pptx + images/ + viewer.html
```

**执行步骤**：
1. ppt-generator 生成 JSON
2. pptx-generator 生成 .pptx
3. nanobanana-ppt-visualizer 生成图片和播放器

### 场景 3：生成完整路演视频

```
用户请求："生成完整的路演视频"

1. ppt-generator (7 角色协作)
    ↓ ppt_data.json

2. pptx-generator (生成 .pptx)
    ↓ presentation.pptx

3. nanobanana-ppt-visualizer (生成图片)
    ↓ images/

4. ppt-roadshow-generator (10 角色协作)
    ↓ roadshow_video.mp4

5. remotion-video-enhancer (增强动画)
    ↓ enhanced_roadshow_video.mp4
```

**执行步骤**：
1. ppt-generator 生成 JSON
2. pptx-generator 生成 .pptx
3. nanobanana-ppt-visualizer 生成图片
4. ppt-roadshow-generator 生成视频
5. remotion-video-enhancer 增强动画

---

## 数据格式兼容性

### JSON 格式标准

ppt-generator 和 pptx-generator 使用相同的 JSON 格式：

```json
{
  "metadata": {
    "title": "演示文稿标题",
    "author": "作者姓名",
    "theme": "主题风格"
  },
  "slides": [
    {
      "layout": "ContentSlide",
      "title": "幻灯片标题",
      "content": ["内容要点1", "内容要点2"],
      "notes": "备注内容"
    }
  ]
}
```

### 兼容性说明

| 字段 | ppt-generator | pptx-generator | 兼容性 |
|------|--------------|---------------|--------|
| metadata.title | ✓ | ✓ | 完全兼容 |
| metadata.author | ✓ | ✓ | 完全兼容 |
| metadata.theme | ✓ | ✓ | 完全兼容 |
| slides[*].layout | ✓ | ✓ | 完全兼容 |
| slides[*].title | ✓ | ✓ | 完全兼容 |
| slides[*].content | ✓ | ✓ | 完全兼容 |
| slides[*].notes | ✓ | ✓ | 完全兼容 |

### 验证命令

```bash
# 验证 JSON 格式
python scripts/json_validator.py --input ./ppt_data.json
```

---

## 注意事项

### 1. 输入文件检查

在使用 pptx-generator 之前，确保：
- JSON 文件格式正确
- JSON 文件存在且可读
- 幻灯片数量合理（建议 5-20 页）

### 2. 输出文件管理

- 使用有意义的文件名
- 定期清理临时文件
- 区分不同版本的输出

### 3. 布局选择

根据内容类型选择合适的布局：
- 封面：TitleSlide
- 标准内容：ContentSlide
- 对比：TwoColumnSlide
- 总结：SummarySlide

### 4. 样式应用

使用风格配置文件自定义样式：
- 字体设置
- 颜色设置
- 大小设置

### 5. 测试和调整

- 生成后在 PowerPoint 中打开查看
- 检查布局和内容
- 必要时调整 JSON 数据

---

## 常见问题

### Q1：pptx-generator 能生成哪些元素？

A：目前支持：
- 标题（Title）
- 内容（Text、Bullet Points）
- 备注（Notes）
- 未来版本将支持：图片、图表、表格

### Q2：能否自定义布局？

A：目前使用预设布局，未来版本将支持自定义布局。

### Q3：生成的 .pptx 文件能在哪些软件中打开？

A：支持的软件：
- Microsoft PowerPoint
- WPS Office
- Google Slides（导入）
- LibreOffice Impress

### Q4：如何与现有播放器集成？

A：pptx-generator 生成 .pptx 文件，可与 nanobanana-ppt-visualizer 生成的播放器配合使用。

### Q5：能否批量生成多个 PPTX 文件？

A：可以，使用批量处理命令：
```bash
python scripts/pptx_builder.py \
  --input-dir ./json_files/ \
  --output-dir ./pptx_files/
```
