#!/usr/bin/env python3
"""Check GitHub Releases for a newer Skill version without auto-updating."""

import argparse
import json
import os
import platform
import re
import subprocess
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path


REPOSITORY = "chengyi-ai/native-subtitle-quote-image"
LATEST_API = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
RELEASES_URL = f"https://github.com/{REPOSITORY}/releases"
CACHE_TTL = timedelta(hours=24)
VERSION_FILE = Path(__file__).resolve().parents[1] / "VERSION"


def parse_version(value):
    match = re.fullmatch(r"\s*v?(\d+)\.(\d+)\.(\d+)(?:[-+][0-9A-Za-z.-]+)?\s*", value)
    if not match:
        raise ValueError(f"无法识别版本号: {value!r}")
    return tuple(int(part) for part in match.groups())


def normalize_version(value):
    return ".".join(str(part) for part in parse_version(value))


def read_current_version():
    return normalize_version(VERSION_FILE.read_text(encoding="utf-8"))


def default_cache_path():
    override = os.environ.get("NATIVE_SUBTITLE_UPDATE_CACHE")
    if override:
        return Path(override).expanduser()

    system = platform.system()
    if system == "Darwin":
        root = Path.home() / "Library" / "Caches"
    elif system == "Windows":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        root = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return root / "native-subtitle-quote-image" / "update-check.json"


def utc_now():
    return datetime.now(timezone.utc)


def format_timestamp(value):
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def parse_timestamp(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def read_cache(path):
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        latest_version = normalize_version(payload["latest_version"])
        checked_at = parse_timestamp(payload["checked_at"])
        release_url = payload.get("release_url") or RELEASES_URL
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None
    return {
        "latest_version": latest_version,
        "release_url": release_url,
        "checked_at": checked_at,
    }


def cache_is_fresh(cache, now):
    if not cache:
        return False
    age = now - cache["checked_at"]
    return timedelta(0) <= age < CACHE_TTL


def write_cache(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)


def release_from_payload(payload):
    latest_version = normalize_version(payload["tag_name"])
    return {
        "latest_version": latest_version,
        "release_url": payload.get("html_url") or RELEASES_URL,
    }


def fetch_latest_release(timeout=4):
    request = urllib.request.Request(
        LATEST_API,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "native-subtitle-quote-image-update-check",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return release_from_payload(json.load(response))
    except (OSError, urllib.error.URLError) as urllib_error:
        # Python.org builds on macOS can lack a configured CA bundle. Use the
        # operating system's curl as a verified-HTTPS fallback; never disable TLS.
        try:
            proc = subprocess.run(
                [
                    "curl",
                    "-fsSL",
                    "--connect-timeout",
                    str(timeout),
                    "--max-time",
                    str(timeout),
                    "-H",
                    "Accept: application/vnd.github+json",
                    "-A",
                    "native-subtitle-quote-image-update-check",
                    LATEST_API,
                ],
                capture_output=True,
                encoding="utf-8",
                errors="replace",
                check=False,
                timeout=timeout + 1,
            )
        except (OSError, subprocess.SubprocessError) as curl_error:
            raise OSError(
                f"Python HTTPS 失败: {urllib_error}; curl 回退失败: {curl_error}"
            ) from curl_error
        if proc.returncode != 0:
            detail = proc.stderr.strip() or f"退出码 {proc.returncode}"
            raise OSError(
                f"Python HTTPS 失败: {urllib_error}; curl 回退失败: {detail}"
            )
        return release_from_payload(json.loads(proc.stdout))


def check_for_update(force=False, now=None, cache_path=None, fetcher=None):
    now = now or utc_now()
    cache_path = cache_path or default_cache_path()
    fetcher = fetcher or fetch_latest_release
    current_version = read_current_version()
    cache = read_cache(cache_path)
    error = None

    if cache_is_fresh(cache, now) and not force:
        release = cache
        from_cache = True
    else:
        try:
            release = fetcher()
            release = {
                "latest_version": normalize_version(release["latest_version"]),
                "release_url": release.get("release_url") or RELEASES_URL,
                "checked_at": now,
            }
            from_cache = False
            try:
                write_cache(
                    cache_path,
                    {
                        "checked_at": format_timestamp(now),
                        "latest_version": release["latest_version"],
                        "release_url": release["release_url"],
                    },
                )
            except OSError as exc:
                error = f"无法写入更新缓存: {exc}"
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError, urllib.error.URLError) as exc:
            error = f"无法检查更新: {exc}"
            if cache:
                release = cache
                from_cache = True
            else:
                return {
                    "status": "unavailable",
                    "current_version": current_version,
                    "latest_version": None,
                    "release_url": RELEASES_URL,
                    "checked_at": None,
                    "from_cache": False,
                    "error": error,
                }

    latest_version = release["latest_version"]
    status = (
        "update_available"
        if parse_version(latest_version) > parse_version(current_version)
        else "up_to_date"
    )
    return {
        "status": status,
        "current_version": current_version,
        "latest_version": latest_version,
        "release_url": release.get("release_url") or RELEASES_URL,
        "checked_at": format_timestamp(release["checked_at"]),
        "from_cache": from_cache,
        "error": error,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true", help="忽略 24 小时缓存并立即检查")
    parser.add_argument("--json", action="store_true", help="输出机器可读 JSON")
    parser.add_argument("--verbose", action="store_true", help="没有更新或检查失败时也显示状态")
    args = parser.parse_args()

    result = check_for_update(force=args.force)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result["status"] == "update_available":
        print(
            f"发现 Skill 新版本 v{result['latest_version']} "
            f"（当前 v{result['current_version']}）：{result['release_url']}"
        )
    elif args.verbose and result["status"] == "up_to_date":
        print(f"当前已是最新版 v{result['current_version']}。")
    elif args.verbose:
        print(result["error"] or "暂时无法检查更新。")

    # 更新检查永远不阻断主要任务。
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
