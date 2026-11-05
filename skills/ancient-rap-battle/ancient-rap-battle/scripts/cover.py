# -*- coding: utf-8 -*-
"""Step 10 - covers: the two rivals face to face, gold brush title, red VS.

usage: python scripts/cover.py <episode_dir> [--clip B05] [--t 2.0] [--frame path.png] [--no-mirror]
default frame: the close two-shot of B's line 5 (Zhuge-Liang-style: B on the left), mirrored so A is on the left
like the title "A VS B". Writes cover/封面_竖版3x4.jpg (1080x1440, Douyin) and cover/封面_横版16x9.jpg.
"""
import argparse
import os
import subprocess
import sys

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import font, jload, load_episode  # noqa: E402

GOLD = [(255, 244, 190), (246, 200, 72), (196, 132, 24)]
RED = [(255, 96, 70), (214, 30, 30), (140, 10, 16)]
CREAM = [(255, 248, 225), (250, 232, 180), (232, 200, 130)]
INK = (34, 16, 0)


def gradient(size, stops):
    w, h = size
    g = Image.new("RGB", (1, h))
    for y in range(h):
        t = y / max(1, h - 1)
        a, b, u = (stops[0], stops[1], t / 0.5) if t < 0.5 else (stops[1], stops[2], (t - 0.5) / 0.5)
        g.putpixel((0, y), tuple(int(a[i] + (b[i] - a[i]) * u) for i in range(3)))
    return g.resize((w, h))


def fancy(img, xy, text, f, stops, stroke=6, shadow=14):
    W, H = img.size
    mask = Image.new("L", (W, H), 0)
    ImageDraw.Draw(mask).text(xy, text, font=f, fill=255, anchor="mm")
    outline = Image.new("L", (W, H), 0)
    ImageDraw.Draw(outline).text(xy, text, font=f, fill=255, anchor="mm", stroke_width=stroke, stroke_fill=255)
    img.paste(Image.new("RGB", (W, H), (0, 0, 0)), (6, 10), outline.filter(ImageFilter.GaussianBlur(shadow)).point(lambda v: int(v * .85)))
    img.paste(Image.new("RGB", (W, H), INK), (0, 0), outline)
    bb = mask.getbbox()
    if bb:
        grad = Image.new("RGB", (W, H), stops[1])
        grad.paste(gradient((bb[2] - bb[0], bb[3] - bb[1]), stops), bb[:2])
        img.paste(grad, (0, 0), mask)


def row(img, cx, y, items, gap=20):
    """items = [(text, font, stops, stroke)] laid out by MEASURED width (brush glyph widths are irregular)"""
    d = ImageDraw.Draw(img)
    ws = [d.textlength(t, font=f) for t, f, _, _ in items]
    x = cx - (sum(ws) + gap * (len(items) - 1)) / 2
    for (t, f, st, sk), w in zip(items, ws):
        fancy(img, (x + w / 2, y), t, f, st, stroke=sk)
        x += w + gap


def small(img, xy, text, anchor, fill):
    f = ImageFont.truetype(font("serif_sc"), 30 if img.size[0] < 1500 else 34)
    try:
        f.set_variation_by_name("Bold")
    except Exception:
        pass
    ImageDraw.Draw(img).text(xy, text, font=f, fill=fill, anchor=anchor, stroke_width=2, stroke_fill=INK)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep")
    ap.add_argument("--clip", default="B05")
    ap.add_argument("--t", type=float, default=2.0)
    ap.add_argument("--frame")
    ap.add_argument("--no-mirror", action="store_true")
    a = ap.parse_args()
    ep, e = a.ep, load_episode(a.ep)
    os.makedirs(os.path.join(ep, "cover"), exist_ok=True)
    frame = a.frame
    if not frame:
        picks = jload(os.path.join(ep, "work", "picks.json"))
        frame = os.path.join(ep, "cover", "frame.png")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", str(a.t), "-i",
                        os.path.join(ep, "clips", "%s_t%s.mp4" % (a.clip, picks[a.clip])), "-frames:v", "1", frame], check=True)
    f = Image.open(frame).convert("RGB")
    if not a.no_mirror:
        f = ImageOps.mirror(f)
    A, B = e["a"]["name_cn"], e["b"]["name_cn"]
    brush, en = font("brush"), font("serif_en_bolditalic")
    tag_f = ImageFont.truetype(font("serif_sc"), 46)
    try:
        tag_f.set_variation_by_name("Bold")
    except Exception:
        pass
    wm = e.get("watermark", "")

    # vertical 3:4
    W, H = 1080, 1440
    img = ImageEnhance.Brightness(ImageOps.fit(f, (W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(28))).enhance(0.42)
    fw, fh = int(W * 1.25), int(f.height * W * 1.25 / f.width)
    sharp = ImageEnhance.Contrast(f.resize((fw, fh), Image.LANCZOS)).enhance(1.08).crop(((fw - W) // 2, 0, (fw - W) // 2 + W, fh))
    m = Image.new("L", (W, fh), 255)
    d = ImageDraw.Draw(m)
    for y in range(110):
        d.line([(0, y), (W, y)], fill=int(255 * y / 110))
        d.line([(0, fh - 1 - y), (W, fh - 1 - y)], fill=int(255 * y / 110))
    y0 = 360
    img.paste(sharp, (0, y0), m)
    row(img, W // 2, 225, [(A, ImageFont.truetype(brush, 150), GOLD, 6), ("VS", ImageFont.truetype(en, 150), RED, 6),
                           (B, ImageFont.truetype(brush, 150), GOLD, 6)], gap=18)
    row(img, W // 2, y0 + fh + 70, [("说唱", ImageFont.truetype(brush, 140), GOLD, 6), ("Battle", ImageFont.truetype(en, 112), GOLD, 5)], gap=26)
    if e.get("tagline"):
        fancy(img, (W // 2, y0 + fh + 185), e["tagline"], tag_f, CREAM, stroke=3, shadow=6)
    small(img, (40, 52), "AI 生成", "lm", (230, 230, 230))
    if wm:
        small(img, (W - 40, 52), wm, "rm", (246, 200, 72))
    img.save(os.path.join(ep, "cover", "封面_竖版3x4.jpg"), quality=95)

    # horizontal 16:9
    W, H = 1920, 1080
    img = ImageEnhance.Contrast(f.resize((W, H), Image.LANCZOS)).enhance(1.08)
    shade = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(shade)
    for y in range(H // 2, H):
        d.line([(0, y), (W, y)], fill=int(205 * ((y - H / 2) / (H / 2)) ** 1.3))
    img.paste(Image.new("RGB", (W, H), (0, 0, 0)), (0, 0), shade)
    row(img, W // 2, 850, [(A, ImageFont.truetype(brush, 200), GOLD, 6), ("VS", ImageFont.truetype(en, 170), RED, 6),
                           (B, ImageFont.truetype(brush, 200), GOLD, 6)], gap=26)
    fancy(img, (W // 2, 990), "说唱 Battle" + (" · " + e["tagline"] if e.get("tagline") else ""),
          ImageFont.truetype(font("serif_sc"), 50), CREAM, stroke=3, shadow=6)
    small(img, (50, 60), "AI 生成", "lm", (230, 230, 230))
    if wm:
        small(img, (W - 50, 60), wm, "rm", (246, 200, 72))
    img.save(os.path.join(ep, "cover", "封面_横版16x9.jpg"), quality=95)
    print("wrote cover/封面_竖版3x4.jpg and cover/封面_横版16x9.jpg")


if __name__ == "__main__":
    main()
