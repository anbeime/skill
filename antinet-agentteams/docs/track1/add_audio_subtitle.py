"""Enhance Antinet_GOAI_track1_demo.mp4 with TTS audio + burned-in subtitles.

Pipeline:
  1. parse deck_track1.md -> per-page narration text (title + bullets, spoken-style,
     NO fabricated facts: only rephrases existing deck content)
  2. call live backend POST /api/speech/tts/speak-bytes (edge-tts Xiaoxiao) -> per-page mp3
  3. use existing frames/ (from render_video.py) or re-render, stitch video with
     per-page duration = audio duration + 0.4s tail, crossfade between pages
  4. burn subtitles (per-page .srt via subtitles filter, with CJK font)
  5. mux all mp3s into one audio track -> final mp4 with sound + subtitles
"""
import os, re, json, subprocess, shutil, urllib.request, urllib.error, sys

# Force UTF-8 stdout on Windows (gbk console can't encode some CJK/punct chars)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "deck_track1.md")
FRAMES = os.path.join(HERE, "frames")
AUDIO = os.path.join(HERE, "audio")
OUT = os.path.join(HERE, "Antinet_GOAI_track1_demo_v2.mp4")
TTS_ENDPOINT = "http://localhost:8000/api/speech/tts/speak-bytes"
VOICE = "zh-CN-XiaoxiaoNeural"

# Reuse an existing ffmpeg binary on this machine (no download/install needed).
# Located via search: C:\E\Infinite_Talk\py312\ffmpeg\bin\ffmpeg.exe (gyan.dev essentials build,
# includes libx264/libass/fontconfig/freetype for subtitle burn-in).
FF = r"C:\E\Infinite_Talk\py312\ffmpeg\bin\ffmpeg.exe"
FFPROBE = r"C:\E\Infinite_Talk\py312\ffmpeg\bin\ffprobe.exe"

os.makedirs(AUDIO, exist_ok=True)

# ---- parse deck ----
with open(SRC, encoding="utf-8") as f:
    raw = f.read()
blocks = re.split(r"\n## ", raw)
slides = []
for block in blocks[1:]:
    lines = block.splitlines()
    m = re.match(r"^(P\d+)\s*[·•-]?\s*(.+)$", lines[0].strip())
    if not m:
        continue
    pid, title = m.group(1), m.group(2).strip()
    bullets = [ln[2:].strip() for ln in lines[1:] if ln.strip().startswith("- ")]
    slides.append((pid, title, bullets))

print(f"parsed {len(slides)} slides")

# ---- narration text per page (spoken, derived from deck only) ----
def narration(pid, title, bullets):
    parts = [title.replace("·", " ").strip()]
    for b in bullets[:5]:
        b = re.sub(r"\*\*(.+?)\*\*", r"\1", b)
        b = re.sub(r"[（(].*?[)）]", "", b)  # drop paren remarks for cleaner speech
        if b.strip():
            parts.append(b.strip())
    return "。".join(parts) + "。"

# ---- call TTS (bytes) ----
def tts_bytes(text):
    req = json.dumps({"text": text, "voice": VOICE}).encode("utf-8")
    r = urllib.request.Request(TTS_ENDPOINT, data=req,
                               headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(r, timeout=60) as resp:
            return resp.read()
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"TTS HTTP {e.code}: {e.read().decode('utf-8', 'ignore')[:300]}")

audio_paths = []
durations = []
for i, (pid, title, bullets) in enumerate(slides):
    txt = narration(pid, title, bullets)
    mp3 = os.path.join(AUDIO, f"page_{i+1:02d}.mp3")
    if os.path.exists(mp3) and os.path.getsize(mp3) > 1000:
        data = open(mp3, "rb").read()
    else:
        data = tts_bytes(txt)
    with open(mp3, "wb") as f:
        f.write(data)
    audio_paths.append(mp3)
    # duration via ffprobe
    d = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", mp3],
                       capture_output=True, text=True)
    try:
        dur = float(d.stdout.strip())
    except Exception:
        dur = max(2.0, len(txt) / 8.0)
    durations.append(dur)
    print(f"  page {i+1:02d}: {dur:.1f}s  text={txt[:30]}...")

# ---- per-page subtitle srt ----
def write_srt(idx, text, dur):
    # split long text into <=2 lines per cue
    cues = []
    seg = ""
    for ch in text:
        if len(seg) < 38:
            seg += ch
        else:
            cues.append(seg); seg = ch
    if seg:
        cues.append(seg)
    step = dur / max(1, len(cues))
    srt = ""
    for k, c in enumerate(cues):
        st = k * step
        en = (k + 1) * step
        def ts(t):
            ms = int((t - int(t)) * 1000)
            h = int(t // 3600); m = int((t % 3600) // 60); s = int(t % 60)
            return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
        srt += f"{k+1}\n{ts(st)} --> {ts(en)}\n{c}\n\n"
    p = os.path.join(AUDIO, f"page_{idx:02d}.srt")
    with open(p, "w", encoding="utf-8") as f:
        f.write(srt)
    return p

srt_paths = [write_srt(i + 1, narration(*slides[i]), durations[i]) for i in range(len(slides))]

# ---- build concat of audio (for mux) ----
# use ffmpeg concat demuxer
concat_list = os.path.join(AUDIO, "concat.txt")
with open(concat_list, "w", encoding="utf-8") as f:
    for p in audio_paths:
        f.write(f"file '{p}'\n")
merged_audio = os.path.join(AUDIO, "full.mp3")
subprocess.run([FF, "-y", "-f", "concat", "-safe", "0", "-i", concat_list,
                "-c", "copy", merged_audio], check=True)

# ---- render frames if missing ----
if not os.path.exists(FRAMES) or len(os.listdir(FRAMES)) < len(slides):
    print("frames missing, re-run render_video.py first")
    raise SystemExit(1)

# ---- stitch video: per-page duration = audio + tail, crossfade ----
tail = 0.4
td = 0.5
page_dur = [d + tail for d in durations]
total = sum(page_dur)
# build per-image input with its own duration
inputs = []
for i in range(len(slides)):
    p = os.path.join(FRAMES, f"page_{i+1:02d}.png")
    inputs += ["-loop", "1", "-t", str(page_dur[i]), "-i", p]

# xfade chain
flt = ""
prev = "[0:v]"
off = 0.0
for i in range(1, len(slides)):
    off += page_dur[i - 1] - td
    outtag = "[vout]" if i == len(slides) - 1 else f"[v{i}]"
    flt += f"{prev}[{i}:v]xfade=transition=fade:duration={td}:offset={off:.2f}{outtag};"
    prev = outtag
flt = flt.rstrip(";")

# subtitles burned on the xfade output
sub_chain = "[vout]"
sub_exprs = []
for i in range(len(slides)):
    sub_exprs.append(
        f"subtitles='{srt_paths[i].replace(chr(92), chr(92)+chr(92))}'"
        f":force_style='FontName=Microsoft YaHei,FontSize=30,PrimaryColour=&H00FFFFFF&,OutlineColour=&H00000000&,Outline=3'"
    )
# chain subtitles one per page won't align timing unless we split by timestamp.
# Simpler: apply a single subtitles filter using concatenated srt timed to full video.
all_srt = os.path.join(AUDIO, "full.srt")
with open(all_srt, "w", encoding="utf-8") as f:
    n = 1
    t = 0.0
    for i in range(len(slides)):
        txt = narration(*slides[i])
        cues = []
        seg = ""
        for ch in txt:
            if len(seg) < 38:
                seg += ch
            else:
                cues.append(seg); seg = ch
        if seg:
            cues.append(seg)
        dur = page_dur[i]
        step = dur / max(1, len(cues))
        for k, c in enumerate(cues):
            st = t + k * step; en = t + (k + 1) * step
            def ts(tt):
                ms = int((tt - int(tt)) * 1000)
                h = int(tt // 3600); m = int((tt % 3600) // 60); s = int(tt % 60)
                return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
            f.write(f"{n}\n{ts(st)} --> {ts(en)}\n{c}\n\n")
            n += 1
        t += dur

sub_path = all_srt.replace("\\", "/").replace(":", "\\:")
sub_filter = (f"[vout]subtitles=filename='{sub_path}'"
              f":force_style='FontName=Microsoft YaHei,FontSize=28,PrimaryColour=&H00FFFFFF&,OutlineColour=&H00000000&,Outline=3'[vsub]")

cmd = ([FF, "-y"] + inputs +
       ["-filter_complex", flt, "-map", "[vout]", "-r", "25",
        "-pix_fmt", "yuv420p", "-c:v", "libx264", OUT])
# First produce silent video, then mux audio + subtitles in a second pass.
print("running ffmpeg (video pass)...")
r = subprocess.run(cmd, capture_output=True, text=True)
if r.returncode != 0:
    print("FFMPEG ERR:\n", r.stderr[-2000:])
    raise SystemExit(1)
print("video pass done:", OUT)

silent = os.path.join(AUDIO, "silent.mp4")
os.replace(OUT, silent)

# second pass: add audio + burned subtitles
cmd2 = [FF, "-y", "-i", silent, "-i", merged_audio,
        "-filter_complex",
        f"[0:v]subtitles=filename='{sub_path}'"
        f":force_style='FontName=Microsoft YaHei,FontSize=28,PrimaryColour=&H00FFFFFF&,OutlineColour=&H00000000&,Outline=3'[v]",
        "-map", "[v]", "-map", "1:a", "-c:v", "libx264", "-r", "25",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "128k", "-shortest", OUT]
print("running ffmpeg (audio+subtitle pass)...")
r2 = subprocess.run(cmd2, capture_output=True, text=True)
if r2.returncode != 0:
    print("FFMPEG2 ERR:\n", r2.stderr[-2000:])
    raise SystemExit(1)
print("FINAL saved:", OUT, "size:", os.path.getsize(OUT), "bytes")
