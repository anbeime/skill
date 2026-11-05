#!/usr/bin/env bash
# Agent 结束后：检查改动边界 → 跑校验与测试 → 提交并推送到 agent/issue-N → 创建或更新 PR。
set -euo pipefail
issue="$1"
branch="agent/issue-${issue}"
title_file=.agent-out/pr-title.txt
body_file=.agent-out/pr-body.md
touch "$body_file"

changed="$(git -c core.quotePath=false status --porcelain --untracked-files=all | sed 's/^...//')"
if [ -z "$changed" ]; then
  {
    echo "### 🤖 Agent 未提交改动"
    echo
    cat "$body_file"
  } > .agent-out/comment.md
  gh issue comment "$issue" --body-file .agent-out/comment.md
  gh issue edit "$issue" --add-label agent:failed --remove-label agent:in-progress
  exit 0
fi

forbidden="$(printf '%s\n' "$changed" | grep -E '^(\.github/|\.codex-plugin/|skills/native-subtitle-quote-image/VERSION$)' || true)"
if [ -n "$forbidden" ]; then
  printf '### 🤖 Agent 改动越界，已中止\n\n以下文件不允许由 Agent 修改：\n\n```\n%s\n```\n' "$forbidden" > .agent-out/comment.md
  gh issue comment "$issue" --body-file .agent-out/comment.md
  gh issue edit "$issue" --add-label agent:failed --remove-label agent:in-progress
  exit 1
fi

tests_ok=true
{
  python scripts/validate_repo.py
  python -m unittest discover -s tests
} > .agent-out/test.log 2>&1 || tests_ok=false

title="$(head -n 1 "$title_file" 2>/dev/null || true)"
[ -n "$title" ] || title="$(gh issue view "$issue" --json title --jq '"fix: " + .title')"

git config user.name "github-actions[bot]"
git config user.email "41898282+github-actions[bot]@users.noreply.github.com"
git checkout -B "$branch"
git add -A
git commit -q -m "$title" -m "Closes #${issue}"
git push -q --force "https://x-access-token:${PUSH_TOKEN}@github.com/${GITHUB_REPOSITORY}.git" "HEAD:refs/heads/${branch}"

{
  cat "$body_file"
  echo
  echo "---"
  echo
  if $tests_ok; then
    echo "✅ \`validate_repo.py\` 与单元测试已在 Agent 运行环境通过。"
  else
    echo "❌ 校验或测试未通过，已作为草稿 PR 提交，需要人工或 \`@claude\` 继续处理。"
    echo
    echo '<details><summary>测试输出（末尾 80 行）</summary>'
    echo
    echo '```'
    tail -n 80 .agent-out/test.log
    echo '```'
    echo
    echo '</details>'
  fi
  echo
  echo "Closes #${issue}"
  echo
  echo "_本 PR 由 Agent 根据 issue 自动生成，合并前需要维护者审查。_"
} > .agent-out/pr-final.md

# 把 issue 上的 release:* / type:* 标签带到 PR，决定合并后的发版级别和 Release 说明分类。
carried="$(gh issue view "$issue" --json labels --jq '[.labels[].name | select(startswith("release:") or startswith("type:"))] | join(",")')"
labels="agent-pr"
[ -n "$carried" ] && labels="${labels},${carried}"
$tests_ok || labels="${labels},agent:failed"

pr="$(gh pr list --head "$branch" --state open --json number --jq '.[0].number // ""')"
if [ -n "$pr" ]; then
  gh pr edit "$pr" --title "$title" --body-file .agent-out/pr-final.md --add-label "$labels"
else
  draft=()
  $tests_ok || draft=(--draft)
  gh pr create --base "${BASE_BRANCH:-main}" --head "$branch" --title "$title" \
    --body-file .agent-out/pr-final.md --label "$labels" "${draft[@]}"
  pr="$(gh pr list --head "$branch" --state open --json number --jq '.[0].number')"
fi

# 用默认 GITHUB_TOKEN 推送/建 PR 不会触发 pull_request 事件，这里手动补触发 CI 与审查。
if [ "${USING_FALLBACK_TOKEN:-false}" = "true" ]; then
  gh workflow run validate.yml --ref "$branch" || true
  gh workflow run agent-review.yml -f pr_number="$pr" || true
fi

gh issue edit "$issue" --add-label agent:pr-open --remove-label agent:in-progress
gh issue comment "$issue" --body "🤖 已提交 PR #${pr}，等待审查。"
echo "pr_number=${pr}" >> "${GITHUB_OUTPUT:-/dev/null}"
