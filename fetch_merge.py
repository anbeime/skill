#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓取 SkillHub 多个榜单并合并去重，输出 merged.json。"""
import subprocess, json, os, sys

CLI = r"C:\D\skill\.tmp_kit\cli\skills_store_cli.py"
OUT = r"C:\D\skill\skillhub-collection\merged.json"

TYPES = ["recommended", "hot", "featured", "newest", "trending", "paid", "all"]

def fetch(t):
    try:
        out = subprocess.check_output(
            [sys.executable, CLI, "skill", "rankings", "--type", t, "--timeout", "25"],
            stderr=subprocess.DEVNULL, timeout=60,
        )
        data = json.loads(out.decode("utf-8"))
        skills = data.get("skills") or []
        return skills
    except Exception as e:
        print(f"  [warn] type={t} failed: {e}")
        return []

def better(a, b):
    """返回更优的技能条目（字段更全、描述更长）。"""
    if not a: return b
    if not b: return a
    da = (a.get("description") or "").strip()
    db = (b.get("description") or "").strip()
    # 优先有描述
    if bool(da) != bool(db):
        return a if da else b
    # 都有/都无描述时，比较描述长度与字段数
    if len(db) != len(da):
        return a if len(da) >= len(db) else b
    ka, kb = len(a), len(b)
    return a if ka >= kb else b

merged = {}
per_type_counts = {}
for t in TYPES:
    print(f"fetching type={t} ...")
    skills = fetch(t)
    per_type_counts[t] = len(skills)
    for s in skills:
        slug = s.get("slug")
        if not slug:
            continue
        cur = merged.get(slug)
        merged[slug] = better(cur, s)

result = {
    "sources": per_type_counts,
    "total": len(merged),
    "skills": list(merged.values()),
}
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("=== 各榜单抓取数 ===")
for t, c in per_type_counts.items():
    print(f"  {t}: {c}")
print(f"=== 合并去重后总数: {len(merged)} ===")

# 统计仍缺描述的
empty = [s["name"] for s in merged.values() if not (s.get("description") or "").strip()]
print(f"合并后仍缺描述: {len(empty)}")
for n in empty:
    print("   -", n)
