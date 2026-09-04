"""Image metadata parsing and heuristic default-camera descriptor helpers."""

from __future__ import annotations

import argparse
import struct
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TypeAlias

JsonValue: TypeAlias = str | int | float | bool | None | Sequence["JsonValue"] | Mapping[str, "JsonValue"]


def png_size(data: bytes) -> tuple[int, int] | None:
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        return struct.unpack(">II", data[16:24])
    return None


def gif_size(data: bytes) -> tuple[int, int] | None:
    if data[:6] in {b"GIF87a", b"GIF89a"} and len(data) >= 10:
        return struct.unpack("<HH", data[6:10])
    return None


def jpeg_size(data: bytes) -> tuple[int, int] | None:
    if not data.startswith(b"\xff\xd8"):
        return None
    index = 2
    while index + 9 < len(data):
        if data[index] != 0xFF:
            index += 1
            continue
        marker = data[index + 1]
        index += 2
        if marker in {0xD8, 0xD9}:
            continue
        if index + 2 > len(data):
            return None
        length = struct.unpack(">H", data[index : index + 2])[0]
        if length < 2 or index + length > len(data):
            return None
        if marker in {0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7, 0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF} and length >= 7:
            height, width = struct.unpack(">HH", data[index + 3 : index + 7])
            return width, height
        index += length
    return None


def webp_size(data: bytes) -> tuple[int, int] | None:
    if len(data) < 30 or data[:4] != b"RIFF" or data[8:12] != b"WEBP":
        return None
    chunk = data[12:16]
    if chunk == b"VP8X":
        width = 1 + int.from_bytes(data[24:27], "little")
        height = 1 + int.from_bytes(data[27:30], "little")
        return width, height
    if chunk == b"VP8 ":
        start = data.find(b"\x9d\x01\x2a")
        if start != -1 and start + 7 <= len(data):
            width, height = struct.unpack("<HH", data[start + 3 : start + 7])
            return width & 0x3FFF, height & 0x3FFF
    return None


def bmp_size(data: bytes) -> tuple[int, int] | None:
    if len(data) >= 26 and data[:2] == b"BM":
        width = struct.unpack("<I", data[18:22])[0]
        height = abs(struct.unpack("<i", data[22:26])[0])
        return width, height
    return None


def detect_size(data: bytes) -> tuple[int, int] | None:
    return png_size(data) or jpeg_size(data) or gif_size(data) or webp_size(data) or bmp_size(data)


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def estimate_fov(aspect: float | None) -> tuple[float, str]:
    """Return the established default vertical FOV guess and rationale."""
    if aspect is not None and aspect < 0.75:
        return 38.0, "default guess for a portrait-oriented photo (typical phone/short-tele framing)"
    return 35.0, "default guess for a landscape/square photo (typical phone/short-tele framing)"


def build_camera(image: Path, args: argparse.Namespace) -> dict[str, JsonValue]:
    """Build the existing heuristic reference-camera descriptor from image metadata."""
    size = detect_size(image.read_bytes())
    warnings: list[str] = []
    if size is None:
        warnings.append("could not read image dimensions; aspect defaults to 1.0")
        width = height = None
        aspect = 1.0
    else:
        width, height = size
        aspect = round(width / height, 4) if height else 1.0
    default_fov, fov_rationale = estimate_fov(aspect)
    fov_degrees = args.fov_degrees if args.fov_degrees is not None else default_fov
    fov_source = "user-supplied" if args.fov_degrees is not None else "default-guess"
    distance = args.distance if args.distance is not None else 2.5
    distance_source = "user-supplied" if args.distance is not None else "placeholder"
    return {
        "version": "1.0",
        "sourceImage": str(image),
        "solver": "stage1_intake/solve_camera_pose.py",
        "method": "heuristic default-guess camera, not solved from image content; image dimensions give an exact aspect ratio, everything else is a starting point for agent refinement",
        "imageWidth": width,
        "imageHeight": height,
        "fovDegrees": {"value": round(fov_degrees, 2), "source": fov_source, "agentFill": fov_source == "default-guess", "rationale": fov_rationale},
        "aspect": {"value": aspect, "source": "image-dimensions" if size else "fallback-default", "agentFill": size is None},
        "orientation": {
            "yawDegrees": {"value": args.yaw, "source": "placeholder", "agentFill": True},
            "pitchDegrees": {"value": args.pitch, "source": "placeholder", "agentFill": True},
            "rollDegrees": {"value": args.roll, "source": "placeholder", "agentFill": True},
            "note": "0/0/0 assumes a straight-on, level shot; adjust by eye against the reference image.",
        },
        "position": {
            "hint": [0.0, args.height_offset, distance],
            "distance": {"value": distance, "source": distance_source, "agentFill": distance_source == "placeholder"},
            "note": "Position hint assumes the subject is centered at the origin and the camera looks down -Z.",
        },
        "confidence": 0.35 if size else 0.15,
        "limitations": [
            "no true camera calibration is performed; focal length/FOV/orientation are not recovered from pixels",
            "fovDegrees is a genre default, not a measurement; wrong FOV distorts perceived proportions under overlay",
            "orientation and position are placeholders and will almost always need manual/agent adjustment",
            "this script cannot detect lens distortion, perspective foreshortening, or non-zero roll",
        ] + warnings,
        "note": "Final camera match must be confirmed by overlay review: render the fitted mesh from this camera, place it beside or over the reference image, and adjust fovDegrees/orientation/position until silhouette and landmark alignment match before trusting projected texture bakes.",
    }
