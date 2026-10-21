#!/usr/bin/env python3
"""
SRT 解析 + 分镜建议

把 .srt 字幕解析成结构化字幕条，并按「每幕 25-35 秒口播」的建议把字幕
分组成场景，给出每个场景的起止时间、总时长（→ sceneDurationMs）和文本。

用途：作为 srt-whiteboard-animation 工作流第 1 步的输入依据——
读出叙事事件、规划配图策略、并为每张图片的标注确定 sceneDurationMs。

用法：
  python parse_srt.py <字幕.srt> [--target-sec 30] [--min-sec 25] [--max-sec 35]

输出：JSON（stdout），字段：
  cues    每条字幕: {index, startMs, endMs, durMs, text}
  scenes  建议场景: {sceneIndex, startMs, endMs, sceneDurationMs, cueRange, text}
标准 stderr 打印人类可读摘要，便于直接阅读。
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_TIME = re.compile(r"(\d+):(\d{2}):(\d{2})[,.](\d{1,3})")


def _to_ms(h: str, m: str, s: str, ms: str) -> int:
    return ((int(h) * 60 + int(m)) * 60 + int(s)) * 1000 + int(ms.ljust(3, "0"))


def parse_srt(text: str) -> list[dict]:
    """把 SRT 文本解析成字幕条列表。容忍多余空行、BOM、逗号/点毫秒分隔。"""
    text = text.lstrip("﻿").replace("\r\n", "\n").replace("\r", "\n")
    blocks = re.split(r"\n\s*\n", text.strip())
    cues: list[dict] = []
    for block in blocks:
        lines = [ln for ln in block.split("\n") if ln.strip() != ""]
        if not lines:
            continue
        # 找到含时间轴的行
        time_line_idx = next((i for i, ln in enumerate(lines) if "-->" in ln), None)
        if time_line_idx is None:
            continue
        times = _TIME.findall(lines[time_line_idx])
        if len(times) < 2:
            continue
        start = _to_ms(*times[0])
        end = _to_ms(*times[1])
        body = " ".join(lines[time_line_idx + 1:]).strip()
        cues.append({
            "index": len(cues) + 1,
            "startMs": start,
            "endMs": end,
            "durMs": max(0, end - start),
            "text": body,
        })
    return cues


def group_scenes(cues: list[dict], target_sec: float, min_sec: float, max_sec: float) -> list[dict]:
    """
    按目标时长把连续字幕聚成场景：累积到 target 附近就断一幕，
    但不小于 min、不大于 max（超过 max 强制断幕）。
    """
    scenes: list[dict] = []
    bucket: list[dict] = []
    target_ms, min_ms, max_ms = target_sec * 1000, min_sec * 1000, max_sec * 1000

    def flush() -> None:
        if not bucket:
            return
        start = bucket[0]["startMs"]
        end = bucket[-1]["endMs"]
        scenes.append({
            "sceneIndex": len(scenes) + 1,
            "startMs": start,
            "endMs": end,
            "sceneDurationMs": max(0, end - start),
            "cueRange": [bucket[0]["index"], bucket[-1]["index"]],
            "text": " ".join(c["text"] for c in bucket).strip(),
        })
        bucket.clear()

    for cue in cues:
        # 若把这条并进当前幕会超过 max，先断幕（避免出现超长幕）
        if bucket:
            span_with = cue["endMs"] - bucket[0]["startMs"]
            if span_with > max_ms:
                flush()
        bucket.append(cue)
        span = bucket[-1]["endMs"] - bucket[0]["startMs"]
        # 达到目标且不短于 min 即断幕
        if span >= target_ms and span >= min_ms:
            flush()
    flush()
    return scenes


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="SRT 解析 + 分镜建议")
    p.add_argument("srt", help="字幕文件路径 (.srt)")
    p.add_argument("--target-sec", type=float, default=30.0, help="每幕目标口播秒数（默认 30）")
    p.add_argument("--min-sec", type=float, default=25.0, help="每幕最短秒数（默认 25）")
    p.add_argument("--max-sec", type=float, default=35.0, help="每幕最长秒数（默认 35）")
    args = p.parse_args(argv)

    try:
        raw = Path(args.srt).read_text(encoding="utf-8-sig")
    except OSError as e:
        print(f"[err] 无法读取字幕: {e}", file=sys.stderr)
        return 1

    cues = parse_srt(raw)
    if not cues:
        print("[err] 未解析到任何字幕条，请检查 SRT 格式", file=sys.stderr)
        return 1
    scenes = group_scenes(cues, args.target_sec, args.min_sec, args.max_sec)

    total_ms = cues[-1]["endMs"] - cues[0]["startMs"]
    print(f"字幕条: {len(cues)}  总时长: {total_ms/1000:.1f}s  建议场景: {len(scenes)}", file=sys.stderr)
    for s in scenes:
        print(f"  幕{s['sceneIndex']:>2}  {s['startMs']/1000:6.1f}-{s['endMs']/1000:6.1f}s "
              f"({s['sceneDurationMs']/1000:4.1f}s, 字幕{s['cueRange'][0]}-{s['cueRange'][1]}): "
              f"{s['text'][:40]}", file=sys.stderr)

    json.dump({"cues": cues, "scenes": scenes}, sys.stdout, ensure_ascii=False, indent=2)
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
