import importlib.util
import os
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
BANNER_SCRIPT = ROOT / "scripts" / "render_banners.py"
SPEC = importlib.util.spec_from_file_location("render_banners", BANNER_SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class BannerHtmlTests(unittest.TestCase):
    def test_every_language_builds(self):
        for lang, copy in MODULE.COPY.items():
            with self.subTest(lang=lang):
                html = MODULE.build_html(lang)
                for line in copy["lines"]:
                    self.assertIn(line, html)
                for name in MODULE.wall_images():
                    self.assertIn(f"gallery/{name}", html)

    def test_wall_images_exist(self):
        for name in MODULE.wall_images():
            path = MODULE.GALLERY_DIR / name
            self.assertTrue(path.is_file(), path)

    def test_committed_banners(self):
        for lang in MODULE.COPY:
            with self.subTest(lang=lang):
                path = ROOT / "assets" / f"banner-{lang}.jpg"
                self.assertTrue(path.is_file(), path)
                # 中文版兼作 GitHub 社交预览图：上限 1MB，推荐 2:1。
                self.assertLess(path.stat().st_size, 1_000_000)
                with MODULE.Image.open(path) as image:
                    self.assertEqual(image.size, (MODULE.WIDTH * MODULE.SCALE, MODULE.HEIGHT * MODULE.SCALE))

    def test_readmes_use_banners(self):
        for readme, lang in (("README.md", "zh"), ("README_EN.md", "en"), ("README_KO.md", "ko")):
            with self.subTest(readme=readme):
                self.assertIn(f'src="assets/banner-{lang}.jpg"', (ROOT / readme).read_text(encoding="utf-8"))


class FindChromeTests(unittest.TestCase):
    def test_explicit_path_wins(self):
        with mock.patch.dict(os.environ, {"CHROME": "/from/env"}):
            self.assertEqual(MODULE.find_chrome("/explicit"), "/explicit")

    def test_env_used_when_no_explicit_path(self):
        with mock.patch.dict(os.environ, {"CHROME": "/from/env"}):
            self.assertEqual(MODULE.find_chrome(), "/from/env")

    def test_returns_none_when_nothing_found(self):
        env = {k: v for k, v in os.environ.items() if k != "CHROME"}
        with mock.patch.dict(os.environ, env, clear=True), \
             mock.patch.object(MODULE, "CHROME_CANDIDATES", []), \
             mock.patch.object(MODULE.shutil, "which", return_value=None):
            self.assertIsNone(MODULE.find_chrome())


if __name__ == "__main__":
    unittest.main()
