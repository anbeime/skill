#!/usr/bin/env python3
"""Install this skill for Qoder or Codex on Windows, macOS, and Linux.

The installer copies the skill into the target application's skill directory,
preserves an existing mail configuration, and optionally runs the automated
setup bootstrapper.
"""
import argparse
import fnmatch
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def destination_is_inside_source(source: Path, destination: Path) -> bool:
    """Return whether copying would recursively copy an install into itself."""
    try:
        destination.relative_to(source)
        return True
    except ValueError:
        return False


def _is_first_install(destination: Path) -> bool:
    """Return True if no setup-completed marker exists in the destination."""
    return not (destination / "state" / ".setup_completed.json").exists()


def read_ignore_patterns(path: Path) -> list[str]:
    """Read newline-separated ignore patterns from a file."""
    if not path.exists():
        return []
    return [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]


def should_include(name: str, ignores: list[str]) -> bool:
    """Return False if a file or directory name matches an ignore pattern."""
    for pattern in ignores:
        normalized = pattern.rstrip("/")
        if fnmatch.fnmatch(name, normalized) or name == normalized or name.startswith(normalized + os.sep):
            return False
    return True


def copy_skill(source: Path, destination: Path, ignores: list[str]) -> list[str]:
    """Copy skill files while preserving an existing config and honouring ignores."""
    copied: list[str] = []
    destination.mkdir(parents=True, exist_ok=True)

    for item in source.iterdir():
        if not should_include(item.name, ignores):
            continue
        target = destination / item.name
        if item.is_dir():
            # Merge directories so a user's state/config and future runtime
            # files survive an upgrade. Individual skill files are replaced.
            target.mkdir(parents=True, exist_ok=True)
            nested_ignores = ignores
            for child in item.rglob("*"):
                relative = child.relative_to(item)
                if any(not should_include(part, nested_ignores) for part in relative.parts):
                    continue
                child_target = target / relative
                if child.is_dir():
                    child_target.mkdir(parents=True, exist_ok=True)
                else:
                    child_target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(child, child_target)
            copied.append(str(target.relative_to(destination)))
        else:
            if item.name == "email_concierge_config.json" and target.exists():
                continue
            shutil.copy2(item, target)
            copied.append(item.name)

    # Ensure runtime directories exist.
    (destination / "state").mkdir(parents=True, exist_ok=True)
    return copied


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Email Concierge skill")
    parser.add_argument("--target", choices=("qoder", "codex"), default="qoder")
    parser.add_argument("--destination")
    parser.add_argument("--setup", dest="setup", action="store_true", help="Run automatic dependency setup (default)")
    parser.add_argument("--no-setup", dest="setup", action="store_false", help="Copy files without installing dependencies")
    parser.add_argument("--first-install", dest="first_install", action="store_true", default=None,
                        help="Treat as first install (allows system package manager installs)")
    parser.add_argument("--no-first-install", dest="first_install", action="store_false",
                        help="Treat as subsequent install")
    parser.add_argument("--json", action="store_true", help="Output structured result as JSON")
    parser.set_defaults(setup=True)
    args = parser.parse_args()

    base = Path(args.destination).expanduser() if args.destination else Path.home() / f".{args.target}" / "skills"
    destination = (base / "email-concierge").resolve()
    if destination_is_inside_source(ROOT, destination):
        parser.error("--destination must be outside the source skill directory")

    is_first = args.first_install if args.first_install is not None else _is_first_install(destination)

    ignores = read_ignore_patterns(ROOT / ".qoderignore")
    copied = copy_skill(ROOT, destination, ignores)

    result = {
        "target": args.target,
        "destination": str(destination),
        "copied": copied,
        "setup_run": False,
        "setup_result": None,
        "error": "",
    }

    if args.setup:
        result["setup_run"] = True
        try:
            setup_script = destination / "setup_auto.py"
            setup_cmd = [
                sys.executable, str(setup_script),
                "--project-dir", str(destination),
                "--yes", "--json",
            ]
            if is_first:
                setup_cmd.append("--first-install")
            completed = subprocess.run(
                setup_cmd, capture_output=True, text=True, check=False,
            )
            result["setup_result"] = completed.returncode
            result["setup_stdout"] = completed.stdout[-4000:]
            result["setup_stderr"] = completed.stderr[-4000:]
            if completed.returncode != 0:
                result["error"] = "setup_auto.py returned a non-zero exit code"
        except OSError as error:
            result["error"] = str(error)

    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"Installed {args.target} skill to {destination}")
        if args.setup and result["setup_result"] != 0:
            print("Setup reported a non-zero exit code; run setup manually if needed.")

    return 0 if not result["error"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
