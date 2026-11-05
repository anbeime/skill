# Agent 驱动的反馈处理工作流

本项目用一套 GitHub Actions 把「收集反馈 → 评估 → 编码测试 → PR → 审查合并」串起来。Agent 负责评估、写代码、跑测试和初审，**合并永远由维护者决定**。

```
社区 / 社媒 / GitHub ──► ① Feedback Intake ──► issue（needs-triage）
                                                   │
                                                   ▼
                                         ② Agent Triage 评估可行性
                     ┌──────────────┬──────────────┼─────────────────┐
                needs-info       rejected /     accepted          accepted
               （追问用户）      duplicate     （自动条件满足）  （需维护者确认）
                                                   │                 │ 加 agent:implement
                                                   ▼                 ▼
                                         ③ Agent Implement 编码 + 测试
                                                   │
                                                   ▼
                                         ④ 自动提交 PR（agent/issue-N）
                                                   │
                                                   ▼
                          ⑤ Validate CI + Agent Review ──► 维护者审查合并（可 @claude 继续改）
```

## 各阶段

| 阶段 | 工作流 | 触发 | 产出 |
|---|---|---|---|
| ① 收集 | `feedback-intake.yml` | `repository_dispatch`（类型 `feedback`）、手动运行、Discussions 的 Ideas/Feedback 分类新帖 | 带 `needs-triage`、`source:*` 的 issue；按原帖链接去重 |
| ① 收集 | Issue 模板 | 用户在 GitHub 提 issue | 结构化的 bug / 功能建议 |
| ② 评估 | `agent-triage.yml` | 新 issue、维护者评论 `/triage`、被 ① 调用 | `triage:*`、`type:*`、`size:*`、`risk:*` 标签 + 评估评论 |
| ③ 编码 | `agent-implement.yml` | 满足自动条件、维护者加 `agent:implement`、手动运行 | 改动 + 测试，跑通 `tools/validate_repo.py` 与 `unittest` |
| ④ PR | `.github/scripts/open_agent_pr.sh` | ③ 完成后 | `agent/issue-N` 分支上的 PR，`Closes #N`；测试失败则提交为草稿 |
| ⑤ 审查 | `validate.yml`、`agent-review.yml`、`claude.yml` | PR 打开/更新；维护者 `@claude` | CI 结果、Agent 行内审查意见；`@claude` 可按意见继续改 |
| 收尾 | `agent-cleanup.yml` | PR 关闭 | 合并后摘掉关联 issue 上的 `agent:*`、`status:awaiting-maintainer` 过程标签；未合并就关闭只摘 `agent:pr-open` |

CI（`validate.yml`）在 Linux 上跑：仓库检查、单元测试，以及用随包字体渲染一页样张的冒烟测试。依赖 macOS Vision 的 Swift 工具不在 CI 范围内。

## 什么时候自动进入编码

评估结论同时满足以下条件，Agent 才会**不经人工**直接开始编码：

- 仓库变量 `AGENT_AUTO_IMPLEMENT` 为 `true`（默认关闭）；
- 结论 `accepted`，类型是 bug / feature / docs，规模 `S` 或 `M`，风险不是 `high`；
- issue 作者是仓库 Owner / Member / Collaborator，或反馈来自维护者控制的收集入口（社媒、社区）。

其他 `accepted` 的 issue 会打上 `status:awaiting-maintainer`，维护者加 `agent:implement` 标签即可放行。不想让 Agent 碰的 issue 加 `agent:skip`。

改默认版式效果（字号、配色、断行、图层顺序）的需求评估为高风险，始终要维护者看过样张再决定。

## 一次性配置

1. **Agent 凭据**（Settings → Secrets and variables → Actions → Secrets，二选一）
   - `ANTHROPIC_API_KEY`：Anthropic API key；或
   - `CLAUDE_CODE_OAUTH_TOKEN`：在本地运行 `claude setup-token` 生成。

   未配置时 Agent 相关工作流整体跳过，不会报红；`Validate` 照常运行。
2. **允许 Actions 创建 PR**（Settings → Actions → General → Workflow permissions）：勾选 **Allow GitHub Actions to create and approve pull requests** 并保存。不打开时 Agent 能推送分支，但建 PR 会报 `GitHub Actions is not permitted to create or approve pull requests`；配置了 `AGENT_GITHUB_TOKEN` 则不依赖这个开关。
3. **可选 Secret** `AGENT_GITHUB_TOKEN`：fine-grained PAT 或 GitHub App token（权限 Contents、Pull requests、Issues 读写）。配置后 Agent 建的 PR 会正常触发 CI；不配置时工作流会用 `workflow_dispatch` 补触发 Validate 与 Agent Review。
4. **Variables**
   - `AGENT_AUTO_IMPLEMENT`：`true` 开启自动编码，默认关闭。
   - `AGENT_MODEL`：可选，指定 Agent 使用的模型；留空用默认值。
5. **标签**：Actions 页手动运行一次 **Sync Labels**（之后修改 `.github/labels.json` 会自动同步）。
6. **@claude 交互**：在本地 Claude Code 里运行 `/install-github-app`，或安装 [Claude GitHub App](https://github.com/apps/claude)。
7. **分支保护**（Settings → Branches → `main`）：要求 PR、至少 1 个审批、必需检查 `validate (3.10)`、`validate (3.13)`。
8. **Discussions**（可选）：开启后建一个名为 `Ideas` 或 `Feedback` 的分类，新帖会自动转为 issue。

## 接入社媒 / 社区反馈

任何能发 HTTP 请求的工具（n8n、Zapier、飞书/企业微信机器人、定时爬取脚本）都可以把反馈送进来：

```bash
curl -X POST https://api.github.com/repos/chengyi-ai/cy-carousel-skill/dispatches \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  -d '{"event_type":"feedback","client_payload":{
        "source":"social","platform":"小红书",
        "url":"https://www.xiaohongshu.com/explore/xxx",
        "author":"某用户","title":"希望正文支持思源黑体","body":"原帖内容……"}}'
```

或者用仓库自带的命令行：

```bash
GITHUB_TOKEN=... python tools/submit_feedback.py \
  --platform 微博 --url https://weibo.com/xxx --title "浅色底上红圈太淡" --body "原帖内容……"
```

也可以在 Actions → **Feedback Intake** → Run workflow 里手动填写。`source` 取 `social`（社媒）或 `community`（群聊、论坛、Discussions）。同一个 `url` 只会登记一次，再次收到只在原 issue 下追加记录。

用于调用 dispatch 的 token 只需要本仓库的 Contents 写权限；它代表维护者，所以经它登记的反馈视为已过一道人工筛选，可以走自动编码。

## 安全设计

- **用户文本不进 prompt**：issue 内容写入 `.agent-in/issue.json`，Agent 被告知它是不可信数据。
- **评估 Agent 没有执行权**：只有 Read / Glob / Grep / Write，不能运行命令，也没有 GitHub 写权限；标签和评论由 `apply_triage.py` 根据 JSON 结论写入，并过滤疑似凭据。
- **编码 Agent 不能提交和推送**：checkout 不保留凭据；只允许运行 Python 和只读 git 命令。改动 `.github/`、`LICENSE` 或 `assets/fonts/` 会被拒绝。
- **外部用户提的 issue 不会自动编码**，必须维护者加 `agent:implement`。
- **fork 来的 PR 不跑 Agent Review**（拿不到密钥），由维护者手动 `@claude` 或审查。
- **合并永远需要人工审批**。

## 常用操作

| 想做什么 | 怎么做 |
|---|---|
| 重新评估某个 issue | 在 issue 下评论 `/triage` |
| 让 Agent 实现某个 issue | 加 `agent:implement` 标签 |
| 让 Agent 按审查意见修改 PR | 在 PR 下评论 `@claude 请按上面的意见修改` |
| Agent 报 “not permitted to create or approve pull requests” | 按「一次性配置」第 2 步打开开关，再给 issue 重新加 `agent:implement` |
| Agent 失败后接手 | 查看 `agent:failed` 的 issue 与运行日志，在草稿 PR 上继续 |
| 本地跑检查 | `python tools/validate_repo.py && python -m unittest discover -s tests` |
