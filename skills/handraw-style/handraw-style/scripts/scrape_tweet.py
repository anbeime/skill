import os
import sys
import re
import json
import urllib.request
import urllib.parse
from io import BytesIO
from pathlib import Path

from PIL import Image

def fetch_tweet_data(tweet_url_or_id):
    # Extract tweet ID
    match = re.search(r'(?:status(?:es)?/|id=)?(\d{15,25})', tweet_url_or_id)
    if not match:
        raise ValueError(f"Could not extract tweet ID from: {tweet_url_or_id}")
    tweet_id = match.group(1)

    # List of endpoints to try
    endpoints = [
        f"https://api.fxtwitter.com/status/{tweet_id}",
        f"https://api.vxtwitter.com/status/{tweet_id}",
    ]

    last_err = None
    for ep in endpoints:
        try:
            req = urllib.request.Request(ep, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
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

    raise RuntimeError(f"Failed to fetch tweet {tweet_id} from all providers: {last_err}")

def download_file(url, target_path):
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    with urllib.request.urlopen(req, timeout=30) as resp:
        content = resp.read()
    with Image.open(BytesIO(content)) as image:
        if image.mode not in {"RGB", "RGBA"}:
            image = image.convert("RGBA" if "A" in image.getbands() else "RGB")
        image.save(target_path, format="WEBP", quality=90, method=6)
    return target_path.stat().st_size

def main():
    if len(sys.argv) < 2:
        tweet_url = "https://x.com/Artedeingenio/status/2096941708508328344"
    else:
        tweet_url = sys.argv[1]

    output_base = Path("downloads")
    if len(sys.argv) >= 3:
        output_base = Path(sys.argv[2])

    print(f"Fetching tweet data for: {tweet_url}")
    tweet, tweet_id = fetch_tweet_data(tweet_url)

    out_dir = output_base / f"tweet_{tweet_id}"
    out_dir.mkdir(parents=True, exist_ok=True)

    # Save raw json
    json_path = out_dir / "tweet.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(tweet, f, indent=2, ensure_ascii=False)
    print(f"Saved metadata: {json_path}")

    # Extract images
    image_urls = []
    if "media" in tweet and "photos" in tweet["media"]:
        for p in tweet["media"]["photos"]:
            u = p.get("url")
            if u:
                if not u.endswith("?name=orig") and "twimg.com" in u:
                    if "?" in u:
                        u = u.split("?")[0] + "?name=orig"
                    else:
                        u = u + "?name=orig"
                image_urls.append(u)
    elif "mediaURLs" in tweet:
        for u in tweet["mediaURLs"]:
            if "twimg.com" in u:
                if "?" in u:
                    u = u.split("?")[0] + "?name=orig"
                else:
                    u = u + "?name=orig"
            image_urls.append(u)

    print(f"Found {len(image_urls)} images to download.")

    downloaded_images = []
    for idx, img_url in enumerate(image_urls, start=1):
        img_filename = f"image_{idx}.webp"
        img_dest = out_dir / img_filename
        print(f"Downloading [{idx}/{len(image_urls)}] -> {img_filename} ...")
        size = download_file(img_url, img_dest)
        print(f"  Done ({size:,} bytes)")
        downloaded_images.append(img_filename)

    # Generate Markdown summary
    author_name = tweet.get("author", {}).get("name") or tweet.get("user_name", "")
    author_handle = tweet.get("author", {}).get("screen_name") or tweet.get("user_screen_name", "")
    text = tweet.get("text", "")
    created_at = tweet.get("created_at") or tweet.get("date", "")
    likes = tweet.get("likes", 0)
    retweets = tweet.get("retweets", 0)
    bookmarks = tweet.get("bookmarks", 0)

    md_lines = [
        f"# 推文内容与图片记录",
        "",
        f"- **推文地址**: [{tweet_url}]({tweet_url})",
        f"- **发布作者**: {author_name} (@{author_handle})",
        f"- **发布时间**: `{created_at}`",
        f"- **互动数据**: ❤️ {likes} Likes | 🔁 {retweets} Retweets | 🔖 {bookmarks} Bookmarks",
        "",
        "## 推文正文",
        "",
        "```text",
        text,
        "```",
        "",
        "## 推文包含的图片 (共 " + str(len(downloaded_images)) + " 张)",
        ""
    ]

    for idx, img_fn in enumerate(downloaded_images, 1):
        md_lines.append(f"### 图片 {idx}")
        md_lines.append(f"![图片 {idx}]({img_fn})")
        md_lines.append("")

    md_path = out_dir / "tweet.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))
    print(f"Saved Markdown report: {md_path}")
    print("All tasks completed successfully!")

if __name__ == "__main__":
    main()
