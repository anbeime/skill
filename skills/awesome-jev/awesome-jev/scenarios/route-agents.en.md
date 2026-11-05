<!-- Generated from data/scenarios.json + data/projects.json. -->
[← Back to discovery](../README.md#discovery)

# Choose models, tools & agents

Choose an execution route from known options.

**Where JEV fits**

Task + available options → JEV classification → local route selection

## Projects to learn from

### [LiteLLM · JEV Router](https://github.com/BerriAI/litellm)

LiteLLM can use JEV inside its complexity-based model router.

**What to reference:** Request complexity classification before model routing.

[Source](https://github.com/BerriAI/litellm/blob/56116079c8022da0e8f7ff9ccb017ad5aca5aed2/litellm/router_strategy/complexity_router/jev_classifier.py#L70)

### [Jev Model Router](https://github.com/davila7/claude-code-templates)

A Claude Code mod that classifies subagent model and reasoning-effort needs.

**What to reference:** Mapping task classes to Claude Code model and reasoning settings.

[Source](https://github.com/davila7/claude-code-templates/blob/61bfcd1586bf1076f6d3cfa0436317c912811e6c/cli-tool/components/mods/productivity/jev-model-router/hooks/jev-model-router.ts)

### [JevRouter](https://github.com/BillionsBobby/JevRouter)

A lightweight JEV router for models, tools, and subagents.

**What to reference:** Bounded selection among models, tools and subagents.

[Source](https://github.com/BillionsBobby/JevRouter/blob/715970774ae8070e958e83ac9b1a780b32a9184c/src/provider.ts)

These projects illustrate parts of this pattern, not a single ready-made application. Source review does not establish runtime behavior, performance, or BeatAPI compatibility.

[Try the free JEV API](https://docs.beatapi.io/decisions#free-calls) · [Search with your agent](../docs/agent-search.en.md)
