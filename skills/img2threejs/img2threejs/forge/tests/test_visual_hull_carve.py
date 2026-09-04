#!/usr/bin/env python3
"""Tests for the visual-hull carve, each pinning a property the carve could plausibly get wrong.

The load-bearing one is `test_carved_surface_is_watertight`. Emitting all six faces of every occupied
voxel is the obvious implementation and it is wrong: shared faces become duplicated interior walls and
the result is not a surface at all. Because that mesh still *looks* right when rendered from outside,
the only thing that catches it is an edge count, so that is what this asserts.

Pure Python 3.10+ stdlib.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "stage3_build"))
sys.path.insert(0, str(ROOT / "stage4_review"))

from visual_hull import carve_visual_hull  # noqa: E402
from geometry_integrity import mesh_edge_counts  # noqa: E402


def solid_mask(size: int) -> list[str]:
    return ["1" * size for _ in range(size)]


def disc_mask(size: int, radius_fraction: float = 0.45) -> list[str]:
    """A filled circle, the silhouette a sphere casts from any direction."""
    rows = []
    centre = (size - 1) / 2
    radius = size * radius_fraction
    for y in range(size):
        row = []
        for x in range(size):
            inside = (x - centre) ** 2 + (y - centre) ** 2 <= radius**2
            row.append("1" if inside else "0")
        rows.append("".join(row))
    return rows


def descriptor(views, resolution=8, size=16, budget=400_000):
    return {
        "projection": "orthographic",
        "boundsSpace": "component-local",
        "bounds": {"min": [-1.0, -1.0, -1.0], "max": [1.0, 1.0, 1.0]},
        "resolution": resolution,
        "triangleBudget": budget,
        "views": [{"axis": axis, "confidence": 0.9, "mask": mask} for axis, mask in views],
    }


class CarveGeometry(unittest.TestCase):
    def test_carved_surface_is_watertight(self) -> None:
        # Interior walls, or unwelded corners, both show up here and nowhere else.
        result = carve_visual_hull(
            descriptor([("front", disc_mask(16)), ("side", disc_mask(16)), ("top", disc_mask(16))])
        )
        counts = mesh_edge_counts(result["vertices"], result["indices"])
        self.assertEqual(counts["boundaryEdges"], 0)
        self.assertEqual(counts["nonManifoldEdges"], 0)
        self.assertGreater(result["triangleCount"], 0)

    def test_three_discs_carve_a_rounded_solid_not_the_whole_box(self) -> None:
        result = carve_visual_hull(
            descriptor([("front", disc_mask(16)), ("side", disc_mask(16)), ("top", disc_mask(16))])
        )
        # Three orthogonal discs intersect to a rounded solid strictly inside the bounding cube.
        self.assertGreater(result["occupiedFraction"], 0.15)
        self.assertLess(result["occupiedFraction"], 0.75)

    def test_a_view_that_sees_background_carves_the_voxel_away(self) -> None:
        # The defining property: survival requires foreground in EVERY view, not any view.
        empty_left = [("0" * 8 + "1" * 8) for _ in range(16)]
        both_solid = carve_visual_hull(
            descriptor([("front", solid_mask(16)), ("side", solid_mask(16))])
        )
        one_half = carve_visual_hull(
            descriptor([("front", empty_left), ("side", solid_mask(16))])
        )
        self.assertLess(one_half["occupiedVoxelCount"], both_solid["occupiedVoxelCount"])
        self.assertAlmostEqual(
            one_half["occupiedVoxelCount"] / both_solid["occupiedVoxelCount"], 0.5, delta=0.1
        )

    def test_disjoint_silhouettes_carve_everything_away_and_say_so(self) -> None:
        # One bad mask erases the model rather than degrading it. The count must make that visible
        # instead of handing back an empty mesh that reads as "carve succeeded".
        left = [("1" * 8 + "0" * 8) for _ in range(16)]
        right = [("0" * 8 + "1" * 8) for _ in range(16)]
        result = carve_visual_hull(descriptor([("front", left), ("top", right)]))
        self.assertEqual(result["occupiedVoxelCount"], 0)
        self.assertEqual(result["triangleCount"], 0)


class CarveHonesty(unittest.TestCase):
    def test_two_views_report_the_unconstrained_axis(self) -> None:
        result = carve_visual_hull(
            descriptor([("front", disc_mask(16)), ("side", disc_mask(16))])
        )
        # front frees z, side frees x -- so y is never the camera direction and stays unconstrained.
        self.assertEqual(result["unconstrainedAxes"], ["y"])
        self.assertTrue(any("extrudes along" in line for line in result["limitations"]))

    def test_three_views_leave_nothing_unconstrained(self) -> None:
        result = carve_visual_hull(
            descriptor([("front", disc_mask(16)), ("side", disc_mask(16)), ("top", disc_mask(16))])
        )
        self.assertEqual(result["unconstrainedAxes"], [])
        self.assertFalse(any("extrudes along" in line for line in result["limitations"]))

    def test_concavity_limitation_is_always_stated(self) -> None:
        # Stated even for a three-view carve, because view count never fixes it.
        result = carve_visual_hull(
            descriptor([("front", disc_mask(16)), ("side", disc_mask(16)), ("top", disc_mask(16))])
        )
        self.assertTrue(any("concavity" in line for line in result["limitations"]))

    def test_budget_is_guaranteed_upstream_so_the_carve_needs_no_verdict(self) -> None:
        """Pins WHY carve_visual_hull reports no budget-overrun boolean.

        The validator requires triangleBudget >= resolution**3 * 12, the worst case for the grid, so
        an under-budget descriptor never reaches the carve at all. If that rule is ever relaxed this
        test fails, which is the signal that the carve then does need its own verdict.
        """
        with self.assertRaises(ValueError) as caught:
            carve_visual_hull(
                descriptor([("front", solid_mask(16)), ("side", solid_mask(16))], resolution=8, budget=10)
            )
        self.assertIn("triangleBudget", str(caught.exception))

        generous = carve_visual_hull(
            descriptor([("front", solid_mask(16)), ("side", solid_mask(16))], resolution=8)
        )
        self.assertLessEqual(generous["triangleCount"], generous["triangleBudget"])


class CarveConventions(unittest.TestCase):
    def test_front_view_rows_run_downward_in_y(self) -> None:
        """Row 0 of a mask is the TOP of the image, which is MAX y, not min.

        Getting this backwards flips every carve upside down while leaving voxel counts, watertightness
        and every other assertion in this file completely unchanged -- so nothing else here would
        notice. The mask's top half is foreground, so the survivors must all sit at y >= 0.

        Half the mask rather than one row on purpose: with resolution 8 against a 16-row mask, the
        topmost voxel's CENTRE lands in mask row 1, not row 0, so a single-row mask carves everything
        away and would fail for a sampling reason that has nothing to do with direction.
        """
        top_half = ["1" * 16 for _ in range(8)] + ["0" * 16 for _ in range(8)]
        result = carve_visual_hull(
            descriptor([("front", top_half), ("side", solid_mask(16))], resolution=8)
        )
        self.assertGreater(result["occupiedVoxelCount"], 0)
        ys = [v[1] for v in result["vertices"]]
        self.assertGreaterEqual(min(ys), -1e-9)

        # And the mirror image really does land on the other side, so this is measuring direction
        # rather than an accident of where the geometry happened to be.
        bottom_half = ["0" * 16 for _ in range(8)] + ["1" * 16 for _ in range(8)]
        flipped = carve_visual_hull(
            descriptor([("front", bottom_half), ("side", solid_mask(16))], resolution=8)
        )
        self.assertLessEqual(max(v[1] for v in flipped["vertices"]), 1e-9)

    def test_invalid_descriptor_raises_rather_than_carving_nonsense(self) -> None:
        bad = descriptor([("front", disc_mask(16))])  # one view; the schema requires two
        with self.assertRaises(ValueError):
            carve_visual_hull(bad)


if __name__ == "__main__":
    unittest.main()
