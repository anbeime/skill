#!/usr/bin/env python3
"""four-color-cards Skill 执行脚本（通政司 / 监察院 / 丞相府）。

一个 Skill 被三个 Worker 共用，由 --stage 决定具体子任务：
  extract  -> 通政司 TongZhengSiAgent   （蓝卡：事实抽取）
  review   -> 监察院 JianChaYuanAgent    （绿卡：Gap / 解释）
  propose  -> 丞相府 ChengXiangFuAgent   （红卡：行动建议）

真实调用: core.runtime.AgentSession.run_stage("<stage>")
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

VALID_STAGES = {
    "extract": "tongzhengsi(通政司)",
    "review": "jianchayuan(监察院)",
    "propose": "chengxiangfu(丞相府)",
}


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
    ap = argparse.ArgumentParser(description="four-color-cards skill runner")
    ap.add_argument("--stage", required=True, choices=list(VALID_STAGES.keys()),
                    help="extract=蓝卡 / review=绿卡 / propose=红卡")
    ap.add_argument("--topic", default=None)
    args = ap.parse_args()

    sess = AgentSession(PKG)
    if args.topic:
        sess.cfg["project"]["topic_example"] = args.topic

    cards = sess.run_stage(args.stage)  # list[Card]
    payload = {
        "skill": "four-color-cards",
        "stage": args.stage,
        "worker": VALID_STAGES[args.stage],
        "card_count": len(cards) if isinstance(cards, (list, tuple)) else None,
        "cards": _safe(cards),
    }

    out_dir = os.path.join(PKG, "examples", "snse_survey", "skill_outputs")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"four_color_{args.stage}.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"[four-color-cards] stage={args.stage} worker={VALID_STAGES[args.stage]}"
          f" cards={payload['card_count']}")
    print(f"[four-color-cards] -> {out_path}")


if __name__ == "__main__":
    main()
