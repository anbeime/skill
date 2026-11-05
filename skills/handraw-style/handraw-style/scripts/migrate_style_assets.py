#!/usr/bin/env python3
"""Move numbered style assets into 200-style buckets and clean known duplicates."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from pathlib import Path

from style_asset_paths import INDIVIDUAL_ROOT, ROOT, grid_path, single_path


STYLES = ROOT / "skills" / "handdraw-style-prompter" / "references" / "styles.json"
LEGACY_ARCHIVE = ROOT / "downloads" / "legacy" / "217"
KNOWN_DUPLICATES = {
    ROOT / "images" / "sref_2365155667_512.webp": single_path(217),
    ROOT / "images" / "sref_2365155667_grid.webp": grid_path(217),
}
LEGACY_ORIGINAL = INDIVIDUAL_ROOT / "sref_2365155667.webp"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def move_asset(source: Path, target: Path, dry_run: bool) -> None:
    if not source.exists():
        return
    if target.exists():
        if digest(source) != digest(target):
            raise RuntimeError(f"Refusing to overwrite different asset: {target}")
        print(f"Duplicate canonical asset already present: {source.name}")
        if not dry_run:
            source.unlink()
        return
    print(f"Move {source.relative_to(ROOT)} -> {target.relative_to(ROOT)}")
    if not dry_run:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print planned changes without moving or deleting files.")
    args = parser.parse_args()

    styles = json.loads(STYLES.read_text(encoding="utf-8"))
    for number in range(1, len(styles) + 1):
        formatted = f"{number:03}"
        move_asset(INDIVIDUAL_ROOT / f"{formatted}.webp", single_path(number), args.dry_run)
        move_asset(INDIVIDUAL_ROOT / f"{formatted}_grid.webp", grid_path(number), args.dry_run)

    for duplicate, canonical in KNOWN_DUPLICATES.items():
        if not duplicate.exists():
            continue
        verification_target = canonical
        if not verification_target.exists() and args.dry_run:
            verification_target = INDIVIDUAL_ROOT / canonical.name
        if not verification_target.exists():
            raise RuntimeError(f"Cannot verify duplicate without canonical asset: {canonical}")
        if digest(duplicate) != digest(verification_target):
            raise RuntimeError(f"Refusing to delete non-identical duplicate: {duplicate}")
        print(f"Delete verified duplicate: {duplicate.relative_to(ROOT)}")
        if not args.dry_run:
            duplicate.unlink()

    if LEGACY_ORIGINAL.exists():
        target = LEGACY_ARCHIVE / LEGACY_ORIGINAL.name
        print(f"Archive legacy original: {LEGACY_ORIGINAL.relative_to(ROOT)} -> {target.relative_to(ROOT)}")
        if not args.dry_run:
            LEGACY_ARCHIVE.mkdir(parents=True, exist_ok=True)
            if target.exists() and digest(target) != digest(LEGACY_ORIGINAL):
                raise RuntimeError(f"Refusing to overwrite different archived original: {target}")
            if not target.exists():
                shutil.move(str(LEGACY_ORIGINAL), str(target))
            else:
                LEGACY_ORIGINAL.unlink()


if __name__ == "__main__":
    main()
