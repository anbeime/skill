#!/usr/bin/env python3
"""
sync_skills_to_search.py
========================
把 SKILL_SOURCES.json 里的上游仓库列表（被 sync_skills.py 每日抓取）映射成
public/data/skills.json 的格式（前端 skills.html 搜索用的数据源）。

设计目标：
- 自动从 awesome-agent-skills 等上游抓取后，**同一天**反映到前端搜索
- **热门技能榜单**：通过 GitHub Search API 获取 agent-skills /
  claude-skills / cursor-skills 相关仓库，按 Star 数与近期 push 活跃度排序。
- 离线降级：若 GitHub API 不可达 / 触发限流，自动回退到 MANUAL_DESCRIPTIONS
  种子（不再出网），保证每日机器人构建不中断。
- 默认模式：trending-only（只刷新热门榜单段，不污染已有 curated 列表）
- --all 模式：把 SKILL_SOURCES 全量注入（慎用，会把 3000+ 仓库塞进搜索）
- --offline 模式：强制离线，仅用 MANUAL_DESCRIPTIONS 种子（不调用 GitHub API）

约束（与 AGENTS.md §3 出域铁律一致）：
- 默认仍优先复用本地 SKILL_SOURCES.json（零出网）
- 仅「热门榜单」段走 GitHub Search API（api.github.com，只读、无需鉴权也可跑，
  有 GITHUB_TOKEN/GH_TOKEN 时走更高频限额）
- 无 git 操作（push 由 GitHub Actions 后续步骤处理）

用法：
    python scripts/sync_skills_to_search.py                # trending-only（默认抓取在线榜单）
    python scripts/sync_skills_to_search.py --offline      # 离线：仅用 MANUAL 种子
    python scripts/sync_skills_to_search.py --all           # 全量同步 SKILL_SOURCES
    python scripts/sync_skills_to_search.py --dry-run      # 仅打印，不写盘
"""

import argparse
import json
import os
import ssl
import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

# 复用 sync_skills.py 的统计注入能力（A：README 真实计数自动同步）
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sync_skills import (inject_readme_stats, count_local_skills,
                         count_search_skills, count_trending_skills,
                         guard_readme_claims)


SOURCE_PATH = Path("SKILL_SOURCES.json")
TARGET_PATH = Path("public/data/skills.json")

SOURCE_CATEGORY_HINTS = {
    "voltagent_awesome": "Agent Skill",
    "openai_skills": "OpenAI Skill",
    "awesome_dsh_plugin": "DSH Plugin",
    "mattpocock_skills": "TypeScript Skill",
    "voltagent_design_md": "Web Design",
}

# 离线降级种子：GitHub API 不可用时回退，避免构建中断。
# 同时也是「动态抓取结果与手写描述匹配时」的富化来源。
MANUAL_DESCRIPTIONS = {
    "s1dashu/ip-as-logo-skill": "IP as Logo：把产品 prompt 变成 6 张公司级 IP 吉祥物（3 左下 / 3 右下、三色语义、动物优先）。支持 Codex / Coze / Doubao / YouMind / Manus / Gemini Apps / Replit Agent。",
    "img2threejs/img2threejs": "image-to-threejs：把参考图按代码重构为 Three.js 模型（代码-only、不下载 mesh），v1.5.2，Apache-2.0。14 个开源 demo（CS2 / Pikachu / BMX 等），含 forge/ Python 工具链。",
    "ZzzLc0405/photo-abstract-editorial": "photo-abstract-editorial：把一张照片做成「原图 + 抽象记忆面板 + 诗意英文标题」的竖版杂志式编辑作品。CC BY-NC-SA 4.0（仅个人 / 教育 / 非商业）。",
    "firecrawl/anydoc": "anydoc：Rust 库把 Word / PPT / Excel / OpenDocument / RTF / EPUB / CSV / PDF 转成 GitHub-Flavored Markdown，毫秒级；Node.js / Python / WASM 三端绑定；浏览器内 WASM 不出网。",
    "VoltAgent/awesome-design-md": "awesome-design-md：73 个真实网站 DESIGN.md 提取（Claude / Cursor / Vercel / Stripe / Apple / Tesla / Ferrari ...），让 AI 编码 agent 读 DESIGN.md 后生成风格一致的高质量 UI。",
}

# 旧 TRENDING 集合（仅用于离线降级与兼容，不再是数据真源）
TRENDING = set(MANUAL_DESCRIPTIONS.keys())

# GitHub Search API：用于真实抓取「热门 / 趋势」agent 技能仓库
GITHUB_API = "https://api.github.com/search/repositories"
# 更具体的技能主题：用于排除仅靠泛化 `agent-skills` 标签混入的巨型通用仓库
# （如 morluto/rea 453k 星，本质不是「技能」产品）
SKILL_TOPICS_STRICT = ("claude-skills", "cursor-skills", "claude-code",
                       "codex-skills", "ai-agents", "dsh-plugin", "mcp")


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


def infer_category_github(item: dict) -> str:
    topics = [t.lower() for t in (item.get("topics") or [])]
    blob = " ".join(topics) + " " + (item.get("description") or "") + " " + item.get("name", "")
    blob = blob.lower()
    if any(k in blob for k in ("pdf", "docx", "word", "excel", "csv", "markdown", "document")):
        return "Document Parsing"
    if any(k in blob for k in ("image", "photo", "canvas", "art", "draw", "video")):
        return "Image Generation"
    if any(k in blob for k in ("three", "3d", "mesh", "blender")):
        return "3D / Three.js"
    if any(k in blob for k in ("design", "ui", "ux", "tailwind", "frontend", "web")):
        return "Web Design"
    if any(k in blob for k in ("test", "debug", "audit", "security", "agent")):
        return "Development Tooling"
    return "AI Agent Skill"


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


def _is_skill_repo(item: dict) -> bool:
    """相关性过滤：只保留看起来是「技能」的仓库，过滤掉巨型通用仓库的噪声。

    判定（任一满足即保留）：
    - 仓库名或描述含 "skill"（最可靠信号）
    - 命中更具体的技能主题（claude-skills / cursor-skills / claude-code / ...）
    纯靠泛化 `agent-skills` 标签的巨型仓库（如 morluto/rea, 453k 星）会被排除。
    """
    fn = (item.get("full_name") or "").lower()
    desc = (item.get("description") or "").lower()
    topics = [t.lower() for t in (item.get("topics") or [])]
    # 超高星但名称/描述都不含 skill 的巨型通用仓库（如 morluto/rea 453k 星，
    # 仅靠 claude-code/mcp 等泛标签混入）直接排除，避免污染热门榜首。
    stars = item.get("stargazers_count", 0) or 0
    if stars > 200000 and "skill" not in fn and "skill" not in desc:
        return False
    if "skill" in fn or "skill" in desc:
        return True
    return any(t in SKILL_TOPICS_STRICT for t in topics)


def fetch_github_trending(max_per_list: int = 25, timeout: int = 25) -> list:
    """
    调用 GitHub Search API 获取 agent 技能相关仓库的「热门 / 趋势」榜。

    返回 list[dict]，每条含 name/description/link/category/source/stars/forks/
    language/topics/pushed_at/trending 等字段；按 star 数降序。
    任何失败（网络/限流/解析）均返回 []（调用方据此走离线降级）。
    """
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "anbeime-skill-sync-bot",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = "Bearer " + token

    since = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    # 多重查询合并去重：按 star 取「热门」，按近期 push 取「趋势」
    queries = [
        ("popular", "topic:claude-skills", "stars"),
        ("popular", "topic:cursor-skills", "stars"),
        ("popular", "topic:agent-skills", "stars"),
        ("trending", "topic:agent-skills pushed:>%s" % since, "updated"),
    ]

    collected: dict = {}
    ctx = ssl.create_default_context()
    for label, q, sort in queries:
        params = urlencode({"q": q, "sort": sort, "order": "desc", "per_page": max_per_list})
        url = GITHUB_API + "?" + params
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=timeout, context=ctx) as resp:
                if resp.status != 200:
                    print("[WARN] github search (%s) HTTP %d" % (label, resp.status))
                    continue
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001 - 任何异常都降级，不中断每日构建
            print("[WARN] github search (%s) failed: %s" % (label, e))
            continue

        for it in data.get("items", []):
            fn = it.get("full_name", "")
            if not fn or fn in collected:
                continue
            if not _is_skill_repo(it):
                continue
            owner, repo = fn.split("/", 1)
            collected[fn] = {
                "name": fn,
                "description": (it.get("description") or "AI agent skill · 来自 GitHub 实时抓取（按 Star / 近期活跃排序）。").strip(),
                "link": it.get("html_url", "https://github.com/" + fn),
                "category": infer_category_github(it),
                "source": "github-trending",
                "stars": it.get("stargazers_count", 0),
                "forks": it.get("forks_count", 0),
                "language": it.get("language") or "",
                "topics": it.get("topics") or [],
                "pushed_at": it.get("pushed_at") or "",
                "trending": True,
                "crawled_at": datetime.now().isoformat(),
            }

    result = list(collected.values())
    result.sort(key=lambda s: s.get("stars", 0), reverse=True)
    return result


def write_target(skills: list, trending_names: set = None) -> int:
    trending_names = trending_names or TRENDING

    def sort_key(s):
        is_trend = (s.get("name") in trending_names) or (s.get("trending") is True)
        return (0 if is_trend else 1, -(s.get("stars", 0) or 0), s.get("category", "Z"), s["name"].lower())

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


def sync_trending(dry_run: bool, enable_github: bool = True) -> dict:
    """
    刷新「热门技能榜单」段：
    - enable_github=True（默认）：调用 GitHub Search API；
      命中 MANUAL_DESCRIPTIONS 的种子用更丰富的人工描述覆盖，但标记 trending+真实 stars。
    - 网络失败 / --offline：回退到 MANUAL_DESCRIPTIONS 种子（不调用 GitHub API）。

    保留既有 curated 列表（非 trending 条目原样保留），只重写 trending 段，避免污染。
    """
    target = load_target()
    existing = target.get("skills", [])

    # 仅保留「非榜单」条目（旧 trending 段会被整体重写，避免过期残留）
    preserved = [
        s for s in existing
        if not s.get("trending")
        and s.get("source") != "github-trending"
        and s["name"] not in TRENDING
        and not str(s.get("source", "")).startswith("anbeime/skill (D-25 trending")
    ]
    by_name = {s["name"]: s for s in preserved}

    added = updated = 0
    gh = fetch_github_trending() if enable_github else None

    if gh:
        for e in gh:
            fn = e["name"]
            if fn in MANUAL_DESCRIPTIONS:
                e["description"] = MANUAL_DESCRIPTIONS[fn]  # 富化：手写描述优先
            if fn in by_name:
                by_name[fn].update(e)
                updated += 1
            else:
                by_name[fn] = e
                added += 1
        print("[OK github-trending] fetched=%d added=%d updated=%d" % (len(gh), added, updated))
    else:
        # 离线降级：仅用 MANUAL 种子
        sources = load_sources()
        src_repos = sources.get("sources", {})
        for tid in TRENDING:
            meta = src_repos.get(tid)
            source_key = meta.get("upstream_source") if meta else "anbeime/skill D-25 trending"
            if tid in by_name:
                by_name[tid]["trending"] = True
                by_name[tid]["source"] = "github-trending (offline-cache)"
                updated += 1
            else:
                e = build_skill_entry(tid, source_key or "anbeime/skill D-25 trending")
                e["trending"] = True
                e["source"] = "github-trending (offline-cache)"
                by_name[tid] = e
                added += 1
        print("[WARN offline] GitHub API 不可用，回退到 MANUAL_DESCRIPTIONS 种子（共 %d）" % len(TRENDING))

    if dry_run:
        return {"total": len(by_name), "added": added, "updated": updated}
    total = write_target(list(by_name.values()), trending_names=set(by_name.keys()) if gh else TRENDING)
    print("[OK trending-mode] total=" + str(total))
    return {"total": total, "added": added, "updated": updated}


def main():
    parser = argparse.ArgumentParser(description="Sync SKILL_SOURCES.json -> public/data/skills.json")
    parser.add_argument("--dry-run", action="store_true", help="not writing, only print")
    parser.add_argument("--all", dest="sync_all_mode", action="store_true",
                        help="sync ALL repos from SKILL_SOURCES (3000+, may pollute; default = trending-only)")
    parser.add_argument("--offline", dest="offline", action="store_true",
                        help="disable GitHub API, use MANUAL_DESCRIPTIONS seed only")
    args = parser.parse_args()

    if args.sync_all_mode:
        sync_all(dry_run=args.dry_run)
    else:
        sync_trending(dry_run=args.dry_run, enable_github=not args.offline)

    # A：刷新中英 README 统计段真实计数（搜索库/热门榜单数以本次最新 skills.json 为准）
    if not args.dry_run:
        try:
            src = load_sources()
            _stats = dict(
                upstream=src.get("total_count", len(src.get("sources", {}))),
                local=count_local_skills(),
                search=count_search_skills(),
                trending=count_trending_skills(),
            )
            inject_readme_stats(**_stats, path="README.md", lang="zh")
            inject_readme_stats(**_stats, path="README_EN.md", lang="en")
            # 清理头部违规宣称
            guard_readme_claims("README.md")
            guard_readme_claims("README_EN.md")
        except Exception as e:
            print("[WARN] inject_readme_stats failed: %s" % e)


if __name__ == "__main__":
    main()
