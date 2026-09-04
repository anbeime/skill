#!/usr/bin/env python3
"""Tests for the mandatory turntable coverage + interior-hole gate."""

import struct
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "stage4_review"))
from turntable_gate import analyze_turntable  # noqa: E402
from diagnose_render_multi_angle import silhouette_area_fraction  # noqa: E402


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def write_rgb_png(path, w, h, pixel_fn):
    """Minimal, stdlib-only (zlib + struct) uncompressed-filter RGB PNG encoder,
    just enough for read_png/load_image to decode back in tests."""

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    raw = bytearray()
    for y in range(h):
        raw.append(0)  # filter type 0 (none) per scanline
        for x in range(w):
            raw += bytes(pixel_fn(x, y, w, h))
    ihdr = struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)  # bit depth 8, color type 2 (RGB)
    path.write_bytes(
        PNG_SIGNATURE
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )


BACKGROUND = (255, 255, 255)
FOREGROUND = (20, 20, 20)


def _blob(x0, y0, x1, y1, hole_center=None, hole_radius=0):
    """Pixel fn: a solid dark square blob on a white background, optionally
    with a background-coloured disc punched through its middle (the
    silhouette-encloses-background regression case an area check can't see).
    """

    def fn(x, y, w, h):
        if hole_center is not None:
            dx, dy = x - hole_center[0], y - hole_center[1]
            if dx * dx + dy * dy <= hole_radius * hole_radius:
                return BACKGROUND
        if x0 <= x < x1 and y0 <= y < y1:
            return FOREGROUND
        return BACKGROUND

    return fn


def _low_contrast_gradient(x, y, w, h):
    """Pixel fn: a saturated dark subject on a saturated dark gradient.

    This reproduces the review harness's own render style, which is what
    defeated `build_foreground_mask` in practice. The mechanism is specific: the
    segmenter accepts a pixel as foreground when `distance > threshold` OR
    `saturation > 0.16 and luma < 0.94`. A dark violet background satisfies the
    second clause everywhere, so coverage crosses the 0.9 line, the "not clearly
    isolated" warning fires, and the mask becomes the whole frame. A grey-ish
    low-contrast image does NOT reproduce this — it fails the saturation clause
    and segments normally at ~0.58 coverage. The colours below are load-bearing.
    """
    base = 30 + int(22 * (y / max(1, h)))
    if 60 <= x < 140 and 60 <= y < 140:
        return (base + 40, base + 20, base + 62)
    return (base, base - 6, base + 22)


class TurntableGateTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def _write(self, name, w, h, pixel_fn):
        path = self.tmp / name
        write_rgb_png(path, w, h, pixel_fn)
        return path

    def test_unsegmentable_capture_blocks_the_gate_instead_of_passing(self):
        # Found by running this gate on a REAL review turntable: every angle
        # reported area=0.9966 and the verdict was a confident PASS, because
        # build_foreground_mask fell back to "use most pixels" and the mask
        # covered the whole frame. The subject was never measured at all. A gate
        # that cannot see its subject must block, not pass.
        captures = [
            (azimuth, self._write(f"flat_{azimuth}.png", 200, 200, _low_contrast_gradient))
            for azimuth in (0, 90, 180, 270)
        ]
        result = analyze_turntable(captures)

        self.assertEqual(sorted(result["unsegmentedAzimuths"]), [0.0, 90.0, 180.0, 270.0])
        self.assertFalse(result["segmentationReliable"])
        self.assertFalse(result["passed"])
        # Coverage was complete and nothing collapsed -- without the segmentation
        # check every other signal here says "fine", which is precisely the trap.
        self.assertTrue(result["covered"])
        self.assertFalse(result["degenerate"])

    def test_allow_holes_does_not_excuse_an_unsegmentable_capture(self):
        # allow_holes means "this subject may legitimately have a through-hole".
        # It must never be readable as "evaluate this render blind".
        captures = [
            (azimuth, self._write(f"flat2_{azimuth}.png", 200, 200, _low_contrast_gradient))
            for azimuth in (0, 90, 180, 270)
        ]
        self.assertFalse(analyze_turntable(captures, allow_holes=True)["passed"])

    def test_solid_blob_at_all_required_azimuths_passes(self):
        captures = []
        for azimuth in (0, 90, 180, 270):
            path = self._write(f"solid_{azimuth}.png", 200, 200, _blob(40, 40, 160, 160))
            captures.append((azimuth, path))

        result = analyze_turntable(captures)
        self.assertTrue(result["passed"])
        self.assertFalse(result["holed"])
        self.assertEqual(result["missingAzimuths"], [])
        self.assertTrue(result["covered"])
        self.assertFalse(result["degenerate"])

    def test_punched_disc_is_holed_and_fails_while_area_barely_moves(self):
        # Regression case (lead): a background-coloured disc punched through
        # the middle of the blob is an enclosed-background hole. Silhouette
        # AREA barely changes (the disc removes a small fraction of the
        # blob's pixels), so the existing area-collapse signal alone would
        # miss it -- the whole point of this module.
        solid_path = self._write("solid.png", 200, 200, _blob(40, 40, 160, 160))
        punched_path = self._write(
            "punched.png", 200, 200, _blob(40, 40, 160, 160, hole_center=(100, 100), hole_radius=20)
        )

        solid_fraction = silhouette_area_fraction(solid_path)
        punched_fraction = silhouette_area_fraction(punched_path)
        self.assertAlmostEqual(solid_fraction, punched_fraction, delta=0.05)

        captures = [(0, punched_path), (90, solid_path), (180, solid_path), (270, solid_path)]
        result = analyze_turntable(captures)
        self.assertTrue(result["holed"])
        self.assertFalse(result["passed"])
        # And the underlying area signal really did barely move -- this is
        # what makes the hole check a genuinely new signal, not a duplicate.
        self.assertFalse(result["degenerate"])

    def test_missing_azimuths_reported_and_fails(self):
        path = self._write("front.png", 200, 200, _blob(40, 40, 160, 160))
        result = analyze_turntable([(0, path)])
        self.assertEqual(sorted(result["missingAzimuths"]), [90.0, 180.0, 270.0])
        self.assertFalse(result["covered"])
        self.assertFalse(result["passed"])

    def test_allow_holes_flips_holed_case_back_to_passing(self):
        solid_path = self._write("solid2.png", 200, 200, _blob(40, 40, 160, 160))
        punched_path = self._write(
            "punched2.png", 200, 200, _blob(40, 40, 160, 160, hole_center=(100, 100), hole_radius=20)
        )
        captures = [(0, punched_path), (90, solid_path), (180, solid_path), (270, solid_path)]

        gated = analyze_turntable(captures, allow_holes=False)
        allowed = analyze_turntable(captures, allow_holes=True)

        self.assertFalse(gated["passed"])
        self.assertTrue(allowed["passed"])
        # The raw signal is still reported even when allowed -- allow_holes
        # only changes whether it fails the gate, not whether it's detected.
        self.assertTrue(allowed["holed"])

    def test_tiny_hole_does_not_trip_the_gate(self):
        # A 1px anti-aliasing-scale speckle must not read as a defect.
        captures = []
        for azimuth in (0, 90, 180, 270):
            path = self._write(
                f"speckle_{azimuth}.png",
                200,
                200,
                _blob(40, 40, 160, 160, hole_center=(100, 100), hole_radius=1),
            )
            captures.append((azimuth, path))

        result = analyze_turntable(captures)
        self.assertFalse(result["holed"])
        self.assertTrue(result["passed"])

    def test_wraparound_azimuth_matches_required_zero(self):
        captures = [
            (359.5, self._write("wrap_0.png", 200, 200, _blob(40, 40, 160, 160))),
            (90.3, self._write("wrap_90.png", 200, 200, _blob(40, 40, 160, 160))),
            (180.0, self._write("wrap_180.png", 200, 200, _blob(40, 40, 160, 160))),
            (269.8, self._write("wrap_270.png", 200, 200, _blob(40, 40, 160, 160))),
        ]
        result = analyze_turntable(captures)
        self.assertEqual(result["missingAzimuths"], [])
        self.assertTrue(result["covered"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
