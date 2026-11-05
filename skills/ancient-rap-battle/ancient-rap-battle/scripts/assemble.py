# -*- coding: utf-8 -*-
"""Step 8 - assemble a draft from the accepted takes (work/edl.json + work/picks.json + work/shifts.json).

usage: python scripts/assemble.py <episode_dir> [--from 0] [--to END] [--out preview/草稿.mp4]
  * lip-sync clips are placed so their audio lines up with the song; if a clip is too short the LAST FRAME IS HELD -
    never slide it earlier, that breaks the lip sync
  * work/shifts.json: seconds to play a clip's picture earlier (H3 started the song late / the mouth trails)
  * a clip without an accepted take shows as dark grey, so the rhythm is visible before everything exists
  * picks.json may name any take: {"A07": 2}; edl.json may use "B_REACT@1" style ids to force a take as a cutaway
"""
import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import jload  # noqa: E402

W, H, FPS = 1344, 768, 24


def duration(f):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep")
    ap.add_argument("--from", dest="t0", type=float, default=0.0)
    ap.add_argument("--to", dest="t1", type=float, default=None)
    ap.add_argument("--out", default="preview/草稿.mp4")
    a = ap.parse_args()
    ep = a.ep
    work = os.path.join(ep, "work")
    edl = jload(os.path.join(work, "edl.json"))
    clips = {c["id"]: c for c in jload(os.path.join(work, "clips.json"))}
    picks = jload(os.path.join(work, "picks.json")) if os.path.exists(os.path.join(work, "picks.json")) else {}
    shifts = jload(os.path.join(work, "shifts.json")) if os.path.exists(os.path.join(work, "shifts.json")) else {}
    t_end = a.t1 if a.t1 is not None else edl[-1]["t1"]
    inputs, filters, report, n = [], [], [], 0
    for x in edl:
        st, en = max(x["t0"], a.t0), min(x["t1"], t_end)
        if en - st < 0.02:
            continue
        dur = en - st
        cid, take = x["clip"], None
        if "@" in cid:
            cid, take = cid.split("@")
        take = take or picks.get(cid)
        f = os.path.join(ep, "clips", "%s_t%s.mp4" % (cid, take)) if take else None
        if f and os.path.exists(f):
            c = clips[cid]
            if x["in"] is None:                       # lip-sync: clip time 0 = audio start (minus lead)
                src = x["t0"] - (c["audio"][0] - c.get("lead", 0.0)) + shifts.get(cid, 0.0) + (st - x["t0"])
            else:
                src = x["in"] + (st - x["t0"])
            src = max(0.0, src)
            pad, clen = 0.0, duration(f)
            if src + dur > clen - 0.04:
                if x["in"] is None:
                    pad = src + dur - (clen - 0.04)
                else:
                    src = max(0.0, clen - 0.04 - dur)
            inputs += ["-ss", "%.3f" % src, "-t", "%.3f" % (dur + 0.2), "-i", f]
            filters.append("[%d:v]tpad=stop_mode=clone:stop_duration=%.3f,trim=0:%.3f,setpts=PTS-STARTPTS,fps=%d,"
                           "scale=%d:%d:force_original_aspect_ratio=increase,crop=%d:%d,setsar=1[v%d]"
                           % (n, pad + 0.1, dur, FPS, W, H, W, H, n))
            report.append("%6.2f-%6.2f %-8s t%s @%.2f" % (st, en, cid, take, src))
        else:
            inputs += ["-f", "lavfi", "-t", "%.3f" % dur, "-i", "color=c=0x202020:s=%dx%d:r=%d" % (W, H, FPS)]
            filters.append("[%d:v]setsar=1[v%d]" % (n, n))
            report.append("%6.2f-%6.2f %-8s (not generated yet)" % (st, en, cid))
        n += 1
    inputs += ["-ss", "%.3f" % a.t0, "-t", "%.3f" % (t_end - a.t0), "-i", os.path.join(work, "music_final.wav")]
    fc = ";".join(filters) + ";" + "".join("[v%d]" % i for i in range(n)) + "concat=n=%d:v=1:a=0[v]" % n
    out = os.path.join(ep, a.out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-v", "error"] + inputs + ["-filter_complex", fc, "-map", "[v]", "-map", "%d:a" % n,
                    "-c:v", "libx264", "-crf", "20", "-preset", "fast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
                    "-shortest", out], check=True)
    print("\n".join(report))
    print("wrote", out)


if __name__ == "__main__":
    main()
