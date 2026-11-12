# data-flow-skill

面向数据分析任务的一站式 Agent Skill，覆盖“数据类型检测 → 数据理解 → 预处理 → 统计分析 → 可视化图表生成 → 正式报告生成 → 幻灯片生成”的端到端链路。

## 适用场景

- 课程作业/论文实验的可复现分析管线
- CSV、Excel、JSON、文本语料等数据集的探索性分析
- 问卷、量表、时间序列、文学语料等专项分析
- SEO/GEO、内容表现、营销数据和业务指标报告
- 报告与幻灯片的结构化生成

## 核心特性

- 数据类型检测与策略分派：`tabular_generic`、`questionnaire`、`time_series`、`literary`
- 结构化产物契约：检测、画像、预处理日志、图表计划、分析发现和报告上下文
- 可视化规划：围绕问题选择趋势、分布、比较、关系、构成和异常类图表
- 报告与幻灯片生成：从结构化发现中组织正式报告和演示材料
- 质量约束：子任务拆分、源数据保护、预处理留痕、结论证据化
- Python 脚本支持：`scripts/analysis/`、`scripts/visualization/`、`scripts/mermaid/`、`scripts/image_gen/`

## 脚本与依赖

可复用脚本已迁移到 `scripts/` 目录。运行前建议安装依赖：

```bash
pip install -r requirements.txt
```

详细说明见 `scripts/README.md`。

## 推荐输出结构

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

## 使用方式

在 Agent 环境中，当用户提供数据文件并要求分析、绘图、报告或幻灯片时，调用本 Skill。正式分析前应先生成 `plan.md` 并等待用户确认。

详细流程见 `SKILL.md` 与 `references/` 目录。