#!/usr/bin/env python3
"""Turn the triage agent's JSON verdict into labels, a comment and an implement decision.

The agent only writes a JSON file; every write to GitHub happens here, so issue
text can never steer what gets labelled or whether code generation starts.
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


DECISIONS = {"accepted", "needs-info", "rejected", "duplicate"}
TYPES = {"bug", "feature", "docs", "question"}
SIZES = {"S", "M", "L"}
RISKS = {"low", "medium", "high"}
TRUSTED_ASSOCIATIONS = {"OWNER", "MEMBER", "COLLABORATOR"}
# 由维护者控制的入口（repository_dispatch / 手动登记）创建的反馈视为已过一道人工筛选。
TRUSTED_SOURCES = {"community", "social"}
MANAGED_PREFIXES = ("triage:", "type:", "size:", "risk:")
MANAGED_LABELS = {"needs-triage", "status:awaiting-maintainer"}
MARKER = "<!-- agent-triage -->"
SECRET_ENV = ("ANTHROPIC_API_KEY", "CLAUDE_CODE_OAUTH_TOKEN", "GH_TOKEN", "AGENT_GITHUB_TOKEN")
SECRET_PATTERN = re.compile(r"(sk-ant-[A-Za-z0-9_-]{8,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})")


def redact(text):
    """Never echo credentials into a public comment, whatever the agent wrote."""
    for name in SECRET_ENV:
        value = os.environ.get(name)
        if value and len(value) >= 8:
            text = text.replace(value, "[REDACTED]")
    return SECRET_PATTERN.sub("[REDACTED]", text)


def load_result(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    decision = data.get("decision")
    if decision not in DECISIONS:
        raise ValueError(f"decision 无效: {decision!r}")
    data["type"] = data.get("type") if data.get("type") in TYPES else "question"
    data["size"] = data.get("size") if data.get("size") in SIZES else "L"
    data["risk"] = data.get("risk") if data.get("risk") in RISKS else "high"
    for key in ("plan", "questions"):
        value = data.get(key) or []
        data[key] = [str(item) for item in value] if isinstance(value, list) else [str(value)]
    duplicate = data.get("duplicate_of")
    data["duplicate_of"] = duplicate if isinstance(duplicate, int) and duplicate > 0 else None
    return data


def should_implement(result, association, source, auto_implement):
    return (
        auto_implement
        and result["decision"] == "accepted"
        and result["type"] in {"bug", "feature", "docs"}
        and result["size"] in {"S", "M"}
        and result["risk"] != "high"
        and (association in TRUSTED_ASSOCIATIONS or source in TRUSTED_SOURCES)
    )


def render_comment(result, implement):
    lines = [MARKER, "### 🤖 Agent 需求评估", ""]
    verdict = {
        "accepted": "✅ 可行，建议采纳",
        "needs-info": "❓ 信息不足，需要补充",
        "rejected": "⛔ 暂不采纳",
        "duplicate": "🔁 疑似重复",
    }[result["decision"]]
    lines.append(
        f"**结论**：{verdict} · 类型 `{result['type']}` · 规模 `{result['size']}` · 风险 `{result['risk']}`"
    )
    if result.get("summary"):
        lines += ["", f"**需求摘要**：{result['summary']}"]
    if result.get("reasoning"):
        lines += ["", f"**理由**：{result['reasoning']}"]
    if result["duplicate_of"]:
        lines += ["", f"**可能重复**：#{result['duplicate_of']}"]
    if result["plan"]:
        lines += ["", "**实现思路**："] + [f"{i}. {step}" for i, step in enumerate(result["plan"], 1)]
    if result["questions"]:
        lines += ["", "**需要补充的信息**："] + [f"- {q}" for q in result["questions"]]
    lines.append("")
    if implement:
        lines.append("➡️ 已自动进入编码阶段，Agent 完成后会提交 PR 并关联本 issue。")
    elif result["decision"] == "accepted":
        lines.append("⏸ 等待维护者确认：添加 `agent:implement` 标签即可让 Agent 开始编码。")
    elif result["decision"] == "needs-info":
        lines.append("补充信息后编辑 issue 或留言，维护者可重新触发评估。")
    else:
        lines.append("以上为自动评估，最终是否关闭由维护者决定。")
    return "\n".join(lines)


def plan_actions(result, association, source, auto_implement):
    implement = should_implement(result, association, source, auto_implement)
    labels = [
        f"triage:{result['decision']}",
        f"type:{result['type']}",
        f"size:{result['size']}",
        f"risk:{result['risk']}",
    ]
    if result["decision"] == "accepted" and not implement:
        labels.append("status:awaiting-maintainer")
    return {
        "labels": labels,
        "comment": redact(render_comment(result, implement)),
        "implement": implement,
    }


def gh(*args, check=True):
    return subprocess.run(["gh", *args], check=check, text=True, capture_output=True)


def apply(issue, actions):
    current = json.loads(gh("issue", "view", str(issue), "--json", "labels").stdout)["labels"]
    stale = [
        label["name"]
        for label in current
        if label["name"].startswith(MANAGED_PREFIXES) or label["name"] in MANAGED_LABELS
    ]
    stale = [name for name in stale if name not in actions["labels"]]
    if stale:
        gh("issue", "edit", str(issue), "--remove-label", ",".join(stale))
    gh("issue", "edit", str(issue), "--add-label", ",".join(actions["labels"]))
    gh("issue", "comment", str(issue), "--body", actions["comment"])


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result", required=True)
    parser.add_argument("--issue", required=True, type=int)
    parser.add_argument("--association", default="NONE")
    parser.add_argument("--source", default="github")
    parser.add_argument("--auto-implement", default="false")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    result = load_result(args.result)
    actions = plan_actions(
        result,
        args.association.upper(),
        args.source,
        args.auto_implement.lower() == "true",
    )
    if args.dry_run:
        print(json.dumps(actions, ensure_ascii=False, indent=2))
    else:
        apply(args.issue, actions)

    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output, "a", encoding="utf-8") as handle:
            handle.write(f"implement={'true' if actions['implement'] else 'false'}\n")
            handle.write(f"decision={result['decision']}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
