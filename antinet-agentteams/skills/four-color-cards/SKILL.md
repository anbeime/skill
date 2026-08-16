---
name: four-color-cards
description: 基于解析后的文档与用户意图，生成四色卡片——事实蓝卡、解释绿卡、风险黄卡、行动红卡，是八官署方法论的核心分析输出。
assign_when: 该 Worker 负责把结构化文档转化为可审计的事实-解释-风险-行动卡片，并需与监察院（过度声明检测）和丞相府（行动建议）协同。
---

# 四色卡片生成 Skill（通政司 + 监察院 + 丞相府）

## 使用方式
- 由通政司 Worker 主调用，生成蓝卡（事实）/ 绿卡（解释）。
- 黄卡（风险）交由监察院复核过度声明；红卡（行动）交由丞相府补全策略建议。
- 四卡片统一经太史阁留痕，保证每张卡片可溯源。

## 输入（Input）
- `markdown`：密卷房解析产出的结构化文档
- `intent`：用户意图 / 查询目标
- `llm_available`：LLM 是否可用（影响黄卡生成路径）

## 输出（Output）
- `blue_card`：事实卡——可溯源的陈述，附来源片段
- `green_card`：解释卡——对事实的机制/背景说明
- `yellow_card`：风险卡——过度声明、不确定性与潜在偏差（经监察院复核）
- `red_card`：行动卡——下一步建议（经丞相府补全）

## 依赖（Dependencies）
- LLM API（生成蓝/绿/红卡）
- 过度声明检测规则集（监察院提供，用于黄卡）
- 解析置信度（来自 doc-parse，低置信度触发人工复核标记）

## 失败处理（Failure Handling）
- LLM 不可用 → 降级到规则引擎生成卡片，黄卡/红卡显式标注「未启用 LLM」。
- 监察院复核超时 → 黄卡暂以规则引擎结果交付，并标记 `pending_review`。
- 来源缺失 → 对应事实在蓝卡中标注「无来源」，不直接生成断言。

## 复用价值（Reuse Value）
- 方法论通用：科研分析、金融研报、法律文档分析均可套用四色卡片框架。
- 可审计性强：每张卡片带来源与生成方式，天然契合 Agent Infra 的可观测/审计评审维度。

## 复赛代码包执行（runnable package）
- 真实入口：`scripts/run_four_color_cards.py --stage {extract|review|propose}`
- 三个子任务映射：
  - `extract` → 通政司 `comm.tongzhengsi.TongZhengSiAgent`（蓝卡：事实抽取）
  - `review`  → 监察院 `audit.jichayuan.JianChaYuanAgent`（绿卡：Gap/解释）
  - `propose` → 丞相府 `strategy.chengxiangfu.ChengXiangFuAgent`（红卡：行动建议）
- 运行示例：
  - `python skills/four-color-cards/scripts/run_four_color_cards.py --stage extract`
  - `python skills/four-color-cards/scripts/run_four_color_cards.py --stage review`
  - `python skills/four-color-cards/scripts/run_four_color_cards.py --stage propose`
- 产物：`examples/snse_survey/skill_outputs/four_color_<stage>.json`
- 溯源铁律：绿卡 cite 蓝卡、红卡 cite 绿卡/蓝卡，无来源不得入库（由 card_model 强制）。
