#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1) 把 description_zh 回填到 description; 2) 对仍缺失的技能用 search API 补全。"""
import json, os, sys, urllib.request, urllib.parse, ssl

MERGED = r"C:\D\skill\skillhub-collection\merged.json"
SEARCH = "https://api.skillhub.cn/api/v1/search?q={q}&limit=5"
CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

def http_get_json(url):
    req = urllib.request.Request(url, headers={"User-Agent": "skillhub-collector/1.0"})
    with urllib.request.urlopen(req, timeout=20, context=CTX) as r:
        return json.loads(r.read().decode("utf-8"))

d = json.load(open(MERGED, encoding="utf-8"))
skills = d["skills"]

# 步骤1: description_zh -> description
zh_fixed = 0
for s in skills:
    if not (s.get("description") or "").strip() and (s.get("description_zh") or "").strip():
        s["description"] = s["description_zh"]
        s["desc_source"] = "description_zh"
        zh_fixed += 1
print(f"由 description_zh 回填: {zh_fixed}")

# 步骤2: 仍缺失的, 用 search 按 slug/name 检索
still_empty = [s for s in skills if not (s.get("description") or "").strip()]
print(f"search 补全前仍缺失: {len(still_empty)}")
filled = 0
for s in still_empty:
    q = s.get("slug") or s.get("name")
    try:
        data = http_get_json(SEARCH.format(q=urllib.parse.quote(q)))
        items = data if isinstance(data, list) else data.get("results") or data.get("data") or data.get("skills") or []
        hit = None
        for it in items:
            if (it.get("slug") or "") == s.get("slug") or (it.get("name") or "") == s.get("name"):
                hit = it; break
        if not hit and items:
            hit = items[0]
        if hit:
            desc = (hit.get("description") or hit.get("description_zh") or "").strip()
            if desc:
                s["description"] = desc
                s["desc_source"] = "search"
                filled += 1
                print(f"  + [{s.get('name')}] {desc[:40]}...")
    except Exception as e:
        print(f"  [warn] {s.get('name')}: {e}")

json.dump(d, open(MERGED, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

# 最终统计
empty = [s["name"] for s in d["skills"] if not (s.get("description") or "").strip()]
print(f"=== 最终总数 {len(d['skills'])}, 仍缺描述: {len(empty)} ===")
for n in empty:
    print("   -", n)
