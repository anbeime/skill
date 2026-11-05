"""Build a compact offline fallback for local gallery thumbnail requests."""
from base64 import b64encode
from html.parser import HTMLParser
from io import BytesIO
import json
from pathlib import Path

from PIL import Image


class ThumbnailSources(HTMLParser):
    def __init__(self):
        super().__init__()
        self.sources = set()

    def handle_starttag(self, tag, attrs):
        source = dict(attrs).get("src", "")
        if tag == "img" and source.startswith("../") and "/images/" in source:
            self.sources.add(source)


def write_thumbnail_fallback(page: Path) -> None:
    parser = ThumbnailSources()
    parser.feed(page.read_text(encoding="utf-8"))
    images = {}
    for source in sorted(parser.sources):
        path = page.parent / source
        if not path.is_file():
            continue
        with Image.open(path) as image:
            image.thumbnail((192, 192), Image.Resampling.LANCZOS)
            buffer = BytesIO()
            image.save(buffer, "WEBP", quality=55)
        key = source.split("/images/", 1)[1]
        images[key] = "data:image/webp;base64," + b64encode(buffer.getvalue()).decode("ascii")
    page.with_name(page.stem + "-thumbnails.js").write_text(
        "window.handrawThumbnails = " + json.dumps(images, separators=(",", ":")) + ";\n",
        encoding="utf-8",
    )
