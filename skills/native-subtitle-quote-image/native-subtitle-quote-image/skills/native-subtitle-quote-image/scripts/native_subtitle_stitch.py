#!/usr/bin/env python3
"""把视频精确取帧并拼成字幕长图，支持烧录字幕与台词脚本两种模式。"""

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

try:
    import imageio_ffmpeg

    FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
except ImportError:
    FFMPEG = shutil.which("ffmpeg")
    if not FFMPEG:
        sys.exit("找不到 ffmpeg；请安装 ffmpeg 或 imageio-ffmpeg")

# 每张图最多 1 个主画面 + 6 个字幕条；再多字幕条会被压到不可读。
MAX_TIMES_PER_IMAGE = 7
# 缩略图上亮度变化超过 DIFF_LEVEL 的像素占比低于此值，视为同一画面。
# 真实访谈相邻句子的整帧差异通常在 5% 以上；静态封面重编码后接近 0。
DUPLICATE_PIXEL_RATIO = 0.005
DIFF_LEVEL = 12
# 抽帧临时文件目录环境变量；--tmp-dir 优先，都未设置时用系统临时目录。
TMP_DIR_ENV = "NSQI_TMP_DIR"
# 由 main() 根据 --tmp-dir / 环境变量设置；None 表示系统默认。
TMP_DIR = None


def ffmpeg(args, context="FFmpeg 处理失败"):
    try:
        return subprocess.run(
            [FFMPEG, "-hide_banner", "-loglevel", "error", "-y", *args],
            check=True,
            capture_output=True,
        )
    except FileNotFoundError:
        raise SystemExit(f"找不到 FFmpeg 可执行文件: {FFMPEG}") from None
    except subprocess.CalledProcessError as exc:
        stderr = exc.stderr.decode("utf-8", errors="replace").strip()
        detail = "\n".join(stderr.splitlines()[-4:]) or "没有返回错误详情"
        raise SystemExit(f"{context}:\n{detail}") from None


def input_file(value, label):
    path = Path(value).expanduser().resolve()
    if not path.is_file():
        raise SystemExit(f"{label}不存在或不是文件: {path}")
    return path


def video_metadata(path):
    proc = subprocess.run(
        [FFMPEG, "-hide_banner", "-i", str(path)],
        capture_output=True,
        encoding="utf-8",
        errors="replace",
    )
    stderr = proc.stderr or ""
    size_match = re.search(r"Video:.*?(\d{2,5})x(\d{2,5})[\s,]", stderr)
    duration_match = re.search(
        r"Duration:\s*(\d{2}):(\d{2}):(\d{2}(?:\.\d+)?)", stderr
    )
    if not size_match or not duration_match:
        raise SystemExit(f"无法读取视频尺寸或时长: {path}")
    hours, minutes, seconds = duration_match.groups()
    duration = int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    return int(size_match.group(1)), int(size_match.group(2)), duration


def validate_time(value, label="时间点"):
    try:
        seconds = float(value)
    except (TypeError, ValueError):
        raise SystemExit(f"{label}必须是数字: {value!r}") from None
    if not math.isfinite(seconds) or seconds < 0:
        raise SystemExit(f"{label}必须是大于等于 0 的有限数字: {value!r}")
    return seconds


def resolve_tmp_dir(value=None):
    """解析抽帧临时目录：参数优先，其次环境变量；都没有返回 None（系统默认）。"""
    source = "--tmp-dir"
    if value is None:
        value = os.environ.get(TMP_DIR_ENV)
        source = f"环境变量 {TMP_DIR_ENV}"
    if value is None or not str(value).strip():
        return None
    path = Path(value).expanduser().resolve()
    if not path.exists():
        raise SystemExit(f"{source} 指定的临时目录不存在: {path}")
    if not path.is_dir():
        raise SystemExit(f"{source} 指定的路径不是目录: {path}")
    if not os.access(path, os.W_OK | os.X_OK):
        raise SystemExit(f"{source} 指定的临时目录不可写: {path}")
    return str(path)


def grab_frame(path, seconds, tmp_dir=None):
    """先快速跳转，再精确解码 3 秒，避免长 GOP 视频错帧。"""
    seconds = validate_time(seconds)
    preseek = max(0.0, seconds - 3.0)
    offset = seconds - preseek
    tmp_dir = tmp_dir or TMP_DIR
    try:
        fd, tmp = tempfile.mkstemp(suffix=".png", dir=tmp_dir)
    except OSError as exc:
        where = tmp_dir or tempfile.gettempdir()
        raise SystemExit(
            f"无法在临时目录创建抽帧文件: {where}（{exc.strerror or exc}）；"
            f"可用 --tmp-dir 或环境变量 {TMP_DIR_ENV} 指定可写目录"
        ) from None
    os.close(fd)
    try:
        ffmpeg(
            [
                "-ss",
                f"{preseek:.3f}",
                "-i",
                str(path),
                "-ss",
                f"{offset:.3f}",
                "-frames:v",
                "1",
                tmp,
            ],
            context=f"取帧失败 @ {seconds:.2f}s",
        )
        if not os.path.exists(tmp) or os.path.getsize(tmp) == 0:
            raise SystemExit(f"取帧失败 @ {seconds:.2f}s")
        with Image.open(tmp) as opened:
            image = opened.convert("RGB")
            image.load()
        return image
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def changed_ratio(a, b, width=160):
    """两张图在灰度缩略图上明显变化的像素占比。"""
    height = max(1, round(a.height * width / a.width))
    a = a.convert("L").resize((width, height), Image.Resampling.BILINEAR)
    b = b.convert("L").resize((width, height), Image.Resampling.BILINEAR)
    diff = ImageChops.difference(a, b).point(lambda v: 255 if v > DIFF_LEVEL else 0)
    return diff.histogram()[255] / (width * height)


def ensure_distinct_frames(frames, times, bands=None):
    """拦截静态封面视频：所有时间点画面相同，或原生字幕条重复。"""
    if len(frames) < 2:
        return
    if all(changed_ratio(frames[0], frame) < DUPLICATE_PIXEL_RATIO for frame in frames[1:]):
        listed = "、".join(f"{t:.2f}s" for t in times)
        raise SystemExit(
            f"所有时间点（{listed}）取到的画面几乎相同，源视频可能是静态封面图或画面冻结。"
            "请先用 sample 检查画面；确认要这样出图时加 --allow-duplicate-frames。"
        )
    if bands:
        for index in range(1, len(bands)):
            if changed_ratio(bands[index - 1], bands[index]) < DUPLICATE_PIXEL_RATIO:
                raise SystemExit(
                    f"{times[index - 1]:.2f}s 与 {times[index]:.2f}s 的字幕条几乎相同，"
                    "可能是同一句字幕重复或这段画面没有字幕。请用 sample 或 band 核对时间点；"
                    "确认无误时加 --allow-duplicate-frames。"
                )


def parse_aspect(value):
    try:
        parts = value.split(":")
        if len(parts) != 2:
            raise ValueError
        width, height = (float(x) for x in parts)
    except Exception as exc:
        raise argparse.ArgumentTypeError("比例必须写成 3:4 这样的格式") from exc
    if not math.isfinite(width) or not math.isfinite(height):
        raise argparse.ArgumentTypeError("比例必须是有限数字")
    if width <= 0 or height <= 0:
        raise argparse.ArgumentTypeError("比例必须为正数")
    return width, height


def safe_title(value):
    cleaned = re.sub(r"[\\/:*?\"<>|\n\r]+", "_", str(value)).strip(" ._")
    return cleaned or "未命名"


FONT_CANDIDATES = [
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/System/Library/Fonts/Hiragino Sans GB.ttc",
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/simhei.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJKsc-Regular.otf",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
]


HANGUL_RANGES = (
    ("\u1100", "\u11FF"),  # 谚文字母
    ("\u3130", "\u318F"),  # 谚文兼容字母
    ("\uAC00", "\uD7AF"),  # 谚文音节
)

OTHER_CJK_RANGES = (
    ("\u3040", "\u30FF"),  # 平假名与片假名
    ("\u3400", "\u9FFF"),  # CJK 统一表意文字
    ("\uF900", "\uFAFF"),  # CJK 兼容表意文字
    ("\uFF66", "\uFF9D"),  # 半角片假名
)


def _in_ranges(text, ranges):
    return any(start <= char <= end for char in text for start, end in ranges)


def contains_cjk(text):
    return _in_ranges(text, HANGUL_RANGES + OTHER_CJK_RANGES)


KOREAN_FONT_CANDIDATES = [
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "C:/Windows/Fonts/malgun.ttf",
]


def contains_hangul(text):
    return _in_ranges(text, HANGUL_RANGES)


def font_candidates(path, text):
    candidates = [path] if path else []
    if contains_hangul(text):
        candidates.extend(KOREAN_FONT_CANDIDATES)
    candidates.extend(FONT_CANDIDATES)
    return candidates


def load_subtitle_font(path, size, text):
    candidates = font_candidates(path, text)
    if not contains_cjk(text):
        candidates.append("DejaVuSans.ttf")
    for candidate in candidates:
        if not candidate:
            continue
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    if contains_cjk(text):
        raise SystemExit(
            "找不到可用的中文字体；请安装中文字体或使用 --font 指定字体文件"
        )
    return ImageFont.load_default()


# 说话人前缀：比台词小一号、用强调色，与台词共用基线。
SPEAKER_PREFIX_SCALE = 0.68
SPEAKER_PREFIX_FILL = (255, 214, 74)
EMPHASIS_FILL = (255, 196, 64)
EMPHASIS_PLATE_ALPHA = 110
SPEAKER_MODES = ("none", "on-change", "every")


def speaker_label(speaker, text):
    separator = "：" if contains_cjk(speaker + text) else ": "
    return f"{speaker}{separator}"


def draw_scripted_subtitle(
    image, text, y_center, font_path, font_size, max_width, speaker=None,
    emphasis=False,
):
    draw = ImageDraw.Draw(image)
    minimum = max(12, round(font_size * 0.55))
    label = speaker_label(speaker, text) if speaker else ""
    label_width = 0
    if label:
        # 前缀字号只跟基础字号走，不随台词缩小；放不下时只缩台词。
        label_size = max(12, round(font_size * SPEAKER_PREFIX_SCALE))
        label_font = load_subtitle_font(font_path, label_size, label)
        label_stroke = max(2, label_size // 14)
        label_box = draw.textbbox(
            (0, 0), label, font=label_font, stroke_width=label_stroke
        )
        label_width = label_box[2] - label_box[0]
    chosen = None
    box = None
    for size in range(font_size, minimum - 1, -2):
        font = load_subtitle_font(font_path, size, text)
        stroke = max(3, size // 10) if emphasis else max(2, size // 14)
        candidate_box = draw.textbbox(
            (0, 0), text, font=font, stroke_width=stroke
        )
        if label_width + candidate_box[2] - candidate_box[0] <= max_width:
            chosen = (font, stroke)
            box = candidate_box
            break
    if chosen is None:
        raise SystemExit(
            f"台词过长，缩小到可读下限后仍放不下: {text!r}；请拆句或删减"
        )
    font, stroke = chosen
    text_width = box[2] - box[0]
    text_height = box[3] - box[1]
    x = (image.width - label_width - text_width) // 2 - box[0] + label_width
    y = y_center - text_height // 2 - box[1]
    if emphasis:
        # 轻微半透明底衬，只铺在这一行的文字范围内；先画底衬，避免压暗前缀和台词。
        pad = max(4, size // 4)
        left = x + box[0] - label_width - pad
        right = x + box[2] + pad
        top = y + box[1] - pad // 2
        bottom = y + box[3] + pad // 2
        plate = Image.new("RGBA", image.size, (0, 0, 0, 0))
        ImageDraw.Draw(plate).rounded_rectangle(
            (left, top, right, bottom), radius=pad,
            fill=(0, 0, 0, EMPHASIS_PLATE_ALPHA),
        )
        blended = Image.alpha_composite(image.convert("RGBA"), plate).convert(image.mode)
        image.paste(blended)
        draw = ImageDraw.Draw(image)
    if label:
        # 默认锚点在字形上沿，基线 = y + ascent；前缀对齐到台词基线。
        baseline = y + font.getmetrics()[0]
        label_y = baseline - label_font.getmetrics()[0]
        draw.text(
            (x + box[0] - label_width - label_box[0], label_y),
            label,
            font=label_font,
            fill=SPEAKER_PREFIX_FILL,
            stroke_width=label_stroke,
            stroke_fill="black",
        )
    draw.text(
        (x, y),
        text,
        font=font,
        fill=EMPHASIS_FILL if emphasis else "white",
        stroke_width=stroke,
        stroke_fill="black",
    )


def normalize_script_lines(data, duration, speaker_mode="none"):
    lines = data.get("lines") if isinstance(data, dict) else None
    if not isinstance(lines, list) or len(lines) < 2:
        raise SystemExit("台词脚本必须包含至少 2 项的 lines 数组")
    if len(lines) > MAX_TIMES_PER_IMAGE:
        raise SystemExit(
            f"台词脚本最多支持 {MAX_TIMES_PER_IMAGE} 个时间点；请拆成多张图"
        )
    normalized = []
    previous = -1.0
    for index, item in enumerate(lines):
        if not isinstance(item, dict):
            raise SystemExit(f"lines[{index}] 必须是对象")
        seconds = validate_time(item.get("t"), f"lines[{index}].t")
        if seconds <= previous:
            raise SystemExit("台词时间点必须严格递增")
        if seconds >= duration:
            raise SystemExit(
                f"lines[{index}].t={seconds:.2f}s 必须小于视频时长 {duration:.2f}s"
            )
        raw_text = item.get("text")
        if not isinstance(raw_text, str):
            raise SystemExit(f"lines[{index}].text 必须是字符串")
        text = raw_text.strip()
        if not text:
            raise SystemExit(f"lines[{index}].text 不能为空")
        if "\n" in text or "\r" in text:
            raise SystemExit(f"lines[{index}].text 必须是单行台词")
        entry = {"t": seconds, "text": text}
        emphasis = item.get("emphasis")
        if emphasis is not None:
            if not isinstance(emphasis, bool):
                raise SystemExit(f"lines[{index}].emphasis 必须是 true 或 false")
            entry["emphasis"] = emphasis
        speaker = item.get("speaker")
        if speaker is not None:
            if not isinstance(speaker, str) or not speaker.strip():
                raise SystemExit(f"lines[{index}].speaker 必须是非空字符串")
            speaker = speaker.strip()
            if "\n" in speaker or "\r" in speaker:
                raise SystemExit(f"lines[{index}].speaker 必须是单行")
            entry["speaker"] = speaker
        elif speaker_mode != "none":
            raise SystemExit(
                f"--speaker-prefix {speaker_mode} 需要每句都有 speaker；"
                f"lines[{index}] 缺少 speaker"
            )
        normalized.append(entry)
        previous = seconds
    return normalized


def apply_emphasis(lines, target):
    """target 为 None 或 "last" / 1 起算的行号；写入 emphasis 字段，JSON 里显式标注的行保留。"""
    if target is None:
        return lines
    if target == "last":
        index = len(lines) - 1
    else:
        index = target - 1
        if not 0 <= index < len(lines):
            raise SystemExit(
                f"--emphasize-line {target} 超出范围；台词共 {len(lines)} 句（行号从 1 起算）"
            )
    lines[index]["emphasis"] = True
    return lines


def parse_emphasize_line(value):
    if value == "last":
        return value
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("须为 last 或从 1 起算的行号") from None
    if number < 1:
        raise argparse.ArgumentTypeError("须为 last 或从 1 起算的行号")
    return number


def apply_speaker_prefix(lines, mode):
    """按模式决定每句是否显示前缀，结果写入 prefix 字段；text 不变。"""
    previous = None
    for line in lines:
        speaker = line.get("speaker")
        show = mode == "every" or (mode == "on-change" and speaker != previous)
        line["prefix"] = speaker if show else None
        previous = speaker
    return lines


def normalize_times(values, label="时间点"):
    if not isinstance(values, list) or len(values) < 2:
        raise SystemExit(f"{label}必须是至少包含 2 项的数组")
    if len(values) > MAX_TIMES_PER_IMAGE:
        raise SystemExit(
            f"{label}最多支持 {MAX_TIMES_PER_IMAGE} 个时间点；请拆成多张图"
        )
    times = [
        validate_time(value, f"{label}[{index}]")
        for index, value in enumerate(values)
    ]
    if any(b <= a for a, b in zip(times, times[1:])):
        raise SystemExit(f"{label}必须严格递增: {values}")
    return times


def crop_band(frame, top, bottom):
    if not 0 <= top < bottom <= 1:
        raise SystemExit("字幕区域必须满足 0 <= top < bottom <= 1")
    y0, y1 = int(frame.height * top), int(frame.height * bottom)
    if y1 <= y0:
        raise SystemExit("--band-bottom 必须大于 --band-top")
    return frame.crop((0, y0, frame.width, y1)), y0, y1


def fit_lower(image, size, vertical=0.72):
    return ImageOps.fit(
        image,
        size,
        method=Image.Resampling.LANCZOS,
        centering=(0.5, vertical),
    )


def choose_hero_fraction(strip_count, requested=None):
    """保持字幕条紧凑；台词较少时把多余高度留给主画面。"""
    if strip_count <= 0:
        raise SystemExit("至少需要 1 个字幕条")
    if requested is not None:
        return requested
    return min(0.82, max(0.48, 1.0 - strip_count * 0.075))


def six_line_geometry(out_width, out_height):
    """Return the fixed six-line card's hero and strip heights."""
    strip_height = max(1, round(out_width * 114 / 1080))
    hero_height = out_height - 5 * strip_height
    hero_fraction = hero_height / out_height
    if not 0.25 <= hero_fraction <= 0.85:
        raise SystemExit("六句卡主画面高度比例必须在 0.25–0.85 之间")
    return hero_height, strip_height, hero_fraction


HERO_ZOOM_RANGE = (0.8, 1.0)


def parse_hero_zoom(text):
    """解析 --hero-zoom：逗号分隔的每卡缩放系数，范围 0.8–1.0。"""
    low, high = HERO_ZOOM_RANGE
    values = []
    for part in str(text).split(","):
        part = part.strip()
        try:
            value = float(part)
        except ValueError:
            raise SystemExit(
                f"--hero-zoom 含无法解析的系数 {part!r}；示例: 1.0,0.9,0.95"
            ) from None
        if not low <= value <= high:
            raise SystemExit(f"--hero-zoom 系数 {part} 超出范围，必须在 {low}–{high} 之间")
        values.append(value)
    return values


def hero_zoom_for_card(zooms, card_index):
    """按卡循环取缩放系数；card_index 从 0 开始。未启用时返回 1.0。"""
    if not zooms:
        return 1.0
    return zooms[card_index % len(zooms)]


def zoom_crop(image, zoom):
    """居中裁掉四周再放回原尺寸；只用于主图，zoom >= 1 时原样返回。"""
    if zoom >= 1.0:
        return image
    width, height = image.size
    crop_w = max(1, round(width * zoom))
    crop_h = max(1, round(height * zoom))
    left, top = (width - crop_w) // 2, (height - crop_h) // 2
    window = image.crop((left, top, left + crop_w, top + crop_h))
    return window.resize((width, height), Image.Resampling.LANCZOS)


def scale_to_width(image, width):
    """只等比缩放；同宽时保留原始像素，不把裁切区域拉回源高度。"""
    if width == image.width:
        return image.copy()
    height = max(1, round(image.height * width / image.width))
    return image.resize((width, height), Image.Resampling.LANCZOS)


DIVIDER_HEIGHT = 2
DIVIDER_COLOR = (96, 96, 96)
MAX_STRIP_GAP = 8


def layout_gaps(strip_count, strip_gap=0, hero_divider="none"):
    """部件之间插入的 (高度, 颜色) 列表；只新增背景像素，不覆盖任何画面。"""
    gaps = []
    if strip_count:
        gaps.append((DIVIDER_HEIGHT, DIVIDER_COLOR) if hero_divider == "line" else (0, "black"))
        gaps.extend([(strip_gap, "black")] * (strip_count - 1))
    return gaps


def stack_parts(parts, gaps=None):
    if any(part.width != parts[0].width for part in parts):
        raise SystemExit("源帧宽度不一致；请先检查视频旋转或分辨率变化")
    gaps = gaps or [(0, "black")] * (len(parts) - 1)
    total = sum(p.height for p in parts) + sum(h for h, _ in gaps)
    canvas = Image.new("RGB", (parts[0].width, total), "black")
    y = 0
    for index, part in enumerate(parts):
        canvas.paste(part, (0, y))
        y += part.height
        if index < len(gaps) and gaps[index][0]:
            canvas.paste(gaps[index][1], (0, y, part.width, y + gaps[index][0]))
            y += gaps[index][0]
    return canvas


def gap_note(strip_gap, hero_divider):
    notes = []
    if hero_divider == "line":
        notes.append(f"主图与字幕条间 {DIVIDER_HEIGHT}px 分隔线")
    if strip_gap:
        notes.append(f"条间缝隙 {strip_gap}px")
    return "，".join(notes) or "条间距 0"


def save_stack(parts, out_path, gaps=None, note="条间距 0"):
    canvas = stack_parts(parts, gaps)
    canvas.save(out_path, quality=93, subsampling=0)
    print(f"完成: {out_path} ({canvas.width}x{canvas.height})")
    print(f"原比例布局: 仅裁切与等比缩放，高度随内容计算，{note}")


def subtitle_extent(band):
    """估计字幕条内文字的左右边界 (left, right)；找不到可信文字时返回 None。

    烧录字幕通常是低饱和的亮色笔画，旁边有描边、阴影或更暗的背景。
    只用于决定两侧能裁多少：宁可把背景误判成文字而少裁，也不能漏掉文字。
    """
    rgb = band.convert("RGB")
    width, height = rgb.size
    gray = rgb.convert("L")
    bright = gray.point(lambda p: 255 if p >= 200 else 0)
    neutral = rgb.convert("HSV").getchannel("S").point(lambda p: 255 if p <= 70 else 0)
    contrast = ImageChops.subtract(gray, gray.filter(ImageFilter.MinFilter(5)))
    edged = contrast.point(lambda p: 255 if p >= 60 else 0)
    mask = ImageChops.multiply(ImageChops.multiply(bright, neutral), edged)
    # BOX 缩成一行即每列的文字像素占比。
    counts = [value * height / 255 for value in mask.resize((width, 1), Image.Resampling.BOX).tobytes()]
    minimum = max(1.5, height * 0.03)
    gap = max(6, round(width * 0.04))
    clusters = []
    for x, count in enumerate(counts):
        if count < minimum:
            continue
        if clusters and x - clusters[-1][1] <= gap:
            clusters[-1][1] = x
            clusters[-1][2] += count
        else:
            clusters.append([x, x, count])
    if not clusters:
        return None
    strongest = max(mass for _, _, mass in clusters)
    kept = [(left, right) for left, right, mass in clusters if mass >= strongest * 0.25]
    left, right = min(k[0] for k in kept), max(k[1] for k in kept) + 1
    if right - left < width * 0.02:
        return None
    return left, right


def fit_fixed_canvas(stack, extents, size, fit="crop", crop_center=0.5):
    """把整张拼图放进固定画布；所有部分始终同一缩放倍数。

    fit="crop" 时先统一裁去两侧，最多裁到字幕安全边界，剩余差额再留黑边；
    任一字幕边界无法确认时不裁切。返回 (画布, 说明)。
    """
    target_w, target_h = size
    source_w, source_h = stack.size
    wanted_w = round(source_h * target_w / target_h)
    if fit != "crop" or wanted_w >= source_w:
        note = "比例不匹配处留黑边" if fit == "crop" else "按 --fit pad 留黑边，未裁切"
        return ImageOps.pad(stack, size, method=Image.Resampling.LANCZOS, color="black"), note
    unknown = [index for index, extent in enumerate(extents, 1) if extent is None]
    if unknown:
        listed = "、".join(str(index) for index in unknown)
        note = f"第 {listed} 句未能确认字幕左右边界，整图留黑边，未裁切"
        return ImageOps.pad(stack, size, method=Image.Resampling.LANCZOS, color="black"), note
    margin = max(4, round(source_w * 0.02))
    safe_left = max(0, min(e[0] for e in extents) - margin)
    safe_right = min(source_w, max(e[1] for e in extents) + margin)
    crop_w = max(wanted_w, safe_right - safe_left)
    if crop_w >= source_w:
        note = "字幕接近全宽，未裁切，整图留黑边"
        return ImageOps.pad(stack, size, method=Image.Resampling.LANCZOS, color="black"), note
    desired = round(source_w * crop_center - crop_w / 2)
    # 窗口必须同时容纳所有字幕并留在画面内，再尽量靠近期望中心。
    lowest = max(0, safe_right - crop_w)
    highest = min(source_w - crop_w, safe_left)
    x0 = min(max(desired, lowest), highest)
    cropped = stack.crop((x0, 0, x0 + crop_w, source_h))
    removed = (source_w - crop_w) / source_w
    if crop_w == wanted_w:
        canvas = cropped.resize(size, Image.Resampling.LANCZOS)
        note = f"两侧统一裁去 {removed:.0%}，字幕全部保留，无黑边"
    else:
        canvas = ImageOps.pad(cropped, size, method=Image.Resampling.LANCZOS, color="black")
        note = f"字幕较宽，两侧只裁去 {removed:.0%}，其余留黑边"
    return canvas, note


def render_one(
    video, times, out_path, aspect, out_width, top, bottom, hero_fraction,
    layout="natural", fit="crop", crop_center=0.5, check_duplicates=False,
    hero_zoom=1.0, strip_gap=0, hero_divider="none",
):
    times = normalize_times(times)
    frames = [grab_frame(video, seconds) for seconds in times]
    first = frames[0]
    first_band, _, subtitle_bottom = crop_band(first, top, bottom)
    bands = [crop_band(frame, top, bottom)[0] for frame in frames[1:]]
    if check_duplicates:
        ensure_distinct_frames(frames, times, [first_band, *bands])
    hero_source_height = subtitle_bottom
    if hero_fraction is not None:
        # 显式比例只决定源画面裁切窗口，不能改变第一句字幕的缩放倍数。
        requested_height = round(sum(b.height for b in bands) * hero_fraction / (1 - hero_fraction))
        hero_source_height = min(subtitle_bottom, max(first_band.height, requested_height))
    hero = first.crop((0, subtitle_bottom - hero_source_height, first.width, subtitle_bottom))
    band_height = first_band.height
    if hero_zoom < 1.0 and hero.height > band_height:
        # 只缩放字幕条以上的画面；第一句原生字幕条原样保留，窗口不会进入其中。
        scene_height = hero.height - band_height
        scene = zoom_crop(hero.crop((0, 0, hero.width, scene_height)), hero_zoom)
        zoomed = hero.copy()
        zoomed.paste(scene, (0, 0))
        hero = zoomed
    # 先拼源像素，再对整张画布缩放：所有原生字幕只经历同一个几何变换。
    # 缝隙与分隔线是新增的背景像素，随整图一起缩放，不覆盖字幕条。
    source_stack = stack_parts([hero, *bands], layout_gaps(len(bands), strip_gap, hero_divider))
    if layout == "natural":
        width = out_width or first.width
        canvas = scale_to_width(source_stack, width)
    else:
        width = out_width or 1440
        aw, ah = aspect
        extents = [subtitle_extent(band) for band in [first_band, *bands]]
        canvas, fit_note = fit_fixed_canvas(
            source_stack, extents, (width, round(width * ah / aw)), fit, crop_center,
        )
    canvas.save(out_path, quality=93, subsampling=0)
    print(f"完成: {out_path} ({canvas.width}x{canvas.height})")
    print(f"原生字幕: 整图统一等比缩放，字幕条 {len(bands)} 个，{gap_note(strip_gap, hero_divider)}")
    if layout == "fixed":
        print(f"固定画布: {fit_note}")


def scripted_render_one(
    video,
    lines,
    out_path,
    aspect,
    out_width,
    band_center,
    hero_fraction,
    font_path,
    font_size,
    layout="fixed",
    frame_top=0.0,
    frame_bottom=1.0,
    check_duplicates=False,
    six_line_card=False,
    hero_zoom=1.0,
    strip_gap=0,
    hero_divider="none",
):
    frames = [
        crop_band(grab_frame(video, line["t"]), frame_top, frame_bottom)[0]
        for line in lines
    ]
    if check_duplicates:
        ensure_distinct_frames(frames, [line["t"] for line in lines])
    first_frame = frames[0]
    out_width = out_width or (first_frame.width if layout == "natural" else 1440)
    if layout == "natural":
        hero = scale_to_width(zoom_crop(first_frame, hero_zoom), out_width)
        # 1280 像素宽的源画面默认采样 72 像素条高，不依赖总画布高度。
        source_strip_height = min(first_frame.height, max(1, round(first_frame.width * 0.05625)))
        strip_height = max(1, round(source_strip_height * out_width / first_frame.width))
        base_font = font_size or max(16, round(strip_height * 0.62))
        draw_scripted_subtitle(
            hero, lines[0]["text"], hero.height - strip_height // 2,
            font_path, base_font, round(out_width * 0.92),
            speaker=lines[0].get("prefix"),
            emphasis=lines[0].get("emphasis", False),
        )
        parts = [hero]
        for line, frame in zip(lines[1:], frames[1:]):
            height = min(frame.height, max(1, round(frame.width * 0.05625)))
            center = round(frame.height * band_center)
            y0 = max(0, min(frame.height - height, center - height // 2))
            strip = scale_to_width(frame.crop((0, y0, frame.width, y0 + height)), out_width)
            draw_scripted_subtitle(
                strip, line["text"], strip.height // 2,
                font_path, base_font, round(out_width * 0.92),
                speaker=line.get("prefix"),
                emphasis=line.get("emphasis", False),
            )
            parts.append(strip)
        save_stack(
            parts, out_path, layout_gaps(len(parts) - 1, strip_gap, hero_divider),
            gap_note(strip_gap, hero_divider),
        )
        return
    aw, ah = aspect
    out_height = round(out_width * ah / aw)
    strip_count = len(lines) - 1
    if six_line_card:
        # 1080x1440: 870px hero + five contiguous 114px strips.
        # Keep the strip pitch proportional when --width changes.
        hero_height, strip_height, hero_fraction = six_line_geometry(out_width, out_height)
        strip_heights = [strip_height] * strip_count
        gaps = layout_gaps(strip_count)
        base_font = font_size or max(24, round(out_width * 0.0587))
    else:
        hero_fraction = choose_hero_fraction(strip_count, hero_fraction)
        hero_height = round(out_height * hero_fraction)
        gaps = layout_gaps(strip_count, strip_gap, hero_divider)
        remaining = out_height - hero_height - sum(h for h, _ in gaps)
        if remaining < strip_count * 16:
            raise SystemExit("缝隙与分隔线占用过多高度；请减小 --strip-gap 或 --hero-fraction")
        base_strip = remaining // strip_count
        strip_heights = [base_strip] * strip_count
        strip_heights[-1] += remaining - sum(strip_heights)
        base_font = font_size or max(24, round(out_width / 18))

    hero = ImageOps.fit(
        zoom_crop(first_frame, hero_zoom),
        (out_width, hero_height),
        method=Image.Resampling.LANCZOS,
        centering=(0.5, 0.5),
    )
    first_strip_height = strip_heights[0]
    first_line_y = hero.height - first_strip_height // 2
    if not six_line_card:
        first_line_y -= max(4, out_height // 150)
    draw_scripted_subtitle(
        hero,
        lines[0]["text"],
        first_line_y,
        font_path,
        min(base_font, max(16, round(first_strip_height * 0.62))),
        round(out_width * 0.92),
        speaker=lines[0].get("prefix"),
        emphasis=lines[0].get("emphasis", False),
    )

    strips = []
    for line, frame, strip_height in zip(lines[1:], frames[1:], strip_heights):
        source_height = max(
            1, round(frame.width * strip_height / out_width)
        )
        source_height = min(source_height, frame.height)
        center_y = round(frame.height * band_center)
        y0 = max(0, min(frame.height - source_height, center_y - source_height // 2))
        band = frame.crop((0, y0, frame.width, y0 + source_height))
        strip = ImageOps.fit(
            band,
            (out_width, strip_height),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.5),
        )
        draw_scripted_subtitle(
            strip,
            line["text"],
            strip.height // 2,
            font_path,
            min(base_font, max(16, round(strip.height * 0.62))),
            round(out_width * 0.92),
            speaker=line.get("prefix"),
            emphasis=line.get("emphasis", False),
        )
        strips.append(strip)

    canvas = Image.new("RGB", (out_width, out_height), "black")
    canvas.paste(hero, (0, 0))
    y = hero_height
    for index, strip in enumerate(strips):
        height, color = gaps[index]
        if height:
            canvas.paste(color, (0, y, out_width, y + height))
            y += height
        canvas.paste(strip, (0, y))
        y += strip.height
    canvas.save(out_path, quality=93, subsampling=0)
    print(f"完成: {out_path} ({out_width}x{out_height})")
    print(
        f"脚本模式: 主画面 {hero_fraction:.1%}，"
        f"字幕条 {strip_count} 个，{gap_note(strip_gap, hero_divider)}"
    )


def contact_sheet(paths, out_path, columns=4):
    if not paths:
        return
    columns = min(columns, len(paths))
    with Image.open(paths[0]) as first:
        thumb_w = 360
        thumb_h = max(1, round(thumb_w * first.height / first.width))
    rows = (len(paths) + columns - 1) // columns
    sheet = Image.new("RGB", (columns * thumb_w, rows * thumb_h), "#111111")
    for index, path in enumerate(paths):
        with Image.open(path) as opened:
            image = opened.convert("RGB")
            thumb = ImageOps.pad(image, (thumb_w, thumb_h), Image.Resampling.LANCZOS, color="#111111")
        sheet.paste(thumb, ((index % columns) * thumb_w, (index // columns) * thumb_h))
    sheet.save(out_path, quality=92, subsampling=0)


def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    remainder = seconds % 60
    if hours:
        return f"{hours:02d}:{minutes:02d}:{remainder:04.1f}"
    return f"{minutes:02d}:{remainder:04.1f}"


def build_sample_times(start, end, interval, max_frames):
    start = validate_time(start, "--start")
    end = validate_time(end, "--end")
    if end <= start:
        raise SystemExit("--end 必须大于 --start")
    if max_frames <= 0:
        raise SystemExit("--max-frames 必须为正整数")
    if interval is None:
        interval = max(0.25, (end - start) / 23)
    interval = validate_time(interval, "--interval")
    if interval == 0:
        raise SystemExit("--interval 必须大于 0")
    count = int(math.floor((end - start) / interval)) + 1
    if count > max_frames:
        suggested = (end - start) / max(1, max_frames - 1)
        raise SystemExit(
            f"候选帧数量为 {count}，超过上限 {max_frames}；"
            f"请把 --interval 调整为至少 {suggested:.2f} 秒"
        )
    return [start + index * interval for index in range(count)]


def build_focus_times(values, around, duration, max_frames):
    """围绕文字稿给出的时间点生成前、中、后三帧候选。"""
    if not values:
        raise SystemExit("--time 至少需要一个时间点")
    around = validate_time(around, "--around")
    if around == 0:
        raise SystemExit("--around 必须大于 0")
    decode_margin = min(0.5, duration / 10)
    latest_decodable = max(0.0, duration - decode_margin)
    times = []
    for index, value in enumerate(values):
        center = validate_time(value, f"--time[{index}]")
        if center > latest_decodable:
            raise SystemExit(
                f"--time[{index}]={center:.2f}s 超出可取帧范围 "
                f"0–{latest_decodable:.2f}s"
            )
        times.extend(
            max(0.0, min(latest_decodable, center + offset))
            for offset in (-around, 0.0, around)
        )
    unique = sorted({round(value, 3) for value in times})
    if len(unique) > max_frames:
        raise SystemExit(
            f"候选帧数量为 {len(unique)}，超过上限 {max_frames}；"
            "请减少 --time 数量或提高 --max-frames"
        )
    return unique


def sample_contact_sheet(video, times, out_path, video_size, columns, thumb_width):
    frame_width, frame_height = video_size
    thumb_height = max(1, round(thumb_width * frame_height / frame_width))
    label_height = 28
    columns = min(columns, len(times))
    rows = (len(times) + columns - 1) // columns
    sheet = Image.new(
        "RGB",
        (columns * thumb_width, rows * (thumb_height + label_height)),
        "#111111",
    )
    for index, seconds in enumerate(times):
        frame = grab_frame(video, seconds)
        thumb = ImageOps.contain(
            frame, (thumb_width, thumb_height), Image.Resampling.LANCZOS
        )
        tile = Image.new("RGB", (thumb_width, thumb_height + label_height), "#111111")
        tile.paste(thumb, ((thumb_width - thumb.width) // 2, 0))
        draw = ImageDraw.Draw(tile)
        draw.text((8, thumb_height + 7), format_timestamp(seconds), fill="white")
        x = (index % columns) * thumb_width
        y = (index // columns) * (thumb_height + label_height)
        sheet.paste(tile, (x, y))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out_path, quality=90, subsampling=0)


def refuse_existing(paths, overwrite):
    existing = [path for path in paths if path.exists()]
    if existing and not overwrite:
        listed = "\n".join(f"- {path}" for path in existing[:8])
        raise SystemExit(
            "以下输出已存在；请使用新的输出路径，或明确添加 --overwrite:\n" + listed
        )


FAILURE_REPORT = "渲染失败报告.json"


def is_valid_image(path):
    try:
        with Image.open(path) as image:
            image.verify()
        # verify() 不解码像素，查不出被截断的 JPEG；再完整解码一次。
        with Image.open(path) as image:
            image.load()
    except Exception:
        return False
    return True


def command_band(args):
    video = input_file(args.video, "视频")
    _, _, duration = video_metadata(video)
    timestamp = validate_time(args.time, "--time")
    if timestamp >= duration:
        raise SystemExit(f"--time 必须小于视频时长 {duration:.2f}s")
    out_path = Path(args.out).expanduser().resolve()
    refuse_existing([out_path], args.overwrite)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    frame = grab_frame(video, timestamp)
    _, y0, y1 = crop_band(frame, args.band_top, args.band_bottom)
    draw = ImageDraw.Draw(frame)
    line_width = max(3, frame.height // 300)
    draw.line((0, y0, frame.width, y0), fill="red", width=line_width)
    draw.line((0, y1, frame.width, y1), fill="red", width=line_width)
    frame.save(out_path, quality=93)
    print(f"字幕区域预览: {out_path} (y={y0}-{y1})")


LOW_RES_WARN_HEIGHT = 720


def decode_errors(path, seconds):
    """解码前 seconds 秒，返回 FFmpeg 报告的错误行（空列表表示干净）。"""
    try:
        proc = subprocess.run(
            [FFMPEG, "-hide_banner", "-v", "error", "-t", f"{seconds:g}",
             "-i", str(path), "-map", "0:v:0", "-f", "null", "-"],
            capture_output=True,
        )
    except FileNotFoundError:
        raise SystemExit(f"找不到 FFmpeg 可执行文件: {FFMPEG}") from None
    stderr = proc.stderr.decode("utf-8", errors="replace")
    lines = [line.strip() for line in stderr.splitlines() if line.strip()]
    if proc.returncode != 0 and not lines:
        lines = [f"FFmpeg 退出码 {proc.returncode}"]
    return lines


def command_check_source(args):
    video = input_file(args.video, "视频")
    seconds = validate_time(args.seconds, "--seconds")
    if seconds <= 0:
        raise SystemExit("--seconds 必须大于 0")
    if args.min_height is not None and args.min_height <= 0:
        raise SystemExit("--min-height 必须为正整数")
    try:
        width, height, duration = video_metadata(video)
    except SystemExit as exc:
        raise SystemExit(f"源视频自检失败（无法读取元数据，文件可能已损坏）: {exc}") from None
    print(f"源视频: {width}x{height}, 时长 {duration:.2f}s")

    failed = False
    if args.min_height is not None and height < args.min_height:
        print(f"失败: 分辨率 {height}p 低于 --min-height {args.min_height}", file=sys.stderr)
        failed = True
    elif args.min_height is None and height < LOW_RES_WARN_HEIGHT:
        print(
            f"警告: 分辨率 {height}p 低于 {LOW_RES_WARN_HEIGHT}p，画质可能不足；"
            "请征得用户确认，或用 --min-height 强制门槛",
            file=sys.stderr,
        )

    errors = decode_errors(video, seconds)
    if errors:
        failed = True
        print(f"失败: 解码前 {seconds:g} 秒出现错误:", file=sys.stderr)
        for line in errors[:5]:
            print(f"  {line}", file=sys.stderr)
        if len(errors) > 5:
            print(f"  …共 {len(errors)} 行", file=sys.stderr)
    if failed:
        raise SystemExit(1)
    print(f"自检通过: 前 {seconds:g} 秒解码无错误")


def command_sample(args):
    video = input_file(args.video, "视频")
    width, height, duration = video_metadata(video)
    decode_margin = min(0.5, duration / 10)
    latest_decodable = max(0.0, duration - decode_margin)
    if args.times:
        if args.start != 0.0 or args.end is not None or args.interval is not None:
            raise SystemExit(
                "使用 --time 时不要同时传 --start、--end 或 --interval"
            )
        times = build_focus_times(
            args.times, args.around, duration, args.max_frames
        )
    else:
        end = latest_decodable if args.end is None else validate_time(args.end, "--end")
        if end > duration + 0.05:
            raise SystemExit(f"--end 超出视频时长 {duration:.2f}s")
        end = min(end, latest_decodable)
        times = build_sample_times(args.start, end, args.interval, args.max_frames)
    if args.columns <= 0:
        raise SystemExit("--columns 必须为正整数")
    if args.thumb_width < 120:
        raise SystemExit("--thumb-width 不能小于 120")
    out_path = Path(args.out).expanduser().resolve()
    refuse_existing([out_path], args.overwrite)
    sample_contact_sheet(
        video, times, out_path, (width, height), args.columns, args.thumb_width
    )
    print(f"候选帧总览: {out_path}")
    print("时间点: " + ", ".join(f"{value:.2f}" for value in times))


def command_render(args):
    video = input_file(args.video, "视频")
    manifest_path = input_file(args.manifest, "manifest")
    try:
        with manifest_path.open(encoding="utf-8") as handle:
            data = json.load(handle)
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"manifest JSON 格式错误（第 {exc.lineno} 行第 {exc.colno} 列）: {exc.msg}"
        ) from None

    items = data.get("images") if isinstance(data, dict) else None
    if not isinstance(items, list) or not items:
        raise SystemExit("manifest 必须包含非空 images 数组")

    _, _, duration = video_metadata(video)
    jobs = []
    for index, item in enumerate(items, 1):
        if not isinstance(item, dict):
            raise SystemExit(f"images 第 {index} 项必须是对象")
        title = safe_title(item.get("title", f"图片{index}"))
        times = normalize_times(item.get("times"), f"images[{index}].times")
        if times[-1] >= duration:
            raise SystemExit(
                f"images[{index}].times 的最后时间点 {times[-1]:.2f}s "
                f"必须小于视频时长 {duration:.2f}s"
            )
        jobs.append((index, title, times))

    out_dir = Path(args.out_dir).expanduser().resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    outputs = [out_dir / f"{index:02d}_{title}.jpg" for index, title, _ in jobs]
    manifest_target = out_dir / "原生字幕时间点.json"
    contact_target = out_dir / "final_contact_sheet.jpg"
    report_target = out_dir / FAILURE_REPORT
    if args.resume:
        # 续跑只补缺失或损坏的卡；已有的有效图保留，总览图与时间点文件重新生成。
        # 待补的卡要么不存在、要么已确认损坏，不是成品，无需 --overwrite 即可重渲。
        pending = [
            (job, path) for job, path in zip(jobs, outputs) if not is_valid_image(path)
        ]
        skipped = len(jobs) - len(pending)
        if skipped:
            print(f"续跑: 跳过 {skipped} 张已完成的图")
    else:
        pending = list(zip(jobs, outputs))
        guarded = [*outputs, contact_target]
        if manifest_path != manifest_target:
            guarded.append(manifest_target)
        refuse_existing(guarded, args.overwrite)

    keep_going = args.keep_going or args.resume
    failures = []
    for (index, title, times), out_path in pending:
        try:
            render_one(
                video,
                times,
                out_path,
                args.aspect,
                args.width,
                args.band_top,
                args.band_bottom,
                args.hero_fraction,
                args.layout,
                args.fit or "crop",
                0.5 if args.crop_center is None else args.crop_center,
                check_duplicates=not args.allow_duplicate_frames,
                hero_zoom=hero_zoom_for_card(args.hero_zoom, index - 1),
                strip_gap=args.strip_gap,
                hero_divider=args.hero_divider,
            )
        except (Exception, SystemExit) as exc:
            if not keep_going:
                raise
            out_path.unlink(missing_ok=True)
            failures.append({
                "index": index,
                "title": title,
                "times": times,
                "reason": str(exc) or type(exc).__name__,
            })
            print(f"失败: 第 {index} 张（{title}）时间点 {times}: {failures[-1]['reason']}")

    if failures:
        report_target.write_text(
            json.dumps({"failures": failures}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"失败 {len(failures)}/{len(pending)} 张，清单: {report_target}")
        print("修正 manifest 后加 --resume 只重渲失败的卡；总览图未生成。")
        raise SystemExit(1)

    report_target.unlink(missing_ok=True)
    if manifest_path != manifest_target:
        shutil.copyfile(manifest_path, manifest_target)
    contact_sheet(outputs, contact_target)
    print(f"总览图: {contact_target}")


def command_render_script(args):
    video = input_file(args.video, "视频")
    script_path = input_file(args.script, "台词脚本")
    _, _, duration = video_metadata(video)
    try:
        data = json.loads(script_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(
            f"台词脚本 JSON 格式错误（第 {exc.lineno} 行第 {exc.colno} 列）: "
            f"{exc.msg}"
        ) from None
    lines = normalize_script_lines(data, duration, args.speaker_prefix)
    apply_speaker_prefix(lines, args.speaker_prefix)
    apply_emphasis(lines, args.emphasize_line)
    if args.speaker_prefix == "none" and any("speaker" in line for line in lines):
        print("提示: 台词含 speaker 字段，但未启用 --speaker-prefix，画面不显示说话人")
    if args.six_line_card:
        if len(lines) != 6:
            raise SystemExit("--six-line-card 需要恰好 6 句已核对台词")
    out_path = Path(args.out).expanduser().resolve()
    refuse_existing([out_path], args.overwrite)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    font_path = None
    if args.font:
        font_path = str(input_file(args.font, "字体"))
    scripted_render_one(
        video,
        lines,
        out_path,
        args.aspect,
        args.width,
        args.band_center,
        args.hero_fraction,
        font_path,
        args.font_size,
        args.layout,
        args.frame_top,
        args.frame_bottom,
        check_duplicates=not args.allow_duplicate_frames,
        six_line_card=args.six_line_card,
        hero_zoom=hero_zoom_for_card(args.hero_zoom, 0),
        strip_gap=args.strip_gap,
        hero_divider=args.hero_divider,
    )


TMP_DIR_HELP = f"抽帧临时文件目录（默认系统临时目录，也可用环境变量 {TMP_DIR_ENV}）"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check-source", help="下载后自检：分辨率与前 N 秒解码")
    check.add_argument("video")
    check.add_argument("--seconds", type=float, default=10.0,
                       help="解码自检的秒数（默认 10）")
    check.add_argument("--min-height", type=int,
                       help="最低画面高度；低于则失败。默认只在低于 720 时警告")
    check.set_defaults(func=command_check_source)

    sample = sub.add_parser("sample", help="生成带时间点的候选帧总览")
    sample.add_argument("video")
    sample.add_argument("--start", type=float, default=0.0)
    sample.add_argument("--end", type=float)
    sample.add_argument("--interval", type=float)
    sample.add_argument(
        "-t",
        "--time",
        dest="times",
        action="append",
        type=float,
        help="文字稿候选时间点，可重复传入；每个时间点生成前、中、后三帧",
    )
    sample.add_argument(
        "--around",
        type=float,
        default=0.8,
        help="配合 --time 使用的前后偏移秒数（默认 0.8）",
    )
    sample.add_argument("--max-frames", type=int, default=48)
    sample.add_argument("--columns", type=int, default=4)
    sample.add_argument("--thumb-width", type=int, default=320)
    sample.add_argument("--out", default="candidate-contact-sheet.jpg")
    sample.add_argument("--overwrite", action="store_true")
    sample.add_argument("--tmp-dir", help=TMP_DIR_HELP)
    sample.set_defaults(func=command_sample)

    band = sub.add_parser("band", help="预览字幕裁切区域")
    band.add_argument("video")
    band.add_argument("-t", "--time", type=float, required=True)
    band.add_argument("--band-top", type=float, default=0.78)
    band.add_argument("--band-bottom", type=float, default=0.96)
    band.add_argument("--out", default="band-preview.jpg")
    band.add_argument("--overwrite", action="store_true")
    band.add_argument("--tmp-dir", help=TMP_DIR_HELP)
    band.set_defaults(func=command_band)

    render = sub.add_parser("render", help="按 manifest 渲染整套拼图")
    render.add_argument("video")
    render.add_argument("--manifest", required=True)
    render.add_argument("--out-dir", required=True)
    render.add_argument("--aspect", type=parse_aspect, help="固定布局比例，默认 3:4")
    render.add_argument("--layout", choices=("fixed", "natural"),
                        help="默认 natural；显式 --aspect 时用 fixed，整图等比留边")
    render.add_argument("--width", type=int, help="固定布局默认 1440；原比例布局默认源宽度")
    render.add_argument("--band-top", type=float, default=0.78)
    render.add_argument("--band-bottom", type=float, default=0.96)
    render.add_argument(
        "--hero-fraction",
        type=float,
        help="固定布局的源主图裁切比例；受源高度限制，不单独放大主图",
    )
    render.add_argument(
        "--hero-zoom",
        type=parse_hero_zoom,
        help="每卡主图缩放系数，逗号分隔并按卡循环，如 1.0,0.9,0.95；范围 0.8–1.0，默认不启用。只裁掉更多主图画面再放大，不改字幕条；源清晰度不足时主图会更模糊",
    )
    render.add_argument(
        "--fit",
        choices=("crop", "pad"),
        help="固定布局如何适配画布：crop（默认）统一裁两侧到字幕安全边界，pad 只留黑边",
    )
    render.add_argument(
        "--crop-center",
        type=float,
        help="统一裁两侧时裁切窗口的水平中心，0–1，默认 0.5；始终不裁到字幕",
    )
    render.add_argument(
        "--allow-duplicate-frames",
        action="store_true",
        help="跳过重复画面检查（默认遇到静态封面或重复字幕条会中止）",
    )
    render.add_argument("--overwrite", action="store_true")
    render.add_argument("--tmp-dir", help=TMP_DIR_HELP)
    render.add_argument(
        "--keep-going",
        action="store_true",
        help="单张失败不中断整批，结束时输出失败清单并写入 渲染失败报告.json（有失败则退出码非零）",
    )
    render.add_argument(
        "--resume",
        action="store_true",
        help="续跑：跳过已存在且有效的图，只渲染缺失或失败的卡（隐含 --keep-going）",
    )
    render.add_argument(
        "--strip-gap", type=int, default=0,
        help="字幕条之间的黑色呼吸缝像素，0–8，默认 0；只新增背景像素，不覆盖画面",
    )
    render.add_argument(
        "--hero-divider", choices=("none", "line"), default="none",
        help="主图与字幕条之间插入 2px 细分隔线（line），默认 none；插入而非叠加，不改原画面",
    )
    render.set_defaults(func=command_render)

    scripted = sub.add_parser(
        "render-script",
        help="按时间点和台词 JSON 绘制紧凑字幕拼图",
    )
    scripted.add_argument("video")
    scripted.add_argument("--script", required=True)
    scripted.add_argument("--out", required=True)
    scripted.add_argument("--aspect", type=parse_aspect, help="固定布局比例，默认 3:4")
    scripted.add_argument("--layout", choices=("fixed", "natural"), default="fixed",
                          help="fixed: 固定画布；natural: 保留宽度，按裁切内容自动计算高度")
    scripted.add_argument("--width", type=int, help="固定布局默认 1440；原比例布局默认源宽度")
    scripted.add_argument("--frame-top", type=float, default=0.0, help="源画面上裁切边界，默认 0")
    scripted.add_argument("--frame-bottom", type=float, default=1.0, help="源画面下裁切边界，默认 1；只裁切不拉伸")
    scripted.add_argument(
        "--band-center",
        type=float,
        help="字幕条在源画面中的垂直中心比例（默认 0.88；六句卡默认 0.60）",
    )
    scripted.add_argument(
        "--hero-fraction",
        type=float,
        help="主画面高度比例；默认按台词数量自动保持紧凑密度",
    )
    scripted.add_argument(
        "--hero-zoom",
        type=parse_hero_zoom,
        help="主图缩放系数，范围 0.8–1.0，默认不启用；单张图只取第一个系数。只裁掉更多主图画面再放大，不改字幕条和文字；源清晰度不足时主图会更模糊",
    )
    scripted.add_argument(
        "--six-line-card", action="store_true",
        help="可选 3:4 六句卡：首句在主画面，另五句等距排在连续字幕条上",
    )
    scripted.add_argument("--font", help="中文字体文件；未指定时尝试系统字体")
    scripted.add_argument("--font-size", type=int, help="基础字号，过长台词仍会自动缩小")
    scripted.add_argument(
        "--speaker-prefix", choices=SPEAKER_MODES, default="none",
        help="说话人前缀：none 不显示（默认）；on-change 换人时显示；every 每句显示。"
             "需在台词 JSON 每句写 speaker",
    )
    scripted.add_argument(
        "--emphasize-line", type=parse_emphasize_line, metavar="N|last",
        help="强调指定行（暖色、加粗描边、轻微底衬）：last 为最后一句，数字从 1 起算；"
             "默认不强调。也可在台词 JSON 的某句写 \"emphasis\": true。仅脚本模式",
    )
    scripted.add_argument(
        "--allow-duplicate-frames",
        action="store_true",
        help="跳过重复画面检查（默认遇到静态封面或重复字幕条会中止）",
    )
    scripted.add_argument("--overwrite", action="store_true")
    scripted.add_argument("--tmp-dir", help=TMP_DIR_HELP)
    scripted.add_argument(
        "--strip-gap", type=int, default=0,
        help="字幕条之间的黑色呼吸缝像素，0–8，默认 0；只新增背景像素，不覆盖画面",
    )
    scripted.add_argument(
        "--hero-divider", choices=("none", "line"), default="none",
        help="主图与字幕条之间插入 2px 细分隔线（line），默认 none；插入而非叠加，不改原画面",
    )
    scripted.set_defaults(func=command_render_script)

    args = parser.parse_args()
    fixed_only = ("aspect", "hero_fraction", "fit", "crop_center")
    if args.command == "render" and args.layout is None:
        explicit = any(getattr(args, name) is not None for name in fixed_only)
        args.layout = "fixed" if explicit else "natural"
    if hasattr(args, "band_top") and not 0 <= args.band_top < args.band_bottom <= 1:
        raise SystemExit("字幕区域必须满足 0 <= top < bottom <= 1")
    if getattr(args, "width", None) is not None and args.width <= 0:
        raise SystemExit("--width 必须为正数")
    if hasattr(args, "frame_top") and not 0 <= args.frame_top < args.frame_bottom <= 1:
        raise SystemExit("源画面裁切必须满足 0 <= frame-top < frame-bottom <= 1")
    if getattr(args, "layout", None) == "natural" and (
        args.aspect is not None or args.hero_fraction is not None
    ):
        raise SystemExit("--layout natural 不接受 --aspect 或 --hero-fraction；高度由内容决定")
    if getattr(args, "layout", None) == "natural" and (
        getattr(args, "fit", None) is not None or getattr(args, "crop_center", None) is not None
    ):
        raise SystemExit("--layout natural 不接受 --fit 或 --crop-center；它们只用于固定画布")
    if getattr(args, "crop_center", None) is not None:
        if not 0 <= args.crop_center <= 1:
            raise SystemExit("--crop-center 必须在 0–1 之间")
        if args.fit == "pad":
            raise SystemExit("--crop-center 只用于 --fit crop")
    if hasattr(args, "aspect") and args.aspect is None:
        args.aspect = parse_aspect("3:4")
    if hasattr(args, "strip_gap"):
        if not 0 <= args.strip_gap <= MAX_STRIP_GAP:
            raise SystemExit(f"--strip-gap 必须在 0–{MAX_STRIP_GAP} 之间")
        if getattr(args, "six_line_card", False) and (
            args.strip_gap or args.hero_divider != "none"
        ):
            raise SystemExit("--six-line-card 使用固定几何，不接受 --strip-gap 或 --hero-divider")
    if getattr(args, "six_line_card", False):
        if args.layout != "fixed" or not math.isclose(args.aspect[0] / args.aspect[1], 0.75):
            raise SystemExit("--six-line-card 只支持固定 3:4 布局")
        if args.hero_fraction is not None:
            raise SystemExit("--six-line-card 不接受 --hero-fraction；主画面高度由字幕条计算")
    if hasattr(args, "band_center"):
        if args.band_center is None:
            args.band_center = 0.60 if args.six_line_card else 0.88
        if not 0.1 <= args.band_center <= 0.98:
            raise SystemExit("--band-center 必须在 0.10–0.98 之间")
    if getattr(args, "font_size", None) is not None and args.font_size < 12:
        raise SystemExit("--font-size 不能小于 12")
    if (
        hasattr(args, "hero_fraction")
        and args.hero_fraction is not None
        and not 0.25 <= args.hero_fraction <= 0.85
    ):
        raise SystemExit("--hero-fraction 必须在 0.25–0.85 之间")
    if hasattr(args, "tmp_dir"):
        global TMP_DIR
        TMP_DIR = resolve_tmp_dir(args.tmp_dir)
    args.func(args)


if __name__ == "__main__":
    main()
