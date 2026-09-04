"""Attachment Anchor Gate tests.

One test per check, each built by mutating a single small valid fixture (a body with a
head/shoulder/upper-back component set, a matching bone rig, and a hat attachment anchored
to the upper back) so a passing baseline is proven before any failure mode is exercised.
Two tests reproduce the real hat and charm defects from the module docstring with concrete
measured positions, to prove ANCHOR_PROXIMITY actually catches them.
"""

from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "stage4_review"))

from attachment_anchor import analyze_attachments  # noqa: E402


def _tags(errors: list[str]) -> set[str]:
    return {message.split(":")[0] for message in errors}


def _base_spec() -> dict[str, Any]:
    """A body with head/shoulder/upper-back components, a bone rig, and a hat attachment
    anchored to `upper-back` (a component, not a bone) with an explicit maxOffset."""
    return {
        "componentTree": [
            {"id": "root", "name": "Body", "role": "body", "parent": None},
            {"id": "head", "name": "Head", "role": "body", "parent": "root"},
            {"id": "upper-back", "name": "Upper back", "role": "body", "parent": "root",
             "dimensions": {"width": 0.6, "height": 0.5, "depth": 0.3}},
            {"id": "shoulder-l", "name": "Left shoulder", "role": "body", "parent": "upper-back"},
            {
                "id": "hat", "name": "Conical hat", "role": "worn", "parent": "root",
                "attachment": {"anchor": "upper-back", "maxOffset": 0.5},
            },
        ],
        "rig": {
            "bones": [
                {"id": "root", "parent": None, "jointPos": [0.0, 0.0, 0.0]},
                {"id": "spine", "parent": "root", "jointPos": [0.0, 1.0, 0.0]},
                {"id": "shoulder-l", "parent": "spine", "jointPos": [0.3, 3.829, 0.0]},
            ],
        },
    }


class AttachmentAnchorGate(unittest.TestCase):
    def test_base_fixture_passes(self) -> None:
        result = analyze_attachments(_base_spec())
        self.assertEqual(result["errors"], [])
        self.assertTrue(result["passed"])
        self.assertEqual(result["attachmentCount"], 1)

    def test_missing_anchor_fires_anchor_declared(self) -> None:
        spec = copy.deepcopy(_base_spec())
        hat = next(c for c in spec["componentTree"] if c["id"] == "hat")
        del hat["attachment"]
        result = analyze_attachments(spec)
        self.assertEqual(_tags(result["errors"]), {"ANCHOR_DECLARED"})
        self.assertFalse(result["passed"])

    def test_dangling_anchor_fires_anchor_resolves(self) -> None:
        spec = copy.deepcopy(_base_spec())
        hat = next(c for c in spec["componentTree"] if c["id"] == "hat")
        hat["attachment"]["anchor"] = "does-not-exist"
        result = analyze_attachments(spec)
        self.assertEqual(_tags(result["errors"]), {"ANCHOR_RESOLVES"})
        self.assertFalse(result["passed"])

    def test_anchor_at_root_fires_anchor_not_root(self) -> None:
        spec = copy.deepcopy(_base_spec())
        hat = next(c for c in spec["componentTree"] if c["id"] == "hat")
        hat["attachment"]["anchor"] = "root"
        result = analyze_attachments(spec)
        self.assertEqual(_tags(result["errors"]), {"ANCHOR_NOT_ROOT"})
        self.assertFalse(result["passed"])

    def test_mutual_anchors_fire_anchor_not_cyclic(self) -> None:
        spec = copy.deepcopy(_base_spec())
        spec["componentTree"] += [
            {
                "id": "necklace", "name": "Necklace", "role": "worn", "parent": "root",
                "attachment": {"anchor": "amulet"},
            },
            {
                "id": "amulet", "name": "Amulet", "role": "worn", "parent": "root",
                "attachment": {"anchor": "necklace"},
            },
        ]
        result = analyze_attachments(spec)
        # The pre-existing hat attachment is untouched and still valid, so only the new
        # mutual pair should fire -- proving the check is scoped per attachment, not global.
        self.assertEqual(_tags(result["errors"]), {"ANCHOR_NOT_CYCLIC"})
        self.assertFalse(result["passed"])

    def test_hat_regression_anchor_proximity_fires_with_matching_distance(self) -> None:
        """Reproduces the real defect: shoulder joint at y 3.829, hat measured at y 2.5,
        against an authored maxOffset of 0.8. The anchor is switched to the shoulder BONE
        (not the `upper-back` component the base fixture uses), matching how the actual
        defect was measured against a rig joint."""
        spec = copy.deepcopy(_base_spec())
        hat = next(c for c in spec["componentTree"] if c["id"] == "hat")
        hat["attachment"] = {"anchor": "shoulder-l", "maxOffset": 0.8}
        measured = {"shoulder-l": [0.3, 3.829, 0.0], "hat": [0.3, 2.5, 0.0]}
        result = analyze_attachments(spec, measured=measured)
        self.assertEqual(_tags(result["errors"]), {"ANCHOR_PROXIMITY"})
        self.assertFalse(result["passed"])
        record = next(r for r in result["attachments"] if r["component"] == "hat")
        expected_distance = abs(3.829 - 2.5)
        self.assertAlmostEqual(record["distance"], expected_distance, places=9)
        self.assertEqual(record["maxOffset"], 0.8)
        self.assertFalse(record["withinLimit"])

    def test_charm_regression_anchor_proximity_fires_with_default_offset(self) -> None:
        """Reproduces the detached-charm defect: no maxOffset was ever authored, so the
        gate must derive one from the staff's own declared size (a thin 0.1-wide anchor)
        and still catch a real 0.389 detachment against that default."""
        spec = copy.deepcopy(_base_spec())
        spec["componentTree"] += [
            {"id": "staff", "name": "Staff", "role": "body", "parent": "root",
             "dimensions": {"radius": 0.05}},
            {
                "id": "charm", "name": "Charm", "role": "held", "parent": "root",
                "attachment": {"anchor": "staff"},
            },
        ]
        measured = {"staff": [0.0, 0.0, 0.0], "charm": [0.0, 0.0, 0.389]}
        result = analyze_attachments(spec, measured=measured)
        charm_errors = {m for m in result["errors"] if "charm" in m}
        self.assertTrue(any(m.startswith("ANCHOR_PROXIMITY") for m in charm_errors))
        record = next(r for r in result["attachments"] if r["component"] == "charm")
        self.assertAlmostEqual(record["distance"], 0.389, places=9)
        # extent = radius * 2 = 0.1; default limit = 0.1 * 0.25 = 0.025, well under 0.389
        self.assertAlmostEqual(record["maxOffset"], 0.025, places=9)
        self.assertIn("default", record["offsetRule"])
        self.assertFalse(record["withinLimit"])

    def test_no_attachments_passes_and_reports_zero_count(self) -> None:
        spec = copy.deepcopy(_base_spec())
        spec["componentTree"] = [c for c in spec["componentTree"] if c["id"] != "hat"]
        result = analyze_attachments(spec)
        self.assertEqual(result["errors"], [])
        self.assertTrue(result["passed"])
        self.assertEqual(result["attachmentCount"], 0)
        self.assertEqual(result["unmeasuredAttachments"], [])

    def test_component_absent_from_measured_lands_in_unmeasured(self) -> None:
        spec = _base_spec()
        # `measured` is supplied (so ANCHOR_PROXIMITY is in scope) but omits the hat itself --
        # this must not be silently treated as a pass, distinguishing it from the
        # zero-attachments case above (attachmentCount 1 here, not 0).
        result = analyze_attachments(spec, measured={"upper-back": [0.0, 3.0, 0.0]})
        self.assertEqual(result["attachmentCount"], 1)
        self.assertEqual(result["unmeasuredAttachments"], ["hat"])
        record = next(r for r in result["attachments"] if r["component"] == "hat")
        self.assertIsNone(record["withinLimit"])
        self.assertIsNone(record["distance"])
        self.assertTrue(any("hat" in w and "ANCHOR_PROXIMITY" in w for w in result["warnings"]))
        # Missing measurement is a visibility gap, not a structural defect, so it alone
        # must not flip the gate to failing.
        self.assertTrue(result["passed"])


if __name__ == "__main__":
    unittest.main()
