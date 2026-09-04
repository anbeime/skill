from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "stage4_review"))
sys.path.insert(0, str(ROOT / "stage3_build"))

from geometry_integrity import measure_geometry_integrity, mesh_edge_counts
from append_review import main as append_review_main
from orchestrate_passes import ledger_disagreements, pass_order


# The icosphere/punch_through fixtures live in the self-intersection suite. Reusing them keeps one
# definition of "a mesh punched through itself" instead of two that can silently diverge.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_self_intersection import icosphere, punch_through  # noqa: E402


class SelfIntersectionWiring(unittest.TestCase):
    """The gate is only worth having if the pipeline actually calls it.

    `self_intersection.py` shipped as a standalone CLI, which means it runs when somebody remembers to
    run it — and the defect it exists to catch survived eight review rounds precisely because nobody
    remembered. These two tests pin the call site itself: a punched-through mesh must fail
    `measure_geometry_integrity`, and a clean one must not.
    """

    @classmethod
    def setUpClass(cls) -> None:
        cls.vertices, cls.indices = icosphere(2)

    def _payload(self, vertices, indices):
        # Normals come from the CLEAN sphere, where the outward normal of a unit sphere is the position
        # itself. Deriving them from the punched positions instead would point the pushed cap's normals
        # backwards and the gate would be reading a fixture that no sculpt would ever produce.
        # They are supplied at all because measure_geometry_integrity independently requires normals for
        # watertight validation; without them the mesh fails for an unrelated reason and this test would
        # pass while proving nothing.
        normals = [list(v) for v in self.vertices]
        return {"meshes": [{"id": "skull", "vertices": vertices, "indices": indices, "normals": normals}]}

    def test_punched_through_mesh_fails_the_integrity_gate(self) -> None:
        vertices = punch_through(self.vertices)
        result = measure_geometry_integrity(self._payload(vertices, self.indices))
        report = result["meshes"][0] if "meshes" in result else result["reports"][0]

        self.assertTrue(report["selfIntersection"]["selfIntersecting"])
        self.assertTrue(any("selfIntersecting" in f for f in result["failures"]))
        # And the topological checks on the SAME mesh stay clean -- this is what makes the new call
        # site load-bearing rather than redundant with the ones already there.
        self.assertEqual(report["boundaryEdges"], 0)
        self.assertEqual(report["nonManifoldEdges"], 0)

    def test_clean_mesh_does_not_trip_the_new_failure(self) -> None:
        result = measure_geometry_integrity(self._payload(list(self.vertices), self.indices))
        report = result["meshes"][0] if "meshes" in result else result["reports"][0]
        self.assertFalse(report["selfIntersection"]["selfIntersecting"])
        self.assertFalse(any("selfIntersecting" in f for f in result["failures"]))


class StructureGateTest(unittest.TestCase):
    def test_coincident_vertices_are_merged_for_edge_counts(self) -> None:
        vertices = [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, 0, 0], [1, 0, 0], [0, 1, 0]]
        self.assertEqual(mesh_edge_counts(vertices, [0, 1, 2, 3, 5, 4])["boundaryEdges"], 0)

    def test_open_separate_geometry_fails_and_map_only_is_reported(self) -> None:
        result = measure_geometry_integrity({"meshes": [
            {"id": "hardware", "realization": "separate-geometry", "vertices": [[0, 0, 0], [1, 0, 0], [0, 1, 0]], "indices": [0, 1, 2]},
            {"id": "decal", "realization": "map-only"},
        ]})
        self.assertFalse(result["passed"])
        self.assertEqual(result["meshes"][0]["boundaryEdges"], 3)
        self.assertEqual(result["meshes"][1]["realization"], "map-only")
        self.assertTrue(any(issue["code"] == "watertight" and issue["severity"] == "error" for issue in result["issues"]))

    def test_open_integrated_geometry_is_also_watertight_error(self) -> None:
        result = measure_geometry_integrity({"meshes": [{
            "id": "body",
            "realization": "integrated",
            "vertices": [[0, 0, 0], [1, 0, 0], [0, 1, 0]],
            "indices": [0, 1, 2],
        }]})
        self.assertFalse(result["passed"])
        self.assertTrue(any(issue["code"] == "watertight" and issue["severity"] == "error" for issue in result["issues"]))

    def test_non_manifold_edges_are_severity_tagged(self) -> None:
        result = measure_geometry_integrity({"meshes": [{
            "id": "body",
            "vertices": [[0, 0, 0], [1, 0, 0], [0, 1, 0], [0, -1, 0], [0, 0, 1]],
            "indices": [0, 1, 2, 1, 0, 3, 0, 1, 4],
        }]})
        self.assertFalse(result["passed"])
        self.assertTrue(any(issue["code"] == "non-manifold" and issue["severity"] == "error" for issue in result["issues"]))

    def test_out_of_order_append_leaves_spec_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "spec.json"
            path.write_text(json.dumps({"buildPasses": [{"id": "blockout"}, {"id": "material-pass"}], "reviewHistory": []}) + "\n")
            before = path.read_bytes()
            with self.assertRaises(ValueError):
                append_review_main([str(path), "--pass-id", "material-pass", "--fidelity", "0.9", "--action", "stop", "--summary", "out of order"])
            self.assertEqual(path.read_bytes(), before)

    def test_sync_disagreement_names_uncredited_review(self) -> None:
        spec = {"buildPasses": [{"id": "blockout"}, {"id": "material-pass"}], "reviewHistory": [{"passId": "material-pass", "action": "continue"}]}
        self.assertTrue(any(item.startswith("material-pass:") for item in ledger_disagreements(spec, [])))

    def test_triangle_budget_requires_lod_and_is_severity_tagged(self) -> None:
        result = measure_geometry_integrity({
            "triangleBudget": 1,
            "meshes": [{
                "id": "dense-body",
                "realization": "integrated",
                "vertices": [[0, 0, 0], [1, 0, 0], [0, 1, 0]],
                "indices": [0, 1, 2, 0, 2, 1],
            }],
        })
        self.assertFalse(result["passed"])
        self.assertEqual(result["triangleCount"], 2)
        self.assertTrue(any(issue["code"] == "triangle-budget" and issue["severity"] == "error" for issue in result["issues"]))
        self.assertTrue(any(issue["code"] == "lod-required" and issue["severity"] == "error" for issue in result["issues"]))

    def test_triangle_budget_rejects_lod_tiers_without_reduction(self) -> None:
        result = measure_geometry_integrity({
            "triangleBudget": 1,
            "lodPlan": [
                {"tier": "near", "distance": 0, "triangleCount": 2},
                {"tier": "far", "distance": 30, "triangleCount": 2},
            ],
            "meshes": [{
                "id": "dense-body",
                "vertices": [[0, 0, 0], [1, 0, 0], [0, 1, 0]],
                "indices": [0, 1, 2, 0, 2, 1],
            }],
        })
        self.assertFalse(result["lodPlanValid"])
        self.assertTrue(any(issue["code"] == "lod-invalid" and issue["severity"] == "error" for issue in result["issues"]))

    def test_triangle_budget_accepts_lod_tiers_with_reduction(self) -> None:
        result = measure_geometry_integrity({
            "triangleBudget": 1,
            "lodPlan": [
                {"tier": "near", "distance": 0, "triangleCount": 2},
                {"tier": "far", "distance": 30, "triangleCount": 1},
            ],
            "meshes": [{
                "id": "dense-body",
                "vertices": [[0, 0, 0], [1, 0, 0], [0, 1, 0]],
                "indices": [0, 1, 2, 0, 2, 1],
            }],
        })
        self.assertTrue(result["lodPlanValid"])
        self.assertFalse(any(issue["code"] == "lod-invalid" for issue in result["issues"]))

    def test_inconsistent_normals_are_reported(self) -> None:
        result = measure_geometry_integrity({
            "meshes": [{
                "id": "body",
                "realization": "integrated",
                "vertices": [[0, 0, 0], [1, 0, 0], [0, 1, 0]],
                "indices": [0, 1, 2],
                "normals": [[0, 0, -1], [0, 0, -1], [0, 0, -1]],
            }],
        })
        self.assertFalse(result["passed"])
        self.assertTrue(any(issue["code"] == "normal-consistency" and issue["severity"] == "error" for issue in result["issues"]))

    def test_zero_length_normals_are_reported(self) -> None:
        result = measure_geometry_integrity({"meshes": [{
            "id": "body",
            "vertices": [[0, 0, 0], [1, 0, 0], [0, 1, 0]],
            "indices": [0, 1, 2],
            "normals": [[0, 0, 0], [0, 0, 0], [0, 0, 0]],
        }]})
        self.assertFalse(result["passed"])
        self.assertEqual(result["meshes"][0]["normalConsistency"]["invalidNormalTriangles"], 1)


if __name__ == "__main__":
    unittest.main()
