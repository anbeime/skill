#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
解析 SkillHub 推荐清单 (skillhub_paste.txt) -> 每个技能一个 SKILL.md
用法: python build_skills.py
"""
import os, re, json

SRC = r"C:\D\skill\skillhub_paste.txt"
OUT = r"C:\D\skill\skillhub-collection"
SKILLS_DIR = os.path.join(OUT, "skills")

HEADER_WORDS = {"推荐", "skillhub", "套件"}

def sanitize_folder(name: str) -> str:
    bad = '/\\:*?"<>|\t'
    s = ''.join(ch for ch in name if ch not in bad)
    s = s.strip().strip('.')
    s = re.sub(r'\s+', '_', s)
    if not s:
        s = "skill"
    return s[:80]

def is_desc(ln: str) -> bool:
    """一行文本看起来像描述（而非技能名）吗？"""
    if any(p in ln for p in '。；！？、，'):
        return True
    if len(ln) > 25:
        return True
    return False

def next_nonblank(lines, start):
    i = start
    while i < len(lines):
        if lines[i].strip():
            return i
        i += 1
    return None

def main():
    if not os.path.exists(SRC):
        print(f"[ERROR] 找不到源文件: {SRC}")
        print("请先把 SkillHub 推荐清单原文保存为 C:\\D\\skill\\skillhub_paste.txt")
        return

    with open(SRC, encoding="utf-8") as f:
        raw = f.read()

    # 截断用户可能附带的问题文字
    for m in ["github.com/anbeime", "这些技能并", "仓库吗", "你能采集"]:
        idx = raw.find(m)
        if idx != -1:
            raw = raw[:idx]

    lines = [ln.strip() for ln in raw.splitlines()]

    # 丢弃开头页眉(推荐 / SkillHub / 套件)
    i = 0
    while i < len(lines):
        w = lines[i].lower()
        if w in HEADER_WORDS or "skillhub" in w:
            i += 1
        else:
            break

    skills = []
    cur = None
    n = len(lines)

    def append_desc(skill, text):
        skill["desc"] = (skill["desc"] + "\n" + text).strip() if skill["desc"] else text

    while i < n:
        ln = lines[i]
        if not ln:
            i += 1
            continue
        nb = next_nonblank(lines, i + 1)
        nxt = lines[nb].strip() if nb is not None else ""
        # 1) 重复标题锚定: 当前行与下一非空行相同 -> 技能名
        if ln == nxt:
            cur = {"name": ln, "desc": "", "conf": "high"}
            skills.append(cur)
            i = nb + 1
            continue
        # 2) 明显描述行
        if is_desc(ln):
            if cur is None:
                cur = {"name": f"未命名_{i}", "desc": "", "conf": "low"}
                skills.append(cur)
            append_desc(cur, ln)
            i += 1
            continue
        # 3) 看起来像标题的短行 —— 用前瞻判断是否其实是上一条的短描述
        nb2 = next_nonblank(lines, nb + 1) if nb is not None else None
        nxt2 = lines[nb2].strip() if nb2 is not None else ""
        if nxt and (not is_desc(nxt)) and nxt != ln:
            # 当前短行后面紧跟另一个“标题样”短行 -> 当前行很可能是上一条的短描述
            if cur is None:
                cur = {"name": f"未命名_{i}", "desc": "", "conf": "low"}
                skills.append(cur)
            append_desc(cur, ln)
            i += 1
            continue
        if nxt == "" and cur is not None:
            # 文件最后一行且不是标题 -> 当作描述追加
            append_desc(cur, ln)
            i += 1
            continue
        # 否则: 真正的标题
        cur = {"name": ln, "desc": "", "conf": "high"}
        skills.append(cur)
        i += 1

    # 去重(同名取第一条), 并标记可疑项
    seen = set()
    final = []
    for s in skills:
        nm = s["name"]
        if not nm or nm.startswith("未命名_"):
            s["conf"] = "low"
        if any(p in nm for p in "。；！？、，"):
            s["conf"] = "low"
        if len(nm) > 25:
            s["conf"] = "low"
        if nm in seen:
            continue
        seen.add(nm)
        final.append(s)

    os.makedirs(SKILLS_DIR, exist_ok=True)

    used = {}
    index_rows = []
    low_conf = []
    for s in final:
        base = sanitize_folder(s["name"])
        if base in used:
            used[base] += 1
            folder = f"{base}_{used[base]}"
        else:
            used[base] = 0
            folder = base
        d = os.path.join(SKILLS_DIR, folder)
        os.makedirs(d, exist_ok=True)

        desc = s["desc"].replace("\r", "").strip()
        fm_desc = desc.replace("\n", " ").replace('"', "'")
        if len(fm_desc) > 500:
            fm_desc = fm_desc[:497] + "..."

        body_desc = desc if desc else "(暂无描述)"
        md = f"""---
name: "{s['name']}"
description: "{fm_desc}"
source: "SkillHub 推荐列表"
---

# {s['name']}

{body_desc}
"""
        with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as fp:
            fp.write(md)

        index_rows.append((s["name"], folder, desc[:100]))
        if s["conf"] == "low":
            low_conf.append(s["name"])

    # README 索引
    idx_lines = ["# SkillHub 推荐技能集", "",
                 f"> 自动从 SkillHub 推荐清单采集，共 {len(final)} 个技能。", "",
                 "## 目录", ""]
    for i2, (name, folder, _d) in enumerate(index_rows, 1):
        idx_lines.append(f"{i2}. [{name}](skills/{folder}/SKILL.md)")
    idx_lines += ["", "---", "", "每个技能对应 `skills/<名称>/SKILL.md`。"]
    if low_conf:
        idx_lines += ["", "## ⚠️ 需人工核对的条目", "",
                      "以下条目解析置信度较低（名称可能实为描述，或缺少描述），请检查：", ""]
        for nm in low_conf:
            idx_lines.append(f"- {nm}")
    with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8") as fp:
        fp.write("\n".join(idx_lines) + "\n")

    # JSON 备份
    with open(os.path.join(OUT, "skills.json"), "w", encoding="utf-8") as fp:
        json.dump([{"name": s["name"], "description": s["desc"],
                    "folder": sanitize_folder(s["name"]), "conf": s["conf"]}
                   for s in final], fp, ensure_ascii=False, indent=2)

    print(f"[OK] 共解析 {len(final)} 个技能")
    print(f"      空描述: {sum(1 for s in final if not s['desc'])}")
    print(f"      低置信: {len(low_conf)} -> {low_conf[:10]}")
    for s in final[:8]:
        print(f"   - [{s['conf']}] {s['name']}  | 描述 {len(s['desc'])} 字")

if __name__ == "__main__":
    main()
