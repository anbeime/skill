# -*- coding: utf-8 -*-
"""Shared helpers: episode loading, workspace paths, reference images, fonts."""
import json
import os
import sys
import urllib.request

SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.path.join(os.path.expanduser("~"), ".cache", "ancient-rap-battle")

# reference images the user generates in Midjourney, saved into <episode>/refs/
REFS = {
    "a_sheet": "a_sheet.png",      # A full-body turnaround (front / side / back)
    "a_face": "a_face.png",        # A 2x2 expression sheet
    "a_bust": "a_bust.png",        # A waist-up, three-quarters to the right (close shots)
    "b_sheet": "b_sheet.png",
    "b_face": "b_face.png",
    "b_bust": "b_bust.png",        # B waist-up, three-quarters to the left
    "dj": "dj.png",
    "crowd": "crowd.png",          # crowd look
    "venue": "venue.png",          # the stage, straight-on and symmetrical
    "hecklers": "hecklers.png",    # H3 path only (old template); the Seedance path has no recurring trio
}

FONT_URLS = {
    # all SIL Open Font License, from the official Google Fonts repository
    "brush": ("MaShanZheng-Regular.ttf",
              "https://github.com/google/fonts/raw/main/ofl/mashanzheng/MaShanZheng-Regular.ttf"),
    "serif_sc": ("NotoSerifSC[wght].ttf",
                 "https://github.com/google/fonts/raw/main/ofl/notoserifsc/NotoSerifSC%5Bwght%5D.ttf"),
}
LOCAL_FONTS = {
    "serif_sc": ["C:/Windows/Fonts/NotoSerifSC-VF.ttf", "/Library/Fonts/NotoSerifSC-VF.ttf",
                 "/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc"],
    "serif_en_bold": ["C:/Windows/Fonts/georgiab.ttf", "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
                      "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"],
    "serif_en_bolditalic": ["C:/Windows/Fonts/georgiaz.ttf", "/System/Library/Fonts/Supplemental/Georgia Bold Italic.ttf",
                            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-BoldItalic.ttf"],
}


def die(msg):
    sys.exit("ERROR: " + msg)


def load_episode(ep):
    path = os.path.join(ep, "episode.json")
    if not os.path.exists(path):
        die("no episode.json in %s (copy one from examples/)" % ep)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def P(ep, *parts):
    """path inside the episode folder, creating parent folders"""
    p = os.path.join(ep, *parts)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    return p


def jload(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def jsave(path, data):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)


def ref(ep, key):
    """reference image path; the waist-up crops are made by make_clips.py"""
    if key in ("a_bust", "b_bust"):
        return os.path.join(ep, "work", key + ".png")
    return os.path.join(ep, "refs", REFS[key])


def font(kind):
    """local font if present, otherwise download the OFL font once into the cache"""
    for p in LOCAL_FONTS.get(kind, []):
        if os.path.exists(p):
            return p
    if kind in FONT_URLS:
        name, url = FONT_URLS[kind]
        dst = os.path.join(CACHE, "fonts", name)
        if not os.path.exists(dst):
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            print("downloading font", name)
            urllib.request.urlretrieve(url, dst)
        return dst
    if kind.startswith("serif_en"):
        return font("serif_sc")
    die("no font for " + kind)
