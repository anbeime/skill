"""Generate Chinese narration audio (edge-tts) for each deck slide.

Output:
  _tmp/audio/page_NN.mp3   (one per slide)
  _tmp/audio/manifest.json  (pid, title, bullets, narration text, audio path)
No ffmpeg needed.
"""
import os, re, json, asyncio, edge_tts

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "deck_track1.md")
AUD = os.path.join(HERE, "audio")
os.makedirs(AUD, exist_ok=True)
VOICE = "zh-CN-XiaoxiaoNeural"   # natural female Mandarin

# ---- parse deck (same logic as render_video.py) ----
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
    bullets = [re.sub(r"\*\*(.+?)\*\*", r"\1", b) for b in bullets]
    slides.append((pid, title, bullets))

print(f"parsed {len(slides)} slides")

def narration_text(title, bullets):
    # Keep it speech-like: title + key bullets, drop trailing "演讲要点" meta note
    parts = [title + "。"]
    for b in bullets:
        b = re.sub(r"^演讲要点[:：]\s*", "", b).strip()
        if b:
            parts.append(b)
    txt = " ".join(parts)
    # edge-tts single utterance is fine up to a few hundred chars; cap safe
    return txt

async def gen_one(idx, pid, title, bullets):
    text = narration_text(title, bullets)
    out = os.path.join(AUD, f"page_{idx:02d}.mp3")
    c = edge_tts.Communicate(text, VOICE)
    await c.save(out)
    return {"idx": idx, "pid": pid, "title": title,
            "bullets": bullets, "text": text, "audio": out}

async def main():
    manifest = []
    for i, (pid, title, bullets) in enumerate(slides, 1):
        r = await gen_one(i, pid, title, bullets)
        manifest.append(r)
        print(f"  [{r['pid']}] audio {os.path.getsize(r['audio'])} bytes, text {len(r['text'])} chars")
    with open(os.path.join(AUD, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    print("ALL DONE ->", os.path.join(AUD, "manifest.json"))

asyncio.run(main())
