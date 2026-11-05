# -*- coding: utf-8 -*-
"""Step 7 - line one Seedance segment up with the song, shot by shot (and render a preview over the music).

usage: python scripts/seedance_align.py <episode_dir> <pack folder or its number> [clip.mp4] [--whole] [--no-preview]

Seedance usually re-sings the vocal we gave it in its own timing (0.1-0.6 s early/late, a little slower or
faster, now and then a doubled word), so the lips follow ITS audio. Each shot is one lyric line, so each shot
gets its own fit: the clip's words are matched to the words of the vocal we sent (by pinyin), and
song_time = rate * clip_time + shift is fitted per shot (rate kept within +-20 %). Shots are laid on the song
timeline and cut at our line starts. --whole places the clip as it is (frame 0 = the pack audio's 0 s).
Writes work/edl/<pack>.json and preview/<pack>_配音乐.mp4.
"""
import difflib
import glob
import os
import subprocess
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import die, jload, jsave  # noqa: E402

LEAD = 0.30          # silence in front of every pack vocal (mouth closed at the start)
_model = None


def model():
    global _model
    if _model is None:
        from faster_whisper import WhisperModel
        _model = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
    return _model


def audio16(path, work):
    tmp = os.path.join(work, "_a16.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path, "-vn", "-ac", "1", "-ar", "16000", tmp], check=True)
    x, _ = sf.read(tmp, dtype="float32")    # numpy in: faster-whisper's own decoder breaks on some av versions
    return x


def words(x, prompt):
    """[(character, start seconds)] - the recogniser's word times spread over the word's characters"""
    segs, _ = model().transcribe(x, language="zh", word_timestamps=True, initial_prompt=prompt,
                                 condition_on_previous_text=False, beam_size=5)
    out = []
    for s in segs:
        for w in s.words:
            chars = [c for c in w.word.strip() if "一" <= c <= "鿿" or c.isdigit()]
            step = (w.end - w.start) / max(1, len(chars))
            out += [(c, w.start + i * step) for i, c in enumerate(chars)]
    return out


def match(a, b):
    """index pairs of matching characters (by pinyin, so homophones count)"""
    from pypinyin import lazy_pinyin
    pa, pb = [lazy_pinyin(c)[0] for c, _ in a], [lazy_pinyin(c)[0] for c, _ in b]
    pairs = []
    for i, j, n in difflib.SequenceMatcher(None, pa, pb, autojunk=False).get_matching_blocks():
        pairs += [(i + k, j + k) for k in range(n)]
    return pairs


def cuts(path, dur):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-vf", "scale=480:-1,select='gt(scene,0.25)',showinfo",
                        "-an", "-f", "null", "-"], capture_output=True, text=True, encoding="utf-8", errors="ignore")
    ts = [float(t.split(":")[1]) for t in r.stderr.split() if t.startswith("pts_time:")]
    return [0.0] + [t for t in ts if 0.3 < t < dur - 0.3] + [dur]


def duration(path):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                                capture_output=True, text=True).stdout)


def pick_clip(pd):
    clips = [c for c in glob.glob(os.path.join(pd, "*.mp4")) if os.path.basename(c) != "2k.mp4"]
    if not clips:
        die("no video in %s - download the generated clip into it" % pd)
    return max(clips, key=os.path.getmtime)


def render(ep, clip, pieces, out, h=720, fps=60):
    w = round(h * 16 / 9 / 2) * 2
    fc, ins = [], []
    for i, p in enumerate(pieces):
        hold = p["song_out"] - p["song_in"] - p["rate"] * (p["src_out"] - p["src_in"])
        pad = ",tpad=stop_mode=clone:stop_duration=%.3f" % hold if hold > 0.01 else ""
        fc.append("[0:v]trim=%.3f:%.3f,setpts=(PTS-STARTPTS)*%.4f,scale=%d:%d:flags=lanczos,setsar=1,fps=%d%s[p%d]"
                  % (p["src_in"], p["src_out"], p["rate"], w, h, fps, pad, i))
        ins.append("[p%d]" % i)
    a0, a1 = pieces[0]["song_in"], pieces[-1]["song_out"]
    fc.append("".join(ins) + "concat=n=%d:v=1:a=0[v]" % len(pieces))
    fc.append("[1:a]atrim=%.3f:%.3f,asetpts=PTS-STARTPTS[a]" % (a0, a1))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", clip, "-i", os.path.join(ep, "音乐_最终.wav"),
                    "-filter_complex", ";".join(fc), "-map", "[v]", "-map", "[a]", "-c:v", "libx264", "-crf", "20",
                    "-preset", "fast", "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart",
                    out], check=True)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 2:
        die("usage: seedance_align.py <episode_dir> <pack> [clip.mp4] [--whole] [--no-preview]")
    ep = args[0]
    work = os.path.join(ep, "work")
    plan = {p["folder"]: p for p in jload(os.path.join(work, "seedance_plan.json"))}
    folder = next((f for f in plan if f.startswith(args[1])), None) or die("no pack starting with " + args[1])
    p = plan[folder]
    if p["kind"] != "sing":
        die("%s has no singing - seedance_assemble.py places it by itself" % folder)
    pd = os.path.join(ep, "seedance", folder)
    clip = os.path.join(pd, args[2]) if len(args) > 2 else pick_clip(pd)
    dur = duration(clip)
    L = jload(os.path.join(work, "lines.json"))
    lines = [l for l in L if l["who"] == p["who"] and p["first"] <= l["n"] <= p["last"]]
    t0 = p["song_t0"]

    if "--whole" in sys.argv:
        end = min(t0 + dur, lines[-1]["end"] + 0.4)
        shots = [{"src": [0.0, end - t0], "rate": 1.0, "shift": t0, "n": 0}]
    else:
        prompt = " ".join(l["text"] for l in lines)
        rw = words(audio16(os.path.join(pd, p["audio"]), work), prompt)          # pack time
        cw = words(audio16(clip, work), prompt)                                   # clip time
        pairs = [(cw[i][1], rw[j][1] + t0) for i, j in match(cw, rw)]           # (clip, song)
        cs = cuts(clip, dur)
        shots = []
        for k in range(len(cs) - 1):
            pk = [(c, s) for c, s in pairs if cs[k] <= c < cs[k + 1] and c > 0.05]  # skip the recogniser's 0.00 snap
            rate, shift = 1.0, None
            if len(pk) >= 4:
                x, y = np.array([c for c, _ in pk]), np.array([s for _, s in pk])
                for _ in range(2):                                            # drop doubled / misheard words
                    r, b0 = np.polyfit(x, y, 1)
                    keep = np.abs(y - (r * x + b0)) < 0.2
                    if keep.sum() >= 4:
                        x, y = x[keep], y[keep]
                r, _ = np.polyfit(x, y, 1)
                rate = float(min(max(r, 0.8), 1.2))                            # beyond +-20 % it shows
                shift = float(np.median(y - rate * x))
            elif pk:
                shift = float(np.median([s - c for c, s in pk]))
            shots.append({"src": [cs[k], cs[k + 1]], "rate": rate, "shift": shift, "n": len(pk)})
        for k, s in enumerate(shots):                                         # a shot without words: borrow a neighbour
            if s["shift"] is None:
                nb = next((x for x in shots[k + 1:] + shots[:k][::-1] if x["shift"] is not None), None)
                s["shift"] = nb["shift"] + (nb["rate"] - 1) * s["src"][0] if nb else t0

    starts = [l["start"] for l in lines]
    song = lambda s, t: s["rate"] * t + s["shift"]
    pieces, song_in = [], song(shots[0], shots[0]["src"][0])
    for k, s in enumerate(shots):
        if k + 1 < len(shots):
            c = s["src"][1]
            lo, hi = song(shots[k + 1], c), song(s, c)   # this shot reaches its last frame at hi, the next starts at lo
            if lo > hi:
                b = lo                                   # a gap: hold this shot's last frame
            else:
                b = min(max(min(starts, key=lambda x: abs(x - hi)) - 0.05, lo), hi)   # cut at our line start
        else:
            b = song(s, s["src"][1])
        pieces.append({"src_in": round(max(0.0, (song_in - s["shift"]) / s["rate"]), 3),
                       "src_out": round(min(dur - 0.02, (b - s["shift"]) / s["rate"]), 3), "rate": round(s["rate"], 4),
                       "song_in": round(song_in, 3), "song_out": round(b, 3)})
        song_in = b
    edl = {"pack": folder, "clip": os.path.relpath(clip, ep), "first_start": lines[0]["start"],
           "shots": shots, "pieces": pieces}
    jsave(os.path.join(work, "edl", folder + ".json"), edl)
    for s, q in zip(shots, pieces):
        print("shot %5.2f-%5.2f  %2d words  rate %.3f  ->  song %6.2f-%6.2f" % (
            s["src"][0], s["src"][1], s["n"], s["rate"], q["song_in"], q["song_out"]))
    if "--no-preview" not in sys.argv:
        out = os.path.join(ep, "preview", folder + "_配音乐.mp4")
        render(ep, clip, pieces, out)
        print("preview:", out)


if __name__ == "__main__":
    main()
