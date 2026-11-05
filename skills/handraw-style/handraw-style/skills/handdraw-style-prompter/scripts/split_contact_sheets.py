#!/usr/bin/env python3
"""Split every numbered contact sheet into individual numbered WebP images.

Applies precision grid cropping tailored to each sheet's specific layout:
- Standard 1254x1254 sheets: 4x4 uniform cells with safe insets (no outer frames, no divider lines).
- B_036-048: Rows 0-1 are 4 columns; Row 2 has 5 columns (styles 044-048).
- B_049-054: Rows 0-1 (6 styles), with adjusted outer borders.
- C_071-082: Rows 0-2 (12 styles), with adjusted outer borders.
- D_115-123: Top banner offset (y=84), 4 columns, 3 rows (styles 115-123).
- E_124-139: Top banner offset (y=95), 4 columns, 4 card rows (styles 124-139).
- F_187-200: Rows 0-3 (14 styles), with adjusted outer borders.
- G_201-216: Top banner offset (y=96), 4 columns, 4 card rows (styles 201-216).
Only operates on legacy contact sheets [A-G]_*.webp (styles 001-216).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
import sys

from PIL import Image

ROOT = Path(__file__).resolve().parents[3]
if str(Path(__file__).resolve().parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
from style_asset_paths import single_path

SHEET = re.compile(r"^([A-G])_(\d{3})(?:-(\d{3}))?\.webp$")

# Standard 1254x1254 coordinates with safe clearance from border frames and dividers
COLS_STD_SAFE = [(8, 310), (319, 621), (632, 934), (945, 1246)]
ROWS_STD_SAFE = [(8, 310), (319, 621), (632, 934), (945, 1246)]

# B_036-048 coordinates
B_COLS_R01 = [(8, 337), (346, 635), (644, 928), (937, 1246)]
B_ROWS_R01 = [(8, 335), (342, 641)]
B_COLS_R2 = [(6, 318), (326, 522), (531, 724), (733, 937), (946, 1248)]
B_ROW_R2 = (648, 955)

# B_049-054 coordinates
B49_COLS = [(10, 310), (320, 621), (633, 934), (945, 1243)]
B49_ROWS = [(10, 310), (320, 621)]

# C_071-082 coordinates
C71_COLS = [(10, 310), (324, 621), (633, 934), (945, 1246)]
C71_ROWS = [(8, 310), (320, 619), (633, 934)]

# D_115-123 coordinates (header banner at y: 0..81)
D_COLS = [(21, 320), (326, 625), (631, 930), (937, 1233)]
D_ROWS = [(84, 400), (407, 745), (752, 1057)]

# E_124-139 coordinates (header banner at y: 0..92)
E_COLS = [(15, 333), (343, 649), (659, 966), (975, 1295)]
E_ROWS = [(95, 355), (368, 623), (632, 886), (894, 1179)]

# F_187-200 coordinates
F187_COLS = [(10, 310), (320, 619), (633, 934), (945, 1243)]
F187_ROWS = [(9, 310), (320, 621), (633, 934), (945, 1240)]

# G_201-216 coordinates (header banner at y: 0..61)
G_COLS = [(7, 255), (257, 510), (512, 764), (766, 1017)]
G_ROWS = [(62, 278), (280, 500), (502, 742), (744, 1005)]



def get_style_bounds(sheet_name: str, offset: int) -> tuple[int, int, int, int]:
    if sheet_name.startswith("B_036-048"):
        if offset < 4:
            return B_COLS_R01[offset][0], B_ROWS_R01[0][0], B_COLS_R01[offset][1], B_ROWS_R01[0][1]
        elif offset < 8:
            c = offset - 4
            return B_COLS_R01[c][0], B_ROWS_R01[1][0], B_COLS_R01[c][1], B_ROWS_R01[1][1]
        else:
            c = offset - 8
            return B_COLS_R2[c][0], B_ROW_R2[0], B_COLS_R2[c][1], B_ROW_R2[1]

    elif sheet_name.startswith("B_049-054"):
        r, c = divmod(offset, 4)
        return B49_COLS[c][0], B49_ROWS[r][0], B49_COLS[c][1], B49_ROWS[r][1]

    elif sheet_name.startswith("C_071-082"):
        r, c = divmod(offset, 4)
        return C71_COLS[c][0], C71_ROWS[r][0], C71_COLS[c][1], C71_ROWS[r][1]

    elif sheet_name.startswith("D_115-123"):
        r, c = divmod(offset, 4)
        return D_COLS[c][0], D_ROWS[r][0], D_COLS[c][1], D_ROWS[r][1]

    elif sheet_name.startswith("E_124-139"):
        r, c = divmod(offset, 4)
        return E_COLS[c][0], E_ROWS[r][0], E_COLS[c][1], E_ROWS[r][1]

    elif sheet_name.startswith("F_187-200"):
        r, c = divmod(offset, 4)
        return F187_COLS[c][0], F187_ROWS[r][0], F187_COLS[c][1], F187_ROWS[r][1]

    elif sheet_name.startswith("G_201-216"):
        r, c = divmod(offset, 4)
        return G_COLS[c][0], G_ROWS[r][0], G_COLS[c][1], G_ROWS[r][1]

    else:
        r, c = divmod(offset, 4)
        return COLS_STD_SAFE[c][0], ROWS_STD_SAFE[r][0], COLS_STD_SAFE[c][1], ROWS_STD_SAFE[r][1]


def split_sheet(path: Path) -> int:
    match = SHEET.match(path.name)
    if not match:
        return 0
    start = int(match.group(2))
    end = int(match.group(3)) if match.group(3) else start
    count = end - start + 1
    with Image.open(path) as image:
        image = image.convert("RGB")
        for offset in range(count):
            x0, y0, x1, y1 = get_style_bounds(path.name, offset)
            target = single_path(start + offset)
            target.parent.mkdir(parents=True, exist_ok=True)
            cropped = image.crop((x0, y0, x1, y1))
            if path.name.startswith("G_"):
                cropped = cropped.resize((512, 512), Image.Resampling.LANCZOS)
            temp_target = target.with_suffix(".tmp.webp")
            cropped.save(temp_target, "WEBP", quality=92, method=6)
            temp_target.replace(target)
    return count


def main() -> None:
    total = sum(split_sheet(path) for path in sorted((ROOT / "images").glob("[A-G]_*.webp")))
    print(f"Split {total} numbered tiles (001-216) into individual WebP assets.")


if __name__ == "__main__":
    main()
