# -*- coding: utf-8 -*-
"""Optional: does the mouth open and close with the vocal? (MediaPipe face landmarks vs vocal loudness)

usage: python scripts/lipcheck.py <episode_dir> B12 [B13 ...]      (uses the accepted take from picks.json)
Prints how many frames the mouth trails the voice. Only a hint: a microphone over the lips, small faces or
profiles make it unreliable - ALWAYS confirm with the user's eyes before shifting a clip (once a measured
0.58 s shift made a clip worse). A trusted shift goes into work/shifts.json.
"""
import json
import os
import subprocess
import sys
import urllib.request

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import CACHE, jload  # noqa: E402

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
FPS = 24


def model():
    p = os.path.join(CACHE, "face_landmarker.task")
    if not os.path.exists(p):
        os.makedirs(CACHE, exist_ok=True)
        urllib.request.urlretrieve(MODEL_URL, p)
    return p


def mouth(video):
    import cv2
    import mediapipe as mp
    from mediapipe.tasks.python import BaseOptions, vision
    det = vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model()), running_mode=vision.RunningMode.VIDEO, num_faces=2,
        min_face_detection_confidence=0.2, min_face_presence_confidence=0.2, min_tracking_confidence=0.2))
    cap, g, i = cv2.VideoCapture(video), {}, 0
    while True:
        ok, f = cap.read()
        if not ok:
            break
        f = cv2.resize(f, None, fx=2, fy=2)
        r = det.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(f, cv2.COLOR_BGR2RGB)),
                                 int(i * 1000 / FPS))
        if r.face_landmarks:
            lm = max(r.face_landmarks, key=lambda l: abs(l[152].y - l[10].y))   # biggest face = the rapper
            g[i] = abs(lm[14].y - lm[13].y) / (abs(lm[152].y - lm[10].y) + 1e-6)
        i += 1
    return g, i


def loudness(path, n):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
                         capture_output=True).stdout
    x, h = np.frombuffer(raw, dtype=np.float32), 16000 // FPS
    return [float(np.sqrt((x[k * h:(k + 1) * h] ** 2).mean())) if (k + 1) * h <= len(x) else 0.0 for k in range(n)]


def main():
    ep, ids = sys.argv[1], sys.argv[2:]
    picks = jload(os.path.join(ep, "work", "picks.json"))
    for cid in ids:
        g, n = mouth(os.path.join(ep, "clips", "%s_t%s.mp4" % (cid, picks[cid])))
        env = loudness(os.path.join(ep, "work", "audio", cid + ".mp3"), n)
        res = []
        for lag in range(-6, 18):
            a = [env[q] for q in range(n) if q + lag in g and env[q] > 0]
            b = [g[q + lag] for q in range(n) if q + lag in g and env[q] > 0]
            if len(a) > 10:
                res.append((float(np.corrcoef(a, b)[0, 1]), lag))
        if not res:
            print("%s: face found in %d/%d frames - cannot measure" % (cid, len(g), n))
            continue
        c, lag = max(res)
        print(json.dumps({"clip": cid, "face_frames": "%d/%d" % (len(g), n), "best_corr": round(c, 2),
                          "mouth_trails_s": round(lag / FPS, 2)}))


if __name__ == "__main__":
    main()
