from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml
from PIL import Image


ROOT = Path(__file__).resolve().parents[3]
INIT = ROOT / "skills" / "zongkong" / "scripts" / "init_project.py"
VALIDATE = ROOT / "skills" / "zongkong" / "scripts" / "validate_project.py"
BOARD = ROOT / "skills" / "huanzhuang" / "scripts" / "wardrobe_board.py"
THEMES = ROOT / "skills" / "zongkong" / "scripts" / "theme_manager.py"


def options() -> list[dict]:
    return [
        {
            "name": f"方案 {index}",
            "female": f"女生服装 {index}",
            "male": f"男生服装 {index}",
            "couple": f"搭配关系 {index}",
            "scene": f"上海和平饭店室内方案 {index}",
            "location": {
                "location_mode": "real_world",
                "indoor_outdoor": "indoor",
                "country": "中国",
                "city": "上海",
                "district_or_area": "黄浦区外滩",
                "street_or_route": "南京东路",
                "named_place": "和平饭店",
                "exact_space_node": None,
                "verification_status": "known_public_place_needs_current_verification",
                "era_or_period": "当代拍摄",
                "recognizable_environmental_evidence": ["装饰艺术风格室内", "外滩历史建筑语汇"],
            },
            "props": f"道具 {index}"
        }
        for index in range(1, 7)
    ]



class WardrobeBoardTests(unittest.TestCase):
    def command(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, *args], cwd=ROOT, check=check, text=True, capture_output=True)

    def test_numbering_single_grid_and_selection(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            project = temp_root / "selected-project"
            self.command(str(INIT), "test-couple", "--project-dir", str(project))
            self.command(str(THEMES), "create", str(project), "--name", "冬日恋歌")
            root = project
            project = project / "themes" / "THEME-001"
            draft = temp_root / "options.json"
            draft.write_text(json.dumps(options(), ensure_ascii=False), encoding="utf-8")
            self.command(str(BOARD), "create", str(root), "--theme", "冬日恋歌", "--options-file", str(draft), "--theme-id", "THEME-001")
            first = yaml.safe_load((project / "deliverables" / "wardrobe-boards" / "BOARD-001.yaml").read_text(encoding="utf-8"))
            self.assertEqual([item["option_id"] for item in first["options"]], [1, 2, 3, 4, 5, 6])
            self.command(str(VALIDATE), str(project))
            output = self.command(str(BOARD), "prepare-grid", str(project), "BOARD-001").stdout
            self.assertIn("Generate ONE SINGLE IMAGE", output)
            self.assertIn("Panel 6 (slot 6)", output)
            brief = yaml.safe_load((project / "deliverables" / "wardrobe-boards" / "BOARD-001-grid-v1.yaml").read_text(encoding="utf-8"))
            self.assertEqual(brief["grid_mode"], "single_grid")
            self.assertIsNone(brief["panel_aspect_ratio"])
            self.assertEqual(brief["layout_policy"]["mode"], "free_ai")
            self.assertEqual(brief["layout_policy"]["panel_count"], 6)
            self.assertNotIn("layout", brief)
            self.assertEqual(len(brief["slot_mapping"]), 6)
            source = temp_root / "single-grid.png"
            Image.new("RGB", (2400, 2000), (40, 80, 130)).save(source)
            self.command(str(BOARD), "register-grid", str(project), "BOARD-001", "--image", str(source))
            self.assertTrue((project / "images" / "wardrobe-boards" / "BOARD-001.png").exists())
            board = yaml.safe_load((project / "deliverables" / "wardrobe-boards" / "BOARD-001.yaml").read_text(encoding="utf-8"))
            self.assertEqual(board["grid_mode"], "single_grid")
            self.assertTrue((project / board["grid_source_image"]).exists())
            self.command(str(VALIDATE), str(project))
            self.command(str(BOARD), "create", str(project), "--theme", "冬日恋歌", "--options-file", str(draft))
            second = yaml.safe_load((project / "deliverables" / "wardrobe-boards" / "BOARD-002.yaml").read_text(encoding="utf-8"))
            self.assertEqual([item["option_id"] for item in second["options"]], [7, 8, 9, 10, 11, 12])
            self.command(str(BOARD), "prepare-grid", str(project), "BOARD-002")
            second_source = temp_root / "second-single-grid.png"
            Image.new("RGB", (2400, 2000), (80, 60, 110)).save(second_source)
            self.command(str(BOARD), "register-grid", str(project), "BOARD-002", "--image", str(second_source))
            self.command(str(BOARD), "select", str(project), "--ids", "8,10")
            handoff = yaml.safe_load((project / "deliverables" / "requirements-handoff.yaml").read_text(encoding="utf-8"))
            self.assertEqual([look["wardrobe_board_option_id"] for look in handoff["looks"]], [8, 10])
            self.assertEqual(handoff["looks"][0]["visual_lock"]["male_outfit"], second["options"][1]["male"])
            self.command(str(VALIDATE), str(project))
            failed = self.command(str(BOARD), "select", str(project), "--ids", "99", check=False)
            self.assertNotEqual(failed.returncode, 0)
            removed = self.command(str(BOARD), "compose", str(project), "BOARD-001", check=False)
            self.assertNotEqual(removed.returncode, 0)

    def test_three_person_options_preserve_every_outfit(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            project = temp_root / "selected-project"
            self.command(str(INIT), "multi-group", "--project-dir", str(project))
            self.command(str(THEMES), "create", str(project), "--name", "三人城市群像")
            workspace = project / "themes" / "THEME-001"
            multi_options = []
            for index in range(1, 7):
                multi_options.append({
                    "name": f"三人方案 {index}",
                    "participants": [
                        {"participant_id": "P01", "label": "姐姐", "outfit": f"P01 完整服装 {index}：灰蓝外套、白衬衫、深灰长裤、短靴"},
                        {"participant_id": "P02", "label": "弟弟", "outfit": f"P02 完整服装 {index}：深蓝夹克、米白针织、炭灰长裤、运动鞋"},
                        {"participant_id": "P03", "label": "朋友", "outfit": f"P03 完整服装 {index}：暗红针织、旧白T恤、洗旧牛仔裤、皮鞋"},
                    ],
                    "group_relationship": f"三人搭配关系 {index}",
                    "scene": f"杭州西湖北山街城市旅行场景 {index}",
                    "location": {
                        "location_mode": "real_world",
                        "indoor_outdoor": "outdoor",
                        "country": "中国",
                        "city": "杭州",
                        "district_or_area": "西湖风景名胜区·北山街",
                        "named_place": "杭州西湖·北山街沿线",
                        "exact_space_node": None,
                        "verification_status": "known_public_place_needs_current_verification",
                        "era_or_period": "当代拍摄",
                        "recognizable_environmental_evidence": ["西湖水面", "北山街梧桐", "孤山方向湖岸"],
                    },
                    "props": f"共享道具 {index}",
                })
            draft = temp_root / "multi-options.json"
            draft.write_text(json.dumps(multi_options, ensure_ascii=False), encoding="utf-8")
            self.command(str(BOARD), "create", str(project), "--theme", "三人城市群像", "--options-file", str(draft), "--theme-id", "THEME-001")
            output = self.command(str(BOARD), "prepare-grid", str(workspace), "BOARD-001").stdout
            self.assertIn("P01", output)
            self.assertIn("P02", output)
            self.assertIn("P03", output)
            source = temp_root / "multi-grid.png"
            Image.new("RGB", (2400, 2000), (20, 40, 60)).save(source)
            self.command(str(BOARD), "register-grid", str(workspace), "BOARD-001", "--image", str(source))
            self.command(str(BOARD), "select", str(workspace), "--ids", "1")
            handoff = yaml.safe_load((workspace / "deliverables" / "requirements-handoff.yaml").read_text(encoding="utf-8"))
            self.assertEqual(handoff["schema_version"], 3)
            self.assertEqual(handoff["project"]["participant_count"], 3)
            self.assertTrue(handoff["project"]["location_policy"]["specific_location_required"])
            self.assertTrue(handoff["project"]["location_policy"]["progressive_specificity"])
            self.assertIsNone(handoff["looks"][0]["scenes"][0].get("exact_space_node"))
            self.assertEqual(handoff["looks"][0]["scenes"][0]["city"], "杭州")
            locked = handoff["looks"][0]["visual_lock"]["participant_outfits"]
            self.assertEqual([item["participant_id"] for item in locked], ["P01", "P02", "P03"])
            self.assertTrue(all(item["outfit"] for item in locked))
            self.command(str(VALIDATE), str(workspace))


    def test_strict_location_policy_rejects_generic_wardrobe_scene(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            project = temp_root / "selected-project"
            self.command(str(INIT), "strict-location", "--project-dir", str(project))
            self.command(str(THEMES), "create", str(project), "--name", "地点测试")
            generic = []
            for index in range(1, 7):
                generic.append({
                    "name": f"方案 {index}",
                    "participants": [{"participant_id": "P01", "label": "人物", "outfit": f"完整服装 {index}"}],
                    "group_relationship": "单人",
                    "scene": "酒店",
                    "props": "无",
                })
            draft = temp_root / "generic.json"
            draft.write_text(json.dumps(generic, ensure_ascii=False), encoding="utf-8")
            failed = self.command(str(BOARD), "create", str(project), "--theme", "地点测试", "--options-file", str(draft), "--theme-id", "THEME-001", check=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("location", (failed.stderr + failed.stdout).lower())


if __name__ == "__main__":
    unittest.main()
