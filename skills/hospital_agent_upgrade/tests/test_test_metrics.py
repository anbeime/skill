import json

from test_metrics import build_test_metrics


def test_build_test_metrics_counts_case_duration_and_prompt_records(tmp_path):
    output_dir = tmp_path / "test_run"
    output_dir.mkdir()
    (output_dir / "events.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "timestamp": "2026-09-01T10:00:00+08:00",
                        "event_type": "RUN_START",
                        "patient_id": "SYSTEM",
                    }
                ),
                json.dumps(
                    {
                        "timestamp": "2026-09-01T10:00:01+08:00",
                        "event_type": "CASE_START",
                        "patient_id": "Patient_1",
                    }
                ),
                json.dumps(
                    {
                        "timestamp": "2026-09-01T10:00:02+08:00",
                        "event_type": "SEND_MESSAGE",
                        "patient_id": "Patient_1",
                        "payload": {},
                    }
                ),
                json.dumps(
                    {
                        "timestamp": "2026-09-01T10:00:03+08:00",
                        "event_type": "SCHEDULE_EXAMINATION",
                        "patient_id": "Patient_1",
                        "payload": {"items": ["心电图（ECG）"]},
                    }
                ),
                json.dumps(
                    {
                        "timestamp": "2026-09-01T10:00:06+08:00",
                        "event_type": "CASE_END",
                        "patient_id": "Patient_1",
                        "payload": {"finished": True},
                    }
                ),
            ]
        ),
        encoding="utf-8",
    )
    (output_dir / "final_results.jsonl").write_text(
        json.dumps(
            {
                "patient_id": "Patient_1",
                "finished": True,
                "conversation_rounds": 1,
            }
        ),
        encoding="utf-8",
    )
    events = (output_dir / "events.jsonl").read_text(encoding="utf-8")
    events = events.replace(
        '\n{"timestamp": "2026-09-01T10:00:06+08:00"',
        '\n{"timestamp": "2026-09-01T10:00:05+08:00",'
        ' "event_type": "CASE_METRICS", "patient_id": "Patient_1",'
        ' "payload": {"llm_calls": 3, "llm_calls_by_prompt": {"case_profile": 2, "differential_diagnosis": 1},'
        ' "process_duration_seconds": 4.8}}\n{"timestamp": "2026-09-01T10:00:06+08:00"',
    )
    (output_dir / "events.jsonl").write_text(events, encoding="utf-8")
    prompt_dir = output_dir / "llm_prompts"
    prompt_dir.mkdir()
    (prompt_dir / "case_profile_Patient_1.txt").write_text(
        "timestamp: now\n"
        "prompt_name: case_profile\n"
        "patient_id: Patient_1\n"
        "response: {}\n"
        + "=" * 80
        + "\n\n",
        encoding="utf-8",
    )

    report = build_test_metrics(output_dir)
    case = report["cases"][0]
    assert case["duration_seconds"] == 5.0
    assert case["llm_calls"] == 3
    assert case["llm_calls_by_prompt"] == {"case_profile": 2, "differential_diagnosis": 1}
    assert case["consultation_rounds"] == 1
    assert case["examination_rounds"] == 1
    assert case["examination_count"] == 1
