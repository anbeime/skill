# -*- coding: utf-8 -*-
"""Step 9 - packaging: grade, gold lyric subtitles (last two characters big on a red brush stroke), a source
note under every line, name cards, opening title, end question, watermark, crowd sound.

usage: python scripts/package.py <episode_dir> [--src preview/成片_拼接.mp4] [--watermark 账号名] [--test 0:15] [--phone]

Output size follows the source (2K stays 2K). Writes final/<title>_成片.mp4 (--phone: also a < 30 MB copy).
All text is drawn with Pillow into transparent PNGs and overlaid (ffmpeg's drawtext needs fontconfig, often missing).
Grade "B": softer highlights, a little less colour, adaptive sharpening and film grain - it takes the waxy,
plastic look off AI skin without darkening the film (a heavy grade made it ~30% darker once).
"""
import argparse
import os
import random
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import font, jload, load_episode  # noqa: E402
from cover import CREAM, GOLD as GOLD_GRAD, RED as RED_GRAD, fancy, row  # noqa: E402

GOLD = (255, 228, 92, 255)       # bright: the darker (255, 210, 64) read dull on phones
INK = (40, 22, 0, 255)
GRADE = ("eq=contrast=1.04:saturation=0.92:brightness=0.01,colorbalance=rs=0.01:bs=-0.01,"
         "curves=all='0/0 0.25/0.24 0.6/0.6 0.85/0.8 1/0.92',cas=0.35,vignette=angle=PI/12,noise=alls=9:allf=t+u")


class Sheet:
    def __init__(self, w, h):
        self.W, self.H, self.S = w, h, w / 1920

    def canvas(self):
        return Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))

    def f(self, size, weight="Black"):
        f = ImageFont.truetype(font("serif_sc"), int(size * self.S))
        try:
            f.set_variation_by_name(weight)
        except Exception:
            pass
        return f

    def shadowed(self, layer):
        sh = Image.new("RGBA", layer.size, (0, 0, 0, 0))
        sh.putalpha(layer.split()[3].point(lambda v: int(v * 0.7)))
        out = self.canvas()
        out.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5 * self.S)), (int(3 * self.S), int(4 * self.S)))
        out.alpha_composite(layer)
        return out

    def brush(self, w, h, seed):
        rnd = random.Random(seed)
        im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        for i in range(int(h * 0.9)):
            x0 = int(rnd.uniform(0, 0.06) * w + (0.05 * w if i > h * 0.7 else 0))
            x1 = int(w - rnd.uniform(0, 0.12) * w - 0.18 * w * (i / h) ** 2)
            a = int(rnd.uniform(150, 235) * (0.55 if rnd.random() < 0.12 else 1))
            d.line([(x0, int(h * 0.05) + i), (x1, int(h * 0.05) + i)], fill=(190, 18, 24, a))
        return im.filter(ImageFilter.GaussianBlur(1.2))

    def lyric(self, text, note, seed):
        S, W, H = self.S, self.W, self.H
        img, layer = self.canvas(), self.canvas()
        d = ImageDraw.Draw(layer)
        han = [i for i, c in enumerate(text) if "一" <= c <= "鿿"]
        cut = han[-2] if len(han) >= 2 else 0
        head, tail = text[:cut].replace(" ", "  "), text[cut:]
        fh, ft = self.f(60), self.f(84)
        wh, wt = d.textlength(head, font=fh), d.textlength(tail, font=ft)
        base = int(H * 0.896)
        x = (W - wh - wt) / 2
        img.alpha_composite(self.brush(int(wt + 46 * S), int(52 * S), seed), (int(x + wh - 20 * S), int(base - 34 * S)))
        d.text((x, base), head, font=fh, fill=GOLD, anchor="ls", stroke_width=int(3 * S), stroke_fill=INK)
        d.text((x + wh, base), tail, font=ft, fill=GOLD, anchor="ls", stroke_width=int(4 * S), stroke_fill=INK)
        if note:
            fn = self.f(36)
            while d.textlength(note, font=fn) > W - 120 * S:
                fn = ImageFont.truetype(font("serif_sc"), fn.size - 2)
                fn.set_variation_by_name("Black")
            y = int(H * 0.971)
            glow = self.canvas()               # a soft white halo makes the white read brighter
            ImageDraw.Draw(glow).text((W / 2, y), note, font=fn, fill=(255, 255, 255, 110), anchor="ms",
                                      stroke_width=int(5 * S), stroke_fill=(255, 255, 255, 70))
            layer.alpha_composite(glow.filter(ImageFilter.GaussianBlur(6 * S)))
            d.text((W / 2, y), note, font=fn, fill=(255, 255, 255, 255), anchor="ms",
                   stroke_width=int(2.5 * S), stroke_fill=(0, 0, 0, 235))
            bh = int(H * 0.18)
            band = Image.new("L", (1, bh))
            for yy in range(bh):
                band.putpixel((0, yy), int(165 * min(1, yy / (bh * 0.58))))
            img.alpha_composite(Image.merge("RGBA", [Image.new("L", (W, bh), 0)] * 3 + [band.resize((W, bh))]), (0, H - bh))
        img.alpha_composite(self.shadowed(layer))
        return img

    def name(self, name, aka, right):
        S, W, H = self.S, self.W, self.H
        img, layer = self.canvas(), self.canvas()
        d = ImageDraw.Draw(layer)
        x = W - int(150 * S) if right else int(150 * S)
        anc = "rs" if right else "ls"          # B's card sits on the right, where B stands
        d.text((x, int(H * 0.8125)), "“%s”" % name, font=self.f(92), fill=GOLD, anchor=anc,
               stroke_width=int(3 * S), stroke_fill=INK)
        if aka:
            d.text((x, int(H * 0.849)), "aka %s" % aka, font=self.f(36, "Bold"), fill=(250, 232, 180, 255), anchor=anc,
                   stroke_width=int(2 * S), stroke_fill=INK)
        img.alpha_composite(self.shadowed(layer))
        return img

    def title(self, a, b):
        S, W, H = self.S, self.W, self.H
        img = self.canvas()
        br = ImageFont.truetype(font("brush"), int(172 * S))
        en = ImageFont.truetype(font("serif_en_bolditalic"), int(150 * S))
        row(img, W // 2, int(H * 0.44), [(a, br, GOLD_GRAD, 8), ("VS", en, RED_GRAD, 8), (b, br, GOLD_GRAD, 8)], gap=30)
        fancy(img, (W // 2, int(H * 0.58)), "FREESTYLE BATTLE", ImageFont.truetype(font("serif_en_bold"), int(64 * S)),
              GOLD_GRAD, stroke=4, shadow=8)
        fancy(img, (W // 2, int(H * 0.655)), "AI生成  仅供娱乐", self.f(40, "Bold"), CREAM, stroke=3, shadow=6)
        return img

    def end(self, l1, l2):
        S, W, H = self.S, self.W, self.H
        img = self.canvas()
        br = ImageFont.truetype(font("brush"), int(150 * S))
        fancy(img, (W // 2, int(H * 0.40)), l1, br, GOLD_GRAD, stroke=8)
        fancy(img, (W // 2, int(H * 0.56)), l2, br, GOLD_GRAD, stroke=8)
        fancy(img, (W // 2, int(H * 0.68)), "FREESTYLE BATTLE  ·  AI生成 仅供娱乐", self.f(36, "Bold"), CREAM, stroke=3, shadow=6)
        return img

    def watermark(self, text):
        S, W = self.S, self.W
        img, layer = self.canvas(), self.canvas()
        ImageDraw.Draw(layer).text((W - int(56 * S), int(80 * S)), text, font=self.f(38, "Bold"), fill=(255, 228, 92, 215),
                                   anchor="rs", stroke_width=int(2 * S), stroke_fill=INK)
        img.alpha_composite(self.shadowed(layer))
        return img


def probe(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height,r_frame_rate",
                        "-show_entries", "format=duration", "-of", "csv=p=0", path], capture_output=True, text=True).stdout.split()
    w, h, fr = r[0].split(",")
    num, den = fr.split("/")
    return int(w), int(h), round(int(num) / int(den)), float(r[1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep")
    ap.add_argument("--src", default=None)
    ap.add_argument("--watermark", default=None)
    ap.add_argument("--test", default=None, help="from:to seconds, renders only that part")
    ap.add_argument("--phone", action="store_true")
    a = ap.parse_args()
    ep, e = a.ep, load_episode(a.ep)
    work = os.path.join(ep, "work")
    tmp = os.path.join(work, "package")
    os.makedirs(tmp, exist_ok=True)
    src = a.src or next(p for p in ("preview/成片_拼接.mp4", "preview/最终剪辑.mp4") if os.path.exists(os.path.join(ep, p)))
    W, H, fps, end = probe(os.path.join(ep, src))
    sh = Sheet(W, H)
    L = jload(os.path.join(work, "lines.json"))
    notes = e.get("notes", {})
    A, B = e["a"], e["b"]
    wm = a.watermark if a.watermark is not None else e.get("watermark", "")

    layers = []
    sh.title(A["name_cn"], B["name_cn"]).save(os.path.join(tmp, "title.png"))
    layers.append(("title.png", 0.0, L[0]["start"] - 0.1, 0.3))
    for who, right in (("a", False), ("b", True)):
        first = next(l for l in L if l["who"] == who and l["n"] == 1)
        second = next((l for l in L if l["who"] == who and l["n"] == 2), first)
        sh.name(e[who]["name_cn"], e[who].get("aka", ""), right).save(os.path.join(tmp, "name_%s.png" % who))
        layers.append(("name_%s.png" % who, first["start"] - 0.08, second["end"] - 0.1, 0.25))
    for i, l in enumerate(L):
        ns = notes.get(l["who"], [])
        note = ns[l["n"] - 1] if l["n"] - 1 < len(ns) else ""
        sh.lyric(l["text"], note, i).save(os.path.join(tmp, "line_%02d.png" % i))
        last = i + 1 == len(L) or L[i + 1]["who"] != l["who"]
        layers.append(("line_%02d.png" % i, l["start"] - 0.05, l["end"] + 0.5 if last else L[i + 1]["start"] - 0.07, 0.0))
    q = e.get("end_question", "下一场|你想看谁的对决？").split("|")
    sh.end(q[0], q[-1]).save(os.path.join(tmp, "end.png"))
    layers.append(("end.png", end - 4.6, end, 0.5))
    if wm:
        sh.watermark(wm).save(os.path.join(tmp, "watermark.png"))
        layers.append(("watermark.png", 0.0, end, 0.0))

    t_from, t_to = (0.0, end)
    if a.test:
        t_from, t_to = [float(x) for x in a.test.split(":")]
    inputs = ["-ss", "%.3f" % t_from, "-t", "%.3f" % (t_to - t_from), "-i", os.path.join(ep, src),
              "-ss", "%.3f" % t_from, "-t", "%.3f" % (t_to - t_from), "-i", os.path.join(work, "music_final.wav")]
    fc = ["[0:v]%s,format=yuv420p,setpts=PTS-STARTPTS[base]" % GRADE]
    last, k = "base", 2
    for idx, (png, st, en, fade) in enumerate(layers):
        st, en = max(st, t_from) - t_from, min(en, t_to) - t_from
        if en - st < 0.05:
            continue
        dur = en - st
        inputs += ["-loop", "1", "-framerate", "30", "-t", "%.3f" % dur, "-i", os.path.join(tmp, png)]
        ch = "[%d:v]format=rgba" % k
        if fade:
            ch += ",fade=t=in:st=0:d=%.2f:alpha=1,fade=t=out:st=%.3f:d=%.2f:alpha=1" % (fade, max(0, dur - fade), fade)
        fc += [ch + ",setpts=PTS-STARTPTS+%.3f/TB[l%d]" % (st, idx), "[%s][l%d]overlay=0:0:eof_action=pass[o%d]" % (last, idx, idx)]
        last, k = "o%d" % idx, k + 1

    # crowd sound: from the Seedance opening / break / ending clips (assembly.json), quietly under the music
    labels = ["[1:a]"]
    asm = os.path.join(work, "assembly.json")
    vol = {"open": 0.35, "break": 0.45, "end": 0.55}
    for j, x in enumerate(jload(asm)["ambience"] if os.path.exists(asm) else []):
        s0, s1 = max(x["song"][0], t_from), min(x["song"][1], t_to)
        if s1 - s0 < 0.2:
            continue
        inputs += ["-ss", "%.3f" % (x["src"] + s0 - x["song"][0]), "-t", "%.3f" % (s1 - s0), "-i", os.path.join(ep, x["clip"])]
        fc.append("[%d:a]aresample=44100,aformat=channel_layouts=stereo,volume=%.2f,afade=t=in:d=0.25,afade=t=out:st=%.3f:d=0.4,"
                  "adelay=%d:all=1[c%d]" % (k, vol[x["kind"]], max(0, s1 - s0 - 0.4), int((s0 - t_from) * 1000), j))
        labels.append("[c%d]" % j)
        k += 1
    fc.append("%samix=inputs=%d:normalize=0:duration=first,alimiter=limit=0.95[aout]" % ("".join(labels), len(labels)))
    os.makedirs(os.path.join(ep, "final"), exist_ok=True)
    out = os.path.join(ep, "final", "%s_成片%s.mp4" % (e["title"], "_测试" if a.test else ""))
    subprocess.run(["ffmpeg", "-y", "-v", "error"] + inputs +
                   ["-filter_complex", ";".join(fc), "-map", "[%s]" % last, "-map", "[aout]",
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-r", str(fps),
                    "-c:a", "aac", "-b:a", "256k", "-movflags", "+faststart", out], check=True)
    print("wrote", out)
    if a.phone:
        phone = out.replace(".mp4", "_手机预览.mp4")
        subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", out, "-vf", "scale=1280:-2", "-r", "30", "-c:v", "libx264",
                        "-preset", "slow", "-b:v", "2000k", "-maxrate", "2400k", "-bufsize", "4000k", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", phone], check=True)
        print("wrote", phone)


if __name__ == "__main__":
    main()
