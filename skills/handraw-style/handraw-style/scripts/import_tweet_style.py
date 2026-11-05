#!/usr/bin/env python3
"""
Automated End-to-End Tweet Style Importer:
1. Fetch tweet metadata & full-resolution images from X/Twitter URL.
2. Auto-increment next sequential style number (e.g. 217, 218, ...).
3. Generate 1024x1024 4-grid composite image for AI image generation reference.
4. Generate 512x512 clean single photo without number badge.
5. Append the clean tile to the active 1254x1254 16-grid contact sheet.
6. Auto-update styles_200_reorganized.md, README.md, and SKILL.md.
7. Configure mandatory reference-image passing in model_capabilities.json.
8. Rebuild gallery (build_library.py) and validate library (validate_library.py).
9. Output bilingual prompts and import summary.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import re
import urllib.request
from io import BytesIO
from pathlib import Path

from PIL import Image

from style_library_import import (
    create_style_assets,
    get_next_style_number,
    rebuild_and_validate,
    update_manifest,
    update_markdown_source,
    update_model_capabilities,
    update_readme_and_skill,
)

ROOT = Path(__file__).resolve().parents[1]
DOWNLOADS = ROOT / "downloads"


def extract_tweet_id(tweet_url_or_id: str) -> str:
    match = re.search(r'(?:status(?:es)?/|id=)?(\d{15,25})', tweet_url_or_id)
    if not match:
        raise ValueError(f"Cannot extract tweet ID from: {tweet_url_or_id}")
    return match.group(1)


def duplicate_notice(tweet_id: str, downloads_root: Path = DOWNLOADS) -> str | None:
    """Return a user-facing duplicate notice without making a network request."""
    download_dir = downloads_root / f"tweet_{tweet_id}"
    if not (download_dir / "tweet.json").exists():
        return None
    manifest = download_dir / "import.json"
    if manifest.exists():
        data = json.loads(manifest.read_text(encoding="utf-8"))
        number = data.get("style_number")
        if number:
            return f"Tweet {tweet_id} has already been imported as style #{number}. No files were changed."
    return None


def write_import_manifest(download_dir: Path, tweet_id: str, tweet_url: str, number: str) -> None:
    manifest = {
        "tweet_id": tweet_id,
        "source_url": tweet_url,
        "style_number": number,
        "imported_at": datetime.now(timezone.utc).isoformat(),
    }
    destination = download_dir / "import.json"
    temporary = destination.with_suffix(".tmp")
    temporary.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, destination)


def fetch_tweet(tweet_url_or_id: str) -> tuple[dict, str]:
    tweet_id = extract_tweet_id(tweet_url_or_id)

    endpoints = [
        f"https://api.fxtwitter.com/status/{tweet_id}",
        f"https://api.vxtwitter.com/status/{tweet_id}",
    ]
    last_err = None
    for ep in endpoints:
        try:
            req = urllib.request.Request(ep, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                if "tweet" in data:
                    return data["tweet"], tweet_id
                elif "tweetID" in data:
                    return data, tweet_id
        except Exception as e:
            last_err = e
            continue
    raise RuntimeError(f"Failed to fetch tweet from all providers: {last_err}")


def download_file(url: str, target: Path) -> int:
    if target.exists() and target.stat().st_size > 1024:
        return target.stat().st_size
    import time
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    })
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                content = resp.read()
            with Image.open(BytesIO(content)) as image:
                if image.mode not in {"RGB", "RGBA"}:
                    image = image.convert("RGBA" if "A" in image.getbands() else "RGB")
                image.save(target, format="WEBP", quality=90, method=6)
            return target.stat().st_size
        except Exception as e:
            if attempt == 3:
                raise e
            time.sleep(1.5)


def extract_images(tweet: dict) -> list[str]:
    image_urls = []
    if "media" in tweet and "photos" in tweet["media"]:
        for p in tweet["media"]["photos"]:
            u = p.get("url")
            if u:
                if "twimg.com" in u:
                    u = u.split("?")[0] + "?name=orig"
                image_urls.append(u)
    elif "mediaURLs" in tweet:
        for u in tweet["mediaURLs"]:
            if "twimg.com" in u:
                u = u.split("?")[0] + "?name=orig"
            image_urls.append(u)
    return image_urls


def main():
    parser = argparse.ArgumentParser(description="Import tweet as a numbered style reference.")
    parser.add_argument("tweet_url", help="X/Twitter tweet URL or status ID")
    parser.add_argument("--name", help="Custom English generation style name")
    parser.add_argument("--traits", help="Custom core visual traits (Chinese)")
    args = parser.parse_args()

    tweet_id = extract_tweet_id(args.tweet_url)
    if notice := duplicate_notice(tweet_id):
        raise SystemExit(f"DUPLICATE: {notice}")

    print(f"=== [1/6] Fetching Tweet Metadata: {args.tweet_url} ===")
    tweet, tweet_id = fetch_tweet(args.tweet_url)
    author_name = tweet.get("author", {}).get("name") or tweet.get("user_name") or "Artist"
    author_handle = tweet.get("author", {}).get("screen_name") or tweet.get("user_screen_name") or "artist"
    tweet_text = tweet.get("text", "")
    print(f"Author: {author_name} (@{author_handle})")

    downloads_dir = DOWNLOADS / f"tweet_{tweet_id}"
    downloads_dir.mkdir(parents=True, exist_ok=True)
    (downloads_dir / "tweet.json").write_text(json.dumps(tweet, indent=2, ensure_ascii=False), encoding="utf-8")

    existing_images = sorted(downloads_dir.glob("image_*.webp"))
    img_urls = extract_images(tweet)
    if not img_urls and not existing_images:
        raise RuntimeError("No images found in the tweet!")

    raw_images = []
    if existing_images and (not img_urls or len(existing_images) >= len(img_urls)):
        raw_images = existing_images
        print(f"Using {len(raw_images)} existing downloaded images from {downloads_dir.name}")
    else:
        print(f"Downloading {len(img_urls)} high-resolution images...")
        for idx, u in enumerate(img_urls, 1):
            target = downloads_dir / f"image_{idx}.webp"
            download_file(u, target)
            raw_images.append(target)
            print(f"  [{idx}/{len(img_urls)}] Saved {target.name}")

    print("=== [2/6] Calculating Next Sequential Style Number ===")
    number = get_next_style_number()
    print(f"Assigned Style Number: #{number}")

    gen_name = args.name
    if not gen_name:
        sref_match = re.search(r'--sref\s+(\d+)', tweet_text)
        sref_code = sref_match.group(1) if sref_match else ""
        if "3D" in tweet_text or "cartoon" in tweet_text.lower():
            gen_name = f"Stylized 3D Cartoon Personality"
        else:
            gen_name = f"Creative Stylized Character"

    traits = args.traits
    if not traits:
        traits = f"奇想风格化3D卡通美学、夸张头身比例、富有表现力的大眼、独特剪影轮廓与精细触感材质纹理；具有现代动画长片质感。"

    print("=== [3/6] Generating Reference & Contact Sheet Assets ===")
    assets = create_style_assets(number, raw_images)
    if assets["grid"]:
        print(f"Created 4-grid generation reference: {assets['grid'].name}")
    else:
        print("One source image supplied; using the clean single image as the generation reference.")
    print(f"Created clean single tile: {assets['tile'].name}")
    print(f"Updated 16-grid contact sheet: {assets['sheet'].name}")

    print("=== [4/6] Updating Style Library & Model Capabilities ===")
    update_markdown_source(number, author_name, gen_name, traits)
    update_readme_and_skill(number)
    update_manifest(number)
    update_model_capabilities(number, name_activation="none", traits_activation="none")

    print("=== [5/6] Rebuilding Gallery & Validating Invariants ===")
    rebuild_and_validate()
    write_import_manifest(downloads_dir, tweet_id, args.tweet_url, number)

    print("=== [6/6] Import Summary ===")
    print(f"Successfully imported style #{number}!")
    print(f"- Number: #{number}")
    print(f"- Author: {author_name} (@{author_handle})")
    print(f"- Style Name: {gen_name}")
    print(f"- Gallery Sheet: images/{assets['sheet'].name} (16-grid scale)")
    print(f"- Generation Reference: {assets['grid'].relative_to(ROOT)} (1024x1024 4-grid)")
    print(f"- Mandatory Image-Passing: Enabled (use_reference_image=True)")
    print("\nDraft Chinese Prompt:")
    print(f"风格名称：#{number} · {gen_name}。主题：[在此输入主题]。参考作者/风格名称：{author_name}。")
    print("\nDraft English Prompt:")
    print(f"Style name: #{number} · {gen_name}. Theme: [Your theme here]. Reference author/style name: {author_name}.")


if __name__ == "__main__":
    main()
