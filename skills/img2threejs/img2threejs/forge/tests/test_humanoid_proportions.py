#!/usr/bin/env python3
"""A reference-free humanoid must be expressible without fabricating anatomy.

`validate_sculpt_spec.py` blocks a character spec until `anatomy.applies` is true, which is
correct when a reference exists — a specific person's proportions are evidence. It also made
"build me a stylized humanoid, no reference" impossible to state. `humanoid_proportions.py`
supplies public figure-drawing canon for that case and labels it as canon.

The properties worth pinning are the honesty ones: canon must never masquerade as measured
evidence, and a head count the corpus does not actually cover must fail loudly rather than
be interpolated into existence.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path[:0] = [str(ROOT / "stage2_spec"), str(ROOT / "_shared")]

from humanoid_proportions import (  # noqa: E402
    CANON_BY_HEADS,
    PARTIAL_CANON_BY_HEADS,
    SUPPORTED_HEADS,
    apply_to_spec,
    derive_anatomy,
)
from validate_sculpt_spec import is_number  # noqa: E402


class CanonTest(unittest.TestCase):
    def test_eight_head_canon_satisfies_the_character_gate(self) -> None:
        """The gate wants a positive torso OR legs head-unit ratio, plus a face landmark."""
        anatomy = derive_anatomy(8)
        self.assertIs(anatomy["applies"], True)
        proportions = anatomy["proportions"]
        self.assertTrue(
            any(is_number(proportions.get(k)) and float(proportions[k]) > 0
                for k in ("torso", "legs")),
            proportions,
        )
        landmarks = anatomy["faceLandmarks"]
        self.assertTrue(
            any(is_number(landmarks.get(k)) and float(landmarks[k]) > 0
                for k in ("eyeLine", "noseBase", "mouthLine")),
            landmarks,
        )

    def test_the_classic_head_torso_legs_split_adds_up(self) -> None:
        anatomy = derive_anatomy(8)
        proportions = anatomy["proportions"]
        self.assertEqual(proportions["torso"], 3.0)
        self.assertEqual(proportions["legs"], 4.0)
        # head (1) + torso (3) + legs (4) == styleHeads
        self.assertEqual(1 + proportions["torso"] + proportions["legs"], 8)

    def test_canon_is_labelled_as_canon_not_as_reference(self) -> None:
        self.assertEqual(derive_anatomy(8)["source"], "canon-table")

    def test_unsourced_landmarks_are_named_rather_than_invented(self) -> None:
        anatomy = derive_anatomy(8)
        self.assertTrue(anatomy["unsourced"])
        for key in anatomy["unsourced"]:
            self.assertNotIn(key, anatomy["proportions"], f"{key} is listed unsourced yet present")


class IncompleteCanonTest(unittest.TestCase):
    def test_a_head_count_without_a_hip_line_is_refused(self) -> None:
        """4-head limb lengths are sourced; its hip line is not, so it must not be derived.

        The corpus was asked directly for the 4-head hip line, torso span, leg span and
        shoulder width and answered NOT IN SOURCES for all four.
        """
        self.assertIn(4, PARTIAL_CANON_BY_HEADS)
        self.assertNotIn(4, CANON_BY_HEADS)
        with self.assertRaises(ValueError) as caught:
            derive_anatomy(4)
        message = str(caught.exception)
        self.assertIn("hipLineY", message)
        self.assertIn("4", message)

    def test_supported_heads_are_exactly_the_complete_tables(self) -> None:
        self.assertEqual(set(SUPPORTED_HEADS), set(CANON_BY_HEADS))

    def test_nonsense_head_counts_are_refused(self) -> None:
        for bad in (0, -8, "8", True, None):
            with self.assertRaises(ValueError):
                derive_anatomy(bad)


class SpecApplicationTest(unittest.TestCase):
    def test_canon_is_refused_when_the_spec_names_a_reference(self) -> None:
        """Otherwise a gate that demands evidence silently starts accepting a default."""
        with self.assertRaises(ValueError) as caught:
            apply_to_spec({"sourceImage": "warrior.png"}, 8)
        self.assertIn("measure anatomy from it", str(caught.exception))

    def test_canon_is_allowed_when_there_is_no_reference(self) -> None:
        for spec in ({}, {"sourceImage": ""}, {"sourceImage": "/dev/null"}):
            filled = apply_to_spec(dict(spec), 8)
            self.assertIs(filled["preSpecAssessment"]["anatomy"]["applies"], True)


if __name__ == "__main__":
    unittest.main()
