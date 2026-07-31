#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫描用户级已装技能，生成 teams/installed-skills.md 真实目录。"""
import os, re, sys

SKILLS_ROOT = r"C:\Users\topgo\.workbuddy\skills"
OUT = r"C:\D\skill\skillhub-collection\teams\installed-skills.md"

def extract(name, path):
    try:
        txt = open(path, encoding="utf-8").read()
    except Exception:
        return (name, "(无法读取)", "")
    txt = txt.replace("\r\n", "\n").replace("\r", "\n")
    # frontmatter
    fm = ""
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", txt, re.S)
    if m:
        fm = m.group(1)
    def fld(k):
        # 优先多行块 description: | ...
        mm = re.search(rf'^{k}:\s*\|\n(.*?)(?:\n\S|\Z)', fm, re.S)
        if mm: return mm.group(1).strip()
        mm = re.search(rf'^{k}:\s*(.*)$', fm, re.M)
        if mm:
            v = mm.group(1).strip().strip('"').strip("'")
            if v and v != "|":
                return v
        return ""
    desc = fld("description") or fld("name") or txt.split("\n", 1)[-1][:80]
    desc = re.sub(r"\s+", " ", desc)[:120]
    return (name, desc, fld("name"))

rows = []
for entry in sorted(os.listdir(SKILLS_ROOT)):
    d = os.path.join(SKILLS_ROOT, entry)
    if not os.path.isdir(d):
        continue
    sk = os.path.join(d, "SKILL.md")
    if os.path.isfile(sk):
        rows.append(extract(entry, sk))
    else:
        rows.append((entry, "(无 SKILL.md)", ""))

lines = ["# 已安装技能清单（用户级）", "",
         f"> 来源：`~/.workbuddy/skills/`，共 **{len(rows)}** 个已安装技能。",
         "> 这些技能被 TOP 专家团的 9 大团队所引用。", "",
         "| # | 目录名 | 简介 |",
         "|---|--------|------|"]
for i, (dirn, desc, _n) in enumerate(rows, 1):
    lines.append(f"| {i} | `{dirn}` | {desc[:90]} |")
lines.append("")
with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print(f"[OK] 生成 {len(rows)} 个已装技能目录 -> {OUT}")
