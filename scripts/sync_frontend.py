#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""前端 + README 同步脚本（skillhub-collection）。

职责：
1. 合并 data/ 与 public/data/ 两份已分叉的 local_skills.json（取并集，data/ 为主）；
2. 写回两处保持一致（前端 local-skills.html 读 public/data/local_skills.json）；
3. 重写 README.md「💾 本地技能库」段（LOCAL-SKILLS 标记内，机器人不会触碰）；
4. 供收录流水线调用：新收录技能后跑一次即完成前端+README 同步。

用法: python scripts/sync_frontend.py [--dry-run]
"""
import json
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_A = ROOT / "data" / "local_skills.json"        # 主数据（机器人 badge 引用）
DATA_B = ROOT / "public" / "data" / "local_skills.json"  # 前端数据
README = ROOT / "README.md"

MARK_START = "<!-- LOCAL-SKILLS-START -->"
MARK_END = "<!-- LOCAL-SKILLS-END -->"

CAT_ORDER_LEGACY = [  # 原 README 里的展示顺序，没出现的排后面
    "内容创作与发布", "视频创作", "电商与营销", "PPT与演示", "语音与音频",
    "数字人与视频配音", "文档与分析", "智能体协作", "产品与项目管理",
    "设计与可视化", "AI 创意与可视化", "文档处理", "技能管理", "财务分析",
    "文化创作", "邮件与办公自动化", "医疗与行业 Agent", "收录开源技能",
]


def merge(a: dict, b: dict) -> dict:
    cats_a = a.get("categories", {})
    cats_b = b.get("categories", {})
    merged_cats = {}
    names = list(cats_a.keys()) + [k for k in cats_b.keys() if k not in cats_a]
    for cat in names:
        sa = list((cats_a.get(cat) or {}).get("skills", []))
        sb = list((cats_b.get(cat) or {}).get("skills", []))
        seen, skills = set(), []
        for s in sa + sb:
            if s not in seen:
                seen.add(s)
                skills.append(s)
        merged_cats[cat] = {"count": len(skills), "skills": skills}

    # skill_details：以 A 为准，缺的从 B 补
    details = dict(a.get("skill_details", {}))
    for k, v in (b.get("skill_details") or {}).items():
        details.setdefault(k, v)

    # 统计：字段级取 A，数值取两边较大值（保守估计已收录规模）
    stats_a = a.get("statistics", {})
    stats_b = b.get("statistics", {})
    stats = {}
    for key in ("by_api_requirement", "by_usage_frequency"):
        sa, sb = stats_a.get(key, {}), stats_b.get(key, {})
        stats[key] = {k: max(sa.get(k, 0), sb.get(k, 0)) for k in set(sa) | set(sb)}

    all_skills = sorted({s for c in merged_cats.values() for s in c["skills"]})
    total = len(all_skills)
    today = date.today().isoformat()

    out = dict(a)  # metadata/highlights 等以 A 为骨架
    out["categories"] = merged_cats
    out["skill_details"] = details
    out["statistics"] = stats
    out["metadata"] = {**a.get("metadata", {}),
                       "total_skills": total,
                       "last_updated": today}

    log = list(a.get("update_log", []))
    prev_total = a.get("metadata", {}).get("total_skills")
    if str(prev_total) != str(total):
        log.append({"date": today, "version": "auto-sync",
                    "changes": [f"前端/README 同步：技能总数 {prev_total} → {total}（合并 data/ 与 public/ 分叉）"]})
    out["update_log"] = log[-20:]
    return out


def readme_section(data: dict) -> str:
    order = [c for c in CAT_ORDER_LEGACY if c in data["categories"]] + \
            [c for c in data["categories"] if c not in CAT_ORDER_LEGACY]
    lines = ["## 💾 本地技能库", "",
             f"共 **{data['metadata']['total_skills']}** 个精选技能，按用途分类"
             f"（最后同步 {data['metadata']['last_updated']}，由 `scripts/sync_frontend.py` 自动生成本段）。", ""]
    for cat in order:
        skills = data["categories"][cat]["skills"]
        lines.append(f"### {cat}（{len(skills)}个）")
        for s in skills:
            d = data["skill_details"].get(s) or {}
            desc = d.get("description_cn") or d.get("description_en") or ""
            star = d.get("rating") or ""
            suffix = f" - {desc}" if desc else ""
            prefix = f"{star} " if star else ""
            lines.append(f"- **{s}** {prefix}{suffix}".rstrip())
        lines.append("")
    return "\n".join(lines)


def apply_readme(text: str, section: str) -> str:
    if MARK_START in text and MARK_END in text:
        pre = text.split(MARK_START)[0]
        post = text.split(MARK_END, 1)[1]
        return f"{pre}{MARK_START}\n{section}\n{MARK_END}{post}"
    # 无标记：替换整个「## 💾 本地技能库」段（到下一个 ## 标题为止），并补上标记
    pat = re.compile(r"## 💾 本地技能库\n.*?(?=\n## )", re.S)
    if pat.search(text):
        return pat.sub(f"{MARK_START}\n{section}\n{MARK_END}", text, count=1)
    # 兜底：追加到 AUTO-SYNC-SKILLS 段之后
    return text.replace("<!-- AUTO-SYNC-SKILLS-END -->",
                        f"<!-- AUTO-SYNC-SKILLS-END -->\n\n{MARK_START}\n{section}\n{MARK_END}", 1)


def main():
    dry = "--dry-run" in sys.argv
    a = json.loads(DATA_A.read_text(encoding="utf-8"))
    b = json.loads(DATA_B.read_text(encoding="utf-8"))
    merged = merge(a, b)
    payload = json.dumps(merged, ensure_ascii=False, indent=2)

    section = readme_section(merged)
    readme = README.read_text(encoding="utf-8")
    new_readme = apply_readme(readme, section)

    n_cats = len(merged["categories"])
    total = merged["metadata"]["total_skills"]
    print(f"合并结果: {n_cats} 个分类 / {total} 个技能")
    for cat, c in merged["categories"].items():
        print(f"  - {cat}: {c['count']}")
    changed_b = set()
    for cat in merged["categories"]:
        pass
    print(f"README: {'将更新' if new_readme != readme else '无变化'}"
          f"（{len(new_readme.splitlines())} 行）")
    if dry:
        print("[dry-run] 未写入任何文件")
        return 0
    DATA_A.write_text(payload + "\n", encoding="utf-8")
    DATA_B.write_text(payload + "\n", encoding="utf-8")
    if new_readme != readme:
        README.write_text(new_readme, encoding="utf-8")
    print("✅ 已写入 data/local_skills.json、public/data/local_skills.json、README.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
