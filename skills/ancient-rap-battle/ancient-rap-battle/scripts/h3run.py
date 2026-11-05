# -*- coding: utf-8 -*-
"""Step 6 - generate clips with MiniMax H3 (stdlib + ffmpeg).

usage:
  python scripts/h3run.py <episode_dir> A01 A02 OPEN ...     # several clips, submitted in parallel (8 s apart)
  python scripts/h3run.py <episode_dir> --all                  # every clip that has no accepted take yet
  python scripts/h3run.py <episode_dir> A01 --dry-run          # print the request, no upload, no cost
  options: --resolution 768P|2K  --estimate (print the cost and stop)

The API key comes ONLY from the environment variable MINIMAX_API_KEY and is never written anywhere.
Every take is saved as clips/<id>_t<n>.mp4, checked with qa.py, and accepted automatically into
work/picks.json (+ work/shifts.json when H3 started the song late) if the lips can match the song.
"""
import argparse
import concurrent.futures
import hashlib
import json
import os
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import qa  # noqa: E402
from common import die, jload, jsave  # noqa: E402

API = os.environ.get("MINIMAX_API_BASE", "https://api.minimax.io").rstrip("/")
PRICE = {"768P": 0.08, "2K": 0.13}
CTYPE = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".mp3": "audio/mpeg", ".wav": "audio/wav"}
LOCK = threading.Lock()


def log(msg):
    with LOCK:
        print(msg, flush=True)


def api(method, path, body=None, headers=None, raw=False, timeout=180):
    key = os.environ.get("MINIMAX_API_KEY")
    if not key:
        die("set the environment variable MINIMAX_API_KEY first")
    h = {"Authorization": "Bearer " + key}
    h.update(headers or {})
    data = body
    if body is not None and not raw:
        data = json.dumps(body).encode()
        h["Content-Type"] = "application/json"
    req = urllib.request.Request(API + path, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        hint = {401: "API key invalid", 402: "insufficient balance - top up", 422: "blocked by moderation",
                429: "rate limited - wait and retry"}.get(e.code, "")
        raise RuntimeError("HTTP %s %s %s %s" % (e.code, path, hint, e.read().decode(errors="replace")[:500]))


def check(resp, what):
    br = resp.get("base_resp") or {}
    if br.get("status_code", 0) not in (0, None):
        raise RuntimeError("%s failed: %s" % (what, br))


def upload(ep, path):
    cache_file = os.path.join(ep, "work", "uploads.json")
    raw = open(path, "rb").read()
    digest = hashlib.sha256(raw).hexdigest()
    with LOCK:
        cache = jload(cache_file) if os.path.exists(cache_file) else {}
    hit = cache.get(digest)
    if hit and time.time() - hit["t"] < 6 * 86400:            # uploaded files live 7 days
        return hit["url"]
    b = uuid.uuid4().hex
    ext = os.path.splitext(path)[1].lower()
    body = (("--%s\r\nContent-Disposition: form-data; name=\"purpose\"\r\n\r\nvideo_generation_input\r\n" % b).encode()
            + ("--%s\r\nContent-Disposition: form-data; name=\"file\"; filename=\"f_%s%s\"\r\nContent-Type: %s\r\n\r\n"
               % (b, digest[:12], ext, CTYPE.get(ext, "application/octet-stream"))).encode()
            + raw + ("\r\n--%s--\r\n" % b).encode())
    resp = api("POST", "/v1/files/upload", body, raw=True, timeout=600,
               headers={"Content-Type": "multipart/form-data; boundary=" + b})
    check(resp, "upload " + os.path.basename(path))
    url = "mm_file://%s" % resp["file"]["file_id"]
    with LOCK:
        cache = jload(cache_file) if os.path.exists(cache_file) else {}
        cache[digest] = {"url": url, "t": time.time(), "name": os.path.basename(path)}
        jsave(cache_file, cache)
    return url


def find(d, *paths):
    for p in paths:
        cur = d
        for k in p.split("."):
            cur = cur.get(k) if isinstance(cur, dict) else None
        if cur not in (None, ""):
            return cur
    return None


def cut_audio(ep, c):
    out = os.path.join(ep, "work", "audio", c["id"] + ".mp3")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    a, b = c["audio"]
    dur = max(2.0, b - a)
    af = "afade=t=in:d=0.02,afade=t=out:st=%.3f:d=0.05" % (dur - 0.05)
    if c.get("lead"):
        af += ",adelay=%d:all=1" % int(c["lead"] * 1000)   # silence before the first word: the singer lifts the mic first
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-ss", "%.3f" % a, "-t", "%.3f" % dur,
                    "-i", os.path.join(ep, "work", "vocals_final.wav"), "-af", af, "-ac", "2", "-ar", "44100",
                    "-b:a", "192k", out], check=True)
    return out


def next_take(ep, cid):
    n = 1
    while os.path.exists(os.path.join(ep, "clips", "%s_t%d.mp4" % (cid, n))):
        n += 1
    return n


def run_one(ep, c, take, resolution, dry):
    audio = cut_audio(ep, c) if c["kind"] == "rap" else None
    content = [{"type": "text", "text": c["prompt"]}]
    if dry:
        imgs = ["mm_file://<%s>" % os.path.basename(f) for f in c["images"]]
        aud = "mm_file://<%s>" % os.path.basename(audio) if audio else None
    else:
        imgs = [upload(ep, f) for f in c["images"]]
        aud = upload(ep, audio) if audio else None
    content += [{"type": "image_url", "image_url": {"url": u}, "role": "reference_image"} for u in imgs]
    if aud:
        content.append({"type": "audio_url", "audio_url": {"url": aud}, "role": "reference_audio"})
    body = {"model": "MiniMax-H3", "content": content, "resolution": resolution, "duration": c["dur"], "ratio": "16:9"}
    if dry:
        print(json.dumps(body, ensure_ascii=False, indent=1)[:2500])
        return
    resp = api("POST", "/v2/video_generation", body)
    check(resp, "create task")
    tid = find(resp, "task_id", "task.id", "id")
    runs = os.path.join(ep, "work", "runs.jsonl")
    with LOCK, open(runs, "a", encoding="utf-8") as f:
        f.write(json.dumps({"clip": c["id"], "take": take, "task": tid, "t": time.strftime("%Y-%m-%d %H:%M:%S")}) + "\n")
    log("%s t%d submitted (task %s)" % (c["id"], take, tid))
    t0 = time.time()
    while True:
        time.sleep(15)
        q = api("GET", "/v2/query/video_generation/%s" % tid)
        st = find(q, "task.status", "status")
        if st in ("succeeded", "success", "Success"):
            break
        if st in ("failed", "cancelled", "Fail", "fail"):
            raise RuntimeError("%s t%d %s: %s" % (c["id"], take, st, json.dumps(q, ensure_ascii=False)[:500]))
        if time.time() - t0 > 1800:
            raise RuntimeError("%s t%d timeout - task %s can be queried later" % (c["id"], take, tid))
    url = find(q, "task.content.url", "content.url", "task.video_url", "video_url", "file.download_url")
    out = os.path.join(ep, "clips", "%s_t%d.mp4" % (c["id"], take))
    os.makedirs(os.path.dirname(out), exist_ok=True)
    urllib.request.urlretrieve(url, out)
    usage = find(q, "task.usage", "usage") or {}
    verdict = qa.analyze(out, audio) if audio else {"ok": True}
    with LOCK:
        with open(runs, "a", encoding="utf-8") as f:
            f.write(json.dumps({"clip": c["id"], "take": take, "done": out, "usage": usage, "qa": verdict}) + "\n")
        picks_p, shifts_p = os.path.join(ep, "work", "picks.json"), os.path.join(ep, "work", "shifts.json")
        picks = jload(picks_p) if os.path.exists(picks_p) else {}
        shifts = jload(shifts_p) if os.path.exists(shifts_p) else {}
        if verdict.get("ok") and c["id"] not in picks:
            picks[c["id"]] = take
            if verdict.get("shift", 0) > 0.03:
                shifts[c["id"]] = verdict["shift"]
            jsave(picks_p, picks)
            jsave(shifts_p, shifts)
    if audio:
        msg = ("OK" + (" (song starts %.2fs late - shift saved)" % verdict["shift"] if verdict.get("shift", 0) > 0.03 else "")
               if verdict.get("ok") else "LIPS WON'T MATCH after %.1fs - re-roll" % verdict.get("ok_until", 0))
    else:
        msg = "saved"
    log("%s t%d %s  [%ss billed]" % (c["id"], take, msg, usage.get("output_seconds", "?")))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep")
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--resolution", default="768P", choices=["768P", "2K"])
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--estimate", action="store_true")
    a = ap.parse_args()
    ep = a.ep
    clips = {c["id"]: c for c in jload(os.path.join(ep, "work", "clips.json"))}
    picks_p = os.path.join(ep, "work", "picks.json")
    picks = jload(picks_p) if os.path.exists(picks_p) else {}
    ids = [i for i in clips if i not in picks] if a.all else a.ids
    bad = [i for i in ids if i not in clips]
    if bad or not ids:
        die("unknown or no clip ids: %s (known: %s)" % (bad, ", ".join(clips)))
    for i in ids:
        for f in clips[i]["images"]:
            if not os.path.exists(f):
                die("missing reference image " + f)
    secs = sum(clips[i]["dur"] for i in ids)
    print("%d clip(s), %ds at %s = about $%.2f" % (len(ids), secs, a.resolution, secs * PRICE[a.resolution]))
    if a.estimate:
        return
    if a.dry_run:
        run_one(ep, clips[ids[0]], 0, a.resolution, True)
        return
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
        futs = []
        for i in ids:
            futs.append(pool.submit(run_one, ep, clips[i], next_take(ep, i), a.resolution, False))
            time.sleep(8)
        for f in futs:
            try:
                f.result()
            except Exception as ex:   # one failure must not stop the rest
                log("FAILED: %s" % ex)


if __name__ == "__main__":
    main()
