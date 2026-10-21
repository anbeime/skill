"""Shared utilities for the doctor agent."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any, Dict, List, Optional

from .terminology import best_match

BASE_DIR = Path(__file__).resolve().parents[1]
REF_DATA_DIR = BASE_DIR / "data" / "ref_data"


def build_name_map(names: Iterable[str]) -> Dict[str, str]:
    result = {}
    for name in names:
        normalized = normalize_name(name)
        if normalized and normalized not in result:
            result[normalized] = name
    return result


def load_examination_catalog() -> Dict[str, List[str]]:
    data = json.loads((REF_DATA_DIR / "examinations_catalog.json").read_text(encoding="utf-8"))
    catalog: Dict[str, List[str]] = {}
    for category, items in data.get("examinations", {}).items():
        names = []
        for item in items if isinstance(items, list) else []:
            name = item.get("name") if isinstance(item, dict) else item
            if str(name or "").strip():
                names.append(str(name).strip())
        if names:
            catalog[str(category)] = names
    return catalog


def load_disease_catalog() -> Dict[str, List[str]]:
    data = json.loads((REF_DATA_DIR / "diseases_catalog.json").read_text(encoding="utf-8"))
    catalog: Dict[str, List[str]] = {}
    for department, names in data.get("diseases", {}).items():
        clean_names = [str(name).strip() for name in names if str(name).strip()]
        if clean_names:
            catalog[str(department)] = clean_names
    return catalog


def match_standard_name(value: Any, name_map: Dict[str, str]) -> str:
    text = clean_text(value)
    if not text:
        return ""
    return name_map.get(normalize_name(text), "")


def match_standard_or_contained_name(value: Any, name_map: Dict[str, str]) -> str:
    direct_match = match_standard_name(value, name_map)
    if direct_match:
        return direct_match
    normalized = normalize_name(value)
    if not normalized:
        return ""
    for standard_normalized, standard_name in name_map.items():
        if standard_normalized and (
            standard_normalized in normalized
            or (len(normalized) >= 3 and normalized in standard_normalized)
        ):
            return standard_name
    fuzzy = best_match(value, name_map.values(), score_cutoff=0.84)
    return fuzzy


def as_text_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, dict):
        value = value.values()
    if not isinstance(value, Iterable):
        return [str(value).strip()] if str(value).strip() else []
    items = []
    for item in value:
        text = str(item).strip()
        if text:
            items.append(text)
    return items


def resolve_ordered_examination_items(
    exam_response: Dict[str, Any],
    requested: List[str],
) -> List[str]:
    """Resolve successfully ordered exam names from an SDK response."""
    ordered = as_text_list(exam_response.get("normalized_items"))
    if ordered:
        return ordered

    results = exam_response.get("results")
    if isinstance(results, dict) and results:
        return [name for name in requested if name in results]

    return list(requested)


def unique_preserve_order(values: Iterable[str]) -> List[str]:
    seen = set()
    result = []
    for value in as_text_list(values):
        if value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def parse_json_object(raw: Any) -> Optional[Dict[str, Any]]:
    text = str(raw or "").strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            text = "\n".join(lines[1:-1]).strip()
        else:
            text = text.strip("`").strip()

    candidates = [text]
    match = re.search(r"\{.*\}", text, flags=re.S)
    if match:
        candidates.append(match.group(0))
    for candidate in unique_preserve_order(candidates):
        try:
            parsed = json.loads(candidate)
        except Exception:
            repaired = _repair_mismatched_json_closers(candidate)
            if repaired == candidate:
                continue
            try:
                parsed = json.loads(repaired)
            except Exception:
                continue
        if isinstance(parsed, dict):
            return parsed
    return None


def _repair_mismatched_json_closers(text: str) -> str:
    """Drop an isolated wrong closer without rewriting JSON values.

    Long model responses occasionally emit ``],`` after a scalar object field.
    The surrounding object is otherwise valid, so sending the entire response
    through another model is both slower and less reliable than this bounded
    structural repair.
    """
    output: List[str] = []
    stack: List[str] = []
    in_string = False
    escaped = False
    changed = False
    pairs = {"}": "{", "]": "["}

    for char in text:
        if in_string:
            output.append(char)
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue
        if char == '"':
            in_string = True
            output.append(char)
        elif char in "{[":
            stack.append(char)
            output.append(char)
        elif char in "}]":
            if stack and stack[-1] == pairs[char]:
                stack.pop()
                output.append(char)
            else:
                changed = True
        else:
            output.append(char)

    return "".join(output) if changed else text


def normalize_name(value: Any) -> str:
    text = str(value or "").lower()
    return re.sub(r"[\s\-_/，,。.;；:：、（）()\[\]【】]+", "", text)


def clean_text(value: Any) -> str:
    return str(value or "").strip()


def build_disease_department_map(disease_catalog: Dict[str, List[str]]) -> Dict[str, str]:
    result = {}
    for department, diseases in disease_catalog.items():
        for disease in diseases:
            normalized = normalize_name(disease)
            if normalized and normalized not in result:
                result[normalized] = department
    return result


def build_global_disease_map(disease_catalog: Dict[str, List[str]]) -> Dict[str, str]:
    all_diseases: List[str] = []
    for diseases in disease_catalog.values():
        all_diseases.extend(diseases)
    return build_name_map(all_diseases)


def case_context_fingerprint(chat_history: List[Any], examinations: Dict[str, Any]) -> str:
    payload = {
        "chat_history": chat_history,
        "ordered_examinations": examinations.get("ordered_examinations", []),
        "examination_results": examinations.get("examination_results", []),
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)
