#!/usr/bin/env python3
"""
scripts/patch_image_numbers.py

Precision in-place background-matching patch script to eliminate style numbers from all 280 thumbnails in images/individual/.
Strict Rules:
- No CSS cropping.
- No AI inpainting.
- In-place patching ONLY: Never overwrite or pull from downloads/ or _grid.webp (prevents reverting user-replaced styles like 240, 251, 257, 259, 260, etc.).
- Covers numbers using ultra-precise bounding boxes filled with matching local background color.
- Strictly bounds patch width and height to never touch author names, titles, or line 2 text.
- 124-139: Strictly (0, 0, 46, 25) so it covers only the 3 digits and leaves line 1 names and line 2 titles 100% intact.
- 140-154: Strictly (120, 254, 178, 277) covering centered digits in white banner without touching artwork or line 2 title.
- 187-200: Strictly bounds y <= 28 (and y <= 15 for 199-200) so artwork and line 2 are never clipped.
- 201-216: Dynamically detects digit bounds inside cloud badge and fills with sampled cloud background color.
- 217-280: Dynamically detects digits inside badge (12..56, 10..34) and covers strictly with white, leaving @handle, borders, and all user-replaced styles (240, 251, etc.) 100% intact.
- Backs up originals before making any changes.
- Provides --restore and --dry-run flags.
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path
from PIL import Image
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
INDIVIDUAL_DIR = ROOT / "images" / "individual"
BACKUP_DIR = ROOT / "images" / "individual_backup"


def get_image_path(num: int) -> Path:
    bucket = "001-200" if num <= 200 else "201-400"
    return INDIVIDUAL_DIR / bucket / f"{num:03d}.webp"


def backup_images(force: bool = False) -> None:
    if BACKUP_DIR.exists() and not force:
        print(f"[Backup] Backup directory already exists at {BACKUP_DIR}. Skipping copy.")
        return
    print(f"[Backup] Creating backup of images/individual at {BACKUP_DIR}...")
    if BACKUP_DIR.exists():
        shutil.rmtree(BACKUP_DIR)
    shutil.copytree(INDIVIDUAL_DIR, BACKUP_DIR)
    print("[Backup] Backup completed successfully.")


def restore_images() -> None:
    if not BACKUP_DIR.exists():
        print(f"[Restore Error] Backup directory {BACKUP_DIR} does not exist!")
        sys.exit(1)
    print(f"[Restore] Restoring images from {BACKUP_DIR} to {INDIVIDUAL_DIR}...")
    for p in BACKUP_DIR.glob("*/*.webp"):
        rel = p.relative_to(BACKUP_DIR)
        dest = INDIVIDUAL_DIR / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
    print("[Restore] All original images restored successfully.")


def fill_rect(image: Image.Image, x0: int, y0: int, x1: int, y1: int, color: tuple[int, int, int]) -> None:
    w, h = image.size
    cx0 = max(0, min(w, x0))
    cy0 = max(0, min(h, y0))
    cx1 = max(0, min(w, x1))
    cy1 = max(0, min(h, y1))
    for y in range(cy0, cy1):
        for x in range(cx0, cx1):
            image.putpixel((x, y), color)


def patch_single_image(num: int, dry_run: bool = False) -> tuple[bool, str]:
    path = get_image_path(num)
    if not path.exists():
        return False, f"File {path} not found"

    with Image.open(path) as img:
        im = img.convert("RGB")
    w, h = im.size
    arr = np.array(im)
    method_desc = ""

    # 1. Sheet A1 (001-016): Top-left "001 Gemma Correll"
    if 1 <= num <= 16:
        fill_rect(im, 0, 0, 46, 25, (255, 255, 255))
        method_desc = "White patch top-left digits (0,0,46,25)"

    # 2. Sheet A2 (017-032): Top-left pink circle & number
    elif 17 <= num <= 32:
        fill_rect(im, 0, 0, 48, 48, (255, 255, 255))
        method_desc = "White patch pink circle (0,0,48,48)"

    # 3. Sheet A3 (033-035): Top-left "033 — ..."
    elif 33 <= num <= 35:
        if num == 34:
            fill_rect(im, 0, 0, 54, 25, (255, 255, 255))
        else:
            fill_rect(im, 0, 0, 48, 25, (255, 255, 255))
        method_desc = "White patch top-left digits"

    # 4. Sheet B1 (036-048)
    elif 36 <= num <= 48:
        if 36 <= num <= 39:
            fill_rect(im, 0, 0, 48, 22, (255, 255, 255))
            fill_rect(im, 0, 290, w, h, (255, 255, 255))
            method_desc = "White patch top digits (0,0,48,22) & bottom bleed"
        elif 40 <= num <= 43:
            fill_rect(im, 0, 0, w, 16, (255, 255, 255))
            fill_rect(im, 0, 290, w, h, (255, 255, 255))
            method_desc = "Clean top cut-off & bottom bleed"
        else: # 44..48
            fill_rect(im, 0, 0, 48, 22, (255, 255, 255))
            method_desc = "White patch top digits (0,0,48,22)"

    # 5. Sheet B2 (049-054): Already clean art
    elif 49 <= num <= 54:
        method_desc = "Clean art, no patch needed"

    # 6. Sheet C1 (055-070): Top-left "055 — ..."
    elif 55 <= num <= 70:
        fill_rect(im, 0, 0, 46, 25, (255, 255, 255))
        method_desc = "White patch top-left digits (0,0,46,25)"

    # 7. Sheet C2 (071-082): Top-left "Cxx"
    elif 71 <= num <= 82:
        if 71 <= num <= 74:
            fill_rect(im, 0, 0, 75, 38, (255, 255, 255))
        elif 75 <= num <= 78:
            fill_rect(im, 0, 0, 75, 30, (255, 255, 255))
        else: # 79..82
            fill_rect(im, 0, 0, 75, 33, (255, 255, 255))
        method_desc = "White patch top-left Cxx"

    # 8. Sheet D1 (083-098): Top-left "083" (ends at x=55, y=25. Line 2 starts at y=36)
    elif 83 <= num <= 98:
        fill_rect(im, 0, 0, 56, 28, (255, 255, 255))
        method_desc = "White patch top-left (0,0,56,28)"

    # 9. Sheet D2 (099-114): Top-left "099 — ..."
    elif 99 <= num <= 114:
        fill_rect(im, 0, 0, 46, 25, (255, 255, 255))
        method_desc = "White patch top-left digits (0,0,46,25)"

    # 10. Sheet D3 (115-123): Top-center "D115"
    elif 115 <= num <= 123:
        fill_rect(im, 80, 0, 220, 24, (255, 255, 255))
        method_desc = "White patch top-center (80,0,220,24)"

    # 11. Sheet E1 (124-139): Top-left "124"
    # Digits end at x <= 45, next word on line 1 starts at x >= 57, line 2 starts at y >= 30.
    # Strictly (0, 0, 46, 25) guarantees zero text clipping!
    elif 124 <= num <= 139:
        fill_rect(im, 0, 0, 46, 25, (255, 255, 255))
        method_desc = "White patch top-left digits (0,0,46,25)"

    # 12. Sheet E2 (140-154): Bottom banner line 1 centered digits "140"
    # Centered digits strictly within x: 125..175, y: 255..275.
    # Artwork above ends at y <= 253, title below starts at y >= 278.
    elif 140 <= num <= 154:
        fill_rect(im, 120, 254, 178, 277, (255, 255, 255))
        method_desc = "White patch bottom banner centered digits (120,254,178,277)"

    # 13. Sheet F1 (155-170): Top-left "155 ..."
    elif 155 <= num <= 170:
        fill_rect(im, 0, 0, 48, 25, (255, 255, 255))
        method_desc = "White patch top-left digits (0,0,48,25)"

    # 14. Sheet F2 (171-186): Top-left "171 ..."
    elif 171 <= num <= 186:
        fill_rect(im, 0, 0, 48, 25, (255, 255, 255))
        method_desc = "White patch top-left digits (0,0,48,25)"

    # 15. Sheet F3 (187-200): Top-left "187"
    elif 187 <= num <= 200:
        if 187 <= num <= 198:
            fill_rect(im, 0, 0, 48, 28, (255, 255, 255))
            method_desc = "White patch top-left digits (0,0,48,28)"
        else: # 199, 200
            fill_rect(im, 0, 0, 48, 15, (255, 255, 255))
            method_desc = "White patch top-left digits (0,0,48,15)"

    # 16. Sheet G (201-216): Chinese illustrations, cloud badge with digits
    elif 201 <= num <= 216:
        dark_pixels = []
        for y in range(16, 60):
            for x in range(18, 95):
                if np.mean(arr[y, x]) < 180:
                    dark_pixels.append((x, y))
        if dark_pixels:
            min_x = max(0, min(p[0] for p in dark_pixels) - 2)
            max_x = min(w, max(p[0] for p in dark_pixels) + 3)
            min_y = max(0, min(p[1] for p in dark_pixels) - 2)
            max_y = min(h, max(p[1] for p in dark_pixels) + 3)
            # Sample ring around digit box in cloud
            ring = []
            for y in range(max(0, min_y - 4), min(h, max_y + 4)):
                for x in range(max(0, min_x - 4), min(w, max_x + 4)):
                    if (x < min_x or x >= max_x or y < min_y or y >= max_y) and np.mean(arr[y, x]) > 220:
                        ring.append(arr[y, x])
            c = tuple(np.mean(ring, axis=0).astype(int)) if ring else (245, 245, 245)
            fill_rect(im, min_x, min_y, max_x, max_y, (int(c[0]), int(c[1]), int(c[2])))
            method_desc = f"Sampled cloud patch ({min_x},{min_y})-({max_x},{max_y}) with {c}"
        else:
            method_desc = "No digits found in cloud"

    # 17. Range 217-280 (Sheet H): In-place precision badge patch
    # Dynamically detects digits inside x: 12..56 (or 70 for #257), y: 10..34 and fills with white.
    # Leaves pill border, @handle, and all user replaced styles (240, 251, 257, 259, 260, etc.) 100% intact.
    elif 217 <= num <= 280:
        dark_pixels = []
        limit_x = 70 if num == 257 else 56
        for y in range(10, 34):
            for x in range(12, limit_x):
                if np.mean(arr[y, x]) < 180:
                    dark_pixels.append((x, y))
        if dark_pixels:
            min_x = max(8, min(p[0] for p in dark_pixels) - 2)
            max_x = min(limit_x, max(p[0] for p in dark_pixels) + 3)
            min_y = max(8, min(p[1] for p in dark_pixels) - 2)
            max_y = min(36, max(p[1] for p in dark_pixels) + 3)
            fill_rect(im, min_x, min_y, max_x, max_y, (255, 255, 255))
            method_desc = f"White patch digits inside badge ({min_x},{min_y})-({max_x},{max_y})"
        else:
            method_desc = "No digits found in badge area"

    if not dry_run and method_desc != "Clean art, no patch needed":
        im.save(path, format="WEBP", quality=92, method=6)

    return True, method_desc


def main() -> None:
    parser = argparse.ArgumentParser(description="Precision patch style numbers on all thumbnails.")
    parser.add_argument("--restore", action="store_true", help="Restore all images from backup.")
    parser.add_argument("--dry-run", action="store_true", help="Preview operations without saving.")
    parser.add_argument("--force-backup", action="store_true", help="Overwrite existing backup.")
    parser.add_argument("--range", type=str, default="1-280", help="Range of styles to process (e.g. 1-280).")
    args = parser.parse_args()

    if args.restore:
        restore_images()
        return

    backup_images(force=args.force_backup)

    if "-" in args.range:
        start_s, end_s = args.range.split("-")
        start_num, end_num = int(start_s), int(end_s)
    else:
        start_num = end_num = int(args.range)

    print(f"[Processing] Patching numbers for styles {start_num:03d} to {end_num:03d} (dry_run={args.dry_run})...")
    processed = 0
    for num in range(start_num, end_num + 1):
        ok, desc = patch_single_image(num, dry_run=args.dry_run)
        if ok:
            processed += 1
            if num % 20 == 0 or num == end_num or num == start_num:
                print(f"  Style #{num:03d}: {desc}")

    print(f"[Complete] Successfully processed {processed} images.")


if __name__ == "__main__":
    main()
