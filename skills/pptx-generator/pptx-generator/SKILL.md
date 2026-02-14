---
name: pptx-generator
description: 将 JSON 格式的 PPT 内容转换为标准的 .pptx 文件。使用 python-pptx 库，支持多种布局、图表、表格和样式。与 ppt-generator Skill 完全协同，可作为独立使用或与其他 PPT Skill 配合。
dependency:
  python:
    - python-pptx>=1.0.2
    - pillow>=9.0.0
    - openpyxl>=3.1.0
---

# PPTX 文件生成器

## 任务目标
- 本 Skill 用于：将 JSON 格式的 PPT 内容转换为标准的 .pptx 文件
- 能力包含：JSON 解析、PPTX 创建、多布局支持、样式应用、图表生成、表格生成
- 触发条件：用户需要生成 .pptx 文件，或需要将 JSON 数据转换为可编辑的 PPT

## 前置准备
- 依赖说明：scripts 脚本所需的依赖包
  ```
  python-pptx>=1.0.2
  pillow>=9.0.0
  openpyxl>=3.1.0
  ```

## 操作步骤

### 标准流程（JSON 转 PPTX）

#### 步骤 1：接收 JSON 数据
从以下来源接收 JSON 数据：
- **ppt-generator Skill**：7 角色协作生成的 JSON
- **用户直接提供**：符合格式规范的 JSON 文件
- **其他来源**：任何符合 JSON 格式的 PPT 数据

#### 步骤 2：验证 JSON 格式
调用 `scripts/json_validator.py` 验证 JSON 格式：
```bash
python scripts/json_validator.py --input ./ppt_data.json
```
验证内容包括：
- 元数据完整性（title, author, theme）
- 幻灯片数组存在性
- 每个幻灯片的必需字段（title, content）
- 数据类型正确性

#### 步骤 3：生成 PPTX 文件
调用 `scripts/pptx_builder.py` 生成 .pptx 文件：
```bash
python scripts/pptx_builder.py \
  --input ./ppt_data.json \
  --style assets/styles/modern.json \
  --output ./presentation.pptx
```

**核心功能**：
1. **创建演示文稿**：初始化 Presentation 对象
2. **添加幻灯片**：根据 JSON 数据逐页添加
3. **应用布局**：根据幻灯片类型选择布局
4. **添加内容**：
   - 标题（Title）
   - 内容（Text、Bullet Points）
   - 图片（Picture）
   - 图表（Chart）
   - 表格（Table）
5. **应用样式**：根据风格配置设置字体、颜色、间距
6. **保存文件**：导出为 .pptx 文件

#### 步骤 4：验证 PPTX 文件
调用 `scripts/pptx_validator.py` 验证生成的 .pptx 文件：
```bash
python scripts/pptx_validator.py --input ./presentation.pptx
```
验证内容包括：
- 文件完整性
- 幻灯片数量
- 内容正确性
- 可编辑性

### 高级功能

#### 自定义样式
使用自定义风格配置：
```bash
python scripts/pptx_builder.py \
  --input ./ppt_data.json \
  --style ./custom_style.json \
  --output ./presentation.pptx
```

#### 批量生成
批量处理多个 JSON 文件：
```bash
python scripts/pptx_builder.py \
  --input-dir ./json_files/ \
  --style assets/styles/modern.json \
  --output-dir ./pptx_files/
```

#### 使用模板
基于模板生成 PPTX：
```bash
python scripts/pptx_builder.py \
  --input ./ppt_data.json \
  --template assets/templates/business_template.pptx \
  --output ./presentation.pptx
```

### 与其他 Skill 协同

#### 与 ppt-generator 协同
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
│  2. PPTX 构建（pptx_builder.py）                       │
│     - 创建演示文稿                                      │
│     - 添加幻灯片                                        │
│     - 应用布局和样式                                    │
│     - 添加内容（文本、图片、图表、表格）                  │
│  3. PPTX 验证（pptx_validator.py）                     │
│  4. 输出 .pptx 文件                                   │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼ presentation.pptx
```

#### 与 nanobanana-ppt-visualizer 协同
```
用户请求："生成 PPT 文件和图片"

ppt-generator → pptx-generator → nanobanana-ppt-visualizer
     ↓              ↓                  ↓
  JSON 数据      .pptx 文件        图片 + HTML 播放器
```

#### 完整工作流
```
1. ppt-generator → JSON 数据
2. pptx-generator → .pptx 文件
3. nanobanana-ppt-visualizer → 图片 + HTML 播放器
4. ppt-roadshow-generator → 视频
5. remotion-video-enhancer → 增强动画
```

## 资源索引
- JSON 验证脚本：见 [scripts/json_validator.py](scripts/json_validator.py)（用途：验证 JSON 格式）
- PPTX 构建脚本：见 [scripts/pptx_builder.py](scripts/pptx_builder.py)（用途：生成 .pptx 文件）
- PPTX 验证脚本：见 [scripts/pptx_validator.py](scripts/pptx_validator.py)（用途：验证 .pptx 文件）
- 格式规范：见 [references/json_format_spec.md](references/json_format_spec.md)（用途：JSON 格式标准）
- 布局指南：见 [references/layout_guide.md](references/layout_guide.md)（用途：布局类型说明）
- 风格配置：见 [assets/styles/](assets/styles/)（可选：modern, minimal, business）
- 协同指南：见 [references/collaboration_guide.md](references/collaboration_guide.md)（用途：与其他 Skill 协同）

## 注意事项
- 本 Skill 使用 python-pptx 库生成标准的 .pptx 文件
- JSON 格式必须符合规范（见 references/json_format_spec.md）
- 支持的图片格式：PNG、JPG、JPEG、GIF
- 支持的图表类型：柱状图、折线图、饼图
- 支持的表格：普通表格、样式化表格
- 与 ppt-generator Skill 完全兼容，可无缝协同
- 生成的 .pptx 文件可在 Microsoft PowerPoint、WPS 等软件中编辑

## 使用示例

### 示例 1：与 ppt-generator 协同生成 PPTX
- 功能说明：ppt-generator 生成 JSON，pptx-generator 生成 .pptx
- 执行方式：ppt-generator → pptx-generator
- 用户指令："生成一个产品介绍的 PPT 文件"
- 输出：presentation.pptx

### 示例 2：仅生成 PPTX 文件
- 功能说明：基于现有 JSON 生成 .pptx 文件
- 执行方式：pptx-generator 独立运行
- 关键参数：JSON 文件路径、风格配置
- 命令：`python scripts/pptx_builder.py --input ./ppt_data.json --output ./presentation.pptx`

### 示例 3：自定义风格生成
- 功能说明：使用自定义风格配置
- 执行方式：指定自定义风格文件
- 关键参数：--style
- 命令：`python scripts/pptx_builder.py --input ./ppt_data.json --style ./my_style.json --output ./presentation.pptx`

### 示例 4：批量生成 PPTX 文件
- 功能说明：一次性处理多个 JSON 文件
- 执行方式：批量处理
- 关键参数：--input-dir, --output-dir
- 命令：`python scripts/pptx_builder.py --input-dir ./json_files/ --output-dir ./pptx_files/`
