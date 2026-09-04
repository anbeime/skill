from __future__ import annotations

from copy import deepcopy
from collections.abc import Callable, Mapping, Sequence


def _approval_state(
    result: Mapping[str, object],
    input_error: Callable[[str, str], ValueError],
    field: str,
) -> tuple[list[str], str | None, str | None, bool]:
    hard_gates = result.get("hardGateFailures", [])
    if not isinstance(hard_gates, list) or not all(isinstance(tag, str) for tag in hard_gates):
        raise input_error(f"{field}.hardGateFailures", "must be a list of strings")
    action = result.get("action")
    verdict = result.get("verdict")
    if action is not None and not isinstance(action, str):
        raise input_error(f"{field}.action", "must be a string")
    if verdict is not None and not isinstance(verdict, str):
        raise input_error(f"{field}.verdict", "must be a string")
    approved = not hard_gates and action in (None, "continue") and verdict in (None, "pass")
    return hard_gates, action, verdict, approved


def is_approved_divine_eye_result(
    result: Mapping[str, object],
    input_error: Callable[[str, str], ValueError],
    field: str,
) -> bool:
    return _approval_state(result, input_error, field)[3]


def normalize_history(
    results: Sequence[Mapping[str, object]],
    fidelity: Callable[[Mapping[str, object]], float],
    input_error: Callable[[str, str], ValueError],
) -> list[dict[str, object]]:
    if isinstance(results, str | bytes) or not isinstance(results, Sequence):
        raise input_error("results", "must be a sequence of mappings")
    history: list[dict[str, object]] = []
    accepted_fidelity: float | None = None
    for index, result in enumerate(results):
        if not isinstance(result, Mapping):
            raise input_error(f"results[{index}]", "must be a mapping")
        score = fidelity(result)
        hard_gates, action, verdict, approved = _approval_state(result, input_error, f"results[{index}]")
        pending_review = not approved
        reverted = accepted_fidelity is not None and score < accepted_fidelity
        entry = {
            "fidelity": score,
            "defectTags": hard_gates.copy(),
            "hardGateFailures": hard_gates.copy(),
            "reverted": reverted,
            "pendingReview": pending_review,
            "divineEye": deepcopy(dict(result)),
        }
        if action is not None:
            entry["divineEyeAction"] = action
        if verdict is not None:
            entry["divineEyeVerdict"] = verdict
        history.append(entry)
        if approved and (accepted_fidelity is None or score > accepted_fidelity):
            accepted_fidelity = score
    return history
