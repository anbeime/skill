import importlib.util
import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


APPLY = load("apply_triage", ".github/scripts/apply_triage.py")
INTAKE = load("intake_feedback", ".github/scripts/intake_feedback.py")
BUMP = load("bump_version", "scripts/bump_version.py")
SUBMIT = load("submit_feedback", "scripts/submit_feedback.py")


def verdict(**overrides):
    data = {
        "decision": "accepted",
        "type": "bug",
        "size": "S",
        "risk": "low",
        "release": "patch",
        "duplicate_of": None,
        "summary": "修复 3:4 裁切时字幕被截断",
        "reasoning": "问题在 native_subtitle_stitch.py 的裁切边界计算。",
        "plan": ["调整裁切边界", "补充测试"],
        "questions": [],
    }
    data.update(overrides)
    return data


class TriageTests(unittest.TestCase):
    def load_verdict(self, **overrides):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "triage.json"
            path.write_text(json.dumps(verdict(**overrides)), encoding="utf-8")
            return APPLY.load_result(path)

    def test_collaborator_small_bug_is_auto_implemented(self):
        actions = APPLY.plan_actions(self.load_verdict(), "COLLABORATOR", "github", True)
        self.assertTrue(actions["implement"])
        self.assertIn("triage:accepted", actions["labels"])
        self.assertIn("release:patch", actions["labels"])
        self.assertNotIn("status:awaiting-maintainer", actions["labels"])

    def test_outside_contributor_waits_for_maintainer(self):
        actions = APPLY.plan_actions(self.load_verdict(), "NONE", "github", True)
        self.assertFalse(actions["implement"])
        self.assertIn("status:awaiting-maintainer", actions["labels"])
        self.assertIn("agent:implement", actions["comment"])

    def test_intake_sources_are_trusted(self):
        actions = APPLY.plan_actions(self.load_verdict(), "NONE", "social", True)
        self.assertTrue(actions["implement"])

    def test_auto_implement_switch_off(self):
        actions = APPLY.plan_actions(self.load_verdict(), "OWNER", "github", False)
        self.assertFalse(actions["implement"])

    def test_large_or_high_risk_needs_human(self):
        for overrides in ({"size": "L"}, {"risk": "high"}, {"type": "question"}):
            with self.subTest(**overrides):
                actions = APPLY.plan_actions(self.load_verdict(**overrides), "OWNER", "github", True)
                self.assertFalse(actions["implement"])

    def test_invalid_fields_fall_back_to_conservative_values(self):
        result = self.load_verdict(size="XL", risk="none", release="huge", duplicate_of="12")
        self.assertEqual((result["size"], result["risk"], result["release"]), ("L", "high", "skip"))
        self.assertIsNone(result["duplicate_of"])

    def test_invalid_decision_is_rejected(self):
        with self.assertRaises(ValueError):
            self.load_verdict(decision="merge-now")

    def test_needs_info_lists_questions_without_release_label(self):
        actions = APPLY.plan_actions(
            self.load_verdict(decision="needs-info", questions=["用的是哪条命令？"]),
            "NONE",
            "github",
            True,
        )
        self.assertIn("- 用的是哪条命令？", actions["comment"])
        self.assertFalse(any(label.startswith("release:") for label in actions["labels"]))

    def test_comment_redacts_credentials(self):
        leaked = "sk-ant-api03-abcdefghijklmnop"
        with mock.patch.dict(os.environ, {"GH_TOKEN": "ghs_secretvalue123"}):
            actions = APPLY.plan_actions(
                self.load_verdict(summary=f"{leaked} ghs_secretvalue123"), "OWNER", "github", True
            )
        self.assertNotIn(leaked, actions["comment"])
        self.assertNotIn("ghs_secretvalue123", actions["comment"])
        self.assertIn("[REDACTED]", actions["comment"])


class IntakeTests(unittest.TestCase):
    def test_repository_dispatch_payload(self):
        item = INTAKE.normalize(
            "repository_dispatch",
            {"client_payload": {"source": "social", "platform": "小红书", "url": "https://x/1", "title": "希望支持 9:16", "body": "竖版更好发"}},
        )
        self.assertEqual(item["source"], "social")
        body = INTAKE.render_issue(item)
        self.assertIn("小红书", body)
        self.assertIn("> 竖版更好发", body)

    def test_unknown_source_defaults_to_social(self):
        item = INTAKE.normalize("workflow_dispatch", {"inputs": {"source": "evil", "title": "t", "body": "b"}})
        self.assertEqual(item["source"], "social")

    def test_title_falls_back_to_first_body_line(self):
        item = INTAKE.normalize("repository_dispatch", {"client_payload": {"body": "第一行\n第二行"}})
        self.assertEqual(item["title"], "第一行")

    def test_empty_feedback_is_rejected(self):
        with self.assertRaises(ValueError):
            INTAKE.normalize("repository_dispatch", {"client_payload": {}})

    def test_discussion_event(self):
        event = {
            "discussion": {
                "category": {"name": "Ideas"},
                "html_url": "https://github.com/o/r/discussions/3",
                "user": {"login": "alice"},
                "title": "加个水印开关",
                "body": None,
            }
        }
        item = INTAKE.normalize("discussion", event)
        self.assertEqual((item["source"], item["author"]), ("community", "alice"))

    def test_long_text_is_clipped(self):
        item = INTAKE.normalize("repository_dispatch", {"client_payload": {"title": "x" * 200, "body": "y"}})
        self.assertEqual(len(item["title"]), INTAKE.MAX_TITLE)


class BumpVersionTests(unittest.TestCase):
    def test_next_version(self):
        self.assertEqual(BUMP.next_version("2.3.0", "patch"), "2.3.1")
        self.assertEqual(BUMP.next_version("2.3.4", "minor"), "2.4.0")
        self.assertEqual(BUMP.next_version("2.3.4", "major"), "3.0.0")
        self.assertEqual(BUMP.next_version("2.3.4", "v2.5.0"), "2.5.0")

    def test_bump_updates_all_pinned_versions(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for relative in (
                "skills/native-subtitle-quote-image/VERSION",
                ".codex-plugin/plugin.json",
                "scripts/validate_repo.py",
            ):
                (root / relative).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy(ROOT / relative, root / relative)
            plugin_before = (root / ".codex-plugin/plugin.json").read_text(encoding="utf-8")
            current = (root / "skills/native-subtitle-quote-image/VERSION").read_text(encoding="utf-8").strip()
            expected = BUMP.next_version(current, "minor")

            with mock.patch("sys.stdout"):
                BUMP.main(["minor", "--root", str(root)])

            self.assertEqual((root / "skills/native-subtitle-quote-image/VERSION").read_text(encoding="utf-8").strip(), expected)
            plugin_after = (root / ".codex-plugin/plugin.json").read_text(encoding="utf-8")
            self.assertEqual(json.loads(plugin_after)["version"], expected)
            self.assertEqual(
                plugin_after, plugin_before.replace(f'"version": "{current}"', f'"version": "{expected}"')
            )
            self.assertIn(f'EXPECTED_VERSION = "{expected}"', (root / "scripts/validate_repo.py").read_text(encoding="utf-8"))

    def test_refuses_downgrade(self):
        with mock.patch("sys.stderr"), self.assertRaises(SystemExit):
            BUMP.main(["0.0.1"])


class SubmitFeedbackTests(unittest.TestCase):
    def test_payload_shape(self):
        args = SUBMIT.argparse.Namespace(
            source="social", platform="微博", url="https://weibo.com/1", author="a", title="t", body="b"
        )
        payload = SUBMIT.build_payload(args)
        self.assertEqual(payload["event_type"], "feedback")
        self.assertEqual(payload["client_payload"]["platform"], "微博")


class LabelConfigTests(unittest.TestCase):
    def test_every_label_used_by_scripts_is_defined(self):
        defined = {label["name"] for label in json.loads((ROOT / ".github/labels.json").read_text(encoding="utf-8"))}
        required = {"needs-triage", "agent:implement", "agent:in-progress", "agent:pr-open", "agent:failed", "agent-pr"}
        required |= {f"triage:{d}" for d in APPLY.DECISIONS}
        required |= {f"type:{t}" for t in APPLY.TYPES}
        required |= {f"size:{s}" for s in APPLY.SIZES}
        required |= {f"risk:{r}" for r in APPLY.RISKS}
        required |= {f"release:{r}" for r in APPLY.RELEASES}
        required |= {f"source:{s}" for s in INTAKE.SOURCES}
        self.assertEqual(required - defined, set())


if __name__ == "__main__":
    unittest.main()
