#!/usr/bin/env python3
"""`performanceBudget.targetTriangles` must actually reach the emitted geometry.

The field was in the schema and read by nothing — `validate_sculpt_spec.py` checked only
that `performanceBudget` was an object, and the generator never opened it. A 61-component
humanoid spec therefore built 14,208 triangles no matter what budget it declared, because
every primitive's segment counts were module-level constants. Measured, not inferred: the
emitted factory was constructed under node and its triangles counted.

These tests pin the three properties that make the tier mechanism worth having:
  1. a spec that declares no budget generates exactly what it generated before tiers existed,
  2. a smaller budget really does emit coarser primitives,
  3. no tier may drop below the segment floors that skinning deformation depends on.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "_shared"), str(ROOT / "stage2_spec"), str(ROOT / "stage3_build")]

from subdivision import (  # noqa: E402
    CYLINDER_HEIGHT_SEGMENTS,
    CYLINDER_RADIAL_SEGMENTS,
    DEFAULT_TESSELLATION_TIER,
    MIN_JOINT_HEIGHT_SEGMENTS,
    MIN_RADIAL_SEGMENTS,
    SPHERE_HEIGHT_SEGMENTS,
    SPHERE_WIDTH_SEGMENTS,
    TESSELLATION_TIERS,
    segments_for_spec,
    tier_for_target_triangles,
    validate_tier,
)


class TierSelectionTest(unittest.TestCase):
    def test_absent_or_unusable_budget_keeps_the_pre_tier_behaviour(self) -> None:
        for value in (None, 0, -1, "3000", True, float("nan") * 0 - 1):
            self.assertEqual(tier_for_target_triangles(value), DEFAULT_TESSELLATION_TIER, value)
        self.assertEqual(segments_for_spec({}), TESSELLATION_TIERS[DEFAULT_TESSELLATION_TIER])
        self.assertEqual(
            segments_for_spec({"performanceBudget": {}}),
            TESSELLATION_TIERS[DEFAULT_TESSELLATION_TIER],
        )

    def test_budget_maps_to_a_coarser_tier(self) -> None:
        self.assertEqual(tier_for_target_triangles(3_000), "low")
        self.assertEqual(tier_for_target_triangles(6_000), "low")
        self.assertEqual(tier_for_target_triangles(20_000), "standard")
        self.assertEqual(tier_for_target_triangles(250_000), "hero")

    def test_hero_tier_is_the_module_constants(self) -> None:
        """Backwards compatibility is a property, not a hope: `hero` must BE the old values."""
        hero = TESSELLATION_TIERS["hero"]
        self.assertEqual(hero["SPHERE_WIDTH_SEGMENTS"], SPHERE_WIDTH_SEGMENTS)
        self.assertEqual(hero["SPHERE_HEIGHT_SEGMENTS"], SPHERE_HEIGHT_SEGMENTS)
        self.assertEqual(hero["CYLINDER_RADIAL_SEGMENTS"], CYLINDER_RADIAL_SEGMENTS)
        self.assertEqual(hero["CYLINDER_HEIGHT_SEGMENTS"], CYLINDER_HEIGHT_SEGMENTS)


class TierFloorTest(unittest.TestCase):
    def test_every_shipped_tier_clears_the_deformation_floors(self) -> None:
        for name in TESSELLATION_TIERS:
            validate_tier(name)  # raises if a floor is violated

    def test_the_joint_floor_matches_the_in_repo_precedent_not_the_textbook(self) -> None:
        """External practice says 3 loops at a joint; this repo already decided 3 was too few.

        `emit_rig.py:399` derives `max(4, ceil(cyl_length / target_ring_spacing))` — a hard
        floor of 4 — in the same module whose NOTES.md documents the single-quad-band
        joint-pinch failure. A measurement made here outranks a rule of thumb made elsewhere.
        """
        self.assertEqual(MIN_JOINT_HEIGHT_SEGMENTS, 4)
        for name, table in TESSELLATION_TIERS.items():
            for key in ("CYLINDER_HEIGHT_SEGMENTS", "ATTACHMENT_CYLINDER_HEIGHT_SEGMENTS"):
                self.assertGreaterEqual(table[key], 4, f"{name}.{key}")

    def test_cone_height_segments_is_pinned_out_of_the_budget_knobs(self) -> None:
        """A tapering cone welds to 0/0 only at 1; higher counts are a real topology defect."""
        for name, table in TESSELLATION_TIERS.items():
            self.assertEqual(table["CONE_HEIGHT_SEGMENTS"], 1, name)
        original = TESSELLATION_TIERS["low"]["CONE_HEIGHT_SEGMENTS"]
        TESSELLATION_TIERS["low"]["CONE_HEIGHT_SEGMENTS"] = 4
        try:
            with self.assertRaises(ValueError) as caught:
                validate_tier("low")
            self.assertIn("welds cleanly", str(caught.exception))
        finally:
            TESSELLATION_TIERS["low"]["CONE_HEIGHT_SEGMENTS"] = original

    def test_a_tier_below_the_joint_floor_is_refused(self) -> None:
        """One quad across a joint leaves no vertex at the pivot, so the joint collapses."""
        original = TESSELLATION_TIERS["low"]["CYLINDER_HEIGHT_SEGMENTS"]
        TESSELLATION_TIERS["low"]["CYLINDER_HEIGHT_SEGMENTS"] = MIN_JOINT_HEIGHT_SEGMENTS - 1
        try:
            with self.assertRaises(ValueError) as caught:
                validate_tier("low")
            self.assertIn("deform", str(caught.exception))
        finally:
            TESSELLATION_TIERS["low"]["CYLINDER_HEIGHT_SEGMENTS"] = original

    def test_a_tier_below_the_radial_floor_is_refused(self) -> None:
        original = TESSELLATION_TIERS["low"]["CAPSULE_RADIAL_SEGMENTS"]
        TESSELLATION_TIERS["low"]["CAPSULE_RADIAL_SEGMENTS"] = MIN_RADIAL_SEGMENTS - 1
        try:
            with self.assertRaises(ValueError) as caught:
                validate_tier("low")
            self.assertIn("round", str(caught.exception))
        finally:
            TESSELLATION_TIERS["low"]["CAPSULE_RADIAL_SEGMENTS"] = original

    def test_unknown_tier_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            validate_tier("potato")


class EmittedGeometryTest(unittest.TestCase):
    """The tier has to reach the generated source, not just the resolver."""

    def _emit(self, primitive: str, tier: str) -> str:
        from generate_threejs_factory import geometry_for

        return geometry_for(primitive, {}, False, TESSELLATION_TIERS[tier])

    def test_low_tier_emits_coarser_primitives_than_hero(self) -> None:
        for primitive in ("sphere", "cylinder", "capsule", "box"):
            hero = self._emit(primitive, "hero")
            low = self._emit(primitive, "low")
            self.assertNotEqual(hero, low, f"{primitive} ignored the tier")

    def test_default_argument_reproduces_the_hero_string(self) -> None:
        from generate_threejs_factory import geometry_for

        self.assertEqual(geometry_for("sphere", {}), self._emit("sphere", "hero"))
        self.assertEqual(
            geometry_for("sphere", {}),
            f"new THREE.SphereGeometry(0.5, {SPHERE_WIDTH_SEGMENTS}, {SPHERE_HEIGHT_SEGMENTS})",
        )


class SdfResolutionCapTest(unittest.TestCase):
    """An implicit surface has no segment counts, so the tier has to reach its sampling grid.

    Left uncapped it is the one unbudgeted source of triangles in an otherwise budgeted model.
    Marching-cubes output scales with the surface it crosses — O(N^2), measured on a capsule
    field at N = 64/96/128 → 3,432/7,840/13,960 crossing cells — so lowering the grid is a
    real lever, not a rounding error.
    """

    def _capped(self, resolution: int, tier: str) -> int:
        from generate_threejs_factory import capped_sdf

        result = capped_sdf({"resolution": resolution}, TESSELLATION_TIERS[tier])
        return result["resolution"]

    def test_low_tier_lowers_a_grid_above_its_ceiling(self) -> None:
        self.assertEqual(self._capped(32, "low"), TESSELLATION_TIERS["low"]["SDF_MAX_RESOLUTION"])

    def test_a_grid_already_below_the_ceiling_is_left_alone(self) -> None:
        """The cap must never make a deliberately coarse field denser."""
        self.assertEqual(self._capped(8, "low"), 8)
        self.assertEqual(self._capped(32, "hero"), 32)

    def test_a_descriptor_without_a_resolution_is_returned_unchanged(self) -> None:
        from generate_threejs_factory import capped_sdf

        descriptor = {"primitives": [], "operations": []}
        self.assertIs(capped_sdf(descriptor, TESSELLATION_TIERS["low"]), descriptor)

    def test_every_tier_declares_a_ceiling(self) -> None:
        for name, table in TESSELLATION_TIERS.items():
            self.assertIn("SDF_MAX_RESOLUTION", table, name)


class FlatShadingTest(unittest.TestCase):
    """The faceted low-poly look has to be expressible, and has to stay opt-in.

    three.js gives every face its own normals for flat shading, which needs unshared
    vertices — the geometry becomes non-indexed and the vertex count triples. Enabling it
    by default would silently spend the budget the tier mechanism exists to protect.
    """

    def _generated(self) -> str:
        import json

        from generate_threejs_factory import generate

        fixture = ROOT / "tests" / "fixtures" / "subdivision_cage.json"
        return generate(json.loads(fixture.read_text(encoding="utf-8")), "form-pass")

    def test_flat_shading_is_emitted_and_reads_from_the_material_spec(self) -> None:
        self.assertIn("flatShading: spec.flatShading === true", self._generated())

    def test_flat_shading_defaults_to_off(self) -> None:
        """`=== true` and nothing looser: a truthy stray value must not enable it."""
        generated = self._generated()
        self.assertNotIn("flatShading: spec.flatShading,", generated)
        self.assertNotIn("flatShading: !!spec.flatShading", generated)


if __name__ == "__main__":
    unittest.main()
