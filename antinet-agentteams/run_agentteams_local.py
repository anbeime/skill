#!/usr/bin/env python3
"""run_agentteams_local.py —— 免 Docker 的本地 AgentTeams 执行入口（复赛可运行 Demo）。

在不依赖 Docker / MinIO / Matrix 的前提下，按 manifests/manifest.yaml 声明的九大 CR
（1 Manager + 1 Team + 7 Worker）在本地装载八官署并跑通端到端主链路，证明
「复赛 · 可执行 AgentTeams 代码包」真实可运行。

真实集群部署（需 Docker）见 README 的 `make install` 路径；本脚本是同等代码的本地免容器运行，
便于评委在无 Docker 环境下一键验收与复现。

用法：
    python run_agentteams_local.py [--topic "SnSe 空位工程导热"] [--no-reset]
"""
from __future__ import annotations

import os
import sys
import json
import argparse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "core"))

from runtime import AgentSession, ROLE_MAP, PIPELINE, STAGE_OWNER  # noqa: E402


def print_topology() -> None:
    print("=== AgentTeams CR 拓扑（来自 manifests/manifest.yaml）===")
    for name, meta in ROLE_MAP.items():
        kind = meta["kind"]
        office = meta["office"]
        if kind == "Manager":
            print(f"  [Manager] {name:<12} ← {office}（意图识别 / 任务分发 / 异常熔断）")
        else:
            role = meta.get("team_role") or "worker"
            skill = meta.get("skill") or "—"
            print(f"  [Worker ] {name:<12} ← {office}（{role}，skill:{skill}）")
    print("  [Team   ] antinet       ← 八官署协作团队（含上述 1 Leader + 6 成员）")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--topic", default="SnSe 空位工程导热")
    ap.add_argument("--no-reset", action="store_true",
                    help="不清空 provenance 目录（默认每次重跑前清空，保证可追溯日志干净）")
    args = ap.parse_args()

    print_topology()
    print()

    base = HERE
    # 本地 Demo 的 provenance 追踪由 ProvenanceLogger 在会话开始时自清空，
    # 无需在此删除目录（删目录/删文件在沙箱内会被安全删除护栏拦截）。
    prov_dir = os.path.join(base, "examples", "snse_survey", "provenance")
    os.makedirs(prov_dir, exist_ok=True)

    session = AgentSession(base)
    res = session.run_full(args.topic)

    # —— 复赛 Demo 产物：survey_report.json ——
    out_dir = os.path.join(base, "examples", "snse_survey")
    llm_cards = sum(1 for c in (res["blues"] + res["greens"] + res["reds"])
                    if getattr(c, "llm_involved", False))
    summary = {
        "topic": res["topic"],
        "agentteams_topology": {
            "manager": "zhihuiling",
            "team": "antinet",
            "workers": [n for n, m in ROLE_MAP.items() if m["kind"] == "Worker"],
            "pipeline": PIPELINE,
        },
        "counts": {
            "blue": len(res["blues"]), "green": len(res["greens"]),
            "red": len(res["reds"]), "yellow": len(res["yellows"]),
        },
        "llm_used": res["llm_used"],
        "llm_endpoint": res["llm_endpoint"],
        "llm_card_count": llm_cards,
        "parsed": session.mijuanfang.last_parsed_count,
        "oa_papers": len(res["scan_report"].get("intercepted_papers", [])),
        "scan_report": res["scan_report"],
    }
    with open(os.path.join(out_dir, "survey_report.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    # —— AgentTeams 风格的派发追踪（Matrix 群聊可追溯，审计评审维度）——
    trace_path = os.path.join(prov_dir, "trace_summary.json")
    events = json.load(open(trace_path, encoding="utf-8")) if os.path.exists(trace_path) else session.logger.events
    dispatch = {
        "agentteams": "agentteams.io/v1beta1",
        "manager": "zhihuiling",
        "team": "antinet",
        "pipeline_stages": PIPELINE,
        "stage_owner": {s: STAGE_OWNER[s][1] for s in PIPELINE},
        "provenance_events": events,
    }
    with open(os.path.join(out_dir, "agentteams_dispatch_trace.json"), "w", encoding="utf-8") as f:
        json.dump(dispatch, f, ensure_ascii=False, indent=2)

    print("\n=== SURVEY DONE ===")
    print(f"主题: {summary['topic']}")
    print(f"四色卡片: 蓝{summary['counts']['blue']} 绿{summary['counts']['green']} "
          f"黄{summary['counts']['yellow']} 红{summary['counts']['red']}")
    print(f"解析论文: {summary['parsed']}/10")
    no_cache_impersonation = res["scan_report"]["no_local_cache_as_production"]
    print(f"锦衣卫: 拦截侵权源 {len(res['scan_report']['intercepted_papers'])}，"
          f"本地缓存冒充生产={'否' if no_cache_impersonation else '是(已如实标注)'}")
    if res["llm_used"]:
        print(f"LLM 在环: ✅ 真实本地模型参与（{res['llm_endpoint']}），生成 {llm_cards} 张 LLM 卡片")
    else:
        print("LLM 在环: ⚠️ 未启用（本地模型 Genie:8910 / FreeLLM:9000 不可达），已如实降级为规则引擎")
    print("产物: examples/snse_survey/{blue,green,red,yellow}_cards.json, cards_index.json, "
          "scan_report.json, provenance/, agentteams_dispatch_trace.json")


if __name__ == "__main__":
    main()
