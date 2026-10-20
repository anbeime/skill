#!/usr/bin/env python3
"""security-scan Skill 执行脚本（锦衣卫 / jinyiwei）。

对应 AgentTeams 子任务: security-scan
真实调用: core.runtime.AgentSession.run_stage("security-scan")
          -> security.jinyiwei.JinYiWeiAgent.scan()

零外部依赖，可离线运行。证明每个 AgentTeams Worker 背后都是可执行代码，
而非规划文档。
"""
from __future__ import annotations
import os
import sys
import json
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
SKILLS_ROOT = os.path.dirname(os.path.dirname(HERE))
PKG = os.path.dirname(SKILLS_ROOT)
sys.path.insert(0, os.path.join(PKG, "core"))

from runtime import AgentSession  # noqa: E402


def _safe(o):
    if hasattr(o, "to_dict"):
        return o.to_dict()
    if isinstance(o, (list, tuple)):
        return [_safe(x) for x in o]
    if isinstance(o, dict):
        return {k: _safe(v) for k, v in o.items()}
    if isinstance(o, (str, int, float, bool)) or o is None:
        return o
    return str(o)


def main() -> None:
    ap = argparse.ArgumentParser(description="security-scan skill runner")
    ap.add_argument("--topic", default=None, help="可选：覆盖默认调研主题")
    args = ap.parse_args()

    sess = AgentSession(PKG)
    if args.topic:
        sess.cfg["project"]["topic_example"] = args.topic

    result = sess.run_stage("security-scan")  # {"yellows":[Card], "scan_report":{...}}
    scan_report = result["scan_report"]
    intercepted = scan_report.get("intercepted_papers", [])

    payload = {
        "skill": "security-scan",
        "stage": "security-scan",
        "worker": "jinyiwei(锦衣卫)",
        "passed": len(intercepted) == 0,
        "intercepted_count": len(intercepted),
        "intercepted": _safe(intercepted),
        "no_local_cache_as_production": scan_report.get("no_local_cache_as_production"),
        "yellow_cards": _safe(result["yellows"]),
        "scan_report": _safe(scan_report),
    }

    out_dir = os.path.join(PKG, "examples", "snse_survey", "skill_outputs")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "security_scan.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"[security-scan] verdict={'PASS' if payload['passed'] else 'REJECT'}"
          f" intercepted={payload['intercepted_count']}"
          f" yellows={len(payload['yellow_cards'])}")
    print(f"[security-scan] -> {out_path}")


if __name__ == "__main__":
    main()
