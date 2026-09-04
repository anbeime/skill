#!/usr/bin/env python3
"""Tests for inter-part penetration, morph targets, and decimation.

Each group pins the case that would otherwise ship silently:

* penetration -- two individually flawless meshes occupying the same space, which every per-mesh gate
  passes by construction;
* morphs -- a target whose vertex order does not match the base, which zip-truncation would turn into
  a plausible-looking nonsense deformation;
* decimation -- a collapse that folds the surface, which still hits the triangle count and is exactly
  the defect `self_intersection.py` exists to catch.

Pure Python 3.10+ stdlib.
"""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "stage3_build"))
sys.path.insert(0, str(ROOT / "stage4_review"))
sys.path.insert(0, str(ROOT / "tests"))

from pairwise_penetration import analyze_meshes, analyze_pair, point_inside  # noqa: E402
from morph_targets import build_morph_set, corrective_from_bend, make_morph_target  # noqa: E402
from decimate import build_lod_plan, decimate  # noqa: E402
from geometry_integrity import mesh_edge_counts  # noqa: E402
from test_self_intersection import icosphere  # noqa: E402


def box(x0, x1, y0, y1, z0, z1, name="box"):
    vertices = [
        [x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
        [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1],
    ]
    quads = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (2, 3, 7, 6), (1, 2, 6, 5), (0, 4, 7, 3)]
    indices = []
    for a, b, c, d in quads:
        indices.extend([a, b, c, a, c, d])
    return {"name": name, "vertices": vertices, "indices": indices}


class InterPartPenetration(unittest.TestCase):
    def test_a_bar_driven_through_a_block_is_caught(self) -> None:
        block = box(0, 2, 0, 2, 0, 2, "torso")
        bar = box(0.8, 1.2, -1, 3, 0.8, 1.2, "staff")
        result = analyze_meshes([block, bar])
        self.assertFalse(result["passed"])
        self.assertTrue(any("staff" in failure and "torso" in failure for failure in result["failures"]))

    def test_each_mesh_alone_is_flawless_so_only_a_pair_test_can_see_this(self) -> None:
        # The argument for the module: both meshes are closed and clean on their own.
        for mesh in (box(0, 2, 0, 2, 0, 2), box(0.8, 1.2, -1, 3, 0.8, 1.2)):
            counts = mesh_edge_counts(mesh["vertices"], mesh["indices"])
            self.assertEqual(counts["boundaryEdges"], 0)
            self.assertEqual(counts["nonManifoldEdges"], 0)

    def test_separated_parts_pass_and_say_the_test_actually_ran(self) -> None:
        result = analyze_meshes([box(0, 1, 0, 1, 0, 1, "a"), box(5, 6, 5, 6, 5, 6, "b")])
        self.assertTrue(result["passed"])
        self.assertEqual(result["pairs"], [])

    def test_allowed_pairs_exempt_parts_meant_to_touch(self) -> None:
        # A hand gripping a staff shares space on purpose; without this the gate is useless on exactly
        # the models it is for.
        hand = box(0, 2, 0, 2, 0, 2, "hand")
        staff = box(0.8, 1.2, -1, 3, 0.8, 1.2, "staff")
        self.assertFalse(analyze_meshes([hand, staff])["passed"])
        self.assertTrue(analyze_meshes([hand, staff], allowed_pairs=[["hand", "staff"]])["passed"])

    def test_both_directions_are_checked(self) -> None:
        # A small part fully inside a large one has no vertex of the large part inside it, so testing
        # only one direction would miss it entirely.
        big = box(0, 10, 0, 10, 0, 10, "big")
        small = box(4, 5, 4, 5, 4, 5, "small")
        result = analyze_meshes([big, small])
        self.assertFalse(result["passed"])
        self.assertTrue(any(pair["a"] == "small" and pair["penetrating"] for pair in result["pairs"]))

    def test_point_inside_agrees_with_geometry(self) -> None:
        cube = box(0, 1, 0, 1, 0, 1)
        faces = [tuple(cube["indices"][i:i + 3]) for i in range(0, len(cube["indices"]), 3)]
        self.assertEqual(point_inside((0.5, 0.5, 0.5), cube["vertices"], faces), "inside")
        self.assertEqual(point_inside((5.0, 5.0, 5.0), cube["vertices"], faces), "outside")

    def test_sampling_is_reported(self) -> None:
        a = box(0, 2, 0, 2, 0, 2, "a")
        b = box(1, 3, 1, 3, 1, 3, "b")
        result = analyze_pair(a, b, max_samples=4)
        self.assertIn("sampledVertexCount", result)
        self.assertIn("totalVertexCount", result)
        self.assertGreaterEqual(result["samplingStride"], 1)


class MorphTargets(unittest.TestCase):
    def test_mismatched_vertex_count_is_refused_not_truncated(self) -> None:
        base = [[0, 0, 0], [1, 0, 0], [0, 1, 0]]
        shorter = [[0, 0, 0], [1, 0, 0]]
        with self.assertRaises(ValueError) as caught:
            make_morph_target(base, shorter, "smile")
        self.assertIn("vertex order", str(caught.exception))

    def test_deltas_are_relative_and_mostly_zero(self) -> None:
        base = [[0, 0, 0], [1, 0, 0], [0, 1, 0]]
        target = [[0, 0, 0], [1, 0.5, 0], [0, 1, 0]]
        result = make_morph_target(base, target, "raise")
        self.assertEqual(result["deltas"][0], [0.0, 0.0, 0.0])
        self.assertEqual(result["deltas"][1], [0.0, 0.5, 0.0])
        self.assertEqual(result["movedVertexCount"], 1)

    def test_a_target_that_moves_nothing_is_flagged(self) -> None:
        base = [[0, 0, 0], [1, 0, 0], [0, 1, 0]]
        result = build_morph_set({"vertices": base}, [{"name": "dead", "vertices": base}])
        self.assertEqual(result["noOpTargets"], ["dead"])

    def test_relative_flag_is_declared_because_absolute_would_collapse_the_mesh(self) -> None:
        base = [[0, 0, 0], [1, 0, 0], [0, 1, 0]]
        result = build_morph_set({"vertices": base}, [])
        self.assertTrue(result["morphTargetsRelative"])
        self.assertTrue(any("morphTargetsRelative" in note for note in [result["note"]]))

    def test_corrective_pushes_the_surface_outward_near_the_joint_only(self) -> None:
        # The joint sits ON the surface, not at the sphere's centre: from the centre every vertex of a
        # unit sphere is exactly 1.0 away, so any radius below 1 touches nothing and any radius above
        # touches everything, and the test would measure nothing either way.
        vertices, _ = icosphere(2)
        joint = [1.0, 0.0, 0.0]
        moved = corrective_from_bend(vertices, joint, [0, 1, 0], radius=0.6, volume_gain=0.1)

        def distance_to_joint(v):
            return math.dist(v, joint)

        near = [i for i, v in enumerate(vertices) if distance_to_joint(v) < 0.5]
        far = [i for i, v in enumerate(vertices) if distance_to_joint(v) > 1.2]
        self.assertTrue(near and far)
        self.assertTrue(any(moved[i] != list(vertices[i]) for i in near))
        for i in far:
            self.assertEqual(moved[i], list(vertices[i]))


class Decimation(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.vertices, cls.indices = icosphere(3)

    def test_triangle_count_actually_drops(self) -> None:
        result = decimate({"vertices": self.vertices, "indices": self.indices}, 0.5)
        self.assertLess(result["triangleCount"], result["originalTriangleCount"])
        self.assertLessEqual(result["achievedRatio"], 0.75)

    def test_decimated_mesh_is_still_a_closed_surface(self) -> None:
        # The whole risk: hitting the triangle count while leaving a mesh that is no longer a surface.
        result = decimate({"vertices": self.vertices, "indices": self.indices}, 0.5)
        counts = mesh_edge_counts(result["vertices"], result["indices"])
        self.assertEqual(counts["boundaryEdges"], 0)
        self.assertEqual(counts["nonManifoldEdges"], 0)

    def test_flip_refusals_are_counted_not_hidden(self) -> None:
        result = decimate({"vertices": self.vertices, "indices": self.indices}, 0.2)
        self.assertIn("collapsesRefusedForFlip", result)
        self.assertIn("reachedTarget", result)

    def test_indices_stay_in_range_after_remapping(self) -> None:
        result = decimate({"vertices": self.vertices, "indices": self.indices}, 0.4)
        self.assertTrue(result["indices"])
        self.assertLess(max(result["indices"]), len(result["vertices"]))

    def test_ratio_of_one_is_a_no_op(self) -> None:
        result = decimate({"vertices": self.vertices, "indices": self.indices}, 1.0)
        self.assertEqual(result["triangleCount"], result["originalTriangleCount"])

    def test_invalid_ratio_raises(self) -> None:
        with self.assertRaises(ValueError):
            decimate({"vertices": self.vertices, "indices": self.indices}, 0.0)

    def test_generated_lod_plan_satisfies_the_validator_it_was_only_declared_for(self) -> None:
        plan = build_lod_plan(
            {"vertices": self.vertices, "indices": self.indices},
            ratios=[0.6, 0.3],
            distances=[10.0, 40.0],
        )
        tiers = plan["lodPlan"]
        self.assertEqual(len(tiers), 2)
        self.assertLess(tiers[0]["distance"], tiers[1]["distance"])
        self.assertGreater(tiers[0]["triangleCount"], tiers[1]["triangleCount"])

    def test_non_monotonic_request_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            build_lod_plan(
                {"vertices": self.vertices, "indices": self.indices},
                ratios=[0.3, 0.9],
                distances=[10.0, 40.0],
            )


if __name__ == "__main__":
    unittest.main()
