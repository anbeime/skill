"""Build final demo video: subtitle-burned frames + edge-tts narration, via real ffmpeg.

Uses the system ffmpeg at C:\E\Infinite_Talk\py312\ffmpeg\bin\ffmpeg.exe (has libass).
Subtitles are already burned into frames_sub/page_NN.png (Pillow). This script only
(1) reads each page's audio duration via ffprobe, (2) makes a per-page clip
(still image + audio), (3) concatenates all clips into one mp4 with AAC audio.
"""
import os, glob, subprocess, json

HERE = os.path.dirname(os.path.abspath(__file__))
FFMPEG = r"C:\E\Infinite_Talk\py312\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"C:\E\Infinite_Talk\py312\ffmpeg\bin\ffprobe.exe"

FRAMES = os.path.join(HERE, "frames_sub")
AUDIO = os.path.join(HERE, "audio")
CLIPS = os.path.join(HERE, "_clips")
os.makedirs(CLIPS, exist_ok=True)
OUT = os.path.join(HERE, "Antinet_GOAI_track1_demo_v2.mp4")

def probe_dur(path):
    out = subprocess.check_output([
        FFPROBE, "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=nw=1:nk=1", path
    ]).decode().strip()
    return float(out)

def main():
    frames = sorted(glob.glob(os.path.join(FRAMES, "page_*.png")))
    clips = []
    for i, fr in enumerate(frames, 1):
        aud = os.path.join(AUDIO, f"page_{i:02d}.mp3")
        if not os.path.exists(aud):
            print(f"  ! missing audio for page {i:02d}, skip")
            continue
        dur = probe_dur(aud)
        # small pad so last word isn't cut; cap at 60s (longest narration ~43s)
        dur = min(dur + 0.4, 60.0)
        clip = os.path.join(CLIPS, f"clip_{i:02d}.mp4")
        cmd = [
            FFMPEG, "-y",
            "-loop", "1", "-i", fr,
            "-i", aud,
            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "25",
            "-c:a", "aac", "-b:a", "192k",
            "-t", f"{dur:.3f}", "-shortest",
            "-movflags", "+faststart",
            clip,
        ]
        subprocess.run(cmd, check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        clips.append(clip)
        print(f"  page {i:02d}: {dur:.2f}s -> {os.path.getsize(clip)//1024} KB")

    # concat via filter_complex (re-encode, smooth boundaries)
    with open(os.path.join(HERE, "_clips.txt"), "w", encoding="utf-8") as f:
        for c in clips:
            f.write(f"file '{c.replace(chr(92), '/')}'\n")

    # build filter chain: [0:v][0:a][1:v][1:a]... concat=n=18:v=1:a=1
    n = len(clips)
    inp = []
    for c in clips:
        inp += ["-i", c]
    filt = "".join(f"[{k}:v][{k}:a]" for k in range(n)) + f"concat=n={n}:v=1:a=1[v][a]"
    cmd = [FFMPEG, "-y"] + inp + [
        "-filter_complex", filt,
        "-map", "[v]", "-map", "[a]",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "25",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        OUT,
    ]
    print(f"concatenating {n} clips -> {OUT}")
    subprocess.run(cmd, check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sz = os.path.getsize(OUT)
    print(f"DONE: {OUT} ({sz//1024//1024} MB)")

if __name__ == "__main__":
    main()
