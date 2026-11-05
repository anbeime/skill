# -*- coding: utf-8 -*-
"""Step 3 - analyze and trim the Suno song (fully automatic).

usage: python scripts/analyze_song.py <episode_dir> [--intro-bars 1] [--outro-bars 3]

1. split vocals / instrumental (demucs)
2. word timestamps on the vocal (faster-whisper; the text is mostly homophones, only the times are used)
3. beat grid from the instrumental
4. find both verses and every line start (one lyric line = one bar)
5. trim long intro / interlude / outro on bar lines (all tracks in sync)
6. pitch-shift each verse's vocal (episode a.pitch / b.pitch, semitones) so the two rappers sound different
7. write the final music, the final vocal (used for lip sync), lines.json and the subtitle file
"""
import argparse
import difflib
import glob
import os
import shutil
import subprocess
import sys

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import P, die, jload, jsave, load_episode  # noqa: E402


def separate(song, work):
    out = glob.glob(os.path.join(work, "sep", "htdemucs", "*", "vocals.wav"))
    if not out:
        print("[1/7] separating vocals (demucs, ~1-3 min)...")
        subprocess.run([sys.executable, "-m", "demucs", "--two-stems=vocals", "-o", os.path.join(work, "sep"), song],
                       check=True)
        out = glob.glob(os.path.join(work, "sep", "htdemucs", "*", "vocals.wav"))
    v = out[0]
    return v, os.path.join(os.path.dirname(v), "no_vocals.wav")


def transcribe(vocals, ep, e):
    path = P(ep, "work", "asr.json")
    if os.path.exists(path):
        return jload(path)
    print("[2/7] word timestamps (faster-whisper large-v3-turbo, ~2-5 min on CPU)...")
    from faster_whisper import WhisperModel
    x, sr = sf.read(vocals)
    x = x.mean(1) if x.ndim > 1 else x
    x = resample_poly(x, 16000, sr).astype(np.float32)
    prompt = " ".join([e["a"]["name_cn"], e["b"]["name_cn"]] + e["lyrics"]["a"][:3] + e["lyrics"]["b"][:3])[:200]
    m = WhisperModel("large-v3-turbo", device="cpu", compute_type="int8")
    segs, _ = m.transcribe(x, language="zh", word_timestamps=True, initial_prompt=prompt,
                           condition_on_previous_text=False, beam_size=5)
    words = [{"s": w.start, "e": w.end, "w": w.word} for s in segs for w in s.words]
    jsave(path, words)
    return words


def beat_grid(inst):
    print("[3/7] beat grid...")
    x, sr = sf.read(inst)
    x = x.mean(1) if x.ndim > 1 else x
    x = resample_poly(x, 1, 4)
    sr //= 4
    hop, n = int(sr / 200), 1024
    fr = np.lib.stride_tricks.sliding_window_view(x, n)[::hop] * np.hanning(n)
    sp = np.log1p(np.abs(np.fft.rfft(fr, axis=1)))
    on = np.maximum(np.diff(sp, axis=0), 0).sum(1)
    on = np.maximum(on - np.convolve(on, np.ones(40) / 40, "same"), 0)
    fps = sr / hop

    def best(bpms):
        b = (-1, 0, 0)
        for bpm in bpms:
            p = 60 / bpm * fps
            k = np.arange(0, len(on) / p - 1)
            for ph in range(int(p)):
                s = on[(ph + k * p).astype(int)].sum()
                if s > b[0]:
                    b = (s, bpm, ph / fps)
        return b
    _, bpm, _ = best(np.arange(70, 120, 0.1))
    _, bpm, b0 = best(np.arange(bpm - 0.15, bpm + 0.15, 0.01))
    return float(bpm), float(b0)


def han(s):
    return "".join(ch for ch in s if "一" <= ch <= "鿿")


def find_verse(words, t_from, lyrics, beat, b0, bar):
    """where the verse starts = where the recognized text best matches its first 4 lyric lines
    (the recognizer writes homophones and hallucinates in instrumental parts, but many characters still match),
    then one bar per lyric line from that anchor"""
    n_lines = len(lyrics)
    target = han("".join(lyrics[:4]))
    ws = [w for w in words if w["s"] >= t_from]
    best = (0.0, None)
    for i, w in enumerate(ws):
        window = han("".join(x["w"] for x in ws[i:] if x["s"] < w["s"] + 4 * bar))
        if len(window) < len(target) * 0.4:
            continue
        sm = difflib.SequenceMatcher(None, window, target)
        score = sum(b.size for b in sm.get_matching_blocks()) / len(target)
        if score > best[0]:
            best = (score, w["s"])
    t0 = best[1]
    if t0 is None or best[0] < 0.25:
        die("could not find the verse starting with '%s' after %.1fs - check the song sings the lyrics" % (lyrics[0], t_from))
    print("      verse '%s...' found at %.2fs (text match %.0f%%)" % (lyrics[0][:6], t0, best[0] * 100))
    k = np.ceil((t0 - 0.25 - b0) / beat)
    anchor = b0 + k * beat
    lines = []
    for i in range(n_lines):
        bt = anchor + i * bar
        ws = [w for w in words if bt - 0.13 <= w["s"] < bt + bar - 0.13]
        # Suno lets the previous line's last syllable spill up to ~0.15 s past the bar line: skip words up to
        # and including the last one (among the first three, starting before bar + 0.15) that is that syllable
        prev_tail = han(lyrics[i - 1])[-1:] if i else ""
        k = 0
        for j, w in enumerate(ws[:3]):
            if prev_tail and w["s"] < bt + 0.15 and han(w["w"])[-1:] == prev_tail:
                k = j + 1
        ws = ws[k:] if k < len(ws) else ws
        lines.append({"bar": round(bt, 3), "start": round(min((w["s"] for w in ws), default=bt), 3),
                      "heard": "".join(w["w"] for w in ws).strip()})
    return anchor, lines


def cut(path, keep, out, xf=0.04, fade_in=0.03, fade_out=1.5):
    x, sr = sf.read(path)
    if x.ndim == 1:
        x = x[:, None]
    y = x[int(round(keep[0][0] * sr)):int(round(keep[0][1] * sr))].copy()
    for i, (a, b) in enumerate(keep[1:]):
        h = int(xf * sr / 2)
        n = 2 * h
        prev_end = int(round(keep[i][1] * sr))
        y = np.concatenate([y, x[prev_end:prev_end + h]])
        p = x[int(round(a * sr)) - h:int(round(b * sr))]
        t = np.linspace(0, np.pi / 2, n)[:, None]
        y = np.concatenate([y[:-n], y[-n:] * np.cos(t) + p[:n] * np.sin(t), p[n:]])
    fi, fo = int(fade_in * sr), int(fade_out * sr)
    y[:fi] *= np.linspace(0, 1, fi)[:, None]
    y[-fo:] *= np.linspace(1, 0, fo)[:, None]
    sf.write(out, y, sr)
    return sr


def pitch(src, semis, out):
    if not semis:
        shutil.copy(src, out)
        return
    ratio = 2 ** (semis / 12)
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-af",
                    "rubberband=pitch=%.6f:formant=shifted:pitchq=quality:transients=crisp" % ratio, out], check=True)


def srt_time(t):
    h, m, s = int(t // 3600), int(t % 3600 // 60), t % 60
    return "%02d:%02d:%06.3f" % (h, m, s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep")
    ap.add_argument("--intro-bars", type=int, default=1, help="bars kept before the first verse")
    ap.add_argument("--outro-bars", type=int, default=3, help="bars kept after the second verse (crowd chant)")
    a = ap.parse_args()
    ep, e = a.ep, load_episode(a.ep)
    song = os.path.join(ep, e.get("song", "song.mp3"))
    if not os.path.exists(song):
        die("put the Suno song at " + song)
    work = os.path.join(ep, "work")
    os.makedirs(work, exist_ok=True)
    na, nb = len(e["lyrics"]["a"]), len(e["lyrics"]["b"])

    vocals, inst = separate(song, work)
    words = transcribe(vocals, ep, e)
    bpm, b0 = beat_grid(inst)
    beat, bar = 60 / bpm, 240 / bpm
    print("      %.2f BPM, one bar = %.3fs" % (bpm, bar))

    print("[4/7] finding verses and line starts...")
    aA, la = find_verse(words, 0.0, e["lyrics"]["a"], beat, b0, bar)
    aB, lb = find_verse(words, aA + (na - 1) * bar, e["lyrics"]["b"], beat, b0, bar)
    length = sf.info(vocals).duration
    keep = [(max(0.0, aA - a.intro_bars * bar), aA + (na + 1) * bar),
            (aB - bar, min(length - 0.05, aB + (nb + a.outro_bars) * bar))]
    if keep[1][0] <= keep[0][1]:
        keep = [(keep[0][0], keep[1][1])]
    offs, acc = [], 0.0
    for s, t in keep:
        offs.append((s, t, acc - s))
        acc += t - s

    def new(t):
        for s, u, o in offs:
            if s - 0.6 <= t <= u + 0.6:
                return t + o
        die("time %.2f is outside the kept song" % t)

    print("[5/7] trimming on bar lines: %s -> %.1fs" % (", ".join("%.1f-%.1f" % k for k in keep), acc))
    sr = cut(vocals, keep, os.path.join(work, "vocals_cut.wav"))
    cut(inst, keep, os.path.join(work, "inst_cut.wav"))

    print("[6/7] pitch-shifting the two voices (a %+d, b %+d semitones)..." % (e["a"].get("pitch", 0), e["b"].get("pitch", 0)))
    pitch(os.path.join(work, "vocals_cut.wav"), e["a"].get("pitch", 0), os.path.join(work, "voc_a.wav"))
    pitch(os.path.join(work, "vocals_cut.wav"), e["b"].get("pitch", 0), os.path.join(work, "voc_b.wav"))
    base, _ = sf.read(os.path.join(work, "vocals_cut.wav"))
    va, _ = sf.read(os.path.join(work, "voc_a.wav"))
    vb, _ = sf.read(os.path.join(work, "voc_b.wav"))
    inst_c, _ = sf.read(os.path.join(work, "inst_cut.wav"))
    n = min(len(base), len(va), len(vb), len(inst_c))
    base, va, vb, inst_c = base[:n], va[:n], vb[:n], inst_c[:n]
    wa, wb = np.zeros(n), np.zeros(n)

    def ramp(w, t0, t1, x=0.08):
        i0, i1, k = max(0, int(t0 * sr)), min(n, int(t1 * sr)), int(x * sr)
        w[i0:i1] = 1
        w[i0:i0 + k] = np.linspace(0, 1, k)
        w[i1 - k:i1] = np.linspace(1, 0, k)
    ramp(wa, 0, new(aA + na * bar) + 0.3)
    ramp(wb, new(aB) - 0.4, new(aB + nb * bar) + 0.3)
    voc = base * (1 - wa - wb)[:, None] + va * wa[:, None] + vb * wb[:, None]
    sf.write(os.path.join(work, "vocals_final.wav"), voc, sr)
    mix = voc + inst_c
    pk = np.abs(mix).max()
    if pk > 0.98:
        mix *= 0.98 / pk
    sf.write(os.path.join(work, "music_final.wav"), mix, sr)
    shutil.copy(os.path.join(work, "music_final.wav"), os.path.join(ep, "音乐_最终.wav"))

    print("[7/7] lines and subtitles...")
    lines = []
    for who, ls, texts in (("a", la, e["lyrics"]["a"]), ("b", lb, e["lyrics"]["b"])):
        for i, (l, txt) in enumerate(zip(ls, texts)):
            st = new(l["start"])
            en = new(ls[i + 1]["start"]) if i + 1 < len(ls) else st + bar
            lines.append({"who": who, "n": i + 1, "text": txt, "start": round(st, 3), "end": round(en, 3),
                          "bar": round(new(l["bar"]), 3), "heard": l["heard"],
                          "orig_start": l["start"], "orig_bar": l["bar"]})     # times in the untrimmed song (retrim.py)
    jsave(os.path.join(work, "lines.json"), lines)
    with open(os.path.join(ep, "字幕.srt"), "w", encoding="utf-8") as f:
        for i, l in enumerate(lines, 1):
            f.write("%d\n%s --> %s\n%s\n\n" % (i, srt_time(l["start"] - 0.05).replace(".", ","),
                                               srt_time(l["end"] - 0.07).replace(".", ","), l["text"]))
    jsave(os.path.join(work, "grid.json"), {"bpm": bpm, "beat0": b0, "bar": bar, "keep": keep, "length": acc,
                                            "verse_a": aA, "verse_b": aB})
    print("\nline check (time | what the recognizer heard | lyric) - the heard text is homophones, compare lengths:")
    for l in lines:
        print("%s%02d %6.2f | %-22s | %s" % (l["who"].upper(), l["n"], l["start"], l["heard"][:22], l["text"]))
    print("\nwrote 音乐_最终.wav (%.1fs), 字幕.srt, work/lines.json" % acc)


if __name__ == "__main__":
    main()
