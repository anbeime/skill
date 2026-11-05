"""Load and resolve the canonical layout-prompt library."""
from __future__ import annotations

import json
import re
from pathlib import Path


SKILL = Path(__file__).resolve().parents[1]
REFERENCES = SKILL / "references"
INDEX = REFERENCES / "layouts.json"
VALID_CATEGORIES = {"social-card", "infographic", "comic-storyboard", "ip-character", "ecommerce"}
LANGUAGE_MARKER = re.compile(r"<!--\s*(zh|en)\s*-->")
CJK = re.compile(r"[\u3400-\u9fff]")


def detect_language(value: str) -> str:
    """Use Chinese for mixed input; otherwise return English."""
    return "zh" if CJK.search(value) else "en"


def read_prompt(path: Path) -> dict[str, str]:
    content = path.read_text(encoding="utf-8").strip()
    parts = LANGUAGE_MARKER.split(content)
    prompts: dict[str, str] = {}
    for index in range(1, len(parts), 2):
        prompts[parts[index]] = parts[index + 1].strip()
    if set(prompts) != {"zh", "en"} or not all(prompts.values()):
        raise ValueError(f"Layout prompt must contain non-empty zh and en blocks: {path}")
    return prompts


def load_layouts() -> list[dict[str, object]]:
    layouts = json.loads(INDEX.read_text(encoding="utf-8"))
    if not isinstance(layouts, list):
        raise ValueError("Layout index must be a JSON array.")
    seen: set[str] = set()
    resolved: list[dict[str, object]] = []
    for item in layouts:
        if not isinstance(item, dict):
            raise ValueError("Each layout index item must be an object.")
        identifier = str(item.get("id", "")).upper()
        category = item.get("category")
        name = item.get("name")
        image = item.get("image")
        prompt_file = item.get("prompt_file")
        keywords = item.get("keywords")
        if not re.fullmatch(r"(?:SC|IG|SB|IP|EC)-\d{3}", identifier):
            raise ValueError(f"Invalid layout ID: {identifier or item.get('id')!r}")
        expected_prefix = (
            "SC" if category == "social-card"
            else "IG" if category == "infographic"
            else "SB" if category == "comic-storyboard"
            else "IP" if category == "ip-character"
            else "EC" if category == "ecommerce"
            else ""
        )
        if not expected_prefix or not identifier.startswith(f"{expected_prefix}-"):
            raise ValueError(f"Layout {identifier} has an invalid category.")
        if identifier in seen:
            raise ValueError(f"Duplicate layout ID: {identifier}")
        if not isinstance(name, str) or not name.strip() or not isinstance(image, str) or not image.strip():
            raise ValueError(f"Layout {identifier} needs a name and image path.")
        if not isinstance(prompt_file, str) or not prompt_file.strip():
            raise ValueError(f"Layout {identifier} needs a prompt file.")
        if not isinstance(keywords, list) or not all(isinstance(keyword, str) and keyword.strip() for keyword in keywords):
            raise ValueError(f"Layout {identifier} needs non-empty keyword strings.")
        prompt_path = SKILL / prompt_file
        if not prompt_path.is_file():
            prompt_path = REFERENCES / prompt_file
        if not prompt_path.is_file():
            prompt_path = REFERENCES / Path(prompt_file).name
        if not prompt_path.is_file():
            raise ValueError(f"Layout prompt file is missing: {prompt_path}")
        seen.add(identifier)
        resolved.append({
            **item,
            "id": identifier,
            "prompts": read_prompt(prompt_path),
        })
    return resolved


LAYOUT_ALIASES: dict[str, str] = {
    "IG-036": "IP-002",
    "SC-023": "IP-001",
}


def resolve_layout(identifier: str) -> dict[str, object]:
    normalized = identifier.strip().upper()
    normalized = LAYOUT_ALIASES.get(normalized, normalized)
    for layout in load_layouts():
        if layout["id"] == normalized:
            return layout
    raise ValueError(f"Unknown layout ID: {identifier}. Use a listed SC-, IG-, SB-, IP-, or EC- identifier.")
