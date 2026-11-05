"""渲染冒烟测试：只用仓库自带字体，在 Linux / macOS 上都能跑。"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import 手排 as S  # noqa: E402
import render  # noqa: E402
from check_all import red_lines  # noqa: E402


def sample_page():
    return {
        "layout": "cover",
        "elements": [
            S.headline("什么是 AI 幻觉，\n[[一场官司讲清楚]]", 0.06, 0.05, 118),
            S.body("律师让 ChatGPT 找判例，交上去的六个判例全是编的。", 0.06, 0.5, 0.88),
            S.body("文楷正文样张。", 0.06, 0.6, 0.88, font="文楷"),
            S.big("6", 0.06, 0.7, 200),
            S.sticker("真的吗？", 0.06, 0.85),
        ],
    }


class RenderSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        out = Path(cls.tmp.name)
        cls.page = sample_page()
        spec = out / "页面脚本.json"
        spec.write_text(
            json.dumps({"mode": "sample", "tone": "暗", "config": {}, "pages": [cls.page]}, ensure_ascii=False),
            encoding="utf-8",
        )
        cls.reports = render.render(spec, out / "pages")
        cls.image = Image.open(out / "pages" / "p01.png").convert("RGB")

    @classmethod
    def tearDownClass(cls):
        cls.image.close()
        cls.tmp.cleanup()

    def test_page_size_and_report(self):
        self.assertEqual(self.image.size, (1440, 1920))
        self.assertEqual(len(self.reports), 1)
        self.assertEqual(self.reports[0]["size"], [1440, 1920])

    def test_bundled_fonts_are_used(self):
        fonts = [t.get("font") for t in self.reports[0]["text"]]
        self.assertEqual(fonts[:3], ["headline", "serif-bold", "wenkai"])

    def test_background_is_pure_black(self):
        # check_all 只认 ≤8 为纯黑。
        self.assertLessEqual(max(self.image.getpixel((1400, 900))), 8)

    def test_headline_second_line_is_cyan(self):
        pixels = np.asarray(self.image.crop((80, 230, 950, 380))).reshape(-1, 3)
        r, g, b = pixels.T
        self.assertTrue(((r < 60) & (g > 200) & (b > 220)).any())

    def test_text_stays_inside_page(self):
        for text in self.reports[0]["text"]:
            x0, y0, x1, y1 = text["ink_bounds"]
            self.assertTrue(0 <= x0 < x1 <= 1440 and 0 <= y0 < y1 <= 1920, text["text"])

    def test_red_lines_pass(self):
        self.assertEqual(red_lines(1, self.page, self.reports[0]), [])


class LatinFontFallbackTest(unittest.TestCase):
    def setUp(self):
        self.saved = {k: render.SYSTEM_FONTS[k] for k in ("serif-latin", "serif-latin-bold", "songti-sc")}
        for k in self.saved:
            render.SYSTEM_FONTS[k] = [("/nonexistent/font.ttf", None)]
            render.FONTS.pop(k, None)
        render.warn_latin_fallback.cache_clear()

    def tearDown(self):
        render.SYSTEM_FONTS.update(self.saved)
        for k in self.saved:
            render.FONTS.pop(k, None)

    def test_latin_fonts_fall_back_with_warning(self):
        for name in ("serif-latin", "serif-latin-bold"):
            with self.assertWarns(RuntimeWarning):
                face, info = render.resolved_font(name, 40, {})
            self.assertTrue(info["fallback"])
            self.assertEqual(info["source"], "latin-fallback")
            self.assertGreater(face.getlength("Ab12"), 0)

    def test_other_system_fonts_still_raise(self):
        with self.assertRaises(FileNotFoundError):
            render.font("songti-sc", 40, {})

    def test_body_typo_renders(self):
        with self.assertWarns(RuntimeWarning):
            S.body("律师让 ChatGPT 找判例，共 6 个。", 0.06, 0.5, 0.88, typo=True)


if __name__ == "__main__":
    unittest.main()
