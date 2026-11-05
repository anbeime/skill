#!/usr/bin/env python3
"""Validate legacy and v2 people-photo project workspaces."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml


LEGACY_STAGES = {
    "DISCOVERY", "BRIEF_CONFIRMED", "LOOK_PLAN_REVIEW", "WARDROBE_TEXT_REVIEW",
    "WARDROBE_GRID_REVIEW", "LOOKS_CONFIRMED", "SHOOT_PLAN_REVIEW",
    "GENERATION_APPROVED", "MAIN_VISUAL_REVIEW", "SHOTLIST_REVIEW",
}
V2_STAGES = {
    "DISCOVERY", "BRIEF_CONFIRMED", "LOOK_PLAN_REVIEW", "WARDROBE_TEXT_REVIEW",
    "WARDROBE_GRID_REVIEW", "LOOKS_CONFIRMED",
    "SHOTLIST_REVIEW", "SHOT_GRID_REVIEW",
}
PRE_CONFIRMATION = {"DISCOVERY", "BRIEF_CONFIRMED", "LOOK_PLAN_REVIEW", "WARDROBE_TEXT_REVIEW", "WARDROBE_GRID_REVIEW"}
CONFIRMED_OR_LATER = {"LOOKS_CONFIRMED", "SHOOT_PLAN_REVIEW", "GENERATION_APPROVED", "MAIN_VISUAL_REVIEW", "SHOTLIST_REVIEW", "SHOT_GRID_REVIEW"}
LEGACY_SHOOT_PLAN_OR_LATER = {"SHOOT_PLAN_REVIEW", "GENERATION_APPROVED", "MAIN_VISUAL_REVIEW", "SHOTLIST_REVIEW"}
BOARD_SIZE = 8


GENERIC_LOCATIONS = {
    "室内", "户外", "酒店", "公寓", "民宿", "卧室", "客厅", "书房", "街头", "街区", "城市",
    "海边", "湖边", "河边", "庭院", "古镇", "公园", "长廊", "宫殿", "山门", "影棚", "摄影棚",
    "indoor", "outdoor", "hotel", "apartment", "street", "city", "beach", "garden", "studio",
}
VALID_LOCATION_MODES = {"real_world", "historical_real_world", "future_landmark", "source_work", "original_fictional"}
VALID_VERIFICATION = {"user_supplied", "verified_current", "known_public_place_needs_current_verification", "conceptual_private_interior"}


def _text(value: object) -> str:
    return str(value or "").strip()


def _generic_location(value: object) -> bool:
    text = _text(value).lower().strip(" .，,。;；:-—_/\\")
    return not text or text in GENERIC_LOCATIONS


def validate_location_scene(scene: dict, label: str, errors: list[str]) -> None:
    """Validate pre-shot location anchors. Micro-location is intentionally optional here."""
    if not isinstance(scene, dict):
        errors.append(f"{label} must be a structured Location Card")
        return
    mode = _text(scene.get("location_mode"))
    indoor_outdoor = _text(scene.get("indoor_outdoor"))
    if mode not in VALID_LOCATION_MODES:
        errors.append(f"{label} location_mode must be one of {sorted(VALID_LOCATION_MODES)}")
    if indoor_outdoor and indoor_outdoor not in {"indoor", "outdoor", "mixed"}:
        errors.append(f"{label} indoor_outdoor must be indoor, outdoor, or mixed")

    if mode in {"real_world", "historical_real_world", "future_landmark"}:
        if not _text(scene.get("city")):
            errors.append(f"{label} real-world location requires city")
        named = scene.get("named_place")
        district = scene.get("district_or_area")
        street = scene.get("street_or_route")
        area = district or street
        if _generic_location(named) and _generic_location(area):
            errors.append(f"{label} real-world location requires a concrete area, scenic zone, street, or named place")
        if indoor_outdoor == "indoor" and _generic_location(named) and _generic_location(street):
            errors.append(f"{label} indoor real-world location requires a real named venue/building or a real street/route anchor; district alone is not specific enough")
        verification = _text(scene.get("verification_status"))
        if verification not in VALID_VERIFICATION:
            errors.append(f"{label} real-world location requires a valid verification_status")
        if mode in {"historical_real_world", "future_landmark"} and not _text(scene.get("era_or_period")):
            errors.append(f"{label} historical_real_world/future_landmark location requires era_or_period")
    elif mode == "source_work":
        if not _text(scene.get("source_work")):
            errors.append(f"{label} source_work location requires source_work")
        if _generic_location(scene.get("in_world_location")):
            errors.append(f"{label} source_work location requires a concrete in_world_location")
        if not (_text(scene.get("era_or_period")) or _text(scene.get("world_state_or_chapter"))):
            errors.append(f"{label} source_work location requires era_or_period or world_state_or_chapter")
    elif mode == "original_fictional":
        if _generic_location(scene.get("named_place")):
            errors.append(f"{label} original_fictional location requires a named fictional place")
        if not (_text(scene.get("city")) or _text(scene.get("district_or_area"))):
            errors.append(f"{label} original_fictional location requires world/city/region context")
        if not (_text(scene.get("era_or_period")) or _text(scene.get("world_state_or_chapter"))):
            errors.append(f"{label} original_fictional location requires era/world-state context")


def read_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


NO_COMPRESSION_TERMS = (
    "其他人同风格", "其余人类似", "剩下的人类似", "其余成员同款", "其他成员类似",
    "同上", "沿用前文即可", "场景同前", "服装统一协调即可",
)


def validate_quality_policy(state: dict, errors: list[str]) -> None:
    policy = state.get("quality_policy")
    if state.get("workflow_version") != 2:
        return
    if not isinstance(policy, dict):
        errors.append("workflow v2 theme requires quality_policy")
        return
    required = {
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
    }
    for key, expected in required.items():
        if policy.get(key) != expected:
            errors.append(f"quality_policy.{key} must equal {expected!r}")


def contains_compression_phrase(value: object) -> bool:
    text = _text(value)
    return any(term in text for term in NO_COMPRESSION_TERMS)


def validate_wardrobe(project: Path, state: dict, stage: str, errors: list[str]) -> None:
    wardrobe = state.get("wardrobe_board")
    if not wardrobe:
        return
    boards_dir = project / "deliverables" / "wardrobe-boards"
    board_paths = sorted(path for path in boards_dir.glob("BOARD-*.yaml") if path.stem.count("-") == 1) if boards_dir.exists() else []
    all_ids: list[int] = []
    boards: dict[str, dict] = {}
    for path in board_paths:
        board = read_yaml(path)
        board_id = board.get("board_id")
        options = board.get("options", [])
        if not board_id or not isinstance(options, list) or len(options) != 6:
            errors.append(f"{path.name} must contain exactly six options")
            continue
        ids = [option.get("option_id") for option in options]
        if not all(isinstance(value, int) for value in ids) or ids != list(range(min(ids), min(ids) + 6)):
            errors.append(f"{path.name} option ids must be six consecutive integers")
        all_ids.extend(ids)
        boards[board_id] = board
    if len(set(all_ids)) != len(all_ids):
        errors.append("wardrobe option ids must be unique within a project")
    expected_next = max(all_ids, default=0) + 1
    if wardrobe.get("next_option_id") != expected_next:
        errors.append(f"wardrobe_board.next_option_id must equal {expected_next}")
    active = wardrobe.get("active_board")
    if stage in {"WARDROBE_TEXT_REVIEW", "WARDROBE_GRID_REVIEW"}:
        if active not in boards:
            errors.append("wardrobe review requires an existing active board")
        elif stage == "WARDROBE_TEXT_REVIEW" and boards[active].get("status") != "text_review":
            errors.append("WARDROBE_TEXT_REVIEW requires an active text_review board")
        elif stage == "WARDROBE_GRID_REVIEW":
            board = boards[active]
            image = board.get("grid_image")
            if board.get("status") != "grid_review" or not image or not (project / image).exists():
                errors.append("WARDROBE_GRID_REVIEW requires an active board with an existing grid image")
            if board.get("grid_mode") != "single_grid":
                errors.append("WARDROBE_GRID_REVIEW supports only single_grid boards; recreate legacy composed boards")
            source = board.get("grid_source_image")
            if not source or not (project / source).exists():
                errors.append("WARDROBE_GRID_REVIEW requires one existing source grid image")
    selected = wardrobe.get("selected_option_ids", [])
    if selected and not all(option_id in all_ids for option_id in selected):
        errors.append("wardrobe selected_option_ids must refer to existing options")



def validate_identity_reference_policy(project_data: dict, errors: list[str]) -> None:
    policy = project_data.get("identity_reference_policy") or {}
    if not policy:
        return  # legacy handoffs remain readable
    if policy.get("canonical_source") != "original_user_upload":
        errors.append("identity_reference_policy.canonical_source must be original_user_upload")
    if policy.get("derived_images_never_auto_promote") is not True:
        errors.append("identity_reference_policy.derived_images_never_auto_promote must be true")
    if policy.get("explicit_user_promotion_required") is not True:
        errors.append("identity_reference_policy.explicit_user_promotion_required must be true")
    for item in project_data.get("identity_map", []) if isinstance(project_data.get("identity_map", []), list) else []:
        if not isinstance(item, dict):
            continue
        pid = _text(item.get("participant_id")) or "unknown"
        originals = item.get("canonical_original_references") or []
        active = item.get("active_identity_references") or item.get("identity_references") or []
        promoted = bool(item.get("explicit_promotion"))
        source = _text(item.get("active_reference_source")) or "original_user_upload"
        if active and not originals:
            errors.append(f"identity_map {pid} has active references but no canonical_original_references")
        if originals and not promoted and list(active) != list(originals):
            errors.append(f"identity_map {pid} cannot replace canonical originals without explicit promotion")
        if not promoted and source != "original_user_upload":
            errors.append(f"identity_map {pid} active_reference_source must remain original_user_upload unless explicitly promoted")
        if promoted and source != "explicit_user_promoted_derived":
            errors.append(f"identity_map {pid} explicit promotion must use active_reference_source=explicit_user_promoted_derived")
        if promoted and not active:
            errors.append(f"identity_map {pid} explicit promotion requires active_identity_references")

def validate_common(project: Path, stage: str, errors: list[str]) -> dict:
    deliverables = project / "deliverables"
    handoff_path = deliverables / "requirements-handoff.yaml"
    handoff = read_yaml(handoff_path) if handoff_path.exists() else {}
    if stage == "LOOK_PLAN_REVIEW" and not (deliverables / "couple-look-plan.md").exists():
        errors.append("LOOK_PLAN_REVIEW requires deliverables/couple-look-plan.md")
    if stage in PRE_CONFIRMATION and handoff_path.exists():
        errors.append("requirements-handoff.yaml must not exist before full Look confirmation")
    if stage in CONFIRMED_OR_LATER and not handoff_path.exists():
        errors.append("confirmed-or-later project requires deliverables/requirements-handoff.yaml")
    if handoff_path.exists() and stage in CONFIRMED_OR_LATER:
        looks = handoff.get("looks", [])
        confirmation = handoff.get("look_group_confirmation", {})
        if confirmation.get("status") != "confirmed":
            errors.append("confirmed-or-later project requires the selected direction to be authorized")
        elif confirmation.get("confirmation_source") not in {None, "direction_selected", "ai_auto_selected", "ai_auto_confirmed", "user_override", "user_confirmed"}:
            errors.append("look_group_confirmation.confirmation_source is invalid")
        if handoff.get("handoff_to_photography_skill", {}).get("ready") is not True:
            errors.append("confirmed-or-later project requires handoff_to_photography_skill.ready: true")
        if not looks or any(look.get("status") != "confirmed" for look in looks):
            errors.append("confirmed-or-later project requires every handoff look to be confirmed")

        if handoff.get("schema_version") in {2, 3}:
            project_data = handoff.get("project", {})
            validate_identity_reference_policy(project_data, errors)
            styling_required = bool(project_data.get("styling_policy", {}).get("professional_nodes_required"))
            participants = project_data.get("participants", [])
            participant_count = project_data.get("participant_count")
            if not isinstance(participants, list) or not participants:
                errors.append("participant-array handoff requires a non-empty project.participants roster")
            else:
                roster_ids = [str(person.get("id", "")).strip() for person in participants if isinstance(person, dict)]
                if len(roster_ids) != len(participants) or any(not value for value in roster_ids) or len(set(roster_ids)) != len(roster_ids):
                    errors.append("participant-array project.participants must contain unique non-empty ids")
                if participant_count != len(participants):
                    errors.append("participant-array project.participant_count must match the roster length")
                roster = set(roster_ids)
                for look in looks:
                    look_id = look.get("id", "unknown look")
                    participant_looks = look.get("participant_looks", [])
                    look_ids = [str(person.get("participant_id", "")).strip() for person in participant_looks if isinstance(person, dict)]
                    if set(look_ids) != roster or len(look_ids) != len(roster):
                        errors.append(f"{look_id} participant_looks must describe every roster participant exactly once")
                    for person in participant_looks:
                        if isinstance(person, dict) and not (person.get("outfit") or person.get("full_description")):
                            errors.append(f"{look_id} participant {person.get('participant_id')} is missing a complete outfit description")
                        if isinstance(person, dict):
                            outfit_data = person.get("outfit") if isinstance(person.get("outfit"), dict) else {}
                            hairstyle = person.get("hairstyle_design") or outfit_data.get("hairstyle_design")
                            makeup = person.get("makeup_design") or outfit_data.get("makeup_design")
                            if styling_required and not _text(hairstyle):
                                errors.append(f"{look_id} participant {person.get('participant_id')} is missing hairstyle_design")
                            if styling_required and not _text(makeup):
                                errors.append(f"{look_id} participant {person.get('participant_id')} is missing makeup_design")
                        if isinstance(person, dict):
                            description = person.get("full_description") or person.get("outfit")
                            if contains_compression_phrase(description):
                                errors.append(f"{look_id} participant {person.get('participant_id')} uses forbidden compression wording")
                    locked = look.get("visual_lock", {}).get("participant_outfits", [])
                    lock_ids = [str(person.get("participant_id", "")).strip() for person in locked if isinstance(person, dict)]
                    if set(lock_ids) != roster or len(lock_ids) != len(roster):
                        errors.append(f"{look_id} visual_lock.participant_outfits must lock every roster participant exactly once")
                    for person in locked:
                        if isinstance(person, dict) and not str(person.get("outfit", "")).strip():
                            errors.append(f"{look_id} visual lock for {person.get('participant_id')} is missing outfit text")
                        if styling_required and isinstance(person, dict) and not _text(person.get("hairstyle_design")):
                            errors.append(f"{look_id} visual lock for {person.get('participant_id')} is missing hairstyle_design")
                        if styling_required and isinstance(person, dict) and not _text(person.get("makeup_design")):
                            errors.append(f"{look_id} visual lock for {person.get('participant_id')} is missing makeup_design")

                    if handoff.get("schema_version") == 3:
                        scenes = look.get("scenes", [])
                        if not isinstance(scenes, list) or not scenes:
                            errors.append(f"{look_id} schema v3 requires at least one structured scene Location Card")
                        else:
                            for scene_index, scene in enumerate(scenes, start=1):
                                validate_location_scene(scene, f"{look_id} scene {scene_index}", errors)
                        location_lock = look.get("visual_lock", {}).get("location_lock", [])
                        if not isinstance(location_lock, list) or not location_lock:
                            errors.append(f"{look_id} schema v3 requires visual_lock.location_lock")
                        else:
                            for scene_index, scene in enumerate(location_lock, start=1):
                                validate_location_scene(scene, f"{look_id} location_lock {scene_index}", errors)

            if handoff.get("schema_version") == 3:
                policy = project_data.get("location_policy", {})
                required_flags = (
                    "specific_location_required", "progressive_specificity", "discovery_anchor_only",
                    "look_uses_shootable_zones_not_micro_points", "shot_micro_location_required",
                    "indoor_must_be_geographically_anchored",
                    "outdoor_must_name_specific_place", "named_work_must_name_in_world_location",
                    "no_invented_real_addresses", "generic_location_only_is_invalid",
                    "unspecified_modern_location_uses_random_world_famous_fallback",
                    "random_fallback_must_be_theme_compatible", "random_fallback_reroll_changes_place",
                )
                if not isinstance(policy, dict) or any(policy.get(flag) is not True for flag in required_flags):
                    errors.append("schema v3 project.location_policy is missing required progressive-location flags")
    return handoff


def validate_legacy(project: Path, stage: str, errors: list[str]) -> None:
    handoff = validate_common(project, stage, errors)
    deliverables = project / "deliverables"
    if handoff and stage in LEGACY_SHOOT_PLAN_OR_LATER:
        for look in handoff.get("looks", []):
            if not (deliverables / "generation-briefs" / f"{look.get('id')}-main.yaml").exists():
                errors.append(f"shoot-plan-or-later project requires generation brief for {look.get('id')}")
    main_visual_review = deliverables / "main-visual-review.yaml"
    if stage in {"MAIN_VISUAL_REVIEW", "SHOTLIST_REVIEW"}:
        if not list((project / "images").glob("LOOK-*-main.*")):
            errors.append("main-visual-review-or-later requires at least one images/LOOK-xx-main.* file")
        log_path = deliverables / "generation-log.yaml"
        if not log_path.exists() or read_yaml(log_path).get("quality_check", {}).get("status") != "passed":
            errors.append("main-visual-review-or-later requires a passed quality_check in generation-log.yaml")
        if not main_visual_review.exists():
            errors.append("main-visual-review-or-later requires deliverables/main-visual-review.yaml")
    if stage == "SHOTLIST_REVIEW":
        if not (deliverables / "shot-list.md").exists():
            errors.append("SHOTLIST_REVIEW requires deliverables/shot-list.md")
        if main_visual_review.exists() and read_yaml(main_visual_review).get("status") != "confirmed":
            errors.append("SHOTLIST_REVIEW requires confirmed main-visual review")


def validate_v2_shot_board(project: Path, state: dict, stage: str, errors: list[str]) -> None:
    deliverables = project / "deliverables"
    boards_dir = deliverables / "shot-boards"
    boards: dict[str, dict] = {}
    shot_ids: list[int] = []
    for path in sorted(boards_dir.glob("SHOTBOARD-*.yaml")) if boards_dir.exists() else []:
        board = read_yaml(path)
        shots = board.get("shots", [])
        ids = [shot.get("shot_id") for shot in shots]
        if not board.get("board_id") or not isinstance(shots, list) or len(shots) != BOARD_SIZE:
            errors.append(f"{path.name} must contain exactly eight shots")
            continue
        if not all(isinstance(value, int) for value in ids) or ids != list(range(min(ids), min(ids) + BOARD_SIZE)):
            errors.append(f"{path.name} shot ids must be eight consecutive integers")
        lock_roster = [
            str(person.get("participant_id", "")).strip()
            for person in board.get("visual_lock", {}).get("participant_outfits", [])
            if isinstance(person, dict) and str(person.get("participant_id", "")).strip()
        ]
        visual_lock = board.get("visual_lock", {})
        if visual_lock.get("strict_location"):
            for shot in shots:
                if _generic_location(shot.get("location_context")):
                    errors.append(f"{path.name} shot {shot.get('shot_id')} requires a concrete location_context")
                if _generic_location(shot.get("scene_area")):
                    errors.append(f"{path.name} shot {shot.get('shot_id')} requires a concrete scene_area micro-location")
                if visual_lock.get("requires_era_or_world_context") and not _text(shot.get("era_or_world_context")):
                    errors.append(f"{path.name} shot {shot.get('shot_id')} requires era_or_world_context")

        if len(lock_roster) > 2:
            roster = set(lock_roster)
            coverage: set[str] = set()
            full_group = False
            for shot in shots:
                present = shot.get("participants_present", [])
                directions = shot.get("participant_directions", [])
                if not isinstance(present, list) or not present:
                    errors.append(f"{path.name} multi-person shot {shot.get('shot_id')} requires participants_present")
                    continue
                present_ids = [str(value).strip() for value in present if str(value).strip()]
                if any(pid not in roster for pid in present_ids):
                    errors.append(f"{path.name} shot {shot.get('shot_id')} references a participant outside the locked roster")
                direction_ids = [
                    str(item.get("participant_id", "")).strip()
                    for item in directions if isinstance(item, dict)
                ] if isinstance(directions, list) else []
                if set(direction_ids) != set(present_ids) or len(direction_ids) != len(present_ids):
                    errors.append(f"{path.name} shot {shot.get('shot_id')} must direction every visible participant exactly once")
                coverage.update(present_ids)
                if set(present_ids) == roster:
                    full_group = True
            if coverage != roster:
                errors.append(f"{path.name} eight-shot coverage must include every locked participant")
            if not full_group:
                errors.append(f"{path.name} multi-person board requires at least one full-group shot")
        boards[board["board_id"]] = board
        shot_ids.extend(ids)
    if len(set(shot_ids)) != len(shot_ids):
        errors.append("shot ids must be unique within a project")
    shot_state = state.get("shot_board", {})
    expected_next = max(shot_ids, default=0) + 1
    if shot_state.get("next_shot_id") != expected_next:
        errors.append(f"shot_board.next_shot_id must equal {expected_next}")
    active = shot_state.get("active_board")
    if stage in {"SHOTLIST_REVIEW", "SHOT_GRID_REVIEW"}:
        if active not in boards:
            errors.append("shot review requires an existing active board")
        else:
            board = boards[active]
            if stage == "SHOTLIST_REVIEW" and board.get("status") != "text_review":
                errors.append("SHOTLIST_REVIEW requires an active text_review shot board")
            if stage == "SHOT_GRID_REVIEW":
                grid = board.get("grid_image")
                cells = board.get("cell_images", {})
                expected = {str(shot["shot_id"]) for shot in board["shots"]}
                if board.get("status") != "grid_review" or not grid or not (project / grid).exists():
                    errors.append("SHOT_GRID_REVIEW requires an active board with an existing grid image")
                grid_mode = board.get("grid_mode", "composed_cells")
                if grid_mode == "single_grid":
                    source = board.get("grid_source_image")
                    if not source or not (project / source).exists():
                        errors.append("single_grid SHOT_GRID_REVIEW requires one existing source grid image")
                    if cells:
                        errors.append("single_grid SHOT_GRID_REVIEW must not contain cell_images")
                elif grid_mode == "composed_cells":
                    if set(cells) != expected or any(not (project / image).exists() for image in cells.values()):
                        errors.append("composed_cells SHOT_GRID_REVIEW requires eight existing cell images for the active board")
                else:
                    errors.append(f"SHOT_GRID_REVIEW has unsupported grid_mode: {grid_mode!r}")
    valid_ids = set(shot_ids)
    selected = shot_state.get("selected_shot_ids", [])
    if selected and (len(set(selected)) != len(selected) or not all(value in valid_ids for value in selected)):
        errors.append("shot_board.selected_shot_ids must be unique existing shot ids")
    briefs_dir = deliverables / "shot-detail-briefs"
    for path in briefs_dir.glob("SHOT-*-detail-*.yaml") if briefs_dir.exists() else []:
        brief = read_yaml(path)
        if brief.get("shot_id") not in valid_ids or brief.get("orientation") not in {"portrait", "landscape"}:
            errors.append(f"{path.name} has an invalid shot id or orientation")
        if brief.get("status") == "passed":
            output = brief.get("output_path")
            if not output or not (project / output).exists():
                errors.append(f"{path.name} is passed but its detail image is missing")


def validate_v2(project: Path, state: dict, stage: str, errors: list[str]) -> None:
    validate_common(project, stage, errors)
    validate_v2_shot_board(project, state, stage, errors)


def validate_single_workspace(project: Path, state: dict, errors: list[str]) -> None:
    stage = state.get("stage")
    is_v2 = state.get("workflow_version") == 2
    if stage not in (V2_STAGES if is_v2 else LEGACY_STAGES):
        errors.append(f"invalid {'v2 ' if is_v2 else ''}stage: {stage!r}")
    if is_v2:
        validate_quality_policy(state, errors)
    validate_wardrobe(project, state, stage, errors)
    if is_v2:
        validate_v2(project, state, stage, errors)
    else:
        validate_legacy(project, stage, errors)


def validate_v3(root: Path, manifest: dict, errors: list[str]) -> None:
    themes = manifest.get("themes", {})
    items = themes.get("items", [])
    ids = [item.get("id") for item in items]
    if not isinstance(items, list) or len(set(ids)) != len(ids) or any(not isinstance(value, str) or not value.startswith("THEME-") for value in ids):
        errors.append("v3 project requires unique THEME-xxx registry items")
        return
    active = themes.get("active_theme_id")
    if items and active not in ids:
        errors.append("v3 project active_theme_id must reference a registered theme")
    if not items and active is not None:
        errors.append("v3 project without themes must not set active_theme_id")
    if themes.get("next_theme_number") != len(items) + 1:
        errors.append("v3 project next_theme_number must follow registered themes")
    for item in items:
        workspace = root / str(item.get("path", ""))
        if not workspace.is_relative_to(root) or not (workspace / "project.yaml").exists():
            errors.append(f"registered theme is missing its workspace: {item.get('id')}")
            continue
        for relative in ("references", "deliverables", "images"):
            if not (workspace / relative).exists():
                errors.append(f"theme {item.get('id')} missing {relative}")
        theme_state = read_yaml(workspace / "project.yaml")
        if theme_state.get("workflow_version") != 2:
            errors.append(f"theme {item.get('id')} must use workflow_version: 2")
            continue
        scoped_errors: list[str] = []
        validate_single_workspace(workspace, theme_state, scoped_errors)
        errors.extend(f"{item.get('id')}: {error}" for error in scoped_errors)
        if item.get("stage") != theme_state.get("stage"):
            errors.append(f"theme {item.get('id')} registry stage is out of sync")


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate a people-photo project")
    parser.add_argument("project_dir", type=Path)
    args = parser.parse_args()
    project = args.project_dir.resolve()
    errors: list[str] = []
    for relative in ("project.yaml", "references"):
        if not (project / relative).exists():
            errors.append(f"missing {relative}")
    state_path = project / "project.yaml"
    state = read_yaml(state_path) if state_path.exists() else {}
    if state.get("workflow_version") == 3:
        if not (project / "themes").is_dir():
            errors.append("v3 project requires themes directory")
        validate_v3(project, state, errors)
    else:
        for relative in ("deliverables", "images"):
            if not (project / relative).exists():
                errors.append(f"missing {relative}")
        validate_single_workspace(project, state, errors)
    if errors:
        print("INVALID")
        print("\n".join(f"- {error}" for error in errors))
        raise SystemExit(1)
    label = "multi-theme" if state.get("workflow_version") == 3 else state.get("stage")
    print(f"VALID: {project} ({label})")


if __name__ == "__main__":
    main()
