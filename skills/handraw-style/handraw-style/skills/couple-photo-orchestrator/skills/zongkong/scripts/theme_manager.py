#!/usr/bin/env python3
"""Create, switch, and migrate multi-theme people-photo projects."""

from __future__ import annotations

import argparse
from pathlib import Path

from theme_workspace import initialize_theme, migrate_v2_project, read_yaml, resolve_theme, sync_theme, write_yaml


def create(args: argparse.Namespace) -> None:
    root = Path(args.project).resolve()
    manifest = migrate_v2_project(root)
    if manifest.get("workflow_version") != 3:
        raise SystemExit("theme creation requires a v3 project manifest")
    name = args.name.strip()
    if not name:
        raise SystemExit("--name is required")
    themes = manifest["themes"]
    number = int(themes["next_theme_number"])
    theme_id = f"THEME-{number:03d}"
    workspace = initialize_theme(root, theme_id, name, manifest.get("interaction_mode", "user_directed"))
    themes["items"].append({"id": theme_id, "name": name, "path": f"themes/{theme_id}", "stage": "DISCOVERY"})
    themes["next_theme_number"] = number + 1
    themes["active_theme_id"] = theme_id
    write_yaml(root / "project.yaml", manifest)
    print(f"{theme_id}\t{workspace}")


def switch(args: argparse.Namespace) -> None:
    root = Path(args.project).resolve()
    manifest = migrate_v2_project(root)
    if manifest.get("workflow_version") != 3:
        raise SystemExit("theme switching requires a v3 project manifest")
    _, theme_id = resolve_theme(root, args.theme_id)
    sync_theme(root, theme_id)
    manifest = read_yaml(root / "project.yaml")
    manifest["themes"]["active_theme_id"] = theme_id
    write_yaml(root / "project.yaml", manifest)
    print(theme_id)



def set_mode(args: argparse.Namespace) -> None:
    root = Path(args.project).resolve()
    manifest = migrate_v2_project(root)
    if manifest.get("workflow_version") != 3:
        raise SystemExit("mode switching requires a v3 project manifest")
    mode = args.mode
    manifest["interaction_mode"] = mode
    active = manifest.get("themes", {}).get("active_theme_id")
    write_yaml(root / "project.yaml", manifest)
    if active:
        workspace, _ = resolve_theme(root, active)
        state = read_yaml(workspace / "project.yaml")
        state["interaction_mode"] = mode
        state["confirmation_authority"] = "ai_recommendation" if mode == "card_draw" else "user"
        write_yaml(workspace / "project.yaml", state)
    print(mode)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    create_parser = subparsers.add_parser("create", help="create a numbered theme workspace; migrates a v2 project first")
    create_parser.add_argument("project")
    create_parser.add_argument("--name", required=True)
    create_parser.set_defaults(func=create)
    switch_parser = subparsers.add_parser("switch", help="select the active theme")
    switch_parser.add_argument("project")
    switch_parser.add_argument("theme_id")
    switch_parser.set_defaults(func=switch)
    mode_parser = subparsers.add_parser("set-mode", help="switch between user-directed and draw-card interaction without resetting the active theme")
    mode_parser.add_argument("project")
    mode_parser.add_argument("mode", choices=("user_directed", "card_draw"))
    mode_parser.set_defaults(func=set_mode)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
