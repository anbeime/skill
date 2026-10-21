"""Local training entrypoint for the baseline agent."""

from __future__ import annotations

import json
import ssl
import time
import urllib.error

from agent import MyDoctorAgent, build_memory
from hospital_agent_sdk import load_config
from hospital_agent_sdk.client import ServiceClientError


TRAIN_RETRY_DELAYS_SECONDS = (2, 5, 10)


def main() -> None:
    config = load_config("config.yaml")
    memory = build_memory(config)
    agent = MyDoctorAgent(config=config, memory=memory)
    summary = run_train_with_retry(agent)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def run_train_with_retry(agent: MyDoctorAgent) -> dict:
    for attempt in range(len(TRAIN_RETRY_DELAYS_SECONDS) + 1):
        try:
            return agent.run_train()
        except ServiceClientError as exc:
            if not _caused_by_transport_error(exc) or attempt >= len(TRAIN_RETRY_DELAYS_SECONDS):
                raise
            delay = TRAIN_RETRY_DELAYS_SECONDS[attempt]
            print(
                "Training service transport error; retrying in %gs (%d/%d): %s"
                % (delay, attempt + 2, len(TRAIN_RETRY_DELAYS_SECONDS) + 1, exc),
                flush=True,
            )
            time.sleep(delay)
    raise AssertionError("unreachable")


def _caused_by_transport_error(exc: BaseException) -> bool:
    current: BaseException | None = exc
    while current is not None:
        if isinstance(current, (urllib.error.URLError, ConnectionError, TimeoutError, ssl.SSLError)):
            return True
        current = current.__cause__
    return False


if __name__ == "__main__":
    main()
