# -*- coding: utf-8 -*-
"""Step 3b - re-trim the song by hand (for the break / ending), keeping every line time right.

usage: python scripts/retrim.py <episode_dir> --keep 7.36-53.64,63.63-109.8 [--mute 52.6-53.2] [--set b1=62.25]

Times are seconds in the ORIGINAL Suno song (what analyze_song.py printed as "trimming on bar lines").
--keep   the pieces of the song to keep, in order (cut on bar lines or in the pause after a word)
--mute   original-song ranges whose vocal is silenced (Suno ad-libs you want gone, the beat stays)
--set    correct a line's start in original-song seconds, e.g. b1=62.25 when the recogniser was late

Rewrites 音乐_最终.wav, work/vocals_final.wav, work/lines.json, 字幕.srt and work/grid.json.
The splice that sounds seamless (see references/pitfalls.md): keep Suno's own continuous transition
(chant -> first words of the next verse) and jump to the identical spot in the verse a whole number of bars later.
"""
import argparse
import os
import shutil
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_song import cut, pitch, srt_time  # noqa: E402
from common import die, jload, jsave, load_episode  # noqa: E402


def ranges(s):
    return [tuple(float(x) for x in r.split("-")) for r in s.split(",") if r.strip()] if s else []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep")
    ap.add_argument("--keep", required=True)
    ap.add_argument("--mute", default="")
    ap.add_argument("--set", default="", help="line=seconds, comma separated, e.g. b1=62.25")
    a = ap.parse_args()
    ep, e = a.ep, load_episode(a.ep)
    work = os.path.join(ep, "work")
    g = jload(os.path.join(work, "grid.json"))
    L = jload(os.path.join(work, "lines.json"))
    if "orig_start" not in L[0]:
        die("lines.json has no original times - re-run analyze_song.py first")
    keep, mute, bar = ranges(a.keep), ranges(a.mute), g["bar"]
    for kv in filter(None, a.set.split(",")):
        k, v = kv.split("=")
        who, n = k[0], int(k[1:])
        next(l for l in L if l["who"] == who and l["n"] == n)["orig_start"] = float(v)

    offs, acc = [], 0.0
    for s, t in keep:
        offs.append((s, t, acc - s))
        acc += t - s

    def new(t):
        for s, u, o in offs:
            if s - 0.05 <= t <= u + 0.05:
                return t + o
        die("original time %.2f falls in a part you cut - adjust --keep" % t)

    sep = os.path.dirname([os.path.join(r, f) for r, _, fs in os.walk(os.path.join(work, "sep")) for f in fs
                           if f == "vocals.wav" and "htdemucs_ft" not in r][0])
    v, sr = sf.read(os.path.join(sep, "vocals.wav"))
    w = np.ones(len(v))
    f = int(0.05 * sr)
    for s, t in mute:
        i, j = int(s * sr), int(t * sr)
        w[i:j] = 0
        w[max(0, i - f):i] = np.minimum(w[max(0, i - f):i], np.linspace(1, 0, i - max(0, i - f)))
    sf.write(os.path.join(work, "vocals_muted.wav"), v * w[:, None], sr)
    cut(os.path.join(work, "vocals_muted.wav"), keep, os.path.join(work, "vocals_cut.wav"))
    cut(os.path.join(sep, "no_vocals.wav"), keep, os.path.join(work, "inst_cut.wav"))

    a16 = max((l for l in L if l["who"] == "a"), key=lambda l: l["n"])
    b1 = next(l for l in L if l["who"] == "b" and l["n"] == 1)
    a_end, b_start = new(a16["orig_start"]) + bar + 0.3, new(b1["orig_start"]) - 0.1
    pitch(os.path.join(work, "vocals_cut.wav"), e["a"].get("pitch", 0), os.path.join(work, "voc_a.wav"))
    pitch(os.path.join(work, "vocals_cut.wav"), e["b"].get("pitch", 0), os.path.join(work, "voc_b.wav"))
    va, _ = sf.read(os.path.join(work, "voc_a.wav"))
    vb, _ = sf.read(os.path.join(work, "voc_b.wav"))
    base, _ = sf.read(os.path.join(work, "vocals_cut.wav"))
    inst, _ = sf.read(os.path.join(work, "inst_cut.wav"))
    n = min(len(va), len(vb), len(base), len(inst))
    k = int(0.08 * sr)
    wa, wb = np.zeros(n), np.zeros(n)
    ia, ib = int(a_end * sr), int(b_start * sr)
    wa[:ia] = 1
    wa[ia - k:ia] = np.linspace(1, 0, k)
    wb[ib:] = 1
    wb[ib:ib + k] = np.linspace(0, 1, k)
    voc = base[:n] * (1 - wa - wb)[:, None] + va[:n] * wa[:, None] + vb[:n] * wb[:, None]
    sf.write(os.path.join(work, "vocals_final.wav"), voc, sr)
    mix = voc + inst[:n]
    pk = np.abs(mix).max()
    if pk > 0.98:
        mix *= 0.98 / pk
    sf.write(os.path.join(work, "music_final.wav"), mix, sr)
    shutil.copy(os.path.join(work, "music_final.wav"), os.path.join(ep, "音乐_最终.wav"))

    for l in L:
        l["start"], l["bar"] = round(new(l["orig_start"]), 3), round(new(l["orig_bar"]), 3)
    for i, l in enumerate(L):
        nxt = L[i + 1] if i + 1 < len(L) and L[i + 1]["who"] == l["who"] else None
        l["end"] = nxt["start"] if nxt else round(l["start"] + bar, 3)
    jsave(os.path.join(work, "lines.json"), L)
    with open(os.path.join(ep, "字幕.srt"), "w", encoding="utf-8") as fh:
        for i, l in enumerate(L, 1):
            fh.write("%d\n%s --> %s\n%s\n\n" % (i, srt_time(l["start"] - 0.05).replace(".", ","),
                                                srt_time(l["end"] - 0.07).replace(".", ","), l["text"]))
    g.setdefault("keep_auto", g["keep"])
    g["keep"], g["length"] = keep, n / sr
    jsave(os.path.join(work, "grid.json"), g)
    print("kept %s -> %.2fs; A ends %.2f, B starts %.2f" % (a.keep, n / sr, a_end, b_start))


if __name__ == "__main__":
    main()
