# PPT 结构规范与数据格式

## 目录
1. JSON 数据格式定义
2. 幻灯片布局类型
3. 布局推荐指南（新增）
4. 内容编写规范
5. 完整示例
6. 验证规则

## 概览
本文档定义了 `generate_pptx.py` 脚本所需的 JSON 输入格式。所有 PPT 内容必须按照此规范组织，确保脚本能够正确解析并生成 .pptx 文件。

## JSON 数据格式定义

### 根对象结构
```json
{
  "metadata": {
    "title": "演示文稿标题",
    "author": "作者姓名",
    "subject": "主题描述",
    "keywords": "关键词1,关键词2,关键词3"
  },
  "slides": [
    {
      "layout": "TitleSlide",
      "title": "封面标题",
      "content": ["副标题或描述"],
      "notes": "演讲者备注"
    },
    ...
  ]
}
```

### 字段说明

#### metadata（必需）
- `title`：演示文稿标题（字符串）
- `author`：作者姓名（字符串，可选）
- `subject`：主题描述（字符串，可选）
- `keywords`：关键词，逗号分隔（字符串，可选）

#### slides（必需）
幻灯片对象数组，每个幻灯片包含以下字段：
- `layout`：布局类型（字符串，必需），见"幻灯片布局类型"
- `title`：幻灯片标题（字符串，必需）
- `content`：内容列表（字符串数组，必需），每个元素代表一行或一个要点
- `notes`：演讲者备注（字符串，可选）

## 幻灯片布局类型

### TitleSlide（标题页）
- 用途：封面页
- 结构：大标题 + 副标题/描述
- 示例：
```json
{
  "layout": "TitleSlide",
  "title": "产品发布演示",
  "content": ["2024年第一季度新产品发布会"]
}
```

### TitleAndContent（标题和内容）
- 用途：普通内容页，最常见的布局
- 结构：标题 + 标题区 + 内容区
- 示例：
```json
{
  "layout": "TitleAndContent",
  "title": "市场分析",
  "content": [
    "市场规模：2023年达到100亿美元",
    "年增长率：15%",
    "主要驱动力：数字化转型"
  ]
}
```

### TwoColumnText（双栏文本）
- 用途：对比展示或并列内容
- 结构：标题 + 左栏内容 + 右栏内容
- 示例：
```json
{
  "layout": "TwoColumnText",
  "title": "产品对比",
  "content": [
    "【产品A】",
    "价格：$99",
    "功能：基础版",
    "【产品B】",
    "价格：$199",
    "功能：高级版"
  ]
}
```

### SectionHeader（章节标题页）
- 用途：新章节开始前的过渡页
- 结构：章节标题 + 描述
- 示例：
```json
{
  "layout": "SectionHeader",
  "title": "第二部分：产品介绍",
  "content": ["核心功能与特性"]
}
```

### ContentWithCaption（带说明的内容）
- 用途：需要详细说明的内容页
- 结构：标题 + 内容区 + 说明区
- 示例：
```json
{
  "layout": "ContentWithCaption",
  "title": "技术架构",
  "content": ["微服务架构", "云原生部署", "容器化"],
  "caption": "基于 Kubernetes 的分布式架构"
}
```

### BulletList（项目符号列表）
- 用途：列举多个要点
- 结构：标题 + 项目符号列表
- 示例：
```json
{
  "layout": "BulletList",
  "title": "核心优势",
  "content": [
    "高可用性：99.99% SLA",
    "低成本：节省30%运营成本",
    "快速部署：5分钟上线",
    "易于扩展：支持横向扩展"
  ]
}
```

### BlankSlide（空白页）
- 用途：自定义布局或完全空白
- 结构：标题（可选）+ 自由内容
- 示例：
```json
{
  "layout": "BlankSlide",
  "title": "谢谢",
  "content": []
}
```

## 布局推荐指南

本指南根据不同场景和内容类型，推荐合适的布局类型，帮助模板设计师和内容策划师做出最佳选择。

### 商务场景（专业汇报）

| 页面类型 | 推荐布局 | 适用情况 | 示例 |
|---------|---------|---------|------|
| 封面页 | TitleSlide | 演示文稿开场 | 公司介绍、项目启动、年度总结 |
| 目录页 | BulletList | 展示整体结构 | 章节目录、议程安排 |
| 内容页 | TitleAndContent | 核心信息展示 | 市场分析、产品介绍、业务规划 |
| 对比页 | TwoColumnText | 左右对比 | 产品对比、方案选择、优劣势分析 |
| 章节页 | SectionHeader | 新章节过渡 | 主题切换、重点强调 |
| 结束页 | BlankSlide | 感谢和联系方式 | 谢谢、Q&A、联系方式 |

**特点**：
- 布局简洁专业
- 信息层次清晰
- 适合数据和图表展示

### 创意场景（营销、设计、艺术）

| 页面类型 | 推荐布局 | 适用情况 | 示例 |
|---------|---------|---------|------|
| 封面页 | TitleSlide | 视觉冲击力强的开场 | 产品发布、品牌宣传 |
| 内容页 | ContentWithCaption | 图片+文字组合 | 案例展示、创意说明 |
| 列表页 | BulletList | 多个创意点展示 | 创意清单、灵感来源 |
| 对比页 | TwoColumnText | 创意方案对比 | A/B测试、方案对比 |
| 章节页 | SectionHeader | 主题切换 | 新创意主题开始 |

**特点**：
- 注重视觉表现
- 布局灵活多变
- 强调图片和视觉元素

### 教育培训场景

| 页面类型 | 推荐布局 | 适用情况 | 示例 |
|---------|---------|---------|------|
| 封面页 | TitleSlide | 课程开场 | 课程介绍、培训主题 |
| 目录页 | BulletList | 课程大纲 | 课程结构、章节安排 |
| 概念页 | TitleAndContent | 核心概念讲解 | 理论知识、定义说明 |
| 列表页 | BulletList | 要点列举 | 注意事项、学习要点 |
| 对比页 | TwoColumnText | 概念对比 | 不同理论、方法对比 |
| 总结页 | ContentWithCaption | 课程总结 | 关键点回顾、课后作业 |

**特点**：
- 逻辑清晰
- 便于记录笔记
- 适合知识传递

### 学术研究场景

| 页面类型 | 推荐布局 | 适用情况 | 示例 |
|---------|---------|---------|------|
| 封面页 | TitleSlide | 研究报告开场 | 论文答辩、学术汇报 |
| 背景页 | TitleAndContent | 研究背景 | 研究动机、问题陈述 |
| 方法页 | ContentWithCaption | 研究方法 | 技术路线、实验设计 |
| 结果页 | TitleAndContent | 实验结果 | 数据展示、图表分析 |
| 对比页 | TwoColumnText | 方案对比 | 不同方法对比 |
| 结论页 | ContentWithCaption | 研究结论 | 主要发现、研究局限 |

**特点**：
- 强调数据和逻辑
- 适合复杂信息展示
- 需要清晰的层次结构

### 项目汇报场景

| 页面类型 | 推荐布局 | 适用情况 | 示例 |
|---------|---------|---------|------|
| 封面页 | TitleSlide | 项目开场 | 项目启动、阶段总结 |
| 进度页 | ContentWithCaption | 项目进展 | 时间线、里程碑 |
| 问题页 | TwoColumnText | 问题与解决方案 | 遇到的困难 vs 解决方案 |
| 数据页 | TitleAndContent | 数据展示 | KPI、关键指标 |
| 计划页 | BulletList | 未来计划 | 下一步工作、时间安排 |

**特点**：
- 时间维度清晰
- 问题-解决方案对应
- 适合阶段性汇报

### 特殊页面布局建议

#### 数据密集型页面
- **推荐布局**：ContentWithCaption 或 TitleAndContent
- **特点**：数据区+说明区分离
- **适用**：市场数据、实验结果、财务报表

#### 流程类页面
- **推荐布局**：TitleAndContent
- **特点**：使用编号或箭头标记流程步骤
- **适用**：工作流程、技术架构、实施路线

#### 图片为主页面
- **推荐布局**：ContentWithCaption
- **特点**：大图片区域+简短说明
- **适用**：产品展示、案例图解、设计稿

#### 文字密集型页面
- **推荐布局**：BulletList
- **特点**：多个要点列表展示
- **适用**：规则说明、注意事项、知识清单

#### 对比分析页面
- **推荐布局**：TwoColumnText
- **特点**：左右对比展示
- **适用**：产品对比、方案选择、优劣势分析

### 布局选择决策树

```
开始
  │
  ├─ 封面页？
  │   └─ → TitleSlide
  │
  ├─ 章节过渡？
  │   └─ → SectionHeader
  │
  ├─ 结束页？
  │   └─ → BlankSlide
  │
  ├─ 需要对比？
  │   └─ → TwoColumnText
  │
  ├─ 图片为主？
  │   └─ → ContentWithCaption
  │
  ├─ 多个要点？
  │   └─ → BulletList
  │
  └─ 普通内容
      └─ → TitleAndContent
```

### 布局组合建议

**标准 PPT 结构**：
1. TitleSlide（封面）
2. BulletList（目录）
3. SectionHeader（章节1）
4. TitleAndContent × N（章节1内容）
5. SectionHeader（章节2）
6. TitleAndContent × N（章节2内容）
7. ...
8. ContentWithCaption（总结）
9. BlankSlide（结束）

**对比型 PPT 结构**：
1. TitleSlide
2. BulletList
3. TitleAndContent（背景）
4. TwoColumnText × N（方案对比）
5. TitleAndContent（推荐方案）
6. BlankSlide

**产品发布型 PPT 结构**：
1. TitleSlide
2. SectionHeader（产品概述）
3. ContentWithCaption × N（产品特性+图片）
4. SectionHeader（功能展示）
5. TitleAndContent × N（功能介绍）
6. BulletList（价格与购买）
7. BlankSlide

## 内容编写规范

### 标题规范
- 简洁有力，不超过 20 字
- 使用主动语态
- 避免使用"关于"、"关于..."等冗余词汇
- 同一章节内标题风格保持一致

### 内容要点规范
- 每页 3-5 个要点为宜
- 每个要点不超过 20 字
- 使用平行结构，保持语法一致
- 开头使用动词或名词
- 避免完整句子，使用短语

### 双栏内容规范
- 使用特殊标记区分左右栏
  - 左栏：无标记或 `【左】`
  - 右栏：`【右】` 或使用 `|` 分隔
- 左右栏内容数量建议平衡

### 备注规范
- 提供详细的演讲提示
- 包含数据来源、背景信息
- 建议演讲时间分配

## 完整示例

### 示例 1：商业演示文稿
```json
{
  "metadata": {
    "title": "2024年度商业计划",
    "author": "张三",
    "subject": "年度商业发展计划",
    "keywords": "商业计划,战略规划,2024"
  },
  "slides": [
    {
      "layout": "TitleSlide",
      "title": "2024年度商业计划",
      "content": ["驱动创新，引领未来"]
    },
    {
      "layout": "SectionHeader",
      "title": "第一部分：市场分析",
      "content": ["机遇与挑战"]
    },
    {
      "layout": "TitleAndContent",
      "title": "市场规模",
      "content": [
        "2023年市场规模：500亿美元",
        "预计2024年增长率：20%",
        "目标市场份额：从10%提升至15%"
      ]
    },
    {
      "layout": "TwoColumnText",
      "title": "竞争对比",
      "content": [
        "【我们】",
        "产品创新能力强",
        "客户满意度高",
        "成本控制优秀",
        "【竞争对手】",
        "市场份额大",
        "品牌知名度高",
        "渠道覆盖广"
      ]
    },
    {
      "layout": "SectionHeader",
      "title": "第二部分：战略规划",
      "content": ["核心发展方向"]
    },
    {
      "layout": "BulletList",
      "title": "三大战略支柱",
      "content": [
        "产品创新：持续推出新产品",
        "市场拓展：进入新兴市场",
        "生态建设：构建合作伙伴网络"
      ]
    },
    {
      "layout": "BlankSlide",
      "title": "谢谢",
      "content": []
    }
  ]
}
```

### 示例 2：学术汇报
```json
{
  "metadata": {
    "title": "人工智能在医疗诊断中的应用研究",
    "author": "李四",
    "subject": "学术研究报告",
    "keywords": "人工智能,医疗诊断,深度学习"
  },
  "slides": [
    {
      "layout": "TitleSlide",
      "title": "人工智能在医疗诊断中的应用",
      "content": ["基于深度学习的图像识别技术研究"]
    },
    {
      "layout": "TitleAndContent",
      "title": "研究背景",
      "content": [
        "医疗资源分布不均",
        "误诊率仍然较高",
        "AI技术日趋成熟",
        "深度学习取得突破"
      ]
    },
    {
      "layout": "TitleAndContent",
      "title": "研究目标",
      "content": [
        "提高诊断准确率",
        "缩短诊断时间",
        "降低医疗成本",
        "实现辅助诊断工具"
      ]
    },
    {
      "layout": "SectionHeader",
      "title": "研究方法",
      "content": ["技术路线与实验设计"]
    },
    {
      "layout": "TitleAndContent",
      "title": "模型架构",
      "content": [
        "采用 ResNet-50 作为基础模型",
        "引入注意力机制",
        "多尺度特征融合",
        "数据增强技术"
      ]
    },
    {
      "layout": "ContentWithCaption",
      "title": "实验数据",
      "content": [
        "数据集：ChestX-ray14",
        "样本数：112,120张X光片",
        "训练集/测试集：8:2"
      ],
      "caption": "数据来源：美国国立卫生研究院"
    },
    {
      "layout": "TitleAndContent",
      "title": "实验结果",
      "content": [
        "准确率：95.3%",
        "灵敏度：94.1%",
        "特异性：96.2%",
        "对比方法：提升5.8个百分点"
      ]
    },
    {
      "layout": "BlankSlide",
      "title": "谢谢",
      "content": []
    }
  ]
}
```

## 验证规则

### 必填字段验证
- `metadata.title`：必须存在且非空
- `slides`：必须存在且至少包含 1 个幻灯片
- 每个幻灯片的 `layout`、`title`、`content`：必须存在且非空

### 布局类型验证
- `layout` 必须是以下值之一：
  - TitleSlide
  - TitleAndContent
  - TwoColumnText
  - SectionHeader
  - ContentWithCaption
  - BulletList
  - BlankSlide

### 内容格式验证
- `content` 必须是数组
- `content` 数组元素必须是字符串
- 对于 `TitleAndContent` 和 `BulletList`，`content` 建议包含 3-5 个元素
- 对于 `TwoColumnText`，应使用标记正确区分左右栏

### JSON 语法验证
- 必须是合法的 JSON 格式
- 所有字符串必须使用双引号
- 不能有尾随逗号
- 布尔值使用 true/false，非 True/False

### 数据一致性验证
- 幻灯片数量建议在 10-20 页之间
- 标题层级应逻辑清晰
- 相邻幻灯片的内容应有连贯性

## 常见问题

### Q1：如何插入图片？
A：当前版本主要通过 `notes` 字段提供图片建议，如需插入图片，请在 `content` 中标注图片位置，如 `[图片：市场增长趋势图]`。

### Q2：如何设置字体和颜色？
A：当前版本使用默认样式，如需自定义，请参考 `assets/ppt_templates/` 中的模板配置文件。

### Q3：如何调整幻灯片顺序？
A：直接调整 `slides` 数组中对象的顺序即可。

### Q4：content 数组中的元素如何换行显示？
A：每个数组元素会自动作为一个段落或要点显示，无需额外处理。

### Q5：双栏布局如何确保左右区分？
A：推荐使用以下格式之一：
- 使用 `【左】` 和 `【右】` 标记
- 使用竖线 `|` 分隔
- 确保标记清晰且对称
