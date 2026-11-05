"""跨平台兼容测试：UTF-8 读写、OCR 延迟初始化、清单结构报错、打包缺文稿提示。"""

import json
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import 手排 as S  # noqa: E402
import check_all  # noqa: E402
import package  # noqa: E402


class Utf8Tests(unittest.TestCase):
    def test_scripts_do_not_use_default_encoding(self):
        # 内建 open() 与 Path.read_text/write_text；Image.open 等带点号的调用不在此列
        call = re.compile(r"((?<![\w.])open|\.read_text|\.write_text)\(([^()]*(?:\([^()]*\)[^()]*)*)\)")
        binary = re.compile(r"""['"][rwax+]*b[rwax+]*['"]""")
        for path in (ROOT / "scripts").glob("*.py"):
            for m in call.finditer(path.read_text(encoding="utf-8")):
                args = m.group(2)
                if "encoding=" in args:
                    continue
                if m.group(1) == "open" and binary.search(args):
                    continue
                self.fail(f"{path.name}: {m.group(0)} 缺少 encoding=")

    def test_write_script_uses_utf8(self):
        with tempfile.TemporaryDirectory() as td:
            S.init(td)
            S.pages[:] = []
            S.write_script("测试", "手排.py")
            raw = (Path(td) / "页面脚本.json").read_bytes()
            self.assertEqual(json.loads(raw.decode("utf-8"))["topic"], "测试")


class LazyOcrTests(unittest.TestCase):
    def test_init_does_not_call_swiftc(self):
        with tempfile.TemporaryDirectory() as td, mock.patch.object(S.subprocess, "run") as run:
            S.init(td)
            run.assert_not_called()

    def test_missing_swift_gives_clear_error(self):
        with tempfile.TemporaryDirectory() as td:
            missing = Path(td) / "bin/tool"
            with mock.patch.object(S.sys, "platform", "win32"):
                with self.assertRaisesRegex(RuntimeError, "macOS"):
                    S._ensure_tool(missing, "ocrfind.swift", "OCR 词框")


class ManifestTests(unittest.TestCase):
    def test_array_manifest_gives_friendly_error(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "素材清单.json"
            p.write_text(json.dumps([{"path": "a.png", "sha256": "x"}]), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "assets"):
                check_all.load_manifest(p)

    def test_valid_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "素材清单.json"
            p.write_text(json.dumps({"assets": [{"path": "a.png", "sha256": "x"}]}), encoding="utf-8")
            self.assertEqual(check_all.load_manifest(p), [{"path": "a.png", "sha256": "x"}])

    def test_visual_acceptance_never_claims_pass(self):
        self.assertIn("未验收", check_all.visual_acceptance([]))
        self.assertIn("3 条", check_all.visual_acceptance(["a", "b", "c"]))


class PackageTests(unittest.TestCase):
    def test_missing_manuscript_lists_required_files(self):
        with tempfile.TemporaryDirectory() as td:
            note = Path(td) / "note"
            note.mkdir()
            with mock.patch.object(package, "check_note", return_value={"passed": True, "scope": "x"}):
                with self.assertRaisesRegex(ValueError, "标题.txt.*正文.txt.*置顶评论.txt.*来源.md"):
                    package.deliver(note, Path(td) / "pages", Path(td) / "out")

    def test_cli_success_path(self):
        from PIL import Image

        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            note, pages, out = td / "note", td / "pages", td / "out"
            note.mkdir()
            pages.mkdir()
            (note / "页面脚本.json").write_text(
                json.dumps({"topic": "测试", "pages": [{}]}), encoding="utf-8")
            for name in ("标题.txt", "正文.txt", "置顶评论.txt", "来源.md"):
                (note / name).write_text("内容", encoding="utf-8")
            Image.new("RGB", (1440, 1920), "white").save(pages / "p01.png")
            # 只替换检查环节，其余走真实的 CLI 入口与打包流程
            code = (
                "import sys, runpy, check_all;"
                "check_all.check_note = lambda *a, **k: dict(passed=True, errors=[], scope='test',"
                " visual_acceptance='未验收', advisories=[]);"
                "sys.argv = ['package.py'] + sys.argv[1:];"
                "runpy.run_path('package.py', run_name='__main__')"
            )
            proc = subprocess.run(
                [sys.executable, "-c", code, "--note", str(note), "--pages", str(pages), "--out", str(out)],
                cwd=ROOT / "scripts", capture_output=True, encoding="utf-8")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            result = json.loads(proc.stdout)
            self.assertIn("visual_acceptance", result)
            self.assertEqual(result["images"], 1)
            self.assertTrue((out / "交付清单.json").is_file())


if __name__ == "__main__":
    unittest.main()
