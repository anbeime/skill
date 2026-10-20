# Skill 工程体系说明（赛道一·必选项）

> 赛道一要求：Skill 是**必选项**。每个方案至少提供核心 Skill 清单，并说明：名称、用途、输入与输出、调用条件、依赖工具、失败处理机制、安全边界、复用价值、与多 Agent 协同流程的关系。
> 本体系基于 `backend/skills/` 中 15 个真实可运行 Skill 模块，下表给出核心 Skill 的完整规格，其余列入注册表。

---

## 一、核心 Skill 规格

### Skill 1 · four_color_cards（四色卡片）
- **用途**：从文本/文档中抽取结构化知识，生成事实蓝/解释绿/风险黄/行动红四色卡片。
- **输入**：`text`(string, 必填)、`source`(string, 选填)、`build_relations`(bool, 选填)
- **输出**：`cards[]`（含 card_type/card_type_cn/title/content/source/tags）、`statistics`、`relations`、`quality_assessment`
- **调用条件**：任意官署需要结构化沉淀时（通政司抽取事实、监察院抽 Gap、丞相府生成行动）
- **依赖工具**：本地 NPU 模型（Genie）可选；无 LLM 时走关键词分类降级
- **失败处理**：try/except 捕获，返回 `status=error` + 空卡片集，不阻断主链路
- **安全边界**：仅写入本地知识库，不出域；来源须已通过锦衣卫合规扫描
- **复用价值**：可被科研/客服/风控等多场景直接调用，与八署解耦
- **与协同关系**：是四色卡片上下文介质的生产者，承载八署间上下文传递

### Skill 2 · knowledge_graph（知识图谱）
- **用途**：基于卡片构建实体-关系图谱，支持稀疏语义链接与可视化
- **输入**：`cards[]`、`link_type` 枚举（cite/refute/extend/sibling）、出链上限 20
- **输出**：图谱 JSON + 可视化 SVG
- **调用条件**：太史阁需要呈现知识关联或检索增强时
- **依赖工具**：networkx（可选）/ 标准库降级
- **失败处理**：链接去重失败则跳过该边，保留节点
- **安全边界**：链接必须携带类型与权重，无类型链接不入库（AGENTS.md 链接约束）
- **复用价值**：独立于八署，可作通用 RAG/可视化底座
- **与协同关系**：太史阁的记忆与共享状态能力实现者

### Skill 3 · infographic（信息图生成）
- **用途**：将卡片/统计生成自包含 SVG 信息图
- **输入**：`data`、`template`
- **输出**：SVG/PNG 文件
- **调用条件**：丞相府/军机处需要产出展示材料时
- **依赖工具**：resvg（可选）/ 标准库 SVG 字符串
- **失败处理**：模板缺失回退默认布局
- **安全边界**：不访问外部网络取图
- **复用价值**：通用报告配图能力
- **与协同关系**：展示层，消费红/绿卡产出演示素材

### Skill 4 · html_report（HTML 报告）
- **用途**：汇编四色卡片 + provenance 为自包含 HTML 报告
- **输入**：`cards[]`、`provenance_log`
- **输出**：单文件 HTML（base64 内联资源）
- **调用条件**：军机处落盘或用户请求导出时
- **依赖工具**：无强制第三方依赖
- **失败处理**：资源内联失败则外链降级并告警
- **安全边界**：数据全部本地，不出域
- **复用价值**：可作为任意知识任务的通用报告出口
- **与协同关系**：八署产物的聚合展示端

### Skill 5 · report_automation（报告自动化）
- **用途**：端到端生成调研/分析文档
- **输入**：任务描述 + 卡片集
- **输出**：Markdown/PDF/Word
- **调用条件**：需要交付正式文档时
- **依赖工具**：python-docx / reportlab（可选，环境已有则用）
- **失败处理**：缺依赖则退回纯 Markdown
- **安全边界**：仅本地文件写出
- **复用价值**：复用至 AFAC 等其它赛事文档
- **与协同关系**：军机处产物落盘的执行者

### Skill 6 · ppt_structure_draft（PPT 结构草拟）
- **用途**：根据大纲生成 PPT 页面结构与 speaker notes
- **输入**：`outline`、`pages`
- **输出**：逐页结构 + 备注
- **调用条件**：丞相府需要产出路演材料时
- **依赖工具**：python-pptx（可选）
- **失败处理**：无 pptx 依赖则仅输出 Markdown 大纲
- **安全边界**：本地生成
- **复用价值**：通用演示稿生成
- **与协同关系**：展示层，消费八署结论

### Skill 7 · card_filter（卡片过滤）
- **用途**：按类型/标签/置信度过滤卡片集
- **输入**：`cards[]`、`filters`
- **输出**：子集
- **调用条件**：监察院做质量评估或用户检索时
- **依赖工具**：无
- **失败处理**：空过滤返回全集
- **安全边界**：只读
- **复用价值**：通用检索前置
- **与协同关系**：监察院质量门禁

### Skill 8 · chart_recommendation（图表推荐）
- **用途**：根据数据特征推荐合适图表类型
- **输入**：`data_schema`
- **输出**：图表类型 + 配置
- **调用条件**：展示层需要可视化时
- **依赖工具**：无强制
- **失败处理**：无匹配则返回表格
- **安全边界**：本地
- **复用价值**：通用可视化决策
- **与协同关系**：展示层辅助

---

## 二、Skill 注册表（其余模块）

| Skill 名称 | 归属官署 | 一句话用途 |
|-----------|---------|-----------|
| `markdown_converter` | 通政司 | Markdown ↔ 其它格式互转 |
| `markdown_formatter` | 通政司 | Markdown 规范化 |
| `local_audio_processor` | 密卷房 | 本地音频转写（可选） |
| `view_manager` | 太史阁/UI | 前端视图状态管理 |
| `book_skill` | 太史阁 | 书籍/长文档知识抽取 |
| `invoice_skill` | 扩展域 | 发票结构化（复用验证） |

> 全部 Skill 均以 `Skill` 基类抽象（`name/description/category/agent_name/parameters_schema/execute`），支持热插拔、版本与失败降级，符合赛道一"Skill 作为任务能力抽象层而非一次性行为"的要求。

---

## 三、Skill 与多 Agent 协同的关系

```
指挥使 ──调度──> [Skill: card_filter / ppt_structure_draft]
锦衣卫 ──调用──> [Skill: 密钥扫描 / OA 黑名单匹配]
密卷房 ──调用──> [Skill: local_audio_processor / markdown_converter]
通政司 ──调用──> [Skill: four_color_cards / markdown_formatter]
监察院 ──调用──> [Skill: card_filter / knowledge_graph]
丞相府 ──调用──> [Skill: ppt_structure_draft / infographic]
军机处 ──调用──> [Skill: report_automation / html_report]
太史阁 ──调用──> [Skill: knowledge_graph / view_manager]
```

Skill 是 Agent 的能力抽象层，MCP/外部工具是连接层；本方案未强制使用 MCP，但提供等价集成契约（见 AgentTeams 映射文档），后续可平滑迁移。
