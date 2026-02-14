from __future__ import annotations

from datetime import datetime
import re
from pathlib import Path
from typing import Any

_RE_HEADING_PREFIX = re.compile(r"^(#{1,6})[ \t]+")
_RE_ARTICLE = re.compile(r"^\s*第[零〇一二三四五六七八九十百千万两0-9]+条")
_RE_ARTICLE_FULL = re.compile(r"^\s*(第[零〇一二三四五六七八九十百千万两0-9]+条)(.*)$")
_RE_NON_LAW_STD = re.compile(r"^\s*(?:GB(?:/T)?|DB|ISO|IEC|ASTM|JJF|T/)\b", re.IGNORECASE)
_RE_NON_LAW_KEYWORD = re.compile(r"(国家标准|行业标准|地方标准|团体标准)")
_RE_TRAILING_WS = re.compile(r"[ \t\u3000]+$")
_RE_ITEM = re.compile(r"（[一二三四五六七八九十百千万零〇两]+）")
_RE_SUBITEM = re.compile(r"(?:\([0-9]{1,3}\)|[0-9]{1,3}[、\.．])")
_RE_CANONICAL_HEADING = re.compile(r"^(#{1,6}) ")


def _read_text(path: Path) -> tuple[str | None, str | None]:
    if not path.exists():
        return None, "file-not-found"
    if path.stat().st_size == 0:
        return None, "file-empty"
    try:
        return path.read_text(encoding="utf-8"), None
    except UnicodeDecodeError:
        return None, "utf8-decode-failed"


def _canonical_text(text: str) -> str:
    pieces: list[str] = []
    for line in text.splitlines():
        stripped = _RE_CANONICAL_HEADING.sub("", line, count=1)
        stripped = re.sub(r"[ \t\r\n\u3000]+", "", stripped)
        pieces.append(stripped)
    return "".join(pieces)


def _first_mismatch(old: str, new: str) -> dict[str, Any]:
    same_len = min(len(old), len(new))
    idx = 0
    while idx < same_len and old[idx] == new[idx]:
        idx += 1
    old_ctx = old[max(0, idx - 40) : idx + 80]
    new_ctx = new[max(0, idx - 40) : idx + 80]
    return {
        "index": idx,
        "old_context": old_ctx,
        "new_context": new_ctx,
        "old_char": old[idx] if idx < len(old) else "",
        "new_char": new[idx] if idx < len(new) else "",
        "old_len": len(old),
        "new_len": len(new),
    }


def _check_stage3_a(stage1_text: str, stage2_text: str) -> dict[str, Any]:
    old = _canonical_text(stage1_text)
    new = _canonical_text(stage2_text)
    if old == new:
        return {
            "id": "CHK-001",
            "name": "内容准确性（stage1→stage2）",
            "status": "PASS",
            "detail": "字符流一致（已忽略标题标记与空白差异）",
            "evidence": {},
        }
    return {
        "id": "CHK-001",
        "name": "内容准确性（stage1→stage2）",
        "status": "FAIL",
        "detail": "发现非空白字符差异",
        "evidence": _first_mismatch(old, new),
    }


def _extract_heading(level_line: str) -> tuple[int, str] | None:
    match = re.match(r"^(#{1,6}) (.*)$", level_line)
    if not match:
        return None
    marks, content = match.groups()
    return len(marks), content


def _is_non_law_text(lines: list[str]) -> bool:
    checked = 0
    for line in lines:
        content = line.strip()
        if not content:
            continue
        if content.startswith("<!-- Page "):
            continue
        checked += 1
        if _RE_NON_LAW_STD.search(content) or _RE_NON_LAW_KEYWORD.search(content):
            return True
        if checked >= 80:
            break
    return False


def _check_stage3_b(stage2_text: str, law_decision: str, stage2_reason: str) -> dict[str, Any]:
    lines = stage2_text.splitlines()
    checks: list[dict[str, Any]] = []
    fail_ids: list[str] = []

    if law_decision == "non-law" or stage2_reason == "non-law-document":
        non_law_ok = _is_non_law_text(lines)
        status = "PASS" if non_law_ok else "FAIL"
        if status == "FAIL":
            fail_ids.append("CHK-102")
        checks.append(
            {
                "id": "CHK-102",
                "name": "非法律文档策略一致性",
                "status": status,
                "detail": "非法律文档应触发拒绝路径",
                "evidence": {},
            }
        )
        return {
            "pass": status == "PASS",
            "checks": checks,
            "fail_ids": fail_ids,
            "auto_fixable_fail": False,
            "business_decision": "rejected_non_law",
            "reject_reason": "non-law-document",
        }

    heading_rows: list[tuple[int, int, str]] = []
    for idx, line in enumerate(lines, 1):
        parsed = _extract_heading(line)
        if parsed:
            level, content = parsed
            heading_rows.append((idx, level, content))

    hierarchy_fail = None
    title_count = 0
    for row, level, content in heading_rows:
        if level > 5:
            hierarchy_fail = f"line {row}: heading level > 5"
            break
        if re.match(r"^第[零〇一二三四五六七八九十百千万两0-9]+(?:编|分编)", content):
            if level != 2:
                hierarchy_fail = f"line {row}: 编/分编必须是二级标题"
                break
            continue
        if re.match(r"^第[零〇一二三四五六七八九十百千万两0-9]+章", content):
            if level != 3:
                hierarchy_fail = f"line {row}: 章必须是三级标题"
                break
            continue
        if re.match(r"^第[零〇一二三四五六七八九十百千万两0-9]+节", content):
            if level != 4:
                hierarchy_fail = f"line {row}: 节必须是四级标题"
                break
            continue
        if _RE_ARTICLE.match(content):
            if level != 5:
                hierarchy_fail = f"line {row}: 条必须是五级标题"
                break
            continue
        if level == 1:
            title_count += 1
            continue
        hierarchy_fail = f"line {row}: 非结构标题层级异常"
        break
    if hierarchy_fail is None and title_count == 0:
        hierarchy_fail = "缺少一级标题（法律名称）"
    if hierarchy_fail:
        fail_ids.append("CHK-103")
    checks.append(
        {
            "id": "CHK-103",
            "name": "标题层级合法性",
            "status": "FAIL" if hierarchy_fail else "PASS",
            "detail": hierarchy_fail or "层级合法",
            "evidence": {},
        }
    )

    article_rule_fail = None
    for row, level, content in heading_rows:
        art = _RE_ARTICLE_FULL.match(content)
        if level == 5 and art:
            _, rest = art.groups()
            if rest and not re.match(r"^\s*【[^】]+】", rest):
                article_rule_fail = f"line {row}: 第X条标题中混入正文"
                break
        if level != 5 and _RE_ARTICLE.match(content):
            article_rule_fail = f"line {row}: 第X条未使用五级标题"
            break
    if article_rule_fail is None:
        for idx, line in enumerate(lines, 1):
            if _extract_heading(line):
                continue
            art_line = _RE_ARTICLE_FULL.match(line)
            if not art_line:
                continue
            _, rest = art_line.groups()
            if rest.strip():
                article_rule_fail = f"line {idx}: 第X条与正文未拆行"
                break
    if article_rule_fail:
        fail_ids.append("CHK-104")
    checks.append(
        {
            "id": "CHK-104",
            "name": "条标题规则",
            "status": "FAIL" if article_rule_fail else "PASS",
            "detail": article_rule_fail or "条标题规则通过",
            "evidence": {},
        }
    )

    space_fail = None
    for idx, line in enumerate(lines, 1):
        if _RE_TRAILING_WS.search(line):
            space_fail = f"line {idx}: trailing whitespace"
            break
        if line.startswith((" ", "\t")):
            space_fail = f"line {idx}: leading ASCII whitespace"
            break
        if line.startswith("　"):
            space_fail = f"line {idx}: leading fullwidth whitespace"
            break
        if line.startswith("#") and not re.match(r"^#{1,5}(?: .*)?$", line):
            space_fail = f"line {idx}: heading format invalid"
            break
    if space_fail:
        fail_ids.append("CHK-105")
    checks.append(
        {
            "id": "CHK-105",
            "name": "空格规范",
            "status": "FAIL" if space_fail else "PASS",
            "detail": space_fail or "空格规范通过",
            "evidence": {},
        }
    )

    item_fail = None
    for idx, line in enumerate(lines, 1):
        if _extract_heading(line):
            continue
        count = len(_RE_ITEM.findall(line)) + len(_RE_SUBITEM.findall(line))
        if count > 1:
            item_fail = f"line {idx}: 一行内出现多个项/目标记"
            break
    if item_fail:
        fail_ids.append("CHK-106")
    checks.append(
        {
            "id": "CHK-106",
            "name": "项/目换行规范",
            "status": "FAIL" if item_fail else "PASS",
            "detail": item_fail or "项/目换行规范通过",
            "evidence": {},
        }
    )

    structure_fail = None
    chapter_count = 0
    article_count = 0
    for _, _, content in heading_rows:
        if re.match(r"^第[零〇一二三四五六七八九十百千万两0-9]+章", content):
            chapter_count += 1
        if _RE_ARTICLE.match(content):
            article_count += 1
    if chapter_count == 0 and article_count == 0:
        structure_fail = "缺少章/条结构"
    if structure_fail:
        fail_ids.append("CHK-107")
    checks.append(
        {
            "id": "CHK-107",
            "name": "法律结构完整性",
            "status": "FAIL" if structure_fail else "PASS",
            "detail": structure_fail or f"chapter={chapter_count}, article={article_count}",
            "evidence": {},
        }
    )

    fixable = {"CHK-105", "CHK-106"}
    auto_fixable_fail = len(fail_ids) > 0 and all(x in fixable for x in fail_ids)
    return {
        "pass": len(fail_ids) == 0,
        "checks": checks,
        "fail_ids": fail_ids,
        "auto_fixable_fail": auto_fixable_fail,
        "business_decision": "approved" if len(fail_ids) == 0 else "rejected_check_failed",
        "reject_reason": "" if len(fail_ids) == 0 else "stage3-check-failed",
    }


def run_stage3_checks(
    stage1_path: Path,
    stage2_path: Path,
    law_decision: str,
    attempt: int,
    stage2_reason: str = "",
) -> dict[str, Any]:
    stage1_text, stage1_err = _read_text(stage1_path)
    stage2_text, stage2_err = _read_text(stage2_path)
    prechecks: list[dict[str, Any]] = []
    precheck_fail = False

    if stage1_err:
        precheck_fail = True
        prechecks.append(
            {
                "id": "CHK-000A",
                "name": "stage1 文件可读性",
                "status": "FAIL",
                "detail": stage1_err,
                "evidence": {"path": str(stage1_path)},
            }
        )
    else:
        prechecks.append(
            {
                "id": "CHK-000A",
                "name": "stage1 文件可读性",
                "status": "PASS",
                "detail": "ok",
                "evidence": {"path": str(stage1_path)},
            }
        )

    if stage2_err:
        precheck_fail = True
        prechecks.append(
            {
                "id": "CHK-000B",
                "name": "stage2 文件可读性",
                "status": "FAIL",
                "detail": stage2_err,
                "evidence": {"path": str(stage2_path)},
            }
        )
    else:
        prechecks.append(
            {
                "id": "CHK-000B",
                "name": "stage2 文件可读性",
                "status": "PASS",
                "detail": "ok",
                "evidence": {"path": str(stage2_path)},
            }
        )

    if precheck_fail:
        return {
            "attempt": attempt,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "stage3a_pass": False,
            "stage3b_pass": False,
            "overall_pass": False,
            "stage3b_auto_fixable_fail": False,
            "business_decision": "rejected_check_failed",
            "reject_reason": "file-precheck-failed",
            "checks": prechecks,
        }

    assert stage1_text is not None and stage2_text is not None
    stage3_a = _check_stage3_a(stage1_text, stage2_text)
    stage3_b = _check_stage3_b(stage2_text, law_decision=law_decision, stage2_reason=stage2_reason)
    checks = prechecks + [stage3_a] + stage3_b["checks"]
    stage3a_pass = stage3_a["status"] == "PASS"
    stage3b_pass = stage3_b["pass"]
    business_decision = stage3_b.get("business_decision", "rejected_check_failed")
    reject_reason = stage3_b.get("reject_reason", "")
    overall_pass = stage3a_pass and stage3b_pass and business_decision == "approved"
    return {
        "attempt": attempt,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "stage3a_pass": stage3a_pass,
        "stage3b_pass": stage3b_pass,
        "overall_pass": overall_pass,
        "stage3b_auto_fixable_fail": stage3_b["auto_fixable_fail"],
        "business_decision": business_decision,
        "reject_reason": reject_reason,
        "checks": checks,
    }


def write_stage3_report_md(report_path: Path, check_result: dict[str, Any]) -> None:
    attempts: list[dict[str, Any]] = check_result.get("attempts", [])
    overall_pass = bool(check_result.get("overall_pass", False))
    lines: list[str] = []
    lines.append("# Stage3 Check Report")
    lines.append("")
    lines.append(f"- Overall: {'PASS' if overall_pass else 'FAIL'}")
    lines.append(f"- Total attempts: {len(attempts)}")
    lines.append(f"- Generated at: {datetime.now().isoformat(timespec='seconds')}")
    lines.append("")

    for entry in attempts:
        idx = entry.get("attempt", 0)
        suffix = " (auto-fix)" if entry.get("auto_fix_applied") else ""
        lines.append(f"## Attempt {idx}{suffix}")
        lines.append("")
        lines.append(f"- Stage3-A: {'PASS' if entry.get('stage3a_pass') else 'FAIL'}")
        lines.append(f"- Stage3-B: {'PASS' if entry.get('stage3b_pass') else 'FAIL'}")
        lines.append(f"- Overall: {'PASS' if entry.get('overall_pass') else 'FAIL'}")
        lines.append(f"- Decision: {entry.get('business_decision', '')}")
        lines.append("")
        lines.append("| Check ID | Result | Detail |")
        lines.append("| --- | --- | --- |")
        for check in entry.get("checks", []):
            lines.append(
                f"| {check.get('id','')} | {check.get('status','')} | {str(check.get('detail','')).replace('|', '/')} |"
            )
        lines.append("")

        for check in entry.get("checks", []):
            evidence = check.get("evidence", {})
            if not evidence:
                continue
            if "index" in evidence:
                lines.append(f"### {check.get('id')} 差异证据")
                lines.append("")
                lines.append(f"- index: {evidence.get('index')}")
                lines.append(f"- old_char: `{evidence.get('old_char', '')}`")
                lines.append(f"- new_char: `{evidence.get('new_char', '')}`")
                lines.append(f"- old_context: `{evidence.get('old_context', '')}`")
                lines.append(f"- new_context: `{evidence.get('new_context', '')}`")
                lines.append("")

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
