#!/usr/bin/env bash
# 把 issue 及其评论写进 .agent-in/，供 Agent 以“数据文件”的方式读取，避免把用户文本拼进 prompt。
set -euo pipefail
issue="$1"
mkdir -p .agent-in .agent-out
gh issue view "$issue" --json number,title,body,author,labels,comments,url,state > .agent-in/issue.json
gh api "repos/${GITHUB_REPOSITORY}/issues/${issue}" --jq '.author_association' > .agent-in/association.txt
gh issue list --state open --limit 200 --json number,title > .agent-in/open-issues.json
