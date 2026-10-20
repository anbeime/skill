---
name: provenance
description: 收集系统全链路操作日志，生成可追溯的执行证据链与向量索引，是多智能体系统可观测性与安全审计的底座。
assign_when: 该 Worker 负责记录每一次分发、扫描、解析与卡片生成事件，为系统提供端到端留痕与可观测能力。
---

# Provenance 留痕 Skill（太史阁）

## 使用方式
- 由各官署在关键操作节点调用（或通过事件总线异步推送），写入证据链。
- 提供按 `trace_id` / 时间窗 / 官署维度的检索接口，支撑审计面板与回滚定位。

## 输入（Input）
- `event`：操作事件，含 `actor`（官署名）、`action`、`target`、`timestamp`、`trace_id`
- `payload`：（可选）与事件关联的结构化产物引用

## 输出（Output）
- `evidence_chain`：按 trace_id 串联的可追溯证据链
- `vector_index`：用于语义检索的向量索引条目
- `query_api`：按条件检索历史证据的接口描述

## 依赖（Dependencies）
- Qdrant（向量存储，经 MCP 接入）
- SQLite（结构化事件落地，本地兜底）
- 各官署的事件上报协议（统一 schema）

## 失败处理（Failure Handling）
- 向量库写入失败 → 本地 SQLite 缓存事件，恢复后异步补写，不阻塞主流程。
- 单条事件 schema 非法 → 记录并丢弃该条，不影响整链写入。
- 检索超时 → 返回最近一次成功快照并标注 `stale`。

## 复用价值（Reuse Value）
- 可观测性底座：任何多 Agent 系统都能直接挂载，获得开箱即用的审计与回放能力。
- 契合评审：Agent Infra 赛道「工程落地与运行验证及安全审计（20%）」维度的天然得分点。

## 复赛代码包执行（runnable package）
- 真实入口：`scripts/run_provenance.py`
- 执行等价于 `core.runtime.AgentSession.run_stage("provenance")`，调用 `memory.taishige.TaiShiGeAgent.writeback`（把全链路事件与四色卡片回流证据链，纯 Python 可离线）。
- 运行：`python skills/provenance/scripts/run_provenance.py`
- 产物：`examples/snse_survey/provenance/`（trace.jsonl + trace_summary.json，含每一条军机处派发与官署执行事件）。
