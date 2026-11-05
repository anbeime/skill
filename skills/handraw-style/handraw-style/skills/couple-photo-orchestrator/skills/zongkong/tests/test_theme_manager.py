from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[3]
INIT = ROOT / "skills" / "zongkong" / "scripts" / "init_project.py"
THEMES = ROOT / "skills" / "zongkong" / "scripts" / "theme_manager.py"
VALIDATE = ROOT / "skills" / "zongkong" / "scripts" / "validate_project.py"


class ThemeManagerTests(unittest.TestCase):
    def command(self, script: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(script), *args], cwd=ROOT, check=check, text=True, capture_output=True)

    def test_parallel_themes_are_isolated_and_switchable(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "project"
            self.command(INIT, "multi-theme", "--project-dir", str(root))
            self.command(THEMES, "create", str(root), "--name", "对手戏")
            first = root / "themes" / "THEME-001"
            state = yaml.safe_load((first / "project.yaml").read_text(encoding="utf-8"))
            state["stage"] = "LOOK_PLAN_REVIEW"
            (first / "deliverables" / "couple-look-plan.md").write_text("# 主题一\n", encoding="utf-8")
            (first / "project.yaml").write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
            self.command(THEMES, "create", str(root), "--name", "枫丹旅行")
            second = root / "themes" / "THEME-002"
            self.assertTrue((second / "deliverables").is_dir())
            second_state = yaml.safe_load((second / "project.yaml").read_text(encoding="utf-8"))
            self.assertTrue(second_state["quality_policy"]["restart_theme_preserves_quality"])
            self.assertTrue(second_state["quality_policy"]["location_specificity_required"])
            self.assertTrue(second_state["quality_policy"]["progressive_location_specificity"])
            self.assertEqual(second_state["quality_policy"]["discovery_location_level"], "spacetime_anchor")
            self.assertEqual(second_state["quality_policy"]["shot_location_level"], "micro_location")
            self.assertFalse((second / "deliverables" / "couple-look-plan.md").exists())
            self.command(THEMES, "switch", str(root), "THEME-001")
            manifest = yaml.safe_load((root / "project.yaml").read_text(encoding="utf-8"))
            self.assertEqual(manifest["themes"]["active_theme_id"], "THEME-001")
            self.assertEqual(manifest["themes"]["items"][0]["stage"], "LOOK_PLAN_REVIEW")
            self.command(VALIDATE, str(root))

    def test_create_migrates_v2_without_losing_theme_artifacts(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "legacy"
            root.mkdir()
            for relative in ("references/identity", "references/style", "deliverables", "images"):
                (root / relative).mkdir(parents=True, exist_ok=True)
            legacy = {"project_id": "legacy", "workflow_version": 2, "stage": "DISCOVERY", "reference_photos": [], "looks": [], "artifacts": {}, "wardrobe_board": {"next_option_id": 1, "active_board": None, "selected_option_ids": [], "theme": None}, "shot_board": {"next_shot_id": 1, "active_board": None, "selected_shot_ids": [], "enlargements": []}}
            (root / "project.yaml").write_text(yaml.safe_dump(legacy, allow_unicode=True, sort_keys=False), encoding="utf-8")
            sentinel = root / "deliverables" / "keep.md"
            sentinel.write_text("保留", encoding="utf-8")
            self.command(THEMES, "create", str(root), "--name", "新增主题")
            self.assertTrue((root / "themes" / "THEME-001" / "deliverables" / "keep.md").exists())
            self.assertTrue((root / "themes" / "THEME-002" / "project.yaml").exists())
            manifest = yaml.safe_load((root / "project.yaml").read_text(encoding="utf-8"))
            self.assertEqual(manifest["workflow_version"], 3)
            self.assertEqual([item["id"] for item in manifest["themes"]["items"]], ["THEME-001", "THEME-002"])
            self.command(VALIDATE, str(root))


if __name__ == "__main__":
    unittest.main()
