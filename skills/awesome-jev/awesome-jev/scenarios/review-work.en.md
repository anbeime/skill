<!-- Generated from data/scenarios.json + data/projects.json. -->
[← Back to discovery](../README.md#discovery)

# Review code & check outputs

Add bounded checks before accepting or passing on a result.

**Where JEV fits**

Candidate output + criteria → JEV judgment → code flags, blocks or requests review

## Projects to learn from

### [Jev Review](https://github.com/devagrawal09/jev-review)

Reviews a Git diff or a codebase in stages and displays review leads in a local dashboard.

**What to reference:** Staged decisions about evidence, issue mechanism and severity.

[Source](https://github.com/devagrawal09/jev-review/blob/31f89602797fb7bea007f8a480bf368bf564954e/src/review/judgments.ts#L38)

### [Supercov](https://github.com/supercorp-ai/supercov)

A code-quality and coverage tool that uses JEV for bounded quality checks.

**What to reference:** Checking tests and coverage changes against quality criteria.

[Source](https://github.com/supercorp-ai/supercov/blob/55f5ce93a239829c224b89e6749991310be91ea4/crates/supercov-cli/src/quality.rs)

### [Agentgateway · JEV Guardrail](https://github.com/agentgateway/agentgateway)

A JEV webhook guardrail example for inspecting model requests and responses.

**What to reference:** Scoring request/response risks before gateway policy decides.

[Source](https://github.com/agentgateway/agentgateway/blob/6b0270efd25b5255932943e48b5ca47583d3ad28/examples/llm-guardrail-jev/guardrail.ts)

These projects illustrate parts of this pattern, not a single ready-made application. Source review does not establish runtime behavior, performance, or BeatAPI compatibility.

[Try the free JEV API](https://docs.beatapi.io/decisions#free-calls) · [Search with your agent](../docs/agent-search.en.md)
