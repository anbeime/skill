#!/usr/bin/env python3
"""
sync_skills_to_search.py
========================
把 SKILL_SOURCES.json 里的上游仓库列表（被 sync_skills.py 每日抓取）映射成
public/data/skills.json 的格式（前端 skills.html 搜索用的数据源）。

设计目标：
- 自动从 awesome-agent-skills 等上游抓取后，**同一天**反映到前端搜索
- 5 个 D-25 trending skill（s1dashu/ip-as-logo-skill 等）保留人工 description（更详细）
- 默认模式：trending-only（只注入 5 条 trending，不污染已有 curated 列表）
- --all 模式：把 SKILL_SOURCES 全量注入（慎用，会把 3000+ 仓库塞进搜索）

约束（与 AGENTS.md §3 出域铁律一致）：
- 纯本地操作，零出网（read + write 本地 JSON）
- 无 git 操作（push 由 GitHub Actions 后续步骤处理）

用法：
    python scripts/sync_skills_to_search.py                # trending-only 模式（默认）
    python scripts/sync_skills_to_search.py --all           # 全量同步 SKILL_SOURCES
    python scripts/sync_skills_to_search.py --dry-run      # 仅打印，不写盘
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path


SOURCE_PATH = Path("SKILL_SOURCES.json")
TARGET_PATH = Path("public/data/skills.json")

SOURCE_CATEGORY_HINTS = {
    "voltagent_awesome": "Agent Skill",
    "openai_skills": "OpenAI Skill",
    "awesome_dsh_plugin": "DSH Plugin",
    "mattpocock_skills": "TypeScript Skill",
    "voltagent_design_md": "Web Design",
}

MANUAL_DESCRIPTIONS = {
    "s1dashu/ip-as-logo-skill": "IP as Logo：把产品 prompt 变成 6 张公司级 IP 吉祥物（3 左下 / 3 右下、三色语义、动物优先）。支持 Codex / Coze / Doubao / YouMind / Manus / Gemini Apps / Replit Agent。",
    "img2threejs/img2threejs": "image-to-threejs：把参考图按代码重构为 Three.js 模型（代码-only、不下载 mesh），v1.5.2，Apache-2.0。14 个开源 demo（CS2 / Pikachu / BMX 等），含 forge/ Python 工具链。",
    "ZzzLc0405/photo-abstract-editorial": "photo-abstract-editorial：把一张照片做成「原图 + 抽象记忆面板 + 诗意英文标题」的竖版杂志式编辑作品。CC BY-NC-SA 4.0（仅个人 / 教育 / 非商业）。",
    "firecrawl/anydoc": "anydoc：Rust 库把 Word / PPT / Excel / OpenDocument / RTF / EPUB / CSV / PDF 转成 GitHub-Flavored Markdown，毫秒级；Node.js / Python / WASM 三端绑定；浏览器内 WASM 不出网。",
    "VoltAgent/awesome-design-md": "awesome-design-md：73 个真实网站 DESIGN.md 提取（Claude / Cursor / Vercel / Stripe / Apple / Tesla / Ferrari ...），让 AI 编码 agent 读 DESIGN.md 后生成风格一致的高质量 UI。",
}

TRENDING = set(MANUAL_DESCRIPTIONS.keys())


def infer_category(source_key: str, repo_name: str) -> str:
    name_lower = repo_name.lower()
    if any(k in name_lower for k in ("pdf", "docx", "word", "excel", "csv", "markdown")):
        return "Document Parsing"
    if any(k in name_lower for k in ("image", "photo", "canvas", "art", "draw")):
        return "Image Generation"
    if any(k in name_lower for k in ("three", "3d", "mesh")):
        return "3D / Three.js"
    if any(k in name_lower for k in ("design", "ui", "ux", "tailwind", "frontend")):
        return "Web Design"
    if any(k in name_lower for k in ("test", "debug", "audit", "security")):
        return "Development Tooling"
    return SOURCE_CATEGORY_HINTS.get(source_key, "Other")


def make_description(source_key: str, repo_id: str) -> str:
    if repo_id in MANUAL_DESCRIPTIONS:
        return MANUAL_DESCRIPTIONS[repo_id]
    return "AI agent skill · 来源上游 " + source_key + "（自动收录于 " + datetime.now().strftime("%Y-%m-%d") + "）。请到上游 README 查看实际描述。"


def load_sources() -> dict:
    if not SOURCE_PATH.exists():
        print("[ERR] " + str(SOURCE_PATH) + " not found", file=sys.stderr)
        sys.exit(1)
    return json.loads(SOURCE_PATH.read_text(encoding="utf-8"))


def load_target() -> dict:
    if not TARGET_PATH.exists():
        return {"skills": [], "total": 0, "updated_at": None}
    return json.loads(TARGET_PATH.read_text(encoding="utf-8"))


def build_skill_entry(repo_id: str, source_key: str) -> dict:
    owner, repo = repo_id.split("/", 1)
    return {
        "name": repo_id,
        "description": make_description(source_key, repo_id),
        "link": "https://github.com/" + owner + "/" + repo,
        "category": infer_category(source_key, repo),
        "source": source_key,
        "crawled_at": datetime.now().isoformat(),
    }


def write_target(skills: list) -> int:
    def sort_key(s):
        is_trend = s["name"] in TRENDING
        return (0 if is_trend else 1, s.get("category", "Z"), s["name"].lower())
    skills.sort(key=sort_key)
    out = {
        "skills": skills,
        "total": len(skills),
        "updated_at": datetime.now().isoformat(),
    }
    TARGET_PATH.parent.mkdir(parents=True, exist_ok=True)
    TARGET_PATH.write_text(
        json.dumps(out, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return out["total"]


def sync_all(dry_run: bool) -> dict:
    """全量同步 SKILL_SOURCES.json 里的所有 repo"""
    sources = load_sources()
    target = load_target()
    by_name = {s["name"]: s for s in target["skills"]}
    src_repos = sources.get("sources", {})

    added = updated = skipped = 0
    for repo_id, meta in src_repos.items():
        source_key = meta.get("upstream_source", "unknown")
        if repo_id in by_name:
            existing = by_name[repo_id]
            if existing.get("source") != source_key:
                existing["source"] = source_key
                updated += 1
            else:
                skipped += 1
        else:
            by_name[repo_id] = build_skill_entry(repo_id, source_key)
            added += 1

    print("[INFO all-mode] added=" + str(added) + " updated=" + str(updated) + " skipped=" + str(skipped))
    if dry_run:
        return {"total": len(by_name), "added": added, "updated": updated}
    total = write_target(list(by_name.values()))
    print("[OK all-mode] total=" + str(total))
    return {"total": total, "added": added, "updated": updated}


def sync_trending(dry_run: bool) -> dict:
    """只注入 5 条 D-25 trending（不污染 curated 列表）"""
    sources = load_sources()
    target = load_target()
    by_name = {s["name"]: s for s in target["skills"]}
    src_repos = sources.get("sources", {})

    added = updated = skipped = 0
    for tid in TRENDING:
        meta = src_repos.get(tid)
        source_key = meta.get("upstream_source") if meta else "anbeime/skill D-25 trending"
        if tid in by_name:
            existing = by_name[tid]
            # 只在 source 字段缺失时补
            if not existing.get("source"):
                existing["source"] = source_key
                updated += 1
            else:
                skipped += 1
        else:
            by_name[tid] = build_skill_entry(tid, source_key or "anbeime/skill D-25 trending")
            added += 1

    print("[INFO trending-mode] added=" + str(added) + " updated=" + str(updated) + " skipped=" + str(skipped))
    if dry_run:
        return {"total": len(by_name), "added": added, "updated": updated}
    total = write_target(list(by_name.values()))
    print("[OK trending-mode] total=" + str(total))
    return {"total": total, "added": added, "updated": updated}


def main():
    parser = argparse.ArgumentParser(description="Sync SKILL_SOURCES.json -> public/data/skills.json")
    parser.add_argument("--dry-run", action="store_true", help="not writing, only print")
    parser.add_argument("--all", dest="sync_all_mode", action="store_true",
                        help="sync ALL repos from SKILL_SOURCES (3000+, may pollute; default = trending-only)")
    args = parser.parse_args()

    if args.sync_all_mode:
        sync_all(dry_run=args.dry_run)
    else:
        sync_trending(dry_run=args.dry_run)


if __name__ == "__main__":
    main()