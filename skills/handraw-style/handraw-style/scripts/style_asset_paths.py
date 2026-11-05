"""Canonical paths for categorized and numbered style-generation assets."""
from __future__ import annotations

import json
import re
from pathlib import Path

# Locate root directory
ROOT = Path(__file__).resolve().parents[1]
if not (ROOT / "images" / "individual").exists():
    for p in Path(__file__).resolve().parents:
        if (p / "images" / "individual").exists():
            ROOT = p
            break

INDIVIDUAL_ROOT = ROOT / "images" / "individual"
ALIAS_MAP_FILE = ROOT / "skills" / "handdraw-style-prompter" / "references" / "style_alias_map.json"

_ALIAS_CACHE: dict[str, str] | None = None


def get_alias_map() -> dict[str, str]:
    global _ALIAS_CACHE
    if _ALIAS_CACHE is None:
        if ALIAS_MAP_FILE.exists():
            try:
                data = json.loads(ALIAS_MAP_FILE.read_text(encoding="utf-8"))
                _ALIAS_CACHE = data.get("legacy_to_new", {})
            except Exception:
                _ALIAS_CACHE = {}
        else:
            _ALIAS_CACHE = {}
    return _ALIAS_CACHE


def canonical_style_id(identifier: str | int) -> str:
    """Normalize any style identifier (legacy '001', '240' or new 'FA-001', 'fa-1') to canonical form (e.g. 'FA-001')."""
    raw = str(identifier).strip()
    if raw.isdigit():
        num_str = f"{int(raw):03}"
        alias_map = get_alias_map()
        if num_str in alias_map:
            return alias_map[num_str]
        return num_str

    m = re.match(r"^([A-Za-z]{2})[-_]?(\d+)$", raw)
    if m:
        cat = m.group(1).upper()
        num = int(m.group(2))
        return f"{cat}-{num:03}"

    return raw.upper()


def category_name(identifier: str | int) -> str:
    canonical = canonical_style_id(identifier)
    if "-" in canonical:
        return canonical.split("-")[0]
    return "FA"


def asset_dir(identifier: str | int) -> Path:
    cat = category_name(identifier)
    return INDIVIDUAL_ROOT / cat


def single_path(identifier: str | int) -> Path:
    canonical = canonical_style_id(identifier)
    return asset_dir(canonical) / f"{canonical}.webp"


def grid_path(identifier: str | int) -> Path:
    canonical = canonical_style_id(identifier)
    return asset_dir(canonical) / f"{canonical}_grid.webp"


def number_value(number: str | int) -> int:
    canonical = canonical_style_id(number)
    if "-" in canonical:
        return int(canonical.split("-")[1])
    return int(number)


def bucket_name(number: str | int) -> str:
    return category_name(number)
