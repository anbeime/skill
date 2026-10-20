"""Render deck_track1.md -> Antinet_GOAI_track1_demo.mp4 (PPT playback video).

Self-contained: Pillow draws 1920x1080 slide PNGs, ffmpeg (imageio-ffmpeg) stitches
them with crossfade transitions. No desktop recording / slidep engine required.
"""
import os, re, subprocess, shutil
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "deck_track1.md")
FRAMES = os.path.join(HERE, "frames")
OUT = os.path.join(HERE, "Antinet_GOAI_track1_demo.mp4")
os.makedirs(FRAMES, exist_ok=True)

# ffmpeg binary
import imageio_ffmpeg
FF = imageio_ffmpeg.get_ffmpeg_exe()

# ---- fonts ----
def _font(regular, bold):
    cand = []
    if bold:
        cand += [r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\simhei.ttf"]
    cand += [regular, r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simhei.ttf"]
    for c in cand:
        if os.path.exists(c):
            try:
                return ImageFont.truetype(c, 0)  # size set later via font_variant
            except Exception:
                pass
    return None

_REG = r"C:\Windows\Fonts\msyh.ttc"
_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"

def font(size, bold=False):
    path = _BOLD if (bold and os.path.exists(_BOLD)) else _REG
    if os.path.exists(path):
        return ImageFont.truetype(path, size)
    # simhei fallback
    sh = r"C:\Windows\Fonts\simhei.ttf"
    if os.path.exists(sh):
        return ImageFont.truetype(sh, size)
    return ImageFont.load_default()

# ---- palette ----
INK   = (11, 20, 55)      # deep navy bg
PAPER = (245, 241, 230)   # 宣纸白
RED   = (200, 57, 43)      # 朱红
GOLD  = (184, 138, 43)     # 金
GREY  = (150, 160, 180)    # footer grey
WHITE = (235, 240, 250)

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

def draw_slide(idx, total, pid, title, bullets):
    W, H = 1920, 1080
    img = Image.new("RGB", (W, H), INK)
    d = ImageDraw.Draw(img)
    # subtle vertical gradient (darken bottom)
    for y in range(H):
        t = y / H
        r = int(INK[0] + (6 - INK[0]) * t)
        g = int(INK[1] + (12 - INK[1]) * t)
        b = int(INK[2] + (38 - INK[2]) * t)
        d.line([(0, y), (W, y)], fill=(r, g, b))
    # top + left spine
    d.rectangle([0, 0, W, 14], fill=RED)
    d.rectangle([0, 0, 14, H], fill=RED)
    # label
    lab = font(34, True)
    d.text((60, 64), f"GOAI · {pid}", font=lab, fill=GOLD)
    # title (wrap)
    tf = font(60, True)
    tlines = wrap(d, title, tf, W - 160)
    y = 140
    for ln in tlines[:2]:
        d.text((60, y), ln, font=tf, fill=PAPER)
        y += 72
    # divider
    d.rectangle([60, y + 12, W - 60, y + 15], fill=GOLD)
    y += 60
    # bullets
    bf = font(34)
    for b in bullets[:6]:
        b = re.sub(r"\*\*(.+?)\*\*", r"\1", b)
        blines = wrap(d, b, bf, W - 230)
        d.ellipse([78, y + 10, 98, y + 30], fill=RED)
        ty = y
        for ln in blines:
            d.text((124, ty), ln, font=bf, fill=WHITE)
            ty += 46
        y = ty + 26
    # footer
    ff = font(22)
    d.text((60, H - 52), "Antinet·八官署 — 面向复杂知识任务的多智能体基础设施", font=ff, fill=GREY)
    d.text((W - 380, H - 52), f"GOAI 赛道一 Agent Infra   {idx}/{total}", font=ff, fill=GREY)
    return img

# ---- parse deck ----
with open(SRC, encoding="utf-8") as f:
    raw = f.read()
blocks = re.split(r"\n## ", raw)
slides = []
for block in blocks[1:]:
    lines = block.splitlines()
    m = re.match(r"^(P\d+)\s*[·•-]?\s*(.+)$", lines[0].strip())
    if not m:
        continue
    pid, title = m.group(1), m.group(2).strip()
    bullets = [ln[2:].strip() for ln in lines[1:] if ln.strip().startswith("- ")]
    slides.append((pid, title, bullets))

print(f"parsed {len(slides)} slides")

# ---- render frames ----
paths = []
for i, (pid, title, bullets) in enumerate(slides):
    img = draw_slide(i + 1, len(slides), pid, title, bullets)
    p = os.path.join(FRAMES, f"page_{i+1:02d}.png")
    img.save(p)
    paths.append(p)
print("rendered frames ->", FRAMES)

# ---- ffmpeg stitch with crossfade ----
n = len(paths)
dur, td = 3.0, 0.5
inp = []
for p in paths:
    inp += ["-loop", "1", "-t", str(dur), "-i", p]
flt, prev = "", "[0:v]"
for i in range(1, n):
    off = round(i * (dur - td), 2)
    outtag = "[vout]" if i == n - 1 else f"[v{i}]"
    flt += f"{prev}[{i}:v]xfade=transition=fade:duration={td}:offset={off}{outtag};"
    prev = outtag
flt = flt.rstrip(";")

cmd = [FF, "-y"] + inp + ["-filter_complex", flt, "-map", "[vout]",
      "-c:v", "libx264", "-r", "25", "-pix_fmt", "yuv420p", OUT]
print("running ffmpeg...")
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode != 0:
    print("FFMPEG STDERR:\n", r.stderr[-1500:])
    raise SystemExit(1)
print("saved video:", OUT, "size:", os.path.getsize(OUT), "bytes")
