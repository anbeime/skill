#!/usr/bin/env python3
"""Send community or social-media feedback into the repository's intake workflow.

Uses GitHub's repository_dispatch API, so it works from n8n, Zapier, a chat bot
or a terminal. Requires a token with ``contents: write`` on this repository in
GITHUB_TOKEN (or pass --token).
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request


REPOSITORY = "chengyi-ai/cy-carousel-skill"
SOURCES = ("social", "community", "github")


def build_payload(args):
    return {
        "event_type": "feedback",
        "client_payload": {
            "source": args.source,
            "platform": args.platform,
            "url": args.url,
            "author": args.author,
            "title": args.title,
            "body": args.body,
        },
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--title", required=True, help="一句话概括反馈")
    parser.add_argument("--body", required=True, help="反馈原文或整理后的描述")
    parser.add_argument("--source", choices=SOURCES, default="social")
    parser.add_argument("--platform", default="", help="如 小红书、微博、X、即刻、微信群")
    parser.add_argument("--url", default="", help="原帖链接，用于去重和回溯")
    parser.add_argument("--author", default="", help="反馈者昵称（可留空）")
    parser.add_argument("--repo", default=REPOSITORY)
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN", ""))
    parser.add_argument("--dry-run", action="store_true", help="只打印请求体")
    args = parser.parse_args(argv)

    payload = build_payload(args)
    if args.dry_run:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        return 0
    if not args.token:
        parser.error("缺少 token：设置 GITHUB_TOKEN 或传 --token")

    request = urllib.request.Request(
        f"https://api.github.com/repos/{args.repo}/dispatches",
        data=json.dumps(payload).encode("utf-8"),
        method="POST",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {args.token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20):
            pass
    except urllib.error.HTTPError as exc:
        print(f"提交失败: HTTP {exc.code} {exc.read().decode('utf-8', 'replace')}", file=sys.stderr)
        return 1
    print("已提交，稍后会在 Issues 中看到带 needs-triage 标签的新条目。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
