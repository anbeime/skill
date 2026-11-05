from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
INIT = ROOT / "skills" / "zongkong" / "scripts" / "init_project.py"


class InitProjectTests(unittest.TestCase):
    def command(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run([sys.executable, str(INIT), *args], cwd=ROOT, check=check, text=True, capture_output=True)

    def test_creates_a_user_selected_new_absolute_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "selected-project"
            self.command("test-couple", "--project-dir", str(project))
            self.assertTrue((project / "project.yaml").exists())
            self.assertTrue((project / "themes").is_dir())

    def test_accepts_a_user_selected_empty_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "empty-project"
            project.mkdir()
            self.command("test-couple", "--project-dir", str(project))
            self.assertTrue((project / "themes").is_dir())

    def test_rejects_missing_relative_and_non_empty_directories_without_writing(self) -> None:
        missing = self.command("test-couple", check=False)
        self.assertNotEqual(missing.returncode, 0)

        relative = self.command("test-couple", "--project-dir", "relative-project", check=False)
        self.assertNotEqual(relative.returncode, 0)

        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp) / "occupied-project"
            project.mkdir()
            sentinel = project / "keep.txt"
            sentinel.write_text("keep", encoding="utf-8")
            occupied = self.command("test-couple", "--project-dir", str(project), check=False)
            self.assertNotEqual(occupied.returncode, 0)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "keep")
            self.assertFalse((project / "project.yaml").exists())


if __name__ == "__main__":
    unittest.main()
