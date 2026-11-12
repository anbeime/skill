"""Dataset profiling helpers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any


TARGET_MARKERS = ("target", "label", "\u76ee\u6807")
CLUSTER_MARKERS = ("cluster", "\u805a\u7c7b")
DIMENSION_REDUCTION_MARKERS = ("dimension reduction", "\u964d\u7ef4")


@dataclass(slots=True)
class FieldSummary:
    field_name: str
    inferred_type: str
    missing_rate: float
    is_candidate_target: bool = False
    is_candidate_group: bool = False
    is_candidate_time: bool = False
    is_high_cardinality: bool = False


def is_missing_value(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str) and value.strip() == "":
        return True
    return False


def infer_type(sample_values: list[Any]) -> str:
    valid_values = [value for value in sample_values if not is_missing_value(value)]
    if not valid_values:
        return "unknown"

    if all(isinstance(value, bool) for value in valid_values):
        return "boolean"

    if all(isinstance(value, (int, float)) and not isinstance(value, bool) for value in valid_values):
        return "numeric"

    normalized_values = [str(value).strip() for value in valid_values]
    if all(text.lower() in {"true", "false", "yes", "no", "0", "1"} for text in normalized_values):
        return "boolean"

    numeric_parse_count = 0
    datetime_parse_count = 0
    for text in normalized_values:
        try:
            float(text)
            numeric_parse_count += 1
        except ValueError:
            pass
        for date_format in ("%Y-%m-%d", "%Y/%m/%d", "%Y-%m", "%Y/%m", "%d/%m/%Y"):
            try:
                datetime.strptime(text, date_format)
                datetime_parse_count += 1
                break
            except ValueError:
                continue

    if numeric_parse_count == len(normalized_values):
        return "numeric"
    if datetime_parse_count >= max(1, len(normalized_values) // 2):
        return "datetime"
    if len(set(normalized_values)) <= max(12, len(normalized_values) // 3):
        return "categorical"
    return "text"


def build_data_profile(
    sample_rows: list[dict[str, Any]] | None = None,
    task_description: str = "",
) -> dict[str, Any]:
    sample_rows = sample_rows or []
    if not sample_rows:
        return {
            "schema": [],
            "data_profile": {
                "row_count": 0,
                "column_count": 0,
                "field_summaries": [],
                "missing_rate_overview": {},
                "constant_columns": [],
                "high_missing_fields": [],
                "analysis_opportunities": [],
            },
        }

    field_names = list(sample_rows[0].keys())
    row_count = len(sample_rows)
    schema: list[dict[str, Any]] = []
    constant_columns: list[str] = []
    high_missing_fields: list[str] = []

    for field_name in field_names:
        column_values = [row.get(field_name) for row in sample_rows]
        missing_count = sum(1 for value in column_values if is_missing_value(value))
        non_missing_values = [value for value in column_values if not is_missing_value(value)]
        inferred_type = infer_type(column_values)
        unique_value_count = len({str(value) for value in non_missing_values})
        lower_field_name = field_name.lower()

        if non_missing_values and unique_value_count == 1:
            constant_columns.append(field_name)
        if row_count and missing_count / row_count >= 0.3:
            high_missing_fields.append(field_name)

        summary = FieldSummary(
            field_name=field_name,
            inferred_type=inferred_type,
            missing_rate=round(missing_count / row_count, 4) if row_count else 0.0,
            is_candidate_target=any(marker in lower_field_name or marker in field_name for marker in TARGET_MARKERS),
            is_candidate_group=inferred_type == "categorical",
            is_candidate_time=inferred_type == "datetime",
            is_high_cardinality=inferred_type == "categorical" and unique_value_count >= max(20, row_count // 5),
        )
        schema.append(asdict(summary))

    analysis_opportunities: list[str] = []
    if any(field["inferred_type"] == "datetime" for field in schema):
        analysis_opportunities.append("Trend analysis is available.")
    if sum(field["inferred_type"] == "numeric" for field in schema) >= 2:
        analysis_opportunities.append("Correlation analysis is available.")
    if any(marker in task_description.lower() for marker in CLUSTER_MARKERS) or any(
        marker in task_description.lower() or marker in task_description
        for marker in DIMENSION_REDUCTION_MARKERS
    ):
        analysis_opportunities.append("The task explicitly requests clustering or dimensionality reduction.")

    return {
        "schema": schema,
        "data_profile": {
            "row_count": row_count,
            "column_count": len(field_names),
            "field_summaries": schema,
            "missing_rate_overview": {field["field_name"]: field["missing_rate"] for field in schema},
            "constant_columns": constant_columns,
            "high_missing_fields": high_missing_fields,
            "analysis_opportunities": analysis_opportunities,
        },
    }
