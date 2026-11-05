#!/usr/bin/env python3
"""Normalise feedback from social media, communities or Discussions into a GitHub issue.

Reads the triggering event from GITHUB_EVENT_PATH, de-duplicates by source URL,
creates (or +1s) an issue labelled ``needs-triage`` and writes ``issue_number``
and ``created`` to GITHUB_OUTPUT.
"""

import json
import os
import subprocess
import sys


SOURCES = {"social", "community", "github"}
MAX_TITLE = 80
MAX_BODY = 6000


def clip(text, limit):
    text = (text or "").strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def normalize(event_name, event):
    if event_name == "repository_dispatch":
        data = event.get("client_payload") or {}
    elif event_name == "workflow_dispatch":
        data = event.get("inputs") or {}
    elif event_name == "discussion":
        discussion = event["discussion"]
        data = {
            "source": "community",
            "platform": f"GitHub Discussions · {discussion['category']['name']}",
            "url": discussion["html_url"],
            "author": discussion["user"]["login"],
            "title": discussion["title"],
            "body": discussion.get("body") or "",
        }
    else:
        raise ValueError(f"不支持的事件: {event_name}")

    source = data.get("source") if data.get("source") in SOURCES else "social"
    title = clip(data.get("title"), MAX_TITLE)
    body = clip(data.get("body"), MAX_BODY)
    if not title and body:
        title = clip(body.splitlines()[0], MAX_TITLE)
    if not title:
        raise ValueError("反馈缺少标题和正文")
    return {
        "source": source,
        "platform": clip(data.get("platform"), 60),
        "url": clip(data.get("url"), 500),
        "author": clip(data.get("author"), 60),
        "title": title,
        "body": body,
    }


def render_issue(item):
    meta = [f"- 来源：`{item['source']}`" + (f" · {item['platform']}" if item["platform"] else "")]
    if item["author"]:
        meta.append(f"- 反馈者：{item['author']}")
    if item["url"]:
        meta.append(f"- 原帖：{item['url']}")
    quoted = "\n".join(f"> {line}" if line else ">" for line in item["body"].splitlines()) or "> （无正文）"
    return "\n".join(
        [
            "<!-- feedback-intake -->",
            "由反馈收集流程自动登记，原文如下。",
            "",
            *meta,
            "",
            "### 原始反馈",
            "",
            quoted,
        ]
    )


def gh(*args):
    return subprocess.run(["gh", *args], check=True, text=True, capture_output=True).stdout


def find_existing(url):
    if not url:
        return None
    found = json.loads(
        gh("issue", "list", "--state", "all", "--search", f'"{url}" in:body', "--json", "number", "--limit", "1")
    )
    return found[0]["number"] if found else None


def write_output(**values):
    path = os.environ.get("GITHUB_OUTPUT")
    if path:
        with open(path, "a", encoding="utf-8") as handle:
            for key, value in values.items():
                handle.write(f"{key}={value}\n")


def main():
    with open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8") as handle:
        event = json.load(handle)
    item = normalize(os.environ["GITHUB_EVENT_NAME"], event)

    existing = find_existing(item["url"])
    if existing:
        gh("issue", "comment", str(existing), "--body", f"同一来源再次收到反馈（{item['platform'] or item['source']}）。")
        write_output(issue_number=existing, created="false", source=item["source"])
        print(f"已存在 #{existing}，仅追加记录")
        return 0

    url = gh(
        "issue",
        "create",
        "--title",
        item["title"],
        "--body",
        render_issue(item),
        "--label",
        f"needs-triage,source:{item['source']}",
    ).strip()
    number = int(url.rstrip("/").rsplit("/", 1)[-1])
    write_output(issue_number=number, created="true", source=item["source"])
    print(f"已创建 #{number}: {url}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
