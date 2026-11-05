# -*- coding: utf-8 -*-
"""Step 0 - check the local environment and print exactly what is missing.

usage: python scripts/setup_check.py
"""
import importlib.util
import shutil
import subprocess
import sys

NEED = {"numpy": "numpy", "scipy": "scipy", "soundfile": "soundfile", "PIL": "pillow",
        "demucs": "demucs", "faster_whisper": "faster-whisper", "pypinyin": "pypinyin"}
OPTIONAL = {"mediapipe": "mediapipe", "cv2": "opencv-python"}


def main():
    ok = True
    print("python", sys.version.split()[0], "->", sys.executable)
    if sys.version_info < (3, 9):
        print("  ! Python 3.9+ needed")
        ok = False
    ff = shutil.which("ffmpeg")
    if not ff:
        print("  ! ffmpeg not found (Windows: winget install Gyan.FFmpeg | macOS: brew install ffmpeg)")
        ok = False
    else:
        filters = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
        print("ffmpeg", "OK" if "rubberband" in filters else "found, but WITHOUT rubberband (voice pitch shift needs a full build)")
        if "rubberband" not in filters:
            ok = False
    missing = [pip for mod, pip in NEED.items() if importlib.util.find_spec(mod) is None]
    opt = [pip for mod, pip in OPTIONAL.items() if importlib.util.find_spec(mod) is None]
    if missing:
        ok = False
        print("  ! missing:", " ".join(missing))
        print("    install: %s -m pip install %s   (about 1-2 GB with PyTorch)" % (sys.executable, " ".join(missing)))
    if opt:
        print("  optional (lipcheck.py only):", " ".join(opt))
    print("\nREADY" if ok else "\nNOT READY - fix the lines marked !")
    print("Also needed: a Suno account, a Midjourney account, and a Jimeng (即梦) membership for Seedance 2.5.")
    print("Optional H3 path: a MiniMax API key in the env var MINIMAX_API_KEY.")


if __name__ == "__main__":
    main()
