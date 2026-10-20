"""Build the final narrated + subtitled demo video (v2).

Self-contained:
  1. extract ffmpeg.exe from the cached wheel into imageio-ffmpeg binaries
  2. verify ffmpeg runs on this host (x86_64 emulation on ARM check)
  3. for each slide: png (loop) + its TTS mp3 -> segment mp4 (hard-burned subtitles)
  4. concat all segments -> Antinet_GOAI_track1_demo_v2.mp4
"""
import os, sys, json, re, subprocess, zipfile, imageio_ffmpeg

HERE = os.path.dirname(os.path.abspath(__file__))
WHL = os.path.join(HERE, "_tmp", "iff_win.whl")
BIN = os.path.join(os.path.dirname(imageio_ffmpeg.__file__), "binaries")
EXE = os.path.join(BIN, "ffmpeg-win-x86_64-v7.1.exe")

# ---- 0) extract ffmpeg from wheel if missing ----
if not os.path.exists(EXE):
    print("extracting ffmpeg from wheel ...")
    z = zipfile.ZipFile(WHL)
    nm = [n for n in z.namelist() if n.endswith('.exe') and 'ffmpeg' in n.lower()][0]
    with open(EXE, 'wb') as f:
        f.write(z.read(nm))
    print("extracted", os.path.getsize(EXE), "bytes")

FF = imageio_ffmpeg.get_ffmpeg_exe()
v = subprocess.run([FF, "-version"], capture_output=True, text=True)
head = (v.stdout or v.stderr).splitlines()[0] if (v.stdout or v.stderr) else "NONE"
print("ffmpeg :", FF)
print("version:", head, "| rc =", v.returncode)
if v.returncode != 0:
    print("FFMPEG CANNOT RUN ON THIS HOST (likely x86_64 vs ARM emulation issue)")
    sys.exit(2)

# ---- 1) per-slide segments ----
MAN = os.path.join(HERE, "_tmp", "audio", "manifest.json")
FRM = os.path.join(HERE, "frames_sub")
TMP = os.path.join(HERE, "_tmp", "segs")
os.makedirs(TMP, exist_ok=True)

def dur_of(mp3):
    r = subprocess.run([FF, "-i", mp3], capture_output=True, text=True, stderr=subprocess.STDOUT)
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", r.stdout)
    if m:
        h, mi, s = float(m.group(1)), float(m.group(2)), float(m.group(3))
        return h * 3600 + mi * 60 + s
    return 5.0

man = json.load(open(MAN, encoding="utf-8"))
segs = []
for i, m in enumerate(man, 1):
    mp3 = m["audio"]
    dur = max(dur_of(mp3), 2.0)
    png = os.path.join(FRM, f"page_{i:02d}.png")
    seg = os.path.join(TMP, f"seg_{i:02d}.mp4")
    cmd = [FF, "-y", "-loop", "1", "-i", png, "-i", mp3,
           "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "25",
           "-c:a", "aac", "-b:a", "128k", "-shortest",
           "-movflags", "+faststart", seg]
    rr = subprocess.run(cmd, capture_output=True, text=True, stderr=subprocess.STDOUT)
    if rr.returncode != 0:
        print("SEG FAIL", i, rr.stdout[-800:]); sys.exit(3)
    segs.append(seg)
    print(f"seg {i:02d} dur={dur:.2f}s")

# ---- 2) concat ----
listf = os.path.join(TMP, "list.txt")
with open(listf, "w") as f:
    for s in segs:
        f.write(f"file '{s}'\n")
OUT = os.path.join(HERE, "Antinet_GOAI_track1_demo_v2.mp4")
r2 = subprocess.run([FF, "-y", "-f", "concat", "-safe", "0", "-i", listf,
                    "-c", "copy", OUT], capture_output=True, text=True, stderr=subprocess.STDOUT)
print("concat rc", r2.returncode)
if r2.returncode != 0:
    print(r2.stdout[-1500:])
if os.path.exists(OUT):
    print("OUTPUT", OUT, os.path.getsize(OUT), "bytes")
else:
    print("OUTPUT MISSING")
