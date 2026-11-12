---
name: data-flow-skill
description: 面向数据分析任务的一站式 Agent Skill，覆盖数据类型检测、数据理解、预处理、统计分析、可视化图表生成、正式报告和幻灯片输出。适用于课程作业、论文实验、业务分析、SEO/GEO 数据报告和可追溯数据分析工作流。
dependency:
  python:
    - pandas>=2.0.0
    - numpy>=1.24.0
    - matplotlib>=3.7.0
    - scipy>=1.10.0
  optional:
    - Node.js 与 @mermaid-js/mermaid-cli 用于 Mermaid 本地渲染
    - LaTeX 用于报告或幻灯片 PDF 编译
    - DASHSCOPE_API_KEY 用于主题示意图生成
---

# Data Flow Skill

## 任务目标

本 Skill 用于将用户提供的数据集转化为可追溯的数据分析产物，覆盖“数据类型检测 → 数据理解 → 预处理 → 统计分析 → 可视化图表 → 报告 → 幻灯片”的端到端流程。

适用场景包括：

- 课程作业或论文实验中的可复现数据分析
- CSV、Excel、JSON、文本语料等数据集的探索性分析
- 问卷、量表、时间序列和文学语料的专项分析
- SEO/GEO、内容表现、营销数据和业务指标报告
- 将分析结果整理为正式报告、PPT 或演示材料

## 触发条件

当用户提出以下需求时使用本 Skill：

- “分析这个数据集”
- “根据 CSV/Excel 生成图表和报告”
- “帮我判断数据类型并做统计分析”
- “把分析结果整理成论文/课程报告”
- “根据数据生成 PPT 或幻灯片”
- “分析 SEO/GEO 指标、Search Console 导出或业务表现数据”

如果用户需要实时网页抓取、SERP 采集、API 拉取或站点爬虫，应先使用相应的数据收集技能，再使用本 Skill 进行分析。

## 核心能力

1. **数据类型检测**：识别 `tabular_generic`、`questionnaire`、`time_series`、`literary` 四类主要数据策略。
2. **数据画像**：检查字段类型、缺失值、重复值、异常值、时间覆盖、类别分布和指标含义。
3. **透明预处理**：保留源数据，不静默修改文件，所有清洗动作写入日志。
4. **分任务分析**：将数据处理、统计分析、图表生成和发现提炼拆成可检查的小任务。
5. **可视化生成**：根据问题选择趋势、分布、比较、关系、构成和异常类图表。
6. **结构化发现**：为每条发现记录证据、来源、限制、置信度和建议动作。
7. **报告与幻灯片**：从结构化产物生成正式报告和 slide-ready 输出。

## 标准工作流

### 1. 确认任务上下文

先确认以下信息：

- 数据文件或目录路径
- 分析目标和要回答的问题
- 受众：课程、论文、业务汇报、SEO 团队或管理层
- 交付形式：探索性分析、图表包、正式报告、PPT 或全部产物
- 语言、风格和格式要求
- 是否允许自动预处理、是否有字段含义或指标公式说明

### 2. 检测数据类型

对输入数据进行策略识别，并将结果写入：

```text
output/artifacts/dataset_detection.json
```

检测结果应包含：

- `strategy`：主策略
- `confidence`：置信度
- `evidence`：判断依据
- `alternatives`：备选策略
- `assumptions`：假设
- `fallback_plan`：回退方案

### 3. 制定并确认计划

正式分析前生成 `plan.md`，内容包括：

- 分析目标
- 数据摘要
- 数据类型策略
- 开放问题和假设
- 预处理规则
- 分析任务拆分
- 可视化计划
- 预期输出
- 风险与校验点

在用户确认计划前，不进入正式分析、报告生成或幻灯片生成。

### 4. 数据理解与画像

读取数据后生成：

```text
output/artifacts/data_profile.json
```

至少检查：

- 文件类型、编码和解析问题
- 行数、列数、字段类型
- 缺失值、重复值、异常值
- 数值范围和类别分布
- 时间字段、时间粒度和覆盖范围
- 指标定义、单位和方向

### 5. 透明预处理

不得直接覆盖原始数据。所有预处理动作写入：

```text
output/artifacts/preprocessing_log.json
```

常见动作包括：

- 字段名标准化
- 日期解析
- 数值格式转换
- 缺失值处理
- 重复记录处理
- 类别归一化
- 派生指标计算

### 6. 分策略分析

- `tabular_generic`：描述统计、分组比较、相关性、异常点、业务含义。
- `questionnaire`：量表方向、选项分布、组间差异、开放题归纳、信度检查。
- `time_series`：趋势、季节性、峰值、下降点、同比/环比、异常时段。
- `literary`：篇章结构、人物/地点/主题、词频、共现关系、情绪和风格特征。

### 7. 可视化规划与生成

先写入：

```text
output/artifacts/visualization_plan.json
```

每张图需要说明：

- 图表标题
- 回答的问题
- 输入数据
- 变量和筛选条件
- 图表类型
- 选择原因
- 输出路径
- 解读要点

图表输出到：

```text
output/figures/
```

### 8. 生成结构化发现

将结论写入：

```text
output/artifacts/analysis_findings.json
```

每条发现应包含：

- 结论 claim
- 证据 evidence
- 来源图表或表格路径
- 适用范围 scope
- 限制 limitation
- 置信度 confidence
- 建议动作 recommendation

### 9. 生成报告和幻灯片

报告应基于结构化产物，而不是重新从原始数据开始分析。建议报告结构：

- 执行摘要
- 数据来源与质量说明
- 方法与预处理说明
- 关键指标与趋势
- 分组/策略分析
- 图表证据
- 结论与建议
- 局限性和附录

幻灯片应基于 `analysis_findings.json` 和 `report_context.json`，围绕受众、演示目标、叙事主线和关键图表组织。

## 输出目录约定

推荐输出结构：

```text
output/
  figures/
  tables/
  report/
  slides/
  artifacts/
    dataset_detection.json
    data_profile.json
    preprocessing_log.json
    visualization_plan.json
    analysis_findings.json
    report_context.json
```

## 质量检查

交付前确认：

- 数据类型已检测并记录
- `plan.md` 已经用户确认
- 字段含义、时间窗口和指标方向已明确或列为假设
- 源数据未被静默修改
- 预处理动作已记录
- 分析任务已拆分
- 图表有明确问题和解读
- 发现包含证据、限制和置信度
- 报告和幻灯片基于结构化产物
- 结论没有超出数据证据

## 资源索引

- 工作流说明：见 [references/workflow.md](references/workflow.md)
- 数据类型策略：见 [references/data-types.md](references/data-types.md)
- 可视化规范：见 [references/visualization.md](references/visualization.md)
- 报告生成规范：见 [references/reporting.md](references/reporting.md)
- 幻灯片生成规范：见 [references/slides.md](references/slides.md)
- 质量校验清单：见 [references/validation.md](references/validation.md)

## 使用示例

用户请求：

```text
请分析这个 Google Search Console 导出的 CSV，并生成 SEO 表现报告和几张关键图表。
```

执行摘要：

1. 确认文件路径、日期范围、站点、受众和报告格式。
2. 检测数据类型为 `tabular_generic` 或 `time_series`。
3. 创建 `plan.md` 并等待确认。
4. 分析 query、page、country、device、clicks、impressions、CTR 和 average position。
5. 检查缺失值、时间覆盖、重复记录和分组覆盖。
6. 生成趋势图、页面贡献图、查询机会图和设备/国家对比图。
7. 保存结构化发现并生成正式报告。

## 注意事项

- 不要把描述性相关关系写成因果结论。
- 不要在未说明的情况下修改源数据。
- 不要用一个脚本完成读取、清洗、分析、绘图和报告的所有步骤。
- 不要堆叠图表而不写解释。
- 对 SEO/GEO 数据，应区分“数据观察”“可能解释”“优化建议”和“需要额外爬取/审计验证的事项”。
