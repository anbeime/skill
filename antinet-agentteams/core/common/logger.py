"""太史阁 provenance 日志：全链路留痕，供复试/答辩回放。"""
from __future__ import annotations
import os
import json
import time
from datetime import datetime


class ProvenanceLogger:
    def __init__(self, log_dir: str = "examples/snse_survey/provenance"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        # 每次新会话开始时清空本地追踪文件，保证 Demo 复现可追溯日志干净
        # （集群部署下每个 Worker 独立进程/容器，各自管理自身 provenance）。
        try:
            with open(os.path.join(self.log_dir, "trace.jsonl"), "w", encoding="utf-8"):
                pass
        except OSError:
            pass
        self.events: list[dict] = []

    def log(self, agent: str, action: str, detail: str = "", status: str = "ok") -> None:
        ev = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "agent": agent,
            "action": action,
            "detail": detail,
            "status": status,
        }
        self.events.append(ev)
        os.makedirs(self.log_dir, exist_ok=True)
        with open(os.path.join(self.log_dir, "trace.jsonl"), "a", encoding="utf-8") as f:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")
        print(f"[{agent}] {action} -> {status} {detail}")

    def dump(self) -> str:
        path = os.path.join(self.log_dir, "trace_summary.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.events, f, ensure_ascii=False, indent=2)
        return path
