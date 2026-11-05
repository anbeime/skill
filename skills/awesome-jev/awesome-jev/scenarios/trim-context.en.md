<!-- Generated from data/scenarios.json + data/projects.json. -->
[← Back to discovery](../README.md#discovery)

# Trim agent history & tool output

Keep useful context within a limited budget.

**Where JEV fits**

History or output slices → JEV retention judgment → code keeps, truncates or drops

## Projects to learn from

### [Fast Jev Compaction](https://github.com/tamaratran/fast-jev-compaction)

Compacts Claude Code tool history while keeping retained text verbatim.

**What to reference:** Preserving useful tool history without rewriting retained text.

[Source](https://github.com/tamaratran/fast-jev-compaction/blob/e3f262a7f4d42bd8dd32ced30d26176f7cb545b0/src/client.ts)

### [JEV Pruner](https://github.com/tamaratran/jev-pruner)

A Claude Code plugin that trims long Bash output with TypeSafe JEV before the model sees it.

**What to reference:** Trimming long Bash output before it reaches the model.

[Source](https://github.com/tamaratran/jev-pruner/blob/47d017c34eab7690b95f075ce6f4839247c5dc0a/src/jev.ts)

### [Save Token JEV Clean](https://github.com/IAmUnbounded/save-token-jev-clean)

A context cleaner that asks JEV which history to retain, truncate, or drop.

**What to reference:** Applying retention scores to conversation history.

[Source](https://github.com/IAmUnbounded/save-token-jev-clean/blob/a7007354a8d3747f06ff82130561edb2822a17df/src/client.ts)

These projects illustrate parts of this pattern, not a single ready-made application. Source review does not establish runtime behavior, performance, or BeatAPI compatibility.

[Try the free JEV API](https://docs.beatapi.io/decisions#free-calls) · [Search with your agent](../docs/agent-search.en.md)
