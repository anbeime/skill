<!-- Generated from data/scenarios.json + data/projects.json. -->
[← 返回检索入口](../README.zh-CN.md#discovery)

# 选择模型、工具与 Agent

在已有候选中，为任务选择执行路线。

**JEV 在哪一步**

任务与可用候选 → JEV 分类判断 → 本地策略选择执行路线

## 可以参考的项目

### [LiteLLM · JEV Router](https://github.com/BerriAI/litellm)

LiteLLM 可在按复杂度路由模型的策略中使用 JEV。

**值得参考什么:** 参考先判断请求复杂度，再路由到后端模型。

[源码证据](https://github.com/BerriAI/litellm/blob/56116079c8022da0e8f7ff9ccb017ad5aca5aed2/litellm/router_strategy/complexity_router/jev_classifier.py#L70)

### [Jev Model Router](https://github.com/davila7/claude-code-templates)

为 Claude Code 判断子 Agent 模型与推理强度的 Mod。

**值得参考什么:** 参考任务类别到 Claude Code 模型、推理配置的映射。

[源码证据](https://github.com/davila7/claude-code-templates/blob/61bfcd1586bf1076f6d3cfa0436317c912811e6c/cli-tool/components/mods/productivity/jev-model-router/hooks/jev-model-router.ts)

### [JevRouter](https://github.com/BillionsBobby/JevRouter)

用于模型、工具与子 Agent 的轻量 JEV 路由器。

**值得参考什么:** 参考从模型、工具、子 Agent 候选中进行有限选择。

[源码证据](https://github.com/BillionsBobby/JevRouter/blob/715970774ae8070e958e83ac9b1a780b32a9184c/src/provider.ts)

这些项目分别展示该模式的一部分，并非一套开箱即用的完整应用。源码核对不代表运行、性能或 BeatAPI 接入兼容性已经验证。

[试用免费 JEV API](https://docs.beatapi.io/decisions#free-calls) · [用 Agent 搜索](../docs/agent-search.zh.md)
