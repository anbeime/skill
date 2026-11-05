#!/usr/bin/env python3
"""Bump the Skill version everywhere it is pinned (VERSION, plugin.json, validate_repo.py)."""

import argparse
import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VERSION_FILE = ROOT / "skills" / "native-subtitle-quote-image" / "VERSION"
PLUGIN = ROOT / ".codex-plugin" / "plugin.json"
VALIDATOR = ROOT / "scripts" / "validate_repo.py"
BUMPS = ("major", "minor", "patch")


def parse_version(value):
    match = re.fullmatch(r"\s*v?(\d+)\.(\d+)\.(\d+)\s*", value)
    if not match:
        raise ValueError(f"无法识别版本号: {value!r}")
    return tuple(int(part) for part in match.groups())


def next_version(current, bump):
    major, minor, patch = parse_version(current)
    if bump == "major":
        return f"{major + 1}.0.0"
    if bump == "minor":
        return f"{major}.{minor + 1}.0"
    if bump == "patch":
        return f"{major}.{minor}.{patch + 1}"
    return ".".join(str(part) for part in parse_version(bump))


def write_version(root, version):
    version_file = root / VERSION_FILE.relative_to(ROOT)
    plugin_file = root / PLUGIN.relative_to(ROOT)
    validator_file = root / VALIDATOR.relative_to(ROOT)

    version_file.write_text(f"{version}\n", encoding="utf-8")

    plugin = plugin_file.read_text(encoding="utf-8")
    updated, count = re.subn(
        r'^(  "version": )"[^"]+"', rf'\g<1>"{version}"', plugin, flags=re.MULTILINE
    )
    if count != 1:
        raise RuntimeError("plugin.json 中找不到唯一的 version")
    json.loads(updated)
    plugin_file.write_text(updated, encoding="utf-8")

    validator = validator_file.read_text(encoding="utf-8")
    updated, count = re.subn(
        r'^EXPECTED_VERSION = "[^"]+"$',
        f'EXPECTED_VERSION = "{version}"',
        validator,
        flags=re.MULTILINE,
    )
    if count != 1:
        raise RuntimeError("validate_repo.py 中找不到唯一的 EXPECTED_VERSION")
    validator_file.write_text(updated, encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("bump", help="major / minor / patch，或明确的版本号如 2.4.0")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)

    current = (args.root / VERSION_FILE.relative_to(ROOT)).read_text(encoding="utf-8").strip()
    try:
        version = next_version(current, args.bump)
    except ValueError as exc:
        parser.error(str(exc))
    if parse_version(version) <= parse_version(current):
        parser.error(f"新版本 {version} 必须高于当前版本 {current}")
    write_version(args.root, version)
    print(version)


if __name__ == "__main__":
    sys.exit(main())
