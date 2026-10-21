#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kb_to_mpt.py — 知易知识库 → MoneyPrinterTurbo 视频生成 桥接

复用已有的 MoneyPrinterTurbo（C:/E/MoneyPrinterTurbo-main，= 「书本视频 skill」），
把知易 knowledge_cards（蓝卡/绿卡）组装成 MPT 的自定义文案(video_script) + 素材关键词(video_terms)，
推给 MPT 的本地 API 批量生成书摘/知识短视频。不重复造轮子。

用法（在已启动 MPT 的机器上运行）:
  # 用某专题的全部卡片生成一条视频
  python kb_to_mpt.py --project-id 66 --mpt-url http://127.0.0.1:8080

  # 按关键词搜卡片生成（如「纳瓦尔宝典」）
  python kb_to_mpt.py --search "纳瓦尔" --subject "纳瓦尔宝典精读" --mpt-url http://127.0.0.1:8080

  # 只生成文案不推（dry-run，打印 video_script）
  python kb_to_mpt.py --project-id 66 --dry-run

依赖: requests（标准库 urllib 亦可，这里用 requests 简化）
"""
import argparse
import json
import sqlite3
import sys
import time
import urllib.request
import urllib.error

DB = "C:/D/zhiyi/backend/data/antinet.db"
DEFAULT_MPT = "http://127.0.0.1:8080"


def load_cards(project_id=None, search=None, limit=40):
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    cur = c.cursor()
    if project_id:
        cur.execute(
            "SELECT id,card_type,title,content,tags FROM knowledge_cards "
            "WHERE project_id=? ORDER BY id LIMIT ?",
            (project_id, limit),
        )
    elif search:
        like = f"%{search}%"
        cur.execute(
            "SELECT id,card_type,title,content,tags FROM knowledge_cards "
            "WHERE content LIKE ? OR title LIKE ? ORDER BY id LIMIT ?",
            (like, like, limit),
        )
    else:
        raise SystemExit("需要 --project-id 或 --search")
    rows = cur.fetchall()
    c.close()
    return rows


def assemble_script(cards):
    """把卡片拼成一段连贯口播文案：蓝卡=事实点，绿卡=解读，红卡=行动号召。"""
    lines = []
    for r in cards:
        t, title, content = r["card_type"], r["title"], (r["content"] or "")
        # 取正文前 120 字，去掉换行的冗余
        text = content.replace("\n", " ").strip()
        text = text[:160]
        if t == "blue":
            prefix = "要点"
        elif t == "green":
            prefix = "解读"
        elif t == "red":
            prefix = "行动"
        elif t == "yellow":
            prefix = "提醒"
        else:
            prefix = "·"
        lines.append(f"{prefix}：{title}。{text}")
    return "\n".join(lines)


def extract_terms(cards, top_n=8):
    """优先用卡片 curated tags 作素材关键词；无 tag 时回退到标题 2 字非重叠 bigram。"""
    import re, json
    from collections import Counter
    tags = []
    for r in cards:
        raw = r["tags"]
        if raw:
            try:
                t = json.loads(raw) if isinstance(raw, str) else raw
                if isinstance(t, list):
                    tags += [str(x) for x in t if len(str(x)) >= 2]
            except Exception:
                pass
    if tags:
        # 词频排序，去重保序
        seen, out = set(), []
        for w, _ in Counter(tags).most_common():
            if w not in seen:
                seen.add(w); out.append(w)
        return out[:top_n]
    # 回退：标题 2 字非重叠 bigram
    stop = set("的 了 是 在 和 与 及 我们 你 我 他 这 那 也 都 就 而 把 被 让 从 到".split())
    bigrams = []
    for r in cards:
        txt = re.sub(r"[^\u4e00-\u9fff]", "", r["title"] or "")
        for i in range(0, len(txt) - 1, 2):
            bg = txt[i:i+2]
            if bg not in stop:
                bigrams.append(bg)
    return bigrams[:top_n]


def post_video(mpt_url, subject, script, terms, language="zh"):
    url = f"{mpt_url.rstrip('/')}/api/v1/videos"
    body = {
        "video_subject": subject,
        "video_script": script,
        "video_terms": terms,
        "video_language": language,
    }
    data = json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.URLError as e:
        return None, {"error": str(e)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-id", type=int, default=None)
    ap.add_argument("--search", type=str, default=None)
    ap.add_argument("--subject", type=str, default=None)
    ap.add_argument("--mpt-url", type=str, default=DEFAULT_MPT)
    ap.add_argument("--limit", type=int, default=40)
    ap.add_argument("--dry-run", action="store_true", help="只打印文案不上传")
    a = ap.parse_args()

    cards = load_cards(a.project_id, a.search, a.limit)
    if not cards:
        print("未命中任何卡片")
        sys.exit(1)
    print(f"命中卡片 {len(cards)} 张")

    script = assemble_script(cards)
    terms = extract_terms(cards)
    subject = a.subject or (cards[0]["title"] if cards else "知识短视频")

    print("\n===== 组装的 video_script =====")
    print(script[:800])
    print("\n===== 素材关键词 video_terms =====")
    print(terms)

    if a.dry_run:
        print("\n[dry-run] 未上传")
        return

    status, resp = post_video(a.mpt_url, subject, script, terms)
    print(f"\nMPT 响应: HTTP {status}")
    print(json.dumps(resp, ensure_ascii=False, indent=2)[:500])


if __name__ == "__main__":
    main()
