"""Turn a checkerboard-painted RGB 'transparent' PNG into a real RGBA cutout.

Some image tools simulate transparency by painting a gray/white checkerboard
into the RGB pixels and returning a flat RGB PNG. Downstream AI matting then
fails to produce a clean cutout. This script detects the periodic 2-tone
checker field and converts it into a genuine alpha channel - deterministic,
no AI pass, no manual work.

Detection: the two dominant colors of the image border must form a periodic
grid (cell size 8..64 px). Conversion marks a pixel as background only when
(a) it matches the checker color predicted for its cell phase, and
(b) most of its neighbours also match their own phase colors. Guard (b) keeps
character content alive even when it shares a color with the checkerboard
(e.g. white hair over white cells).

Usage:
  python3 checkerboard_to_alpha.py <input.png> <output.png>
  python3 checkerboard_to_alpha.py --selftest

API (used by validate_assets.py):
  detect_checkerboard(image) -> dict | None
  convert_to_alpha(image) -> (RGBA Image, report dict)
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

TOL = 32          # max channel distance from the predicted checker color
MIN_SPLIT = 8     # the two checker tones must differ by at least this much
BORDER = 0.06     # border fraction used for detection
CELL_MIN, CELL_MAX = 8, 64
NEED_COVER = 0.80  # border pixels inside tolerance for a valid detection
NEED_NEIGH = 6     # of 8 neighbours that must be field-consistent


def _border_mask(h, w, frac=BORDER):
    m = np.zeros((h, w), dtype=bool)
    t = max(1, int(h * frac)); s = max(1, int(w * frac))
    m[:t] = m[-t:] = m[:, :s] = m[:, -s:] = True
    return m


def _dominant_pair(px, bmask):
    """Return (color_a, color_b) of the two dominant border tones or None."""
    q = (px[bmask] >> 3).astype(np.uint32)
    key = (q[:, 0].astype(np.uint32) << 10) | (q[:, 1] << 5) | q[:, 2]
    vals, counts = np.unique(key, return_counts=True)
    if len(vals) < 2:
        return None
    order = np.argsort(counts)[::-1][:2]
    colors = []
    for v in vals[order]:
        r, g, b = (v >> 10) & 31, (v >> 5) & 31, v & 31
        lo = np.array([r << 3, g << 3, b << 3]); hi = lo + 7
        sel = (px[bmask] >= lo).all(axis=1) & (px[bmask] <= hi).all(axis=1)
        if sel.sum() == 0:
            return None
        colors.append(px[bmask][sel].mean(axis=0))
    a, b = np.asarray(colors[0]), np.asarray(colors[1])
    if np.abs(a - b).max() < MIN_SPLIT:
        return None
    return a, b


def _best_grid(px, bmask, a, b):
    """Search cell sizes and phase assignment; return (cell, flipped, coverage).

    The true cell minimises the mean clipped distance to the phase-predicted
    tone; this stays discriminative even when the two tones are very close.
    """
    best = None
    for cell in range(CELL_MIN, CELL_MAX + 1):
        xs, ys = np.nonzero(bmask)
        phase = ((xs // cell) + (ys // cell)) & 1
        for flip in (0, 1):
            c0, c1 = (b, a) if flip else (a, b)
            pred = np.where(phase[:, None], c1, c0)
            d = np.abs(px[bmask].astype(np.int16) - pred).max(axis=1)
            score = float(np.minimum(d, 60).mean())
            if best is None or score < best[2]:
                best = (cell, flip, score)
    cell, flip, score = best
    xs, ys = np.nonzero(bmask)
    phase = ((xs // cell) + (ys // cell)) & 1
    c0, c1 = (b, a) if flip else (a, b)
    pred = np.where(phase[:, None], c1, c0)
    d = np.abs(px[bmask].astype(np.int16) - pred).max(axis=1)
    cov = float((d < TOL).mean())
    return cell, flip, cov


def detect_checkerboard(image):
    """Return detection report dict, or None when no checkerboard is found."""
    px = np.asarray(image.convert("RGB"))
    h, w = px.shape[:2]
    bmask = _border_mask(h, w)
    pair = _dominant_pair(px, bmask)
    if pair is None:
        return None
    a, b = pair
    cell, flip, cov = _best_grid(px, bmask, a, b)
    if cov < NEED_COVER:
        return None
    return {
        "cell": cell,
        "color_a": [int(v) for v in a],
        "color_b": [int(v) for v in b],
        "flipped": bool(flip),
        "coverage": round(cov, 4),
        "tone_split": int(np.abs(a - b).max()),
    }


def convert_to_alpha(image, report_in=None):
    """Convert a checkerboard RGB image to RGBA with true transparency."""
    det = report_in or detect_checkerboard(image)
    if det is None:
        raise ValueError("no checkerboard pattern detected")
    px = np.asarray(image.convert("RGB")).astype(np.int16)
    h, w = px.shape[:2]
    cell = det["cell"]
    a = np.asarray(det["color_a"])
    b = np.asarray(det["color_b"])
    if det.get("flipped"):
        a, b = b, a
    ys, xs = np.mgrid[0:h, 0:w]
    phase = ((xs // cell) + (ys // cell)) & 1
    pred = np.where(phase[..., None], b, a)

    d = np.abs(px - pred).max(axis=2)
    near = d < TOL

    # Neighbour consistency: a window ~one cell wide must be mostly
    # field-consistent. Character areas that share a checker color (white hair
    # over white cells) still contain off-phase neighbours because the window
    # spans several cells, so they are kept; real checkerboard stays consistent.
    win = cell + 1 if cell % 2 == 0 else cell
    pad = win // 2 + 1
    P = np.pad(near.astype(np.uint32), pad, mode="reflect")
    S = P.cumsum(axis=0).cumsum(axis=1)
    cnt = (S[win:win + h, win:win + w] - S[win:win + h, :w]
           - S[:h, win:win + w] + S[:h, :w]).astype(np.float64)
    background = near & (cnt >= win * win * 0.62)

    alpha = np.where(background, np.clip(d / TOL, 0.0, 1.0), 1.0)
    alpha = (alpha * 255).astype(np.uint8)
    rgba = np.dstack([np.asarray(image.convert("RGB")), alpha])
    out = Image.fromarray(rgba, "RGBA")
    report = {
        "cell": cell,
        "coverage": det["coverage"],
        "tone_split": det.get("tone_split"),
        "transparent_fraction": round(float((alpha < 8).mean()), 4),
    }
    if det.get("tone_split", 99) < 16:
        report["warning"] = (
            "checker tones are very close; subject areas sharing that tone range "
            "cannot be separated locally - inspect the result"
        )
    return out, report


def main(argv=None):
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print(__doc__)
        return 2
    src, dst = argv[0], argv[1] if len(argv) > 1 else None
    if not dst:
        dst = os.path.splitext(src)[0] + "-alpha.png"
    image = Image.open(src)
    det = detect_checkerboard(image)
    if det is None:
        print(json.dumps({"ok": False, "error": "no checkerboard detected",
                          "input": src}, ensure_ascii=False))
        return 1
    out, report = convert_to_alpha(image, det)
    out.save(dst)
    report["ok"] = True
    report["output"] = dst
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
