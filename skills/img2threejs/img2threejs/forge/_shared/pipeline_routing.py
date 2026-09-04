"""Fail-closed routing for the weapon and character authoring tracks."""

from __future__ import annotations

from typing import Any, Final


CONFIDENCE_THRESHOLD: Final[float] = 0.82
TRACK_BY_KIND: Final[dict[str, str]] = {
    "weapon": "weapon-v1.4",
    "character": "character-v1.5",
}
VALID_TRACKS: Final[frozenset[str]] = frozenset(TRACK_BY_KIND.values())
VALID_KINDS: Final[frozenset[str]] = frozenset({"weapon", "character", "hybrid", "unknown"})
VALID_SOURCES: Final[frozenset[str]] = frozenset({"explicit", "classification", "legacy"})
VALID_STATUSES: Final[frozenset[str]] = frozenset({"resolved", "request-input"})


def _fallback_classification(reason: str) -> dict[str, Any]:
    return {
        "kind": "unknown",
        "confidence": 0.0,
        "evidenceRefs": [f"pipeline-routing:{reason}"],
        "provider": "pipeline-routing",
        "version": "1",
    }


def _explicit_classification(track: str) -> dict[str, Any]:
    kind = "weapon" if track == "weapon-v1.4" else "character"
    return {
        "kind": kind,
        "confidence": 1.0,
        "evidenceRefs": [f"pipeline-routing:explicit:{track}"],
        "provider": "pipeline-routing-cli",
        "version": "1",
    }


def _normalize_classification(classification: Any) -> tuple[dict[str, Any], list[str]]:
    if classification is None:
        return _fallback_classification("missing-classification"), []
    if not isinstance(classification, dict):
        return _fallback_classification("malformed-classification"), ["classification is malformed"]
    kind = classification.get("kind")
    confidence = classification.get("confidence")
    refs = classification.get("evidenceRefs")
    provider = classification.get("provider")
    version = classification.get("version")
    malformed = (
        kind not in VALID_KINDS
        or not isinstance(confidence, (int, float))
        or isinstance(confidence, bool)
        or not 0.0 <= confidence <= 1.0
        or not isinstance(refs, list)
        or not refs
        or not all(isinstance(ref, str) and ref for ref in refs)
        or not isinstance(provider, str)
        or not provider
        or not isinstance(version, str)
        or not version
    )
    if malformed:
        return _fallback_classification("malformed-classification"), ["classification is malformed"]
    return {
        "kind": kind,
        "confidence": float(confidence),
        "evidenceRefs": list(refs),
        "provider": provider,
        "version": version,
    }, []


def classification_from_cs2_manifest(manifest: dict[str, Any]) -> dict[str, Any]:
    """Translate the CS2 authoritative record into the shared routing classification."""
    record = manifest.get("classification")
    if not isinstance(record, dict):
        return _fallback_classification("cs2-manifest-missing-classification")
    return {
        "kind": "weapon",
        "confidence": record.get("confidence"),
        "evidenceRefs": record.get("evidenceRefs"),
        "provider": record.get("provider"),
        "version": record.get("version"),
    }


def resolve_pipeline_routing(
    *,
    explicit_track: str | None = None,
    classification: Any = None,
    legacy_cs2: bool = False,
) -> dict[str, Any]:
    """Resolve one supported track or return request-input without guessing a template."""
    if legacy_cs2:
        resolved_classification = {
            "kind": "weapon",
            "confidence": 1.0,
            "evidenceRefs": ["legacy:cs2Intake"],
            "provider": "legacy-cs2-intake",
            "version": "1",
        }
        if explicit_track is not None and explicit_track != "weapon-v1.4":
            return {
                "version": 1,
                "track": explicit_track,
                "source": "explicit",
                "status": "request-input",
                "classification": resolved_classification,
                "conflicts": [
                    f"explicit track {explicit_track!r} contradicts legacy CS2 weapon routing"
                ],
            }
        return {
            "version": 1,
            "track": "weapon-v1.4",
            "source": "legacy",
            "status": "resolved",
            "classification": resolved_classification,
            "conflicts": [],
        }

    normalized, conflicts = _normalize_classification(classification)
    if explicit_track is not None and explicit_track not in VALID_TRACKS:
        conflicts.append("explicit track is invalid")
        explicit_track = None
    if explicit_track is not None and classification is None:
        normalized = _explicit_classification(explicit_track)

    kind = normalized["kind"]
    confidence = normalized["confidence"]
    reliable_kind = kind in TRACK_BY_KIND and confidence >= CONFIDENCE_THRESHOLD
    requested_track = explicit_track or TRACK_BY_KIND.get(kind, "weapon-v1.4")
    if kind in {"hybrid", "unknown"}:
        conflicts.append(f"classification kind {kind!r} requires input")
    elif confidence < CONFIDENCE_THRESHOLD:
        conflicts.append(f"classification confidence {confidence:.2f} is below {CONFIDENCE_THRESHOLD:.2f}")
    elif explicit_track is not None and reliable_kind and TRACK_BY_KIND[kind] != explicit_track:
        conflicts.append(f"explicit track {explicit_track!r} contradicts reliable classification {kind!r}")

    status = "resolved" if reliable_kind and not conflicts else "request-input"
    source = "explicit" if explicit_track is not None else "classification"
    return {
        "version": 1,
        "track": requested_track,
        "source": source,
        "status": status,
        "classification": normalized,
        "conflicts": conflicts,
    }


def validate_pipeline_routing(routing: Any) -> list[str]:
    """Return contract errors for a persisted routing record."""
    if not isinstance(routing, dict):
        return ["pipelineRouting must be an object"]
    errors: list[str] = []
    if routing.get("version") != 1:
        errors.append("pipelineRouting.version must be 1")
    if routing.get("track") not in VALID_TRACKS:
        errors.append("pipelineRouting.track must be weapon-v1.4 or character-v1.5")
    if routing.get("source") not in VALID_SOURCES:
        errors.append("pipelineRouting.source must be explicit, classification, or legacy")
    if routing.get("status") not in VALID_STATUSES:
        errors.append("pipelineRouting.status must be resolved or request-input")
    classification = routing.get("classification")
    normalized, classification_errors = _normalize_classification(classification)
    if classification_errors:
        errors.append("pipelineRouting.classification is malformed")
    if not isinstance(classification, dict) or classification != normalized:
        errors.append("pipelineRouting.classification must use the shared classification contract")
    conflicts = routing.get("conflicts")
    if not isinstance(conflicts, list) or not all(isinstance(conflict, str) for conflict in conflicts):
        errors.append("pipelineRouting.conflicts must be a list")
    elif routing.get("status") == "resolved" and conflicts:
        errors.append("resolved pipelineRouting cannot contain conflicts")
    return errors
