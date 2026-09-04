#!/usr/bin/env python3
"""Legacy CLI schema regression tests for camera fitting."""

from __future__ import annotations

import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from forge.stage1_intake import solve_camera_pose as camera_fit  # noqa: E402


MINIMAL_PNG_BYTES = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00"
    b"\x90wS\xde"
    b"\x00\x00\x00\x0cIDAT\x08\xd7c\xf8\xff\xff?\x00\x05\xfe\x02\xfeA\xbf\xb6\xcc"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)


class CameraFittingCliTest(unittest.TestCase):
    def test_legacy_cli_emits_descriptor_and_writes_matching_out_file(self):
        with tempfile.TemporaryDirectory() as directory:
            image = Path(directory) / "reference.png"
            out = Path(directory) / "camera.json"
            image.write_bytes(MINIMAL_PNG_BYTES)
            stdout = io.StringIO()

            with redirect_stdout(stdout):
                result = camera_fit.main([str(image), "--out", str(out)])

            self.assertEqual(result, 0)
            self.assertEqual(out.read_text(encoding="utf-8"), stdout.getvalue())
            payload = json.loads(stdout.getvalue())
            self.assertEqual(set(payload), {"referenceCamera"})
            descriptor = payload["referenceCamera"]
            self.assertEqual(
                set(descriptor),
                {
                    "version",
                    "sourceImage",
                    "solver",
                    "method",
                    "imageWidth",
                    "imageHeight",
                    "fovDegrees",
                    "aspect",
                    "orientation",
                    "position",
                    "confidence",
                    "limitations",
                    "note",
                },
            )
            self.assertEqual(descriptor["version"], "1.0")
            self.assertIsInstance(descriptor["sourceImage"], str)
            self.assertEqual(Path(descriptor["sourceImage"]), image.resolve())
            self.assertEqual(descriptor["solver"], "stage1_intake/solve_camera_pose.py")
            self.assertEqual(descriptor["method"], "heuristic default-guess camera, not solved from image content; image dimensions give an exact aspect ratio, everything else is a starting point for agent refinement")
            self.assertEqual(descriptor["imageWidth"], 1)
            self.assertEqual(descriptor["imageHeight"], 1)
            self.assertEqual(set(descriptor["fovDegrees"]), {"value", "source", "agentFill", "rationale"})
            self.assertIsInstance(descriptor["fovDegrees"]["rationale"], str)
            self.assertEqual(descriptor["fovDegrees"]["source"], "default-guess")
            self.assertIs(descriptor["fovDegrees"]["agentFill"], True)
            self.assertEqual(set(descriptor["aspect"]), {"value", "source", "agentFill"})
            self.assertEqual(descriptor["aspect"], {"value": 1.0, "source": "image-dimensions", "agentFill": False})
            self.assertEqual(descriptor["fovDegrees"]["value"], 35.0)
            self.assertEqual(set(descriptor["orientation"]), {"yawDegrees", "pitchDegrees", "rollDegrees", "note"})
            self.assertIsInstance(descriptor["orientation"]["note"], str)
            for scalar_name in ("yawDegrees", "pitchDegrees", "rollDegrees"):
                scalar = descriptor["orientation"][scalar_name]
                self.assertEqual(set(scalar), {"value", "source", "agentFill"})
                self.assertIsInstance(scalar["value"], float)
                self.assertEqual(scalar["source"], "placeholder")
                self.assertIs(scalar["agentFill"], True)
            self.assertEqual(set(descriptor["position"]), {"hint", "distance", "note"})
            self.assertIsInstance(descriptor["position"]["note"], str)
            self.assertEqual(descriptor["position"]["hint"], [0.0, 0.0, 2.5])
            self.assertEqual(set(descriptor["position"]["distance"]), {"value", "source", "agentFill"})
            self.assertEqual(descriptor["position"]["distance"], {"value": 2.5, "source": "placeholder", "agentFill": True})
            self.assertIsInstance(descriptor["confidence"], float)
            self.assertIsInstance(descriptor["limitations"], list)
            self.assertTrue(descriptor["limitations"])
            for limitation in descriptor["limitations"]:
                self.assertIsInstance(limitation, str)
            self.assertIsInstance(descriptor["note"], str)


if __name__ == "__main__":
    unittest.main(verbosity=2)
