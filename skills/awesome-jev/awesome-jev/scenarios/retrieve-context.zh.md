<!-- Generated from data/scenarios.json + data/projects.json. -->
[← 返回检索入口](../README.zh-CN.md#discovery)

# 找到相关文档与记忆

从已经召回的候选中，选出更值得交给 Agent 的内容。

**JEV 在哪一步**

召回候选 → JEV 相关性评分 → 本地重排与回退

## 可以参考的项目

### [OpenViking · JEV Rerank](https://github.com/volcengine/OpenViking)

OpenViking 可用 JEV 对 Agent 记忆与上下文检索结果做校准重排。

**值得参考什么:** 参考逐文档相关性判断，以及失败时回退向量分数。

[源码证据](https://github.com/volcengine/OpenViking/blob/b8bed5a1ad3a1c524b5e1fd0fa591df51ca9b7cc/openviking/models/rerank/jev_rerank.py)

### [Hindsight · TypeSafe Rerank](https://github.com/vectorize-io/hindsight)

在 Agent 记忆系统中加入 TypeSafe 重排器，可剔除无关召回候选。

**值得参考什么:** 参考记忆召回中的评分与候选剔除。

[源码证据](https://github.com/vectorize-io/hindsight/blob/680406b3dd9cca2108c7f0e204820a09b4e30906/hindsight-api-slim/hindsight_api/engine/cross_encoder.py)

### [Hippo Memory · JEV Reranker](https://github.com/kitfunso/hippo-memory)

本地优先的 Agent Memory 类库，可选用 JEV 对召回记忆重新排序。

**值得参考什么:** 参考批量判断召回记忆，以及本地排序回退。

[源码证据](https://github.com/kitfunso/hippo-memory/blob/c9eb2c31cd307cdae78c05e1fcb3e6d062efd5c0/src/rerankers/jev.ts)

这些项目分别展示该模式的一部分，并非一套开箱即用的完整应用。源码核对不代表运行、性能或 BeatAPI 接入兼容性已经验证。

[试用免费 JEV API](https://docs.beatapi.io/decisions#free-calls) · [用 Agent 搜索](../docs/agent-search.zh.md)
