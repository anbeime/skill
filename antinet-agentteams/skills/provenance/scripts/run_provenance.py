#!/usr/bin/env python3
"""provenance Skill 执行脚本（太史阁 / taishige）。

对应 AgentTeams 子任务: provenance
真实调用: core.runtime.AgentSession.run_stage("provenance")
          -> memory.taishige.TaiShiGeAgent.writeback()

把全链路派发/扫描/解析/卡片事件回流成可追溯证据链（trace.jsonl + trace_summary.json）。
该阶段会按依赖惰性触发前面各子任务（extract/review/propose/verify），
因此独立运行即可演示整条主链路的可观测留痕。
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


def main() -> None:
    ap = argparse.ArgumentParser(description="provenance skill runner")
    ap.add_argument("--topic", default=None)
    args = ap.parse_args()

    sess = AgentSession(PKG)
    if args.topic:
        sess.cfg["project"]["topic_example"] = args.topic

    # provenance 是主链路最后一环：先跑通前面各子任务（extract/review/propose/verify），
    # 再把累计的四色卡片与扫描事件回流成证据链，才能体现真实 writeback。
    res = sess.run_full(args.topic)
    ok = res is not None

    prov_dir = os.path.join(PKG, "examples", "snse_survey", "provenance")
    trace_summary = None
    trace_path = os.path.join(prov_dir, "trace_summary.json")
    if os.path.exists(trace_path):
        with open(trace_path, encoding="utf-8") as f:
            trace_summary = json.load(f)

    payload = {
        "skill": "provenance",
        "stage": "provenance",
        "worker": "taishige(太史阁)",
        "writeback_ok": bool(ok),
        "sunk_cards": {
            "blue": len(res.get("blues", [])),
            "green": len(res.get("greens", [])),
            "red": len(res.get("reds", [])),
            "yellow": len(res.get("yellows", [])),
        },
        "llm_used": res.get("llm_used"),
        "event_count": len(trace_summary) if isinstance(trace_summary, list) else None,
        "trace_summary": trace_summary,
    }

    out_dir = os.path.join(PKG, "examples", "snse_survey", "skill_outputs")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "provenance_run.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"[provenance] writeback_ok={payload['writeback_ok']}"
          f" sunk_cards={payload['sunk_cards']}"
          f" events={payload['event_count']}")
    print(f"[provenance] -> {out_path}")


if __name__ == "__main__":
    main()
