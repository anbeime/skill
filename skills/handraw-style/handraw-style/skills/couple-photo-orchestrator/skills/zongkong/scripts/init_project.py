#!/usr/bin/env python3
"""Initialize a non-destructive people-photo project workspace."""

from __future__ import annotations

import argparse
import re
from datetime import datetime, timezone
from pathlib import Path


PROJECT_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize a people-photo project")
    parser.add_argument("project_id", help="lowercase letters, numbers, and hyphens")
    parser.add_argument("--project-dir", type=Path, required=True, help="user-selected absolute project directory")
    args = parser.parse_args()

    if not PROJECT_ID.fullmatch(args.project_id):
        parser.error("project_id must use lowercase letters, numbers, and hyphens")

    if not args.project_dir.is_absolute():
        parser.error("--project-dir must be an absolute path selected by the user")

    project_dir = args.project_dir.expanduser().resolve()
    if project_dir.exists():
        if not project_dir.is_dir():
            parser.error(f"--project-dir must be a directory path: {project_dir}")
        if any(project_dir.iterdir()):
            parser.error(f"refusing to initialize a non-empty project directory: {project_dir}")

    for relative in ("references/identity", "references/style", "themes"):
        (project_dir / relative).mkdir(parents=True, exist_ok=True)

    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    state = f'''project_id: {args.project_id}
created_at: {created_at}
workflow_version: 3
interaction_mode: user_directed
story_card_name: null
creative_history: []
spacetime_passport: []
direction_type_history: []
remix_history: []
shared_identity_references: []
identity_reference_policy:
  canonical_source: original_user_upload
  derived_images_never_auto_promote: true
  explicit_user_promotion_required: true
identity_reference_history: []
themes:
  next_theme_number: 1
  active_theme_id: null
  items: []
'''
    (project_dir / "project.yaml").write_text(state, encoding="utf-8")
    print(project_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
