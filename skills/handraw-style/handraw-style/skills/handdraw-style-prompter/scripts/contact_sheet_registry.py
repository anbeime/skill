#!/usr/bin/env python3
"""Expose H-category contact-sheet paths to the package-local validators."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from PIL import Image, ImageDraw

from style_asset_paths import ROOT, single_path


IMAGES = ROOT / "images"
STATE_FILE = Path(__file__).resolve().parents[1] / "references" / "contact_sheet_state.json"
CAPACITY = 16
SHEET_SIZE = 1254
SHEET = re.compile(r"^[GHI]_(\d{3})(?:-(\d{3}))?\.webp$")


def sheet_group(start: int) -> str:
    if start <= 216:
        return "G"
    if start <= 331:
        return "H"
    return "I"


def sheet_path(start: int, end: int) -> Path:
    suffix = f"{start:03}" if start == end else f"{start:03}-{end:03}"
    return IMAGES / f"{sheet_group(start)}_{suffix}.webp"


def read_state() -> dict | None:
    if not STATE_FILE.exists():
        return None
    state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
    if state.get("capacity") != CAPACITY:
        raise RuntimeError(f"Unsupported contact-sheet capacity: {state.get('capacity')}")
    return state


def write_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    temporary = STATE_FILE.with_suffix(".tmp")
    temporary.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, STATE_FILE)


def parse_sheet(path: Path) -> tuple[int, int] | None:
    match = SHEET.match(path.name)
    if not match:
        return None
    start = int(match.group(1))
    return start, int(match.group(2) or start)
