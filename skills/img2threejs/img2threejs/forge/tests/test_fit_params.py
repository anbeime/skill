#!/usr/bin/env python3
"""Contract tests for WS4 deterministic analysis-by-synthesis fitting."""

from __future__ import annotations

import io
import json
import math
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from forge.stage4_review.fit_params import (  # noqa: E402
    FitConfig,
    DivineEyeFitResult,
    FitInputError,
    NonFiniteScoreError,
    divine_eye_correction_history,
    divine_eye_fidelity,
    fit,
    fit_against_divine_eye,
    main,
)


def quadratic(target: tuple[float, ...]):
    return lambda values: 1.0 - sum((value - target[index]) ** 2 for index, value in enumerate(values))


class FitParamsTest(unittest.TestCase):
    def test_seeded_metadata_and_result_are_deterministic(self):
        config = FitConfig(seed=42, max_iterations=12, max_evaluations=100)

        first = fit((0.0, 0.0), ((-1.0, 1.0), (-1.0, 1.0)), quadratic((0.5, -0.5)), config)
        second = fit((0.0, 0.0), ((-1.0, 1.0), (-1.0, 1.0)), quadratic((0.5, -0.5)), config)

        self.assertEqual(first, second)
        self.assertEqual(first.seed, 42)

    def test_best_score_history_is_monotonic_and_normalizes_for_correction_loop(self):
        result = fit((0.0,), ((-1.0, 1.0),), quadratic((0.5,)), FitConfig(max_iterations=10, max_evaluations=100))

        scores = [record.best_score for record in result.history]
        self.assertEqual(scores, sorted(scores))
        history = result.to_correction_history(defect_tags=("detail-gap",))
        self.assertTrue(history)
        self.assertEqual(set(history[0]), {"fidelity", "defectTags", "reverted"})
        self.assertEqual(history[0]["defectTags"], ["detail-gap"])
        self.assertFalse(history[0]["reverted"])

    def test_stops_at_max_evaluations(self):
        result = fit((0.0,), ((-1.0, 1.0),), quadratic((0.8,)), FitConfig(max_iterations=20, max_evaluations=2))

        self.assertEqual(result.status, "max-evaluations")
        self.assertLessEqual(result.evaluations, 2)

    def test_budget_exhaustion_commits_evaluated_coordinate_improvement(self):
        result = fit((0.0,), ((-1.0, 1.0),), lambda values: -values[0], FitConfig(max_evaluations=2))

        self.assertEqual(result.status, "max-evaluations")
        self.assertEqual(result.parameters, (-0.5,))
        self.assertEqual(result.best_score, 0.5)
        self.assertEqual(result.history[-1].iteration, 1)
        self.assertTrue(result.history[-1].improved)

    def test_fit_against_divine_eye_runs_evaluator_and_preserves_provenance(self):
        scores = {"render-0.0.png": (0.5, []), "render--0.5.png": (0.2, ["scale"]), "render-0.5.png": (0.9, [])}
        rendered: list[tuple[float, ...]] = []
        evaluator_results: list[dict[str, object]] = []

        def render_for_parameters(parameters: tuple[float, ...]) -> Path:
            rendered.append(parameters)
            return Path(f"render-{parameters[0]:.1f}.png")

        def evaluator(reference: Path, render: Path) -> dict[str, object]:
            fidelity, gates = scores[render.name]
            result = {"fidelity": fidelity, "hardGateFailures": gates.copy(), "action": "refine-code" if gates else "continue", "signals": {"source": render.name}, "reference": str(reference), "render": str(render)}
            evaluator_results.append(result)
            return result

        result = fit_against_divine_eye((0.0,), ((-1.0, 1.0),), render_for_parameters, "reference.png", evaluator, FitConfig(max_iterations=1, max_evaluations=10))

        self.assertIsInstance(result, DivineEyeFitResult)
        self.assertEqual(result.fit_result.parameters, (0.5,))
        self.assertEqual(result.fit_result.best_score, 0.9)
        self.assertEqual(result.best_raw_fidelity, 0.9)
        self.assertEqual(len(rendered), 3)
        self.assertEqual(len(result.divine_eye_results), result.fit_result.evaluations)
        self.assertEqual(result.correction_history[1]["hardGateFailures"], ["scale"])
        self.assertEqual(result.correction_history[1]["divineEye"]["signals"], {"source": "render--0.5.png"})
        self.assertEqual(result.divine_eye_results[1]["fitCandidateParameters"], [-0.5])
        self.assertEqual(result.divine_eye_results[1]["fitReferencePng"], "reference.png")
        self.assertEqual(result.divine_eye_results[1]["fitRenderPath"], "render--0.5.png")
        self.assertEqual(result.to_json()["bestObjectiveScore"], 0.9)
        self.assertEqual(result.to_json()["bestRawFidelity"], 0.9)
        evaluator_results[1]["signals"]["source"] = "mutated"
        self.assertEqual(result.divine_eye_results[1]["signals"], {"source": "render--0.5.png"})

    def test_fit_against_divine_eye_snapshots_reused_evaluator_mapping(self):
        scores = {"render-0.0.png": (0.5, []), "render--0.5.png": (0.2, ["scale"]), "render-0.5.png": (0.9, [])}
        shared_result = {"fidelity": 0.0, "hardGateFailures": [], "signals": {"source": ""}}

        def render_for_parameters(parameters: tuple[float, ...]) -> Path:
            return Path(f"render-{parameters[0]:.1f}.png")

        def evaluator(_reference: Path, render: Path) -> dict[str, object]:
            fidelity, gates = scores[render.name]
            shared_result["fidelity"] = fidelity
            shared_result["hardGateFailures"] = gates
            shared_result["signals"]["source"] = render.name
            return shared_result

        result = fit_against_divine_eye((0.0,), ((-1.0, 1.0),), render_for_parameters, "reference.png", evaluator, FitConfig(max_iterations=1))

        self.assertEqual([item["fidelity"] for item in result.divine_eye_results], [0.5, 0.2, 0.9])
        self.assertEqual([item["divineEye"]["signals"]["source"] for item in result.correction_history], ["render-0.0.png", "render--0.5.png", "render-0.5.png"])
        self.assertEqual(result.correction_history[1]["hardGateFailures"], ["scale"])
        self.assertEqual([item["fitCandidateParameters"] for item in result.divine_eye_results], [[0.0], [-0.5], [0.5]])

    def test_fit_against_divine_eye_normalizes_fidelity_only_result_without_mutation(self):
        source_result = {"fidelity": 0.9}

        def render_for_parameters(parameters: tuple[float, ...]) -> Path:
            return Path(f"render-{parameters[0]:.1f}.png")

        def evaluator(_reference: Path, _render: Path) -> dict[str, object]:
            return source_result

        result = fit_against_divine_eye((0.0,), ((-1.0, 1.0),), render_for_parameters, "reference.png", evaluator, FitConfig(max_iterations=1))

        self.assertEqual(source_result, {"fidelity": 0.9})
        self.assertEqual(result.fit_result.best_score, 0.9)
        self.assertEqual(result.best_raw_fidelity, 0.9)
        self.assertTrue(all(item["hardGateFailures"] == [] for item in result.divine_eye_results))
        self.assertTrue(all(item["hardGateFailures"] == [] for item in result.correction_history))

    def test_fit_against_divine_eye_rejects_higher_fidelity_hard_gate_as_best(self):
        scores = {"render-0.0.png": (0.85, []), "render--0.5.png": (0.90, ["scale"]), "render-0.5.png": (0.80, [])}

        def render_for_parameters(parameters: tuple[float, ...]) -> Path:
            return Path(f"render-{parameters[0]:.1f}.png")

        def evaluator(_reference: Path, render: Path) -> dict[str, object]:
            fidelity, gates = scores[render.name]
            return {"fidelity": fidelity, "hardGateFailures": gates, "render": str(render)}

        result = fit_against_divine_eye((0.0,), ((-1.0, 1.0),), render_for_parameters, "reference.png", evaluator, FitConfig(max_iterations=1))

        self.assertEqual(result.fit_result.parameters, (0.0,))
        self.assertEqual(result.fit_result.best_score, 0.85)
        self.assertEqual(result.best_raw_fidelity, 0.85)
        self.assertEqual(result.divine_eye_results[1]["fidelity"], 0.90)
        self.assertEqual(result.correction_history[1]["hardGateFailures"], ["scale"])

    def test_fit_against_divine_eye_rejects_higher_fidelity_probe_as_best(self):
        scores = {"render-0.0.png": (0.85, "continue", "pass"), "render--0.5.png": (0.95, "probe", "low-confidence"), "render-0.5.png": (0.80, "continue", "pass")}

        def render_for_parameters(parameters: tuple[float, ...]) -> Path:
            return Path(f"render-{parameters[0]:.1f}.png")

        def evaluator(_reference: Path, render: Path) -> dict[str, object]:
            fidelity, action, verdict = scores[render.name]
            return {"fidelity": fidelity, "action": action, "verdict": verdict}

        result = fit_against_divine_eye((0.0,), ((-1.0, 1.0),), render_for_parameters, "reference.png", evaluator, FitConfig(max_iterations=1))

        self.assertEqual(result.fit_result.parameters, (0.0,))
        self.assertEqual(result.fit_result.best_score, 0.85)
        self.assertEqual(result.best_raw_fidelity, 0.85)
        self.assertEqual(result.divine_eye_results[1]["fidelity"], 0.95)
        self.assertTrue(result.correction_history[1]["pendingReview"])

    def test_fit_against_divine_eye_bounds_all_gated_runs_with_raw_provenance(self):
        def render_for_parameters(parameters: tuple[float, ...]) -> Path:
            return Path(f"render-{parameters[0]:.1f}.png")

        def evaluator(_reference: Path, render: Path) -> dict[str, object]:
            return {"fidelity": 0.90, "hardGateFailures": ["scale"], "render": str(render)}

        result = fit_against_divine_eye((0.0,), ((-1.0, 1.0),), render_for_parameters, "reference.png", evaluator, FitConfig(plateau_iterations=1))

        self.assertEqual(result.fit_result.status, "plateau")
        self.assertEqual(result.fit_result.best_score, -1.0)
        self.assertIsNone(result.best_raw_fidelity)
        self.assertTrue(all(item["fidelity"] == 0.90 for item in result.divine_eye_results))
        self.assertTrue(all(item["hardGateFailures"] == ["scale"] for item in result.correction_history))
        self.assertEqual([item["fidelity"] for item in result.correction_history], [0.90, 0.90, 0.90])

    def test_stops_on_plateau(self):
        result = fit((0.0,), ((-1.0, 1.0),), lambda _values: 0.5, FitConfig(plateau_iterations=1))

        self.assertEqual(result.status, "plateau")

    def test_stops_on_direction_oscillation(self):
        scores = {
            (0.5, 0.5): 0.0,
            (0.25, 0.5): 0.1,
            (0.25, 0.25): 0.2,
            (0.5, 0.25): 0.3,
            (0.5, 0.0): 0.4,
            (0.25, 0.0): 0.5,
        }

        def objective(values: tuple[float, ...]) -> float:
            return scores.get(tuple(round(value, 3) for value in values), -1.0)

        result = fit(
            (0.5, 0.5),
            ((0.0, 1.0), (0.0, 1.0)),
            objective,
            FitConfig(max_iterations=8, max_evaluations=100, min_improvement=1.0, plateau_iterations=4, oscillation_flips=2),
        )

        self.assertEqual(result.status, "oscillation")

    def test_non_consecutive_direction_flips_do_not_oscillate(self):
        scores = {
            (0.5, 0.5): 0.0,
            (0.25, 0.5): 0.1,
            (0.25, 0.25): 0.2,
            (0.5, 0.25): 0.3,
            (0.5, 0.0): 0.5,
            (0.25, 0.0): 0.6,
        }

        def objective(values: tuple[float, ...]) -> float:
            return scores.get(tuple(round(value, 3) for value in values), -1.0)

        result = fit(
            (0.5, 0.5),
            ((0.0, 1.0), (0.0, 1.0)),
            objective,
            FitConfig(max_iterations=6, max_evaluations=100, min_improvement=0.15, plateau_iterations=4, oscillation_flips=1),
        )

        self.assertNotEqual(result.status, "oscillation")

    def test_one_unstable_iteration_with_multiple_reversals_does_not_oscillate(self):
        scores = {
            (0.5, 0.5, 0.5): 0.0,
            (0.25, 0.5, 0.5): 0.1,
            (0.25, 0.25, 0.5): 0.2,
            (0.25, 0.25, 0.25): 0.3,
            (0.5, 0.25, 0.25): 0.4,
            (0.5, 0.5, 0.25): 0.5,
        }

        def objective(values: tuple[float, ...]) -> float:
            return scores.get(tuple(round(value, 3) for value in values), -1.0)

        result = fit(
            (0.5, 0.5, 0.5),
            ((0.0, 1.0), (0.0, 1.0), (0.0, 1.0)),
            objective,
            FitConfig(max_iterations=6, max_evaluations=100, min_improvement=1.0, plateau_iterations=3, oscillation_flips=2),
        )

        self.assertNotEqual(result.status, "oscillation")

    def test_smooth_quadratic_refinement_does_not_count_boundary_bracketing_as_oscillation(self):
        result = fit(
            (0.0,),
            ((-1.0, 1.0),),
            quadratic((0.2,)),
            FitConfig(max_iterations=20, max_evaluations=200, oscillation_flips=2),
        )

        self.assertNotEqual(result.status, "oscillation")
        self.assertGreater(result.best_score, 0.999)

    def test_rejects_invalid_bounds_and_non_finite_scores(self):
        with self.assertRaises(FitInputError):
            fit((0.0,) * 16, ((-1.0, 1.0),) * 16, quadratic((0.0,) * 16))
        with self.assertRaises(FitInputError):
            fit((2.0,), ((-1.0, 1.0),), quadratic((0.0,)))
        with self.assertRaises(NonFiniteScoreError):
            fit((0.0,), ((-1.0, 1.0),), lambda _values: math.nan)

    def test_direct_call_rejects_invalid_config_and_objective(self):
        cases = (
            (quadratic((0.0,)), None, "config"),
            (quadratic((0.0,)), {}, "config"),
            (None, FitConfig(), "objective"),
            (0, FitConfig(), "objective"),
        )

        for objective, config, field in cases:
            with self.subTest(field=field, value=objective if field == "objective" else config):
                with self.assertRaises(FitInputError) as raised:
                    fit((0.0,), ((-1.0, 1.0),), objective, config)
                self.assertEqual(raised.exception.field, field)

    def test_fit_config_rejects_invalid_limits_minimum_improvement_and_seed(self):
        cases = (
            ("max_iterations", 0, "config"), ("max_iterations", True, "config"),
            ("max_evaluations", 0, "config"), ("max_evaluations", True, "config"),
            ("plateau_iterations", 0, "config"), ("plateau_iterations", True, "config"),
            ("oscillation_flips", 0, "config"), ("oscillation_flips", True, "config"),
            ("min_improvement", -0.1, "config.min_improvement"), ("min_improvement", math.nan, "config.min_improvement"),
            ("min_improvement", math.inf, "config.min_improvement"),
            ("seed", True, "config.seed"), ("seed", 1.5, "config.seed"), ("seed", "seed", "config.seed"),
        )
        for field, value, expected_field in cases:
            with self.subTest(field=field, value=value):
                with self.assertRaises(FitInputError) as raised:
                    fit((0.0,), ((-1.0, 1.0),), quadratic((0.0,)), FitConfig(**{field: value}))
                self.assertEqual(raised.exception.field, expected_field)

    def test_rejects_malformed_bounds_with_field_specific_input_errors(self):
        for bounds, field in (([1], "bounds[0]"), ([[1]], "bounds[0]"), (["1,2"], "bounds[0]")):
            with self.subTest(bounds=bounds):
                with self.assertRaises(FitInputError) as raised:
                    fit((0.0,), bounds, quadratic((0.0,)))
                self.assertEqual(raised.exception.field, field)

    def test_cli_rejects_malformed_bounds_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "invalid-fit.json"
            input_path.write_text(json.dumps({"initial": [0.0], "bounds": [[1]], "target": [0.5], "config": {}}), encoding="utf-8")
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(["--input", str(input_path), "--json"])

        self.assertEqual(exit_code, 2)
        self.assertIn("bounds[0]", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_cli_rejects_unknown_config_keys_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "unknown-config.json"
            input_path.write_text(
                json.dumps({"initial": [0.0], "bounds": [[-1.0, 1.0]], "target": [0.5], "config": {"maxEvaluatons": 5}}),
                encoding="utf-8",
            )
            stderr = io.StringIO()
            with redirect_stderr(stderr):
                exit_code = main(["--input", str(input_path), "--json"])

        self.assertEqual(exit_code, 2)
        self.assertIn("maxEvaluatons", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_cli_requires_exact_top_level_schema(self):
        cases = (
            ({"initial": [0.0], "bounds": [[-1.0, 1.0]], "target": [0.5], "config": {}, "extra": True}, "extra"),
            ({"initial": [0.0], "bounds": [[-1.0, 1.0]], "target": [0.5]}, "config"),
        )
        with tempfile.TemporaryDirectory() as directory:
            for index, (payload, field) in enumerate(cases):
                with self.subTest(field=field):
                    input_path = Path(directory) / f"schema-{index}.json"
                    input_path.write_text(json.dumps(payload), encoding="utf-8")
                    stderr = io.StringIO()
                    with redirect_stderr(stderr):
                        exit_code = main(["--input", str(input_path), "--json"])
                    self.assertEqual(exit_code, 2)
                    self.assertIn(field, stderr.getvalue())
                    self.assertNotIn("Traceback", stderr.getvalue())

    def test_divine_eye_adapter_reads_fidelity_without_changing_gate_keys(self):
        result = {"fidelity": 0.75, "hardGateFailures": ["scale"], "action": "refine-code"}

        score = divine_eye_fidelity(result)

        self.assertEqual(score, 0.75)
        self.assertEqual(result["hardGateFailures"], ["scale"])
        self.assertEqual(result["action"], "refine-code")

    def test_divine_eye_adapter_rejects_invalid_fidelity(self):
        for score in (-0.1, 1.1, math.nan, math.inf, True):
            with self.subTest(score=score):
                with self.assertRaises(FitInputError) as raised:
                    divine_eye_fidelity({"fidelity": score})
                self.assertEqual(raised.exception.field, "Divine Eye result.fidelity")

    def test_divine_eye_adapter_rejects_non_mapping_results(self):
        for result in (None, "not-a-result", []):
            with self.subTest(result=result):
                with self.assertRaises(FitInputError) as raised:
                    divine_eye_fidelity(result)
                self.assertEqual(raised.exception.field, "Divine Eye result")

    def test_divine_eye_history_preserves_per_iteration_hard_gates_for_correction_loop(self):
        from forge.stage4_review.correction_loop import decide

        results = [
            {"fidelity": 0.9, "hardGateFailures": ["scale"], "action": "refine-code"},
            {"fidelity": 0.8, "hardGateFailures": [], "action": "continue"},
        ]

        history = divine_eye_correction_history(results)
        decision = decide(history[:1])

        self.assertEqual(history[0]["fidelity"], 0.9)
        self.assertEqual(history[0]["defectTags"], ["scale"])
        self.assertEqual(history[0]["hardGateFailures"], ["scale"])
        self.assertFalse(history[0]["reverted"])
        self.assertFalse(history[1]["reverted"])
        self.assertEqual(history[0]["divineEye"], results[0])
        self.assertEqual(results[0]["hardGateFailures"], ["scale"])
        self.assertEqual(results[0]["action"], "refine-code")
        self.assertTrue(decision["stop"])
        self.assertEqual(decision["action"], "refine-code")

    def test_divine_eye_history_compares_attempts_to_last_accepted_fidelity(self):
        history = divine_eye_correction_history([
            {"fidelity": 0.90},
            {"fidelity": 0.80},
            {"fidelity": 0.85},
        ])

        self.assertEqual([entry["reverted"] for entry in history], [False, True, True])

    def test_divine_eye_history_preserves_pending_review_routing(self):
        from forge.stage4_review.correction_loop import decide

        history = divine_eye_correction_history([{"fidelity": 0.95, "action": "probe", "verdict": "low-confidence"}])

        self.assertTrue(history[0]["pendingReview"])
        self.assertEqual(history[0]["divineEyeAction"], "probe")
        self.assertEqual(history[0]["divineEyeVerdict"], "low-confidence")
        self.assertEqual(decide(history)["action"], "request-input")

    def test_pending_high_fidelity_does_not_replace_approved_baseline(self):
        history = divine_eye_correction_history([
            {"fidelity": 0.95, "action": "probe", "verdict": "low-confidence"},
            {"fidelity": 0.90, "action": "continue", "verdict": "pass"},
        ])

        self.assertEqual([entry["reverted"] for entry in history], [False, False])

    def test_divine_eye_history_rejects_malformed_direct_inputs(self):
        cases = ((None, "results"), ("not-results", "results"), ([None], "results[0]"), ([0], "results[0]"))
        for results, field in cases:
            with self.subTest(field=field, results=results):
                with self.assertRaises(FitInputError) as raised:
                    divine_eye_correction_history(results)
                self.assertEqual(raised.exception.field, field)

    def test_hard_gated_result_does_not_replace_accepted_fidelity(self):
        history = divine_eye_correction_history([
            {"fidelity": 0.85},
            {"fidelity": 0.90, "hardGateFailures": ["scale"]},
            {"fidelity": 0.80},
        ])

        self.assertEqual([entry["reverted"] for entry in history], [False, False, True])

    def test_divine_eye_history_copies_rich_provenance(self):
        results = [{
            "fidelity": 0.8,
            "hardGateFailures": ["scale"],
            "action": "refine-code",
            "signals": {"ssim": 0.7},
            "reference": "reference.png",
            "render": "render.png",
        }]

        history = divine_eye_correction_history(results)
        results[0]["hardGateFailures"].append("silhouette")
        results[0]["signals"]["ssim"] = 0.1

        self.assertEqual(history[0]["divineEye"], {
            "fidelity": 0.8,
            "hardGateFailures": ["scale"],
            "action": "refine-code",
            "signals": {"ssim": 0.7},
            "reference": "reference.png",
            "render": "render.png",
        })

    def test_cli_json_roundtrip(self):
        payload = {
            "initial": [0.0, 0.0],
            "bounds": [[-1.0, 1.0], [-1.0, 1.0]],
            "target": [0.5, -0.5],
            "config": {"maxIterations": 8, "maxEvaluations": 100, "seed": 7},
        }
        with tempfile.TemporaryDirectory() as directory:
            input_path = Path(directory) / "fit.json"
            input_path.write_text(json.dumps(payload), encoding="utf-8")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                exit_code = main(["--input", str(input_path), "--json"])

        self.assertEqual(exit_code, 0)
        result = json.loads(stdout.getvalue())
        self.assertEqual(result["seed"], 7)
        self.assertLessEqual(result["evaluations"], 100)
        self.assertEqual(len(result["parameters"]), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
