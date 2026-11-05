import ast
import importlib.util
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
ENV_SCRIPT = (
    ROOT / "skills" / "native-subtitle-quote-image" / "scripts" / "check_environment.py"
)
SPEC = importlib.util.spec_from_file_location("check_environment", ENV_SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

SOURCE_DIRS = ("skills/native-subtitle-quote-image/scripts", "scripts", "tests")


def keyword_names(call):
    return {keyword.arg for keyword in call.keywords}


def missing_encoding(call):
    """返回未显式指定编码的文本 I/O 调用描述，否则返回 None。"""
    func = call.func
    name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", "")
    keywords = keyword_names(call)
    if name in ("read_text", "write_text") and "encoding" not in keywords:
        return name
    if name == "open" and not ast.unparse(func).endswith("Image.open"):
        # Path.open(mode) 或内置 open(path, mode)：二进制模式无需编码。
        mode_args = [a for a in call.args if isinstance(a, ast.Constant) and isinstance(a.value, str)]
        mode = next((k.value.value for k in call.keywords if k.arg == "mode"), None)
        modes = [m.value for m in mode_args] + ([mode] if isinstance(mode, str) else [])
        if not any("b" in m for m in modes) and "encoding" not in keywords:
            if not (isinstance(func, ast.Name) and not call.args):
                return name
    if name == "run" and "text" in keywords and "encoding" not in keywords:
        return "subprocess.run(text=True)"
    return None


class TextEncodingTests(unittest.TestCase):
    def test_utf8_default_detection(self):
        with mock.patch.object(MODULE.sys, "flags", mock.Mock(utf8_mode=1)):
            self.assertTrue(MODULE.utf8_default())
        with mock.patch.object(MODULE.sys, "flags", mock.Mock(utf8_mode=0)):
            with mock.patch.object(MODULE.locale, "getpreferredencoding", return_value="cp936"):
                self.assertFalse(MODULE.utf8_default())
            with mock.patch.object(MODULE.locale, "getpreferredencoding", return_value="UTF-8"):
                self.assertTrue(MODULE.utf8_default())

    def test_non_utf8_default_adds_hint_row(self):
        with mock.patch.object(MODULE, "utf8_default", return_value=False):
            rows = MODULE.inspect_environment()
        row = next(r for r in rows if r["component"] == "UTF-8 encoding")
        self.assertIn("PYTHONUTF8=1", row["detail"])
        self.assertFalse(MODULE.is_blocking(row, True, True))

    def test_no_implicit_locale_text_io(self):
        problems = []
        for directory in SOURCE_DIRS:
            for path in sorted((ROOT / directory).glob("*.py")):
                tree = ast.parse(path.read_text(encoding="utf-8"))
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        found = missing_encoding(node)
                        if found:
                            problems.append(f"{path.relative_to(ROOT)}:{node.lineno} {found}")
        self.assertEqual(problems, [])


if __name__ == "__main__":
    unittest.main()
