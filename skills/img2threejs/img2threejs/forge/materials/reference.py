#!/usr/bin/env python3
"""Load and resolve the canonical Three.js material reference library.

This is the runtime bridge for ``docs/materials/material-reference.json``.  The
registry is intentionally data-driven: profile numbers seed a candidate, while
image evidence and user metadata decide whether that candidate may proceed.
The module is stdlib-only so it can be used by every forge stage and in CI.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REFERENCE = ROOT / "docs" / "materials" / "material-reference.json"


class MaterialReferenceError(ValueError):
    """Raised when the canonical registry cannot safely be consumed."""


def _token(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", " ", str(value or "").strip().lower()).strip()


def _tokens(value: Any) -> set[str]:
    token = _token(value)
    return {token, token.replace(" ", "-")} if token else set()


def validate_reference(payload: dict[str, Any]) -> list[str]:
    """Return structural errors; an empty list means the registry is usable."""
    errors: list[str] = []
    if not isinstance(payload, dict):
        return ["reference must be a JSON object"]
    if payload.get("schemaVersion") != 1:
        errors.append("schemaVersion must be 1")
    renderer = payload.get("renderer")
    if not isinstance(renderer, dict) or renderer.get("engine") != "three.js":
        errors.append("renderer.engine must be three.js")
    sources = payload.get("sources")
    if not isinstance(sources, list) or not sources:
        errors.append("sources must be a non-empty array")
        source_ids: set[str] = set()
    else:
        source_ids = set()
        for index, source in enumerate(sources):
            if not isinstance(source, dict):
                errors.append(f"sources[{index}] must be an object")
                continue
            source_id = source.get("id")
            if not isinstance(source_id, str) or not source_id:
                errors.append(f"sources[{index}].id is required")
            elif source_id in source_ids:
                errors.append(f"duplicate source id {source_id!r}")
            source_ids.add(str(source_id))
            if not isinstance(source.get("url"), str) or not source["url"].startswith("https://"):
                errors.append(f"source {source_id!r} must have an https URL")
    materials = payload.get("materials")
    if not isinstance(materials, list) or not materials:
        errors.append("materials must be a non-empty array")
        materials = []
    ids: set[str] = set()
    legal = payload.get("legalRanges", {})
    if not isinstance(legal, dict):
        errors.append("legalRanges must be an object")
        legal = {}
    for index, material in enumerate(materials):
        if not isinstance(material, dict):
            errors.append(f"materials[{index}] must be an object")
            continue
        material_id = material.get("id")
        if not isinstance(material_id, str) or not material_id:
            errors.append(f"materials[{index}].id is required")
            continue
        if material_id in ids:
            errors.append(f"duplicate material id {material_id!r}")
        ids.add(material_id)
        if material.get("recipeBasis") != "inferred-starting-prior":
            errors.append(f"material {material_id!r} must label its recipeBasis as a prior")
        for source_ref in material.get("sourceRefs", []):
            if source_ref not in source_ids:
                errors.append(f"material {material_id!r} has unresolved sourceRef {source_ref!r}")
        render_prior = material.get("renderPrior", {})
        if not isinstance(render_prior, dict):
            errors.append(f"material {material_id!r}.renderPrior must be an object")
            continue
        for property_name, prior in render_prior.items():
            if property_name not in legal:
                errors.append(f"material {material_id!r} uses undocumented property {property_name!r}")
                continue
            if not isinstance(prior, dict) or not isinstance(prior.get("default"), (int, float)):
                errors.append(f"material {material_id!r}.{property_name} prior is malformed")
                continue
            bounds = prior.get("range")
            allowed = legal[property_name]
            if not isinstance(bounds, list) or len(bounds) != 2 or not isinstance(allowed, list) or len(allowed) != 2:
                errors.append(f"material {material_id!r}.{property_name} prior range is malformed")
                continue
            if bounds[0] > prior["default"] or prior["default"] > bounds[1] or bounds[0] < allowed[0] or bounds[1] > allowed[1]:
                errors.append(f"material {material_id!r}.{property_name} prior escapes legal range")
    return errors


def load_reference(path: Path | str = DEFAULT_REFERENCE) -> dict[str, Any]:
    reference_path = Path(path)
    try:
        payload = json.loads(reference_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MaterialReferenceError(f"cannot load material reference {reference_path}: {exc}") from exc
    errors = validate_reference(payload)
    if errors:
        raise MaterialReferenceError("invalid material reference: " + "; ".join(errors))
    return payload


def _material_index(payload: dict[str, Any]) -> list[dict[str, Any]]:
    return [item for item in payload.get("materials", []) if isinstance(item, dict)]


def _candidate(profile: dict[str, Any], method: str, confidence: float, reason: str) -> dict[str, Any]:
    return {
        "materialId": profile.get("id"),
        "profile": profile,
        "method": method,
        "confidence": max(0.0, min(1.0, float(confidence))),
        "reason": reason,
    }


def resolve_material(hypothesis: dict[str, Any], payload: dict[str, Any] | None = None) -> dict[str, Any]:
    """Resolve one hypothesis while retaining alternatives and uncertainty.

    Explicit user/metadata identity wins.  Alias and family matching never
    silently chooses between materially different candidates.
    """
    registry = payload or load_reference()
    materials = _material_index(registry)
    by_id = {str(item.get("id")): item for item in materials}
    explicit = hypothesis.get("materialId")
    if isinstance(explicit, str) and explicit in by_id:
        result = _candidate(by_id[explicit], "explicit-material-id", 1.0, "authoritative material id")
        result["status"] = "proceed"
        result["alternatives"] = []
        return result

    family = _token(hypothesis.get("family"))
    subtype = _token(hypothesis.get("subtype"))
    finish = _token(hypothesis.get("finish"))
    exact = [
        item for item in materials
        if _token(item.get("family")) == family
        and (not subtype or _token(item.get("subtype")) == subtype)
        and (not finish or _token(item.get("finish")) == finish)
    ]
    if len(exact) == 1:
        result = _candidate(exact[0], "family-subtype-finish", float(hypothesis.get("confidence", 0.7)), "exact semantic match")
        result["status"] = "proceed" if result["confidence"] >= 0.7 else "probe"
        result["alternatives"] = []
        return result

    aliases = set()
    for field in ("aliases", "alternatives"):
        value = hypothesis.get(field, [])
        if isinstance(value, list):
            for item in value:
                aliases.update(_tokens(item.get("materialId") if isinstance(item, dict) else item))
    alias_matches = [item for item in materials if aliases & set().union(*(_tokens(alias) for alias in item.get("aliases", [])))]
    if len(alias_matches) == 1:
        result = _candidate(alias_matches[0], "alias", float(hypothesis.get("confidence", 0.5)), "unique alias match")
        result["status"] = "proceed" if result["confidence"] >= 0.7 else "probe"
        result["alternatives"] = []
        return result

    family_matches = [item for item in materials if family and _token(item.get("family")) == family]
    family_matches.sort(key=lambda item: str(item.get("id")))
    alternatives = [
        _candidate(item, "family-fallback", max(0.1, float(hypothesis.get("confidence", 0.3)) * 0.65), "family fallback")
        for item in family_matches
    ]
    if len(family_matches) == 1:
        result = alternatives[0]
        result["status"] = "probe"
        result["alternatives"] = []
        return result
    return {
        "materialId": None,
        "profile": None,
        "method": "unresolved",
        "confidence": 0.0,
        "reason": "ambiguous or unknown material; request more evidence",
        "status": "request-input" if family_matches else "unknown",
        "alternatives": alternatives,
    }


def _prior_values(profile: dict[str, Any]) -> dict[str, float]:
    return {
        name: float(value["default"])
        for name, value in profile.get("renderPrior", {}).items()
        if isinstance(value, dict) and isinstance(value.get("default"), (int, float))
    }


def build_assignment(
    hypothesis: dict[str, Any],
    evidence: dict[str, Any] | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the spec-ready assignment without mutating the input hypothesis."""
    result = resolve_material(hypothesis, payload)
    profile = result.get("profile")
    assignment: dict[str, Any] = {
        "materialId": result.get("materialId"),
        "status": result["status"],
        "source": hypothesis.get("source", "vision"),
        "confidence": result["confidence"],
        "method": result["method"],
        "alternatives": [item["materialId"] for item in result.get("alternatives", [])],
        "evidence": copy.deepcopy(evidence or {}),
    }
    if profile:
        assignment.update({
            "profileId": profile["id"],
            "family": profile.get("family"),
            "subtype": profile.get("subtype"),
            "finish": profile.get("finish"),
            "renderPrior": _prior_values(profile),
            "requiredMaps": list(profile.get("requiredMaps", [])),
            "optionalMaps": list(profile.get("optionalMaps", [])),
            "validationViews": list(profile.get("validationViews", [])),
            "sourceRefs": list(profile.get("sourceRefs", [])),
            "visualCues": list(profile.get("visualCues", [])),
        })
    return assignment
