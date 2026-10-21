"""Run the local agent test service and evaluate the generated results."""

from __future__ import annotations

import json
import asyncio
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

BASE_DIR = Path(__file__).resolve().parent
REPO_DIR = BASE_DIR.parent
LOCAL_SDK_DIR = REPO_DIR / "hospital_agent_sdk"
if LOCAL_SDK_DIR.exists() and str(LOCAL_SDK_DIR) not in sys.path:
    sys.path.insert(0, str(LOCAL_SDK_DIR))

from hospital_agent_sdk import build_service_clients, load_config, runtime_config_from_project_config
from hospital_agent_sdk.actions import DoctorActions
from hospital_agent_sdk.client import ServiceClientError
from hospital_agent_sdk.event_logger import EventLogger
from test_metrics import write_test_metrics


TEST_URL = "http://127.0.0.1:7860/test"
EVALUATION_RETRY_DELAYS_SECONDS = (2, 5)
# /test 会串行跑完全部病例；超时需覆盖「病例数 × 单例预算」并留余量。
DEFAULT_TEST_OVERHEAD_SECONDS = 300


def main() -> None:
    config = load_config(BASE_DIR / "config.yaml")
    test_timeout = resolve_test_run_timeout_seconds(config)
    server = start_agent_server()
    try:
        wait_until_ready()
        print(
            f"POST {TEST_URL} (timeout={test_timeout}s; "
            f"patient_count={_test_patient_count(config)}, "
            f"max_patient_minutes={(config.get('workflow') or {}).get('max_patient_minutes', 5)})",
            file=sys.stderr,
        )
        test_summary = request_test_run(timeout_seconds=test_timeout)
        output_dir = Path(str(test_summary["result"]["output_dir"]))
        report = evaluate_test_output(output_dir)
        metrics = write_test_metrics(output_dir)
    finally:
        stop_agent_server(server)

    print(
        json.dumps(
            {"test": test_summary, "evaluation": report, "metrics": metrics},
            ensure_ascii=False,
            indent=2,
        )
    )


def _test_patient_count(config: dict[str, Any]) -> int:
    test_cfg = config.get("test") or {}
    if not isinstance(test_cfg, dict):
        return 3
    patient_ids = test_cfg.get("patient_ids") or []
    if isinstance(patient_ids, list) and patient_ids:
        return len(patient_ids)
    return max(1, int(test_cfg.get("patient_count") or 3))


def resolve_test_run_timeout_seconds(config: dict[str, Any] | None = None) -> int:
    """Scale /test client timeout with patient count and per-case time budget."""
    cfg = config if isinstance(config, dict) else {}
    workflow = cfg.get("workflow") or {}
    raw_minutes = (workflow.get("special_case_max_patient_minutes") if isinstance(workflow, dict) else None) or (
        workflow.get("max_patient_minutes") if isinstance(workflow, dict) else None
    ) or 3
    try:
        per_patient_minutes = max(1, int(float(raw_minutes) + 0.999))
    except (TypeError, ValueError):
        per_patient_minutes = 3
    count = _test_patient_count(cfg)
    return max(600, count * per_patient_minutes * 60 + DEFAULT_TEST_OVERHEAD_SECONDS)


def start_agent_server() -> subprocess.Popen[str]:
    env = os.environ.copy()
    if LOCAL_SDK_DIR.exists():
        env["PYTHONPATH"] = "%s%s%s" % (
            LOCAL_SDK_DIR,
            os.pathsep,
            env.get("PYTHONPATH", ""),
        )
    return subprocess.Popen(
        [sys.executable, "-m", "agent.agent"],
        cwd=BASE_DIR,
        env=env,
        text=True,
    )


def wait_until_ready(timeout_seconds: int = 30) -> None:
    deadline = time.time() + timeout_seconds
    health_url = "http://127.0.0.1:7860/health"
    while time.time() < deadline:
        try:
            request_json("GET", health_url, timeout_seconds=5)
            return
        except Exception:
            time.sleep(0.5)
    raise TimeoutError("Agent service did not become ready on http://127.0.0.1:7860.")


def request_test_run(timeout_seconds: int | None = None) -> dict[str, Any]:
    timeout = timeout_seconds if timeout_seconds is not None else resolve_test_run_timeout_seconds(
        load_config(BASE_DIR / "config.yaml")
    )
    try:
        return request_json("POST", TEST_URL, timeout_seconds=timeout)
    except TimeoutError as exc:
        raise TimeoutError(
            f"POST {TEST_URL} timed out after {timeout}s. "
            "Increase test timeout, lower test.patient_count, or check whether the agent hung on a remote call."
        ) from exc


def evaluate_test_output(output_dir: Path) -> dict[str, Any]:
    config = load_config(BASE_DIR / "config.yaml")
    runtime_config = runtime_config_from_project_config(config, {"local_test": True})
    clients = build_service_clients(
        base_url=runtime_config.service_base_url,
        token=runtime_config.service_token,
        modelscope_sdk_token=runtime_config.modelscope_sdk_token,
        model_api_key=runtime_config.model_api_key,
        team_id=runtime_config.team_id,
        mode="train",
    )
    actions = DoctorActions(
        patient_client=clients.patient_client,
        exam_client=clients.exam_client,
        evaluate_client=clients.evaluate_client,
        event_logger=EventLogger(output_dir=output_dir),
        team_id=runtime_config.team_id,
    )
    return asyncio.run(batch_evaluation_with_retry(actions, output_dir))


async def batch_evaluation_with_retry(
    actions: DoctorActions,
    output_dir: Path,
    retry_delays: tuple[float, ...] = EVALUATION_RETRY_DELAYS_SECONDS,
) -> dict[str, Any]:
    """Retry transient transport failures without hiding service HTTP errors."""
    for attempt in range(len(retry_delays) + 1):
        try:
            return await actions.batch_evaluation(output_dir)
        except ServiceClientError as exc:
            if not _caused_by_transport_error(exc) or attempt >= len(retry_delays):
                raise
            delay = retry_delays[attempt]
            print(
                f"Evaluation service is temporarily unreachable; retrying in {delay:g}s "
                f"({attempt + 2}/{len(retry_delays) + 1}).",
                file=sys.stderr,
            )
            await asyncio.sleep(delay)
    raise AssertionError("unreachable")


def _caused_by_transport_error(exc: BaseException) -> bool:
    current: BaseException | None = exc
    while current is not None:
        if isinstance(current, (urllib.error.URLError, ConnectionError, TimeoutError)):
            return True
        current = current.__cause__
    return False


def request_json(method: str, url: str, timeout_seconds: int = 600) -> dict[str, Any]:
    request = urllib.request.Request(
        url,
        data=b"" if method == "POST" else None,
        headers={"Accept": "application/json"},
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read().decode("utf-8")
    except TimeoutError:
        raise
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", None)
        if isinstance(reason, TimeoutError) or "timed out" in str(exc).lower():
            raise TimeoutError(f"{method} {url} timed out after {timeout_seconds}s") from exc
        raise
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"{method} {url} failed with HTTP {exc.code}: {detail}") from exc
    if not raw.strip():
        return {}
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise RuntimeError(f"{method} {url} returned non-object JSON: {payload!r}")
    return payload


def stop_agent_server(server: subprocess.Popen[str]) -> None:
    if server.poll() is not None:
        return
    server.terminate()
    try:
        server.wait(timeout=10)
    except subprocess.TimeoutExpired:
        server.kill()
        server.wait(timeout=10)


if __name__ == "__main__":
    main()
