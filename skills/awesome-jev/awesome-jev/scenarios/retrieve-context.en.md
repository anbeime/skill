<!-- Generated from data/scenarios.json + data/projects.json. -->
[← Back to discovery](../README.md#discovery)

# Find useful documents & memories

Improve which retrieved passages reach an agent.

**Where JEV fits**

Retrieve candidates → JEV relevance scoring → local ranking and fallback

## Projects to learn from

### [OpenViking · JEV Rerank](https://github.com/volcengine/OpenViking)

OpenViking can use JEV as a calibrated reranker for agent memory and context retrieval.

**What to reference:** Per-document relevance questions and vector-score fallback.

[Source](https://github.com/volcengine/OpenViking/blob/b8bed5a1ad3a1c524b5e1fd0fa591df51ca9b7cc/openviking/models/rerank/jev_rerank.py)

### [Hindsight · TypeSafe Rerank](https://github.com/vectorize-io/hindsight)

An agent-memory system with a TypeSafe reranker that can prune irrelevant recall candidates.

**What to reference:** Relevance scoring and pruning in memory recall.

[Source](https://github.com/vectorize-io/hindsight/blob/680406b3dd9cca2108c7f0e204820a09b4e30906/hindsight-api-slim/hindsight_api/engine/cross_encoder.py)

### [Hippo Memory · JEV Reranker](https://github.com/kitfunso/hippo-memory)

A local-first agent-memory library with an opt-in JEV reranker for recalled memories.

**What to reference:** Batched relevance judgments with a local ranking fallback.

[Source](https://github.com/kitfunso/hippo-memory/blob/c9eb2c31cd307cdae78c05e1fcb3e6d062efd5c0/src/rerankers/jev.ts)

These projects illustrate parts of this pattern, not a single ready-made application. Source review does not establish runtime behavior, performance, or BeatAPI compatibility.

[Try the free JEV API](https://docs.beatapi.io/decisions#free-calls) · [Search with your agent](../docs/agent-search.en.md)
