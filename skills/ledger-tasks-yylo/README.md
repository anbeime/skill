# YYLO Ledger Tasks (ledger-tasks-yylo)

让 AI 编程代理通过 git 原生的看板/任务账本驱动多步骤开发：任务状态、依赖排序、状态回执与多 worktree 串行交付，全部以文件形式保存在仓库内，跨会话可审计。

## 适用场景

- 多步骤、跨会话的功能开发与任务追踪
- 依赖感知的并行执行排序（拓扑排序、阻塞关系）
- 状态流转必须留痕（`--response` 回执 + `--commit` 关联）
- 多 agent / 多 worktree 协作的串行合并交付

## 核心原则

1. 先读后写：`yy ledger list` / `get` / `ready` 了解现状再变更。
2. 任务粒度小：一次迭代可完成，避免撑爆上下文。
3. 每次状态变更必须带 `--response` 回执，说明做了什么、如何验证。
4. 依赖显式建模：`deps add` 声明阻塞关系，环会被自动检测。
5. 绝不直接编辑 `.juno_task/` 文件，CLI 是唯一合法入口。

## 安装

```bash
npm install -g @yylo/cli
```

要求 Node >= 20。

## 常用命令

```bash
yy ledger create "任务描述" --status todo --tags feature
yy ledger ready                 # 查看无阻塞任务
yy ledger order --scores        # 拓扑排序，规划并行执行
yy ledger mark in_progress --id TASK_ID --response "开始实现"
yy ledger mark done --id TASK_ID --response "完成并测试" --commit abc123
```

## 技能来源

来源：<https://github.com/yylo-dev/yylo-skills>（MIT）。
依赖外部 YYLO CLI：<https://github.com/yylo-dev/yylo>。
