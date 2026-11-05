#!/usr/bin/env python3
"""Custom Asset Library Manager.

Handles dual-layer persistent storage (global ~/.handraw-style/config.json + local workspace fallback),
self-contained library manifests, directory initialization, attaching existing libraries,
and asset archiving for characters, props, and scenes.
"""
from __future__ import annotations

import json
import os
import shutil
from datetime import date
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1]
ROOT = Path(__file__).resolve().parents[3]

GLOBAL_CONFIG_DIR = Path.home() / ".handraw-style"
GLOBAL_CONFIG_FILE = GLOBAL_CONFIG_DIR / "config.json"
LOCAL_CONFIG_FILE = ROOT / ".custom_library_config.json"
REFERENCES_CONFIG_FILE = SKILL / "references" / "custom_library_config.json"

CUSTOM_IMAGES_DIR = ROOT / "images" / "custom"
CUSTOM_ASSETS_JS_FILE = CUSTOM_IMAGES_DIR / "custom_assets.js"
PRESET_CHARACTERS_JSON = SKILL / "references" / "characters.json"
PRESET_PROPS_JSON = SKILL / "references" / "props.json"
PRESET_SCENES_JSON = SKILL / "references" / "scenes.json"


def get_custom_library_dir() -> Path | None:
    """Resolve the active custom library directory with dual-layer fallback."""
    # 1. Global user profile config (~/.handraw-style/config.json)
    if GLOBAL_CONFIG_FILE.exists():
        try:
            data = json.loads(GLOBAL_CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("tuku_dir"):
                p = Path(str(data["tuku_dir"]))
                if p.is_dir():
                    return p
        except Exception:
            pass

    # 2. Workspace root config (.custom_library_config.json)
    if LOCAL_CONFIG_FILE.exists():
        try:
            data = json.loads(LOCAL_CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("tuku_dir"):
                p = Path(str(data["tuku_dir"]))
                if p.is_dir():
                    return p
        except Exception:
            pass

    # 3. References fallback config
    if REFERENCES_CONFIG_FILE.exists():
        try:
            data = json.loads(REFERENCES_CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data.get("tuku_dir"):
                p = Path(str(data["tuku_dir"]))
                if p.is_dir():
                    return p
        except Exception:
            pass

    return None


def _trigger_rebuild() -> None:
    """Safely trigger gallery rebuild regardless of how the script was invoked."""
    try:
        export_custom_assets_js()
        import sys
        scripts_dir = str(Path(__file__).resolve().parent)
        if scripts_dir not in sys.path:
            sys.path.insert(0, scripts_dir)
        import build_assets_gallery
        build_assets_gallery.build_assets_gallery()
        import build_tutorial_gallery
        build_tutorial_gallery.main()
    except Exception:
        pass


def init_or_attach_library(target_dir: str | Path) -> dict[str, object]:
    """Initialize a new custom library directory or attach an existing one."""
    target_path = Path(target_dir).resolve()
    target_path.mkdir(parents=True, exist_ok=True)

    char_dir = target_path / "characters"
    prop_dir = target_path / "props"
    scene_dir = target_path / "scenes"

    char_dir.mkdir(parents=True, exist_ok=True)
    prop_dir.mkdir(parents=True, exist_ok=True)
    scene_dir.mkdir(parents=True, exist_ok=True)

    # Local web preview mirrors (gitignored)
    for cat in ("characters", "props", "scenes"):
        (CUSTOM_IMAGES_DIR / cat).mkdir(parents=True, exist_ok=True)

    manifest_file = target_path / "library.json"
    is_existing = manifest_file.exists()

    manifest_data: dict[str, object] = {
        "version": 1,
        "characters": [],
        "props": [],
        "scenes": []
    }

    if is_existing:
        try:
            loaded = json.loads(manifest_file.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                manifest_data["characters"] = loaded.get("characters", [])
                manifest_data["props"] = loaded.get("props", [])
                manifest_data["scenes"] = loaded.get("scenes", [])
        except Exception:
            pass
    else:
        # Check if directory already had existing webp files and auto-index
        for cat in ("characters", "props", "scenes"):
            cat_folder = target_path / cat
            for img in sorted(cat_folder.glob("*.webp")):
                base_name = img.stem
                if cat == "characters" and base_name in ("IP-001", "CH-001"):
                    continue
                manifest_data[cat].append({
                    "id": base_name,
                    "name": base_name,
                    "name_en": base_name,
                    "image": f"../../../images/custom/{cat}/{img.name}",
                    "tags": ["自建资产"]
                })
        manifest_file.write_text(json.dumps(manifest_data, ensure_ascii=False, indent=2), encoding="utf-8")

    # Sync mirror cache for offline browser rendering
    for cat in ("characters", "props", "scenes"):
        src_cat = target_path / cat
        dst_cat = CUSTOM_IMAGES_DIR / cat
        for img in src_cat.glob("*.webp"):
            dest_file = dst_cat / img.name
            if not dest_file.exists() or dest_file.stat().st_mtime < img.stat().st_mtime:
                try:
                    shutil.copy2(img, dest_file)
                except Exception:
                    pass

    # Save dual-layer config
    config_payload = {
        "tuku_dir": str(target_path),
        "characters_dir": str(char_dir),
        "props_dir": str(prop_dir),
        "scenes_dir": str(scene_dir),
        "updated_at": date.today().isoformat()
    }
    config_json_str = json.dumps(config_payload, ensure_ascii=False, indent=2)

    # 1. Global config
    try:
        GLOBAL_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        GLOBAL_CONFIG_FILE.write_text(config_json_str, encoding="utf-8")
    except Exception:
        pass

    # 2. Local workspace configs
    try:
        LOCAL_CONFIG_FILE.write_text(config_json_str, encoding="utf-8")
    except Exception:
        pass
    try:
        REFERENCES_CONFIG_FILE.write_text(config_json_str, encoding="utf-8")
    except Exception:
        pass

    # Trigger gallery rebuild
    _trigger_rebuild()

    chars_list = manifest_data.get("characters", [])
    props_list = manifest_data.get("props", [])
    scenes_list = manifest_data.get("scenes", [])

    return {
        "tuku_dir": str(target_path),
        "is_existing": is_existing,
        "characters_count": len(chars_list) if isinstance(chars_list, list) else 0,
        "props_count": len(props_list) if isinstance(props_list, list) else 0,
        "scenes_count": len(scenes_list) if isinstance(scenes_list, list) else 0,
    }


def load_custom_assets() -> tuple[list[dict[str, object]], list[dict[str, object]], list[dict[str, object]]]:
    """Load custom assets from active external library."""
    tuku_dir = get_custom_library_dir()
    if not tuku_dir:
        return [], [], []

    manifest_file = tuku_dir / "library.json"
    if not manifest_file.exists():
        return [], [], []

    try:
        data = json.loads(manifest_file.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            return [], [], []
        chars = data.get("characters", [])
        props = data.get("props", [])
        scenes = data.get("scenes", [])

        # Sync mirror cache for images
        for cat, items in [("characters", chars), ("props", props), ("scenes", scenes)]:
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        item["is_custom"] = True
                        item_id = str(item.get("id", ""))
                        src_img = tuku_dir / cat / f"{item_id}.webp"
                        dst_img = CUSTOM_IMAGES_DIR / cat / f"{item_id}.webp"
                        if src_img.is_file() and not dst_img.is_file():
                            try:
                                dst_img.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copy2(src_img, dst_img)
                            except Exception:
                                pass
                        item["image"] = f"../../../images/custom/{cat}/{item_id}.webp"

        return (
            chars if isinstance(chars, list) else [],
            props if isinstance(props, list) else [],
            scenes if isinstance(scenes, list) else []
        )
    except Exception:
        return [], [], []


def export_custom_assets_js() -> Path:
    """Export local custom assets index as an isolated JavaScript file for client-side hydration (gitignored)."""
    custom_chars, custom_props, custom_scenes = load_custom_assets()
    CUSTOM_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "characters": custom_chars,
        "props": custom_props,
        "scenes": custom_scenes,
    }
    js_content = (
        "// Auto-generated local custom assets index (gitignored - do not commit)\n"
        f"window.CUSTOM_ASSETS_DATA = {json.dumps(payload, ensure_ascii=False, indent=2)};\n"
    )
    CUSTOM_ASSETS_JS_FILE.write_text(js_content, encoding="utf-8")
    return CUSTOM_ASSETS_JS_FILE


def get_next_id(category: str) -> str:
    """Compute next sequential ID for category, accounting for presets and custom items."""
    prefixes = {
        "characters": "CH",
        "props": "PR",
        "scenes": "SCN"
    }
    prefix = prefixes.get(category, "ASSET")
    existing_nums: set[int] = set()

    # Presets
    preset_files = {
        "characters": PRESET_CHARACTERS_JSON,
        "props": PRESET_PROPS_JSON,
        "scenes": PRESET_SCENES_JSON
    }
    preset_path = preset_files.get(category)
    if preset_path and preset_path.exists():
        try:
            presets = json.loads(preset_path.read_text(encoding="utf-8"))
            if isinstance(presets, list):
                for p in presets:
                    pid = str(p.get("id", ""))
                    if pid.startswith(f"{prefix}-"):
                        num_part = pid.split("-")[-1]
                        if num_part.isdigit():
                            existing_nums.add(int(num_part))
        except Exception:
            pass

    # Custom assets
    custom_chars, custom_props, custom_scenes = load_custom_assets()
    cat_items = {
        "characters": custom_chars,
        "props": custom_props,
        "scenes": custom_scenes
    }.get(category, [])

    for c in cat_items:
        cid = str(c.get("id", ""))
        if cid.startswith(f"{prefix}-"):
            num_part = cid.split("-")[-1]
            if num_part.isdigit():
                existing_nums.add(int(num_part))

    next_num = 1
    while next_num in existing_nums:
        next_num += 1

    return f"{prefix}-{next_num:03d}"


def save_asset(category: str, name: str, source_image: Path | str, tags: list[str] | None = None) -> dict[str, object]:
    """Save an asset to the active custom library."""
    tuku_dir = get_custom_library_dir()
    if not tuku_dir:
        raise RuntimeError("Custom library directory is not initialized. Run init_or_attach_library first.")

    src_path = Path(source_image)
    if not src_path.is_file():
        raise FileNotFoundError(f"Source image not found: {source_image}")

    next_id = get_next_id(category)
    ext = src_path.suffix.lower() if src_path.suffix else ".webp"
    if ext != ".webp":
        # Keep webp standard extension for gallery
        ext = ".webp"

    dest_filename = f"{next_id}.webp"
    dest_path = tuku_dir / category / dest_filename
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    mirror_path = CUSTOM_IMAGES_DIR / category / dest_filename
    mirror_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from PIL import Image
        with Image.open(src_path) as im:
            if im.mode not in ("RGB", "RGBA"):
                im = im.convert("RGBA" if "transparency" in im.info or "A" in im.mode else "RGB")
            im.save(dest_path, "WEBP", quality=92)
            im.save(mirror_path, "WEBP", quality=92)
    except Exception:
        shutil.copy2(src_path, dest_path)
        shutil.copy2(src_path, mirror_path)

    # Update external library.json
    manifest_file = tuku_dir / "library.json"
    manifest: dict[str, list[dict[str, object]]] = {"characters": [], "props": [], "scenes": []}
    if manifest_file.exists():
        try:
            loaded = json.loads(manifest_file.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                for k in ("characters", "props", "scenes"):
                    manifest[k] = loaded.get(k, [])
        except Exception:
            pass

    new_entry: dict[str, object] = {
        "id": next_id,
        "name": name,
        "name_en": name,
        "image": f"../../../images/custom/{category}/{dest_filename}",
        "tags": tags or ["自建资产"],
        "created_at": date.today().isoformat()
    }
    manifest[category].append(new_entry)
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    # Rebuild gallery
    _trigger_rebuild()

    return new_entry


def get_asset(asset_id: str) -> tuple[dict[str, object] | None, Path | None]:
    """Find any asset (official preset or custom asset) by ID and resolve its absolute image path."""
    aid = asset_id.strip().upper()

    # 1. Check custom assets
    custom_chars, custom_props, custom_scenes = load_custom_assets()
    for cat, items in [("characters", custom_chars), ("props", custom_props), ("scenes", custom_scenes)]:
        for item in items:
            if str(item.get("id", "")).upper() == aid:
                tuku_dir = get_custom_library_dir()
                if tuku_dir:
                    candidate = tuku_dir / cat / f"{aid}.webp"
                    if candidate.is_file():
                        return item, candidate
                mirror_candidate = CUSTOM_IMAGES_DIR / cat / f"{aid}.webp"
                if mirror_candidate.is_file():
                    return item, mirror_candidate

    # 2. Check official presets
    for cat, preset_file in [
        ("characters", PRESET_CHARACTERS_JSON),
        ("props", PRESET_PROPS_JSON),
        ("scenes", PRESET_SCENES_JSON)
    ]:
        if preset_file.exists():
            try:
                presets = json.loads(preset_file.read_text(encoding="utf-8"))
                if isinstance(presets, list):
                    for item in presets:
                        if str(item.get("id", "")).upper() == aid:
                            raw_img = str(item.get("image", ""))
                            clean_img = raw_img.replace("../", "").lstrip("/\\")
                            preset_img = ROOT / clean_img
                            if preset_img.is_file():
                                return item, preset_img
            except Exception:
                pass

    return None, None


def replace_asset_image(asset_id: str, new_source_image: Path | str) -> dict[str, object]:
    """Replace an existing custom asset's benchmark image while preserving its ID."""
    aid = asset_id.strip().upper()
    tuku_dir = get_custom_library_dir()
    if not tuku_dir:
        raise RuntimeError("Custom library directory is not initialized.")

    src_path = Path(new_source_image)
    if not src_path.is_file():
        raise FileNotFoundError(f"New image file not found: {new_source_image}")

    manifest_file = tuku_dir / "library.json"
    if not manifest_file.exists():
        raise FileNotFoundError("library.json not found in custom library.")

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    found_cat = None
    target_entry = None
    for cat in ("characters", "props", "scenes"):
        for entry in manifest.get(cat, []):
            if str(entry.get("id", "")).upper() == aid:
                found_cat = cat
                target_entry = entry
                break
        if found_cat:
            break

    if not found_cat or not target_entry:
        raise KeyError(f"Custom asset {aid} not found in custom library (official presets cannot be replaced).")

    dest_filename = f"{aid}.webp"
    dest_path = tuku_dir / found_cat / dest_filename
    mirror_path = CUSTOM_IMAGES_DIR / found_cat / dest_filename
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    mirror_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        from PIL import Image
        with Image.open(src_path) as im:
            if im.mode not in ("RGB", "RGBA"):
                im = im.convert("RGBA" if "transparency" in im.info or "A" in im.mode else "RGB")
            im.save(dest_path, "WEBP", quality=92)
            im.save(mirror_path, "WEBP", quality=92)
    except Exception:
        shutil.copy2(src_path, dest_path)
        shutil.copy2(src_path, mirror_path)

    target_entry["updated_at"] = date.today().isoformat()
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    _trigger_rebuild()
    return target_entry


def update_asset_metadata(asset_id: str, name: str | None = None, name_en: str | None = None, tags: list[str] | None = None) -> dict[str, object]:
    """Update name, English name, and/or tags of an existing custom asset."""
    aid = asset_id.strip().upper()
    tuku_dir = get_custom_library_dir()
    if not tuku_dir:
        raise RuntimeError("Custom library directory is not initialized.")

    manifest_file = tuku_dir / "library.json"
    if not manifest_file.exists():
        raise FileNotFoundError("library.json not found.")

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    target_entry = None
    for cat in ("characters", "props", "scenes"):
        for entry in manifest.get(cat, []):
            if str(entry.get("id", "")).upper() == aid:
                target_entry = entry
                break
        if target_entry:
            break

    if not target_entry:
        raise KeyError(f"Custom asset {aid} not found in custom library.")

    if name is not None:
        target_entry["name"] = name
    if name_en is not None:
        target_entry["name_en"] = name_en
    if tags is not None:
        target_entry["tags"] = tags

    target_entry["updated_at"] = date.today().isoformat()
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    _trigger_rebuild()
    return target_entry


def delete_asset(asset_id: str) -> dict[str, object]:
    """Safely delete a custom asset from external library and cache, then rebuild gallery."""
    aid = asset_id.strip().upper()
    tuku_dir = get_custom_library_dir()
    if not tuku_dir:
        raise RuntimeError("Custom library directory is not initialized.")

    manifest_file = tuku_dir / "library.json"
    if not manifest_file.exists():
        raise FileNotFoundError("library.json not found.")

    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    found_cat = None
    target_idx = None
    deleted_entry = None

    for cat in ("characters", "props", "scenes"):
        for i, entry in enumerate(manifest.get(cat, [])):
            if str(entry.get("id", "")).upper() == aid:
                found_cat = cat
                target_idx = i
                deleted_entry = entry
                break
        if found_cat:
            break

    if not found_cat or target_idx is None or not deleted_entry:
        raise KeyError(f"Custom asset {aid} not found (official presets cannot be deleted).")

    # Remove files
    dest_filename = f"{aid}.webp"
    tuku_file = tuku_dir / found_cat / dest_filename
    if tuku_file.is_file():
        try:
            tuku_file.unlink()
        except Exception:
            pass

    mirror_file = CUSTOM_IMAGES_DIR / found_cat / dest_filename
    if mirror_file.is_file():
        try:
            mirror_file.unlink()
        except Exception:
            pass

    # Remove from manifest
    manifest[found_cat].pop(target_idx)
    manifest_file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

    _trigger_rebuild()
    return {"id": aid, "name": deleted_entry.get("name", aid), "category": found_cat, "deleted": True}


if __name__ == "__main__":
    tuku = get_custom_library_dir()
    print(f"Active custom library directory: {tuku}")
