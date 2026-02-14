---
name: web-design-analyzer
description: 分析网页截图，提取设计系统（Design System）并生成结构化数据和可用的 AI Coding Prompt。适用于 UI/UX 设计师和前端工程师需要从现有网页设计中提取设计规范、配色方案、排版系统和组件风格的场景。
dependency:
  python:
    - Pillow>=10.0.0
  system: []
---

# Web Design Analyzer

## 任务目标
- 本 Skill 用于：从网页截图中自动提取设计系统（Design System），包括色彩、排版、组件风格等核心要素
- 能力包含：
  - 自动识别网页视觉风格（Vibe & Style）
  - 提取精确的色彩系统（Hex Code + Tailwind 类名）
  - 分析排版系统（字体类型、字重、行高）
  - 识别组件特征（圆角、阴影、边框）
  - 生成结构化 JSON 数据和可直接使用的 Coding Prompt
  - 导出为路演视频品牌风格配置（与 ppt-roadshow-generator 协同）
- 触发条件：用户上传网页截图并要求分析其设计，或需要将网页设计风格应用于路演视频

## 前置准备
- 依赖说明：scripts 脚本所需的依赖包及版本
  ```
  Pillow>=10.0.0
  ```
- 非标准文件/文件夹准备：无

## 操作步骤
- 标准流程：
  1. **接收图片**
     - 用户上传网页截图（支持 PNG、JPG、JPEG 等常见格式）
     - 智能体确认图片文件路径

  2. **调用分析脚本**
     - 智能体调用 `scripts/analyze_design.py --image <图片文件路径>` 执行分析
     - 脚本将自动调用 OpenAI GPT-4 Vision API 处理图片
     - 脚本返回结构化的分析结果

  3. **展示结果**
     - 智能体展示 JSON 格式的设计系统数据
     - 智能体展示生成的 Coding Prompt
     - 智能体提供进一步操作建议（如：使用生成的 Prompt 创建 Landing Page）

- 可选分支：
  - 当用户希望使用 Gemini API：提示当前版本仅支持 OpenAI，未来可能扩展
  - 当 API 调用失败：提供错误信息和可能的解决方案（如检查 API Key、图片格式等）

## 资源索引
- 必要脚本：
  - 见 [scripts/analyze_design.py](scripts/analyze_design.py)（用途与参数：接收图片路径，调用 OpenAI Vision API，返回设计系统分析结果）
  - 见 [scripts/convert_to_roadshow_style.py](scripts/convert_to_roadshow_style.py)（用途与参数：将设计系统转换为路演视频品牌风格，输入 `--input` 指定 JSON 路径，`--output` 指定输出路径）
- 领域参考：
  - 见 [references/api-spec.md](references/api-spec.md)（何时读取：需要了解 API 调用细节或调试时）
  - 见 [references/roadshow-export-guide.md](references/roadshow-export-guide.md)（何时读取：需要将设计系统导出为路演视频风格时）
- 输出资产：无

## 注意事项
- 仅在需要时读取参考，保持上下文简洁。
- 确保用户上传的图片清晰度足够，以便准确提取设计细节。
- 脚本会自动处理图片编码和 API 调用，无需手动干预。
- 充分利用智能体的语言理解和展示能力，将 API 返回的结构化数据以友好的方式呈现给用户。

## 使用示例

### 示例 1：分析网页截图
- **功能说明**：上传一张网页截图，提取完整的设计系统
- **执行方式**：混合（用户上传 → 脚本分析 → 智能体展示）
- **关键参数**：图片文件路径
- **简单示例**：
  ```bash
  # 用户：请分析这张网页截图
  # 智能体调用脚本
  python scripts/analyze_design.py --image ./uploads/landing-page.png
  ```

### 示例 2：生成 Coding Prompt 后创建组件
- **功能说明**：先分析设计，然后使用生成的 Prompt 创建类似的 Landing Page
- **执行方式**：混合（脚本分析 → 智能体生成代码）
- **关键要点**：确保生成的 Coding Prompt 准确反映设计风格
- **简单示例**：
  ```bash
  # 用户：分析这个网页，然后用提取的设计规范创建一个 Hero Section
  # 智能体：
  # 1. 调用脚本分析图片
  # 2. 展示结果
  # 3. 使用生成的 Coding Prompt 指导代码生成
  ```

### 示例 3：导出为路演视频风格
- **功能说明**：将网页设计转换为路演视频可用的品牌风格配置
- **执行方式**：混合（脚本分析 → 转换脚本 → 导出配置）
- **关键参数**：设计系统 JSON 路径
- **简单示例**：
  ```bash
  # 用户：分析这个网页，然后导出为路演视频风格
  # 智能体：
  # 1. 调用 analyze_design.py 分析图片，生成 design_system.json
  # 2. 调用 convert_to_roadshow_style.py 转换，生成 brand_style.json
  # 3. 提示用户可以将 brand_style.json 用于路演视频生成
  ```
  # 1. 调用脚本分析图片
  # 2. 展示结果
  # 3. 使用生成的 Coding Prompt 指导代码生成
  ```
