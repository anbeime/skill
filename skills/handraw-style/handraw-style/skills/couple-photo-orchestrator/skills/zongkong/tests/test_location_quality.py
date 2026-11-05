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


class LocationQualityTests(unittest.TestCase):
    def command(self, script: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(script), *args], cwd=ROOT, check=check, text=True, capture_output=True)

    def make_project(self, temp: str) -> tuple[Path, Path]:
        root = Path(temp) / "project"
        self.command(INIT, "location-quality", "--project-dir", str(root))
        self.command(THEMES, "create", str(root), "--name", "作品地点测试")
        workspace = root / "themes" / "THEME-001"
        state = yaml.safe_load((workspace / "project.yaml").read_text(encoding="utf-8"))
        state["stage"] = "LOOKS_CONFIRMED"
        (workspace / "project.yaml").write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
        return root, workspace

    @staticmethod
    def handoff(scene: dict) -> dict:
        participant = {"participant_id": "P01", "label": "角色", "outfit": "唐制圆领袍、革带、长靴，完整角色造型"}
        return {
            "schema_version": 3,
            "project": {
                "participant_count": 1,
                "participants": [{"id": "P01", "label": "角色"}],
                "location_policy": {
                    "specific_location_required": True,
                    "progressive_specificity": True,
                    "discovery_anchor_only": True,
                    "look_uses_shootable_zones_not_micro_points": True,
                    "shot_micro_location_required": True,
                    "indoor_must_be_geographically_anchored": True,
                    "outdoor_must_name_specific_place": True,
                    "named_work_must_name_in_world_location": True,
                    "period_context_required_when_material": True,
                    "no_invented_real_addresses": True,
                    "generic_location_only_is_invalid": True,
                    "unspecified_modern_location_uses_random_world_famous_fallback": True,
                    "random_fallback_must_be_theme_compatible": True,
                    "random_fallback_reroll_changes_place": True,
                },
            },
            "looks": [{
                "id": "LOOK-01", "status": "confirmed",
                "participant_looks": [participant],
                "scenes": [scene],
                "visual_lock": {
                    "participant_outfits": [participant],
                    "location_lock": [scene],
                    "quality_floor": "full_detail_no_compression",
                },
            }],
            "look_group_confirmation": {"status": "confirmed"},
            "handoff_to_photography_skill": {"ready": True},
        }

    def test_source_work_requires_specific_place_and_world_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            _, workspace = self.make_project(temp)
            invalid_scene = {
                "id": "SCENE-01", "name": "古风庭院", "location_mode": "source_work", "indoor_outdoor": "outdoor",
                "source_work": "《红楼梦》", "in_world_location": "庭院", "exact_space_node": "回廊", "era_or_period": None,
                "world_state_or_chapter": None,
            }
            handoff = self.handoff(invalid_scene)
            (workspace / "deliverables" / "requirements-handoff.yaml").write_text(yaml.safe_dump(handoff, allow_unicode=True, sort_keys=False), encoding="utf-8")
            failed = self.command(VALIDATE, str(workspace), check=False)
            self.assertNotEqual(failed.returncode, 0)
            output = failed.stdout + failed.stderr
            self.assertIn("in_world_location", output)
            self.assertIn("era_or_period", output)

    def test_specific_source_work_location_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            _, workspace = self.make_project(temp)
            scene = {
                "id": "SCENE-01", "name": "大观园·潇湘馆竹影院落", "location_mode": "source_work", "indoor_outdoor": "outdoor",
                "source_work": "《红楼梦》", "in_world_location": "大观园·潇湘馆", "exact_space_node": None,
                "era_or_period": "清代小说语境", "world_state_or_chapter": "大观园居住时期",
                "recognizable_environmental_evidence": ["竹影", "小轩窗", "回廊", "清雅闺阁园林语汇"],
            }
            handoff = self.handoff(scene)
            (workspace / "deliverables" / "requirements-handoff.yaml").write_text(yaml.safe_dump(handoff, allow_unicode=True, sort_keys=False), encoding="utf-8")
            passed = self.command(VALIDATE, str(workspace), check=False)
            self.assertEqual(passed.returncode, 0, passed.stdout + passed.stderr)

    def test_real_world_anchor_without_micro_location_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            _, workspace = self.make_project(temp)
            scene = {
                "id": "SCENE-01", "name": "杭州西湖旅行写真", "location_mode": "real_world", "indoor_outdoor": "outdoor",
                "country": "中国", "city": "杭州", "district_or_area": "西湖风景名胜区·孤山 / 北山街一带",
                "named_place": None, "exact_space_node": None,
                "verification_status": "known_public_place_needs_current_verification",
                "era_or_period": "当代拍摄",
            }
            handoff = self.handoff(scene)
            (workspace / "deliverables" / "requirements-handoff.yaml").write_text(yaml.safe_dump(handoff, allow_unicode=True, sort_keys=False), encoding="utf-8")
            passed = self.command(VALIDATE, str(workspace), check=False)
            self.assertEqual(passed.returncode, 0, passed.stdout + passed.stderr)


    def test_indoor_real_world_requires_named_venue_or_street_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            _, workspace = self.make_project(temp)
            scene = {
                "id": "SCENE-01", "name": "巴黎公寓", "location_mode": "real_world", "indoor_outdoor": "indoor",
                "country": "法国", "city": "巴黎", "district_or_area": "Paris 6e / Saint-Germain-des-Prés",
                "street_or_route": None, "named_place": None, "exact_space_node": None,
                "verification_status": "conceptual_private_interior", "era_or_period": "当代拍摄",
            }
            handoff = self.handoff(scene)
            (workspace / "deliverables" / "requirements-handoff.yaml").write_text(
                yaml.safe_dump(handoff, allow_unicode=True, sort_keys=False), encoding="utf-8"
            )
            failed = self.command(VALIDATE, str(workspace), check=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("named venue/building or a real street/route anchor", failed.stdout + failed.stderr)

    def test_indoor_real_world_named_hotel_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            _, workspace = self.make_project(temp)
            scene = {
                "id": "SCENE-01", "name": "巴黎酒店室内", "location_mode": "real_world", "indoor_outdoor": "indoor",
                "country": "法国", "city": "巴黎", "district_or_area": "Paris 6e",
                "street_or_route": "Boulevard Raspail", "named_place": "Hôtel Lutetia Paris",
                "exact_space_node": None, "verification_status": "known_public_place_needs_current_verification",
                "era_or_period": "当代拍摄",
            }
            handoff = self.handoff(scene)
            (workspace / "deliverables" / "requirements-handoff.yaml").write_text(
                yaml.safe_dump(handoff, allow_unicode=True, sort_keys=False), encoding="utf-8"
            )
            passed = self.command(VALIDATE, str(workspace), check=False)
            self.assertEqual(passed.returncode, 0, passed.stdout + passed.stderr)

    def test_theme_quality_policy_is_mandatory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            _, workspace = self.make_project(temp)
            state_path = workspace / "project.yaml"
            state = yaml.safe_load(state_path.read_text(encoding="utf-8"))
            state.pop("quality_policy", None)
            state_path.write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")
            scene = {
                "id": "SCENE-01", "name": "杭州西湖旅行写真", "location_mode": "real_world", "indoor_outdoor": "outdoor",
                "country": "中国", "city": "杭州", "district_or_area": "西湖风景名胜区·北山街",
                "street_or_route": "北山街", "named_place": "杭州西湖风景名胜区",
                "verification_status": "known_public_place_needs_current_verification", "era_or_period": "当代拍摄",
            }
            handoff = self.handoff(scene)
            (workspace / "deliverables" / "requirements-handoff.yaml").write_text(
                yaml.safe_dump(handoff, allow_unicode=True, sort_keys=False), encoding="utf-8"
            )
            failed = self.command(VALIDATE, str(workspace), check=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("quality_policy", failed.stdout + failed.stderr)


    def test_theme_declares_random_world_famous_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            _, workspace = self.make_project(temp)
            state = yaml.safe_load((workspace / "project.yaml").read_text(encoding="utf-8"))
            policy = state["quality_policy"]
            self.assertEqual(policy["unspecified_modern_location_fallback"], "random_world_famous_named_place")
            self.assertTrue(policy["random_location_must_be_theme_compatible"])
            self.assertTrue(policy["location_reroll_must_change_place"])



if __name__ == "__main__":
    unittest.main()
