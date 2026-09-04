#!/usr/bin/env python3
"""Tests for geodesic voxel binding, built around the defect it exists to remove.

`test_euclidean_leaks_across_the_gap_and_geodesic_does_not` is the whole argument for this module. It
binds ONE mesh with BOTH methods and compares them, because "geodesic distance stops weight leaking
across a gap" is otherwise just a claim. The fixture is an arm hanging beside a torso with a real air
gap, joined only at the shoulder -- the default pose of almost every character.

Pure Python 3.10+ stdlib.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "stage5_rig"))

from geodesic_skinning import (  # noqa: E402
    bind,
    euclidean_bind,
    geodesic_field,
    VoxelGrid,
    _segment_voxels,
    _triangles,
)


def box(x0, x1, y0, y1, z0, z1):
    vertices = [
        [x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
        [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1],
    ]
    quads = [
        (0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
        (2, 3, 7, 6), (1, 2, 6, 5), (0, 4, 7, 3),
    ]
    indices = []
    for a, b, c, d in quads:
        indices.extend([a, b, c, a, c, d])
    return vertices, indices


def merge(*meshes):
    vertices: list[list[float]] = []
    indices: list[int] = []
    for verts, inds in meshes:
        offset = len(vertices)
        vertices.extend(verts)
        indices.extend(index + offset for index in inds)
    return vertices, indices


def torso_with_hanging_arm():
    """A torso, an arm beside it across a 0.4 air gap, and a shoulder bridge joining them at the top.

    The gap matters: at the default resolution it is several voxels wide, so no geodesic path can cut
    across it. Every route from the arm to the lower torso has to climb to the shoulder and back down,
    which is exactly the anatomy that makes Euclidean binding fail.
    """
    torso = box(0.0, 2.0, 0.0, 4.0, 0.0, 1.0)
    arm = box(2.4, 3.4, 0.0, 3.4, 0.0, 1.0)
    shoulder = box(1.8, 2.6, 3.4, 4.0, 0.0, 1.0)
    return merge(torso, arm, shoulder)


SPINE = {"id": "spine", "jointPos": [1.0, 0.5, 0.5], "tipPos": [1.0, 3.5, 0.5]}
ARM = {"id": "arm", "jointPos": [2.9, 3.2, 0.5], "tipPos": [2.9, 0.4, 0.5]}


def arm_weight(result, vertex_index: int) -> float:
    arm_bone = result["boneOrder"].index("arm")
    total = 0.0
    for slot, bone in enumerate(result["skinIndices"][vertex_index]):
        if bone == arm_bone:
            total += result["skinWeights"][vertex_index][slot]
    return total


class TheDefectThisFixes(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.vertices, cls.indices = torso_with_hanging_arm()
        cls.mesh = {"vertices": cls.vertices, "indices": cls.indices}
        # The lower-right corner of the torso: close to the arm bone in a straight line, far from it
        # through the body. Vertex 1 of the torso box is [2, 0, 0].
        cls.chest_index = 1
        cls.geodesic = bind(cls.mesh, [SPINE, ARM], resolution=32)
        cls.euclidean = euclidean_bind(cls.mesh, [SPINE, ARM])

    def test_the_probe_vertex_really_is_euclidean_close_to_the_arm(self) -> None:
        # If this were false the comparison below would prove nothing -- it would just be a vertex
        # nowhere near the arm under either metric.
        vertex = self.vertices[self.chest_index]
        self.assertLess(abs(vertex[0] - ARM["jointPos"][0]), 1.0)

    def test_the_distance_field_routes_around_the_shoulder(self) -> None:
        """What this module actually computes, asserted directly.

        The weights below are a POLICY applied to these distances, and a falloff constant can make a
        correct field look wrong. So the field is pinned on its own: the straight line from the chest
        corner to the arm bone is under 1 unit, while any path through the solid has to climb to the
        shoulder and come back down, which is several times further.
        """
        grid = VoxelGrid(self.vertices, _triangles(self.indices), 32)
        cell = grid.index_of(self.vertices[self.chest_index])
        to_spine = geodesic_field(grid, _segment_voxels(grid, SPINE["jointPos"], SPINE["tipPos"]))[cell]
        to_arm = geodesic_field(grid, _segment_voxels(grid, ARM["jointPos"], ARM["tipPos"]))[cell]
        self.assertGreater(to_arm / to_spine, 3.0)
        # And the arm really is close in a straight line, which is what makes Euclidean fail.
        self.assertLess(abs(self.vertices[self.chest_index][0] - ARM["jointPos"][0]), 1.0)

    def test_euclidean_leaks_across_the_gap_and_geodesic_does_not(self) -> None:
        leaked = arm_weight(self.euclidean, self.chest_index)
        contained = arm_weight(self.geodesic, self.chest_index)
        # The comparison is the claim. An absolute threshold here would be measuring the falloff
        # constant rather than the method: at the same distances, power 2 leaves 8.6% and power 4
        # leaves 0.9%, and neither number says anything about whether the path crossed the gap.
        self.assertGreater(leaked, 0.25)
        self.assertLess(contained, leaked / 5.0)

    def test_arm_vertices_still_belong_to_the_arm(self) -> None:
        # The fix must not work by simply weakening the arm bone everywhere.
        arm_corner = 8 + 1  # second vertex of the arm box: [3.4, 0, 0]
        self.assertGreater(arm_weight(self.geodesic, arm_corner), 0.8)


class WeightInvariants(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        vertices, indices = torso_with_hanging_arm()
        cls.result = bind({"vertices": vertices, "indices": indices}, [SPINE, ARM], resolution=24)

    def test_weights_are_normalised(self) -> None:
        self.assertLess(self.result["maxWeightError"], 1e-9)

    def test_every_vertex_gets_four_slots(self) -> None:
        for row in self.result["skinWeights"]:
            self.assertEqual(len(row), 4)
        for row in self.result["skinIndices"]:
            self.assertEqual(len(row), 4)

    def test_no_negative_weights(self) -> None:
        for row in self.result["skinWeights"]:
            for weight in row:
                self.assertGreaterEqual(weight, 0.0)

    def test_solid_voxels_exceed_surface_voxels(self) -> None:
        # Proves the interior flood fill actually filled something. If the surface shell leaked, the
        # interior would be classified as outside and solid would collapse onto the shell.
        self.assertGreater(self.result["solidVoxelCount"], self.result["surfaceVoxelCount"])


class Voxelization(unittest.TestCase):
    def test_a_solid_box_is_filled_not_hollow(self) -> None:
        vertices, indices = box(0, 1, 0, 1, 0, 1)
        grid = VoxelGrid(vertices, _triangles(indices), 16)
        self.assertGreater(len(grid.solid), len(grid.surface))
        # The centre of the box must be solid; if the flood fill leaked it would not be.
        self.assertIn(grid.index_of([0.5, 0.5, 0.5]), grid.solid)

    def test_the_gap_between_torso_and_arm_stays_empty(self) -> None:
        # The single assumption the headline test rests on. If the voxelization bridged the gap the
        # geodesic path would cut straight across and the comparison would silently become vacuous.
        vertices, indices = torso_with_hanging_arm()
        grid = VoxelGrid(vertices, _triangles(indices), 32)
        self.assertNotIn(grid.index_of([2.2, 1.0, 0.5]), grid.solid)


class Reporting(unittest.TestCase):
    def test_a_detached_island_is_reported_not_silently_pinned(self) -> None:
        # An unreachable vertex usually means a hole or a loose island. Pinning it to the nearest bone
        # in space would hide exactly the thing worth knowing.
        main_mesh = box(0, 1, 0, 1, 0, 1)
        island = box(5, 6, 5, 6, 5, 6)
        vertices, indices = merge(main_mesh, island)
        bone = {"id": "b", "jointPos": [0.5, 0.2, 0.5], "tipPos": [0.5, 0.8, 0.5]}
        result = bind({"vertices": vertices, "indices": indices}, [bone], resolution=24)
        self.assertGreater(result["unreachableVertexCount"], 0)

    def test_rejects_input_it_cannot_bind(self) -> None:
        vertices, indices = box(0, 1, 0, 1, 0, 1)
        with self.assertRaises(ValueError):
            bind({"vertices": vertices, "indices": indices}, [])
        with self.assertRaises(ValueError):
            bind({"vertices": [], "indices": indices}, [SPINE])


if __name__ == "__main__":
    unittest.main()
