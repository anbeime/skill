#!/usr/bin/env python3
"""Decimation has to reach generated geometry, and has to land before skin binding.

`decimate.py` implemented Garland-Heckbert quadric collapse and then sat unreachable: it reads
a mesh FILE, and this pipeline emits TypeScript that builds geometry in the browser, so there
was no mesh for it to read. Its own docstring records the symptom — "`lodPlan` is validated in
three places in this repository and generated in none".

The port lives in the emitted runtime instead. What these tests pin:

  1. It is opt-in — a spec that does not ask for it gets no helper and no cost.
  2. The ratio actually reaches the emitted call.
  3. It runs BEFORE the bind pass. This is the load-bearing one: a quadric collapse merges two
     vertices, and skinIndex/skinWeight would have to be interpolated across that merge to stay
     correct. Because the bind pass recomputes weights from `position` afterwards, decimating
     first means no skinning data is ever carried across a merge. Ordering it the other way
     round would be silently wrong rather than loudly broken.
  4. UVs cannot be silently destroyed — decimation keeps position only.
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "_shared"), str(ROOT / "stage2_spec"), str(ROOT / "stage3_build")]

from generate_threejs_factory import decimate_ratio, generate  # noqa: E402
from validate_sculpt_spec import validate_spec  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "implicit_character_torso_limb.json"


def load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def with_decimation(ratio: object) -> dict:
    spec = load_fixture()
    spec["componentTree"][0]["geometryDescriptor"]["decimate"] = {"targetRatio": ratio}
    return spec


class RatioReadingTest(unittest.TestCase):
    def test_absent_descriptor_means_no_decimation(self) -> None:
        self.assertIsNone(decimate_ratio({}))
        self.assertIsNone(decimate_ratio({"geometryDescriptor": {}}))
        self.assertIsNone(decimate_ratio({"geometryDescriptor": {"decimate": {}}}))

    def test_out_of_range_ratios_are_ignored(self) -> None:
        for bad in (0, 1, 1.5, -0.5, "0.5", True, None):
            component = {"geometryDescriptor": {"decimate": {"targetRatio": bad}}}
            self.assertIsNone(decimate_ratio(component), bad)

    def test_a_usable_ratio_is_returned(self) -> None:
        component = {"geometryDescriptor": {"decimate": {"targetRatio": 0.4}}}
        self.assertEqual(decimate_ratio(component), 0.4)


class EmissionTest(unittest.TestCase):
    def test_helper_is_absent_when_nothing_asks_for_it(self) -> None:
        """Opt-in matters: a quadric pass on page load is real work, not a free default."""
        generated = generate(load_fixture(), "form-pass")
        self.assertNotIn("function decimateGeometry", generated)
        self.assertNotIn("decimateGeometry(", generated)

    def test_helper_and_call_appear_with_the_requested_ratio(self) -> None:
        generated = generate(with_decimation(0.4), "form-pass")
        self.assertIn("function decimateGeometry", generated)
        self.assertIn("decimateGeometry(", generated)
        self.assertIn(", 0.4);", generated)

    def test_decimation_is_emitted_before_the_skin_weight_pass(self) -> None:
        """The whole reason for the ordering: weights are recomputed from the survivors.

        If the call moved after the bind pass, skinIndex/skinWeight would be interpolated
        across vertex merges instead — the exact failure this ordering avoids.
        """
        generated = generate(with_decimation(0.4), "form-pass")
        call = generated.find("decimateGeometry(")
        self.assertGreater(call, -1)
        for marker in ("setAttribute('skinIndex'", "setAttribute('skinWeight'"):
            where = generated.find(marker)
            if where == -1:
                continue
            self.assertLess(call, where, f"decimation must precede {marker}")

    def test_the_dense_source_is_kept_addressable(self) -> None:
        """The pre-decimation geometry gets its own name rather than being inlined away."""
        generated = generate(with_decimation(0.4), "form-pass")
        self.assertIn("GeometryDense", generated)


class ValidationTest(unittest.TestCase):
    def test_a_sane_ratio_validates(self) -> None:
        errors, _warnings = validate_spec(with_decimation(0.4))
        self.assertEqual([e for e in errors if "decimate" in e], [])

    def test_ratios_outside_the_open_unit_interval_are_rejected(self) -> None:
        for bad in (0, 1, 1.5, -0.2):
            errors, _warnings = validate_spec(with_decimation(bad))
            self.assertTrue(
                any("targetRatio must be greater than 0 and less than 1" in e for e in errors),
                f"{bad} was accepted: {errors}",
            )

    def test_a_non_numeric_ratio_is_rejected(self) -> None:
        errors, _warnings = validate_spec(with_decimation("half"))
        self.assertTrue(any("targetRatio must be a number" in e for e in errors), errors)

    def test_decimation_is_refused_on_authored_uvs(self) -> None:
        """A quadric collapse has no correct UV for the merged vertex, so the seam would move."""
        spec = with_decimation(0.4)
        spec["componentTree"][0]["geometryDescriptor"]["uvStrategy"] = "authored unwrap"
        errors, _warnings = validate_spec(spec)
        self.assertTrue(any("drops UVs" in e for e in errors), errors)

    def test_generated_uv_strategies_stay_allowed(self) -> None:
        spec = with_decimation(0.4)
        spec["componentTree"][0]["geometryDescriptor"]["uvStrategy"] = (
            "generated procedural coordinates"
        )
        errors, _warnings = validate_spec(spec)
        self.assertEqual([e for e in errors if "drops UVs" in e], [])


if __name__ == "__main__":
    unittest.main()
