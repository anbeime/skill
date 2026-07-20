"""Statistical summary helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class NumericSummary:
    field_name: str
    sample_size: int
    minimum: float | None
    maximum: float | None
    mean_value: float | None
    median_value: float | None


@dataclass(slots=True)
class CategoricalSummary:
    field_name: str
    unique_value_count: int
    most_frequent_category: str | None
    most_frequent_count: int


def generate_statistical_summary(
    numeric_fields: list[NumericSummary] | None = None,
    categorical_fields: list[CategoricalSummary] | None = None,
    notes: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "numeric_summary": [asdict(field) for field in (numeric_fields or [])],
        "categorical_summary": [asdict(field) for field in (categorical_fields or [])],
        "notes": notes or [],
    }
