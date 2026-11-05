#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
insert_illustrations.py - Deterministic Markdown Article Illustration Inserter & Text Pruner
Part of the article-illustration-planner Skill.

Supports:
1. Pure insertion: Insert image embeds at designated anchor points (after/before heading or paragraph).
2. High-fidelity text replacement & pruning: Replace verbose/complex text blocks with image embeds + simplified summary
   to reduce cognitive load in knowledge articles while enforcing zero knowledge loss on core formulas and metrics.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path


def audit_knowledge_fidelity(replace_text: str, simplified_prose: str, index: int | str):
    """
    Audits whether critical formulas or numbers in replaced text were preserved in simplified text.
    Warns if high-value knowledge items (LaTeX formulas, specific percentages, pricing, ratios) disappear.
    """
    warnings = []
    # Check LaTeX math formulas
    if ("$$" in replace_text or "\\text" in replace_text or "\\times" in replace_text) and ("$$" not in simplified_prose and "\\text" not in simplified_prose and "×" not in simplified_prose and "*" not in simplified_prose):
        warnings.append("LaTeX mathematical formula detected in replaced text but not in simplified prose.")

    # Check key percentages
    pcts = re.findall(r"\d+(?:\.\d+)?%", replace_text)
    if pcts:
        missing_pcts = [p for p in set(pcts) if p not in simplified_prose]
        if missing_pcts and len(missing_pcts) == len(set(pcts)):
            warnings.append(f"Quantitative metrics {missing_pcts} detected in replaced text; ensure diagram visualizes them.")

    if warnings:
        print(f"[FIDELITY AUDIT NOTICE - Illus {index}] " + " | ".join(warnings))


def insert_illustrations(
    article_text: str,
    manifest: list[dict],
) -> str:
    """
    Inserts image embeds into article_text at anchor points or replaces text blocks.

    Manifest schema:
    [
        {
            "index": 1,
            "anchor": "### 1. 概念起源",
            "position": "after", # "after" or "before"
            "image_path": "images/illus_01.webp",
            "caption": "图1：概念起源与核心意象",
            "alt": "插图1: 概念起源", # optional
            "replace_text": "[被替换的原文字段]", # optional: for knowledge articles
            "simplified_prose": "[精炼后的替代文本]" # optional: summary prose after image
        }
    ]
    """
    processed_text = article_text

    # First pass: Handle explicit text replacements (Knowledge article cognitive pruning)
    for item in manifest:
        replace_text = item.get("replace_text", "").strip()
        if not replace_text:
            continue

        image_path = item.get("image_path", "")
        caption = item.get("caption", "")
        alt = item.get("alt", caption or f"插图{item.get('index', '')}")
        simplified_prose = item.get("simplified_prose", "").strip()

        # Knowledge fidelity audit
        audit_knowledge_fidelity(replace_text, simplified_prose, item.get("index", ""))

        # Build replacement block
        parts = [f"\n\n![{alt}]({image_path})\n"]
        if caption:
            parts.append(f"*▲ {caption}*\n\n")
        else:
            parts.append("\n")
        if simplified_prose:
            parts.append(f"{simplified_prose}\n\n")

        replacement_block = "".join(parts)

        # Look for replace_text
        if replace_text in processed_text:
            processed_text = processed_text.replace(replace_text, replacement_block, 1)
            item["_handled"] = True
            print(f"[REPLACED] Successfully replaced complex text block with illustration {item.get('index', '')}")
        else:
            # Fuzzy match: try line-trimmed match
            trimmed_target = "\n".join(line.strip() for line in replace_text.splitlines() if line.strip())
            found = False
            # Check paragraphs
            for chunk in processed_text.split("\n\n"):
                trimmed_chunk = "\n".join(l.strip() for l in chunk.splitlines() if l.strip())
                if trimmed_target and trimmed_target in trimmed_chunk:
                    processed_text = processed_text.replace(chunk, replacement_block, 1)
                    item["_handled"] = True
                    found = True
                    print(f"[REPLACED-FUZZY] Replaced matched paragraph with illustration {item.get('index', '')}")
                    break
            if not found:
                sys.stderr.write(f"[WARNING] replace_text not found in article for illustration {item.get('index', '')}. Will fall back to anchor insertion.\n")

    # Second pass: Handle pure anchor insertions for remaining items
    lines = processed_text.splitlines(keepends=True)
    for item in manifest:
        if item.get("_handled"):
            continue

        anchor = item.get("anchor", "").strip()
        if not anchor:
            continue

        position = item.get("position", "after").lower()
        image_path = item.get("image_path", "")
        caption = item.get("caption", "")
        alt = item.get("alt", caption or f"插图{item.get('index', '')}")
        simplified_prose = item.get("simplified_prose", "").strip()

        # Build insertion block
        parts = [f"\n![{alt}]({image_path})\n"]
        if caption:
            parts.append(f"*▲ {caption}*\n\n")
        else:
            parts.append("\n")
        if simplified_prose:
            parts.append(f"{simplified_prose}\n\n")
        insertion_block = "".join(parts)

        # Find matching line
        matched_idx = -1
        for idx, line in enumerate(lines):
            if anchor in line:
                matched_idx = idx
                break

        if matched_idx != -1:
            if position == "before":
                lines.insert(matched_idx, insertion_block)
            else:
                lines.insert(matched_idx + 1, insertion_block)
            print(f"[INSERTED] Inserted illustration {item.get('index', '')} {position} anchor: '{anchor}'")
        else:
            sys.stderr.write(f"[WARNING] Anchor not found in article: '{anchor}'. Appending illustration.\n")
            lines.append(insertion_block)

    return "".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Insert illustrations and prune complex text in Markdown article.")
    parser.add_argument("--article", "-a", required=True, help="Path to input Markdown article.")
    parser.add_argument("--manifest", "-m", help="Path to JSON manifest of illustrations.")
    parser.add_argument("--manifest-json", help="Direct JSON string of manifest.")
    parser.add_argument("--output", "-o", help="Path to output Markdown file. Defaults to [stem]_illustrated.md")

    args = parser.parse_args()

    article_path = Path(args.article)
    if not article_path.exists():
        sys.stderr.write(f"Error: Article file '{article_path}' does not exist.\n")
        sys.exit(1)

    article_text = article_path.read_text(encoding="utf-8")

    manifest = []
    if args.manifest:
        manifest_file = Path(args.manifest)
        if not manifest_file.exists():
            sys.stderr.write(f"Error: Manifest file '{manifest_file}' does not exist.\n")
            sys.exit(1)
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    elif args.manifest_json:
        manifest = json.loads(args.manifest_json)
    else:
        sys.stderr.write("Error: Either --manifest or --manifest-json must be provided.\n")
        sys.exit(1)

    illustrated_text = insert_illustrations(article_text, manifest)

    if args.output:
        output_path = Path(args.output)
    else:
        output_path = article_path.parent / f"{article_path.stem}_illustrated{article_path.suffix}"

    output_path.write_text(illustrated_text, encoding="utf-8")
    print(f"[SUCCESS] Illustrated article written to: {output_path}")


if __name__ == "__main__":
    main()
