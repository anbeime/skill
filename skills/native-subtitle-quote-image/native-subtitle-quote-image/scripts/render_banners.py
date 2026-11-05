#!/usr/bin/env python3
"""重新生成 README 头图（中文、英文、韩文各一张），需要本机安装 Chrome 或 Chromium。

头图 2560×1280，用 examples/gallery 里的成品案例铺满背景，左侧放标题；
自带深色背景，GitHub 浅色、深色主题共用一张。中文版同时用作仓库社交预览图，
在仓库 Settings → General → Social preview 上传。
改文字：编辑下方 COPY；改背景墙：编辑 WALL。
运行 `python3 scripts/render_banners.py`；渲染时从 Google Fonts 加载字体，需要联网。
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
GALLERY_DIR = ROOT / "examples" / "gallery"
OUT_DIR = ROOT / "assets"
WIDTH, HEIGHT, SCALE = 1280, 640, 2
JPEG_QUALITY = 88

COPY = {
    "zh": {
        "lines": ["一段视频", "拼成字幕长图"],
        "tagline": "原生字幕拼图 · Claude Code / Codex Skill",
        "title_size": 118,
        "font": "'Ma Shan Zheng', serif",
        "meta_font": "'Noto Sans SC', sans-serif",
    },
    "en": {
        "lines": ["One video,", "one quote image"],
        "tagline": "Claude Code / Codex Skill",
        "title_size": 104,
        "font": "'Kalam', cursive",
        "meta_font": "'Noto Sans SC', sans-serif",
    },
    "ko": {
        "lines": ["영상 한 편을", "자막 콜라주로"],
        "tagline": "원본 자막 콜라주 · Claude Code / Codex Skill",
        "title_size": 112,
        "font": "'Jua', sans-serif",
        "meta_font": "'Noto Sans KR', sans-serif",
    },
}
NAME = "native-subtitle-quote-image"
# 背景墙的列：(上移像素, 案例相对路径...)，错落排列。
WALL = [
    (-150, "zh/chen-shu-simple-life.jpg", "en/darby-saxbe-shared-care.jpg", "ko/masud-husain-starting-hill.jpg"),
    (-40, "ko/codie-sanchez-321-speaking.jpg", "zh/rick-rubin-creative-clouds.jpg", "en/mikayla-johnson-define-outcome.jpg"),
    (-210, "en/rick-rubin-be-yourself.jpg", "ko/inaya-mcmillan-money-program.jpg", "zh/chen-shu-simple-life.jpg"),
    (-90, "zh/girls-on-the-bus-native.jpg", "en/darby-saxbe-shared-care.jpg", "zh/rick-rubin-creative-clouds.jpg"),
    (-180, "ko/masud-husain-starting-hill.jpg", "en/mikayla-johnson-define-outcome.jpg", "ko/codie-sanchez-321-speaking.jpg"),
    (-20, "en/rick-rubin-be-yourself.jpg", "zh/girls-on-the-bus-native.jpg", "ko/inaya-mcmillan-money-program.jpg"),
]

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "C:/Program Files/Google/Chrome/Application/chrome.exe",
    "C:/Program Files (x86)/Google/Chrome/Application/chrome.exe",
]
CHROME_COMMANDS = ["google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"]


def wall_images():
    return sorted({name for _, *names in WALL for name in names})


def build_html(lang, gallery_src="gallery"):
    copy = COPY[lang]
    columns = "\n".join(
        f'<div class="col" style="margin-top:{offset}px">'
        + "".join(f'<img src="{gallery_src}/{name}">' for name in names)
        + "</div>"
        for offset, *names in WALL
    )
    first, second = copy["lines"]
    return f"""<!doctype html><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Jua&family=Kalam:wght@700&family=Ma+Shan+Zheng&family=Noto+Sans+KR:wght@500;700&family=Noto+Sans+SC:wght@500;700&display=block" rel="stylesheet">
<style>
html,body{{margin:0;background:#0e0e11}}
.card{{position:relative;width:{WIDTH}px;height:{HEIGHT}px;overflow:hidden;background:#0e0e11}}
.wall{{position:absolute;inset:0 -20px 0 auto;display:flex;gap:10px;transform:rotate(-4deg);transform-origin:right center}}
.col{{display:flex;flex-direction:column;gap:10px;width:204px}}
.col img{{width:204px;height:272px;object-fit:cover;border-radius:6px;display:block}}
.shade{{position:absolute;inset:0;background:
 linear-gradient(0deg,rgba(14,14,17,.9) 0%,rgba(14,14,17,0) 24%),
 linear-gradient(90deg,rgba(14,14,17,.95) 0%,rgba(14,14,17,.92) 42%,rgba(14,14,17,.6) 62%,rgba(14,14,17,.1) 82%,rgba(14,14,17,0) 100%)}}
.text{{position:absolute;left:72px;top:0;bottom:0;display:flex;flex-direction:column;justify-content:center}}
h1{{margin:0;font-family:{copy['font']};font-weight:400;font-size:{copy['title_size']}px;line-height:1.12;
 color:#f4f1ea;text-shadow:0 4px 18px rgba(0,0,0,.6);white-space:nowrap}}
h1 span{{display:block}}
h1 .accent{{color:#b9adff}}
.meta{{position:absolute;left:72px;bottom:46px;font-family:{copy['meta_font']};font-size:25px;
 font-weight:500;color:#c9c6d6;white-space:nowrap}}
.meta b{{color:#b9adff;font-weight:700;margin-right:20px}}
</style>
<body><div class="card">
<div class="wall">{columns}</div>
<div class="shade"></div>
<div class="text"><h1><span>{first}</span><span class="accent">{second}</span></h1></div>
<div class="meta"><b>{NAME}</b>{copy['tagline']}</div>
</div></body>
"""


def find_chrome(explicit=None):
    for candidate in (explicit, os.environ.get("CHROME")):
        if candidate:
            return candidate
    for path in CHROME_CANDIDATES:
        if Path(path).is_file():
            return path
    for command in CHROME_COMMANDS:
        found = shutil.which(command)
        if found:
            return found
    return None


def render(chrome, html_path, png_path):
    subprocess.run(
        [
            chrome,
            "--headless=new",
            "--disable-gpu",
            "--hide-scrollbars",
            f"--force-device-scale-factor={SCALE}",
            f"--window-size={WIDTH},{HEIGHT}",
            "--virtual-time-budget=8000",
            "--allow-file-access-from-files",
            f"--screenshot={png_path}",
            html_path.as_uri(),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--lang", choices=sorted(COPY), action="append", help="只生成指定语言，可重复")
    parser.add_argument("--chrome", help="Chrome/Chromium 可执行文件路径；也可用 CHROME 环境变量")
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR, help="输出目录，默认 assets/")
    args = parser.parse_args()

    chrome = find_chrome(args.chrome)
    if not chrome:
        sys.exit("找不到 Chrome 或 Chromium，请用 --chrome 或 CHROME 环境变量指定路径。")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        for name in wall_images():
            target = tmp / "gallery" / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(GALLERY_DIR / name, target)
        for lang in args.lang or sorted(COPY):
            html_path = tmp / f"{lang}.html"
            html_path.write_text(build_html(lang), encoding="utf-8")
            png_path = tmp / f"{lang}.png"
            render(chrome, html_path, png_path)
            if not png_path.is_file() or png_path.stat().st_size == 0:
                sys.exit(f"渲染失败: {lang}")
            out_path = (args.out_dir / f"banner-{lang}.jpg").resolve()
            with Image.open(png_path) as image:
                image.convert("RGB").save(out_path, "JPEG", quality=JPEG_QUALITY, optimize=True, progressive=True)
            print(f"完成: {out_path.relative_to(ROOT) if out_path.is_relative_to(ROOT) else out_path}")


if __name__ == "__main__":
    main()
