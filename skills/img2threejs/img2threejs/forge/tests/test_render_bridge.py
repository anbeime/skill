import json
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

from forge.stage4_review.render_bridge import (
    init_manifest,
    record_capture,
    validate_manifest,
    write_manifest,
)


def write_png(path: Path, width: int = 8, height: int = 8) -> None:
    signature = b"\x89PNG\r\n\x1a\n"

    def chunk(kind: bytes, payload: bytes) -> bytes:
        checksum = zlib.crc32(kind)
        checksum = zlib.crc32(payload, checksum) & 0xFFFFFFFF
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", checksum)

    rows = b"".join(b"\x00" + bytes([220, 80, 80]) * width for _ in range(height))
    path.write_bytes(
        signature
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(rows))
        + chunk(b"IEND", b"")
    )


class RenderBridgeTest(unittest.TestCase):
    def test_init_emits_required_camera_batch(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "reference.png"
            write_png(reference)
            manifest_path = root / "manifest.json"
            manifest = init_manifest(reference, "http://127.0.0.1:5173/#/character", manifest_path, (620, 1000), 1.0, "captures")
            self.assertEqual(manifest["schemaVersion"], 1)
            self.assertEqual({item["id"] for item in manifest["captures"]}, {
                "hero", "orbit-plus35", "orbit-minus35", "profile", "rear", "head-hero", "head-threequarter"
            })
            self.assertEqual(manifest["reference"]["sha256"], __import__("hashlib").sha256(reference.read_bytes()).hexdigest())

    def test_record_and_validate_preserve_screenshot_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "reference.png"
            screenshot = root / "captures" / "hero.png"
            screenshot.parent.mkdir()
            write_png(reference)
            write_png(screenshot, 16, 16)
            manifest_path = root / "manifest.json"
            manifest = init_manifest(reference, "http://127.0.0.1:5173", manifest_path, (620, 1000), 1.0, "captures")
            record_capture(manifest_path, manifest, "hero", screenshot, ready_signal=True)
            write_manifest(manifest_path, manifest)
            result = validate_manifest(manifest_path)
            self.assertTrue(result["passed"])
            saved = json.loads(manifest_path.read_text())
            self.assertEqual(saved["captures"][0]["status"], "recorded")
            self.assertEqual(saved["captures"][0]["image"]["width"], 16)

    def test_validate_detects_changed_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            reference = root / "reference.png"
            write_png(reference)
            manifest_path = root / "manifest.json"
            write_manifest(manifest_path, init_manifest(reference, "http://127.0.0.1:5173", manifest_path, (1, 1), 1.0, "captures"))
            reference.write_bytes(reference.read_bytes() + b"changed")
            result = validate_manifest(manifest_path)
            self.assertFalse(result["passed"])
            self.assertTrue(any("hash changed" in error for error in result["errors"]))
