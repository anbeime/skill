---
name: doc-parse
description: 将 PDF/PPT/Excel/Word 等多格式文档解析为结构化 Markdown，并输出元数据与解析置信度，作为 RAG 与四色卡片的数据底座。
assign_when: 该 Worker 负责把任意格式的原始文档转成机器可读的结构化文本，是下游信息抽取与检索的通用解析入口。
---

# 多格式文档解析 Skill（密卷房）

## 使用方式
- 由密卷房 Worker 在收到已通过安全扫描的文件时调用。
- 三级 fallback 依次尝试，输出最终结构化结果与置信度。

## 输入（Input）
- `file_path`：已通过 security-scan 的本地文件路径
- `formats`：（可选）期望支持的格式白名单，默认全格式

## 输出（Output）
- `markdown`：结构化 Markdown 正文
- `metadata`：标题、页数、表格数、作者等元数据
- `confidence`：0–1 解析置信度
- `fallback_used`：最终生效的解析器名称

## 依赖（Dependencies）
- MinerU（首选，强排版还原）
- PyMuPDF（次选，PDF 快速解析）
- pdfplumber（兜底，表格/文本抽取）
- `python-magic`（类型探测）

## 失败处理（Failure Handling）
- 主解析器失败 → 自动降级到下一档，直到全部尝试。
- 三级全部失败 → 标记 `人工介入`，不输出残缺结果，回传 BLOCKED 给军机处。
- 单页超大文件 → 分块解析后拼接，避免内存溢出；块级失败仅标记该块低置信度。

## 复用价值（Reuse Value）
- 通用解析底座：RAG 索引、企业知识库、合同结构化均可直接复用。
- 置信度透明：下游（通政司四色卡片）可据此决定是否需要人工复核，降低幻觉风险。

## 复赛代码包执行（runnable package）
- 真实入口：`scripts/run_doc_parse.py`
- 执行等价于 `core.runtime.AgentSession.run_stage("doc-parse")`，调用 `archive.mijuanfang.MiJuanFangAgent`（三级解析 fallback，纯 Python 可离线）。
- 运行：`python skills/doc-parse/scripts/run_doc_parse.py`
- 产物：`examples/snse_survey/skill_outputs/doc_parse.json`（解析结果 + 置信度 + fallback 信息）。
