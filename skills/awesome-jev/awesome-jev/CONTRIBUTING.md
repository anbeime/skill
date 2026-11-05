# Contributing

Submit additions through a pull request. Every project must include:

- the original repository URL;
- the original X case or another primary discovery source;
- a permalink to the exact file and commit that shows the Jev integration;
- a plain-language description of the bounded decision Jev makes;
- the local policy or execution step that consumes the result;
- license and language metadata when they can be verified.

We do not accept promotional pages without inspectable source evidence, duplicate
projects, or claims that turn source review into runtime, safety, performance, or
commercial validation.

## Discovery and generated pages

- `data/projects.json` remains the project source of truth. Keep the existing ten
  project categories; scenario membership is a separate, many-to-many index.
- Edit `data/scenarios.json` to curate scenarios. Each reference uses an existing
  `projectId` and explains **what to learn from that implementation**, in English,
  Chinese and Japanese. A category match alone is not sufficient evidence.
- Prefer a small, useful selection per scenario. Do not imply a partial module is
  a complete application; do not claim runtime or BeatAPI compatibility testing
  from source inspection alone.
- Run `npm run catalog:readmes` to regenerate the README navigation, complete
  project lists and all scenario pages. Do not edit generated scenario pages.
  The existing featured gallery is preserved by the generator.
- Run `npm test`. Check local links, scenario references and repeatable generation
  before submitting. Project removals must also update scenario references.
- `skills/awesome-jev/SKILL.md` is the installable discovery skill. It reads current
  public data rather than bundling a second catalogue. Keep installation and
  usage instructions under `docs/agent-search.{en,zh,ja}.md` consistent.

The catalogue is a source-reviewed reading guide, not a promise of compatibility,
performance, safety or production readiness. No key is required to search it.
