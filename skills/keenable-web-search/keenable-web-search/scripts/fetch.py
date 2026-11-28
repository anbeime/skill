#!/usr/bin/env python3
"""Keenable 网页读取：把一个网页转成干净的 Markdown，只用 Python 标准库，无需 API Key。

用法:
  python3 fetch.py https://example.com/page [--max-chars 20000] [--json]

默认调用免 Key 的公共接口；设置环境变量 KEENABLE_API_KEY 后改用带 Key 的接口。
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

PUBLIC_URL = "https://api.keenable.ai/v1/fetch/public"
KEYED_URL = "https://api.keenable.ai/v1/fetch"
APP_TITLE = "anbeime-skill"  # 免 Key 调用必须带的应用标识（X-Keenable-Title）


def build_request(page_url, api_key=None):
    headers = {"X-Keenable-Title": APP_TITLE}
    base = PUBLIC_URL
    if api_key:
        base = KEYED_URL
        headers["X-API-Key"] = api_key
    query = urllib.parse.urlencode({"url": page_url})
    return urllib.request.Request(f"{base}?{query}", headers=headers, method="GET")


def fetch(req):
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        if e.code == 429:
            sys.exit("触发频率限制（免 Key 每个 IP 每秒 10 次、每小时 1000 次），请稍后重试。")
        sys.exit(f"读取失败（HTTP {e.code}）：{body}")
    except urllib.error.URLError as e:
        sys.exit(f"无法连接 Keenable：{e.reason}")


def format_page(data, max_chars):
    title = data.get("title") or ""
    url = data.get("url") or ""
    content = data.get("content") or ""
    if max_chars and len(content) > max_chars:
        content = content[:max_chars] + "\n\n...（已截断）"
    # 正文没有自带一级标题时，把标题补在前面
    if title and not content.lstrip().startswith("# "):
        head = f"# {title}\n{url}"
    else:
        head = url
    return f"{head}\n\n{content}".strip()


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Keenable 网页读取（免 Key）")
    p.add_argument("url", help="要读取的网页 URL")
    p.add_argument("--max-chars", dest="max_chars", type=int, default=20000,
                   help="正文最多保留的字符数，默认 20000，0 表示不截断")
    p.add_argument("-j", "--json", action="store_true", help="输出原始 JSON")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    req = build_request(args.url, api_key=os.environ.get("KEENABLE_API_KEY") or None)
    data = fetch(req)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(format_page(data, args.max_chars))


if __name__ == "__main__":
    main()
