# -*- coding: utf-8 -*-
"""Does a generated clip still carry OUR vocal? (H3 lip-syncs to the soundtrack it outputs.)

Three outcomes seen in practice:
  * identical (corr ~0.98)                       -> lips match the song
  * identical but started late by 0.1-0.3 s      -> usable: play the picture that much earlier (shift)
  * H3 re-sang part or all of it (corr drops)    -> only the part before the drift is usable; otherwise re-roll
usage: python scripts/qa.py <clip.mp4> <sent_audio.mp3>
"""
import subprocess
import sys

import numpy as np


def load(p):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-ac", "1", "-ar", "8000", "-f", "f32le", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32)


def env(x, h=80):                                   # 10 ms log-energy envelope
    n = len(x) // h
    return np.log(np.sqrt((x[:n * h].reshape(n, h) ** 2).mean(1)) + 1e-4)


def analyze(video, ref):
    a, b = env(load(video)), env(load(ref))
    if len(a) < 50 or len(b) < 50:
        return {"ok": False, "reason": "no audio"}
    L = min(len(b), len(a) - 60)
    best = (-1.0, 0)
    for lag in range(-20, 61):                      # -0.2 .. +0.6 s: H3 sometimes starts the song late
        if lag < 0 or lag + L > len(a):
            continue
        c = float(np.corrcoef(a[lag:lag + L], b[:L])[0, 1])
        if c > best[0]:
            best = (c, lag)
    corr, lag = best
    ok_until = L / 100
    for s in range(0, L - 50, 50):                  # 1 s windows every 0.5 s at that offset
        wa, wb = a[lag + s:lag + s + 100], b[s:s + 100]
        if len(wb) < 60 or wb.std() < 0.3:
            continue
        if np.corrcoef(wa[:len(wb)], wb)[0, 1] < 0.9:
            ok_until = s / 100
            break
    return {"ok": corr >= 0.85 and ok_until >= min(L / 100 - 0.3, 2.3), "corr": round(corr, 3),
            "shift": round(lag / 100, 2), "ok_until": round(ok_until, 2), "ref_len": round(L / 100, 2)}


if __name__ == "__main__":
    r = analyze(sys.argv[1], sys.argv[2])
    print(r)
    if r.get("ok"):
        print("OK" + (" - play the picture %.2fs earlier" % r["shift"] if r["shift"] > 0.03 else ""))
    else:
        print("drift: usable only for the first %.1fs" % r.get("ok_until", 0))
