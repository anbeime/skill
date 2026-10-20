#!/usr/bin/env python3
"""
GPT-Image-2 Prompt Engine - Template & Case Query Script
零依赖辅助脚本，按类别/关键词检索本地克隆仓库的模板与案例。
未克隆时优雅降级，输出在线 raw 链接与克隆命令。

Usage:
    python3 query_templates.py --category ecommerce
    python3 query_templates.py --keyword "香水 海报"
    python3 query_templates.py --list
"""

import argparse
import os
import sys

# 上游仓库信息
REPO_URL = "https://github.com/freestylefly/awesome-gpt-image-2"
RAW_BASE = "https://raw.githubusercontent.com/freestylefly/awesome-gpt-image-2/main"

ONLINE_RESOURCES = {
    "templates": f"{RAW_BASE}/docs/templates.md",
    "gallery_part1": f"{RAW_BASE}/docs/gallery-part-1.md",
    "gallery_part2": f"{RAW_BASE}/docs/gallery-part-2.md",
    "gallery": f"{RAW_BASE}/docs/gallery.md",
    "style_library": f"{RAW_BASE}/agents/skills/gpt-image-2-style-library/references/style-library.md",
}

# 模板类别映射
CATEGORIES = {
    "ui": {"id": "ui-screenshot-system", "name": "UI截图系统", "anchor": "tpl-ui"},
    "infographic": {"id": "infographic-engine", "name": "信息图引擎", "anchor": "tpl-infographic"},
    "poster": {"id": "poster-campaign", "name": "海报与排版", "anchor": "tpl-poster"},
    "ecommerce": {"id": "ecommerce-hero", "name": "电商主图", "anchor": "tpl-ecommerce"},
    "brand": {"id": "brand-identity", "name": "品牌视觉", "anchor": "tpl-brand"},
    "photo": {"id": "commercial-photo", "name": "商业摄影", "anchor": "tpl-photo"},
    "character": {"id": "character-design", "name": "角色与IP", "anchor": "tpl-character"},
    "narrative": {"id": "narrative-illustration", "name": "叙事插画", "anchor": "tpl-narrative"},
    "classical": {"id": "classical-chinese", "name": "古籍国风", "anchor": "tpl-classical"},
    "3d": {"id": "3d-render", "name": "3D渲染", "anchor": "tpl-3d"},
}


def find_local_repo():
    """尝试在常见路径查找本地克隆的仓库"""
    candidates = [
        os.path.join(os.path.dirname(__file__), "..", "..", "awesome-gpt-image-2"),
        os.path.expanduser("~/awesome-gpt-image-2"),
        "/tmp/awesome-gpt-image-2",
    ]
    for path in candidates:
        if os.path.isdir(os.path.join(path, "docs")):
            return os.path.abspath(path)
    return None


def print_online_links():
    """输出在线资源链接（降级模式）"""
    print("Local repo not found. Using online search mode.\n")
    print("Online resources:")
    for name, url in ONLINE_RESOURCES.items():
        print(f"  - {name}: {url}")
    print(f"\nClone for full search:")
    print(f"  git clone {REPO_URL}.git")


def list_categories():
    """列出所有模板类别"""
    print("Available template categories:\n")
    for key, info in CATEGORIES.items():
        print(f"  {key:15s} -> {info['name']} (ID: {info['id']})")
    print(f"\nTemplates doc: {ONLINE_RESOURCES['templates']}")


def search_category(category):
    """按类别检索模板"""
    cat = category.lower().strip()
    if cat not in CATEGORIES:
        print(f"Unknown category: {category}")
        print(f"Available: {', '.join(CATEGORIES.keys())}")
        return

    info = CATEGORIES[cat]
    local_repo = find_local_repo()

    print(f"Category: {info['name']} (ID: {info['id']})\n")

    if local_repo:
        templates_path = os.path.join(local_repo, "docs", "templates.md")
        if os.path.isfile(templates_path):
            with open(templates_path, "r", encoding="utf-8") as f:
                content = f.read()
            anchor = f'<a name="{info["anchor"]}"></a>'
            if anchor in content:
                section = content.split(anchor)[1].split('<a name=')[0]
                print(section[:3000])
                return
        print("Local template file parse failed, falling back to online links.")

    print(f"Online templates: {ONLINE_RESOURCES['templates']}#{info['anchor']}")
    print(f"Gallery: {ONLINE_RESOURCES['gallery']}")


def search_keyword(keyword):
    """按关键词搜索模板和案例"""
    local_repo = find_local_repo()
    print(f"Keyword: {keyword}\n")

    if local_repo:
        found = False
        for doc_name in ["templates.md", "gallery.md", "gallery-part-1.md", "gallery-part-2.md"]:
            doc_path = os.path.join(local_repo, "docs", doc_name)
            if os.path.isfile(doc_path):
                with open(doc_path, "r", encoding="utf-8") as f:
                    for i, line in enumerate(f, 1):
                        if keyword.lower() in line.lower():
                            print(f"  [{doc_name}:{i}] {line.strip()[:200]}")
                            found = True
        if found:
            return
        print("No local matches, falling back to online links.")

    print(f"Online templates: {ONLINE_RESOURCES['templates']}")
    print(f"Gallery Part1: {ONLINE_RESOURCES['gallery_part1']}")
    print(f"Gallery Part2: {ONLINE_RESOURCES['gallery_part2']}")


def main():
    parser = argparse.ArgumentParser(description="GPT-Image-2 Template & Case Query")
    parser.add_argument("--category", "-c", help="Search by category")
    parser.add_argument("--keyword", "-k", help="Search by keyword")
    parser.add_argument("--list", "-l", action="store_true", help="List all categories")
    args = parser.parse_args()

    if args.list:
        list_categories()
    elif args.category:
        search_category(args.category)
    elif args.keyword:
        search_keyword(args.keyword)
    else:
        parser.print_help()
        print()
        print_online_links()


if __name__ == "__main__":
    main()
