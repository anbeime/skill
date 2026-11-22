#!/usr/bin/env python3
"""Keenable 联网搜索：只用 Python 标准库，无需 API Key。

用法:
  python3 search.py "查询内容" [--site arxiv.org]
                    [--published-after YYYY-MM-DD] [--published-before YYYY-MM-DD]
                    [--max-results 10] [--json]

默认调用免 Key 的公共接口；设置环境变量 KEENABLE_API_KEY 后改用带 Key 的接口
（Key 只用于提高频率限制）。
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request

PUBLIC_URL = "https://api.keenable.ai/v1/search/public"
KEYED_URL = "https://api.keenable.ai/v1/search"
APP_TITLE = "anbeime-skill"  # 免 Key 调用必须带的应用标识（X-Keenable-Title）
SNIPPET_MAX = 400


def build_request(query, site=None, published_after=None, published_before=None,
                  max_results=10, api_key=None):
    payload = {"query": query, "max_results": max_results}
    if site:
        payload["site"] = site
    if published_after:
        payload["published_after"] = published_after
    if published_before:
        payload["published_before"] = published_before

    headers = {"Content-Type": "application/json", "X-Keenable-Title": APP_TITLE}
    url = PUBLIC_URL
    if api_key:
        url = KEYED_URL
        headers["X-API-Key"] = api_key
    return urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )


def search(req):
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", "replace")
        if e.code == 429:
            sys.exit("触发频率限制（免 Key 每个 IP 每秒 10 次、每小时 1000 次），请稍后重试。")
        sys.exit(f"搜索失败（HTTP {e.code}）：{body}")
    except urllib.error.URLError as e:
        sys.exit(f"无法连接 Keenable：{e.reason}")


def format_results(data):
    results = data.get("results") or []
    if not results:
        return "没有结果。"
    out = []
    for i, r in enumerate(results, 1):
        title = r.get("title") or "（无标题）"
        url = r.get("url", "")
        # description 字段为空，正文摘要在 snippet 里
        snippet = " ".join((r.get("snippet") or "").split())
        if len(snippet) > SNIPPET_MAX:
            snippet = snippet[:SNIPPET_MAX] + "..."
        out.append(f"{i}. {title}\n   {url}")
        if snippet:
            out.append(f"   {snippet}")
    return "\n".join(out)


def max_results_arg(value):
    n = int(value)
    if not 1 <= n <= 50:
        raise argparse.ArgumentTypeError("max-results 取值 1-50")
    return n


def parse_args(argv=None):
    p = argparse.ArgumentParser(description="Keenable 联网搜索（免 Key）")
    p.add_argument("query", nargs="+", help="自然语言查询")
    p.add_argument("--site", help="只搜一个站点，例如 arxiv.org")
    p.add_argument("--published-after", dest="published_after", help="YYYY-MM-DD")
    p.add_argument("--published-before", dest="published_before", help="YYYY-MM-DD")
    p.add_argument("--max-results", dest="max_results", type=max_results_arg,
                   default=10, help="返回条数 1-50，默认 10")
    p.add_argument("-j", "--json", action="store_true", help="输出原始 JSON")
    return p.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    req = build_request(
        " ".join(args.query),
        site=args.site,
        published_after=args.published_after,
        published_before=args.published_before,
        max_results=args.max_results,
        api_key=os.environ.get("KEENABLE_API_KEY") or None,
    )
    data = search(req)
    if args.json:
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        print(format_results(data))


if __name__ == "__main__":
    main()
