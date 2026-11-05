#!/usr/bin/env python3
"""Maintain the active 4×4 H-category Tweet-style contact sheet."""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

from PIL import Image, ImageDraw

from style_asset_paths import ROOT, single_path


IMAGES = ROOT / "images"
STATE_FILE = ROOT / "skills" / "handdraw-style-prompter" / "references" / "contact_sheet_state.json"
CAPACITY = 16
SHEET_SIZE = 1254
SHEET = re.compile(r"^[GHI]_(\d{3})(?:-(\d{3}))?\.webp$")


def sheet_group(start: int) -> str:
    """Return the display category prefix for a contact sheet range."""
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


def recover_state(next_number: int) -> dict:
    """Recover the last incomplete H/I sheet when the state file is missing."""
    sheets = [(end, start, path) for path in IMAGES.glob("[HI]_*.webp")
              if (parsed := parse_sheet(path)) for start, end in [parsed]]
    if not sheets:
        return {"version": 1, "capacity": CAPACITY, "active_start": next_number,
                "filled": 0, "next_cell": 1}
    end, start, _ = max(sheets)
    filled = end - start + 1
    if filled < CAPACITY and end == next_number - 1:
        return {"version": 1, "capacity": CAPACITY, "active_start": start,
                "filled": filled, "next_cell": filled + 1}
    return {"version": 1, "capacity": CAPACITY, "active_start": next_number,
            "filled": 0, "next_cell": 1}


def next_state(number: int, state: dict | None = None) -> tuple[dict, Path | None]:
    state = state or recover_state(number)
    start = int(state["active_start"])
    filled = int(state["filled"])
    if filled >= CAPACITY:
        start, filled = number, 0
    elif number != start + filled:
        raise RuntimeError(
            f"Expected style #{start + filled:03} for the active contact sheet, got #{number:03}."
        )

    previous = sheet_path(start, start + filled - 1) if filled else None
    filled += 1
    return ({"version": 1, "capacity": CAPACITY, "active_start": start,
             "filled": filled, "next_cell": filled + 1 if filled < CAPACITY else 1}, previous)


def render_sheet(start: int, end: int, destination: Path) -> None:
    cell = round(SHEET_SIZE / 4)
    canvas = Image.new("RGB", (SHEET_SIZE, SHEET_SIZE), (250, 249, 246))
    for offset, number in enumerate(range(start, end + 1)):
        tile_path = single_path(number)
        if not tile_path.exists():
            raise RuntimeError(f"Missing numbered tile for contact sheet: {tile_path}")
        with Image.open(tile_path) as tile:
            row, column = divmod(offset, 4)
            canvas.paste(tile.convert("RGB").resize((cell, cell), Image.Resampling.LANCZOS),
                         (column * cell, row * cell))

    draw = ImageDraw.Draw(canvas)
    for index in range(1, 4):
        position = round(index * SHEET_SIZE / 4)
        draw.line([(position, 0), (position, SHEET_SIZE)], fill=(230, 226, 220), width=1)
        draw.line([(0, position), (SHEET_SIZE, position)], fill=(230, 226, 220), width=1)

    temporary = destination.with_name(f".{destination.stem}.tmp.webp")
    canvas.save(temporary, format="WEBP", quality=90, method=6)
    os.replace(temporary, destination)


def append_style(number: int) -> Path:
    state, previous = next_state(number, read_state())
    start = int(state["active_start"])
    destination = sheet_path(start, number)
    if destination.exists() and destination != previous:
        raise RuntimeError(f"Refusing to overwrite an existing contact sheet: {destination}")
    render_sheet(start, number, destination)
    write_state(state)
    if previous and previous != destination and previous.exists():
        previous.unlink()
    return destination


def repair_active_sheet(start: int, end: int) -> Path:
    if end < start or end - start + 1 > CAPACITY:
        raise ValueError("Repair range must contain 1–16 sequential styles.")
    destination = sheet_path(start, end)
    render_sheet(start, end, destination)
    state = {"version": 1, "capacity": CAPACITY, "active_start": start,
             "filled": end - start + 1,
             "next_cell": end - start + 2 if end - start + 1 < CAPACITY else 1}
    write_state(state)
    for path in IMAGES.glob("[HI]_*.webp"):
        parsed = parse_sheet(path)
        if parsed and path != destination and parsed[0] >= start and parsed[1] <= end:
            path.unlink()
    return destination


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repair", nargs=2, type=int, metavar=("START", "END"))
    args = parser.parse_args()
    if not args.repair:
        parser.error("Use --repair START END for a one-time repair.")
    result = repair_active_sheet(*args.repair)
    print(f"Rebuilt active contact sheet: {result.relative_to(ROOT)}")
