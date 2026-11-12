"""Dataset type detection helpers."""

from __future__ import annotations

import csv
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


SURVEY_COLUMN_PATTERN = re.compile(
    r"(\u6ee1\u610f|\u95ee\u5377|\u9898\u76ee|\u8bc4\u5206|\u5206\u503c|\u5efa\u8bae|\u53cd\u9988|likert|score|survey|question|q\d+|\u662f\u5426|\u5e74\u7ea7|\u73ed\u7ea7|\u90e8\u95e8)",
    re.IGNORECASE,
)
TIME_COLUMN_PATTERN = re.compile(
    r"(date|time|year|month|day|week|timestamp|\u65e5\u671f|\u65f6\u95f4|\u5e74\u6708|\u5b63\u5ea6|\u5468|\u65f6\u70b9)",
    re.IGNORECASE,
)
LITERARY_TITLE_PATTERN = re.compile(
    r"(\u7b2c[\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\u5341\u767e\u96f6\u3007\u4e24\d]+\u56de|\u7b2c[\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\u5341\u767e\u96f6\u3007\u4e24\d]+\u7ae0|\u5bf9\u4e0b\u8054|\u4e0a\u8054|\u4e0b\u8054)"
)
POETRY_PATTERN = re.compile(
    r"(\u4e03\u5f8b|\u4e94\u5f8b|\u7edd\u53e5|\u8bcd\u724c|\u6d63\u6eaa\u6c99|\u6c34\u8c03\u6b4c\u5934|\u9e67\u9e2a\u5929|\u8776\u604b\u82b1)"
)
SURVEY_VALUE_MARKERS = (
    "\u6ee1\u610f",
    "\u4e00\u822c",
    "\u4e0d\u540c\u610f",
    "\u540c\u610f",
    "\u975e\u5e38",
    "\u662f",
    "\u5426",
    "\u7537",
    "\u5973",
)
COUPLET_MARKERS = ("\u5bf9\u4e0b\u8054", "\u4e0a\u8054", "\u4e0b\u8054")
SALES_MARKERS = ("\u9500\u91cf", "\u9500\u552e", "price", "amount")


@dataclass(slots=True)
class DetectionResult:
    primary_type: str
    subtype: str | None
    confidence: float
    fallback_type: str
    signals: list[str]
    file_extension: str
    detected_strategy: str


def read_text_sample(data_path: Path, max_characters: int = 4000) -> str:
    raw_bytes = data_path.read_bytes()[: max_characters * 4]
    for encoding in ("utf-8", "gb18030", "gbk", "big5"):
        try:
            return raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    return raw_bytes.decode("utf-8", errors="ignore")


def read_table_sample(data_path: Path, max_rows: int = 30) -> tuple[list[str], list[dict[str, Any]]]:
    if data_path.suffix.lower() != ".csv":
        return [], []
    with data_path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        rows: list[dict[str, Any]] = []
        for row in reader:
            rows.append(dict(row))
            if len(rows) >= max_rows:
                break
    return reader.fieldnames or [], rows


def is_low_cardinality_survey_column(sample_rows: list[dict[str, Any]], column_name: str) -> bool:
    values = {str(row.get(column_name, "")).strip() for row in sample_rows if str(row.get(column_name, "")).strip()}
    if not values:
        return False
    if all(value in {"1", "2", "3", "4", "5", "6", "7"} for value in values):
        return True
    if len(values) <= 7 and any(marker in value for value in values for marker in SURVEY_VALUE_MARKERS):
        return True
    return False


def detect_dataset(data_path: str, task_description: str = "") -> dict[str, Any]:
    path = Path(data_path)
    extension = path.suffix.lower()
    signals: list[str] = []

    if extension in {".txt", ".md", ".jsonl"}:
        text_sample = read_text_sample(path)
        if LITERARY_TITLE_PATTERN.search(text_sample):
            subtype = "novel_or_couplet"
            if any(marker in text_sample for marker in COUPLET_MARKERS):
                subtype = "couplet"
                signals.append("The text contains couplet markers.")
            elif POETRY_PATTERN.search(text_sample):
                subtype = "poetry"
                signals.append("The text contains poetry-form clues.")
            else:
                signals.append("The text contains literary chapter markers.")
            result = DetectionResult(
                primary_type="literary",
                subtype=subtype,
                confidence=0.9,
                fallback_type="unknown",
                signals=signals,
                file_extension=extension,
                detected_strategy="literary",
            )
            return asdict(result)

        result = DetectionResult(
            primary_type="unknown",
            subtype=None,
            confidence=0.45,
            fallback_type="tabular_generic",
            signals=["The text file does not expose clear literary structure cues."],
            file_extension=extension,
            detected_strategy="tabular_generic",
        )
        return asdict(result)

    if extension in {".csv", ".xlsx"}:
        headers, sample_rows = read_table_sample(path)
        survey_match_count = sum(bool(SURVEY_COLUMN_PATTERN.search(header)) for header in headers)
        time_match_columns = [header for header in headers if TIME_COLUMN_PATTERN.search(header)]
        low_cardinality_survey_columns = (
            sum(is_low_cardinality_survey_column(sample_rows, header) for header in headers) if sample_rows else 0
        )
        long_text_column_count = 0
        if sample_rows:
            for header in headers:
                max_length = max((len(str(row.get(header, "")).strip()) for row in sample_rows), default=0)
                if max_length >= 24:
                    long_text_column_count += 1

        if survey_match_count >= 2 or low_cardinality_survey_columns >= max(3, len(headers) // 3):
            signals.extend(
                [
                    f"Matched {survey_match_count} survey-related header columns.",
                    f"Detected {low_cardinality_survey_columns} low-cardinality survey columns in samples.",
                ]
            )
            if long_text_column_count:
                signals.append(f"Detected {long_text_column_count} possible free-text response columns.")
            result = DetectionResult(
                primary_type="questionnaire",
                subtype="mixed_questionnaire" if long_text_column_count else "structured_questionnaire",
                confidence=0.88,
                fallback_type="tabular_generic",
                signals=signals,
                file_extension=extension,
                detected_strategy="questionnaire",
            )
            return asdict(result)

        if time_match_columns:
            signals.append(f"Detected candidate time columns: {time_match_columns}")
            if any(marker in header.lower() or marker in header for header in headers for marker in SALES_MARKERS):
                signals.append("Candidate time columns co-occur with numeric business metric columns.")
            result = DetectionResult(
                primary_type="time_series",
                subtype="tabular_time_series",
                confidence=0.82,
                fallback_type="tabular_generic",
                signals=signals,
                file_extension=extension,
                detected_strategy="time_series",
            )
            return asdict(result)

        signals.append("Detected a standard table file without strong questionnaire or time-series signals.")
        result = DetectionResult(
            primary_type="tabular_generic",
            subtype="generic_spreadsheet",
            confidence=0.72,
            fallback_type="tabular_generic",
            signals=signals,
            file_extension=extension,
            detected_strategy="tabular_generic",
        )
        return asdict(result)

    result = DetectionResult(
        primary_type="unknown",
        subtype=None,
        confidence=0.3,
        fallback_type="tabular_generic",
        signals=[f"Unsupported extension encountered: {extension or 'no_extension'}"],
        file_extension=extension,
        detected_strategy="tabular_generic",
    )
    return asdict(result)
