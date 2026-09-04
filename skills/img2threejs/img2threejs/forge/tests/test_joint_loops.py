#!/usr/bin/env python3
"""Tests for the joint edge-loop gate.

The load-bearing one is `test_a_dense_two_ring_joint_still_fails`: ten thousand vertices arranged in
two rings cannot bend, and a gate that counted vertices instead of bands would call that mesh dense
and wave it through. Counting the wrong thing is the only way this gate can be useless, so that is
what gets pinned.

Pure Python 3.10+ stdlib.
"""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "stage4_review"))

from joint_loops import analyze_joint_loops, count_loops_at_joint  # noqa: E402


def limb(rings: int, segments: int = 12, radius: float = 0.5, length: float = 1.0):
    """A tube along +y with `rings` rings of vertices, centred on the origin.

    Length 1.0 against the 2.0-long ELBOW bone puts every ring inside the gate's axial window
    (0.35 x bone length = 0.7). A longer tube parks its rings outside the window entirely, which the
    gate correctly scores as zero loops -- a real defect, but a different one from "too few bands",
    and not what these tests are measuring.
    """
    vertices = []
    for ring in range(rings):
        y = -length / 2 + length * ring / max(1, rings - 1)
        for segment in range(segments):
            angle = 2 * math.pi * segment / segments
            vertices.append([radius * math.cos(angle), y, radius * math.sin(angle)])
    return vertices


ELBOW = {"id": "elbow", "jointPos": [0.0, 0.0, 0.0], "tipPos": [0.0, 2.0, 0.0]}


class LoopCounting(unittest.TestCase):
    def test_a_dense_two_ring_joint_still_fails(self) -> None:
        # 600 vertices, two rings. Vertex count says "dense"; the joint cannot bend.
        vertices = limb(rings=2, segments=300)
        result = analyze_joint_loops([{"vertices": vertices}], [ELBOW])
        self.assertEqual(result["joints"][0]["loops"], 2)
        self.assertGreater(result["joints"][0]["vertexCount"], 100)
        self.assertFalse(result["passed"])

    def test_a_sparse_five_ring_joint_passes(self) -> None:
        # 30 vertices, five rings. Far fewer vertices than the failing case above, and correct.
        vertices = limb(rings=5, segments=6)
        result = analyze_joint_loops([{"vertices": vertices}], [ELBOW])
        self.assertGreaterEqual(result["joints"][0]["loops"], 3)
        self.assertLess(result["joints"][0]["vertexCount"], 100)
        self.assertTrue(result["passed"])

    def test_loop_count_is_scale_invariant(self) -> None:
        # The same character at two scales must score the same, or the threshold is measuring units.
        small = limb(rings=5, segments=8, radius=0.5, length=2.0)
        big = [[c * 100 for c in v] for v in small]
        small_result = count_loops_at_joint(small, [0, 0, 0], [0, 0, 0], [0, 2, 0], 0.7)
        big_result = count_loops_at_joint(big, [0, 0, 0], [0, 0, 0], [0, 200, 0], 70.0)
        self.assertEqual(small_result["loops"], big_result["loops"])

    def test_vertices_outside_the_radius_are_ignored(self) -> None:
        near = limb(rings=4, segments=8, length=1.0)
        far = [[0.0, 50.0 + i, 0.0] for i in range(20)]
        with_far = count_loops_at_joint(near + far, [0, 0, 0], [0, 0, 0], [0, 2, 0], 0.8)
        without = count_loops_at_joint(near, [0, 0, 0], [0, 0, 0], [0, 2, 0], 0.8)
        self.assertEqual(with_far["loops"], without["loops"])


class GateBehaviour(unittest.TestCase):
    def test_failure_names_the_bone_and_says_what_happens(self) -> None:
        result = analyze_joint_loops([{"vertices": limb(rings=2)}], [ELBOW])
        self.assertEqual(result["failingJointCount"], 1)
        self.assertIn("elbow", result["failures"][0])
        self.assertIn("crease", result["failures"][0])

    def test_meshes_are_pooled_so_a_seam_joint_is_not_half_measured(self) -> None:
        # A joint where two components meet: each half alone has too few rings, together they are fine.
        # Measuring per mesh would fail a joint that is actually correct.
        lower = [[0.4 * math.cos(a), y, 0.4 * math.sin(a)]
                 for y in (-0.30, -0.15) for a in [i * math.pi / 4 for i in range(8)]]
        upper = [[0.4 * math.cos(a), y, 0.4 * math.sin(a)]
                 for y in (0.15, 0.30) for a in [i * math.pi / 4 for i in range(8)]]
        pooled = analyze_joint_loops([{"vertices": lower}, {"vertices": upper}], [ELBOW])
        self.assertGreaterEqual(pooled["joints"][0]["loops"], 4)
        self.assertTrue(pooled["passed"])

    def test_zero_length_bone_is_reported_not_divided_by(self) -> None:
        degenerate = {"id": "stub", "jointPos": [0.0, 0.0, 0.0], "tipPos": [0.0, 0.0, 0.0]}
        result = analyze_joint_loops([{"vertices": limb(rings=5)}], [degenerate])
        self.assertEqual(result["joints"][0]["loops"], 0)
        self.assertFalse(result["passed"])

    def test_no_vertices_raises(self) -> None:
        with self.assertRaises(ValueError):
            analyze_joint_loops([{"vertices": []}], [ELBOW])

    def test_min_loops_is_configurable(self) -> None:
        vertices = limb(rings=3, segments=8)
        self.assertTrue(analyze_joint_loops([{"vertices": vertices}], [ELBOW], min_loops=3)["passed"])
        self.assertFalse(analyze_joint_loops([{"vertices": vertices}], [ELBOW], min_loops=6)["passed"])


if __name__ == "__main__":
    unittest.main()
