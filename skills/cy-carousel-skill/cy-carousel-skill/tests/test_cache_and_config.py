"""修复轮回归测试：断行缓存键、水印占位符、ink_box 键、aged 确定性、PDF 文档复用。

只用仓库自带字体；PDF 用 pymupdf 现做，不依赖 macOS 系统字体和 Swift 工具。
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from PIL import Image, ImageFont

import build as T
import render as RD
import 手排 as S


class FitCacheKeyTest(unittest.TestCase):
    def test_tight_punctuation_is_part_of_cache_key(self):
        # 标点密集文本：tight='all'（optical 压缩标点）与 False 的行数确实不同；
        # 先查 all 再查 False 时，False 必须拿到自己的真实行数，不能命中 all 的缓存。
        text = "一。二。三。四。五。六。七。一。二。三。四。五。六。七。"
        base = {"font": "serif-bold", "size": 60, "box": [0.06, 0, 0.84, 1], "spacing": 0,
                "hscale": 1.0, "typo": False, "stroke": 0}
        T._FIT_CACHE.clear()
        tight = T.rendered_lines({**base, "tight_punctuation": "all"}, text)
        T._FIT_CACHE.clear()
        plain = T.rendered_lines({**base, "tight_punctuation": False}, text)
        self.assertNotEqual(tight, plain)
        T._FIT_CACHE.clear()
        T.rendered_lines({**base, "tight_punctuation": "all"}, text)
        self.assertEqual(T.rendered_lines({**base, "tight_punctuation": False}, text), plain)


class InkBoxCacheTest(unittest.TestCase):
    def test_stroke_is_part_of_cache_key(self):
        face = ImageFont.truetype(str(RD.FONT_ROOT / "NotoSerifSC[wght].ttf"), 60, index=0)
        face.set_variation_by_axes([700])
        self.assertNotEqual(RD.ink_box(face, "国", 0), RD.ink_box(face, "国", 3))


class WriteScriptPlaceholderTest(unittest.TestCase):
    def test_write_script_uses_placeholder_account(self):
        with tempfile.TemporaryDirectory() as td:
            saved = (S.NOTE, S.OUT, S.PROTECT, list(S.pages))
            S.init(td)
            S.pages = []
            try:
                S.write_script("测试", "测试")
                data = json.loads((Path(td) / "页面脚本.json").read_text(encoding="utf-8"))
                # 占位符沿用 package.py 认的 {账号名}，打包清单才会标 placeholder_account；水印字去掉花括号。
                self.assertEqual(data["config"]["account_name"], "{账号名}")
                self.assertEqual(data["config"]["watermark_text"], "账号名")
                S.write_script("测试", "测试", account="某某")
                data = json.loads((Path(td) / "页面脚本.json").read_text(encoding="utf-8"))
                self.assertEqual(data["config"]["account_name"], "某某")
                self.assertEqual(data["config"]["watermark_text"], "某某")
            finally:
                S.NOTE, S.OUT, S.PROTECT, S.pages = saved[0], saved[1], saved[2], saved[3]


class AgedDeterminismTest(unittest.TestCase):
    def test_aged_noise_is_deterministic(self):
        with tempfile.TemporaryDirectory() as td:
            Image.new("RGB", (120, 90), (200, 180, 160)).save(Path(td) / "a.png")
            args = ({"path": "a.png", "effects": ["aged"]}, td, (100, 100), {"cover_only": False})
            first = RD.processed_image(*args).tobytes()
            second = RD.processed_image(*args).tobytes()
            self.assertEqual(first, second)

    def test_aged_noise_is_monochrome(self):
        # 噪点是灰度颗粒：纯灰输入加 aged 后，每个像素三通道仍相等，不能出现彩色噪点。
        with tempfile.TemporaryDirectory() as td:
            Image.new("RGB", (120, 90), (128, 128, 128)).save(Path(td) / "a.png")
            out = RD.processed_image({"path": "a.png", "effects": ["aged"]}, td, (100, 100), {"cover_only": False})
            r, g, b = out.convert("RGB").split()
            self.assertEqual(r.tobytes(), g.tobytes())
            self.assertEqual(g.tobytes(), b.tobytes())


class PdfDocCacheTest(unittest.TestCase):
    def test_snap_find_strip_open_pdf_once(self):
        import pymupdf
        with tempfile.TemporaryDirectory() as td:
            doc = pymupdf.open()
            page = doc.new_page(width=595, height=842)
            page.insert_text((72, 100), "The quick brown fox jumps over the lazy dog near the river bank.", fontsize=12)
            doc.save(str(Path(td) / "t.pdf"))
            doc.close()
            saved = (S.NOTE, S.OUT, S.PROTECT, list(S.pages))
            S.init(td)
            opens = []
            real_open = S.pymupdf.open

            def counting_open(p):
                opens.append(str(p))
                return real_open(p)

            S.pymupdf.open = counting_open
            try:
                S.find("t.pdf", 0, "brown")
                S.snap("t.pdf", 0, [0.1, 0.09, 0.9, 0.15])
                S.strip("t.pdf", 0, [0.08, 0.08, 0.92, 0.16], 800, circles=("brown",))
                self.assertEqual(len(opens), 1)
            finally:
                S.pymupdf.open = real_open
                # 临时目录清理前关掉缓存的 PDF：Windows 上文件被占用时删不掉（WinError 32）。
                for d in S.PDF_DOCS.values():
                    d.close()
                S.PDF_DOCS.clear()
                S.NOTE, S.OUT, S.PROTECT, S.pages = saved[0], saved[1], saved[2], saved[3]

    def test_init_closes_cached_pdfs(self):
        import pymupdf
        with tempfile.TemporaryDirectory() as td, tempfile.TemporaryDirectory() as td2:
            doc = pymupdf.open()
            doc.new_page().insert_text((72, 100), "hello", fontsize=12)
            doc.save(str(Path(td) / "t.pdf"))
            doc.close()
            saved = (S.NOTE, S.OUT, S.PROTECT, list(S.pages))
            try:
                S.init(td)
                cached = S._doc("t.pdf")
                self.assertEqual(len(S.PDF_DOCS), 1)
                S.init(td2)
                self.assertEqual(S.PDF_DOCS, {})
                self.assertTrue(cached.is_closed)
            finally:
                S.NOTE, S.OUT, S.PROTECT, S.pages = saved[0], saved[1], saved[2], saved[3]


if __name__ == "__main__":
    unittest.main()
