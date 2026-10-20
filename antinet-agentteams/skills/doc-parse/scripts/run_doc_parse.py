#!/usr/bin/env python3
"""doc-parse Skill 执行脚本（密卷房 / mijuanfang）。

对应 AgentTeams 子任务: doc-parse
真实调用: core.runtime.AgentSession.run_stage("doc-parse")
          -> archive.mijuanfang.MiJuanFangAgent.parse()

三级 fallback（mineru -> pymupdf -> pdfplumber）；离线时降级为预存全文读取，
并如实标注 fallback_used 与 confidence。证明解析 Worker 真实可执行。
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
    ap = argparse.ArgumentParser(description="doc-parse skill runner")
    ap.add_argument("--topic", default=None)
    args = ap.parse_args()

    sess = AgentSession(PKG)
    if args.topic:
        sess.cfg["project"]["topic_example"] = args.topic

    texts = sess.run_stage("doc-parse")  # 解析结果（list[dict] 或 list[object]）
    parsed_count = getattr(sess.mijuanfang, "last_parsed_count", None)

    payload = {
        "skill": "doc-parse",
        "stage": "doc-parse",
        "worker": "mijuanfang(密卷房)",
        "parsed_count": parsed_count,
        "doc_count": len(texts) if isinstance(texts, (list, tuple)) else None,
        "result": _safe(texts),
    }

    out_dir = os.path.join(PKG, "examples", "snse_survey", "skill_outputs")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "doc_parse.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"[doc-parse] parsed={parsed_count} docs={payload['doc_count']}")
    print(f"[doc-parse] -> {out_path}")


if __name__ == "__main__":
    main()
