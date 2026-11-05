[← Awesome JEV](../README.md#discovery)

# Search with your agent

Describe your task and let your agent select useful GitHub references. This skill searches the same catalogue and scenario index as this repository; no BeatAPI account or API key is needed.

## Install

```bash
npx skills add BeatAPI/awesome-jev
```

Run in the project where you want to use the skill, then choose your agent in the installer. Requires Node.js/npm; host support follows the installer.

[Skill source](../skills/awesome-jev/SKILL.md) · [Installer documentation](https://skills.sh/docs/cli)

## Try asking

- I want to filter brand-related news. Find JEV projects and explain which part of each I should reference.
- Find Python projects for reranking agent memory. Separate direct fits from ideas that need adaptation.
- Compare JEV model-routing projects for a coding agent. Link the implementation evidence.

## What you get

A short selection with GitHub links, matching reasons, specific implementation references and evidence status. The agent reads the current public catalogue rather than a bundled frozen list. If fetching fails, it must report the limitation.

## Manual installation

Copy the `skills/awesome-jev` folder into your host’s documented skill directory. For Codex, for example, copy it into `~/.codex/skills/awesome-jev` and start a new session. This installs discovery instructions only, not the recommended projects.

## Maintainer preview

Before this change is merged, validate from a checkout with `npx skills add . --list`, then install from that checkout with `npx skills add .`. The remote command above becomes available after the skill reaches the default branch.
