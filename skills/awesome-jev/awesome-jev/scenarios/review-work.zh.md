<!-- Generated from data/scenarios.json + data/projects.json. -->
[← 返回检索入口](../README.zh-CN.md#discovery)

# 审查代码与检查产出

在采纳或放行结果前，增加明确条件下的检查。

**JEV 在哪一步**

候选产出与检查标准 → JEV 判断 → 程序标记、拦截或转交复核

## 可以参考的项目

### [Jev Review](https://github.com/devagrawal09/jev-review)

分阶段检查 Git diff 或整个代码库，在本地面板里展示可复核的审查线索。

**值得参考什么:** 参考如何分阶段判断证据、问题机制与严重程度。

[源码证据](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L38)

### [Supercov](https://github.com/supercorp-ai/supercov)

使用 JEV 做有限质量检查的代码质量与覆盖率工具。

**值得参考什么:** 参考按质量标准检查生成测试与覆盖率变化。

[源码证据](https://github.com/supercorp-ai/supercov/blob/55f5ce93a239829c224b89e6749991310be91ea4/crates/supercov-cli/src/quality.rs)

### [Agentgateway · JEV Guardrail](https://github.com/agentgateway/agentgateway)

用 JEV Webhook 检查模型请求与响应的 Guardrail 示例。

**值得参考什么:** 参考请求和响应风险评分，以及网关策略如何消费结果。

[源码证据](https://github.com/agentgateway/agentgateway/blob/6b0270efd25b5255932943e48b5ca47583d3ad28/examples/llm-guardrail-jev/guardrail.ts)

这些项目分别展示该模式的一部分，并非一套开箱即用的完整应用。源码核对不代表运行、性能或 BeatAPI 接入兼容性已经验证。

[试用免费 JEV API](https://docs.beatapi.io/decisions#free-calls) · [用 Agent 搜索](../docs/agent-search.zh.md)
