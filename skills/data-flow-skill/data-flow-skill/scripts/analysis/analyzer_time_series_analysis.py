"""Time-series profiling helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from statistics import mean
from typing import Any


@dataclass(slots=True)
class TimeSeriesSummary:
    time_field: str
    metric_field: str
    sample_size: int
    earliest_time: str | None
    latest_time: str | None
    gap_count: int
    candidate_frequency: str
    is_univariate: bool


def build_time_series_profile(
    time_field: str,
    metric_field: str,
    time_values: list[str],
    metric_values: list[float | int],
) -> dict[str, Any]:
    non_empty_time_values = [str(value) for value in time_values if value not in (None, "")]
    non_empty_metric_values = [float(value) for value in metric_values if value not in (None, "")]
    sample_size = min(len(non_empty_time_values), len(non_empty_metric_values))

    summary = TimeSeriesSummary(
        time_field=time_field,
        metric_field=metric_field,
        sample_size=sample_size,
        earliest_time=min(non_empty_time_values) if non_empty_time_values else None,
        latest_time=max(non_empty_time_values) if non_empty_time_values else None,
        gap_count=max(len(time_values) - len(non_empty_time_values), 0),
        candidate_frequency="unknown",
        is_univariate=True,
    )

    return {
        "time_series_profile": asdict(summary),
        "summary_statistics": {
            "mean": round(mean(non_empty_metric_values), 4) if non_empty_metric_values else None,
            "minimum": min(non_empty_metric_values) if non_empty_metric_values else None,
            "maximum": max(non_empty_metric_values) if non_empty_metric_values else None,
        },
        "recommended_checks": [
            "Check whether the time index is continuous.",
            "Check whether daily, weekly, or monthly aggregation is needed.",
            "Check anomaly spikes and missing intervals.",
            "Add rolling, period-over-period, or seasonal views when appropriate.",
        ],
    }
