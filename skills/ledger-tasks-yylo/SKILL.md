---
name: ledger-tasks-yylo
description: Drive multi-step coding-agent work through a git-native Kanban/task ledger. Use when an agent needs persistent task state across sessions, dependency-aware ordering, status transitions with receipts, or serialized multi-worktree delivery. For task/board operations, not memory or general notes.
---

# YYLO Ledger Tasks

Use this skill when a coding agent needs persistent, reviewable task state that lives in the repository and drives multi-step feature work across sessions.

## When to Use

- Planning or executing a multi-step feature that spans several sessions or agents
- Tracking a task board (backlog → todo → in_progress → done) as files inside the repo
- Ordering work by dependencies before starting parallel agents
- Recording status changes with an explicit response receipt and commit link
- Coordinating feature worktrees with serialized merge delivery

## Required Workflow

1. Read state before mutating: `yy ledger list`, `yy ledger get TASK_ID`, `yy ledger ready`.
2. Create small, one-iteration tasks: `yy ledger create "Implement X" --status todo --tags backend`.
3. Record every transition with a receipt: `yy ledger mark in_progress --id TASK_ID --response "Starting: scope Y"`.
4. Model blockers explicitly: `yy ledger deps add --id TASK_ID --blocked-by BLOCKER1 BLOCKER2`.
5. Plan parallel work topologically: `yy ledger order --scores`.
6. Link outcomes to git: mark done with `--response` plus `--commit HASH`.
7. Never edit `.juno_task/` files directly; the CLI is the only sanctioned mutation path and fails closed on controller errors.

## Core Commands

```bash
yy ledger create "Task description" --status todo --tags feature,backend
yy ledger list --status todo,in_progress --limit 10
yy ledger search --tag backend --open
yy ledger get TASK_ID
yy ledger mark in_progress --id TASK_ID --response "Starting work"
yy ledger mark done --id TASK_ID --response "Done: implemented X, tested Y" --commit abc123
yy ledger update TASK_ID --tags backend,urgent
yy ledger deps TASK_ID
yy ledger ready
yy ledger order --scores
```

## Answer Shape

When answering task questions, include:

- the task's current status and unresolved blockers
- the receipt (`--response`) that produced the last transition
- the next unblocked task from `ready` / `order` when asked what to work on next

## Fallback Rules

- If the `yy` CLI is missing, install it first: `npm install -g @yylo/cli` (Node >= 20).
- On controller/routing errors, stop and report; never bypass by editing task files.
- Task state is hot by default; archived tasks surface only via `get` and bounded `archive-search`.
- Cross-project routing is opt-in via registry config; without it, operate from the project root only.

## Source

Canonical home: https://github.com/yylo-dev/yylo-skills (MIT). Requires the external YYLO CLI: https://github.com/yylo-dev/yylo
