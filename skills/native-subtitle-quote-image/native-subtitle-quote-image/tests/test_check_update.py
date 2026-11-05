import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


# 子进程继承 UTF-8 模式，避免 GBK 等默认编码下输出与解码不一致。
os.environ.setdefault("PYTHONUTF8", "1")

ROOT = Path(__file__).resolve().parents[1]
UPDATE_SCRIPT = (
    ROOT
    / "skills"
    / "native-subtitle-quote-image"
    / "scripts"
    / "check_update.py"
)
SPEC = importlib.util.spec_from_file_location("check_update", UPDATE_SCRIPT)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class UpdateCheckTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 8, 24, 8, 0, tzinfo=timezone.utc)

    def write_cache(
        self,
        path,
        version="9.9.9",
        age=timedelta(hours=1),
        reference_time=None,
    ):
        reference_time = reference_time or self.now
        path.write_text(
            json.dumps(
                {
                    "checked_at": MODULE.format_timestamp(reference_time - age),
                    "latest_version": version,
                    "release_url": "https://example.test/release",
                }
            ),
            encoding="utf-8",
        )

    def test_parse_version_accepts_release_tag(self):
        self.assertEqual(MODULE.parse_version("v2.1.1"), (2, 1, 1))
        self.assertEqual(MODULE.normalize_version("2.1.1"), "2.1.1")
        with self.assertRaises(ValueError):
            MODULE.parse_version("latest")

    def test_fresh_cache_reports_update_without_network(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "cache.json"
            self.write_cache(cache)
            fetcher = mock.Mock(side_effect=AssertionError("不应联网"))
            result = MODULE.check_for_update(
                now=self.now,
                cache_path=cache,
                fetcher=fetcher,
            )
        self.assertEqual(result["status"], "update_available")
        self.assertTrue(result["from_cache"])
        fetcher.assert_not_called()

    def test_stale_cache_fetches_and_writes_latest_release(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "cache.json"
            self.write_cache(cache, age=timedelta(days=2))
            result = MODULE.check_for_update(
                now=self.now,
                cache_path=cache,
                fetcher=lambda: {
                    "latest_version": "9.9.9",
                    "release_url": "https://example.test/v9.9.9",
                },
            )
            saved = json.loads(cache.read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "update_available")
        self.assertFalse(result["from_cache"])
        self.assertEqual(saved["latest_version"], "9.9.9")

    def test_network_failure_is_non_blocking(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = MODULE.check_for_update(
                now=self.now,
                cache_path=Path(tmp) / "missing.json",
                fetcher=mock.Mock(side_effect=OSError("offline")),
            )
        self.assertEqual(result["status"], "unavailable")
        self.assertIn("offline", result["error"])

    def test_fetch_latest_release_uses_verified_curl_fallback(self):
        payload = json.dumps(
            {
                "tag_name": "v2.1.1",
                "html_url": "https://example.test/v2.1.1",
            }
        )
        completed = subprocess.CompletedProcess(
            args=["curl"],
            returncode=0,
            stdout=payload,
            stderr="",
        )
        with mock.patch.object(
            MODULE.urllib.request,
            "urlopen",
            side_effect=MODULE.urllib.error.URLError("certificate"),
        ), mock.patch.object(MODULE.subprocess, "run", return_value=completed) as run:
            release = MODULE.fetch_latest_release()
        self.assertEqual(release["latest_version"], "2.1.1")
        self.assertEqual(release["release_url"], "https://example.test/v2.1.1")
        self.assertNotIn("-k", run.call_args.args[0])

    def test_cli_prints_cached_update_reminder(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = Path(tmp) / "cache.json"
            self.write_cache(
                cache,
                age=timedelta(minutes=1),
                reference_time=MODULE.utc_now(),
            )
            environment = os.environ.copy()
            environment["NATIVE_SUBTITLE_UPDATE_CACHE"] = str(cache)
            proc = subprocess.run(
                [sys.executable, str(UPDATE_SCRIPT)],
                capture_output=True,
                encoding="utf-8", errors="replace",
                check=True,
                env=environment,
            )
        self.assertIn("发现 Skill 新版本 v9.9.9", proc.stdout)
        self.assertIn(f"当前 v{MODULE.read_current_version()}", proc.stdout)


if __name__ == "__main__":
    unittest.main()
