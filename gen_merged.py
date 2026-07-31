#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 merged.json (多榜单合并) -> 每个技能一个 SKILL.md + README + skills.json"""
import os, re, json, sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = HERE
SKILLS_DIR = os.path.join(OUT, "skills")
SRC = os.path.join(HERE, "merged.json")
SRC = os.path.abspath(SRC)

SOURCE_LABEL = "SkillHub 多榜单合并 (api.skillhub.cn: recommended/hot/featured/newest/trending/paid)"

def safe_folder(slug, name, idx):
    if slug:
        s = re.sub(r'[^a-zA-Z0-9._-]', '-', slug).strip('-')
        if s:
            return s[:80]
    s = re.sub(r'[^a-zA-Z0-9._一-鿿-]', '-', name).strip('-')
    s = s[:80] or f"skill-{idx}"
    return s

def yaml_str(v):
    v = (v or "").replace("\r", "").replace("\n", " ").strip()
    v = re.sub(r'\s+', ' ', v)
    return v.replace('"', "'")

def main():
    with open(SRC, encoding="utf-8") as f:
        data = json.load(f)
    skills = data.get("skills", [])
    sources = data.get("sources", {})
    print(f"[OK] 读取合并数据, 共 {len(skills)} 个技能; 来源: {sources}")

    # 清空旧 skills 目录, 干净重生成
    if os.path.isdir(SKILLS_DIR):
        for entry in os.listdir(SKILLS_DIR):
            p = os.path.join(SKILLS_DIR, entry)
            if os.path.isdir(p):
                import shutil
                shutil.rmtree(p)
    os.makedirs(SKILLS_DIR, exist_ok=True)

    used = {}
    index_rows = []
    for i, s in enumerate(skills):
        name = s.get("name") or s.get("slug") or f"未命名{i}"
        slug = s.get("slug", "")
        desc = yaml_str(s.get("description") or s.get("description_zh") or "")
        category = s.get("category", "")
        tags = s.get("tags") or []
        if isinstance(tags, str):
            tags = [t for t in re.split(r'[，,、\s]+', tags) if t]
        homepage = s.get("homepage") or s.get("upstream_url") or ""
        stars = s.get("stars", 0)
        installs = s.get("installs", 0)

        base = safe_folder(slug, name, i)
        if base in used:
            used[base] += 1
            folder = f"{base}_{used[base]}"
        else:
            used[base] = 0
            folder = base
        d = os.path.join(SKILLS_DIR, folder)
        os.makedirs(d, exist_ok=True)

        tag_list = ", ".join(tags) if tags else "—"
        md = f"""---
name: "{name}"
description: "{desc[:500]}"
source: "{SOURCE_LABEL}"
skillhub_slug: "{slug}"
category: "{category}"
tags: [{", ".join(f'"{t}"' for t in tags)}]
homepage: "{homepage}"
stars: {stars}
installs: {installs}
---

# {name}

{desc if desc else '(暂无描述)'}

## 元信息
- 分类: {category or '—'}
- 标签: {tag_list}
- 主页: {homepage or '—'}
- SkillHub slug: {slug or '—'}
- 来源: {SOURCE_LABEL}
"""
        with open(os.path.join(d, "SKILL.md"), "w", encoding="utf-8") as fp:
            fp.write(md)
        index_rows.append((name, folder, category, desc[:80]))

    # README 索引（按分类分组）
    cats = {}
    for name, folder, category, _d in index_rows:
        cats.setdefault(category or "未分类", []).append((name, folder))

    src_line = "、".join(f"{k}({v})" for k, v in sources.items() if v)
    lines = ["# SkillHub 技能全集（多榜单合并）", "",
             f"> 通过 SkillHub 官方 CLI 从 `api.skillhub.cn` 采集并合并多个榜单：**{src_line}**，去重后共 **{len(skills)}** 个技能。",
             f"> 数据来源：{SOURCE_LABEL}", "",
             "## 按分类浏览", ""]
    for cat in sorted(cats.keys()):
        lines.append(f"### {cat}（{len(cats[cat])}）")
        for name, folder in cats[cat]:
            lines.append(f"- [{name}](skills/{folder}/SKILL.md)")
        lines.append("")
    lines += ["---", "", "每个技能对应 `skills/<slug>/SKILL.md`，含完整 frontmatter（名称/描述/分类/标签/主页/星标/安装数）。"]
    with open(os.path.join(OUT, "README.md"), "w", encoding="utf-8") as fp:
        fp.write("\n".join(lines) + "\n")

    with open(os.path.join(OUT, "skills.json"), "w", encoding="utf-8") as fp:
        json.dump([{
            "name": s.get("name"), "slug": s.get("slug"),
            "category": s.get("category"), "description": s.get("description"),
            "tags": s.get("tags"), "homepage": s.get("homepage"),
            "stars": s.get("stars"), "installs": s.get("installs"),
            "folder": safe_folder(s.get("slug", ""), s.get("name", ""), i)
        } for i, s in enumerate(skills)], fp, ensure_ascii=False, indent=2)

    print(f"[OK] 生成 {len(skills)} 个 SKILL.md -> {SKILLS_DIR}")
    print(f"[OK] 索引 README.md / skills.json 已更新")

if __name__ == "__main__":
    main()
