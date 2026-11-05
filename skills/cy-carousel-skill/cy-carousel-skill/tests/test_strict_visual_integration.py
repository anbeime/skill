"""真实渲染/检查/CLI/打包回归，不用桩替代规则函数或渲染报告。"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

import check_all
import package
import render
import 手排 as S


class StrictSkeletonIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.base = Path(cls.tmp.name)
        # 原尺寸、确定性几何图案：隔离同骨架门禁，不触发留白或放大限制。
        image = Image.new('RGB', (1440, 1920))
        draw = ImageDraw.Draw(image)
        for y in range(0, 1920, 32):
            for x in range(0, 1440, 32):
                draw.rectangle((x, y, x + 31, y + 31),
                               fill='#305880' if (x // 32 + y // 32) % 2 else '#A0A0A0')
        cls.notes = {}
        for variant in ('repeated', 'alternating', 'missing'):
            note = cls.base / variant
            note.mkdir()
            image.save(note / 'fixture.png')
            pages = [S.page(None, [S.headline('严格视觉测试', .05, .10, 110),
                                  S.headline('[[骨架阻断回归]]', .05, .25, 110)], layout='cover')]
            for i in range(8):
                lower = variant == 'alternating' and i % 2
                page = S.page(None, [S.body('相同布局与交替布局的真实流程回归。',
                                           .05, .66 if lower else .20, .90, 56)],
                              backdrop=S.backdrop('fixture.png', .5))
                page.update(text_position='bottom-left' if lower else 'top-left',
                            visual_focus='fixture')
                if variant != 'missing':
                    page['skeleton'] = 'full-background-bottom-text' if lower else 'full-background-top-text'
                pages.append(page)
            data = {'mode': 'production', 'tone': '暗', 'config': {
                'accent': S.CYAN, 'background': S.PAGE_BG, 'account_name': '测试',
                'watermark_text': '测试', 'watermark_style': 'neutral', 'bookmark': False,
                'cover_only': False}, 'pages': pages}
            (note / '页面脚本.json').write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
            for name in ('标题.txt', '正文.txt', '置顶评论.txt', '来源.md'):
                (note / name).write_text('确定性集成测试夹具，不作发布用途。', encoding='utf-8')
            render.render(note / '页面脚本.json', note / 'pages', assets_root=note)
            cls.notes[variant] = note

    def check(self, variant, strict):
        note = self.notes[variant]
        return check_all.check_note(note / '页面脚本.json', note / 'pages',
                                    assets_root=note, strict_visual=strict)

    def check_cli(self, variant, strict):
        note = self.notes[variant]
        args = [sys.executable, str(ROOT / 'scripts/check_all.py'), str(note / '页面脚本.json'),
                '--pages', str(note / 'pages'), '--assets-root', str(note)]
        if strict:
            args.append('--strict-visual')
        return subprocess.run(args, capture_output=True, text=True, encoding='utf-8',
                              env={**os.environ, 'PYTHONIOENCODING': 'utf-8'})

    def deliver(self, variant, destination, **kwargs):
        note = self.notes[variant]
        return package.deliver(note, note / 'pages', self.base / destination,
                               assets_root=note, **kwargs)

    def test_repeated_skeleton_blocks_real_strict_pipeline(self):
        result = self.check('repeated', True)
        actual = [m for m in result['checks']['richness']['errors'] if '骨架相同' in m]
        self.assertEqual(len(actual), 7)
        self.assertTrue(result['checks']['whitespace']['passed'])
        self.assertTrue(result['passed'], result['errors'])
        self.assertEqual(result['visual_blockers'], actual)
        cli = self.check_cli('repeated', True)
        self.assertEqual(cli.returncode, 1, cli.stdout + cli.stderr)
        with self.assertRaisesRegex(ValueError, 'accept-visual'):
            self.deliver('repeated', 'strict-blocked', strict_visual=True)
        self.assertFalse((self.base / 'strict-blocked').exists())

    def test_default_mode_keeps_skeleton_advisory(self):
        result = self.check('repeated', False)
        self.assertTrue(result['passed'], result['errors'])
        self.assertEqual(result['visual_blockers'], [])
        self.assertEqual(len([m for m in result['advisories'] if '骨架相同' in m]), 7)
        cli = self.check_cli('repeated', False)
        self.assertEqual(cli.returncode, 0, cli.stderr)
        manifest = self.deliver('repeated', 'default-delivery')
        self.assertTrue(manifest['technical_passed'])
        self.assertIsNone(manifest['visual_accepted'])

    def test_manual_acceptance_records_real_skeleton_blockers(self):
        manifest = self.deliver('repeated', 'accepted-delivery', strict_visual=True,
                                accept_visual='目检后确认本稿需要重复布局')
        accepted = manifest['visual_accepted']
        self.assertIsNotNone(accepted)
        self.assertEqual(accepted['reason'], '目检后确认本稿需要重复布局')
        self.assertEqual(len(accepted['blockers']), 7)
        self.assertTrue(all('骨架相同' in m for m in accepted['blockers']))
        saved = json.loads((self.base / 'accepted-delivery/交付清单.json').read_text(encoding='utf-8'))
        self.assertEqual(saved['visual_accepted'], accepted)

    def test_alternating_skeleton_passes_real_strict_pipeline(self):
        result = self.check('alternating', True)
        self.assertTrue(result['passed'], result['errors'])
        self.assertEqual(result['visual_blockers'], [])
        self.assertTrue(result['checks']['whitespace']['passed'])
        cli = self.check_cli('alternating', True)
        self.assertEqual(cli.returncode, 0, cli.stderr)
        manifest = self.deliver('alternating', 'alternating-delivery', strict_visual=True)
        self.assertTrue(manifest['technical_passed'])
        self.assertIsNone(manifest['visual_accepted'])

    def test_missing_skeleton_is_not_evidence_of_repeated_layout(self):
        result = self.check('missing', True)
        self.assertTrue(result['passed'], result['errors'])
        self.assertEqual(result['visual_blockers'], [])
        self.assertTrue(any('缺少骨架' in m for m in result['advisories']))
        self.assertFalse(any('骨架相同' in m for m in result['advisories']))


if __name__ == '__main__':
    unittest.main()
