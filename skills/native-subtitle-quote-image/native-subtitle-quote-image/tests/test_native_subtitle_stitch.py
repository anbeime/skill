import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from PIL import Image, ImageDraw, ImageOps


# 子进程继承 UTF-8 模式，避免 GBK 等默认编码下输出与解码不一致。
os.environ.setdefault("PYTHONUTF8", "1")

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = (
    ROOT
    / "skills"
    / "native-subtitle-quote-image"
    / "scripts"
    / "native_subtitle_stitch.py"
)
ENV_SCRIPT = (
    ROOT
    / "skills"
    / "native-subtitle-quote-image"
    / "scripts"
    / "check_environment.py"
)
SPEC = importlib.util.spec_from_file_location("native_subtitle_stitch", SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class HelperTests(unittest.TestCase):
    def test_parse_aspect_and_safe_title(self):
        self.assertEqual(MODULE.parse_aspect("3:4"), (3.0, 4.0))
        self.assertEqual(MODULE.safe_title('a/b:c*?"<>|'), "a_b_c")

    def test_default_sample_times_cover_range_with_24_frames(self):
        times = MODULE.build_sample_times(0, 230, None, 48)
        self.assertEqual(len(times), 24)
        self.assertEqual(times[0], 0)
        self.assertAlmostEqual(times[-1], 230)

    def test_sample_times_enforce_frame_cap(self):
        with self.assertRaisesRegex(SystemExit, "超过上限"):
            MODULE.build_sample_times(0, 100, 1, 48)

    def test_focus_times_add_before_middle_and_after(self):
        times = MODULE.build_focus_times([1, 3], 0.5, 5, 48)
        self.assertEqual(times, [0.5, 1.0, 1.5, 2.5, 3.0, 3.5])

    def test_focus_times_clip_and_deduplicate_edges(self):
        times = MODULE.build_focus_times([0, 2.7], 0.5, 3, 48)
        self.assertEqual(times, [0.0, 0.5, 2.2, 2.7])

    def test_auto_layout_keeps_subtitle_strips_compact(self):
        self.assertEqual(MODULE.choose_hero_fraction(4), 0.7)
        self.assertEqual(MODULE.choose_hero_fraction(3), 0.775)
        self.assertEqual(MODULE.choose_hero_fraction(2), 0.82)
        self.assertEqual(MODULE.choose_hero_fraction(7), 0.48)
        self.assertEqual(MODULE.choose_hero_fraction(4, 0.6), 0.6)

    def test_script_lines_require_increasing_timestamps_and_text(self):
        lines = MODULE.normalize_script_lines(
            {
                "lines": [
                    {"t": 1, "text": "First"},
                    {"t": 2, "text": "Second"},
                ]
            },
            3,
        )
        self.assertEqual(lines[1]["text"], "Second")
        with self.assertRaisesRegex(SystemExit, "严格递增"):
            MODULE.normalize_script_lines(
                {
                    "lines": [
                        {"t": 2, "text": "First"},
                        {"t": 1, "text": "Second"},
                    ]
                },
                3,
            )
        with self.assertRaisesRegex(SystemExit, "最多支持 7"):
            MODULE.normalize_script_lines(
                {
                    "lines": [
                        {"t": index / 10, "text": f"Line {index}"}
                        for index in range(8)
                    ]
                },
                3,
            )

    def test_native_times_share_script_mode_cap(self):
        times = MODULE.normalize_times([index / 10 for index in range(7)])
        self.assertEqual(len(times), 7)
        with self.assertRaisesRegex(SystemExit, "最多支持 7"):
            MODULE.normalize_times([index / 10 for index in range(8)])

    def test_cjk_detection_covers_chinese_japanese_and_korean(self):
        self.assertTrue(MODULE.contains_cjk("中文"))
        self.assertTrue(MODULE.contains_cjk("かな"))
        self.assertTrue(MODULE.contains_cjk("한글"))
        self.assertFalse(MODULE.contains_cjk("English"))

    def test_hangul_detection(self):
        self.assertTrue(MODULE.contains_hangul("한글"))
        self.assertTrue(MODULE.contains_hangul("ㅋㅋ"))
        self.assertFalse(MODULE.contains_hangul("中文"))
        self.assertFalse(MODULE.contains_hangul("かな"))
        self.assertFalse(MODULE.contains_hangul("English"))

    def test_hangul_is_always_cjk(self):
        for sample in ("한글", "ㅋㅋ", "ᄀ"):
            self.assertTrue(MODULE.contains_hangul(sample))
            self.assertTrue(MODULE.contains_cjk(sample))
        for start, end in MODULE.HANGUL_RANGES:
            self.assertTrue(MODULE.contains_cjk(start))
            self.assertTrue(MODULE.contains_cjk(end))

    def test_font_candidates_put_korean_fonts_first_for_hangul(self):
        result = MODULE.font_candidates(None, "안녕하세요")
        self.assertEqual(
            result, MODULE.KOREAN_FONT_CANDIDATES + MODULE.FONT_CANDIDATES
        )
        self.assertLess(
            result.index("/System/Library/Fonts/AppleSDGothicNeo.ttc"),
            result.index("/System/Library/Fonts/PingFang.ttc"),
        )
        self.assertLess(
            result.index("C:/Windows/Fonts/malgun.ttf"),
            result.index("C:/Windows/Fonts/msyh.ttc"),
        )

    def test_font_candidates_keep_user_font_first(self):
        result = MODULE.font_candidates("custom.ttf", "안녕하세요")
        self.assertEqual(result[0], "custom.ttf")
        self.assertEqual(result[1:3], MODULE.KOREAN_FONT_CANDIDATES)

    def test_font_candidates_unchanged_for_chinese_and_japanese(self):
        for text in ("中文台词", "かな"):
            self.assertEqual(
                MODULE.font_candidates(None, text), MODULE.FONT_CANDIDATES
            )
        self.assertEqual(
            MODULE.font_candidates("custom.ttf", "中文"),
            ["custom.ttf"] + MODULE.FONT_CANDIDATES,
        )

    def test_environment_check_local_mode_is_machine_readable(self):
        proc = subprocess.run(
            [sys.executable, str(ENV_SCRIPT), "--json"],
            capture_output=True,
            encoding="utf-8", errors="replace",
            check=True,
        )
        payload = json.loads(proc.stdout)
        self.assertEqual(payload["mode"], "local")
        self.assertTrue(payload["ok"])
        components = {item["component"] for item in payload["components"]}
        self.assertIn("Python 3.10+", components)
        self.assertIn("yt-dlp", components)
        self.assertIn("CJK font", components)

    def test_environment_check_url_mode_guides_cookie_recovery(self):
        proc = subprocess.run(
            [sys.executable, str(ENV_SCRIPT), "--url-mode"],
            capture_output=True,
            encoding="utf-8", errors="replace",
            check=False,
        )
        self.assertIn("不要退回本地模式", proc.stdout)
        self.assertIn("--cookies-from-browser chrome", proc.stdout)

    def test_render_one_has_requested_dimensions(self):
        frame = Image.new("RGB", (640, 360), "#336699")
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            MODULE, "grab_frame", return_value=frame
        ):
            out = Path(tmp) / "render.jpg"
            MODULE.render_one(
                "unused.mp4",
                [0, 1, 2, 3, 4],
                out,
                (3, 4),
                300,
                0.68,
                0.96,
                0.42,
                layout="fixed",
            )
            with Image.open(out) as rendered:
                self.assertEqual(rendered.size, (300, 400))

    def test_render_one_default_keeps_source_geometry_not_seventy_percent(self):
        def fake_frame(_video, seconds):
            color = "#cc0000" if seconds == 0 else "#0033cc"
            return Image.new("RGB", (640, 360), color)

        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            MODULE, "grab_frame", side_effect=fake_frame
        ):
            out = Path(tmp) / "auto-layout.jpg"
            MODULE.render_one(
                "unused.mp4",
                [0, 1, 2, 3, 4],
                out,
                (3, 4),
                300,
                0.78,
                0.96,
                None,
            )
            with Image.open(out) as rendered:
                self.assertEqual(rendered.size, (300, 284))
                self.assertGreater(rendered.getpixel((10, 160))[0], 180)
                self.assertGreater(rendered.getpixel((10, 164))[2], 150)

    def test_missing_input_is_readable_without_traceback(self):
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPT),
                "render",
                "/no/such/video.mp4",
                "--manifest",
                "/no/such/manifest.json",
                "--out-dir",
                "/tmp/unused-native-subtitle-output",
            ],
            capture_output=True,
            encoding="utf-8", errors="replace",
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("视频不存在或不是文件", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)


class NaturalGeometryTests(unittest.TestCase):
    def test_native_subtitles_have_same_size_in_hero_and_every_strip(self):
        for frame_size in [(1280, 720), (720, 1280)]:
            for layout, fit in [("natural", "crop"), ("fixed", "pad"), ("fixed", "crop")]:
                with self.subTest(frame_size=frame_size, layout=layout, fit=fit):
                    w, h = frame_size
                    frame = Image.new("RGB", frame_size, "black")
                    # 宽度覆盖近全帧，模拟长字幕，能同时抓出裁字和字号不一致。
                    ImageDraw.Draw(frame).rectangle(
                        (round(w * 0.03), round(h * 0.88), round(w * 0.97), round(h * 0.91)),
                        fill="white",
                    )
                    with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
                        MODULE, "grab_frame", return_value=frame
                    ):
                        out = Path(tmp) / "uniform.jpg"
                        MODULE.render_one("unused", [0, 1, 2, 3, 4], out, (3, 4), 1080,
                                          0.78, 0.96, None, layout=layout, fit=fit)
                        with Image.open(out) as opened:
                            mask = opened.convert("L").point(lambda p: 255 if p > 127 else 0)
                            runs = []
                            for y in range(mask.height):
                                bounds = mask.crop((0, y, mask.width, y + 1)).getbbox()
                                if bounds is not None:
                                    if not runs or runs[-1][1] != y:
                                        runs.append([y, y + 1, bounds[0], bounds[2]])
                                    else:
                                        runs[-1][1] = y + 1
                                        runs[-1][2] = min(runs[-1][2], bounds[0])
                                        runs[-1][3] = max(runs[-1][3], bounds[2])
                            self.assertEqual(len(runs), 5)
                            heights = [r[1] - r[0] for r in runs]
                            widths = [r[3] - r[2] for r in runs]
                            self.assertLessEqual(max(heights) - min(heights), 1)
                            self.assertLessEqual(max(widths) - min(widths), 1)
                            if layout == "fixed":
                                self.assertEqual(opened.size, (1080, 1440))
                                source_height = int(h * 0.96) + 4 * (int(h * 0.96) - int(h * 0.78))
                                scale = min(1080 / w, 1440 / source_height)
                                expected_width = (round(w * 0.97) - round(w * 0.03) + 1) * scale
                                if fit == "pad":
                                    self.assertLessEqual(abs(min(widths) - expected_width), 2)
                                else:
                                    # 长字幕只允许裁到安全边界：不小于留边版，也不碰画布边缘。
                                    self.assertGreaterEqual(min(widths), expected_width - 2)
                                    self.assertGreater(min(r[2] for r in runs), 0)
                                    self.assertLess(max(r[3] for r in runs), opened.width)
                            else:
                                self.assertGreater(min(widths), 1080 * 0.9)

    def test_crop_and_same_width_keep_exact_source_pixels(self):
        frame = Image.new("RGB", (1280, 720), "black")
        ImageDraw.Draw(frame).ellipse((100, 100, 300, 300), fill="white")
        cropped, y0, y1 = MODULE.crop_band(frame, 0, 0.72)
        result = MODULE.scale_to_width(cropped, 1280)
        self.assertEqual((y0, y1), (0, 518))
        self.assertEqual(result.size, (1280, 518))
        self.assertEqual(result.tobytes(), frame.crop((0, 0, 1280, 518)).tobytes())

    def test_scaling_preserves_circle_geometry(self):
        frame = Image.new("RGB", (1280, 518), "black")
        ImageDraw.Draw(frame).ellipse((100, 100, 300, 300), fill="white")
        result = MODULE.scale_to_width(frame, 640)
        bounds = result.convert("L").point(lambda p: 255 if p > 127 else 0).getbbox()
        self.assertEqual(result.size, (640, 259))
        self.assertLessEqual(abs((bounds[2] - bounds[0]) - (bounds[3] - bounds[1])), 1)

    def test_native_natural_retains_full_width_and_band_height(self):
        frame = Image.new("RGB", (640, 360), "#336699")
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            MODULE, "grab_frame", return_value=frame
        ):
            out = Path(tmp) / "native.jpg"
            MODULE.render_one("unused", [0, 1, 2, 3, 4], out, (3, 4), None,
                              0.78, 0.96, None, layout="natural")
            with Image.open(out) as rendered:
                # 主图 345 + 四条 (345 - 280)，没有填满固定画布。
                self.assertEqual(rendered.size, (640, 605))

    def test_scripted_crop_does_not_stretch_hero_back_to_source_height(self):
        frame = Image.new("RGB", (1280, 720), "black")
        ImageDraw.Draw(frame).ellipse((100, 100, 300, 300), fill="white")
        lines = [{"t": index, "text": f"Line {index}"} for index in range(5)]
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            MODULE, "grab_frame", return_value=frame
        ), mock.patch.object(MODULE, "draw_scripted_subtitle") as draw_text:
            out = Path(tmp) / "script.jpg"
            MODULE.scripted_render_one("unused", lines, out, (3, 4), None,
                                       0.88, None, None, None,
                                       layout="natural", frame_bottom=0.72)
            with Image.open(out) as rendered:
                self.assertEqual(rendered.size, (1280, 806))
                bounds = rendered.crop((0, 0, 1280, 518)).convert("L").point(
                    lambda p: 255 if p > 127 else 0
                ).getbbox()
                self.assertEqual(bounds[2] - bounds[0], bounds[3] - bounds[1])
            self.assertEqual([call.args[1] for call in draw_text.call_args_list],
                             [line["text"] for line in lines])

    def test_cli_rejects_conflicting_layout_and_invalid_crop_before_io(self):
        for options, message in [
            (["--layout", "natural", "--aspect", "3:4"], "不接受"),
            (["--layout", "natural", "--hero-fraction", "0.7"], "不接受"),
            (["--frame-top", "0.8", "--frame-bottom", "0.2"], "裁切必须满足"),
        ]:
            with self.subTest(options=options):
                proc = subprocess.run(
                    [sys.executable, str(SCRIPT), "render-script", "unused.mp4",
                     "--script", "unused.json", "--out", "unused.jpg", *options],
                    capture_output=True, encoding="utf-8", errors="replace",
                )
                self.assertNotEqual(proc.returncode, 0)
                self.assertIn(message, proc.stderr)
                self.assertNotIn("Traceback", proc.stderr)

    def test_cli_rejects_invalid_native_fit_options_before_io(self):
        for options, message in [
            (["--layout", "natural", "--fit", "crop"], "不接受 --fit"),
            (["--layout", "natural", "--crop-center", "0.4"], "不接受 --fit"),
            (["--crop-center", "1.5"], "0–1"),
            (["--fit", "pad", "--crop-center", "0.4"], "只用于 --fit crop"),
        ]:
            with self.subTest(options=options):
                proc = subprocess.run(
                    [sys.executable, str(SCRIPT), "render", "unused.mp4",
                     "--manifest", "unused.json", "--out-dir", "unused", *options],
                    capture_output=True, encoding="utf-8", errors="replace",
                )
                self.assertNotEqual(proc.returncode, 0)
                self.assertIn(message, proc.stderr)
                self.assertNotIn("Traceback", proc.stderr)


class BreathingGapTests(unittest.TestCase):
    def render_native(self, **options):
        frame = Image.new("RGB", (640, 360), "#336699")
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            MODULE, "grab_frame", return_value=frame
        ):
            out = Path(tmp) / "native.jpg"
            MODULE.render_one("unused", [0, 1, 2, 3, 4], out, (3, 4), None,
                              0.78, 0.96, None, layout="natural", **options)
            with Image.open(out) as rendered:
                return rendered.convert("RGB")

    def test_native_defaults_unchanged(self):
        self.assertEqual(self.render_native().size, (640, 605))

    def test_native_gap_and_divider_insert_background_rows(self):
        rendered = self.render_native(strip_gap=4, hero_divider="line")
        # 四条字幕条之间 3 个缝隙 + 1 条 2px 分隔线。
        self.assertEqual(rendered.size, (640, 605 + 3 * 4 + 2))
        self.assertEqual(rendered.getpixel((320, 345 + 1)), (96, 96, 96))
        self.assertLess(max(rendered.getpixel((320, 345 + 2 + 65 + 1))), 8)

    def test_stack_parts_keeps_part_pixels_and_fills_gaps_with_background(self):
        parts = [Image.new("RGB", (20, 10), color) for color in ("red", "green", "blue")]
        stacked = MODULE.stack_parts(parts, MODULE.layout_gaps(2, 3, "line"))
        self.assertEqual(stacked.size, (20, 30 + 2 + 3))
        self.assertEqual(stacked.getpixel((5, 5)), (255, 0, 0))
        self.assertEqual(stacked.getpixel((5, 10)), MODULE.DIVIDER_COLOR)
        self.assertEqual(stacked.getpixel((5, 12 + 5)), (0, 128, 0))
        self.assertEqual(stacked.getpixel((5, 22 + 1)), (0, 0, 0))
        self.assertEqual(stacked.getpixel((5, 25 + 5)), (0, 0, 255))

    def test_scripted_fixed_gap_keeps_canvas_size(self):
        frame = Image.new("RGB", (1280, 720), "#336699")
        lines = [{"t": i, "text": f"Line {i}"} for i in range(5)]
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            MODULE, "grab_frame", return_value=frame
        ), mock.patch.object(MODULE, "draw_scripted_subtitle"):
            out = Path(tmp) / "script.jpg"
            MODULE.scripted_render_one("unused", lines, out, (3, 4), 600,
                                       0.88, None, None, None,
                                       strip_gap=4, hero_divider="line")
            with Image.open(out) as rendered:
                self.assertEqual(rendered.size, (600, 800))

    def test_cli_rejects_invalid_gap_options_before_io(self):
        for command, options, message in [
            ("render", ["--strip-gap", "9"], "--strip-gap"),
            ("render", ["--strip-gap", "-1"], "--strip-gap"),
            ("render-script", ["--six-line-card", "--strip-gap", "2"], "固定几何"),
            ("render-script", ["--six-line-card", "--hero-divider", "line"], "固定几何"),
        ]:
            with self.subTest(options=options):
                extra = (["--manifest", "unused.json", "--out-dir", "unused"]
                         if command == "render"
                         else ["--script", "unused.json", "--out", "unused.jpg"])
                proc = subprocess.run(
                    [sys.executable, str(SCRIPT), command, "unused.mp4", *extra, *options],
                    capture_output=True, encoding="utf-8", errors="replace",
                )
                self.assertNotEqual(proc.returncode, 0)
                self.assertIn(message, proc.stderr)
                self.assertNotIn("Traceback", proc.stderr)


class SixLineCardTests(unittest.TestCase):
    def test_geometry_and_rendered_strips(self):
        self.assertEqual(MODULE.six_line_geometry(1080, 1440), (870, 114, 870 / 1440))
        colors = [(30 + i * 25, 50 + i * 20, 70 + i * 15) for i in range(6)]
        frames = [Image.new("RGB", (1080, 870), color) for color in colors]
        lines = [{"t": i, "text": f"Line {i}"} for i in range(6)]
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            MODULE, "grab_frame", side_effect=frames
        ), mock.patch.object(MODULE, "draw_scripted_subtitle") as draw_text:
            out = Path(tmp) / "six-line.jpg"
            MODULE.scripted_render_one(
                "unused", lines, out, (3, 4), 1080, 0.60, None, None, None,
                six_line_card=True,
            )
            calls = draw_text.call_args_list
            self.assertEqual(len(calls), 6)
            self.assertEqual(calls[0].args[0].size, (1080, 870))
            self.assertTrue(all(call.args[0].size == (1080, 114) for call in calls[1:]))
            centers = [calls[0].args[2]] + [
                870 + i * 114 + call.args[2]
                for i, call in enumerate(calls[1:])
            ]
            self.assertEqual(centers, [813, 927, 1041, 1155, 1269, 1383])
            self.assertTrue(all(call.args[4] == 63 for call in calls))
            with Image.open(out) as rendered:
                self.assertEqual(rendered.size, (1080, 1440))
                # Distinct solid-color frames fill every row, including each seam.
                for i, y in enumerate((869, 870, 983, 984, 1097, 1098, 1211, 1212, 1325, 1326, 1439)):
                    expected = colors[0 if y < 870 else 1 + (y - 870) // 114]
                    actual = rendered.getpixel((540, y))
                    self.assertTrue(all(abs(a - e) <= 8 for a, e in zip(actual, expected)),
                                    (i, y, actual, expected))

    def test_invalid_cli_combinations_fail_before_video_io(self):
        for options, message in [
            (["--layout", "natural"], "只支持固定 3:4"),
            (["--hero-fraction", "0.6"], "不接受 --hero-fraction"),
            (["--aspect", "16:9"], "只支持固定 3:4"),
        ]:
            with self.subTest(options=options):
                proc = subprocess.run(
                    [sys.executable, str(SCRIPT), "render-script", "unused.mp4",
                     "--script", "unused.json", "--out", "unused.jpg",
                     "--six-line-card", *options],
                    capture_output=True, encoding="utf-8", errors="replace",
                )
                self.assertNotEqual(proc.returncode, 0)
                self.assertIn(message, proc.stderr)
                self.assertNotIn("Traceback", proc.stderr)

    def test_requires_exactly_six_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "unused.mp4"
            video.touch()
            script = Path(tmp) / "five.json"
            script.write_text(json.dumps({"lines": [
                {"t": i, "text": f"Line {i}"} for i in range(5)
            ]}), encoding="utf-8")
            args = mock.Mock(
                video=str(video), script=str(script), six_line_card=True,
                speaker_prefix="none", emphasize_line=None,
            )
            with mock.patch.object(MODULE, "video_metadata", return_value=(1080, 870, 10)):
                with self.assertRaisesRegex(SystemExit, "恰好 6 句"):
                    MODULE.command_render_script(args)

    def test_long_line_shrinks_before_reaching_safe_width(self):
        class MeasuredDraw:
            rendered = None

            def textbbox(self, position, text, font, stroke_width):
                return (0, 0, round(len(text) * font * 0.62) + 2 * stroke_width, font)

            def text(self, position, text, font, **kwargs):
                self.rendered = (position, text, font, kwargs)

        measured = MeasuredDraw()
        image = Image.new("RGB", (1080, 114), "white")
        with mock.patch.object(MODULE.ImageDraw, "Draw", return_value=measured), mock.patch.object(
            MODULE, "load_subtitle_font", side_effect=lambda path, size, text: size
        ):
            MODULE.draw_scripted_subtitle(image, "M" * 28, 57, None, 63, round(1080 * 0.92))
        position, text, chosen_size, kwargs = measured.rendered
        stroke = kwargs["stroke_width"]
        width = measured.textbbox((0, 0), text, chosen_size, stroke)[2]
        self.assertLess(chosen_size, 63)
        self.assertLessEqual(width, round(1080 * 0.92))
        self.assertGreaterEqual(position[0], 0)
        self.assertLessEqual(position[0] + width, image.width)
        self.assertGreaterEqual(position[1], 0)
        self.assertLessEqual(position[1] + chosen_size, image.height)


def subtitle_band(width, height, left, right, background="#5a5a5a"):
    """灰底上画白色黑描边的竖笔画，模拟烧录字幕。"""
    band = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(band)
    for x in range(left, right - 3, 9):
        draw.rectangle((x, height * 0.3, x + 3, height * 0.7), fill="white",
                       outline="black", width=1)
    return band


class SpeakerPrefixTests(unittest.TestCase):
    LINES = {"lines": [
        {"t": 1, "text": "Question one", "speaker": "Host"},
        {"t": 2, "text": "Question two", "speaker": "Host"},
        {"t": 3, "text": "Answer one", "speaker": "Guest"},
        {"t": 4, "text": "Answer two", "speaker": "Guest"},
        {"t": 5, "text": "Back to you", "speaker": "Host"},
    ]}

    def prefixes(self, mode):
        lines = MODULE.normalize_script_lines(self.LINES, 10, mode)
        return [line["prefix"] for line in MODULE.apply_speaker_prefix(lines, mode)]

    def test_modes_choose_which_lines_show_prefix(self):
        self.assertEqual(self.prefixes("none"), [None] * 5)
        self.assertEqual(
            self.prefixes("on-change"), ["Host", None, "Guest", None, "Host"]
        )
        self.assertEqual(
            self.prefixes("every"), ["Host", "Host", "Guest", "Guest", "Host"]
        )

    def test_speaker_stays_out_of_text(self):
        lines = MODULE.normalize_script_lines(self.LINES, 10, "every")
        self.assertEqual(lines[0]["text"], "Question one")
        self.assertEqual(lines[0]["speaker"], "Host")

    def test_prefix_modes_require_speaker_on_every_line(self):
        data = {"lines": [{"t": 1, "text": "a", "speaker": "Host"}, {"t": 2, "text": "b"}]}
        self.assertEqual(len(MODULE.normalize_script_lines(data, 10, "none")), 2)
        for mode in ("on-change", "every"):
            with self.assertRaisesRegex(SystemExit, r"lines\[1\] 缺少 speaker"):
                MODULE.normalize_script_lines(data, 10, mode)

    def test_invalid_speaker_values_are_rejected(self):
        for bad in ("", "  ", 3, "A\nB"):
            data = {"lines": [{"t": 1, "text": "a", "speaker": bad}, {"t": 2, "text": "b"}]}
            with self.assertRaises(SystemExit):
                MODULE.normalize_script_lines(data, 10)

    def test_label_separator_follows_script(self):
        self.assertEqual(MODULE.speaker_label("主持人", "你好"), "主持人：")
        self.assertEqual(MODULE.speaker_label("Host", "Hello"), "Host: ")

    def test_prefix_is_drawn_in_accent_color_left_of_text(self):
        plain = Image.new("RGB", (900, 120), "#404040")
        prefixed = plain.copy()
        MODULE.draw_scripted_subtitle(plain, "Hello world", 60, None, 48, 820)
        MODULE.draw_scripted_subtitle(
            prefixed, "Hello world", 60, None, 48, 820, speaker="Host"
        )
        accent = [
            x for x in range(prefixed.width) for y in range(prefixed.height)
            if prefixed.getpixel((x, y)) == MODULE.SPEAKER_PREFIX_FILL
        ]
        white = [
            x for x in range(prefixed.width) for y in range(prefixed.height)
            if prefixed.getpixel((x, y)) == (255, 255, 255)
        ]
        self.assertTrue(accent, "前缀应使用强调色")
        self.assertLess(max(accent), min(white), "前缀应在台词左侧")
        plain_white = [
            x for x in range(plain.width) for y in range(plain.height)
            if plain.getpixel((x, y)) == (255, 255, 255)
        ]
        # 放得下时，前缀不让台词缩小：白字宽度不变。
        self.assertEqual(
            max(white) - min(white), max(plain_white) - min(plain_white)
        )

    def test_prefixed_line_stays_inside_safe_width(self):
        image = Image.new("RGB", (600, 100), "#404040")
        MODULE.draw_scripted_subtitle(
            image, "M" * 12, 50, None, 48, 552, speaker="Speaker"
        )
        lit = [
            x for x in range(image.width) for y in range(image.height)
            if image.getpixel((x, y)) != (64, 64, 64)
        ]
        self.assertGreaterEqual(min(lit), 0)
        self.assertLessEqual(max(lit) - min(lit), 552)


class EmphasisTests(unittest.TestCase):
    def lit(self, image, color):
        return [
            (x, y) for x in range(image.width) for y in range(image.height)
            if image.getpixel((x, y)) == color
        ]

    def test_default_output_is_unchanged(self):
        a = Image.new("RGB", (900, 120), "#404040")
        b = a.copy()
        MODULE.draw_scripted_subtitle(a, "Hello world", 60, None, 48, 820)
        MODULE.draw_scripted_subtitle(b, "Hello world", 60, None, 48, 820, emphasis=False)
        self.assertEqual(a.tobytes(), b.tobytes())
        self.assertFalse(self.lit(a, MODULE.EMPHASIS_FILL))

    def test_emphasis_uses_warm_fill_and_backing_plate(self):
        image = Image.new("RGB", (900, 120), "#808080")
        MODULE.draw_scripted_subtitle(
            image, "Hello world", 60, None, 48, 820, emphasis=True
        )
        self.assertTrue(self.lit(image, MODULE.EMPHASIS_FILL))
        self.assertFalse(self.lit(image, (255, 255, 255)))
        # 底衬把文字周围的灰底按固定透明度压暗，成片出现同一个压暗色。
        alpha = MODULE.EMPHASIS_PLATE_ALPHA
        plate = round(128 * (255 - alpha) / 255)
        self.assertGreater(len(self.lit(image, (plate,) * 3)), 1000)

    def test_emphasis_plate_does_not_dim_speaker_prefix(self):
        image = Image.new("RGB", (900, 120), "#808080")
        MODULE.draw_scripted_subtitle(
            image, "Hello world", 60, None, 48, 820, speaker="Host", emphasis=True
        )
        # 前缀画在底衬之上，仍保持原本的强调色。
        self.assertTrue(self.lit(image, MODULE.SPEAKER_PREFIX_FILL))
        self.assertTrue(self.lit(image, MODULE.EMPHASIS_FILL))

    def test_apply_emphasis_targets(self):
        lines = [{"t": i, "text": str(i)} for i in range(4)]
        MODULE.apply_emphasis(lines, None)
        self.assertFalse(any("emphasis" in line for line in lines))
        MODULE.apply_emphasis(lines, "last")
        self.assertEqual([line.get("emphasis") for line in lines], [None, None, None, True])
        lines = [{"t": i, "text": str(i)} for i in range(4)]
        MODULE.apply_emphasis(lines, 2)
        self.assertEqual([line.get("emphasis") for line in lines], [None, True, None, None])

    def test_out_of_range_line_is_rejected(self):
        lines = [{"t": i, "text": str(i)} for i in range(3)]
        for bad in (4, 99):
            with self.assertRaisesRegex(SystemExit, "超出范围"):
                MODULE.apply_emphasis(lines, bad)

    def test_json_emphasis_must_be_boolean(self):
        data = {"lines": [{"t": 1, "text": "a", "emphasis": True}, {"t": 2, "text": "b"}]}
        lines = MODULE.normalize_script_lines(data, 10)
        self.assertTrue(lines[0]["emphasis"])
        data["lines"][1]["emphasis"] = "yes"
        with self.assertRaisesRegex(SystemExit, "emphasis 必须是"):
            MODULE.normalize_script_lines(data, 10)

    def test_six_line_card_passes_emphasis_only_to_target(self):
        frames = [Image.new("RGB", (1080, 870), "#303030") for _ in range(6)]
        lines = [{"t": i, "text": f"Line {i}"} for i in range(6)]
        MODULE.apply_emphasis(lines, "last")
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            MODULE, "grab_frame", side_effect=frames
        ), mock.patch.object(MODULE, "draw_scripted_subtitle") as draw_text:
            MODULE.scripted_render_one(
                "unused", lines, Path(tmp) / "o.jpg", (3, 4), 1080, 0.60, None,
                None, None, six_line_card=True,
            )
        flags = [call.kwargs["emphasis"] for call in draw_text.call_args_list]
        self.assertEqual(flags, [False] * 5 + [True])

    def test_cli_rejects_bad_value_before_video_io(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "render-script", "unused.mp4",
             "--script", "unused.json", "--out", "unused.jpg",
             "--emphasize-line", "0"],
            capture_output=True, encoding="utf-8", errors="replace",
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertNotIn("Traceback", proc.stderr)

    def test_native_render_has_no_emphasis_option(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "render", "unused.mp4",
             "--manifest", "m.json", "--out-dir", "o", "--emphasize-line", "last"],
            capture_output=True, encoding="utf-8", errors="replace",
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("unrecognized arguments", proc.stderr)


class SideCropTests(unittest.TestCase):
    def assertSubtitlesInside(self, canvas):
        """白色笔画的左右边界都不能贴到画布边缘，否则说明字被裁了。"""
        bright = canvas.convert("L").point(lambda p: 255 if p > 200 else 0)
        bounds = bright.getbbox()
        self.assertIsNotNone(bounds)
        self.assertGreater(bounds[0], 0)
        self.assertLess(bounds[2], canvas.width)

    def test_subtitle_extent_finds_text_and_ignores_plain_band(self):
        extent = MODULE.subtitle_extent(subtitle_band(640, 40, 200, 440))
        self.assertIsNotNone(extent)
        self.assertLessEqual(abs(extent[0] - 200), 3)
        self.assertLessEqual(abs(extent[1] - 436), 6)
        self.assertIsNone(MODULE.subtitle_extent(Image.new("RGB", (640, 40), "#5a5a5a")))

    def stack_with_subtitles(self, left, right, strips=4):
        hero = Image.new("RGB", (640, 300), "#336699")
        hero.paste(subtitle_band(640, 40, left, right), (0, 260))
        bands = [subtitle_band(640, 40, left, right) for _ in range(strips)]
        stack = MODULE.stack_parts([hero, *bands])
        extents = [MODULE.subtitle_extent(b) for b in [hero.crop((0, 260, 640, 300)), *bands]]
        return stack, extents

    def test_narrow_subtitles_fill_canvas_without_black_bars(self):
        stack, extents = self.stack_with_subtitles(260, 380)
        canvas, note = MODULE.fit_fixed_canvas(stack, extents, (300, 400))
        self.assertEqual(canvas.size, (300, 400))
        self.assertIn("无黑边", note)
        for y in (2, 397):
            self.assertGreater(max(canvas.getpixel((150, y))), 40)

    def test_wide_subtitles_limit_crop_and_keep_text(self):
        stack, extents = self.stack_with_subtitles(60, 580)
        canvas, note = MODULE.fit_fixed_canvas(stack, extents, (300, 400))
        self.assertIn("只裁去", note)
        padded = ImageOps.pad(stack, (300, 400), color="black")
        # 裁得比留边版少黑边，但所有字幕边界都在画布内。
        self.assertLess(canvas.convert("L").getbbox()[1], padded.convert("L").getbbox()[1])
        self.assertSubtitlesInside(canvas)

    def test_unknown_subtitle_or_pad_mode_falls_back_to_padding(self):
        stack, extents = self.stack_with_subtitles(260, 380)
        expected = ImageOps.pad(stack, (300, 400), method=Image.Resampling.LANCZOS, color="black")
        for fit, items, message in [
            ("crop", [extents[0], None, *extents[2:]], "第 2 句"),
            ("pad", extents, "--fit pad"),
        ]:
            with self.subTest(fit=fit):
                canvas, note = MODULE.fit_fixed_canvas(stack, items, (300, 400), fit)
                self.assertIn(message, note)
                self.assertEqual(canvas.tobytes(), expected.tobytes())

    def test_crop_center_moves_window_but_never_cuts_subtitles(self):
        hero = Image.new("RGB", (640, 300), "#336699")
        ImageDraw.Draw(hero).rectangle((0, 0, 100, 259), fill="#ff0000")
        stack = MODULE.stack_parts([hero, *[subtitle_band(640, 40, 260, 380)] * 4])
        extents = [(260, 380)] * 5
        left, _ = MODULE.fit_fixed_canvas(stack, extents, (300, 400), crop_center=0.0)
        centered, _ = MODULE.fit_fixed_canvas(stack, extents, (300, 400), crop_center=0.5)
        # 期望窗口靠左时会尽量左移，但仍须容纳字幕左右安全边界。
        self.assertLess(left.getpixel((5, 100))[2], centered.getpixel((5, 100))[2])
        self.assertSubtitlesInside(left)


class DuplicateFrameTests(unittest.TestCase):
    @staticmethod
    def frame(offset):
        image = Image.new("RGB", (320, 180), (40, 40, 40))
        ImageDraw.Draw(image).rectangle((offset, 40, offset + 60, 120), fill=(230, 200, 60))
        return image

    def test_identical_frames_are_rejected(self):
        frames = [self.frame(20)] * 4
        with self.assertRaises(SystemExit) as raised:
            MODULE.ensure_distinct_frames(frames, [1, 2, 3, 4])
        self.assertIn("静态封面", str(raised.exception))

    def test_moving_frames_pass(self):
        frames = [self.frame(20 + 50 * index) for index in range(4)]
        MODULE.ensure_distinct_frames(frames, [1, 2, 3, 4])

    def test_repeated_native_subtitle_band_is_rejected(self):
        frames = [self.frame(20 + 50 * index) for index in range(3)]
        bands = [self.frame(20), self.frame(120), self.frame(120)]
        with self.assertRaises(SystemExit) as raised:
            MODULE.ensure_distinct_frames(frames, [1, 2, 3], bands)
        self.assertIn("2.00s 与 3.00s", str(raised.exception))

    def test_cli_stops_on_static_video_unless_allowed(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            video = tmp_path / "static.mp4"
            subprocess.run(
                [
                    MODULE.FFMPEG, "-hide_banner", "-loglevel", "error", "-y",
                    "-f", "lavfi", "-i", "color=c=gray:size=640x360:rate=10",
                    "-t", "3", "-c:v", "mpeg4", "-pix_fmt", "yuv420p", str(video),
                ],
                check=True,
                capture_output=True,
            )
            manifest = tmp_path / "manifest.json"
            manifest.write_text(
                json.dumps({"images": [{"title": "static", "times": [0.5, 1.5, 2.5]}]}),
                encoding="utf-8",
            )
            command = [
                sys.executable, str(SCRIPT), "render", str(video),
                "--manifest", str(manifest), "--out-dir", str(tmp_path / "out"),
            ]
            blocked = subprocess.run(command, capture_output=True, encoding="utf-8", errors="replace")
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("静态封面", blocked.stderr)
            self.assertFalse((tmp_path / "out" / "01_static.jpg").exists())

            allowed = subprocess.run(
                [*command, "--allow-duplicate-frames"], capture_output=True, encoding="utf-8", errors="replace"
            )
            self.assertEqual(allowed.returncode, 0, allowed.stderr)
            self.assertTrue((tmp_path / "out" / "01_static.jpg").is_file())


class CheckSourceTests(unittest.TestCase):
    @staticmethod
    def make_video(path, size, seconds=3):
        subprocess.run(
            [
                MODULE.FFMPEG, "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", f"testsrc2=size={size}:rate=10",
                "-t", str(seconds), "-c:v", "mpeg4", "-pix_fmt", "yuv420p",
                str(path),
            ],
            check=True,
            capture_output=True,
        )

    @staticmethod
    def check(video, *extra):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "check-source", str(video), *extra],
            capture_output=True,
            encoding="utf-8", errors="replace",
        )

    def test_clean_hd_source_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "hd.mkv"
            self.make_video(video, "1280x720")
            proc = self.check(video, "--min-height", "720")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("自检通过", proc.stdout)
            self.assertNotIn("警告", proc.stderr)

    def test_low_resolution_warns_without_failing(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "low.mkv"
            self.make_video(video, "640x360")
            proc = self.check(video)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("警告", proc.stderr)

    def test_min_height_fails_low_resolution(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "low.mkv"
            self.make_video(video, "640x360")
            proc = self.check(video, "--min-height", "720")
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("低于 --min-height 720", proc.stderr)

    def test_corrupt_stream_fails(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "bad.mkv"
            self.make_video(video, "1280x720")
            data = bytearray(video.read_bytes())
            start = len(data) // 3
            for index in range(start, start + 4000):
                data[index] = (data[index] * 7 + 13) % 256
            video.write_bytes(bytes(data))
            proc = self.check(video, "--seconds", "3")
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("解码前 3 秒出现错误", proc.stderr)

    def test_unreadable_file_fails_cleanly(self):
        with tempfile.TemporaryDirectory() as tmp:
            video = Path(tmp) / "junk.mp4"
            video.write_bytes(b"not a video")
            proc = self.check(video)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("源视频自检失败", proc.stderr)
            self.assertNotIn("Traceback", proc.stderr)


class CliIntegrationTests(unittest.TestCase):
    def test_sample_band_and_render_with_synthetic_video(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            video = tmp_path / "synthetic.mp4"
            subprocess.run(
                [
                    MODULE.FFMPEG,
                    "-hide_banner",
                    "-loglevel",
                    "error",
                    "-y",
                    "-f",
                    "lavfi",
                    "-i",
                    "testsrc2=size=640x360:rate=10",
                    "-t",
                    "3",
                    "-c:v",
                    "mpeg4",
                    "-pix_fmt",
                    "yuv420p",
                    str(video),
                ],
                check=True,
                capture_output=True,
            )

            sample = tmp_path / "candidate.jpg"
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "sample",
                    str(video),
                    "--start",
                    "0.5",
                    "--end",
                    "2.5",
                    "--interval",
                    "1",
                    "--out",
                    str(sample),
                ],
                check=True,
                capture_output=True,
                encoding="utf-8", errors="replace",
            )
            self.assertTrue(sample.is_file())

            default_sample = tmp_path / "default-candidate.jpg"
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "sample",
                    str(video),
                    "--out",
                    str(default_sample),
                ],
                check=True,
                capture_output=True,
                encoding="utf-8", errors="replace",
            )
            self.assertTrue(default_sample.is_file())

            focused_sample = tmp_path / "focused-candidate.jpg"
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "sample",
                    str(video),
                    "-t",
                    "1",
                    "-t",
                    "2",
                    "--around",
                    "0.2",
                    "--out",
                    str(focused_sample),
                ],
                check=True,
                capture_output=True,
                encoding="utf-8", errors="replace",
            )
            self.assertTrue(focused_sample.is_file())

            band = tmp_path / "band.jpg"
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "band",
                    str(video),
                    "-t",
                    "1",
                    "--out",
                    str(band),
                ],
                check=True,
                capture_output=True,
                encoding="utf-8", errors="replace",
            )
            self.assertTrue(band.is_file())

            manifest = tmp_path / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {"images": [{"title": "合成测试", "times": [0.5, 1, 1.5, 2, 2.5]}]},
                    ensure_ascii=False,
                ),
                encoding="utf-8",
            )
            out_dir = tmp_path / "output"
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "render",
                    str(video),
                    "--manifest",
                    str(manifest),
                    "--out-dir",
                    str(out_dir),
                    "--width",
                    "300",
                ],
                check=True,
                capture_output=True,
                encoding="utf-8", errors="replace",
            )
            output = out_dir / "01_合成测试.jpg"
            self.assertTrue(output.is_file())
            self.assertTrue((out_dir / "final_contact_sheet.jpg").is_file())
            self.assertTrue((out_dir / "原生字幕时间点.json").is_file())
            with Image.open(output) as rendered:
                self.assertEqual(rendered.size, (300, 284))

            script = tmp_path / "script.json"
            script.write_text(
                json.dumps(
                    {
                        "lines": [
                            {"t": 0.5, "text": "First point"},
                            {"t": 1.0, "text": "Second point"},
                            {"t": 1.5, "text": "Third point"},
                            {"t": 2.0, "text": "Fourth point"},
                            {"t": 2.5, "text": "Fifth point"},
                        ]
                    }
                ),
                encoding="utf-8",
            )
            scripted_output = tmp_path / "scripted.jpg"
            subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "render-script",
                    str(video),
                    "--script",
                    str(script),
                    "--out",
                    str(scripted_output),
                    "--width",
                    "300",
                    "--font-size",
                    "18",
                ],
                check=True,
                capture_output=True,
                encoding="utf-8", errors="replace",
            )
            with Image.open(scripted_output) as rendered:
                self.assertEqual(rendered.size, (300, 400))

            for command, inputs, expected in [
                ("render", ["--manifest", str(manifest), "--out-dir", str(tmp_path / "natural")], (640, 605)),
                ("render-script", ["--script", str(script), "--out", str(tmp_path / "natural-script.jpg"),
                                   "--frame-bottom", "0.72"], (640, 403)),
            ]:
                subprocess.run(
                    [sys.executable, str(SCRIPT), command, str(video), *inputs, "--layout", "natural"],
                    check=True, capture_output=True, encoding="utf-8", errors="replace",
                )
                natural_path = (tmp_path / "natural" / "01_合成测试.jpg" if command == "render"
                                else tmp_path / "natural-script.jpg")
                with Image.open(natural_path) as rendered:
                    self.assertEqual(rendered.size, expected)

            fixed_dir = tmp_path / "explicit-fixed"
            subprocess.run(
                [sys.executable, str(SCRIPT), "render", str(video),
                 "--manifest", str(manifest), "--out-dir", str(fixed_dir),
                 "--aspect", "3:4", "--width", "300"],
                check=True, capture_output=True, encoding="utf-8", errors="replace",
            )
            with Image.open(fixed_dir / "01_合成测试.jpg") as rendered:
                self.assertEqual(rendered.size, (300, 400))

            repeated = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPT),
                    "render",
                    str(video),
                    "--manifest",
                    str(manifest),
                    "--out-dir",
                    str(out_dir),
                    "--width",
                    "300",
                ],
                capture_output=True,
                encoding="utf-8", errors="replace",
            )
            self.assertNotEqual(repeated.returncode, 0)
            self.assertIn("--overwrite", repeated.stderr)


def _patterned_frame(size=(640, 360)):
    frame = Image.new("RGB", size, "#224466")
    draw = ImageDraw.Draw(frame)
    for step in range(0, size[0], 40):
        draw.rectangle((step, 0, step + 19, size[1]), fill="#88aa33")
    draw.ellipse((200, 60, 440, 260), fill="white")
    return frame


class HeroZoomTests(unittest.TestCase):
    def render_native(self, name, **kwargs):
        frame = _patterned_frame()
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            MODULE, "grab_frame", return_value=frame
        ):
            out = Path(tmp) / name
            MODULE.render_one("unused", [0, 1, 2, 3, 4], out, (3, 4), None,
                              0.78, 0.96, None, layout="natural",
                              check_duplicates=False, **kwargs)
            with Image.open(out) as image:
                return image.convert("RGB")

    def test_parse_accepts_list_and_boundaries(self):
        self.assertEqual(MODULE.parse_hero_zoom("1.0, 0.9,0.8"), [1.0, 0.9, 0.8])

    def test_parse_rejects_bad_values_in_chinese(self):
        for text in ("0.79", "1.01", "abc", "1.0,,0.9", "", "nan"):
            with self.subTest(text=text), self.assertRaises(SystemExit) as ctx:
                MODULE.parse_hero_zoom(text)
            self.assertIn("--hero-zoom", str(ctx.exception))

    def test_zoom_cycles_per_card(self):
        zooms = [1.0, 0.9, 0.95]
        picked = [MODULE.hero_zoom_for_card(zooms, i) for i in range(5)]
        self.assertEqual(picked, [1.0, 0.9, 0.95, 1.0, 0.9])
        self.assertEqual(MODULE.hero_zoom_for_card(None, 3), 1.0)

    def test_command_render_passes_cycled_zoom(self):
        seen = []

        def fake_render(video, times, out_path, *rest, **kwargs):
            seen.append(kwargs["hero_zoom"])
            Image.new("RGB", (20, 20), "red").save(out_path)

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "v.mp4").touch()
            (root / "m.json").write_text(json.dumps({"images": [
                {"title": f"卡{i}", "times": [1, 2]} for i in range(4)
            ]}), encoding="utf-8")
            args = mock.Mock(
                video=str(root / "v.mp4"), manifest=str(root / "m.json"),
                out_dir=str(root / "out"), aspect=None, width=None,
                band_top=0.78, band_bottom=0.96, hero_fraction=None,
                layout="natural", fit=None, crop_center=None,
                allow_duplicate_frames=False, overwrite=False,
                keep_going=False, resume=False, hero_zoom=[1.0, 0.9, 0.95],
            )
            with mock.patch.object(MODULE, "video_metadata", return_value=(640, 360, 10)), \
                    mock.patch.object(MODULE, "render_one", side_effect=fake_render):
                MODULE.command_render(args)
        self.assertEqual(seen, [1.0, 0.9, 0.95, 1.0])

    def test_disabled_or_full_zoom_is_pixel_identical(self):
        base = self.render_native("base.png")
        full = self.render_native("full.png", hero_zoom=1.0)
        self.assertEqual(base.tobytes(), full.tobytes())

    def test_native_zoom_keeps_size_and_subtitle_strips(self):
        base = self.render_native("base.png")
        zoomed = self.render_native("zoom.png", hero_zoom=0.8)
        self.assertEqual(zoomed.size, base.size)
        self.assertNotEqual(zoomed.tobytes(), base.tobytes())
        # 主图底部的第一条原生字幕条（280–345）与后四条都不得变化。
        self.assertEqual(
            zoomed.crop((0, 280, 640, base.height)).tobytes(),
            base.crop((0, 280, 640, base.height)).tobytes(),
        )

    def test_native_zoom_in_fixed_layout_keeps_canvas_size(self):
        frame = _patterned_frame()
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
            MODULE, "grab_frame", return_value=frame
        ):
            out = Path(tmp) / "fixed.png"
            MODULE.render_one("unused", [0, 1, 2, 3, 4], out, (3, 4), 300,
                              0.78, 0.96, None, layout="fixed", hero_zoom=0.85)
            with Image.open(out) as image:
                self.assertEqual(image.size, (300, 400))

    def test_scripted_zoom_only_changes_hero(self):
        frame = _patterned_frame((1280, 720))
        lines = [{"t": index, "text": f"Line {index}"} for index in range(6)]

        def render(**kwargs):
            with tempfile.TemporaryDirectory() as tmp, mock.patch.object(
                MODULE, "grab_frame", return_value=frame
            ), mock.patch.object(MODULE, "draw_scripted_subtitle"):
                out = Path(tmp) / "s.png"
                MODULE.scripted_render_one(
                    "unused", lines, out, (3, 4), 1080, 0.60, None, None, None,
                    layout="fixed", six_line_card=True, **kwargs)
                with Image.open(out) as image:
                    return image.convert("RGB")

        base, zoomed = render(), render(hero_zoom=0.8)
        self.assertEqual(zoomed.size, (1080, 1440))
        hero_h = 1440 - 5 * 114
        self.assertNotEqual(
            zoomed.crop((0, 0, 1080, hero_h)).tobytes(),
            base.crop((0, 0, 1080, hero_h)).tobytes(),
        )
        self.assertEqual(
            zoomed.crop((0, hero_h, 1080, 1440)).tobytes(),
            base.crop((0, hero_h, 1080, 1440)).tobytes(),
        )

    def test_cli_rejects_out_of_range_zoom(self):
        proc = subprocess.run(
            [sys.executable, str(SCRIPT), "render-script", "v.mp4",
             "--script", "s.json", "--out", "o.jpg", "--hero-zoom", "0.5"],
            capture_output=True, encoding="utf-8", errors="replace", check=False,
        )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("0.8", proc.stderr)


class KeepGoingResumeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.video = root / "v.mp4"
        self.video.touch()
        self.manifest = root / "m.json"
        self.manifest.write_text(json.dumps({"images": [
            {"title": "甲", "times": [1, 2]},
            {"title": "乙", "times": [3, 4]},
            {"title": "丙", "times": [5, 6]},
        ]}), encoding="utf-8")
        self.out_dir = root / "out"

    def run_render(self, fail_titles=(), **flags):
        args = mock.Mock(
            video=str(self.video), manifest=str(self.manifest),
            out_dir=str(self.out_dir), aspect=None, width=None, band_top=0.78,
            band_bottom=0.96, hero_fraction=None, layout="natural", fit=None,
            crop_center=None, allow_duplicate_frames=False, overwrite=False,
            keep_going=False, resume=False, hero_zoom=None,
        )
        for key, value in flags.items():
            setattr(args, key, value)
        rendered = []

        def fake_render(video, times, out_path, *rest, **kwargs):
            if Path(out_path).stem.split("_", 1)[1] in fail_titles:
                raise RuntimeError("抽帧失败")
            Image.new("RGB", (20, 20), "red").save(out_path)
            rendered.append(Path(out_path).name)

        with mock.patch.object(MODULE, "video_metadata", return_value=(640, 360, 10)), \
                mock.patch.object(MODULE, "render_one", side_effect=fake_render):
            try:
                MODULE.command_render(args)
                code = 0
            except SystemExit as exc:
                code = exc.code
        return code, rendered

    def test_default_failure_still_aborts_batch(self):
        with self.assertRaises(RuntimeError):
            self.run_render(fail_titles=("乙",))
        self.assertFalse((self.out_dir / "渲染失败报告.json").exists())

    def test_keep_going_renders_rest_and_writes_report(self):
        code, rendered = self.run_render(fail_titles=("乙",), keep_going=True)
        self.assertEqual(code, 1)
        self.assertEqual(rendered, ["01_甲.jpg", "03_丙.jpg"])
        report = json.loads(
            (self.out_dir / "渲染失败报告.json").read_text(encoding="utf-8"))
        self.assertEqual(len(report["failures"]), 1)
        failure = report["failures"][0]
        self.assertEqual((failure["index"], failure["title"]), (2, "乙"))
        self.assertEqual(failure["times"], [3.0, 4.0])
        self.assertIn("抽帧失败", failure["reason"])
        self.assertFalse((self.out_dir / "final_contact_sheet.jpg").exists())

    def test_resume_only_rerenders_missing_cards_and_clears_report(self):
        self.run_render(fail_titles=("乙",), keep_going=True)
        code, rendered = self.run_render(resume=True)
        self.assertEqual(code, 0)
        self.assertEqual(rendered, ["02_乙.jpg"])
        self.assertFalse((self.out_dir / "渲染失败报告.json").exists())
        self.assertTrue((self.out_dir / "final_contact_sheet.jpg").is_file())

    def test_resume_rerenders_corrupt_output(self):
        self.run_render()
        (self.out_dir / "03_丙.jpg").write_bytes(b"broken")
        code, rendered = self.run_render(resume=True)
        self.assertEqual(code, 0)
        self.assertEqual(rendered, ["03_丙.jpg"])

    def test_resume_rerenders_truncated_jpeg(self):
        self.run_render()
        card = self.out_dir / "02_乙.jpg"
        Image.effect_noise((200, 200), 64).convert("RGB").save(card, quality=95)
        data = card.read_bytes()
        card.write_bytes(data[: len(data) // 2])
        self.assertFalse(MODULE.is_valid_image(card))
        code, rendered = self.run_render(resume=True)
        self.assertEqual(code, 0)
        self.assertEqual(rendered, ["02_乙.jpg"])


class TmpDirTests(unittest.TestCase):
    def setUp(self):
        patcher = mock.patch.object(MODULE, "TMP_DIR", None)
        patcher.start()
        self.addCleanup(patcher.stop)
        env = mock.patch.dict(os.environ)
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop(MODULE.TMP_DIR_ENV, None)

    def run_grab(self, **kwargs):
        seen = {}

        def fake_ffmpeg(args, context=""):
            seen["tmp"] = args[-1]
            Image.new("RGB", (8, 8), "red").save(args[-1], format="PNG")

        with mock.patch.object(MODULE, "ffmpeg", side_effect=fake_ffmpeg):
            MODULE.grab_frame("video.mp4", 1.0, **kwargs)
        return seen["tmp"]

    def test_default_uses_system_temp(self):
        tmp = self.run_grab()
        self.assertEqual(
            Path(tmp).parent.resolve(), Path(tempfile.gettempdir()).resolve()
        )
        self.assertFalse(os.path.exists(tmp))

    def test_explicit_dir_is_used_and_cleaned(self):
        with tempfile.TemporaryDirectory() as folder:
            tmp = self.run_grab(tmp_dir=folder)
            self.assertEqual(Path(tmp).parent, Path(folder))
            self.assertEqual(os.listdir(folder), [])

    def test_module_setting_is_used(self):
        with tempfile.TemporaryDirectory() as folder:
            with mock.patch.object(MODULE, "TMP_DIR", folder):
                tmp = self.run_grab()
            self.assertEqual(Path(tmp).parent, Path(folder))

    def test_resolve_default_is_none(self):
        self.assertIsNone(MODULE.resolve_tmp_dir(None))

    def test_resolve_missing_dir(self):
        with tempfile.TemporaryDirectory() as folder:
            missing = Path(folder) / "nope"
            with self.assertRaises(SystemExit) as ctx:
                MODULE.resolve_tmp_dir(str(missing))
        self.assertIn("不存在", str(ctx.exception))

    def test_resolve_not_a_directory(self):
        with tempfile.NamedTemporaryFile() as handle:
            with self.assertRaises(SystemExit) as ctx:
                MODULE.resolve_tmp_dir(handle.name)
        self.assertIn("不是目录", str(ctx.exception))

    def test_resolve_unwritable_dir(self):
        with tempfile.TemporaryDirectory() as folder:
            with mock.patch.object(MODULE.os, "access", return_value=False):
                with self.assertRaises(SystemExit) as ctx:
                    MODULE.resolve_tmp_dir(folder)
        self.assertIn("不可写", str(ctx.exception))

    def test_env_used_and_flag_wins(self):
        with tempfile.TemporaryDirectory() as env_dir, \
                tempfile.TemporaryDirectory() as flag_dir:
            os.environ[MODULE.TMP_DIR_ENV] = env_dir
            self.assertEqual(MODULE.resolve_tmp_dir(None), str(Path(env_dir).resolve()))
            self.assertEqual(
                MODULE.resolve_tmp_dir(flag_dir), str(Path(flag_dir).resolve())
            )

    def test_env_invalid_reports_source(self):
        os.environ[MODULE.TMP_DIR_ENV] = "/definitely/not/here"
        with self.assertRaises(SystemExit) as ctx:
            MODULE.resolve_tmp_dir(None)
        self.assertIn(MODULE.TMP_DIR_ENV, str(ctx.exception))

    def test_mkstemp_failure_is_clear_error(self):
        with mock.patch.object(
            MODULE.tempfile, "mkstemp", side_effect=PermissionError(13, "拒绝访问")
        ):
            with self.assertRaises(SystemExit) as ctx:
                MODULE.grab_frame("video.mp4", 1.0)
        self.assertIn("--tmp-dir", str(ctx.exception))

    def test_cli_rejects_missing_dir_before_rendering(self):
        with tempfile.TemporaryDirectory() as folder:
            proc = subprocess.run(
                [sys.executable, str(SCRIPT), "band", "x.mp4", "-t", "1",
                 "--tmp-dir", str(Path(folder) / "nope")],
                capture_output=True, text=True, encoding="utf-8",
            )
        self.assertNotEqual(proc.returncode, 0)
        self.assertIn("不存在", proc.stderr)
        self.assertNotIn("Traceback", proc.stderr)


if __name__ == "__main__":
    unittest.main()
