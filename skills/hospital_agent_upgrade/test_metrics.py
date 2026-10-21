"""Build per-case timing and LLM call metrics from a test output directory."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


PROMPT_NAME_RE = re.compile(r"^prompt_name:\s*(.+)$", re.MULTILINE)
PATIENT_ID_RE = re.compile(r"^patient_id:\s*(.+)$", re.MULTILINE)
PROMPT_RECORD_SEPARATOR = "\n" + ("=" * 80) + "\n"


def build_test_metrics(output_dir: Path) -> Dict[str, Any]:
    """Return run-level and per-patient metrics for one test output directory."""
    output_dir = Path(output_dir)
    events = _read_jsonl(output_dir / "events.jsonl")
    final_results = _read_jsonl(output_dir / "final_results.jsonl")
    final_by_patient = {
        str(row.get("patient_id")): row
        for row in final_results
        if isinstance(row, dict) and row.get("patient_id")
    }
    prompt_metrics = _read_prompt_metrics(output_dir / "llm_prompts")

    case_rows: List[Dict[str, Any]] = []
    for start_event in (event for event in events if event.get("event_type") == "CASE_START"):
        patient_id = str(start_event.get("patient_id") or "")
        end_event = _first_case_end(events, patient_id, start_event)
        patient_events = _events_between(events, start_event, end_event, patient_id)
        event_counts = Counter(str(event.get("event_type") or "") for event in patient_events)
        final_result = final_by_patient.get(patient_id, {})
        metrics_event = next(
            (
                event
                for event in patient_events
                if event.get("event_type") == "CASE_METRICS"
                and isinstance(event.get("payload"), dict)
            ),
            None,
        )
        metrics_payload = (metrics_event or {}).get("payload") or {}
        prompt_call_counts = prompt_metrics.get(patient_id, {})

        duration_seconds = _duration_seconds(
            start_event.get("timestamp"),
            end_event.get("timestamp") if end_event else None,
        )
        embedded_llm_calls = metrics_payload.get("llm_calls", final_result.get("llm_calls"))
        llm_calls = (
            int(embedded_llm_calls)
            if isinstance(embedded_llm_calls, (int, float)) and not isinstance(embedded_llm_calls, bool)
            else sum(prompt_call_counts.values()) if prompt_call_counts else None
        )
        embedded_by_prompt = metrics_payload.get(
            "llm_calls_by_prompt",
            final_result.get("llm_calls_by_prompt"),
        )
        calls_by_prompt = (
            embedded_by_prompt
            if isinstance(embedded_by_prompt, dict)
            else dict(prompt_call_counts) if prompt_call_counts else {}
        )

        row: Dict[str, Any] = {
            "patient_id": patient_id,
            "started_at": start_event.get("timestamp"),
            "completed_at": end_event.get("timestamp") if end_event else None,
            "duration_seconds": round(duration_seconds, 3) if duration_seconds is not None else None,
            "duration_minutes": round(duration_seconds / 60, 2) if duration_seconds is not None else None,
            "llm_calls": llm_calls,
            "llm_calls_by_prompt": calls_by_prompt,
            "conversation_rounds": final_result.get("conversation_rounds"),
            "consultation_rounds": event_counts.get("SEND_MESSAGE", 0),
            "examination_rounds": event_counts.get("SCHEDULE_EXAMINATION", 0),
            "examination_count": sum(
                len((event.get("payload") or {}).get("items") or [])
                for event in patient_events
                if event.get("event_type") == "SCHEDULE_EXAMINATION"
            ),
            "event_counts": dict(event_counts),
            "finished": bool(
                final_result.get("finished")
                or (end_event and (end_event.get("payload") or {}).get("finished"))
            ),
        }
        process_duration = metrics_payload.get(
            "process_duration_seconds",
            final_result.get("process_duration_seconds"),
        )
        if isinstance(process_duration, (int, float)):
            row["agent_process_duration_seconds"] = process_duration
        case_rows.append(row)

    run_duration = _run_duration(events)
    return {
        "output_dir": str(output_dir),
        "case_count": len(case_rows),
        "cases": case_rows,
        "summary": {
            "run_wall_time_seconds": round(run_duration, 3) if run_duration is not None else None,
            "case_duration_sum_seconds": round(
                sum(row["duration_seconds"] or 0 for row in case_rows), 3
            ),
            "llm_calls_total": (
                sum(row["llm_calls"] for row in case_rows if row["llm_calls"] is not None)
                if all(row["llm_calls"] is not None for row in case_rows)
                else None
            ),
            "llm_calls_available": all(row["llm_calls"] is not None for row in case_rows),
        },
    }


def write_test_metrics(output_dir: Path) -> Dict[str, Any]:
    """Build and persist ``diagnostic_metrics.json`` beside the test artifacts."""
    report = build_test_metrics(output_dir)
    path = Path(output_dir) / "diagnostic_metrics.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        value = json.loads(line)
        if isinstance(value, dict):
            rows.append(value)
    return rows


def _read_prompt_metrics(prompt_dir: Path) -> Dict[str, Dict[str, int]]:
    metrics: Dict[str, Counter[str]] = defaultdict(Counter)
    if not prompt_dir.exists():
        return {}
    for path in prompt_dir.glob("*.txt"):
        text = path.read_text(encoding="utf-8")
        for record in text.split(PROMPT_RECORD_SEPARATOR):
            prompt_match = PROMPT_NAME_RE.search(record)
            patient_match = PATIENT_ID_RE.search(record)
            if not prompt_match or not patient_match:
                continue
            prompt_name = prompt_match.group(1).strip()
            patient_id = patient_match.group(1).strip()
            if patient_id and prompt_name:
                metrics[patient_id][prompt_name] += 1
    return {patient_id: dict(counter) for patient_id, counter in metrics.items()}


def _first_case_end(
    events: Iterable[Dict[str, Any]],
    patient_id: str,
    start_event: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    started = False
    for event in events:
        if event is start_event:
            started = True
            continue
        if not started:
            continue
        if event.get("patient_id") == patient_id and event.get("event_type") in {
            "CASE_END",
            "AGENT_ERROR",
        }:
            return event
    return None


def _events_between(
    events: Iterable[Dict[str, Any]],
    start_event: Dict[str, Any],
    end_event: Optional[Dict[str, Any]],
    patient_id: str,
) -> List[Dict[str, Any]]:
    started = False
    rows = []
    for event in events:
        if event is start_event:
            started = True
        if not started or event.get("patient_id") != patient_id:
            continue
        rows.append(event)
        if end_event is not None and event is end_event:
            break
    return rows


def _duration_seconds(start: Any, end: Any) -> Optional[float]:
    if not start or not end:
        return None
    try:
        return max(0.0, (datetime.fromisoformat(str(end)) - datetime.fromisoformat(str(start))).total_seconds())
    except (TypeError, ValueError):
        return None


def _run_duration(events: List[Dict[str, Any]]) -> Optional[float]:
    timestamps = [
        event.get("timestamp")
        for event in events
        if event.get("timestamp") and event.get("event_type") in {"RUN_START", "CASE_END", "AGENT_ERROR"}
    ]
    if len(timestamps) < 2:
        return None
    return _duration_seconds(timestamps[0], timestamps[-1])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path, help="test output directory containing events.jsonl")
    args = parser.parse_args()
    report = write_test_metrics(args.output_dir)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
