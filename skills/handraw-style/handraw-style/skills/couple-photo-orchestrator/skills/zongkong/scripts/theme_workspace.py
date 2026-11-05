"""Shared v3 multi-theme workspace helpers for people-photo scripts."""

from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

import yaml


THEME_PREFIX = "THEME-"


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def write_yaml(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, allow_unicode=True, sort_keys=False), encoding="utf-8")


def theme_state(name: str, interaction_mode: str = "user_directed") -> dict:
    return {
        "workflow_version": 2,
        "theme_name": name,
        "stage": "DISCOVERY",
        "interaction_mode": interaction_mode,
        "confirmation_authority": "ai_recommendation" if interaction_mode == "card_draw" else "user",
        "quality_policy": {
            "detail_floor": "full_detail_no_compression",
            "session_independent": True,
            "restart_theme_preserves_quality": True,
            "location_specificity_required": True,
            "progressive_location_specificity": True,
            "discovery_location_level": "spacetime_anchor",
            "look_location_level": "shootable_zones",
            "shot_location_level": "micro_location",
            "no_invented_real_addresses": True,
            "unspecified_modern_location_fallback": "random_world_famous_named_place",
            "random_location_must_be_theme_compatible": True,
            "location_reroll_must_change_place": True,
        },
        "reference_photos": [],
        "identity_reference_policy": {
            "canonical_source": "original_user_upload",
            "derived_images_never_auto_promote": True,
            "explicit_user_promotion_required": True,
        },
        "identity_reference_history": [],
        "looks": [],
        "artifacts": {"couple_look_plan": None, "requirements_handoff": None, "shooting_plan": None, "generation_log": None, "shot_list": None, "shot_prompts": None, "shot_board": None, "shot_grid": None},
        "wardrobe_board": {"next_option_id": 1, "active_board": None, "selected_option_ids": [], "theme": None},
        "shot_list": {"default_shot_count_per_look": 8, "requested_shot_count_per_look": None},
        "shot_board": {"next_shot_id": 1, "active_board": None, "selected_shot_ids": [], "enlargements": []},
    }


def initialize_theme(root: Path, theme_id: str, name: str, interaction_mode: str = "user_directed") -> Path:
    workspace = root / "themes" / theme_id
    if workspace.exists():
        raise SystemExit(f"theme workspace already exists: {workspace}")
    for relative in (
        "references/identity", "references/style", "deliverables/generation-briefs",
        "deliverables/wardrobe-boards", "deliverables/shot-boards", "deliverables/shot-detail-briefs",
        "images/wardrobe-boards", "images/shot-boards", "images/shot-details",
    ):
        (workspace / relative).mkdir(parents=True, exist_ok=True)
    write_yaml(workspace / "project.yaml", theme_state(name, interaction_mode))
    return workspace


def migrate_v2_project(root: Path) -> dict:
    root_state = read_yaml(root / "project.yaml")
    if root_state.get("workflow_version") != 2:
        return root_state
    theme_id = "THEME-001"
    theme_name = root_state.get("theme_name") or root_state.get("shoot_type") or "原有主题"
    workspace = root / "themes" / theme_id
    workspace.mkdir(parents=True, exist_ok=False)
    for relative in ("deliverables", "images"):
        source = root / relative
        if source.exists():
            shutil.move(str(source), str(workspace / relative))
    style_source = root / "references" / "style"
    if style_source.exists():
        (workspace / "references").mkdir(parents=True, exist_ok=True)
        shutil.move(str(style_source), str(workspace / "references" / "style"))
    (workspace / "references" / "identity").mkdir(parents=True, exist_ok=True)
    root_state.pop("project_id", None)
    root_state.pop("created_at", None)
    root_state["theme_name"] = theme_name
    root_state.setdefault("quality_policy", theme_state(theme_name)["quality_policy"])
    write_yaml(workspace / "project.yaml", root_state)
    manifest = {
        "project_id": read_yaml(root / "project.yaml").get("project_id"),
        "created_at": now(),
        "workflow_version": 3,
        "interaction_mode": root_state.get("interaction_mode", "user_directed"),
        "shared_identity_references": read_yaml(root / "project.yaml").get("reference_photos", []),
        "identity_reference_policy": {"canonical_source": "original_user_upload", "derived_images_never_auto_promote": True, "explicit_user_promotion_required": True},
        "identity_reference_history": [],
        "themes": {"next_theme_number": 2, "active_theme_id": theme_id, "items": [{"id": theme_id, "name": theme_name, "path": f"themes/{theme_id}", "stage": root_state.get("stage", "DISCOVERY")}]},
    }
    write_yaml(root / "project.yaml", manifest)
    return manifest


def resolve_theme(root: Path, theme_id: str | None) -> tuple[Path, str | None]:
    root = root.resolve()
    state_path = root / "project.yaml"
    if not state_path.exists():
        raise SystemExit(f"missing project.yaml: {state_path}")
    state = read_yaml(state_path)
    if state.get("workflow_version") != 3:
        if theme_id:
            raise SystemExit("--theme-id is supported only by workflow_version: 3 projects")
        return root, None
    selected = theme_id or state.get("themes", {}).get("active_theme_id")
    items = {item.get("id"): item for item in state.get("themes", {}).get("items", [])}
    item = items.get(selected)
    if not item:
        raise SystemExit(f"unknown theme id: {selected}")
    workspace = root / item["path"]
    if not (workspace / "project.yaml").exists():
        raise SystemExit(f"missing theme workspace: {workspace}")
    return workspace, selected


def sync_theme(root: Path, theme_id: str | None) -> None:
    if not theme_id:
        return
    root = root.resolve()
    manifest = read_yaml(root / "project.yaml")
    for item in manifest.get("themes", {}).get("items", []):
        if item.get("id") == theme_id:
            item["stage"] = read_yaml(root / item["path"] / "project.yaml").get("stage", "DISCOVERY")
            break
    write_yaml(root / "project.yaml", manifest)
