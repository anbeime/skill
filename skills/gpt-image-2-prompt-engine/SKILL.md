---
name: gpt-image-2-prompt-engine
description: 面向电商设计师、海报美工、品牌视觉、UI设计师、信息图编辑、商业摄影师、内容创作者等需要高质量可控出图的角色，在需要用 GPT-Image-2 生成电商主图、电影海报、信息图、品牌视觉、UI截图、古籍国风、角色IP等场景时，通过「Prompt as Code」原子化Schema+20+工业JSON模板+四步工作流，产出结构化、可复用、可批量的生图提示词，再调用 image_generation 出图。不适用于随意生图或简单风景照。
version: 1.0.0
author: anbeime
tags:
  - gpt-image-2
  - prompt-engineering
  - image-generation
  - 提示词工程
  - 电商设计
  - 海报
  - 信息图
  - 品牌视觉
license: MIT
---

# GPT-Image-2 Prompt Engine

> 基于 [freestylefly/awesome-gpt-image-2](https://github.com/freestylefly/awesome-gpt-image-2)（⭐18k+，MIT）工业级提示词引擎方法论，沉淀为可执行的生图提示词构造工作流。

## 任务目标

- 本技能用于：将模糊的出图需求转化为 GPT-Image-2 可稳定执行的结构化提示词
- 能力包含：
  1. **原子化 Schema 拆解**：Subject / Composition / Material / Typography / Lighting / Style / Constraints 七大维度
  2. **20+ 工业级 JSON 模板**：覆盖 UI截图、信息图、海报、电商主图、品牌视觉、商业摄影、角色IP、古籍国风、叙事插画等场景
  3. **四步工作流**：选类别 → 检索案例（抄结构）→ 套模板填变量 → 生成与图生图迭代
  4. **5 个稳定性实测技巧**：文字锁定、比例前置、模块限量、平台特征区分、负向约束
- 触发条件：
  - ✅ 电商主图/详情页、电影/活动海报、信息图/知识图谱、品牌视觉、UI截图、商业摄影、角色/IP设计、叙事插画、古籍国风、3D渲染
  - ❌ 随意生图、简单风景照、不需要精确控制的随手画 → 走基础 image_generation

## 核心方法论：Prompt as Code

### 万能结构公式

```
[主体与任务] + [构图与布局] + [视觉风格与材质] + [文字与标签要求] + [比例与输出格式] + [约束与负向细节]
```

### 原子化 Schema

| 维度 | 字段 | 说明 | 示例 |
|------|------|------|------|
| Subject | 主体 | 画面核心对象，越具体越好 | "一瓶30ml透明玻璃香水瓶，金色瓶盖" |
| Composition | 构图 | 布局、视角、景别 | "居中对称，45度俯拍，浅景深" |
| Material | 材质 | 物体表面质感与触感 | "磨砂玻璃，金属反光，水滴凝结" |
| Typography | 文字 | 画面中文字内容、字体、位置 | "标题'限时特惠'，粗黑体，左上角" |
| Lighting | 光线 | 光源方向、色温、氛围 | "柔和侧逆光，暖色调，丁达尔效应" |
| Style | 风格 | 整体视觉调性 | "高端商业摄影，极简白底，8K" |
| Constraints | 约束 | 负向提示与硬性限制 | "禁止乱码文字，禁止多余手指，9:16" |

## 四步工作流

### Step 1：选类别

根据用户需求匹配模板类别：

| 类别 | 模板ID | 适用场景 |
|------|--------|----------|
| UI与界面 | `ui-screenshot-system` | App截图、仪表盘、社媒截图、直播界面 |
| 图表与信息可视化 | `infographic-engine` | 解释图、技术图解、时间线、知识卡片 |
| 科学尺度图 | `scientific-scale-diagram` | 微观到宏观的尺度递进图 |
| 海报与排版 | `poster-campaign` | 活动海报、电影海报、概念字体海报 |
| 电商主图 | `ecommerce-hero` | 产品主图、详情页banner、带货图 |
| 品牌视觉 | `brand-identity` | 品牌KV、VI应用、包装设计 |
| 商业摄影 | `commercial-photo` | 产品静物、人像、美食摄影 |
| 角色与IP | `character-design` | 角色设定、IP形象、表情包 |
| 叙事插画 | `narrative-illustration` | 故事场景、绘本、编辑插画 |
| 古籍国风 | `classical-chinese` | 国画、工笔、水墨、敦煌风格 |

### Step 2：检索案例（抄结构）

使用 `scripts/query_templates.py` 检索本地克隆仓库的模板与案例：

```bash
python3 scripts/query_templates.py --category ecommerce
python3 scripts/query_templates.py --keyword "香水 海报"
```

未克隆仓库时，脚本会优雅降级，输出在线 raw 链接：
- 模板库：https://raw.githubusercontent.com/freestylefly/awesome-gpt-image-2/main/docs/templates.md
- 画廊Part1：https://raw.githubusercontent.com/freestylefly/awesome-gpt-image-2/main/docs/gallery-part-1.md
- 画廊Part2：https://raw.githubusercontent.com/freestylefly/awesome-gpt-image-2/main/docs/gallery-part-2.md

也可直接 web_fetch 上述链接获取最新案例。

### Step 3：套模板填变量

选择匹配的 JSON 模板，将用户需求填入变量。以下为 3 个核心模板示例：

#### 模板A：信息图

```json
{
  "type": "Infographic",
  "topic": "<主题，明确具体>",
  "audience": "<目标读者>",
  "structure": {
    "title_area": "<主标题>",
    "layout": "<布局描述，如：等距切角，N个编号面板>",
    "modules": [
      {"title": "<模块1>", "icon": "<图标名>", "text": "<1-2句说明>"},
      {"title": "<模块2>", "icon": "<图标名>", "text": "<1-2句说明>"}
    ]
  },
  "style": {
    "aesthetic": "<风格，如：科学图鉴/扁平插画/商务报告>",
    "colors": "<配色方案>",
    "background": "<背景>"
  },
  "constraints": "No gibberish text, strict structural layout, <比例>"
}
```

#### 模板B：电影/活动海报

```json
{
  "type": "Poster",
  "subject": "<主体描述>",
  "title": {
    "text": "<标题，必须精确显示>",
    "style": "<字体风格，如：粗黑体/书法体/衬线体>",
    "position": "<位置，如：居中/底部/对角>"
  },
  "composition": "<构图描述>",
  "visual_style": "<视觉风格，如：赛博朋克/复古胶片/极简>",
  "color_palette": ["<主色>", "<辅色>", "<点缀色>"],
  "mood": "<情绪关键词>",
  "constraints": "Title must be spelled exactly, readable text, <比例>, no random text"
}
```

#### 模板C：电商主图

```json
{
  "type": "Ecommerce",
  "product": {
    "name": "<产品名>",
    "material": "<材质>",
    "color": "<颜色>",
    "key_feature": "<核心卖点>"
  },
  "scene": "<使用场景/背景>",
  "composition": "<构图，如：居中45度俯拍>",
  "lighting": "<光线描述>",
  "style": "<风格，如：高端商业摄影/极简白底/生活方式>",
  "text_overlay": {
    "headline": "<主文案>",
    "subtext": "<副文案>",
    "position": "<位置>"
  },
  "constraints": "Product must be accurate, readable text, <比例>, no watermark"
}
```

### Step 4：生成与迭代

1. 将填好变量的 JSON 转为自然语言提示词
2. 调用 `image_generation` 出图（中文需求用中文提示词，英文需求用英文）
3. 检查出图结果：文字是否准确、构图是否符合、比例是否正确
4. 不满足则调整对应 Schema 维度后重新生成（图生图模式可传入参考图）

## 5 个稳定性实测技巧

1. **文字锁定**：凡是画面中有文字，必须写"文字必须准确显示指定内容，禁止乱码和占位文本"，并把原文逐字写出
2. **比例前置**：宽高比写在提示词最前面或 constraints 第一条，否则模型默认出 1:1 或 9:16
3. **模块限量**：信息图先锁定 3-5 个模块再补细节，模块过多必然混乱
4. **平台特征区分**：UI截图必须指定平台（iOS/Android/小红书/抖音），各平台状态栏、Tab、交互元素差异大
5. **负向约束具体化**：不要只写"no artifacts"，要写"禁止多余手指""禁止乱码按钮""禁止产品变形"

## 使用方式

### 输入

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| category | string | 是 | 出图类别：ui/infographic/poster/ecommerce/brand/photo/character/narrative/classical |
| subject | string | 是 | 主体描述 |
| style | string | 否 | 视觉风格偏好 |
| aspect_ratio | string | 否 | 宽高比（默认 1:1） |
| text_content | string | 否 | 画面中需要显示的文字 |
| reference_image | string | 否 | 参考图路径/URL（图生图模式） |
| extra_constraints | string | 否 | 额外约束 |

### 输出

- 一份结构化的 GPT-Image-2 提示词（可直接复制使用）
- 对应的 JSON Schema（可复用/批量修改）
- 选中的模板名称和参考案例ID
- 负向约束清单

## 资源引用

- **上游项目**：[freestylefly/awesome-gpt-image-2](https://github.com/freestylefly/awesome-gpt-image-2)（⭐18k+，MIT License）
- **在线画廊**：https://gpt-image2.canghe.ai
- **npm 包**：`gpt-image-2-style-library`
- **完整模板库**：`references/style-library.md`（20+ 模板详细索引）
- **案例库**：530+ 逆向工程案例，见上游 `docs/gallery.md`

> ⚠️ 第三方案例商用授权提示：本技能引用的案例仅供学习参考，商用前请确认对应案例的授权范围。

## 注意事项

- 本技能不新增生图工具，出图仍需调用 `image_generation` 技能
- 中文需求默认输出中文提示词，英文需求输出英文提示词
- 批量生成时复用同一模板，仅变更 subject / composition / palette
- 仓库克隆被 403 拦截时，以在线 raw 链接检索为主路径
