"""Strategy registry for dataset analysis."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class StrategyDefinition:
    strategy_id: str
    display_name: str
    supported_types: list[str]
    core_tasks: list[str]
    recommended_artifacts: list[str]
    risk_notes: list[str]


STRATEGY_REGISTRY: dict[str, StrategyDefinition] = {
    "tabular_generic": StrategyDefinition(
        strategy_id="tabular_generic",
        display_name="Generic tabular analysis",
        supported_types=["tabular_generic", "unknown"],
        core_tasks=["schema/profile", "missing and duplicate checks", "distribution analysis", "group comparison", "correlation analysis"],
        recommended_artifacts=["schema.json", "data_profile.json", "visualization_plan.json", "analysis_findings.json"],
        risk_notes=["Do not invent business semantics when field meaning is unclear."],
    ),
    "questionnaire": StrategyDefinition(
        strategy_id="questionnaire",
        display_name="Questionnaire analysis",
        supported_types=["questionnaire"],
        core_tasks=["question-type identification", "scale normalization", "invalid response detection", "group comparison", "open-response analysis"],
        recommended_artifacts=[
            "questionnaire_profile.json",
            "questionnaire_scoring.json",
            "group_comparison.csv",
            "open_response_keywords.csv",
        ],
        risk_notes=["Confirm reverse-coded items, dimension grouping, and scale direction before execution."],
    ),
    "literary": StrategyDefinition(
        strategy_id="literary",
        display_name="Literary corpus analysis",
        supported_types=["literary"],
        core_tasks=["genre refinement", "token statistics", "character and imagery analysis", "structural pattern mining", "corpus limitation summary"],
        recommended_artifacts=[
            "character_frequency.csv",
            "imagery_frequency.csv",
            "character_cooccurrence.csv",
            "analysis_findings.json",
        ],
        risk_notes=["Do not present rule-based extraction outputs as human-annotated ground truth."],
    ),
    "time_series": StrategyDefinition(
        strategy_id="time_series",
        display_name="Time-series analysis",
        supported_types=["time_series"],
        core_tasks=["time index identification", "frequency checks", "trend analysis", "anomaly detection", "rolling metrics and seasonality review"],
        recommended_artifacts=[
            "time_series_profile.json",
            "time_series_summary.csv",
            "time_series_trend.png",
            "rolling_summary.csv",
        ],
        risk_notes=["Confirm time columns, frequency, and aggregation granularity before execution."],
    ),
}


def select_strategy(detection_result: dict[str, Any]) -> dict[str, Any]:
    dataset_type = detection_result.get("primary_type", "unknown")
    strategy_name = detection_result.get("detected_strategy", "tabular_generic")
    if strategy_name not in STRATEGY_REGISTRY:
        strategy_name = "tabular_generic"

    strategy = STRATEGY_REGISTRY[strategy_name]
    if dataset_type not in strategy.supported_types and dataset_type != "unknown":
        fallback_name = detection_result.get("fallback_type", "tabular_generic")
        strategy = STRATEGY_REGISTRY.get(fallback_name, STRATEGY_REGISTRY["tabular_generic"])

    return asdict(strategy)
