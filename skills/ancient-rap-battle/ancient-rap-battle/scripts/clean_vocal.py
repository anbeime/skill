# -*- coding: utf-8 -*-
"""Step 6a - a cleaner, clearer vocal for lip sync (never used in the final mix).

usage: python scripts/clean_vocal.py <episode_dir>

htdemucs_ft separation (less music bleed than the default model) -> the same trim as 音乐_最终.wav
(work/grid.json keep) -> high-pass, less mud, presence boost, gentle compression, -16 LUFS.
Writes work/vocals_clean.wav, which seedance_packs.py cuts into the per-segment vocals.
"""
import glob
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from analyze_song import cut  # noqa: E402
from common import die, jload, load_episode  # noqa: E402


def main():
    if len(sys.argv) < 2:
        die("usage: clean_vocal.py <episode_dir>")
    ep = sys.argv[1]
    e = load_episode(ep)
    work = os.path.join(ep, "work")
    g = jload(os.path.join(work, "grid.json"))
    out = glob.glob(os.path.join(work, "sep_ft", "htdemucs_ft", "*", "vocals.wav"))
    if not out:
        print("separating with htdemucs_ft (slower, ~5-10 min on CPU)...")
        subprocess.run([sys.executable, "-m", "demucs", "-n", "htdemucs_ft", "--two-stems=vocals", "-o",
                        os.path.join(work, "sep_ft"), os.path.join(ep, e.get("song", "song.mp3"))], check=True)
        out = glob.glob(os.path.join(work, "sep_ft", "htdemucs_ft", "*", "vocals.wav"))
    tmp = os.path.join(work, "vocals_ft_cut.wav")
    cut(out[0], g["keep"], tmp)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-af",
                    "highpass=f=90,equalizer=f=250:t=q:w=1:g=-2,equalizer=f=3200:t=q:w=1.2:g=3,"
                    "acompressor=threshold=-20dB:ratio=3:attack=5:release=80,loudnorm=I=-16:TP=-1.5:LRA=7",
                    "-ar", "44100", os.path.join(work, "vocals_clean.wav")], check=True)
    print("wrote work/vocals_clean.wav")


if __name__ == "__main__":
    main()
