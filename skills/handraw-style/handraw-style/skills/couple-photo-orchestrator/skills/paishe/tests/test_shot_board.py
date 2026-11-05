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
BOARD = ROOT / "skills" / "paishe" / "scripts" / "shot_board.py"
THEMES = ROOT / "skills" / "zongkong" / "scripts" / "theme_manager.py"


def shots() -> list[dict[str, str]]:
    return [
        {
            "title": f"镜头 {index}", "purpose": f"目的 {index}",
            "action_event": f"事件 {index}", "pose_structure": f"姿势结构 {index}",
            "key_support_weight": f"关键受力与重心 {index}", "relationship_contact": f"关系接触 {index}",
            "emotion_motivation": f"情绪动机 {index}", "gaze": f"视线 {index}",
            "framing_adaptation": f"景别适配 {index}", "scene_area": f"场景 {index}",
            "interaction": f"互动 {index}", "shot_size": "中景", "composition": f"构图 {index}",
            "lighting": f"光线 {index}", "continuity": f"连续性 {index}", "avoids": f"避免项 {index}",
            "prompt": f"情侣写真提示词 {index}",
        }
        for index in range(1, 9)
    ]


class ShotBoardTests(unittest.TestCase):
    def command(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, *args], cwd=ROOT, check=check, text=True, capture_output=True)

    def create_board(self, project: Path, temp_root: Path, suffix: str = "one") -> None:
        draft = temp_root / f"shots-{suffix}.json"
        draft.write_text(json.dumps(shots(), ensure_ascii=False), encoding="utf-8")
        self.command(str(BOARD), "create", str(project), "--look-id", "LOOK-01", "--theme", "洱海旅行", "--shots-file", str(draft))

    def prepare_project(self, project: Path) -> None:
        handoff = {
            "project": {"theme": "枫丹舞台邂逅", "worldview": "《原神》提瓦特·枫丹", "hard_avoids": ["普通西装", "现代商务感"]},
            "looks": [{
                "id": "LOOK-01", "status": "confirmed",
                "female_outfit": "芙宁娜的枫丹舞台礼服，蓝白礼帽与蝴蝶结",
                "male_outfit": "枫丹旅行者风格的深蓝短斗篷、立领马甲与长靴",
                "couple_relationship": "舞台感与旅行感的轻盈呼应",
                "scenes": [{"name": "枫丹廷歌剧院外水道", "props": ["蓝白手杖"]}],
                "visual_lock": {
                    "female_outfit": "芙宁娜的枫丹舞台礼服，蓝白礼帽与蝴蝶结",
                    "male_outfit": "枫丹旅行者风格的深蓝短斗篷、立领马甲与长靴",
                    "couple_relationship": "舞台感与旅行感的轻盈呼应",
                    "work_era_setting": "《原神》提瓦特·枫丹",
                    "scene_mood": "枫丹廷歌剧院外水道",
                    "hard_avoids": ["普通西装", "现代商务感"],
                },
            }],
            "look_group_confirmation": {"status": "confirmed"},
            "handoff_to_photography_skill": {"ready": True},
        }
        (project / "deliverables" / "requirements-handoff.yaml").write_text(yaml.safe_dump(handoff, allow_unicode=True), encoding="utf-8")
        (project / "deliverables" / "shooting-plan.md").write_text("# 拍摄方案\n", encoding="utf-8")

    def prepare_grid(self, project: Path, board_id: str) -> str:
        return self.command(str(BOARD), "prepare-grid", str(project), board_id).stdout

    def register_grid(self, project: Path, temp_root: Path, board_id: str) -> Path:
        source = temp_root / f"{board_id}-source.png"
        Image.new("RGB", (3200, 2000), (40, 80, 130)).save(source)
        self.command(str(BOARD), "register-grid", str(project), board_id, "--image", str(source))
        return project / "images" / "shot-boards" / f"{board_id}.png"

    def test_single_grid_lifecycle_and_versioned_details(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            project = temp_root / "selected-project"
            self.command(str(INIT), "test-couple", "--project-dir", str(project))
            self.command(str(THEMES), "create", str(project), "--name", "枫丹舞台邂逅")
            root = project
            project = project / "themes" / "THEME-001"
            self.prepare_project(project)
            state = yaml.safe_load((project / "project.yaml").read_text(encoding="utf-8"))
            self.assertEqual(state["workflow_version"], 2)
            self.assertNotIn("generation", state)
            draft = temp_root / "shots-one.json"
            draft.write_text(json.dumps(shots(), ensure_ascii=False), encoding="utf-8")
            self.command(str(BOARD), "create", str(root), "--look-id", "LOOK-01", "--theme", "洱海旅行", "--shots-file", str(draft), "--theme-id", "THEME-001")
            self.command(str(VALIDATE), str(project))
            root_manifest = yaml.safe_load((root / "project.yaml").read_text(encoding="utf-8"))
            self.assertEqual(root_manifest["themes"]["items"][0]["stage"], "SHOTLIST_REVIEW")
            self.command(str(VALIDATE), str(root))
            board_before_grid = yaml.safe_load((project / "deliverables" / "shot-boards" / "SHOTBOARD-001.yaml").read_text(encoding="utf-8"))
            self.assertIn("芙宁娜的枫丹舞台礼服", board_before_grid["visual_lock"]["female_outfit"])
            self.assertTrue(all("高级摄影师风格，创意构图，强烈的戏剧张力" in shot["prompt"] for shot in board_before_grid["shots"]))
            self.assertIn("深蓝短斗篷", board_before_grid["shots"][0]["prompt"])
            self.assertIn("不得把任一方替换为普通西装", board_before_grid["shots"][0]["prompt"])
            output = self.prepare_grid(project, "SHOTBOARD-001")
            self.assertIn("Generate ONE SINGLE IMAGE", output)
            self.assertIn("Panel 8 (slot 8)", output)
            self.assertIn("深蓝短斗篷", output)
            brief = project / "deliverables" / "shot-grid-briefs" / "SHOTBOARD-001-grid-v1.yaml"
            data = yaml.safe_load(brief.read_text(encoding="utf-8"))
            self.assertIn("高级摄影师风格，创意构图，强烈的戏剧张力", data["render_prompt"])
            self.assertEqual(data["grid_mode"], "single_grid")
            self.assertIsNone(data["panel_aspect_ratio"])
            self.assertEqual(data["layout_policy"]["mode"], "free_ai")
            self.assertEqual(data["layout_policy"]["panel_count"], 8)
            self.assertEqual(len(data["slot_mapping"]), 8)
            grid = self.register_grid(project, temp_root, "SHOTBOARD-001")
            self.assertTrue(grid.exists())
            with Image.open(grid) as numbered:
                self.assertEqual(numbered.size, (3200, 2000))
            board = yaml.safe_load((project / "deliverables" / "shot-boards" / "SHOTBOARD-001.yaml").read_text(encoding="utf-8"))
            self.assertEqual(board["grid_mode"], "single_grid")
            self.assertEqual(board["cell_images"], {})
            self.assertTrue((project / board["grid_source_image"]).exists())
            self.command(str(VALIDATE), str(project))
            selected_output = self.command(str(BOARD), "select", str(project), "--ids", "1,3", "--orientation", "landscape", "--detail", "加强风感").stdout
            self.assertIn("SHOT-001-detail-landscape-v1.yaml", selected_output)
            detail_brief = project / "deliverables" / "shot-detail-briefs" / "SHOT-001-detail-landscape-v1.yaml"
            detail_data = yaml.safe_load(detail_brief.read_text(encoding="utf-8"))
            self.assertEqual(detail_data["aspect_ratio"], "3:2")
            self.assertEqual(detail_data["user_detail"], "加强风感")
            self.assertEqual(detail_data["reference_source"], "single_grid_full_contact_sheet")
            self.assertEqual(detail_data["reference_usage"], "required")
            anchor = project / detail_data["reference_image"]
            self.assertTrue(anchor.exists())
            with Image.open(anchor) as reference:
                self.assertEqual(reference.size, (3200, 2000))
            self.assertIn("高级摄影师风格，创意构图，强烈的戏剧张力", detail_data["render_prompt"])
            self.assertIn("重新生成一张完整图片", detail_data["render_prompt"])
            self.assertIn("不要机械外延画布", detail_data["render_prompt"])
            self.assertIn("两人的姿势互动", detail_data["preservation_contract"]["required"])
            detail_image = project / "images" / "shot-details" / "SHOT-001-landscape-v1.png"
            Image.new("RGB", (900, 600), (1, 2, 3)).save(detail_image)
            self.command(str(BOARD), "complete", str(project), "--brief", "deliverables/shot-detail-briefs/SHOT-001-detail-landscape-v1.yaml", "--image", str(detail_image))
            self.command(str(VALIDATE), str(project))
            self.command(str(BOARD), "select", str(project), "--ids", "1")
            self.assertTrue((project / "deliverables" / "shot-detail-briefs" / "SHOT-001-detail-portrait-v1.yaml").exists())
            self.create_board(project, temp_root, "two")
            second = yaml.safe_load((project / "deliverables" / "shot-boards" / "SHOTBOARD-002.yaml").read_text(encoding="utf-8"))
            self.assertEqual([shot["shot_id"] for shot in second["shots"]], list(range(9, 17)))
            self.assertTrue(grid.exists())

    def test_grid_ignores_deprecated_panel_ratio_argument(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            project = temp_root / "ratio-project"
            self.command(str(INIT), "ratio-test", "--project-dir", str(project))
            self.command(str(THEMES), "create", str(project), "--name", "比例测试")
            project = project / "themes" / "THEME-001"
            self.prepare_project(project)
            self.create_board(project, temp_root)
            self.command(str(BOARD), "prepare-grid", str(project), "SHOTBOARD-001", "--panel-aspect-ratio", "1:3")
            brief = yaml.safe_load((project / "deliverables" / "shot-grid-briefs" / "SHOTBOARD-001-grid-v1.yaml").read_text(encoding="utf-8"))
            self.assertIsNone(brief["panel_aspect_ratio"])
            self.assertEqual(brief["layout_policy"]["mode"], "free_ai")
            self.assertNotIn("layout", brief)
            self.assertNotIn("aspect ratio 9:16", brief["render_prompt"])
            self.assertNotIn("exact aspect ratio", brief["render_prompt"])
            self.assertIn("exactly eight distinct photographic panels", brief["render_prompt"])

    def test_rejects_invalid_grid_registration_and_orientation(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            project = temp_root / "selected-project"
            self.command(str(INIT), "test-couple", "--project-dir", str(project))
            self.command(str(THEMES), "create", str(project), "--name", "枫丹舞台邂逅")
            project = project / "themes" / "THEME-001"
            self.prepare_project(project)
            self.create_board(project, temp_root)
            conflicting = shots()
            conflicting[0]["prompt"] = "男主穿普通西装站在水道边"
            conflict_file = temp_root / "conflicting-shots.json"
            conflict_file.write_text(json.dumps(conflicting, ensure_ascii=False), encoding="utf-8")
            conflict = self.command(str(BOARD), "create", str(project), "--look-id", "LOOK-01", "--theme", "枫丹舞台邂逅", "--shots-file", str(conflict_file), check=False)
            self.assertNotEqual(conflict.returncode, 0)
            removed = self.command(str(BOARD), "compose", str(project), "SHOTBOARD-001", check=False)
            self.assertNotEqual(removed.returncode, 0)
            missing_grid = self.command(str(BOARD), "register-grid", str(project), "SHOTBOARD-001", "--image", "missing.png", check=False)
            self.assertNotEqual(missing_grid.returncode, 0)
            self.prepare_grid(project, "SHOTBOARD-001")
            missing_grid = self.command(str(BOARD), "register-grid", str(project), "SHOTBOARD-001", "--image", "missing.png", check=False)
            self.assertNotEqual(missing_grid.returncode, 0)
            self.register_grid(project, temp_root, "SHOTBOARD-001")
            unknown = self.command(str(BOARD), "select", str(project), "--ids", "99", check=False)
            self.assertNotEqual(unknown.returncode, 0)
            orientation = self.command(str(BOARD), "select", str(project), "--ids", "1", "--orientation", "square", check=False)
            self.assertNotEqual(orientation.returncode, 0)

    def test_three_person_board_requires_and_preserves_per_person_direction(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            temp_root = Path(temp)
            project = temp_root / "selected-project"
            self.command(str(INIT), "multi-group", "--project-dir", str(project))
            self.command(str(THEMES), "create", str(project), "--name", "三人街头")
            workspace = project / "themes" / "THEME-001"
            handoff = {
                "schema_version": 3,
                "project": {
                    "theme": "三人街头",
                    "participant_count": 3,
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
                    "participants": [
                        {"id": "P01", "label": "姐姐"},
                        {"id": "P02", "label": "弟弟"},
                        {"id": "P03", "label": "朋友"},
                    ],
                },
                "looks": [{
                    "id": "LOOK-01",
                    "status": "confirmed",
                    "participant_looks": [
                        {"participant_id": "P01", "label": "姐姐", "outfit": "灰蓝短风衣、白衬衫、深灰长裤、黑短靴"},
                        {"participant_id": "P02", "label": "弟弟", "outfit": "深蓝夹克、米白针织、炭灰长裤、白运动鞋"},
                        {"participant_id": "P03", "label": "朋友", "outfit": "暗红针织、旧白T恤、洗旧牛仔裤、棕皮鞋"},
                    ],
                    "group_relationship": "冷色为主，P03 暗红形成次级视觉锚点",
                    "scenes": [{
                        "id": "SCENE-01",
                        "name": "杭州西湖·北山街旅行街拍",
                        "location_mode": "real_world",
                        "indoor_outdoor": "outdoor",
                        "country": "中国",
                        "city": "杭州",
                        "district_or_area": "西湖风景名胜区·北山街",
                        "street_or_route": "北山街—孤山路",
                        "named_place": "杭州西湖·北山街沿线",
                        "exact_space_node": None,
                        "verification_status": "known_public_place_needs_current_verification",
                        "source_work": None,
                        "in_world_location": None,
                        "era_or_period": "当代拍摄",
                        "world_state_or_chapter": None,
                        "recognizable_environmental_evidence": ["西湖水面", "北山街梧桐", "孤山湖岸"],
                        "props": ["报纸"],
                    }],
                    "visual_lock": {
                        "participant_outfits": [
                            {"participant_id": "P01", "label": "姐姐", "outfit": "灰蓝短风衣、白衬衫、深灰长裤、黑短靴"},
                            {"participant_id": "P02", "label": "弟弟", "outfit": "深蓝夹克、米白针织、炭灰长裤、白运动鞋"},
                            {"participant_id": "P03", "label": "朋友", "outfit": "暗红针织、旧白T恤、洗旧牛仔裤、棕皮鞋"},
                        ],
                        "group_relationship": "冷色为主，P03 暗红形成次级视觉锚点",
                        "work_era_setting": "现代城市街头",
                        "scene_mood": "杭州西湖·北山街旅行街拍",
                        "location_lock": [{
                        "id": "SCENE-01",
                        "name": "杭州西湖·北山街旅行街拍",
                        "location_mode": "real_world",
                        "indoor_outdoor": "outdoor",
                        "country": "中国",
                        "city": "杭州",
                        "district_or_area": "西湖风景名胜区·北山街",
                        "street_or_route": "北山街—孤山路",
                        "named_place": "杭州西湖·北山街沿线",
                        "exact_space_node": None,
                        "verification_status": "known_public_place_needs_current_verification",
                        "source_work": None,
                        "in_world_location": None,
                        "era_or_period": "当代拍摄",
                        "world_state_or_chapter": None,
                        "recognizable_environmental_evidence": ["西湖水面", "北山街梧桐", "孤山湖岸"],
                        "props": ["报纸"],
                    }],
                        "quality_floor": "full_detail_no_compression",
                        "hard_avoids": ["统一制服感"],
                    },
                }],
                "look_group_confirmation": {"status": "confirmed"},
                "handoff_to_photography_skill": {"ready": True},
            }
            (workspace / "deliverables" / "requirements-handoff.yaml").write_text(yaml.safe_dump(handoff, allow_unicode=True, sort_keys=False), encoding="utf-8")
            state = yaml.safe_load((workspace / "project.yaml").read_text(encoding="utf-8"))
            state["stage"] = "LOOKS_CONFIRMED"
            (workspace / "project.yaml").write_text(yaml.safe_dump(state, allow_unicode=True, sort_keys=False), encoding="utf-8")

            multi_shots = []
            for index in range(1, 9):
                present = ["P01", "P02", "P03"] if index == 1 else (["P01", "P02"] if index % 2 == 0 else ["P02", "P03"])
                directions = [
                    {"participant_id": pid, "direction": f"{pid} 保持独立动作、身体朝向清晰、视线参与同一事件、手部自然"}
                    for pid in present
                ]
                multi_shots.append({
                    "title": f"镜头 {index}",
                    "purpose": f"目的 {index}",
                    "action_event": f"三人共同事件 {index}",
                    "pose_structure": f"前后错位姿势结构 {index}",
                    "key_support_weight": f"自然承重与移动重心 {index}",
                    "relationship_contact": f"同一事件中的群体关系 {index}",
                    "emotion_motivation": f"由当前街拍事件生成的情绪动机 {index}",
                    "gaze": f"人物之间形成有层次的视线关系 {index}",
                    "framing_adaptation": "中景仅描述画面内可见身体关系",
                    "location_context": "中国杭州·西湖风景名胜区·北山街—孤山路·杭州西湖北岸，真实具名户外地点",
                    "scene_area": f"孤山路临湖步道第 {index} 个梧桐树影与湖岸栏杆交界处",
                    "era_or_world_context": "当代杭州旅行街拍",
                    "participants_present": present,
                    "participant_directions": directions,
                    "interaction": "共享一个轻松对话事件",
                    "shot_size": "中景",
                    "composition": "前后错位构图",
                    "lighting": "侧前方漫射光",
                    "continuity": "服装与道具保持一致",
                    "avoids": "不要排队式站姿",
                    "prompt": f"三人街头写真 Shot {index}，真实互动，逐人身份清晰",
                })
            draft = temp_root / "multi-shots.json"
            draft.write_text(json.dumps(multi_shots, ensure_ascii=False), encoding="utf-8")
            self.command(str(BOARD), "create", str(project), "--look-id", "LOOK-01", "--theme", "三人街头", "--shots-file", str(draft), "--theme-id", "THEME-001")
            board = yaml.safe_load((workspace / "deliverables" / "shot-boards" / "SHOTBOARD-001.yaml").read_text(encoding="utf-8"))
            self.assertEqual(len(board["visual_lock"]["participant_outfits"]), 3)
            self.assertEqual(board["shots"][0]["participants_present"], ["P01", "P02", "P03"])
            self.assertEqual(len(board["shots"][0]["participant_directions"]), 3)
            self.assertIn("P03", board["shots"][0]["prompt"])
            self.assertTrue(board["visual_lock"]["strict_location"])
            self.assertIn("杭州", board["shots"][0]["location_context"])
            self.command(str(VALIDATE), str(project))

            invalid = list(multi_shots)
            invalid[0] = dict(invalid[0])
            invalid[0].pop("participant_directions")
            invalid_file = temp_root / "invalid-multi-shots.json"
            invalid_file.write_text(json.dumps(invalid, ensure_ascii=False), encoding="utf-8")
            failed = self.command(str(BOARD), "create", str(project), "--look-id", "LOOK-01", "--theme", "三人街头", "--shots-file", str(invalid_file), "--theme-id", "THEME-001", check=False)
            self.assertNotEqual(failed.returncode, 0)

            invalid_location = [dict(item) for item in multi_shots]
            invalid_location[0] = dict(invalid_location[0])
            invalid_location[0]["location_context"] = "户外"
            invalid_location[0]["scene_area"] = "街头"
            invalid_location_file = temp_root / "invalid-location.json"
            invalid_location_file.write_text(json.dumps(invalid_location, ensure_ascii=False), encoding="utf-8")
            failed_location = self.command(str(BOARD), "create", str(project), "--look-id", "LOOK-01", "--theme", "三人街头", "--shots-file", str(invalid_location_file), "--theme-id", "THEME-001", check=False)
            self.assertNotEqual(failed_location.returncode, 0)
            self.assertIn("location", (failed_location.stderr + failed_location.stdout).lower())


if __name__ == "__main__":
    unittest.main()
