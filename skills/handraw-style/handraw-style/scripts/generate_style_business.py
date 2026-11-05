#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Style Business Guide Generator & Auditor.
Manages comprehensive business application guides for all styles in business/{number}.md.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
BUSINESS_DIR = ROOT_DIR / "business"
STYLES_JSON = ROOT_DIR / "skills" / "handdraw-style-prompter" / "references" / "styles.json"
COLORS_JSON = ROOT_DIR / "skills" / "handdraw-style-prompter" / "references" / "colors.json"
LAYOUTS_JSON = ROOT_DIR / "skills" / "handdraw-style-prompter" / "references" / "layouts.json"

REQUIRED_SECTIONS = [
    "## 一、 为什么适合这些生意",
    "## 二、 优先商业应用场景与物料矩阵",
    "## 三、 可落地的代表性商业项目策划",
    "## 四、 执行要点与适用边界",
    "## 五、 推荐图型与配色搭配",
]

REQUIRED_METADATA = [
    "- **风格编号**：",
    "- **英文生图名称**：",
    "- **商业定位**：",
]


def load_styles() -> list[dict]:
    with open(STYLES_JSON, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_business_file(file_path: Path, style_number: str) -> tuple[bool, list[str]]:
    if not file_path.exists():
        return False, ["文件不存在"]
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        return False, [f"读取失败: {e}"]

    errors = []
    if len(content) < 1800:
        errors.append(f"字数不足 (当前 {len(content)} 字，要求 >= 1800 字)")

    for sec in REQUIRED_SECTIONS:
        if sec not in content:
            errors.append(f"缺少模块: {sec}")

    for meta in REQUIRED_METADATA:
        if meta not in content:
            errors.append(f"缺少元数据: {meta}")

    if f"# {style_number}" not in content:
        errors.append(f"一级标题缺少或未匹配风格编号: # {style_number}")

    return len(errors) == 0, errors


def list_missing_styles() -> list[dict]:
    BUSINESS_DIR.mkdir(parents=True, exist_ok=True)
    styles = load_styles()
    existing_files = {f.name for f in BUSINESS_DIR.glob("*.md")}
    missing = []
    for s in styles:
        filename = f"{s['number']}.md"
        if filename not in existing_files:
            missing.append(s)
        else:
            is_valid, _ = validate_business_file(BUSINESS_DIR / filename, s["number"])
            if not is_valid:
                missing.append(s)
    return missing


def audit_all_files():
    BUSINESS_DIR.mkdir(parents=True, exist_ok=True)
    styles = load_styles()
    total_styles = len(styles)
    existing_files = list(BUSINESS_DIR.glob("*.md"))
    print(f"=== 商业应用指南全库审计 ===")
    print(f"总计画风数量: {total_styles}")
    print(f"现有商业文档: {len(existing_files)}")

    valid_count = 0
    invalid_files = []
    missing_files = []

    for s in styles:
        num = s["number"]
        fpath = BUSINESS_DIR / f"{num}.md"
        if not fpath.exists():
            missing_files.append(num)
            continue
        is_valid, errs = validate_business_file(fpath, num)
        if is_valid:
            valid_count += 1
        else:
            invalid_files.append((num, errs))

    print(f"通过合规校验: {valid_count} / {total_styles}")
    if missing_files:
        print(f"缺失文档数量: {len(missing_files)}")
        print(f"缺失编号示例: {missing_files[:15]}{'...' if len(missing_files) > 15 else ''}")
    if invalid_files:
        print(f"结构不合规文档: {len(invalid_files)}")
        for num, errs in invalid_files[:5]:
            print(f"  - {num}: {'; '.join(errs)}")


def main():
    parser = argparse.ArgumentParser(description="Style Business Guide Generator & Auditor")
    parser.add_argument("--style", help="Style number to inspect or validate (e.g. FI-001 or FA-001)")
    parser.add_argument("--missing", action="store_true", help="List styles that lack valid business application guides")
    parser.add_argument("--audit", action="store_true", help="Run full audit on all business application guides")
    args = parser.parse_args()

    if args.missing:
        missing = list_missing_styles()
        print(f"共发现 {len(missing)} 个风格缺少合规商业文档：")
        for s in missing:
            print(f"  - {s['number']} · {s.get('reference', '')} ({s.get('generation_name', '')})")
        return

    if args.audit or (not args.style and not args.missing):
        audit_all_files()
        return

    if args.style:
        num = args.style.strip()
        fpath = BUSINESS_DIR / f"{num}.md"
        if not fpath.exists():
            print(f"[STATUS] 风格 {num} 尚未生成商业应用文档: {fpath}")
            sys.exit(1)
        is_valid, errs = validate_business_file(fpath, num)
        if is_valid:
            print(f"[OK] 风格 {num} 商业应用文档合规 ({len(fpath.read_text(encoding='utf-8'))} 字): {fpath}")
        else:
            print(f"[FAIL] 风格 {num} 商业应用文档未通过校验:")
            for e in errs:
                print(f"  - {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
