# -*- coding: utf-8 -*-
"""Step 8 - join every Seedance segment over the final music: opening, A's packs, break, B's packs, ending.

usage: python scripts/seedance_assemble.py <episode_dir> [--2k] [--h 1440] [--fps 60] [--crf 18] [--from S --to S]

Singing packs need work/edl/<pack>.json (seedance_align.py). The opening, the break and the ending fill the gaps
on their own (opening: its last seconds up to A's first line; break: up to just before B's first word;
ending: from the start of the clip). Consecutive singing packs hand over at the next pack's first line start.
--2k uses <pack>/2k.mp4 (即梦「超清」of the SAME take) when its audio matches the aligned clip.
Writes preview/成片_拼接.mp4 - package.py turns it into the film.
"""
import glob
import os
import subprocess
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import die, jload, jsave  # noqa: E402
from seedance_align import duration, pick_clip  # noqa: E402


def opt(name, default):
    return float(sys.argv[sys.argv.index(name) + 1]) if name in sys.argv else default


def same_take(a, b, work):
    def au(p, t):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", p, "-vn", "-ac", "1", "-ar", "8000", t], check=True)
        return sf.read(t)[0]
    x, y = au(a, os.path.join(work, "_x.wav")), au(b, os.path.join(work, "_y.wav"))
    n = min(len(x), len(y))
    return n > 8000 and np.corrcoef(x[:n], y[:n])[0, 1] > 0.95


def main():
    if len(sys.argv) < 2:
        die("usage: seedance_assemble.py <episode_dir> [--2k]")
    ep = sys.argv[1]
    work = os.path.join(ep, "work")
    plan = jload(os.path.join(work, "seedance_plan.json"))
    L = jload(os.path.join(work, "lines.json"))
    song_end = sf.info(os.path.join(ep, "音乐_最终.wav")).duration
    segs = []
    for p in plan:
        pd = os.path.join(ep, "seedance", p["folder"])
        if p["kind"] == "sing":
            f = os.path.join(work, "edl", p["folder"] + ".json")
            if not os.path.exists(f):
                die("no alignment for %s - run seedance_align.py on it" % p["folder"])
            e = jload(f)
            e["clip"] = os.path.join(ep, e["clip"])
        else:
            clips = glob.glob(os.path.join(pd, "*.mp4"))
            if not clips:
                print("note: no video for %s yet - skipped" % p["folder"])
                continue
            k2 = os.path.join(pd, "2k.mp4")
            others = [c for c in clips if os.path.basename(c) != "2k.mp4"]
            if "--2k" in sys.argv and os.path.exists(k2) or not others:
                clip = k2
            else:
                clip = pick_clip(pd)
            e = {"clip": clip, "pieces": None}
        if "--2k" in sys.argv and p["kind"] == "sing":
            k2 = os.path.join(pd, "2k.mp4")
            if os.path.exists(k2):
                if same_take(e["clip"], k2, work):
                    e["clip"] = k2
                else:
                    print("WARNING: %s/2k.mp4 is not the aligned take - using the aligned one" % p["folder"])
        e["kind"], e["folder"] = p["kind"], p["folder"]
        segs.append(e)

    # fill in the opening / break / ending around the singing packs
    sing = [s for s in segs if s["kind"] == "sing"]
    b1 = next(l for l in L if l["who"] == "b" and l["n"] == 1)
    for i, s in enumerate(segs):
        if s["kind"] == "sing":
            continue
        dur = duration(s["clip"])
        if s["kind"] == "open":
            a, b = 0.0, sing[0]["pieces"][0]["song_in"]
            src = (max(0.0, dur - (b - a)), dur)
        elif s["kind"] == "break":
            prev = max((x for x in sing if x["first_start"] < b1["start"]), key=lambda x: x["first_start"])
            a, b = prev["pieces"][-1]["song_out"], b1["start"] - 0.1
            src = (max(0.0, dur - (b - a)), dur)
        else:
            a, b = sing[-1]["pieces"][-1]["song_out"], song_end
            src = (min(0.3, dur), min(dur, 0.3 + b - a))
        s["pieces"] = [{"src_in": src[0], "src_out": src[1], "song_in": a, "song_out": b, "rate": 1.0}]
        s["first_start"] = None
    for s in segs:
        s["lo"], s["hi"] = s["pieces"][0]["song_in"], s["pieces"][-1]["song_out"]

    bounds = [opt("--from", segs[0]["lo"])]
    for a, b in zip(segs, segs[1:]):
        if b["first_start"] is None:                      # into the break / ending: they start where the singing ends
            bounds.append(b["lo"])
        elif a["first_start"] is None:                    # out of the opening / break: they run up to their own end
            bounds.append(min(max(a["hi"], b["lo"]), b["hi"]))
        else:
            want = b["first_start"] - 0.05
            bounds.append(min(max(want, b["lo"]), a["hi"]) if b["lo"] <= a["hi"] else b["lo"])
    bounds.append(opt("--to", segs[-1]["hi"]))

    amb = []                                              # for package.py: where the crowd sound of the
    for i, e in enumerate(segs):                          # opening / break / ending clips goes
        if e["kind"] != "sing":
            p = e["pieces"][0]
            a, b = bounds[i], bounds[i + 1]
            amb.append({"kind": e["kind"], "clip": os.path.relpath(e["clip"], ep),
                        "src": round(max(0.0, p["src_in"] + (a - p["song_in"])), 3), "song": [round(a, 3), round(b, 3)]})
    jsave(os.path.join(work, "assembly.json"), {"bounds": bounds, "ambience": amb})

    h = int(opt("--h", 1440))
    w = round(h * 16 / 9 / 2) * 2
    fps, crf = int(opt("--fps", 60)), str(int(opt("--crf", 18)))
    fc, labels, inputs = [], [], []
    for i, e in enumerate(segs):
        inputs += ["-i", e["clip"]]
        s0, s1 = bounds[i], bounds[i + 1]
        for j, p in enumerate(e["pieces"]):
            rate = p.get("rate", 1.0)
            a, b = max(p["song_in"], s0), min(p["song_out"], s1)
            if p is e["pieces"][-1] and s1 > p["song_out"]:
                b = s1                                    # hold the last frame up to the hand-over
            if p is e["pieces"][0] and s0 < p["song_in"]:
                a = s0
            if b - a < 0.02:
                continue
            src_a = max(0.0, p["src_in"] + (a - p["song_in"]) / rate)
            src_b = min(p["src_in"] + (b - p["song_in"]) / rate, p["src_out"])
            hold = (b - a) - rate * (src_b - src_a)
            pad = ",tpad=stop_mode=clone:stop_duration=%.3f" % hold if hold > 0.01 else ""
            lab = "v%d_%d" % (i, j)
            fc.append("[%d:v]trim=%.3f:%.3f,setpts=(PTS-STARTPTS)*%.4f,scale=%d:%d:flags=lanczos,setsar=1,fps=%d%s,"
                      "trim=duration=%.3f[%s]" % (i, src_a, src_b, rate, w, h, fps, pad, b - a, lab))
            labels.append("[%s]" % lab)
    fc.append("".join(labels) + "concat=n=%d:v=1:a=0[v]" % len(labels))
    fc.append("[%d:a]atrim=%.3f:%.3f,asetpts=PTS-STARTPTS[a]" % (len(segs), bounds[0], bounds[-1]))
    out = os.path.join(ep, "preview", "成片_拼接.mp4")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y"] + inputs + ["-i", os.path.join(ep, "音乐_最终.wav"),
                    "-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", crf,
                    "-preset", "medium", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                    out], check=True)
    print("hand-overs", " ".join("%.2f" % b for b in bounds), "->", out)


if __name__ == "__main__":
    main()
