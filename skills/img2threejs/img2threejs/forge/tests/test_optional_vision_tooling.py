from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "stage1_intake" / "run_vision_adapter.py"
SPEC = importlib.util.spec_from_file_location("run_vision_adapter", MODULE_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class OptionalVisionToolingTests(unittest.TestCase):
    def test_bridge_keeps_optional_runtime_outside_forge(self) -> None:
        expected = ROOT.parent / "integrations" / "vision" / ".venv" / "bin" / "python"
        self.assertEqual(MODULE.resolve_python(None), expected)
        command = MODULE.build_command(expected, ["health"])
        self.assertEqual(command[0], str(expected))
        self.assertEqual(command[1], str(ROOT.parent / "integrations" / "vision" / "reference_vision.py"))
        self.assertEqual(command[-1], "health")

    def test_explicit_interpreter_override_is_resolved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            candidate = Path(directory) / "python"
            self.assertEqual(MODULE.resolve_python(str(candidate)), candidate.resolve())

    def test_documentation_preserves_evidence_boundaries(self) -> None:
        documentation = (ROOT.parent / "docs" / "integrations" / "reference_fidelity_tooling.md").read_text(
            encoding="utf-8"
        )
        for phrase in (
            "diagnostic only",
            "relative prior only",
            "Never accept an MCP-only scene edit",
            "MCP diagnosis when needed",
        ):
            self.assertIn(phrase, documentation)

    def test_optional_environment_declares_all_three_vision_routes(self) -> None:
        project = (ROOT.parent / "integrations" / "vision" / "pyproject.toml").read_text(encoding="utf-8")
        for dependency in ("mediapipe", "torch", "transformers"):
            self.assertIn(f'"{dependency}', project)


if __name__ == "__main__":
    unittest.main()
