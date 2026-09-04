#!/usr/bin/env python3
"""Manifest helpers for the v2 browser multi-pass evidence contract."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Callable


PASS_IDS = (
    "beauty",
    "alpha-silhouette",
    "semantic-id",
    "depth",
    "normal",
    "roughness-material-id",
)


def default_pass_records(prefix: str) -> dict[str, dict[str, Any]]:
    prefix = prefix.rstrip("/")
    return {
        pass_id: {"path": f"{prefix}/{pass_id}.png", "status": "pending"}
        for pass_id in PASS_IDS
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def record_pass(
    manifest_path: Path,
    pass_record: dict[str, Any],
    image_path: Path,
    probe: Callable[[Path], dict[str, Any]],
) -> dict[str, Any]:
    image_path = image_path.expanduser().resolve()
    if not image_path.is_file():
        raise ValueError(f"pass image does not exist: {image_path}")
    image = probe(image_path)
    if not image.get("type") or not image.get("width") or not image.get("height"):
        raise ValueError(f"pass image is not readable: {image_path}")
    try:
        relative = image_path.relative_to(manifest_path.parent.resolve()).as_posix()
    except ValueError:
        relative = str(image_path)
    pass_record.update(
        {
            "path": relative,
            "status": "recorded",
            "image": image,
            "sha256": _sha256(image_path),
        }
    )
    return pass_record


def validate_pass_records(
    manifest_path: Path,
    records: Any,
    probe: Callable[[Path], dict[str, Any]],
    *,
    require_complete: bool,
    label: str,
) -> list[str]:
    errors: list[str] = []
    if not isinstance(records, dict):
        if require_complete:
            errors.append(f"{label} pass records are missing")
        return errors
    for pass_id in PASS_IDS:
        record = records.get(pass_id)
        if not isinstance(record, dict):
            if require_complete:
                errors.append(f"{label} pass is missing: {pass_id}")
            continue
        if record.get("status") != "recorded":
            if require_complete:
                errors.append(f"{label} pass is not recorded: {pass_id}")
            continue
        value = record.get("path")
        if not value:
            errors.append(f"{label} pass has no path: {pass_id}")
            continue
        path_value = Path(value).expanduser()
        path = path_value if path_value.is_absolute() else manifest_path.parent / path_value
        if not path.is_file():
            errors.append(f"{label} pass file is missing: {path}")
            continue
        image = probe(path)
        if not image.get("type") or not image.get("width") or not image.get("height"):
            errors.append(f"{label} pass is unreadable: {path}")
        expected_hash = record.get("sha256")
        if expected_hash and expected_hash != _sha256(path):
            errors.append(f"{label} pass hash changed: {path}")
    return errors
