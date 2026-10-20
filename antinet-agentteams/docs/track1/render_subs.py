"""Render subtitle-burned frames (Pillow) for each deck slide.

Reads _tmp/audio/manifest.json (per-slide title/bullets/narration text),
draws the slide (title + bullets) AND a bottom subtitle bar containing the
narration text, so subtitles are hard-burned into the PNG (no ffmpeg libass needed).

Output: frames_sub/page_NN.png
"""
import os, json
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
MAN = os.path.join(HERE, "audio", "manifest.json")
OUT = os.path.join(HERE, "frames_sub")
os.makedirs(OUT, exist_ok=True)

INK = (11, 20, 55); PAPER = (245, 241, 230); RED = (200, 57, 43)
GOLD = (184, 138, 43); GREY = (150, 160, 180); WHITE = (235, 240, 250)

def font(size, bold=False):
    p = r"C:\Windows\Fonts\msyhbd.ttc" if bold else r"C:\Windows\Fonts\msyh.ttc"
    if os.path.exists(p):
        return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def wrap(d, text, fnt, max_w):
    lines, cur = [], ""
    for ch in text:
        if d.textlength(cur + ch, font=fnt) <= max_w:
            cur += ch
        else:
            lines.append(cur); cur = ch
    if cur:
        lines.append(cur)
    return lines

def draw(idx, total, pid, title, bullets, subtitle):
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(img)
    for y in range(H):
        t = y / H
        d.line([(0, y), (W, y)], fill=(int(INK[0] + (6 - INK[0]) * t),
                                    int(INK[1] + (12 - INK[1]) * t),
                                    int(INK[2] + (38 - INK[2]) * t)))
    d.rectangle([0, 0, W, 14], fill=RED)
    d.rectangle([0, 0, 14, H], fill=RED)
    d.text((60, 64), f"GOAI · {pid}", font=font(34, True), fill=GOLD)
    tf = font(58, True)
    tlines = wrap(d, title, tf, W - 160)
    y = 140
    for ln in tlines[:2]:
        d.text((60, y), ln, font=tf, fill=PAPER); y += 70
    d.rectangle([60, y + 10, W - 60, y + 13], fill=GOLD)
    y += 50
    bf = font(32)
    for b in bullets[:5]:
        blines = wrap(d, b, bf, W - 230)
        d.ellipse([78, y + 10, 98, y + 30], fill=RED)
        ty = y
        for ln in blines[:2]:
            d.text((124, ty), ln, font=bf, fill=WHITE); ty += 44
        y = ty + 22
    # ---- subtitle bar (hard-burned) 800..1080 ----
    sub_top = 800
    d.rectangle([0, sub_top, W, H], fill=(0, 0, 0, 175))
    d.rectangle([0, sub_top, W, sub_top + 3], fill=GOLD)
    sf = font(30)
    slines = wrap(d, subtitle, sf, W - 120)[:6]
    sy = sub_top + 26
    for ln in slines:
        d.text((60, sy), ln, font=sf, fill=(255, 255, 255)); sy += 42
    d.text((W - 380, H - 36), f"GOAI 赛道一 Agent Infra   {idx}/{total}",
           font=font(20), fill=GREY)
    return img

with open(MAN, encoding="utf-8") as f:
    man = json.load(f)
print("rendering", len(man), "subtitle frames")
for i, m in enumerate(man, 1):
    img = draw(i, len(man), m["pid"], m["title"], m["bullets"], m["text"])
    img.save(os.path.join(OUT, f"page_{i:02d}.png"))
print("done ->", OUT)
