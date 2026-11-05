#!/usr/bin/env python3
"""Compatibility entry point for the canonical Tweet style importer."""
from __future__ import annotations

import runpy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
CANONICAL_SCRIPTS = ROOT / "scripts"

if str(CANONICAL_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(CANONICAL_SCRIPTS))


if __name__ == "__main__":
    runpy.run_path(str(CANONICAL_SCRIPTS / "import_tweet_style.py"), run_name="__main__")
