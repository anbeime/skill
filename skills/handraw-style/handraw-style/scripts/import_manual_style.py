#!/usr/bin/env python3
"""Add a categorized visual style (FA-FI) after a representative image is available."""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")
from PIL import Image, ImageOps

from style_library_import import (
    create_numbered_tile,
    rebuild_and_validate,
    update_manifest,
    update_readme_and_skill,
)
from contact_sheet_registry import append_style
from style_asset_paths import ALIAS_MAP_FILE, ROOT, asset_dir, single_path

SOURCE_MD = ROOT / "styles_200_reorganized.md"
MODEL_CAP = ROOT / "skills" / "handdraw-style-prompter" / "references" / "model_capabilities.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-name", required=True, help="Chinese/original style label")
    parser.add_argument("--generation-name", required=True, help="English generation style name")
    parser.add_argument("--category", default="FG", help="Style category code (FA~FI), default FG")
    parser.add_argument("--style-id", help="Explicit style ID (e.g. FG-025)")
    parser.add_argument("--traits", default="", help="Positive concrete visual traits")
    parser.add_argument("--traits-file", type=Path, help="File containing traits text")
    parser.add_argument("--raw-traits", action="store_true", help="Preserve traits exactly as provided")
    parser.add_argument("--image", type=Path, help="Representative source image")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    return parser.parse_args()


def positive_traits(value: str) -> str:
    subject_leakage_patterns = [
        r"[白黑红黄蓝绿米粉]\S*?(?:长裙|短裙|连衣裙|衬衫|风衣|T恤|衣服|背带裤)",
        r"[黑金黄棕白]\S*?(?:短发|长发|马尾|卷发|发型)",
        r"(?:侧身|回眸|侧脸|站姿|坐姿|奔跑|漫步|蹲下|招手)的?(?:自然)?(?:姿态|姿势|动态)?",
        r"大面积\S*?(?:花田|花海|草地|植被|向日葵)",
        r"(?:海湾|湖海|山峦|雪山|街道|马路|森林)\S*?(?:远景|中景|近景|层次)",
        r"前景\S*?(?:轻微遮挡|虚化遮挡|花草遮挡)",
        r"三分法构图人物偏[左右中]",
        r"年轻[男女]性|年轻[男女]子",
    ]
    leakage_re = re.compile("|".join(subject_leakage_patterns))

    parts = [part.strip() for part in value.replace("。", "；").split("；")]
    cleaned = []
    for part in parts:
        if not part:
            continue
        sub_clauses = re.split(r"[,，、]", part)
        valid_sub = []
        for sub in sub_clauses:
            s = sub.strip()
            if not s:
                continue
            for marker in ("避免", "不要", "不准", "禁止"):
                if marker in s:
                    s = s.split(marker, 1)[0]
            s = re.sub(r"无(?:写实纹理|精细材质|真实纹理)[、，]?", "", s).strip("、， ")
            if not s:
                continue
            if leakage_re.search(s):
                print(f"[GUARD] 拦截示意图具体画面内容污染: {s}")
                continue
            valid_sub.append(s)
        if valid_sub:
            cleaned.append("、".join(valid_sub))
    return "；".join(cleaned)


def get_next_ids(category: str, explicit_id: str | None = None) -> tuple[str, int]:
    alias_data = json.loads(ALIAS_MAP_FILE.read_text(encoding="utf-8")) if ALIAS_MAP_FILE.exists() else {}
    legacy_map = alias_data.get("legacy_to_new", {})
    legacy_nums = [int(k) for k in legacy_map.keys() if k.isdigit()]
    next_legacy = max(legacy_nums) + 1 if legacy_nums else 1

    if explicit_id:
        return explicit_id.upper(), next_legacy

    cat_upper = category.upper()
    existing_nums = []
    for cid in legacy_map.values():
        m = re.match(rf"^{cat_upper}-(\d+)$", cid)
        if m:
            existing_nums.append(int(m.group(1)))
    next_cat_num = max(existing_nums) + 1 if existing_nums else 1
    canonical_id = f"{cat_upper}-{next_cat_num:03}"
    return canonical_id, next_legacy


def insert_style_row(canonical_id: str, source_name: str, gen_name: str, traits: str) -> None:
    content = SOURCE_MD.read_text(encoding="utf-8")
    cat = canonical_id.split("-")[0]
    
    # 查找该分类的段落位置
    cat_pattern = re.compile(rf"^##\s+{cat}\b.*?$", re.MULTILINE)
    cat_match = cat_pattern.search(content)
    if not cat_match:
        raise ValueError(f"在 styles_200_reorganized.md 中找不到分类章节: ## {cat}")
    
    # 寻找下一个 ## 章节或者文件结束
    next_section = re.search(r"^##\s+[A-Z]{2}\b", content[cat_match.end():], re.MULTILINE)
    insert_pos = cat_match.end() + next_section.start() if next_section else len(content)

    new_row = f"| {canonical_id} · {source_name} | {gen_name} | {traits} |"
    # 插入在下一个章节前的空行处
    prefix = content[:insert_pos].rstrip()
    suffix = content[insert_pos:].lstrip()
    updated_content = prefix + "\n\n" + new_row + "\n\n" + suffix

    # 更新文章顶部的总数
    alias_data = json.loads(ALIAS_MAP_FILE.read_text(encoding="utf-8"))
    new_total = len(alias_data.get("new_to_legacy", {})) + 1
    updated_content = re.sub(r"# \d+ 种人物 IP 手绘与视觉风格库", f"# {new_total} 种人物 IP 手绘与视觉风格库", updated_content, count=1)
    
    SOURCE_MD.write_text(updated_content, encoding="utf-8")


def main() -> None:
    args = parse_args()
    raw_text = args.traits_file.read_text(encoding="utf-8") if args.traits_file and args.traits_file.is_file() else args.traits
    traits = " ".join(raw_text.split()) if args.raw_traits else positive_traits(raw_text)

    canonical_id, next_legacy = get_next_ids(args.category, args.style_id)
    cat = canonical_id.split("-")[0]
    legacy_str = f"{next_legacy:03}"

    record = {
        "number": canonical_id,
        "legacy_number": legacy_str,
        "source_name": args.source_name,
        "generation_name": args.generation_name,
        "traits": traits,
        "name_activation": "weak" if traits else "strong",
        "traits_activation": "strong" if traits else "none",
        "use_reference_image": False,
    }

    if args.dry_run:
        print(json.dumps(record, ensure_ascii=False))
        return

    if not args.image or not args.image.is_file():
        raise SystemExit(f"代表图不存在: {args.image}")

    # 1. 复制/转换单图到 images/individual/{cat}/{canonical_id}.webp (512x512)
    dest_dir = ROOT / "images" / "individual" / cat
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_tile = dest_dir / f"{canonical_id}.webp"
    create_numbered_tile(args.image, canonical_id, dest_tile)
    print(f"✅ 生成单图 WebP: {dest_tile}")

    # 2. 更新 styles_200_reorganized.md
    insert_style_row(canonical_id, args.source_name, args.generation_name, traits)
    print(f"✅ 已更新 styles_200_reorganized.md ({canonical_id})")

    # 3. 更新 style_alias_map.json
    alias_data = json.loads(ALIAS_MAP_FILE.read_text(encoding="utf-8"))
    alias_data["legacy_to_new"][legacy_str] = canonical_id
    alias_data["new_to_legacy"][canonical_id] = legacy_str
    ALIAS_MAP_FILE.write_text(json.dumps(alias_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"✅ 已更新 style_alias_map.json ({legacy_str} <-> {canonical_id})")

    # 4. 更新 model_capabilities.json
    if MODEL_CAP.is_file():
        cap_data = json.loads(MODEL_CAP.read_text(encoding="utf-8"))
        gpt_styles = cap_data.get("models", {}).get("gpt-image-2", {}).setdefault("styles", {})
        gpt_styles[canonical_id] = {
            "name_activation": record["name_activation"],
            "traits_activation": record["traits_activation"],
        }
        MODEL_CAP.write_text(json.dumps(cap_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"✅ 已更新 model_capabilities.json ({canonical_id})")

    # 5. 生成雪碧图
    sheet_dest = append_style(next_legacy)
    print(f"✅ 已更新雪碧图: {sheet_dest}")

    # 6. 更新 README 和 MANIFEST
    update_readme_and_skill(legacy_str)
    update_manifest(legacy_str)
    print(f"✅ 已更新 README 与 MANIFEST ({legacy_str})")

    # 7. 全量构建与校验
    print("🔄 正在运行全量构建与严格校验...")
    rebuild_and_validate()
    print("🎉 全量构建与校验通过！")

    # 8. 输出标准结果供 orchestrator 提取
    res_payload = {
        **record,
        "single_path": str(dest_tile),
        "sheet_path": str(sheet_dest),
    }
    print(f"HANDRAW_RESULT={json.dumps(res_payload, ensure_ascii=False)}")


if __name__ == "__main__":
    main()
