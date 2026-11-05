"""Regression tests for checkerboard_to_alpha.py.

Simulates the exact reported failure: an image tool returns a gray/white
checkerboard painted into RGB (no alpha channel). The converter must turn the
checker field into true transparency while keeping the character - including
white hair, which sits on top of white checker cells.

Run: python3 test_checkerboard.py
Exit code 0 = all assertions passed.
"""
import os
import sys
import tempfile

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import checkerboard_to_alpha as c2a  # noqa: E402

CELL = 16
GRAY = np.array([204, 204, 204], dtype=np.uint8)
WHITE = np.array([255, 255, 255], dtype=np.uint8)


def make_fixture(w=512, h=512):
    """Checkerboard RGB canvas with a dark body blob and a white hair patch."""
    y, x = np.mgrid[0:h, 0:w]
    phase = ((x // CELL) + (y // CELL)) & 1
    img = np.where(phase[..., None], GRAY, WHITE).astype(np.uint8)

    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    body = ((xx - 256) / 120) ** 2 + ((yy - 280) / 180) ** 2 <= 1.0
    hair = ((xx - 300) / 70) ** 2 + ((yy - 130) / 90) ** 2 <= 1.0
    img[body] = (150, 30, 30)      # dark red body
    img[hair] = (250, 250, 250)    # near-white hair (worst case for matting)
    return Image.fromarray(img, "RGB"), body, hair


def main():
    img, body, hair = make_fixture()

    det = c2a.detect_checkerboard(img)
    assert det is not None, "checkerboard must be detected"
    assert det["cell"] == CELL, f"cell size {det['cell']} != {CELL}"
    assert det["coverage"] > 0.8, f"coverage {det['coverage']} too low"

    out, report = c2a.convert_to_alpha(img)
    assert out.mode == "RGBA", f"output mode {out.mode} != RGBA"
    a = np.array(out.getchannel("A")).astype(float) / 255.0

    # 1) Pure checkerboard corner is fully transparent
    assert a[16:32, 16:32].mean() < 0.05, "checkerboard corner not transparent"

    # 2) Body center is fully opaque
    assert a[280, 256] > 0.95, "body center lost"

    # 3) White hair survives (phase + neighborhood guard protects it)
    assert a[130, 300] > 0.9, f"white hair erased: alpha={a[130, 300]:.2f}"

    # 4) No stray opaque checker lattice anywhere: background alpha is low
    bg = a.copy()
    bg[hair | body] = 0.0
    assert bg.mean() < 0.05, f"residual checker pixels: mean={bg.mean():.3f}"

    # 5) Round-trip through the CLI
    with tempfile.TemporaryDirectory() as td:
        src = os.path.join(td, "fixture.png")
        dst = os.path.join(td, "clean.png")
        img.save(src)
        c2a.main([src, dst])
        assert os.path.exists(dst), "CLI did not write output"
        fixed = Image.open(dst)
        assert fixed.mode == "RGBA"
        fa = np.array(fixed.getchannel("A")).astype(float) / 255.0
        assert fa[16:32, 16:32].mean() < 0.05, "CLI output not transparent"
        assert fa[280, 256] > 0.95, "CLI output lost body"

    # 6) A genuinely transparent RGBA (no checkerboard in RGB) stays untouched
    solid = np.full((512, 512, 3), 250, dtype=np.uint8)
    rgba = np.dstack([solid, np.where(body | hair, 255, 0).astype(np.uint8)])
    assert c2a.detect_checkerboard(Image.fromarray(rgba, "RGBA")) is None, \
        "real RGBA misdetected as checkerboard"

    print("ALL TESTS PASSED")


if __name__ == "__main__":
    main()
