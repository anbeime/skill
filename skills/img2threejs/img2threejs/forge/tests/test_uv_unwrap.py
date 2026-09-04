#!/usr/bin/env python3
"""Tests for UV unwrapping, built on shapes whose correct answer is known in advance.

The centrepiece is `test_planar_grid_unwraps_without_distortion`: a flat grid has an exact isometric
flattening, so LSCM must reproduce it to within solver tolerance. If the conformal system is wired
wrong -- a sign flipped, real and imaginary parts crossed -- the result is still a plausible-looking
scatter of UVs, and only a case with a known answer catches it.

`test_closed_cube_reports_non_disk_charts_when_uncut` guards the failure mode that would otherwise
ship silently: a chart that is not a topological disk has no valid flattening, and LSCM returns one
anyway.

Pure Python 3.10+ stdlib.
"""

from __future__ import annotations

import math
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "stage3_build"))

from uv_unwrap import (  # noqa: E402
    chart_distortion,
    chart_is_disk,
    enforce_disk_charts,
    lscm,
    pack_charts,
    segment_charts,
    unwrap,
    _triangles,
)


def planar_grid(n: int = 5, size: float = 1.0):
    """An n x n quad grid on the z = 0 plane, triangulated."""
    vertices = []
    for row in range(n + 1):
        for column in range(n + 1):
            vertices.append([size * column / n, size * row / n, 0.0])
    indices = []
    for row in range(n):
        for column in range(n):
            a = row * (n + 1) + column
            b = a + 1
            c = a + (n + 1)
            d = c + 1
            indices.extend([a, b, d, a, d, c])
    return vertices, indices


def unit_cube():
    """A closed cube: six flat faces, and as one surface not a disk."""
    vertices = [
        [0, 0, 0], [1, 0, 0], [1, 1, 0], [0, 1, 0],
        [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1],
    ]
    quads = [
        (0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4),
        (2, 3, 7, 6), (1, 2, 6, 5), (0, 4, 7, 3),
    ]
    indices = []
    for a, b, c, d in quads:
        indices.extend([a, b, c, a, c, d])
    return vertices, indices


def open_cylinder(segments: int = 12, rings: int = 3, radius: float = 1.0, height: float = 2.0):
    """A tube with open ends: connected, but a cylinder rather than a disk."""
    vertices = []
    for ring in range(rings + 1):
        y = height * ring / rings
        for segment in range(segments):
            angle = 2 * math.pi * segment / segments
            vertices.append([radius * math.cos(angle), y, radius * math.sin(angle)])
    indices = []
    for ring in range(rings):
        for segment in range(segments):
            a = ring * segments + segment
            b = ring * segments + (segment + 1) % segments
            c = a + segments
            d = b + segments
            indices.extend([a, b, d, a, d, c])
    return vertices, indices


class ConformalCorrectness(unittest.TestCase):
    def test_planar_grid_unwraps_without_distortion(self) -> None:
        vertices, indices = planar_grid(5)
        result = unwrap({"vertices": vertices, "indices": indices})

        self.assertEqual(result["chartCount"], 1)
        self.assertEqual(result["totalFlippedTriangles"], 0)
        self.assertEqual(result["nonDiskCharts"], [])
        # A plane has an exact isometric flattening, so every triangle must scale identically and the
        # worst/median ratio must sit at 1.
        self.assertAlmostEqual(result["worstAreaDistortion"], 1.0, delta=0.02)

    def test_planar_grid_uv_preserves_relative_distances(self) -> None:
        # Stronger than the distortion ratio: checks the LAYOUT, not just the areas. A map that folded
        # the grid onto itself could still show uniform area scaling.
        vertices, indices = planar_grid(4)
        faces = _triangles(indices)
        charts = segment_charts(vertices, faces)
        uv = lscm(vertices, faces, charts[0])

        def ratio(i: int, j: int) -> float:
            du = uv[i][0] - uv[j][0]
            dv = uv[i][1] - uv[j][1]
            dx = vertices[i][0] - vertices[j][0]
            dy = vertices[i][1] - vertices[j][1]
            return math.hypot(du, dv) / max(math.hypot(dx, dy), 1e-12)

        pairs = [(0, 4), (0, 20), (4, 24), (6, 18)]
        ratios = [ratio(i, j) for i, j in pairs]
        for value in ratios:
            self.assertAlmostEqual(value, ratios[0], delta=0.05)

    def test_a_curved_chart_costs_area_and_the_number_says_so(self) -> None:
        # LSCM preserves angles, not areas. A cylinder chart must show measurably more area
        # distortion than a flat one -- if it did not, the metric would be inert.
        flat_v, flat_i = planar_grid(5)
        flat = unwrap({"vertices": flat_v, "indices": flat_i})

        cyl_v, cyl_i = open_cylinder()
        faces = _triangles(cyl_i)
        # One chart over the whole tube, bypassing segmentation, to isolate the solver's behaviour.
        whole = list(range(len(faces)))
        uv = lscm(cyl_v, faces, whole)
        curved = chart_distortion(cyl_v, faces, whole, uv)

        self.assertGreater(curved["areaDistortion"], flat["worstAreaDistortion"])


class ChartTopology(unittest.TestCase):
    def test_flat_grid_is_a_disk(self) -> None:
        vertices, indices = planar_grid(3)
        faces = _triangles(indices)
        self.assertTrue(chart_is_disk(faces, list(range(len(faces)))))

    def test_closed_cube_surface_is_not_a_disk(self) -> None:
        vertices, indices = unit_cube()
        faces = _triangles(indices)
        self.assertFalse(chart_is_disk(faces, list(range(len(faces)))))

    def test_open_cylinder_is_not_a_disk(self) -> None:
        vertices, indices = open_cylinder()
        faces = _triangles(indices)
        self.assertFalse(chart_is_disk(faces, list(range(len(faces)))))

    def test_uncut_tube_is_split_into_disks_not_merely_reported(self) -> None:
        """LSCM returns UVs for a non-disk chart and they are garbage, so reporting is not enough.

        Measured on a real skull, leaving seven non-disk charts in place drove worst-case area
        distortion to 171300 with twelve inverted triangles; cutting them first brought both down.
        A threshold of 180 degrees deliberately defeats segmentation so the whole tube arrives as one
        non-disk chart and only `enforce_disk_charts` can save it.
        """
        vertices, indices = open_cylinder(segments=16, rings=2)
        faces = _triangles(indices)
        self.assertFalse(chart_is_disk(faces, list(range(len(faces)))))

        result = unwrap({"vertices": vertices, "indices": indices}, angle_threshold_degrees=180.0)
        self.assertGreater(result["topologySplits"], 0)
        self.assertEqual(result["nonDiskCharts"], [])

    def test_enforce_disk_charts_terminates_and_covers_every_face(self) -> None:
        # A single triangle is always a disk, so the recursion has a floor; this pins that it is
        # reached without dropping or duplicating a face on the way.
        vertices, indices = open_cylinder(segments=12, rings=3)
        faces = _triangles(indices)
        charts, splits = enforce_disk_charts(faces, [list(range(len(faces)))])
        self.assertGreater(splits, 0)
        self.assertEqual(sorted(i for chart in charts for i in chart), list(range(len(faces))))
        for chart in charts:
            self.assertTrue(chart_is_disk(faces, chart))


class Segmentation(unittest.TestCase):
    def test_cube_splits_into_six_planar_charts(self) -> None:
        vertices, indices = unit_cube()
        faces = _triangles(indices)
        charts = segment_charts(vertices, faces, angle_threshold_degrees=50.0)
        self.assertEqual(len(charts), 6)
        for chart in charts:
            self.assertTrue(chart_is_disk(faces, chart))

    def test_growth_is_measured_against_the_seed_not_the_neighbour(self) -> None:
        # Against the neighbour, a chart creeps around a cylinder one tolerable step at a time until
        # its ends face opposite ways. Against the seed it cannot: a 12-segment tube turns 30 degrees
        # per step, so a 50-degree limit must stop well short of wrapping the whole ring.
        vertices, indices = open_cylinder(segments=12, rings=1)
        faces = _triangles(indices)
        charts = segment_charts(vertices, faces, angle_threshold_degrees=50.0)
        self.assertGreater(len(charts), 1)
        self.assertLess(max(len(chart) for chart in charts), len(faces))

    def test_every_face_lands_in_exactly_one_chart(self) -> None:
        vertices, indices = open_cylinder()
        faces = _triangles(indices)
        charts = segment_charts(vertices, faces)
        assigned = [index for chart in charts for index in chart]
        self.assertEqual(sorted(assigned), list(range(len(faces))))


class Packing(unittest.TestCase):
    def test_packed_uvs_stay_inside_the_unit_square(self) -> None:
        vertices, indices = unit_cube()
        result = unwrap({"vertices": vertices, "indices": indices})
        for u, v in result["uv"]:
            self.assertGreaterEqual(u, -1e-6)
            self.assertLessEqual(u, 1.0 + 1e-6)
            self.assertGreaterEqual(v, -1e-6)

    def test_packing_reports_efficiency_rather_than_claiming_optimality(self) -> None:
        vertices, indices = unit_cube()
        result = unwrap({"vertices": vertices, "indices": indices})
        self.assertGreater(result["packingEfficiency"], 0.0)
        self.assertLessEqual(result["packingEfficiency"], 1.0)
        self.assertTrue(any("heuristic" in note for note in result["notes"]))

    def test_empty_chart_list_does_not_crash_the_packer(self) -> None:
        packed, efficiency = pack_charts([])
        self.assertEqual(packed, [])
        self.assertEqual(efficiency, 0.0)


class SeamHonesty(unittest.TestCase):
    def test_multi_chart_mesh_reports_its_seam_vertices(self) -> None:
        # A cube corner belongs to three charts and therefore carries three UVs. Whichever is written
        # last wins, so the bake needs to know which vertices must be duplicated first.
        vertices, indices = unit_cube()
        result = unwrap({"vertices": vertices, "indices": indices})
        self.assertGreater(result["seamVertexCount"], 0)
        self.assertTrue(any("duplicated" in note for note in result["notes"]))


class DegenerateInput(unittest.TestCase):
    def test_empty_vertices_raise(self) -> None:
        with self.assertRaises(ValueError):
            unwrap({"vertices": [], "indices": [0, 1, 2]})

    def test_too_few_indices_raise(self) -> None:
        with self.assertRaises(ValueError):
            unwrap({"vertices": [[0, 0, 0]], "indices": []})

    def test_grouped_and_flat_index_encodings_agree(self) -> None:
        vertices, flat = planar_grid(3)
        grouped = [flat[i:i + 3] for i in range(0, len(flat), 3)]
        self.assertEqual(
            unwrap({"vertices": vertices, "indices": flat})["uv"],
            unwrap({"vertices": vertices, "indices": grouped})["uv"],
        )


if __name__ == "__main__":
    unittest.main()
