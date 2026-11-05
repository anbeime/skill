<!-- Generated from data/scenarios.json + data/projects.json. -->
[← 返回检索入口](../README.zh-CN.md#discovery)

# 精简 Agent 历史与工具输出

在有限上下文预算里，保留更有用的信息。

**JEV 在哪一步**

历史或输出片段 → JEV 判断保留价值 → 程序保留、截断或丢弃

## 可以参考的项目

### [Fast Jev Compaction](https://github.com/tamaratran/fast-jev-compaction)

压缩 Claude Code 工具历史，同时原样保留仍有价值的内容。

**值得参考什么:** 参考保留有用工具历史，并让保留内容维持原文。

[源码证据](https://github.com/tamaratran/fast-jev-compaction/blob/e3f262a7f4d42bd8dd32ced30d26176f7cb545b0/src/client.ts)

### [JEV Pruner](https://github.com/tamaratran/jev-pruner)

Claude Code 插件：在模型看到长 Bash 输出前，用 TypeSafe JEV 裁剪。

**值得参考什么:** 参考模型读取前，如何裁剪过长的 Bash 输出。

[源码证据](https://github.com/tamaratran/jev-pruner/blob/47d017c34eab7690b95f075ce6f4839247c5dc0a/src/jev.ts)

### [Save Token JEV Clean](https://github.com/IAmUnbounded/save-token-jev-clean)

让 JEV 判断哪些历史应保留、截断或丢弃的上下文清理器。

**值得参考什么:** 参考对话条目的保留评分如何驱动清理。

[源码证据](https://github.com/IAmUnbounded/save-token-jev-clean/blob/a7007354a8d3747f06ff82130561edb2822a17df/src/client.ts)

这些项目分别展示该模式的一部分，并非一套开箱即用的完整应用。源码核对不代表运行、性能或 BeatAPI 接入兼容性已经验证。

[试用免费 JEV API](https://docs.beatapi.io/decisions#free-calls) · [用 Agent 搜索](../docs/agent-search.zh.md)
