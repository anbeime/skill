#!/usr/bin/env python3
"""
optimize_images.py - Optimize and compress oversized images in the repository.

Targets:
1. WebP images > 200KB: Re-compress with high-quality lossy WebP (quality=85, method=6)
   if it yields at least a 10% reduction.
2. Large PNG files (such as wechat_personal.png): Compress with palette/optimization.
"""
from __future__ import annotations

import io
import os
import subprocess
import sys
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]


def get_tracked_images() -> list[Path]:
    res = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=ROOT,
        check=True,
        capture_output=True,
    )
    files = [p for p in res.stdout.decode("utf-8").split("\0") if p]
    extensions = (".webp", ".png", ".jpg", ".jpeg")
    return [
        ROOT / f for f in files
        if f.lower().endswith(extensions)
        and (f.startswith("images/") or f.startswith("skills/handdraw-style-prompter/"))
        and (ROOT / f).is_file()
    ]


def optimize_webp(path: Path) -> tuple[int, int] | None:
    orig_size = path.stat().st_size
    if orig_size < 150 * 1024:  # Under 150KB is already compact
        return None

    try:
        im = Image.open(path)
        # Keep transparency if RGBA
        save_mode = im.mode
        if save_mode not in ("RGB", "RGBA"):
            save_mode = "RGBA" if "A" in im.mode or "transparency" in im.info else "RGB"
            im = im.convert(save_mode)

        buf = io.BytesIO()
        im.save(buf, "WEBP", quality=85, method=6)
        new_data = buf.getvalue()
        new_size = len(new_data)

        if new_size < orig_size * 0.90:  # At least 10% smaller
            path.write_bytes(new_data)
            return orig_size, new_size
    except Exception as e:
        print(f"Error optimizing {path}: {e}")
    return None


def optimize_png(path: Path) -> tuple[int, int] | None:
    orig_size = path.stat().st_size
    if orig_size < 200 * 1024:
        return None

    try:
        im = Image.open(path)
        buf = io.BytesIO()
        # Convert to 256-color palette with transparency preserved
        if im.mode == "RGBA":
            im_p = im.convert("P", palette=Image.ADAPTIVE, colors=256)
        else:
            im_p = im.convert("RGB").convert("P", palette=Image.ADAPTIVE, colors=256)
        im_p.save(buf, "PNG", optimize=True)
        new_data = buf.getvalue()
        new_size = len(new_data)

        if new_size < orig_size * 0.90:
            path.write_bytes(new_data)
            return orig_size, new_size
    except Exception as e:
        print(f"Error optimizing {path}: {e}")
    return None


def main() -> int:
    try:
        if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
            sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

    images = get_tracked_images()
    print(f"Scanning {len(images)} tracked images for optimization...")

    optimized_count = 0
    total_saved = 0
    results = []

    for path in images:
        ext = path.suffix.lower()
        res = None
        if ext == ".webp":
            res = optimize_webp(path)
        elif ext == ".png":
            res = optimize_png(path)

        if res:
            orig_s, new_s = res
            diff = orig_s - new_s
            total_saved += diff
            optimized_count += 1
            rel_path = path.relative_to(ROOT)
            results.append((diff, orig_s, new_s, str(rel_path)))

    results.sort(reverse=True)
    print(f"\nOptimization Complete!")
    print(f"Optimized files: {optimized_count}")
    print(f"Total space saved: {total_saved / 1024 / 1024:.2f} MB\n")

    print("Top 25 largest reductions:")
    for diff, orig_s, new_s, rel in results[:25]:
        pct = (1 - new_s / orig_s) * 100
        print(f"  {orig_s/1024:6.1f} KB -> {new_s/1024:5.1f} KB (saved {diff/1024:5.1f} KB, -{pct:.1f}%): {rel}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
