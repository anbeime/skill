"""Preprocessing recommendation helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class PreprocessingAction:
    action_name: str
    target_fields: list[str]
    reason: str
    result: str


def build_preprocessing_log(
    should_run: bool,
    actions: list[PreprocessingAction] | None = None,
    raw_snapshot_path: str = "",
    processed_snapshot_path: str = "",
) -> dict[str, Any]:
    return {
        "should_run_preprocessing": should_run,
        "raw_snapshot_path": raw_snapshot_path,
        "processed_snapshot_path": processed_snapshot_path,
        "actions": [asdict(action) for action in (actions or [])],
    }


def generate_preprocessing_recommendations(
    data_profile: dict[str, Any],
    preprocessing_preference: str,
) -> list[PreprocessingAction]:
    actions: list[PreprocessingAction] = []
    if preprocessing_preference == "no preprocessing":
        return actions

    high_missing_fields = data_profile.get("data_profile", {}).get("high_missing_fields", [])
    if high_missing_fields:
        actions.append(
            PreprocessingAction(
                action_name="Review missing-value treatment",
                target_fields=list(high_missing_fields),
                reason="High-missing fields may distort statistics and figures.",
                result="Wait for user confirmation before dropping or imputing values.",
            )
        )

    constant_columns = data_profile.get("data_profile", {}).get("constant_columns", [])
    if constant_columns:
        actions.append(
            PreprocessingAction(
                action_name="Remove constant columns",
                target_fields=list(constant_columns),
                reason="Constant columns do not provide useful analytical signal.",
                result="Recommended for removal.",
            )
        )

    return actions
