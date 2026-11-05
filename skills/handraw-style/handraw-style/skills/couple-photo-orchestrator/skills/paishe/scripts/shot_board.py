#!/usr/bin/env python3
"""Persist, render, select, and complete numbered eight-shot boards for one or many participants."""

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
from PIL import Image, ImageDraw, ImageFont, ImageOps

THEME_SCRIPT_DIR = Path(__file__).resolve().parents[2] / "zongkong" / "scripts"
sys.path.insert(0, str(THEME_SCRIPT_DIR))
from theme_workspace import resolve_theme, sync_theme


PHOTOGRAPHY_KEYWORDS = "高级摄影师风格，创意构图，强烈的戏剧张力"
BOARD_SIZE = 8
GRID_MODE_SINGLE = "single_grid"
GRID_MODE_LEGACY = "composed_cells"
ORIENTATIONS = {"portrait": {"ratio": "4:5"}, "landscape": {"ratio": "3:2"}}
PANEL_RATIO_VALUES = {
    "1:1": 1.0, "4:5": 4 / 5, "3:4": 3 / 4, "2:3": 2 / 3,
    "4:3": 4 / 3, "3:2": 3 / 2, "9:16": 9 / 16, "16:9": 16 / 9,
}
DEFAULT_PANEL_RATIO = None
REQUIRED_SHOT_FIELDS = (
    "title", "purpose", "action_event", "pose_structure", "key_support_weight",
    "relationship_contact", "emotion_motivation", "gaze", "framing_adaptation",
    "scene_area", "interaction", "shot_size", "composition", "lighting",
    "continuity", "avoids", "prompt",
)

GENERIC_LOCATIONS = {
    "室内", "户外", "酒店", "公寓", "民宿", "卧室", "客厅", "书房", "街头", "街区", "城市",
    "海边", "湖边", "河边", "庭院", "古镇", "公园", "长廊", "宫殿", "山门", "影棚", "摄影棚",
    "indoor", "outdoor", "hotel", "apartment", "street", "city", "beach", "garden", "studio",
}


def normalize_panel_ratio(value: object) -> str:
    """Normalize any numeric ratio to the nearest allowed common photography ratio."""
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


def generic_location(value: object) -> bool:
    text = str(value or "").strip().lower().strip(" .，,。;；:-—_/\\")
    return not text or text in GENERIC_LOCATIONS


def now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def read_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def write_yaml(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(value, allow_unicode=True, sort_keys=False), encoding="utf-8")


def rel(project: Path, path: Path) -> str:
    return str(path.relative_to(project)).replace("\\", "/")


def paths(project: Path) -> tuple[Path, Path, Path, Path, Path]:
    return (
        project / "project.yaml",
        project / "deliverables" / "shot-boards",
        project / "deliverables" / "shot-detail-briefs",
        project / "images" / "shot-boards",
        project / "images" / "shot-details",
    )


def load_project(project: Path) -> tuple[Path, dict, Path, Path, Path, Path]:
    state_path, boards_dir, briefs_dir, grids_dir, details_dir = paths(project)
    if not state_path.exists():
        raise SystemExit(f"missing project.yaml: {state_path}")
    state = read_yaml(state_path)
    if state.get("workflow_version") != 2:
        raise SystemExit("shot boards require workflow_version: 2; existing projects are not migrated")
    for directory in (boards_dir, briefs_dir, grids_dir, details_dir):
        directory.mkdir(parents=True, exist_ok=True)
    state.setdefault("shot_board", {})
    state["shot_board"].setdefault("next_shot_id", 1)
    state["shot_board"].setdefault("active_board", None)
    state["shot_board"].setdefault("selected_shot_ids", [])
    state["shot_board"].setdefault("enlargements", [])
    state.setdefault("artifacts", {})
    return state_path, state, boards_dir, briefs_dir, grids_dir, details_dir


def board_file(boards_dir: Path, board_id: str) -> Path:
    path = boards_dir / f"{board_id}.yaml"
    if not path.exists():
        raise SystemExit(f"unknown shot board: {board_id}")
    return path


def _normalize_participants_present(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [part.strip() for part in re.split(r"[,，、]", value) if part.strip()]
    if isinstance(value, list):
        return [str(part).strip() for part in value if str(part).strip()]
    raise SystemExit("participants_present must be a list or comma-separated string")


def _normalize_directions(value: object) -> list[dict]:
    if value is None:
        return []
    if isinstance(value, dict):
        return [{"participant_id": str(key).strip(), "direction": compact(item)} for key, item in value.items()]
    if not isinstance(value, list):
        raise SystemExit("participant_directions must be a list or mapping")
    result = []
    for item in value:
        if not isinstance(item, dict):
            raise SystemExit("each participant_directions item must be an object")
        pid = str(item.get("participant_id") or item.get("id") or "").strip()
        direction = compact(item.get("direction") or item.get("action") or item.get("blocking") or item)
        if not pid or not direction:
            raise SystemExit("each participant_directions item requires participant_id and direction/action")
        result.append({"participant_id": pid, "direction": direction})
    return result


def validate_shots(value: object, lock: dict | None = None) -> list[dict]:
    if not isinstance(value, list) or len(value) != BOARD_SIZE:
        raise SystemExit("shots file must contain exactly eight shot objects")
    shots: list[dict] = []
    roster = [person["participant_id"] for person in (lock or {}).get("participant_outfits", [])]
    multi = len(roster) > 2
    compressed_terms = ("其他人", "其余人", "剩下的人", "others")
    coverage: set[str] = set()
    has_full_group = False
    for index, item in enumerate(value, start=1):
        if not isinstance(item, dict) or any(not str(item.get(field, "")).strip() for field in REQUIRED_SHOT_FIELDS):
            raise SystemExit(f"shot {index} must include: {', '.join(REQUIRED_SHOT_FIELDS)}")
        shot = {field: str(item[field]).strip() for field in REQUIRED_SHOT_FIELDS}
        strict_location = bool((lock or {}).get("strict_location"))
        if strict_location:
            location_context = str(item.get("location_context", "")).strip()
            era_or_world_context = str(item.get("era_or_world_context", "")).strip()
            if generic_location(location_context):
                raise SystemExit(f"shot {index} must include a concrete location_context under schema v3 location lock")
            if generic_location(shot["scene_area"]):
                raise SystemExit(f"shot {index} scene_area must be a concrete micro-location inside the confirmed place")
            if (lock or {}).get("requires_era_or_world_context") and not era_or_world_context:
                raise SystemExit(f"shot {index} requires era_or_world_context for historical/source-work/original-fictional setting")
            shot["location_context"] = location_context
            shot["era_or_world_context"] = era_or_world_context or "contemporary"
        else:
            shot["location_context"] = str(item.get("location_context", "")).strip()
            shot["era_or_world_context"] = str(item.get("era_or_world_context", "")).strip()
        present = _normalize_participants_present(item.get("participants_present"))
        directions = _normalize_directions(item.get("participant_directions"))
        if roster and not present:
            if multi:
                raise SystemExit(f"shot {index} must include participants_present for a multi-person project")
            present = list(roster)
        if roster:
            unknown = [pid for pid in present if pid not in roster]
            if unknown:
                raise SystemExit(f"shot {index} references unknown participant ids: {', '.join(unknown)}")
            if directions:
                direction_ids = [entry["participant_id"] for entry in directions]
                if len(direction_ids) != len(set(direction_ids)):
                    raise SystemExit(f"shot {index} has duplicate participant_directions ids")
                if set(direction_ids) != set(present):
                    raise SystemExit(f"shot {index} participant_directions must describe every participant_present exactly once")
            elif multi:
                raise SystemExit(f"shot {index} must include participant_directions for every visible person")
            coverage.update(present)
            if set(present) == set(roster):
                has_full_group = True
        if multi:
            joined = " ".join(shot.values()) + " " + " ".join(entry["direction"] for entry in directions)
            if any(term.lower() in joined.lower() for term in compressed_terms):
                raise SystemExit(f"shot {index} uses compressed group wording; describe every visible participant individually")
        shot["participants_present"] = present
        shot["participant_directions"] = directions
        shots.append(shot)
    if roster and set(roster) - coverage:
        missing = sorted(set(roster) - coverage)
        raise SystemExit(f"the eight-shot board must include every confirmed participant at least once; missing: {', '.join(missing)}")
    if multi and not has_full_group:
        raise SystemExit("a multi-person eight-shot board must contain at least one full-group shot unless the handoff is explicitly changed")
    return shots


def compact(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return "；".join(f"{key}：{compact(item)}" for key, item in value.items() if compact(item))
    if isinstance(value, list):
        return "、".join(filter(None, (compact(item) for item in value)))
    return str(value).strip()


def confirmed_visual_lock(project: Path, look_id: str) -> dict:
    handoff_path = project / "deliverables" / "requirements-handoff.yaml"
    if not handoff_path.exists():
        raise SystemExit(f"missing confirmed photography handoff: {handoff_path}")
    handoff = read_yaml(handoff_path)
    look = next((item for item in handoff.get("looks", []) if item.get("id") == look_id), None)
    if not look or look.get("status") not in {"confirmed", "selected", "ready"}:
        raise SystemExit(f"--look-id must refer to an authorized selected handoff look: {look_id}")
    declared_lock = look.get("visual_lock") or {}
    project_context = handoff.get("project", {})
    schema_version = handoff.get("schema_version")
    styling_required = bool(project_context.get("styling_policy", {}).get("professional_nodes_required"))
    share_card_required = bool(project_context.get("share_card_policy", {}).get("required_before_render"))
    roster_identity = {}
    identity_meta = {}
    for roster_person in project_context.get("participants", []) if isinstance(project_context.get("participants", []), list) else []:
        if isinstance(roster_person, dict):
            pid = str(roster_person.get("id") or "").strip()
            originals = roster_person.get("original_identity_references") or roster_person.get("identity_references") or []
            if pid:
                roster_identity[pid] = originals
                identity_meta[pid] = {"canonical_original_references": list(originals), "active_reference_source": "original_user_upload", "explicit_promotion": False}
    for mapped in project_context.get("identity_map", []) if isinstance(project_context.get("identity_map", []), list) else []:
        if isinstance(mapped, dict):
            pid = str(mapped.get("participant_id") or "").strip()
            originals = mapped.get("canonical_original_references") or []
            promoted = bool(mapped.get("explicit_promotion"))
            active = mapped.get("active_identity_references") or mapped.get("identity_references") or originals
            source = str(mapped.get("active_reference_source") or ("explicit_user_promoted_derived" if promoted else "original_user_upload"))
            # Canonical hard gate: absent explicit promotion, active identity is forced back to original uploads.
            refs = active if promoted else (originals or active)
            if pid and refs:
                roster_identity[pid] = refs
                identity_meta[pid] = {"canonical_original_references": list(originals or refs), "active_reference_source": source if promoted else "original_user_upload", "explicit_promotion": promoted}
    location_lock = declared_lock.get("location_lock") or look.get("scenes") or []
    strict_location = schema_version == 3
    requires_era_or_world_context = False
    if strict_location and isinstance(location_lock, list):
        for scene in location_lock:
            if isinstance(scene, dict) and scene.get("location_mode") in {"historical_real_world", "future_landmark", "source_work", "original_fictional"}:
                requires_era_or_world_context = True
                break

    participant_outfits = declared_lock.get("participant_outfits") or look.get("participant_looks") or []
    normalized: list[dict] = []
    if isinstance(participant_outfits, list):
        for index, person in enumerate(participant_outfits, start=1):
            if not isinstance(person, dict):
                continue
            pid = str(person.get("participant_id") or person.get("id") or f"P{index:02d}").strip()
            label = str(person.get("label") or person.get("name") or person.get("role") or pid).strip()
            outfit = compact(person.get("outfit") or person.get("wardrobe") or person.get("full_description"))
            if pid and outfit:
                
                hairstyle = compact(person.get("hairstyle_design") or person.get("hair_design") or person.get("hairstyle"))
                makeup = compact(person.get("makeup_design") or person.get("makeup") or person.get("grooming_makeup"))
                if styling_required and not hairstyle:
                    raise SystemExit(f"authorized look {look_id} participant {pid} is missing hairstyle_design; run the early Editorial hairstylist node")
                if styling_required and not makeup:
                    raise SystemExit(f"authorized look {look_id} participant {pid} is missing makeup_design; run the early Editorial makeup node")
                normalized.append({"participant_id": pid, "label": label, "outfit": outfit, "hairstyle_design": hairstyle, "makeup_design": makeup, "identity_references": roster_identity.get(pid, []), "identity_reference_meta": identity_meta.get(pid, {})})

    legacy_female = compact(declared_lock.get("female_outfit")) or compact(look.get("female_outfit"))
    legacy_male = compact(declared_lock.get("male_outfit")) or compact(look.get("male_outfit"))
    legacy_pair = False
    if not normalized and legacy_female and legacy_male:
        legacy_pair = True
        normalized = [
            {"participant_id": "P01", "label": "女生", "outfit": legacy_female, "hairstyle_design": "legacy-confirmed hairstyle", "makeup_design": "legacy-confirmed makeup", "identity_references": roster_identity.get("P01", []), "identity_reference_meta": identity_meta.get("P01", {})},
            {"participant_id": "P02", "label": "男生", "outfit": legacy_male, "hairstyle_design": "legacy-confirmed hairstyle", "makeup_design": "legacy-confirmed makeup", "identity_references": roster_identity.get("P02", []), "identity_reference_meta": identity_meta.get("P02", {})},
        ]
    if not normalized:
        raise SystemExit(f"confirmed look {look_id} must include at least one participant outfit")

    scenes = compact(look.get("scenes", []))
    relationship = compact(declared_lock.get("group_relationship")) or compact(look.get("group_relationship")) or compact(declared_lock.get("couple_relationship")) or compact(look.get("couple_relationship"))
    result = {
        "participant_outfits": normalized,
        "group_relationship": relationship,
        "world_context": compact(declared_lock.get("work_era_setting")) or compact({key: project_context.get(key) for key in ("theme", "worldview", "media_references", "location_context", "visual_direction")}),
        "scene_context": compact(declared_lock.get("scene_mood")) or scenes,
        "location_lock": location_lock,
        "strict_location": strict_location,
        "requires_era_or_world_context": requires_era_or_world_context,
        "hard_avoids": compact(declared_lock.get("hard_avoids")) or compact(project_context.get("hard_avoids", [])),
        "legacy_pair": legacy_pair,
        "styling_required": styling_required,
        "share_card_required": share_card_required,
    }
    if legacy_pair:
        result["female_outfit"] = legacy_female
        result["male_outfit"] = legacy_male
        result["couple_relationship"] = relationship
    return result


def portrait_reference_quality_prompt() -> str:
    return (
        "真人身份参考 Hard Gate：除非用户明确要求把某张美化图或后续生成图设为人物参考，否则每次生图都必须继续使用该 participant 最初上传的真人原图作为 canonical identity reference。任何 meihua 输出、八宫格、单张 Shot、放大图、重绘图或此前 AI 生成图都不得自动替代原图做人脸参考。\n"
        "如需使用上一轮生成图保持姿势、构图、场景或风格，只把它作为 composition/pose/style reference；身份仍由原始真人图锁定。\n"
        "参考图只锁定身份，不锁定表情：保持脸型、五官结构、年龄感与辨识度，但每个 Shot 按自身动作与情绪重新生成嘴型、笑意、眼神、视线和头部角度。\n"
        "原参考图只做人脸身份锚定，不做发型锚定：只保持脸型、核心五官、年龄印象和识别度。必须忽略原图中的发长、直卷、刘海、分缝、顶部体积、两侧/后区轮廓与发色质感；最终生图只执行方向阶段已锁定的 Editorial 专业发型师设计，除非用户明确要求保留原图发型。\n"
        "最终生图还必须执行方向阶段已经锁定的 Editorial 专业化妆师设计。"
    )


def identity_lock_v2_prompt(lock: dict) -> str:
    people=[]
    for person in lock.get("participant_outfits", []):
        refs=person.get("identity_references") or []
        if not refs:
            continue
        meta=person.get("identity_reference_meta") or {}
        source=meta.get("active_reference_source") or "original_user_upload"
        people.append(f"- {person.get('participant_id')} ({person.get('label')}): active identity source={source}; reference={compact(refs)}")
    if not people:
        return ""
    return (
        "IDENTITY LOCK — HIGHEST PRIORITY\n"
        "The identity references listed below are the sole authoritative facial-identity sources for their matching participants.\n"
        + "\n".join(people) + "\n"
        "For EVERY panel, reconstruct each visible participant's face directly and independently from that participant's identity reference. "
        "Do NOT derive a face from another generated panel, a prior contact-sheet cell, a rerendered portrait, or any composition reference. "
        "Do NOT average, interpolate, redesign, or gradually evolve facial identity across panels.\n"
        "Preserve the same recognizable facial geometry across all panels: face shape and width-to-height ratio; forehead proportion; eye shape and eye spacing; brow placement; nose bridge, nose width and nose-tip structure; cheekbone structure; mouth width and lip proportions; jawline and chin shape; age impression; overall recognizability.\n"
        "Makeup, skin retouching, lighting, expression and camera angle may change appearance, but must NOT alter facial-feature geometry. Identity consistency has higher priority than pose, composition, lighting, styling, environmental scale or cinematic effect.\n"
        "The original identity reference controls FACE IDENTITY ONLY. Ignore hair length, straight/curly/wavy texture, bangs/fringe, parting, crown volume, side/back silhouette and hair-color feel from the identity image unless the user explicitly locked the original hairstyle. Execute the locked Editorial hairstyle_design instead.\n"
        "No face drift. No identity interpolation. No panel-to-panel facial evolution. No face swap."
    )


def panel_identity_reset_prompt(shot: dict, lock: dict) -> str:
    visible=shot.get("participants_present") or [p.get("participant_id") for p in lock.get("participant_outfits", [])]
    clauses=[]
    for person in lock.get("participant_outfits", []):
        pid=person.get("participant_id")
        refs=person.get("identity_references") or []
        if pid not in visible or not refs:
            continue
        source=(person.get("identity_reference_meta") or {}).get("active_reference_source") or "original_user_upload"
        clauses.append(
            f"{pid}: restore the exact recognizable facial identity directly from {pid}'s active identity reference ({source}); do not inherit facial appearance from any other generated panel"
        )
    if not clauses:
        return ""
    return "PANEL IDENTITY RESET — " + "; ".join(clauses) + ". Identity consistency outranks pose, composition and lighting for this panel."


def face_readability_guard(shot: dict) -> str:
    text=" ".join(str(shot.get(k, "")) for k in ("shot_size","composition","action_event","pose_structure","prompt")).lower()
    guards=[]
    if any(term in text for term in ("full-body","full body","wide full","全身","远景","大全景","wide shot")):
        guards.append("Even in this full-body/environmental framing, keep every planned visible real face sufficiently resolved and large enough to remain identity-readable; do not make the subject so tiny that facial identity becomes ambiguous")
    if any(term in text for term in ("back-facing","back facing","over one shoulder","背身","背对","回头","回望")):
        guards.append("For the back-oriented/over-shoulder pose, unless the user explicitly requested a hidden face, rotate the head and necessary upper torso enough that the real face remains clearly visible and identity-readable")
    if any(term in text for term in ("reflection","reflective","mirror","倒影","镜面","反射")):
        guards.append("The real person's face is the primary identity anchor; any reflection is secondary, must show the same identity, and must not distort facial geometry")
    if not guards:
        guards.append("Whenever the face is intended to be visible, keep it sufficiently clear and readable to preserve identity")
    return "FACE READABILITY GATE — " + "; ".join(guards) + "."


def visual_lock_prompt(lock: dict) -> str:
    people = ["已确认且不可替换的人物视觉锁定："]
    for person in lock["participant_outfits"]:
        people.append(f"- {person['participant_id']}｜{person['label']}服装：{person['outfit']}")
        if person.get("hairstyle_design"):
            people.append(f"- {person['participant_id']}｜{person['label']}正式发型：{person['hairstyle_design']}")
        if person.get("makeup_design"):
            people.append(f"- {person['participant_id']}｜{person['label']}正式妆容/皮肤优化：{person['makeup_design']}")
        refs = person.get("identity_references") or []
        if refs:
            meta = person.get('identity_reference_meta') or {}; source = meta.get('active_reference_source') or 'original_user_upload'; people.append(f"- {person['participant_id']}｜{person['label']}身份参考映射：{compact(refs)}；身份源={source}；默认必须持续使用最初上传原图，除非用户显式提升派生图；这些参考只属于该 participant_id，禁止交换脸或身份")
    people.extend([
        f"- 群体造型与关系：{lock['group_relationship'] or '沿用已确认的人物关系与群体造型逻辑'}",
        f"- 作品／时代／场景语境：{lock['world_context'] or lock['scene_context'] or '沿用已确认主题'}",
        f"- 场景与道具语境：{lock['scene_context'] or '沿用已确认场景'}",
        f"- 具体地点锁定：{compact(lock.get('location_lock')) or '沿用已确认具体地点'}",
        f"- 避免项：{lock['hard_avoids'] or '沿用已确认避免项'}",
        f"- 人脸质量：{portrait_reference_quality_prompt().replace(chr(10), '；')}",
    ])
    if lock.get("legacy_pair"):
        people.append("两人必须完整穿着以上各自服装；不得把任一方替换为普通西装、默认礼服或其他未确认造型。")
    else:
        people.append("所有出镜人物必须完整穿着各自已确认服装；不得省略人物、合并身份、交换服装；如存在身份参考映射，必须严格按 participant_id 使用对应参考，禁止 identity swap / face swap。")
    return "\n".join(people)


def inject_visual_lock(shots: list[dict], lock: dict) -> list[dict]:
    lock_prompt = visual_lock_prompt(lock)
    for shot in shots:
        if any(term in shot["prompt"] for term in ("普通西装", "默认礼服", "统一西装")) and not any(term in person["outfit"] for person in lock["participant_outfits"] for term in ("普通西装", "默认礼服", "统一西装")):
            raise SystemExit("shot prompt conflicts with the confirmed participant outfits; remove generic default-clothing wording")
    injected = []
    for shot in shots:
        item = dict(shot)
        if item.get("participants_present"):
            present_line = "、".join(item["participants_present"])
            directions = "；".join(f"{entry['participant_id']}：{entry['direction']}" for entry in item.get("participant_directions", []))
            per_person = f"本格出镜：{present_line}" + (f"；逐人调度：{directions}" if directions else "")
        else:
            per_person = ""
        location_line = f"完整地点锚点：{item.get('location_context') or compact(lock.get('location_lock'))}；具体拍摄节点：{item.get('scene_area')}；时代/作品状态：{item.get('era_or_world_context') or compact(lock.get('world_context'))}"
        item["continuity"] = f"{lock_prompt.replace(chr(10), '；')}；{location_line}；{per_person}；{item['continuity']}"
        item["prompt"] = f"摄影关键词：{PHOTOGRAPHY_KEYWORDS}。\n\n{lock_prompt}\n\n本格地点锁定：\n{location_line}\n\n本格出镜与逐人调度：\n{per_person or item['interaction']}\n\n本格 Shot 的动作与构图：\n{item['prompt']}\n\n再次确认：所有出镜人物的身份、服装、具体地点、作品／时代语境与避免项均不得替换或泛化。"
        injected.append(item)
    return injected


def render_markdown(board: dict) -> str:
    lines = [
        f"# 8 宫格 Shot List｜{board['board_id']}", "",
        f"Look：{board['look_id']}", f"主题：{board['theme']}", "",
        "## 已确认视觉锁定", "", visual_lock_prompt(board["visual_lock"]), "",
        "状态：文字方案审阅", "",
    ]
    for shot in board["shots"]:
        lines.extend([
            f"## {shot['shot_id']}｜{shot['title']}", "",
            f"- 拍摄目的：{shot['purpose']}",
            f"- 完整地点锚点：{shot.get('location_context') or compact(board['visual_lock'].get('location_lock'))}",
            f"- 动作事件：{shot['action_event']}",
            f"- 姿势结构：{shot['pose_structure']}",
            f"- 关键受力/重心：{shot['key_support_weight']}",
            f"- 关系/接触：{shot['relationship_contact']}",
            f"- 情绪动机：{shot['emotion_motivation']}",
            f"- 视线：{shot['gaze']}",
            f"- 景别适配：{shot['framing_adaptation']}",
            f"- 场景具体节点：{shot['scene_area']}",
            f"- 时代 / 作品世界状态：{shot.get('era_or_world_context') or compact(board['visual_lock'].get('world_context'))}",
        ])
        if shot.get("participants_present"):
            lines.append(f"- 出镜人物：{'、'.join(shot['participants_present'])}")
        if shot.get("participant_directions"):
            lines.append("- 逐人调度：")
            for entry in shot["participant_directions"]:
                lines.append(f"  - {entry['participant_id']}：{entry['direction']}")
        lines.extend([
            f"- 群体互动：{shot['interaction']}",
            f"- 景别：{shot['shot_size']}",
            f"- 构图：{shot['composition']}",
            f"- 光线：{shot['lighting']}",
            f"- 服装与道具连续性：{shot['continuity']}",
            f"- 避免项：{shot['avoids']}",
            "",
        ])
    lines.append("确认整组后，才将 8 条 Shot 编译为一次生成的一张八宫格预览图；不指定单格尺寸比例或整板比例，只要求恰好 8 格、每格清晰独立可读；如需新方向，直接说“再来一批”。")
    return "\n".join(lines) + "\n"


def create(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    state_path, state, boards_dir, _, _, _ = load_project(project)
    raw_shots = json.loads(Path(args.shots_file).read_text(encoding="utf-8"))
    look_id = args.look_id.strip()
    theme = args.theme.strip()
    if not look_id or not theme:
        raise SystemExit("--look-id and --theme are required")
    lock = confirmed_visual_lock(project, look_id)
    shots = validate_shots(raw_shots, lock)
    shots = inject_visual_lock(shots, lock)
    board_number = len(list(boards_dir.glob("SHOTBOARD-*.yaml"))) + 1
    board_id = f"SHOTBOARD-{board_number:03d}"
    start = int(state["shot_board"]["next_shot_id"])
    numbered = [{"shot_id": start + index, **shot} for index, shot in enumerate(shots)]
    board = {
        "board_id": board_id,
        "created_at": now(),
        "look_id": look_id,
        "theme": theme,
        "visual_lock": lock,
        "status": "text_review",
        "grid_mode": GRID_MODE_SINGLE,
        "number_range": [start, start + BOARD_SIZE - 1],
        "shots": numbered,
        "cell_images": {},
        "grid_brief": None,
        "grid_source_image": None,
        "grid_image": None,
        "selected_shot_ids": [],
        "share_card": None,
    }
    board_path = boards_dir / f"{board_id}.yaml"
    write_yaml(board_path, board)
    markdown_path = boards_dir / f"{board_id}.md"
    markdown_path.write_text(render_markdown(board), encoding="utf-8")
    state["stage"] = "SHOTLIST_REVIEW"
    state["shot_board"].update({"next_shot_id": start + BOARD_SIZE, "active_board": board_id, "selected_shot_ids": []})
    state["artifacts"].update({"shot_list": rel(project, markdown_path), "shot_board": rel(project, board_path), "shot_grid": None})
    write_yaml(state_path, state)
    print(board_path)


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


def parse_cells(values: list[str], expected: set[int]) -> dict[int, Path]:
    cells: dict[int, Path] = {}
    for raw in values:
        try:
            raw_id, raw_path = raw.split("=", 1)
            cells[int(raw_id)] = Path(raw_path).resolve()
        except ValueError as error:
            raise SystemExit(f"invalid --cell value: {raw}") from error
    if set(cells) != expected:
        raise SystemExit(f"--cell ids must exactly match {sorted(expected)}")
    missing = [str(path) for path in cells.values() if not path.exists()]
    if missing:
        raise SystemExit(f"missing cell images: {', '.join(missing)}")
    return cells


def grid_prompt(board: dict) -> str:
    identity_block = identity_lock_v2_prompt(board.get("visual_lock", {}))
    lines = [
        "Generate ONE SINGLE IMAGE: an editorial contact sheet with exactly eight distinct photographic panels.",
        f"摄影关键词：{PHOTOGRAPHY_KEYWORDS}。",
    ]
    if identity_block:
        lines.extend([identity_block, "FACE READABILITY RULE — Across the whole board, whenever a face is meant to be visible, keep the real face sufficiently clear, sufficiently large and identity-readable. Do not sacrifice facial identity readability merely to make the environment wider or more dramatic."])
    lines.extend([
        "This is an eight-panel contact sheet. Do not specify or force any panel aspect ratio, panel dimensions, overall board aspect ratio, row count, or column count.",
        "Arrange all eight panels freely as one balanced contact sheet. Every panel must read as a clear, standalone photograph with clear separation from neighboring panels; avoid ultra-narrow strips or unreadable collage fragments.",
        "Keep the eight assigned Shots in natural visual reading order from upper-left across/down, whatever layout you choose. Keep each panel visually distinct and faithful to its assigned Shot.",
        "Do not render any text, digits, labels, captions, logos, watermarks, poster layout, or extra panels. Do not merge actions between panels.",
        "This is one coherent portrait/ensemble-photo set: preserve every confirmed identity, each participant's own wardrobe, historical era or work world, group relationship, scene constraints, and avoids across all panels.",
        "Never omit, merge, duplicate, or invent participants. In every panel, follow that Shot's participants_present and participant_directions exactly.",
        "Preserve each Shot's full location_context, exact scene_area, and era/world context; never collapse a named place into a generic hotel, street, garden, palace, or studio.",
        portrait_reference_quality_prompt(),
        "FINAL READABILITY CHECK: exactly 8 panels; each panel is clearly separated and individually readable; no ultra-narrow strips; no extra panels.",
        "\nPanel specifications:",
    ])
    for position, shot in enumerate(board["shots"], start=1):
        panel_lock = panel_identity_reset_prompt(shot, board.get("visual_lock", {}))
        readability = face_readability_guard(shot)
        prefix = "\n".join(x for x in (panel_lock, readability) if x)
        lines.append(f"\nPanel {position} (slot {shot['shot_id']}):\n{prefix}\n{shot['prompt']}")
    return "\n".join(lines)

def next_grid_brief_version(briefs_dir: Path, board_id: str) -> int:
    version = 1
    while (briefs_dir / f"{board_id}-grid-v{version}.yaml").exists():
        version += 1
    return version


def prepare_grid(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    state_path, state, boards_dir, _, grids_dir, _ = load_project(project)
    path = board_file(boards_dir, args.board_id)
    board = read_yaml(path)
    if board.get("status") != "text_review":
        raise SystemExit("only a text_review shot board can prepare a single grid")
    share_card = board.get("share_card") or {}
    if board.get("visual_lock", {}).get("share_card_required") and share_card.get("status") not in {"ready", "skipped"}:
        raise SystemExit("compile Share Card before image rendering, or explicitly mark it skipped when the user asks for no copy")
    briefs_dir = project / "deliverables" / "shot-grid-briefs"
    version = next_grid_brief_version(briefs_dir, board["board_id"])
    brief_path = briefs_dir / f"{board['board_id']}-grid-v{version}.yaml"
    source_path = grids_dir / f"{board['board_id']}-source.png"
    output_path = grids_dir / f"{board['board_id']}.png"
    layout_policy = grid_layout_policy()
    prompt = grid_prompt(board)
    brief = {
        "brief_id": brief_path.stem,
        "status": "pending",
        "board_id": board["board_id"],
        "grid_mode": GRID_MODE_SINGLE,
        "layout_policy": layout_policy,
        "panel_aspect_ratio": None,
        "requested_panel_aspect_ratio": None,
        "slot_mapping": [{"slot": index, "shot_id": shot["shot_id"], "title": shot["title"]} for index, shot in enumerate(board["shots"], start=1)],
        "render_prompt": prompt,
        "identity_lock_version": 2,
        "identity_reference_semantics": "face_geometry_only; per-panel direct reconstruction; no panel-to-panel inheritance",
        "identity_references": [
            {"participant_id": person.get("participant_id"), "references": person.get("identity_references") or [], "source": (person.get("identity_reference_meta") or {}).get("active_reference_source", "original_user_upload")}
            for person in board.get("visual_lock", {}).get("participant_outfits", []) if isinstance(person, dict) and (person.get("identity_references") or [])
        ],
        "source_image": None,
        "output_path": rel(project, output_path),
        "numbering": "No fixed-grid badge overlay. Panel identity follows the stored Shot order / natural visual reading order.",
        "created_at": now(),
    }
    write_yaml(brief_path, brief)
    board.update({"grid_mode": GRID_MODE_SINGLE, "grid_brief": rel(project, brief_path), "grid_source_image": rel(project, source_path), "grid_image": None, "cell_images": {}, "panel_aspect_ratio": None, "grid_layout": None})
    write_yaml(path, board)
    state["shot_board"]["active_board"] = board["board_id"]
    write_yaml(state_path, state)
    print(f"GRID_BRIEF: {rel(project, brief_path)}\n\n{prompt}")


def draw_grid_badges(image: Image.Image, shot_ids: list[int], columns: int, rows: int) -> Image.Image:
    canvas = image.convert("RGB")
    draw = ImageDraw.Draw(canvas)
    cell_width = canvas.width / columns
    cell_height = canvas.height / rows
    badge_size = max(40, int(min(cell_width, cell_height) * 0.16))
    margin = max(12, int(min(cell_width, cell_height) * 0.035))
    badge_font = font(max(20, int(badge_size * 0.52)))
    for index, shot_id in enumerate(shot_ids):
        x = int((index % columns) * cell_width + margin)
        y = int((index // columns) * cell_height + margin)
        badge = (x, y, x + badge_size, y + badge_size)
        draw.rounded_rectangle(badge, radius=max(12, badge_size // 4), fill="#151515", outline="#FFFFFF", width=max(2, badge_size // 24))
        label = str(shot_id)
        box = draw.textbbox((0, 0), label, font=badge_font)
        draw.text((x + (badge_size - (box[2] - box[0])) / 2, y + (badge_size - (box[3] - box[1])) / 2 - 2), label, font=badge_font, fill="#FFFFFF")
    return canvas


def register_grid(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    state_path, state, boards_dir, _, grids_dir, _ = load_project(project)
    path = board_file(boards_dir, args.board_id)
    board = read_yaml(path)
    if board.get("status") != "text_review":
        raise SystemExit("only a text_review shot board can register a single grid")
    if board.get("grid_mode") != GRID_MODE_SINGLE or not board.get("grid_brief"):
        raise SystemExit("prepare-grid must compile the single-grid prompt before registering an image")
    source = Path(args.image).resolve()
    if not source.exists():
        raise SystemExit(f"missing grid image: {source}")
    brief_path = project / board["grid_brief"]
    if not brief_path.exists():
        raise SystemExit(f"missing grid brief: {brief_path}")
    source_path = grids_dir / f"{board['board_id']}-source.png"
    output_path = grids_dir / f"{board['board_id']}.png"
    brief = read_yaml(brief_path)
    with Image.open(source) as image:
        image.convert("RGB").save(source_path, format="PNG")
        image.convert("RGB").save(output_path, format="PNG")
    brief.update({"status": "registered", "source_image": rel(project, source_path), "output_path": rel(project, output_path), "registered_at": now()})
    write_yaml(brief_path, brief)
    board.update({"status": "grid_review", "grid_mode": GRID_MODE_SINGLE, "grid_source_image": rel(project, source_path), "grid_image": rel(project, output_path), "cell_images": {}})
    write_yaml(path, board)
    state["stage"] = "SHOT_GRID_REVIEW"
    state["shot_board"]["active_board"] = board["board_id"]
    state["artifacts"]["shot_grid"] = rel(project, output_path)
    write_yaml(state_path, state)
    print(output_path)


def compose(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    state_path, state, boards_dir, _, grids_dir, _ = load_project(project)
    path = board_file(boards_dir, args.board_id)
    board = read_yaml(path)
    if board.get("status") != "text_review":
        raise SystemExit("only a text_review shot board can be composed")
    if board.get("grid_mode", GRID_MODE_LEGACY) != GRID_MODE_LEGACY:
        raise SystemExit("compose is reserved for legacy composed_cells boards; use prepare-grid and register-grid for new boards")
    expected = {int(shot["shot_id"]) for shot in board["shots"]}
    cells = parse_cells(args.cell, expected)
    width, height = 720, 900
    columns, rows = 4, 2
    gutter, border = 14, 22
    canvas = Image.new("RGB", (width * columns + gutter * (columns - 1) + border * 2, height * rows + gutter * (rows - 1) + border * 2), "#F4F1ED")
    draw = ImageDraw.Draw(canvas)
    badge_font = font(44)
    stored_cells: dict[str, str] = {}
    cells_dir = grids_dir / board["board_id"] / "cells"
    cells_dir.mkdir(parents=True, exist_ok=True)
    for index, shot_id in enumerate(sorted(expected)):
        x = border + (index % columns) * (width + gutter)
        y = border + (index // columns) * (height + gutter)
        source_path = cells[shot_id]
        source = Image.open(source_path).convert("RGB")
        canvas.paste(ImageOps.fit(source, (width, height), method=Image.Resampling.LANCZOS, centering=(0.5, 0.5)), (x, y))
        badge = (x + 24, y + 24, x + 112, y + 112)
        draw.rounded_rectangle(badge, radius=24, fill="#151515", outline="#FFFFFF", width=3)
        label = str(shot_id)
        box = draw.textbbox((0, 0), label, font=badge_font)
        draw.text((x + 68 - (box[2] - box[0]) / 2, y + 68 - (box[3] - box[1]) / 2 - 4), label, font=badge_font, fill="#FFFFFF")
        persisted = cells_dir / f"SHOT-{shot_id:03d}.png"
        shutil.copy2(source_path, persisted)
        stored_cells[str(shot_id)] = rel(project, persisted)
    output = grids_dir / f"{board['board_id']}.png"
    canvas.save(output, format="PNG")
    board.update({"status": "grid_review", "grid_mode": GRID_MODE_LEGACY, "cell_images": stored_cells, "grid_image": rel(project, output)})
    write_yaml(path, board)
    state["stage"] = "SHOT_GRID_REVIEW"
    state["shot_board"]["active_board"] = board["board_id"]
    state["artifacts"]["shot_grid"] = rel(project, output)
    write_yaml(state_path, state)
    print(output)


def selected_shots(boards_dir: Path, ids: list[int]) -> dict[int, dict]:
    found: dict[int, dict] = {}
    for path in boards_dir.glob("SHOTBOARD-*.yaml"):
        board = read_yaml(path)
        for shot in board.get("shots", []):
            found[int(shot["shot_id"])] = {"board": board, "shot": shot, "path": path}
    unknown = [str(value) for value in ids if value not in found]
    if unknown:
        raise SystemExit(f"selected shot ids are unavailable: {', '.join(unknown)}")
    return {value: found[value] for value in ids}


def next_version(briefs_dir: Path, shot_id: int, orientation: str) -> int:
    version = 1
    while (briefs_dir / f"SHOT-{shot_id:03d}-detail-{orientation}-v{version}.yaml").exists():
        version += 1
    return version


def next_anchor_version(anchors_dir: Path, shot_id: int) -> int:
    version = 1
    while (anchors_dir / f"SHOT-{shot_id:03d}-anchor-v{version}.png").exists():
        version += 1
    return version


def selection_anchor(project: Path, board: dict, shot_id: int) -> tuple[Path, str]:
    anchors_dir = project / "images" / "shot-boards" / board["board_id"] / "selection-anchors"
    anchors_dir.mkdir(parents=True, exist_ok=True)
    output = anchors_dir / f"SHOT-{shot_id:03d}-anchor-v{next_anchor_version(anchors_dir, shot_id)}.png"
    grid_mode = board.get("grid_mode", GRID_MODE_LEGACY)
    if grid_mode == GRID_MODE_SINGLE:
        source_value = board.get("grid_source_image")
        source = project / source_value if source_value else None
        if not source or not source.exists():
            raise SystemExit(f"single_grid board is missing its source grid image for shot {shot_id}")
        shot_ids = [int(shot["shot_id"]) for shot in board["shots"]]
        try:
            position = shot_ids.index(shot_id)
        except ValueError as error:
            raise SystemExit(f"shot {shot_id} is not part of {board['board_id']}") from error
        # Free-layout contact sheets cannot be safely cropped by fixed row/column math.
        # Keep the full contact sheet as a visual reference; the detail brief identifies
        # the target Shot by its stored order and prompt.
        with Image.open(source) as image:
            image.convert("RGB").save(output, format="PNG")
        return output, "single_grid_full_contact_sheet"
    if grid_mode == GRID_MODE_LEGACY:
        source_value = board.get("cell_images", {}).get(str(shot_id))
        source = project / source_value if source_value else None
        if not source or not source.exists():
            raise SystemExit(f"composed_cells board is missing its source cell image for shot {shot_id}")
        with Image.open(source) as image:
            image.convert("RGB").save(output, format="PNG")
        return output, "legacy_cell"
    raise SystemExit(f"unsupported grid mode for selection anchor: {grid_mode!r}")


def select(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    state_path, state, boards_dir, briefs_dir, _, _ = load_project(project)
    if state.get("stage") != "SHOT_GRID_REVIEW":
        raise SystemExit("shot selection requires SHOT_GRID_REVIEW")
    ids = [int(value.strip()) for value in args.ids.split(",") if value.strip()]
    if not ids or len(set(ids)) != len(ids):
        raise SystemExit("--ids must be a non-empty comma-separated list of unique shot ids")
    selected = selected_shots(boards_dir, ids)
    orientation = args.orientation
    detail = args.detail.strip()
    records = []
    for shot_id, item in selected.items():
        version = next_version(briefs_dir, shot_id, orientation)
        filename = f"SHOT-{shot_id:03d}-detail-{orientation}-v{version}.yaml"
        output = project / "images" / "shot-details" / f"SHOT-{shot_id:03d}-{orientation}-v{version}.png"
        supplement = detail or "在不改变已确认人物、服装、场景、关系和避免项的前提下，补足自然环境、微互动与真实摄影细节。"
        anchor, anchor_source = selection_anchor(project, item["board"], shot_id)
        ordered_ids = [int(s["shot_id"]) for s in item["board"]["shots"]]
        panel_position = ordered_ids.index(shot_id) + 1
        legacy_pair = bool(item["board"].get("visual_lock", {}).get("legacy_pair"))
        interaction_term = "两人的姿势互动" if legacy_pair else "所有出镜人物的姿势互动与逐人调度"
        preservation = {
            "required": ["所有出镜人物的身份与各自服装", interaction_term, "所有人物的相对站位与身体朝向", "逐人手部与道具关系", "逐人视线与表情方向", "人物与环境的空间关系", "镜头意图与构图重心"],
            "allowed": ["目标画幅下的自然重新取景", "环境空间的自然延展", "皮肤、织物与光线细节", "用户明确要求的细节"],
            "prohibited": ["机械拼接或外延画布", "重新编排人物动作或站位", "增删、合并或复制人物", "交换人物服装", "替换互动事件", "改变已确认的服装、时代或作品世界"],
        }
        reference_relation = "两人姿势互动" if legacy_pair else "所有出镜人物的姿势互动、逐人调度"
        render_prompt = (
            f"摄影关键词：{PHOTOGRAPHY_KEYWORDS}。\n\n"
            f"{item['shot']['prompt']}\n\n"
            f"构图参考要求：随附的 8 宫格/单格派生图只用于 composition/pose continuity，不是人物身份来源。仅将自然视觉阅读顺序中的第 {panel_position} 格（对应 Shot {shot_id}）作为构图视觉锚点；忽略其他格。先理解目标格中的{reference_relation}、相对站位、身体朝向、手部与道具关系、视线方向、人物与环境的空间关系，以及镜头构图意图。人物脸部身份必须直接重新从该 participant 的 active identity reference 恢复；默认仍是最初上传的真人原图，除非用户明确提升了新的身份参考。禁止继承目标格里已经生成的人脸，禁止把八宫格中的脸继续迭代成身份来源。必须保持脸型与长宽比、额头比例、眼型与眼距、眉位、鼻梁/鼻宽/鼻尖结构、颧骨、嘴宽与唇比例、下颌线与下巴、年龄印象与整体辨识度。"
            f"在 {orientation}、画幅比例 {ORIENTATIONS[orientation]['ratio']} 下重新生成一张完整图片，保持上述关系连续性与所有已确认人物、各自服装、时代/作品世界；允许为目标画幅自然重新取景和扩展环境空间。"
            f"不要机械外延画布、不要拼接感、不要重新编排人物动作或站位、不要增删/合并/复制人物、不要交换服装、不要替换互动事件。\n"
            f"细节要求：{supplement}\n"
            "人物发型必须沿用该 Look 已确认的 Editorial 专业发型师设计。原始真人参考图仅锁人脸身份；必须忽略参考图可见的发长、直卷、刘海、分缝、体积、轮廓与发色质感，不得因 identity reference 的视觉内容回退到原图发型。只有用户明确要求保留/恢复原发型时例外。\n"
            "人物妆容与皮肤优化必须沿用该 Look 已确认的 Editorial 专业化妆师设计；不要退化成通用‘自然妆/轻度精修’。"
        )
        brief = {
            "brief_id": Path(filename).stem,
            "status": "pending",
            "board_id": item["board"]["board_id"],
            "shot_id": shot_id,
            "orientation": orientation,
            "aspect_ratio": ORIENTATIONS[orientation]["ratio"],
            "user_detail": detail or None,
            "source_prompt": item["shot"]["prompt"],
            "reference_image": rel(project, anchor),
            "reference_source": anchor_source,
            "reference_usage": "required",
            "composition_reference_image": rel(project, anchor),
            "composition_reference_role": "composition_pose_only",
            "identity_references": [
                {"participant_id": person.get("participant_id"), "references": person.get("identity_references") or [], "source": (person.get("identity_reference_meta") or {}).get("active_reference_source", "original_user_upload")}
                for person in item["board"].get("visual_lock", {}).get("participant_outfits", []) if isinstance(person, dict) and (person.get("identity_references") or [])
            ],
            "preservation_contract": preservation,
            "detail_instruction": supplement,
            "render_prompt": render_prompt,
            "identity_lock_version": 2,
            "identity_reference_semantics": "face_geometry_only; direct reconstruction from active identity reference; composition reference never becomes identity source",
            "output_path": rel(project, output),
            "quality_check": {"status": "pending", "notes": None},
            "created_at": now(),
        }
        brief_path = briefs_dir / filename
        write_yaml(brief_path, brief)
        records.append({"shot_id": shot_id, "orientation": orientation, "brief": rel(project, brief_path), "reference_image": rel(project, anchor), "output": rel(project, output), "status": "pending"})
        board = item["board"]
        board["selected_shot_ids"] = sorted(set(board.get("selected_shot_ids", []) + [shot_id]))
        write_yaml(item["path"], board)
    state["shot_board"]["selected_shot_ids"] = ids
    state["shot_board"]["enlargements"].extend(records)
    write_yaml(state_path, state)
    print("\n".join(record["brief"] for record in records))


def complete(args: argparse.Namespace) -> None:
    project = Path(args.project).resolve()
    state_path, state, _, briefs_dir, _, _ = load_project(project)
    brief_path = (project / args.brief).resolve()
    try:
        brief_path.relative_to(briefs_dir.resolve())
    except ValueError as error:
        raise SystemExit("--brief must refer to a detail brief inside deliverables/shot-detail-briefs") from error
    if not brief_path.exists():
        raise SystemExit(f"missing detail brief: {brief_path}")
    image = Path(args.image).resolve()
    if not image.exists():
        raise SystemExit(f"missing detail image: {image}")
    try:
        image.relative_to(project)
    except ValueError as error:
        raise SystemExit("--image must already be saved inside the project") from error
    brief = read_yaml(brief_path)
    brief["status"] = "passed"
    brief["output_path"] = rel(project, image)
    brief["quality_check"] = {"status": "passed", "notes": args.notes.strip() or None}
    write_yaml(brief_path, brief)
    for record in state["shot_board"].get("enlargements", []):
        if record.get("brief") == rel(project, brief_path):
            record.update({"status": "passed", "output": rel(project, image)})
    write_yaml(state_path, state)
    print(image)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    create_parser = subparsers.add_parser("create", help="allocate eight new shot ids and save a text board")
    create_parser.add_argument("project")
    create_parser.add_argument("--look-id", required=True)
    create_parser.add_argument("--theme", required=True)
    create_parser.add_argument("--shots-file", required=True)
    create_parser.add_argument("--theme-id")
    create_parser.set_defaults(func=create)
    prepare_parser = subparsers.add_parser("prepare-grid", help="compile eight shots into one free-layout single-grid image prompt")
    prepare_parser.add_argument("project")
    prepare_parser.add_argument("board_id")
    prepare_parser.add_argument("--panel-aspect-ratio", help="deprecated and ignored; eight-grid generation no longer specifies panel dimensions")
    prepare_parser.add_argument("--theme-id")
    prepare_parser.set_defaults(func=prepare_grid)
    register_parser = subparsers.add_parser("register-grid", help="register one AI-generated free-layout eight-panel grid image and overlay numeric badges")
    register_parser.add_argument("project")
    register_parser.add_argument("board_id")
    register_parser.add_argument("--image", required=True, help="the one AI-generated free-layout eight-panel grid image")
    register_parser.add_argument("--theme-id")
    register_parser.set_defaults(func=register_grid)
    compose_parser = subparsers.add_parser("compose", help="compose eight portrait cells into a numbered 4x2 board")
    compose_parser.add_argument("project")
    compose_parser.add_argument("board_id")
    compose_parser.add_argument("--cell", action="append", required=True, help="<shot-id>=<image-path>; supply exactly eight")
    compose_parser.add_argument("--theme-id")
    compose_parser.set_defaults(func=compose)
    select_parser = subparsers.add_parser("select", help="write single-image detail briefs for selected shots")
    select_parser.add_argument("project")
    select_parser.add_argument("--ids", required=True)
    select_parser.add_argument("--orientation", choices=sorted(ORIENTATIONS), default="portrait")
    select_parser.add_argument("--detail", default="")
    select_parser.add_argument("--theme-id")
    select_parser.set_defaults(func=select)
    complete_parser = subparsers.add_parser("complete", help="record a visual-QA-passed detail image")
    complete_parser.add_argument("project")
    complete_parser.add_argument("--brief", required=True, help="project-relative path to a detail brief")
    complete_parser.add_argument("--image", required=True, help="existing image path inside the project")
    complete_parser.add_argument("--notes", default="")
    complete_parser.add_argument("--theme-id")
    complete_parser.set_defaults(func=complete)
    args = parser.parse_args()
    root = Path(args.project).resolve()
    workspace, theme_id = resolve_theme(root, args.theme_id)
    args.project = str(workspace)
    args.func(args)
    sync_theme(root, theme_id)


if __name__ == "__main__":
    main()
