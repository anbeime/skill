#!/usr/bin/env python3
"""Tests for the bounded correction-loop stop policy (§3.6).

Pure stdlib unittest. The termination guarantee (test_hard_ceiling_always_terminates
and test_loop_cannot_exceed_max_iter) is the load-bearing property of this suite.
"""

import io
import json
import math
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "stage4_review"))

from correction_loop import budget_exceeded, decide, main  # noqa: E402


def _it(fidelity, defect_tags=None, reverted=False, hard_gate_failures=None):
    """Build one iteration record."""
    record = {
        "fidelity": fidelity,
        "defectTags": list(defect_tags or []),
        "reverted": reverted,
    }
    if hard_gate_failures is not None:
        record["hardGateFailures"] = list(hard_gate_failures)
    return record


class CorrectionLoopTest(unittest.TestCase):
    def test_empty_history_continues(self):
        d = decide([])
        self.assertFalse(d["stop"])
        self.assertEqual(d["action"], "continue-iterating")
        self.assertEqual(d["reason"], "no iterations yet")

    def test_success_when_target_met_and_no_defects(self):
        d = decide([_it(0.90, [])])
        self.assertTrue(d["stop"])
        self.assertEqual(d["action"], "continue")

    def test_success_requires_no_defects(self):
        # Fidelity above target BUT open defects remain -> NOT success.
        d = decide([_it(0.95, ["visible-seam"])])
        self.assertNotEqual(d["action"], "continue")

    def test_success_requires_no_hard_gate_failures(self):
        d = decide([_it(0.95, [], hard_gate_failures=["scale"])])
        self.assertTrue(d["stop"])
        self.assertEqual(d["action"], "refine-code")
        self.assertIn("hard gate", d["reason"])

    def test_pending_review_blocks_success_and_preserves_routing(self):
        cases = (("probe", "low-confidence", "request-input"), ("refine-code", "reject", "refine-code"), ("refine-spec", "withhold", "refine-spec"), ("continue", "reject", "request-input"))
        for action, verdict, expected_action in cases:
            with self.subTest(action=action, verdict=verdict):
                history = [{"fidelity": 0.95, "defectTags": [], "reverted": False, "pendingReview": True, "divineEyeAction": action, "divineEyeVerdict": verdict}]
                d = decide(history)
                self.assertTrue(d["stop"])
                self.assertEqual(d["action"], expected_action)
                self.assertIn("pending Divine Eye review", d["reason"])

    def test_non_approved_routing_overrides_forged_pending_false(self):
        history = [{"fidelity": 0.95, "defectTags": [], "reverted": False, "pendingReview": False, "divineEyeAction": "probe", "divineEyeVerdict": "low-confidence"}]

        d = decide(history)

        self.assertTrue(d["stop"])
        self.assertEqual(d["action"], "request-input")

    def test_nested_divine_eye_provenance_drives_pending_routing(self):
        history = [{"fidelity": 0.95, "defectTags": [], "reverted": False, "divineEye": {"fidelity": 0.95, "action": "probe", "verdict": "low-confidence"}}]

        d = decide(history)

        self.assertTrue(d["stop"])
        self.assertEqual(d["action"], "request-input")

    def test_nested_divine_eye_rejects_tampered_top_level_routing(self):
        history = [{"fidelity": 0.95, "defectTags": [], "reverted": False, "pendingReview": False, "divineEye": {"fidelity": 0.95, "action": "probe", "verdict": "low-confidence"}}]

        with self.assertRaises(ValueError) as raised:
            decide(history)

        self.assertIn("pendingReview conflicts", str(raised.exception))

    def test_nested_divine_eye_rejects_tampered_top_level_fidelity(self):
        history = [{"fidelity": 0.95, "defectTags": [], "reverted": False, "divineEye": {"fidelity": 0.5}}]

        with self.assertRaises(ValueError) as raised:
            decide(history)

        self.assertIn("fidelity conflicts", str(raised.exception))

    def test_decide_rejects_invalid_configuration_and_history_records(self):
        valid_history = [_it(0.9, [])]
        cases = (
            ([], {"target_fidelity": math.nan}, "target_fidelity"),
            ([], {"max_iter": True}, "max_iter"),
            ([], {"max_iter": 1.5}, "max_iter"),
            ([], {"min_delta": math.nan}, "min_delta"),
            ([], {"min_delta": -0.1}, "min_delta"),
            ([{"fidelity": math.nan, "defectTags": [], "reverted": False}], {}, "history[0].fidelity"),
            ([{"fidelity": 0.9, "defectTags": [1], "reverted": False}], {}, "history[0].defectTags"),
            ([{"fidelity": 0.9, "defectTags": [], "hardGateFailures": [1], "reverted": False}], {}, "history[0].hardGateFailures"),
            ([{"fidelity": 0.9, "defectTags": [], "pendingReview": 1, "reverted": False}], {}, "history[0].pendingReview"),
            ([{"fidelity": 0.9, "defectTags": [], "divineEyeAction": 1, "reverted": False}], {}, "history[0].divineEyeAction"),
            ([{"fidelity": 0.9, "defectTags": [], "divineEyeVerdict": 1, "reverted": False}], {}, "history[0].divineEyeVerdict"),
            ([{"fidelity": 0.9, "defectTags": [], "reverted": 1}], {}, "history[0].reverted"),
        )
        self.assertEqual(decide(valid_history)["action"], "continue")
        for history, options, field in cases:
            with self.subTest(field=field):
                with self.assertRaises(ValueError) as raised:
                    decide(history, **options)
                self.assertIn(field, str(raised.exception))

    def test_cli_rejects_invalid_configuration_and_history_without_traceback(self):
        cases = (
            ({"history": [_it(0.9, [])]}, ["--target", "nan"], "target"),
            ({"history": [_it(0.9, [])]}, ["--max-iter", "0"], "max_iter"),
            ({"history": [_it(0.9, [])]}, ["--min-delta", "-0.1"], "min_delta"),
            ({"history": [{"fidelity": 1.1, "defectTags": [], "reverted": False}]}, [], "history[0].fidelity"),
            ({"history": [{"fidelity": 0.9, "defectTags": ["ok", 1], "reverted": False}]}, [], "history[0].defectTags"),
            ({"history": [{"fidelity": 0.9, "defectTags": [], "hardGateFailures": [1], "reverted": False}]}, [], "history[0].hardGateFailures"),
            ({"history": [{"fidelity": 0.9, "defectTags": [], "reverted": 1}]}, [], "history[0].reverted"),
        )
        with tempfile.TemporaryDirectory() as directory:
            for index, (payload, options, field) in enumerate(cases):
                with self.subTest(field=field):
                    history_path = Path(directory) / f"invalid-{index}.json"
                    history_path.write_text(json.dumps(payload["history"]), encoding="utf-8")
                    stdout = io.StringIO()
                    with redirect_stdout(stdout):
                        exit_code = main(["--history", str(history_path), "--json", *options])
                    self.assertEqual(exit_code, 2)
                    self.assertIn(field, stdout.getvalue())
                    self.assertNotIn("Traceback", stdout.getvalue())

    def test_cli_routes_forged_pending_false_probe_to_request_input(self):
        history = [{"fidelity": 0.95, "defectTags": [], "reverted": False, "pendingReview": False, "divineEyeAction": "probe", "divineEyeVerdict": "low-confidence"}]
        with tempfile.TemporaryDirectory() as directory:
            history_path = Path(directory) / "pending-review.json"
            history_path.write_text(json.dumps(history), encoding="utf-8")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["--history", str(history_path), "--json"])

        self.assertEqual(exit_code, 1)
        self.assertIn("request-input", stdout.getvalue())

    def test_cli_rejects_tampered_nested_divine_eye_routing(self):
        history = [{"fidelity": 0.95, "defectTags": [], "reverted": False, "pendingReview": False, "divineEye": {"fidelity": 0.95, "action": "probe", "verdict": "low-confidence"}}]
        with tempfile.TemporaryDirectory() as directory:
            history_path = Path(directory) / "tampered-provenance.json"
            history_path.write_text(json.dumps(history), encoding="utf-8")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["--history", str(history_path), "--json"])

        self.assertEqual(exit_code, 2)
        self.assertIn("pendingReview conflicts", stdout.getvalue())

    def test_cli_rejects_tampered_nested_divine_eye_fidelity(self):
        history = [{"fidelity": 0.95, "defectTags": [], "reverted": False, "divineEye": {"fidelity": 0.5}}]
        with tempfile.TemporaryDirectory() as directory:
            history_path = Path(directory) / "tampered-fidelity.json"
            history_path.write_text(json.dumps(history), encoding="utf-8")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["--history", str(history_path), "--json"])

        self.assertEqual(exit_code, 2)
        self.assertIn("fidelity conflicts", stdout.getvalue())

    def test_repeated_defect_stops_refine_spec(self):
        history = [
            _it(0.60, ["seam"]),
            _it(0.72, ["seam", "gap"]),
        ]
        d = decide(history)
        self.assertTrue(d["stop"])
        self.assertEqual(d["action"], "refine-spec")
        self.assertIn("seam", d["reason"])

    def test_plateau_stops_request_input(self):
        # Second iteration improves by < min_delta and stays below target.
        history = [
            _it(0.60, []),
            _it(0.61, []),
        ]
        d = decide(history)
        self.assertTrue(d["stop"])
        self.assertEqual(d["action"], "request-input")

    def test_hard_ceiling_always_terminates(self):
        # Steadily improving (delta 0.05 > min_delta so PLATEAU cannot fire),
        # never reaching target 0.85, no shared defect tags, no reverts.
        history = [
            _it(0.50, []),
            _it(0.55, []),
            _it(0.60, []),
            _it(0.65, []),
            _it(0.70, []),
            _it(0.75, []),
        ]
        self.assertEqual(len(history), 6)  # == default max_iter
        d = decide(history)
        self.assertTrue(d["stop"])
        self.assertIn("ceiling", d["reason"].lower())

    def test_oscillation_two_consecutive_reverts_stops(self):
        history = [
            _it(0.50, [], reverted=False),
            _it(0.40, [], reverted=True),
            _it(0.30, [], reverted=True),
        ]
        d = decide(history)
        self.assertTrue(d["stop"])
        self.assertEqual(d["action"], "refine-spec")
        self.assertEqual(d["reason"], "oscillating/thrashing")

    def test_interrupted_reverts_do_not_oscillate(self):
        history = [
            _it(0.50, [], reverted=True),
            _it(0.60, [], reverted=False),
            _it(0.70, [], reverted=True),
        ]

        d = decide(history)

        self.assertFalse(d["stop"])
        self.assertEqual(d["action"], "continue-iterating")

    def test_score_flip_without_reverts_does_not_oscillate(self):
        history = [
            _it(0.50, []),
            _it(0.70, []),
            _it(0.60, []),
        ]

        d = decide(history)

        self.assertEqual(d["action"], "request-input")
        self.assertEqual(d["reason"], "progress plateaued below target (Δ<min_delta)")

    def test_loop_cannot_exceed_max_iter(self):
        # Simulate a real caller loop. Even with monotonic tiny improvements,
        # the body MUST execute at most max_iter times. A hard safety counter
        # fails the test if the loop somehow refuses to terminate.
        max_iter = 6
        history = []
        iterations = 0
        safety = 0
        while not decide(history, max_iter=max_iter)["stop"]:
            safety += 1
            if safety > 100:
                self.fail("did not terminate")
            history.append(_it(0.001 * (len(history) + 1), []))
            iterations += 1
        self.assertLessEqual(iterations, max_iter)

    def test_budget_exceeded_helper(self):
        self.assertTrue(budget_exceeded(100, 100))
        self.assertTrue(budget_exceeded(101, 100))
        self.assertFalse(budget_exceeded(99, 100))

    def test_budget_exceeded_rejects_invalid_inputs(self):
        cases = ((True, 1, "spent_tokens"), (-1, 1, "spent_tokens"), (math.nan, 1, "spent_tokens"), (1, True, "budget"), (1, -1, "budget"), (1, 1.5, "budget"))
        for spent_tokens, budget, field in cases:
            with self.subTest(field=field, value=spent_tokens if field == "spent_tokens" else budget):
                with self.assertRaises(ValueError) as raised:
                    budget_exceeded(spent_tokens, budget)
                self.assertIn(field, str(raised.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
