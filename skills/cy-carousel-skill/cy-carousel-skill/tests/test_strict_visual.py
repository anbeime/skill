import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import check_all  # noqa: E402
import package  # noqa: E402


def make_note(td):
    from PIL import Image

    td = Path(td)
    note, pages = td / "note", td / "pages"
    note.mkdir()
    pages.mkdir()
    (note / "页面脚本.json").write_text(json.dumps({"topic": "测试", "pages": [{}]}), encoding="utf-8")
    for name in ("标题.txt", "正文.txt", "置顶评论.txt", "来源.md"):
        (note / name).write_text("内容", encoding="utf-8")
    Image.new("RGB", (1440, 1920), "white").save(pages / "p01.png")
    return note, pages, td / "out"


def fake_result(blockers):
    return dict(passed=True, errors=[], scope="t", visual_acceptance="未验收", advisories=[],
                strict_visual=bool(blockers), visual_blockers=blockers)


class StrictVisualTests(unittest.TestCase):
    def test_only_whitespace_and_same_skeleton_block(self):
        self.assertTrue(check_all.visual_blocking("whitespace", "暗篇空格子均值30.0%>20%"))
        self.assertTrue(check_all.visual_blocking("richness", "P03与前页骨架相同"))
        self.assertFalse(check_all.visual_blocking("richness", "色彩丰富度均值不足33"))
        for name in ("alternation", "color_area", "variation"):
            self.assertFalse(check_all.visual_blocking(name, "与前页骨架相同"))

    def test_blockers_refuse_without_reason(self):
        with tempfile.TemporaryDirectory() as td:
            note, pages, out = make_note(td)
            with mock.patch.object(package, "check_note", return_value=fake_result(["留白"])):
                with self.assertRaisesRegex(ValueError, "accept-visual"):
                    package.deliver(note, pages, out, strict_visual=True)
                with self.assertRaisesRegex(ValueError, "理由"):
                    package.deliver(note, pages, out, strict_visual=True, accept_visual="  ")
            self.assertFalse(out.exists())

    def test_accept_reason_recorded(self):
        with tempfile.TemporaryDirectory() as td:
            note, pages, out = make_note(td)
            with mock.patch.object(package, "check_note", return_value=fake_result(["留白"])):
                package.deliver(note, pages, out, strict_visual=True, accept_visual="目检后确认")
            saved = json.loads((out / "交付清单.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["visual_accepted"], {"reason": "目检后确认", "blockers": ["留白"]})

    def test_default_off_unchanged(self):
        with tempfile.TemporaryDirectory() as td:
            note, pages, out = make_note(td)
            res = dict(passed=True, errors=[], scope="t", advisories=["留白"])
            with mock.patch.object(package, "check_note", return_value=res):
                m = package.deliver(note, pages, out)
            self.assertIsNone(m["visual_accepted"])


OK = dict(passed=True, errors=[])


def make_check_fixture(td, config=None, tone=None, mode=None):
    td = Path(td)
    data = {"pages": [{"layout": "cover", "elements": []}] + [{"layout": "body", "elements": []} for _ in range(9)],
            "config": config or {}}
    if tone:
        data["tone"] = tone
    if mode:
        data["mode"] = mode
    script = td / "页面脚本.json"
    script.write_text(json.dumps(data), encoding="utf-8")
    report = td / "render-report.json"
    report.write_text(json.dumps([{"page": i} for i in range(1, 11)]), encoding="utf-8")
    return script, td, report


def run_check(td, strict=False, ws=None, rich=None, alt=None, **kw):
    """真实 check_note，其余规则全部桩掉，只看严格视觉的分流。"""
    script, pages, report = make_check_fixture(td, **kw)
    names = ("geometry_rules", "background_rules", "tone_rules", "backdrop_rules", "watermark_rules",
             "light_editorial_rules", "color_hierarchy_rules", "variation_rules")
    patches = [mock.patch.object(check_all, n, return_value=dict(OK)) for n in names]
    patches.append(mock.patch.object(check_all, "whitespace_check", **ws or dict(return_value=dict(OK))))
    patches.append(mock.patch.object(check_all, "richness_rules", **rich or dict(return_value=dict(OK))))
    patches.append(mock.patch.object(check_all, "alternation_rules", **alt or dict(return_value=dict(OK))))
    for p in patches:
        p.start()
    try:
        with redirect_stderr(io.StringIO()) as err:
            res = check_all.check_note(script, pages, report, strict_visual=strict)
    finally:
        mock.patch.stopall()
    return res, err.getvalue()


class CheckNoteStrictTests(unittest.TestCase):
    def test_blockers_populated_from_errors(self):
        ws = dict(return_value=dict(errors=["暗篇空格子均值30.0%>20%"]))
        rich = dict(return_value=dict(errors=["P03与前页骨架相同", "色彩丰富度均值不足33"]))
        alt = dict(return_value=dict(errors=["全篇强调色均值3%不在1.2–2.0%"]))
        with tempfile.TemporaryDirectory() as td:
            res, _ = run_check(td, strict=True, ws=ws, rich=rich, alt=alt)
        self.assertEqual(res["visual_blockers"], ["P03与前页骨架相同", "暗篇空格子均值30.0%>20%"])
        self.assertIn("色彩丰富度均值不足33", res["advisories"])
        self.assertIn("全篇强调色均值3%不在1.2–2.0%", res["advisories"])

    def test_default_off_has_no_blockers(self):
        ws = dict(return_value=dict(errors=["留白"]))
        with tempfile.TemporaryDirectory() as td:
            res, _ = run_check(td, ws=ws)
        self.assertFalse(res["strict_visual"])
        self.assertEqual(res["visual_blockers"], [])
        self.assertIn("留白", res["advisories"])

    def test_config_visual_gate_enables(self):
        ws = dict(return_value=dict(errors=["留白"]))
        with tempfile.TemporaryDirectory() as td:
            res, _ = run_check(td, ws=ws, config={"visual_gate": True})
        self.assertTrue(res["strict_visual"])
        self.assertEqual(res["visual_blockers"], ["留白"])

    def test_check_exception_blocks(self):
        ws = dict(side_effect=OSError("缺PNG"))
        rich = dict(side_effect=KeyError("skeleton"))
        with tempfile.TemporaryDirectory() as td:
            res, _ = run_check(td, strict=True, ws=ws, rich=rich)
            off, _ = run_check(td, ws=ws, rich=rich)
        self.assertEqual(len(res["visual_blockers"]), 2)
        self.assertTrue(all("检查未能运行" in m for m in res["visual_blockers"]))
        self.assertEqual(off["visual_blockers"], [])

    def test_alternation_failure_remains_advisory(self):
        with tempfile.TemporaryDirectory() as td:
            res, _ = run_check(td, strict=True, alt=dict(side_effect=KeyError("color")))
        self.assertEqual(res["visual_blockers"], [])
        self.assertTrue(any("alternation" in m for m in res["advisories"]))

    def test_light_tone_not_applicable(self):
        ws = dict(return_value=dict(errors=["留白"]))
        rich = dict(return_value=dict(errors=["P03与前页骨架相同"]))
        with tempfile.TemporaryDirectory() as td:
            res, err = run_check(td, strict=True, ws=ws, rich=rich, tone="浅")
            off, off_err = run_check(td, ws=ws, rich=rich, tone="浅")
        self.assertFalse(res["checks"]["strict_visual"]["applicable"])
        self.assertIn("不适用", err)
        self.assertEqual(res["visual_blockers"], [])
        self.assertNotIn("strict_visual", off["checks"])
        self.assertEqual(off_err, "")

    def test_light_tone_richness_failure_does_not_block(self):
        with tempfile.TemporaryDirectory() as td:
            res, _ = run_check(td, strict=True, tone="浅", rich=dict(side_effect=KeyError("skeleton")))
        self.assertEqual(res["visual_blockers"], [])
        self.assertFalse(res["checks"]["strict_visual"]["applicable"])

    def test_sample_not_applicable(self):
        with tempfile.TemporaryDirectory() as td:
            res, err = run_check(td, strict=True, mode="sample")
        self.assertFalse(res["checks"]["strict_visual"]["applicable"])
        self.assertIn("不适用", err)

    def test_main_exit_code(self):
        def main_with(result, *extra):
            argv = ["check_all.py", "s.json", "--pages", "p", *extra]
            with mock.patch.object(sys, "argv", argv), mock.patch.object(check_all, "check_note", return_value=result), \
                    redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                return check_all.main()

        self.assertEqual(main_with(fake_result(["留白"]), "--strict-visual"), 1)
        self.assertEqual(main_with(fake_result([]), "--strict-visual"), 0)


class PackageCliTests(unittest.TestCase):
    def run_cli(self, note, pages, out, *extra):
        code = (
            "import sys, runpy, check_all;"
            "check_all.check_note = lambda *a, **k: dict(passed=True, errors=[], scope='test',"
            " visual_acceptance='未验收', advisories=[], strict_visual=True, visual_blockers=['留白']);"
            "sys.argv = ['package.py'] + sys.argv[1:];"
            "runpy.run_path('package.py', run_name='__main__')"
        )
        return subprocess.run(
            [sys.executable, "-c", code, "--note", str(note), "--pages", str(pages), "--out", str(out), *extra],
            cwd=ROOT / "scripts", capture_output=True, encoding="utf-8")

    def test_cli_blocked_then_accepted(self):
        with tempfile.TemporaryDirectory() as td:
            note, pages, out = make_note(td)
            proc = self.run_cli(note, pages, out, "--strict-visual")
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("accept-visual", proc.stderr)
            self.assertFalse(out.exists())
            proc = self.run_cli(note, pages, out, "--strict-visual", "--accept-visual", "目检后确认")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            saved = json.loads((out / "交付清单.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["visual_accepted"]["reason"], "目检后确认")

    def test_cli_accept_without_strict_flag(self):
        # 页面脚本 config.visual_gate 开启时，命令行只需 --accept-visual
        with tempfile.TemporaryDirectory() as td:
            note, pages, out = make_note(td)
            proc = self.run_cli(note, pages, out, "--accept-visual", "确认")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            saved = json.loads((out / "交付清单.json").read_text(encoding="utf-8"))
            self.assertEqual(saved["visual_accepted"]["reason"], "确认")


if __name__ == "__main__":
    unittest.main()
