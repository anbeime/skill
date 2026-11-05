<!-- Generated from data/scenarios.json + data/projects.json. -->
[← Back to discovery](../README.md#discovery)

# Automate browser & desktop actions

Select the next interface action while code executes it.

**Where JEV fits**

Observed interface + legal actions → JEV selects target/action → executor acts

## Projects to learn from

### [Jev Ultrafast](https://github.com/browser-use/jev-ultrafast)

A browser agent that uses JEV to choose an action and matching DOM element, calling a text model only when input text is needed.

**What to reference:** Selecting an action and DOM target together; text generation stays separate.

[Source](https://github.com/browser-use/jev-ultrafast/blob/1231850a0bf1a0c0341fe408ef1668dbbfdfac46/jev_ultrafast/model.py)

### [Cua · JEV Use](https://github.com/trycua/cua)

A computer-use example pairing Cua Driver observation and execution with bounded JEV choices.

**What to reference:** Connecting interface observations to bounded action IDs.

[Source](https://github.com/trycua/cua/blob/83f142c4290a0f7d9ed545ae8532858c6e4f8145/libs/cua-driver/examples/jev-use/python/jev_adapter.py#L11)

### [Agent Desktop · JEV Skill](https://github.com/lahfir/agent-desktop)

An optional JEV skill that chooses native desktop controls and actions from accessibility data.

**What to reference:** Choosing native controls from accessibility data.

[Source](https://github.com/lahfir/agent-desktop/blob/7a8e4a10281c7319733aa200fd79501f34529716/scripts/jev/act.mjs)

These projects illustrate parts of this pattern, not a single ready-made application. Source review does not establish runtime behavior, performance, or BeatAPI compatibility.

[Try the free JEV API](https://docs.beatapi.io/decisions#free-calls) · [Search with your agent](../docs/agent-search.en.md)
