#!/usr/bin/env python3
"""Persist, compile, register, and select numbered six-look wardrobe boards for any number of participants."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml
from PIL import Image, ImageDraw, ImageFont

THEME_SCRIPT_DIR = Path(__file__).resolve().parents[2] / "zongkong" / "scripts"
sys.path.insert(0, str(THEME_SCRIPT_DIR))
from theme_workspace import resolve_theme, sync_theme


BOARD_SIZE = 6
GRID_MODE_SINGLE = "single_grid"
BOARD_FILE = re.compile(r"BOARD-\d{3}\.yaml")
PANEL_RATIO_VALUES = {
    "1:1": 1.0, "4:5": 4 / 5, "3:4": 3 / 4, "2:3": 2 / 3,
    "4:3": 4 / 3, "3:2": 3 / 2, "9:16": 9 / 16, "16:9": 16 / 9,
}
DEFAULT_PANEL_RATIO = None

GENERIC_LOCATIONS = {
    "室内", "户外", "酒店", "公寓", "民宿", "卧室", "客厅", "书房", "街头", "街区", "城市",
    "海边", "湖边", "河边", "庭院", "古镇", "公园", "长廊", "宫殿", "山门", "影棚", "摄影棚",
}
VALID_LOCATION_MODES = {"real_world", "historical_real_world", "future_landmark", "source_work", "original_fictional"}


def normalize_panel_ratio(value: object) -> str:
    text = str(value or "").strip().replace("/", ":")
    if not text:
        return DEFAULT_PANEL_RATIO
    match = re.fullmatch(r"\s*(\d+(?:\.\d+)?)\s*:\s*(\d+(?:\.\d+)?)\s*", text)
    if not match:
        raise SystemExit(f"invalid panel aspect ratio: {value!r}; use W:H such as 4:5")
    width, height = float(match.group(1)), float(match.group(2))
    if width <= 0 or height <= 0:
        raise SystemExit("panel aspect ratio values must be positive")
    target = width / height
    for canonical, numeric in PANEL_RATIO_VALUES.items():
        if abs(target - numeric) < 1e-9:
            return canonical
    return min(PANEL_RATIO_VALUES, key=lambda key: abs(__import__('math').log(target / PANEL_RATIO_VALUES[key])))


def grid_layout_policy(count: int = BOARD_SIZE) -> dict:
    if count != BOARD_SIZE:
        raise SystemExit(f"unsupported grid size: {count}")
    return {
        "mode": "free_ai",
        "panel_count": count,
        "slot_order": "natural visual reading order, upper-left across/down",
    }


def _normalize_location(raw: object, option_index: int) -> dict:
    """Normalize a pre-shot spacetime anchor; exact micro-location remains optional."""
    if not isinstance(raw, dict):
        raise SystemExit(f"option {option_index} must include a structured location object under the location-anchor policy")
    location = {str(k): v for k, v in raw.items()}
    mode = _text(location.get("location_mode"))
    if mode not in VALID_LOCATION_MODES:
        raise SystemExit(f"option {option_index} location_mode is invalid")
    if mode in {"real_world", "historical_real_world", "future_landmark"}:
        city = _text(location.get("city"))
        named = _text(location.get("named_place"))
        district = _text(location.get("district_or_area"))
        street = _text(location.get("street_or_route"))
        area = district or street
        if not city or ((not named or named in GENERIC_LOCATIONS) and (not area or area in GENERIC_LOCATIONS)):
            raise SystemExit(f"option {option_index} real-world location requires city plus a concrete area/scenic zone/street or named place")
        if _text(location.get("indoor_outdoor")) == "indoor" and (not named or named in GENERIC_LOCATIONS) and (not street or street in GENERIC_LOCATIONS):
            raise SystemExit(f"option {option_index} indoor real-world location requires a named venue/building or real street/route anchor")
        if not _text(location.get("verification_status")):
            raise SystemExit(f"option {option_index} real-world location requires verification_status")
        if mode == "historical_real_world" and not _text(location.get("era_or_period")):
            raise SystemExit(f"option {option_index} historical location requires era_or_period")
    elif mode == "source_work":
        work = _text(location.get("source_work"))
        in_world = _text(location.get("in_world_location"))
        if not work or not in_world or in_world in GENERIC_LOCATIONS:
            raise SystemExit(f"option {option_index} source-work location requires source_work and a concrete in_world_location")
        if not (_text(location.get("era_or_period")) or _text(location.get("world_state_or_chapter"))):
            raise SystemExit(f"option {option_index} source-work location requires era/world-state")
    elif mode == "original_fictional":
        named = _text(location.get("named_place"))
        if not named or named in GENERIC_LOCATIONS or not (_text(location.get("city")) or _text(location.get("district_or_area"))):
            raise SystemExit(f"option {option_index} original-fictional location requires named place and world/city/region")
        if not (_text(location.get("era_or_period")) or _text(location.get("world_state_or_chapter"))):
            raise SystemExit(f"option {option_index} original-fictional location requires era/world-state")
    return location


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def write_yaml(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, allow_unicode=True, sort_keys=False), encoding="utf-8")


def project_paths(project: Path) -> tuple[Path, Path, Path]:
    return project / "project.yaml", project / "deliverables" / "wardrobe-boards", project / "images" / "wardrobe-boards"


def load_project(project: Path) -> tuple[Path, dict, Path, Path]:
    state_path, boards_dir, images_dir = project_paths(project)
    if not state_path.exists():
        raise SystemExit(f"missing project.yaml: {state_path}")
    state = read_yaml(state_path)
    boards_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)
    state.setdefault("wardrobe_board", {"next_option_id": 1, "active_board": None, "selected_option_ids": [], "theme": None})
    state["wardrobe_board"].setdefault("next_option_id", 1)
    state["wardrobe_board"].setdefault("active_board", None)
    state["wardrobe_board"].setdefault("selected_option_ids", [])
    state["wardrobe_board"].setdefault("theme", None)
    return state_path, state, boards_dir, images_dir


def board_path(boards_dir: Path, board_id: str) -> Path:
    path = boards_dir / f"{board_id}.yaml"
    if not path.exists():
        raise SystemExit(f"unknown board: {board_id}")
    return path


def board_paths(boards_dir: Path) -> list[Path]:
    return sorted(path for path in boards_dir.glob("BOARD-*.yaml") if BOARD_FILE.fullmatch(path.name))


def archive_stale_artifacts(project: Path) -> None:
    deliverables = project / "deliverables"
    targets = [
        deliverables / "requirements-handoff.yaml",
        deliverables / "shooting-plan.md",
        deliverables / "generation-log.yaml",
        deliverables / "main-visual-review.yaml",
        deliverables / "generation-briefs",
    ]
    existing = [target for target in targets if target.exists()]
    if not existing:
        return
    archive_root = deliverables / "archive"
    archive = archive_root / f"wardrobe-revision-{datetime.now().strftime('%Y%m%dT%H%M%SZ')}"
    suffix = 2
    while archive.exists():
        archive = archive_root / f"wardrobe-revision-{datetime.now().strftime('%Y%m%dT%H%M%SZ')}-{suffix}"
        suffix += 1
    archive.mkdir(parents=True, exist_ok=False)
    for target in existing:
        shutil.move(str(target), str(archive / target.name))
    (deliverables / "generation-briefs").mkdir(parents=True, exist_ok=True)


def render_markdown(board: dict) -> str:
    lines = [f"# 换装 6 宫格方案｜{board['board_id']}", "", f"主题：{board['theme']}", "", "状态：文字候选审阅", ""]
    for option in board["options"]:
        lines.extend([f"## {option['option_id']}｜{option['name']}", ""])
        for person in option["participants"]:
            lines.extend([
                f"### {person['participant_id']}｜{person['label']}",
                f"- 服装：{person['outfit']}",
                "",
            ])
        lines.extend([
            f"- 群体搭配关系：{option['group_relationship']}",
            f"- 场景：{option['scene']}",
            f"- 具体地点：{_text(option.get('location')) or 'legacy scene text'}",
            f"- 道具：{option['props']}",
            "",
        ])
    lines.append("确认这 6 套后可生成带编号的 6 宫格图；如不满意，直接说“再来一版”。")
    return "\n".join(lines) + "\n"


def _text(value: object) -> str:
    if isinstance(value, list):
        return "、".join(str(item).strip() for item in value if str(item).strip())
    if isinstance(value, dict):
        return "；".join(f"{key}：{_text(item)}" for key, item in value.items() if _text(item))
    return str(value or "").strip()


def _normalize_participants(item: dict, option_index: int) -> list[dict]:
    raw = item.get("participants")
    if raw is None and item.get("female") and item.get("male"):
        raw = [
            {"participant_id": "P01", "label": "女生", "outfit": item.get("female")},
            {"participant_id": "P02", "label": "男生", "outfit": item.get("male")},
        ]
    if not isinstance(raw, list) or not raw:
        raise SystemExit(f"option {option_index} must include a non-empty participants array")
    result: list[dict] = []
    seen: set[str] = set()
    for person_index, person in enumerate(raw, start=1):
        if not isinstance(person, dict):
            raise SystemExit(f"option {option_index} participant {person_index} must be an object")
        pid = _text(person.get("participant_id") or person.get("id") or f"P{person_index:02d}")
        label = _text(person.get("label") or person.get("name") or person.get("role") or pid)
        outfit = _text(person.get("outfit") or person.get("wardrobe") or person.get("full_description"))
        if not pid or not label or not outfit:
            raise SystemExit(f"option {option_index} participant {person_index} requires participant_id, label, and outfit")
        if pid in seen:
            raise SystemExit(f"option {option_index} contains duplicate participant_id: {pid}")
        seen.add(pid)
        result.append({"participant_id": pid, "label": label, "outfit": outfit})
    return result


def validate_options(value: object) -> list[dict]:
    if not isinstance(value, list) or len(value) != BOARD_SIZE:
        raise SystemExit("options file must contain exactly six option objects")
    options: list[dict] = []
    expected_signature: list[tuple[str, str]] | None = None
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict):
            raise SystemExit(f"option {index} must be an object")
        name = _text(item.get("name"))
        relationship = _text(item.get("group_relationship") or item.get("couple"))
        scene = _text(item.get("scene"))
        props = _text(item.get("props"))
        if not all((name, relationship, scene, props)):
            raise SystemExit(f"option {index} must include name, group_relationship, scene, and props")
        participants = _normalize_participants(item, index)
        signature = [(person["participant_id"], person["label"]) for person in participants]
        if expected_signature is None:
            expected_signature = signature
        elif signature != expected_signature:
            raise SystemExit("all six wardrobe options must contain the same participant ids and labels in the same order")
        normalized = {
            "name": name,
            "participants": participants,
            "group_relationship": relationship,
            "scene": scene,
            "location": _normalize_location(item.get("location"), index) if item.get("location") is not None else None,
            "props": props,
        }
        # Keep legacy aliases only when the source really used the old pair schema.
        if item.get("female") and item.get("male"):
            normalized.update({"female": _text(item.get("female")), "male": _text(item.get("male")), "couple": relationship})
        options.append(normalized)
    return options


def create(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    state_path, state, boards_dir, _ = load_project(project)
    theme = args.theme.strip()
    if not theme:
        raise SystemExit("theme is required")
    options = validate_options(json.loads(Path(args.options_file).read_text(encoding="utf-8")))
    if state.get("quality_policy", {}).get("location_specificity_required"):
        missing = [str(index) for index, option in enumerate(options, start=1) if not option.get("location")]
        if missing:
            raise SystemExit(f"strict location policy requires a structured location object in every wardrobe option; missing options: {', '.join(missing)}")
    archive_stale_artifacts(project)
    board_number = len(board_paths(boards_dir)) + 1
    board_id = f"BOARD-{board_number:03d}"
    start = int(state["wardrobe_board"]["next_option_id"])
    numbered = [{"option_id": start + index, **option} for index, option in enumerate(options)]
    board = {
        "board_id": board_id,
        "created_at": now(),
        "theme": theme,
        "status": "text_review",
        "grid_mode": GRID_MODE_SINGLE,
        "number_range": [start, start + BOARD_SIZE - 1],
        "options": numbered,
        "grid_brief": None,
        "grid_source_image": None,
        "grid_image": None,
        "selected_option_ids": [],
    }
    write_yaml(boards_dir / f"{board_id}.yaml", board)
    (boards_dir / f"{board_id}.md").write_text(render_markdown(board), encoding="utf-8")
    state["stage"] = "WARDROBE_TEXT_REVIEW"
    state["looks"] = []
    state.setdefault("artifacts", {})
    state["artifacts"].update({
        "couple_look_plan": f"deliverables/wardrobe-boards/{board_id}.md",
        "requirements_handoff": None,
        "shooting_plan": None,
        "generation_log": None,
    })
    state.setdefault("generation", {})["approved_looks"] = []
    state["wardrobe_board"].update({
        "next_option_id": start + BOARD_SIZE,
        "active_board": board_id,
        "selected_option_ids": [],
        "theme": theme,
    })
    write_yaml(state_path, state)
    print(boards_dir / f"{board_id}.yaml")


def font(size: int) -> ImageFont.ImageFont:
    candidates = ["arialbd.ttf", "arial.ttf"]
    windir = os.environ.get("WINDIR")
    if windir:
        candidates.append(str(Path(windir) / "Fonts" / "arialbd.ttf"))
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size=size)
        except OSError:
            pass
    return ImageFont.load_default()


def grid_prompt(board: dict) -> str:
    lines = [
        "Generate ONE SINGLE IMAGE: an editorial contact sheet with exactly six distinct full-body wardrobe panels.",
        "Do not specify or force panel aspect ratios, panel dimensions, overall board aspect ratio, row count, or column count.",
        "Arrange all six panels freely as one balanced contact sheet. Each panel must be clear, standalone, and easy to read; avoid ultra-narrow strips or unreadable collage fragments.",
        "Each panel must contain the complete confirmed participant roster for this wardrobe option; do not drop, merge, duplicate, or invent people.",
        "Keep the six wardrobe options in natural visual reading order from upper-left across/down, whatever layout you choose. Every participant must faithfully wear their own assigned outfit, with the stated group styling relationship, setting, and props.",
        "If real-person references are used: preserve identity but do not freeze the source expression. Wardrobe preview hair and makeup are exploratory only; formal hair is designed later by the Editorial hairstylist stage, and formal makeup/skin optimization is designed later by the mandatory Editorial makeup artist stage. Do not treat Wardrobe Board grooming as the final shoot makeup lock.",
        "Do not render any text, digits, labels, captions, logos, watermarks, poster layout, or extra panels.",
        "Each panel is a complete ensemble outfit proposal. Do not merge garments, accessories, scenes, props, or identities between panels.",
        "\nPanel specifications:",
    ]
    for position, option in enumerate(board["options"], start=1):
        people = "\n".join(
            f"- {person['participant_id']} {person['label']}: {person['outfit']}"
            for person in option["participants"]
        )
        lines.append(
            f"\nPanel {position} (slot {option['option_id']}):\n"
            f"Participants and outfits:\n{people}\n"
            f"Group styling relationship: {option['group_relationship']}\nSetting: {option['scene']}\nExact location lock: {_text(option.get('location'))}\nProps: {option['props']}"
        )
    return "\n".join(lines)

def next_grid_brief_version(boards_dir: Path, board_id: str) -> int:
    version = 1
    while (boards_dir / f"{board_id}-grid-v{version}.yaml").exists():
        version += 1
    return version


def prepare_grid(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    state_path, state, boards_dir, images_dir = load_project(project)
    board_file = board_path(boards_dir, args.board_id)
    board = read_yaml(board_file)
    if board.get("status") != "text_review" or board.get("grid_mode") != GRID_MODE_SINGLE:
        raise SystemExit("only a new single_grid text_review wardrobe board can prepare a grid")
    version = next_grid_brief_version(boards_dir, board["board_id"])
    brief_path = boards_dir / f"{board['board_id']}-grid-v{version}.yaml"
    source_path = images_dir / f"{board['board_id']}-source.png"
    output_path = images_dir / f"{board['board_id']}.png"
    layout_policy = grid_layout_policy()
    prompt = grid_prompt(board)
    write_yaml(brief_path, {
        "brief_id": brief_path.stem,
        "status": "pending",
        "board_id": board["board_id"],
        "grid_mode": GRID_MODE_SINGLE,
        "layout_policy": layout_policy,
        "panel_aspect_ratio": None,
        "requested_panel_aspect_ratio": None,
        "slot_mapping": [{"slot": index, "option_id": option["option_id"], "name": option["name"]} for index, option in enumerate(board["options"], start=1)],
        "render_prompt": prompt,
        "source_image": None,
        "output_path": str(output_path.relative_to(project)).replace("\\", "/"),
        "numbering": "No fixed-grid badge overlay. Panel identity follows the stored option order / natural visual reading order.",
        "created_at": now(),
    })
    board.update({"grid_brief": str(brief_path.relative_to(project)).replace("\\", "/"), "grid_source_image": str(source_path.relative_to(project)).replace("\\", "/"), "grid_image": None, "panel_aspect_ratio": None, "grid_layout": None})
    write_yaml(board_file, board)
    state["wardrobe_board"]["active_board"] = board["board_id"]
    write_yaml(state_path, state)
    print(f"GRID_BRIEF: {brief_path.relative_to(project)}\n\n{prompt}")


def draw_grid_badges(image: Image.Image, option_ids: list[int], columns: int, rows: int) -> Image.Image:
    canvas = image.convert("RGB")
    draw = ImageDraw.Draw(canvas)
    cell_width = canvas.width / columns
    cell_height = canvas.height / rows
    badge_size = max(40, int(min(cell_width, cell_height) * 0.16))
    margin = max(12, int(min(cell_width, cell_height) * 0.035))
    badge_font = font(max(20, int(badge_size * 0.52)))
    for index, option_id in enumerate(option_ids):
        x = int((index % columns) * cell_width + margin)
        y = int((index // columns) * cell_height + margin)
        badge = (x, y, x + badge_size, y + badge_size)
        draw.rounded_rectangle(badge, radius=max(12, badge_size // 4), fill="#151515", outline="#FFFFFF", width=max(2, badge_size // 24))
        label = str(option_id)
        box = draw.textbbox((0, 0), label, font=badge_font)
        draw.text((x + (badge_size - (box[2] - box[0])) / 2, y + (badge_size - (box[3] - box[1])) / 2 - 2), label, font=badge_font, fill="#FFFFFF")
    return canvas

def register_grid(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    state_path, state, boards_dir, images_dir = load_project(project)
    board_file = board_path(boards_dir, args.board_id)
    board = read_yaml(board_file)
    if board.get("status") != "text_review" or board.get("grid_mode") != GRID_MODE_SINGLE or not board.get("grid_brief"):
        raise SystemExit("prepare-grid must compile the single-grid prompt before registering an image")
    source = Path(args.image).resolve()
    if not source.exists():
        raise SystemExit(f"missing grid image: {source}")
    brief_path = project / board["grid_brief"]
    if not brief_path.exists():
        raise SystemExit(f"missing grid brief: {brief_path}")
    source_path = images_dir / f"{board['board_id']}-source.png"
    output = images_dir / f"{board['board_id']}.png"
    brief = read_yaml(brief_path)
    with Image.open(source) as image:
        image.convert("RGB").save(source_path, format="PNG")
        image.convert("RGB").save(output, format="PNG")
    brief.update({"status": "registered", "source_image": str(source_path.relative_to(project)).replace("\\", "/"), "output_path": str(output.relative_to(project)).replace("\\", "/"), "registered_at": now()})
    write_yaml(brief_path, brief)
    board["status"] = "grid_review"
    board["grid_source_image"] = str(source_path.relative_to(project)).replace("\\", "/")
    board["grid_image"] = str(output.relative_to(project)).replace("\\", "/")
    write_yaml(board_file, board)
    state["stage"] = "WARDROBE_GRID_REVIEW"
    state["wardrobe_board"]["active_board"] = board["board_id"]
    write_yaml(state_path, state)
    print(output)


def select(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    state_path, state, boards_dir, _ = load_project(project)
    requested = [int(value.strip()) for value in args.ids.split(",") if value.strip()]
    if not requested or len(set(requested)) != len(requested):
        raise SystemExit("--ids must be a non-empty comma-separated list of unique option ids")
    available: dict[int, tuple[Path, dict, dict]] = {}
    for path in board_paths(boards_dir):
        board = read_yaml(path)
        if board.get("theme") != state["wardrobe_board"].get("theme") or board.get("grid_mode") != GRID_MODE_SINGLE or board.get("status") != "grid_review":
            continue
        for option in board.get("options", []):
            available[int(option["option_id"])] = (path, board, option)
    unknown = [str(value) for value in requested if value not in available]
    if unknown:
        raise SystemExit(f"selected ids are unavailable for the current theme: {', '.join(unknown)}")
    selected = [available[value][2] for value in requested]
    selected_by_board: dict[Path, list[int]] = {}
    for value in requested:
        selected_by_board.setdefault(available[value][0], []).append(value)
    for path, option_ids in selected_by_board.items():
        board = read_yaml(path)
        board["selected_option_ids"] = sorted(set(board.get("selected_option_ids", []) + option_ids))
        write_yaml(path, board)

    looks = []
    for index, option in enumerate(selected, start=1):
        looks.append({"id": f"LOOK-{index:02d}", "name": option["name"], "status": "confirmed", "wardrobe_option_id": option["option_id"]})

    plan_lines = ["# 已选 Group Look", ""]
    for look, option in zip(looks, selected):
        plan_lines.extend([f"## {look['id']}｜{option['name']}（换装编号 {option['option_id']}）", ""])
        for person in option["participants"]:
            plan_lines.extend([
                f"### {person['participant_id']}｜{person['label']}",
                f"- 服装：{person['outfit']}",
                "",
            ])
        plan_lines.extend([
            f"- 群体搭配关系：{option['group_relationship']}",
            f"- 场景：{option['scene']}",
            f"- 具体地点：{_text(option.get('location')) or 'legacy scene text'}",
            f"- 道具：{option['props']}",
            "",
        ])
    plan_lines.append("以上由用户选定，可进入拍摄方案。")
    deliverables = project / "deliverables"
    look_plan = deliverables / "couple-look-plan.md"  # legacy filename retained for compatibility
    look_plan.write_text("\n".join(plan_lines) + "\n", encoding="utf-8")

    roster = [{"id": person["participant_id"], "label": person["label"]} for person in selected[0]["participants"]]
    handoff_looks = []
    for look, option in zip(looks, selected):
        participant_outfits = [
            {"participant_id": person["participant_id"], "label": person["label"], "outfit": person["outfit"]}
            for person in option["participants"]
        ]
        look_record = {
            "id": look["id"],
            "status": "confirmed",
            "concept": option["name"],
            "wardrobe_board_option_id": option["option_id"],
            "participant_looks": participant_outfits,
            "group_relationship": option["group_relationship"],
            "scenes": [{**(option.get("location") or {}), "name": option["scene"], "props": [option["props"]]}],
            "visual_lock": {
                "participant_outfits": participant_outfits,
                "group_relationship": option["group_relationship"],
                "work_era_setting": state["wardrobe_board"]["theme"],
                "scene_mood": option["scene"],
                "location_lock": [{**(option.get("location") or {}), "name": option["scene"], "props": [option["props"]]}] if option.get("location") else [],
                "quality_floor": "full_detail_no_compression",
                "hard_avoids": [],
            },
        }
        if option.get("female") and option.get("male"):
            look_record.update({"female_outfit": option["female"], "male_outfit": option["male"], "couple_relationship": option["group_relationship"]})
            look_record["visual_lock"].update({"female_outfit": option["female"], "male_outfit": option["male"], "couple_relationship": option["group_relationship"]})
        handoff_looks.append(look_record)
    handoff = {
        "schema_version": 3 if all(option.get("location") for option in selected) else 2,
        "project": {
            "shoot_type": state.get("shoot_type"),
            "theme": state["wardrobe_board"]["theme"],
            "look_count": len(looks),
            "participant_count": len(roster),
            "participants": roster,
            "location_policy": {
                "specific_location_required": True,
                "progressive_specificity": True,
                "discovery_anchor_only": True,
                "look_uses_shootable_zones_not_micro_points": True,
                "shot_micro_location_required": True,
                "indoor_must_be_geographically_anchored": True,
                "outdoor_must_name_specific_place": True,
                "named_work_must_name_in_world_location": True,
                "period_context_required_when_material": True,
                "no_invented_real_addresses": True,
                "generic_location_only_is_invalid": True,
                "unspecified_modern_location_uses_random_world_famous_fallback": True,
                "random_fallback_must_be_theme_compatible": True,
                "random_fallback_reroll_changes_place": True,
            } if all(option.get("location") for option in selected) else {},
        },
        "looks": handoff_looks,
        "look_group_confirmation": {"status": "confirmed", "confirmation_source": "user_override", "rule": "User selection of wardrobe-board option ids authorizes the replacement Look; do not ask for another Look confirmation."},
        "handoff_to_photography_skill": {"ready": True, "next_task": "Create photography plan and shot boards for selected looks without reducing per-participant detail."},
    }
    write_yaml(deliverables / "requirements-handoff.yaml", handoff)
    state["stage"] = "LOOKS_CONFIRMED"
    state["looks"] = looks
    state["artifacts"].update({"couple_look_plan": "deliverables/couple-look-plan.md", "requirements_handoff": "deliverables/requirements-handoff.yaml"})
    state["wardrobe_board"]["selected_option_ids"] = requested
    write_yaml(state_path, state)
    print(deliverables / "requirements-handoff.yaml")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    create_parser = subparsers.add_parser("create", help="allocate six new option ids and save a text board")
    create_parser.add_argument("project")
    create_parser.add_argument("--theme", required=True)
    create_parser.add_argument("--options-file", required=True)
    create_parser.add_argument("--theme-id")
    create_parser.set_defaults(func=create)
    prepare_parser = subparsers.add_parser("prepare-grid", help="compile six wardrobe options into one free-layout single-grid image prompt")
    prepare_parser.add_argument("project")
    prepare_parser.add_argument("board_id")
    prepare_parser.add_argument("--panel-aspect-ratio", help="deprecated and ignored; wardrobe-grid generation no longer specifies panel dimensions")
    prepare_parser.add_argument("--theme-id")
    prepare_parser.set_defaults(func=prepare_grid)
    register_parser = subparsers.add_parser("register-grid", help="register one AI-generated free-layout six-panel grid image and overlay numeric badges")
    register_parser.add_argument("project")
    register_parser.add_argument("board_id")
    register_parser.add_argument("--image", required=True, help="the one AI-generated free-layout six-panel grid image")
    register_parser.add_argument("--theme-id")
    register_parser.set_defaults(func=register_grid)
    select_parser = subparsers.add_parser("select", help="promote selected option ids into confirmed looks")
    select_parser.add_argument("project")
    select_parser.add_argument("--ids", required=True)
    select_parser.add_argument("--theme-id")
    select_parser.set_defaults(func=select)
    args = parser.parse_args()
    root = Path(args.project).resolve()
    workspace, theme_id = resolve_theme(root, args.theme_id)
    args.project = str(workspace)
    args.func(args)
    sync_theme(root, theme_id)


if __name__ == "__main__":
    main()
