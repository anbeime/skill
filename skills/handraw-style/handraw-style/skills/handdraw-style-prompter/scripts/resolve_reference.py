#!/usr/bin/env python3
"""Resolve whether a style reference image is needed for a model and style."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from style_asset_paths import grid_path, single_path

SKILL = Path(__file__).resolve().parents[1]
POLICY = SKILL / "references" / "model_capabilities.json"
STYLES = SKILL / "references" / "styles.json"
ALLOWED = {"strong", "weak", "none", "unknown"}


def load_policy() -> dict:
    return json.loads(POLICY.read_text(encoding="utf-8"))


def load_style(number: str) -> dict:
    styles = json.loads(STYLES.read_text(encoding="utf-8"))
    return next(item for item in styles if item["number"] == number)


def positive_traits(traits: str) -> str:
    if not traits:
        return ""
    parts = re.split(r"[；;。\n]+", traits)
    kept = []
    for part in parts:
        part = part.strip(" ，,、：:。；;\t")
        if not part:
            continue
        if any(word in part for word in ("避免", "不要", "不准", "禁止")):
            continue
        if re.search(r"无(?:写实纹理|精细材质|真实纹理)", part):
            continue
        kept.append(part)
    return "；".join(kept)


def get_reference_path(number: str) -> str | None:
    reference_grid = grid_path(number)
    if reference_grid.exists():
        return str(reference_grid)
    reference_single = single_path(number)
    if reference_single.exists():
        return str(reference_single)
    return None


def resolve(model: str, style: str, policy: dict | None = None) -> dict:
    styles = json.loads(STYLES.read_text(encoding="utf-8"))
    alias_file = SKILL / "references" / "style_alias_map.json"
    alias_map = json.loads(alias_file.read_text(encoding="utf-8")) if alias_file.exists() else {}
    legacy_to_new = alias_map.get("legacy_to_new", {})
    new_to_legacy = alias_map.get("new_to_legacy", {})

    style_clean = str(style).strip()
    if style_clean.isdigit():
        num_str = f"{int(style_clean):03}"
        canonical = legacy_to_new.get(num_str, num_str)
    else:
        m = re.match(r"^([A-Za-z]{2})[-_]?(\d+)$", style_clean)
        if m:
            canonical = f"{m.group(1).upper()}-{int(m.group(2)):03}"
        else:
            canonical = style_clean.upper()

    style_record = next((item for item in styles if item["number"] == canonical), None)
    if not style_record and canonical in legacy_to_new:
        canonical = legacy_to_new[canonical]
        style_record = next((item for item in styles if item["number"] == canonical), None)

    if not style_record:
        raise ValueError(f"Style '{style}' not found. Use a valid ID like FA-001 or legacy number.")

    number = canonical
    legacy_number = new_to_legacy.get(number, "")
    policy = policy or load_policy()
    fallback = dict(policy["default"])
    profile = policy.get("models", {}).get(model)
    entry = dict(fallback)
    if profile:
        entry.update({key: value for key, value in profile.items() if key != "styles"})
        style_entry = profile.get("styles", {}).get(number) or profile.get("styles", {}).get(legacy_number, {})
        entry.update(style_entry)
    name_activation = entry.get("name_activation", "unknown")
    traits_activation = entry.get("traits_activation", "unknown")
    if name_activation not in ALLOWED or traits_activation not in ALLOWED:
        raise ValueError("Invalid name_activation or traits_activation")
    keep_raw = number in ("FE-048", "FE-049", "FE-051", "FH-050", "FD-042") or legacy_number in ("240", "242", "257", "259", "260")
    traits = style_record.get("traits", "") if keep_raw else positive_traits(style_record.get("traits", ""))
    if name_activation == "strong":
        activation_source = "name+style"
        use_reference_image = False
        prompt_traits = ""
    elif traits_activation == "strong" and traits:
        activation_source = "name+style+traits"
        use_reference_image = False
        prompt_traits = traits
    else:
        use_reference_image = True
        prompt_traits = traits
        activation_source = (
            "name+style+traits+reference-image"
            if prompt_traits
            else "name+style+reference-image"
        )
    return {
        "model": model,
        "style": number,
        "name_activation": name_activation,
        "traits_activation": traits_activation,
        "activation_source": activation_source,
        "use_reference_image": use_reference_image,
        "include_prompt_traits": bool(prompt_traits),
        "prompt_traits": prompt_traits,
        "reference_path": get_reference_path(number) if use_reference_image else None,
        "note": entry.get("note", "")
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gpt-image-2", help="Target model identifier (default: gpt-image-2)")
    parser.add_argument("--style", required=True)
    args = parser.parse_args()
    print(json.dumps(resolve(args.model, args.style), ensure_ascii=False))


if __name__ == "__main__":
    main()
