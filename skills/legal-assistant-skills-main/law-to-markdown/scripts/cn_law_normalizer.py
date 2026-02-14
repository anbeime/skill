from __future__ import annotations

import re
from typing import Any

_CN_NUM = "零〇一二三四五六七八九十百千万两0-9"
_RE_HEADING_PREFIX = re.compile(r"^(#{1,6})[ \t]+")
_RE_CANONICAL_HEADING_PREFIX = re.compile(r"^(#{1,6}) ")
_RE_HEADING_LINE = re.compile(r"^(#{1,6})[ \t\u3000]*(.*)$")
_RE_TRAILING_WS = re.compile(r"[ \t\u3000]+$")
_RE_PART = re.compile(rf"^\s*第[{_CN_NUM}]+(?:编|分编)")
_RE_CHAPTER = re.compile(rf"^\s*第[{_CN_NUM}]+章")
_RE_SECTION = re.compile(rf"^\s*第[{_CN_NUM}]+节")
_RE_ARTICLE = re.compile(rf"^(\s*)(第[{_CN_NUM}]+条)(.*)$")
_RE_ARTICLE_HEAD = re.compile(rf"^\s*第[{_CN_NUM}]+条")
_RE_ITEM = re.compile(r"（[一二三四五六七八九十百千万零〇两]+）")
_RE_SUBITEM = re.compile(r"(?:\([0-9]{1,3}\)|[0-9]{1,3}[、\.．])")
_RE_NON_LAW_STD = re.compile(r"^\s*(?:GB(?:/T)?|DB|ISO|IEC|ASTM|JJF|T/)\b", re.IGNORECASE)
_RE_NON_LAW_KEYWORD = re.compile(r"(国家标准|行业标准|地方标准|团体标准)")


def _strip_heading_prefix(line: str) -> str:
    return _RE_HEADING_PREFIX.sub("", line, count=1)


def _canonical_without_format(text: str) -> str:
    pieces: list[str] = []
    for line in text.splitlines():
        normalized = _RE_CANONICAL_HEADING_PREFIX.sub("", line, count=1)
        normalized = re.sub(r"[ \t\u3000]+", "", normalized)
        pieces.append(normalized)
    return "".join(pieces)


def _split_item_and_subitem(line: str) -> tuple[list[str], int]:
    markers = [m.start() for m in _RE_ITEM.finditer(line)]
    markers.extend(m.start() for m in _RE_SUBITEM.finditer(line))
    markers = sorted(set(markers))
    if len(markers) <= 1:
        return [line], 0

    parts: list[str] = []
    splits = 0
    last = 0
    for idx in markers[1:]:
        parts.append(line[last:idx])
        last = idx
        splits += 1
    parts.append(line[last:])
    return parts, splits


def _cleanup_extra_spaces(lines: list[str]) -> tuple[list[str], int]:
    out: list[str] = []
    changes = 0

    for line in lines:
        new_line = line

        heading = _RE_HEADING_LINE.match(new_line)
        if heading:
            marks, content = heading.groups()
            normalized_content = _RE_TRAILING_WS.sub("", content)
            normalized_content = normalized_content.strip(" \t\u3000")
            normalized = f"{marks} {normalized_content}" if normalized_content else marks
            if normalized != new_line:
                changes += 1
            out.append(normalized)
            continue

        trimmed_trailing = _RE_TRAILING_WS.sub("", new_line)
        if trimmed_trailing != new_line:
            new_line = trimmed_trailing
            changes += 1

        lead_ascii = len(new_line) - len(new_line.lstrip(" \t"))
        if lead_ascii > 0:
            new_line = new_line[lead_ascii:]
            changes += 1

        lead_full = len(new_line) - len(new_line.lstrip("　"))
        if lead_full > 0:
            new_line = new_line[lead_full:]
            changes += 1

        out.append(new_line)

    return out, changes


def _is_non_law_document(lines: list[str]) -> bool:
    checked = 0
    for raw in lines:
        content = _strip_heading_prefix(raw).strip()
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


def normalize_cn_law_markdown(
    text: str,
    law_decision: str = "auto",
    stage2_profile: str = "default",
) -> tuple[str, bool, dict[str, Any]]:
    lines = text.splitlines()
    had_trailing_newline = text.endswith("\n")
    if stage2_profile not in {"default", "structure", "minimal"}:
        stage2_profile = "default"

    if law_decision == "non-law":
        return (
            text,
            False,
            {
                "legal_structure_detected": False,
                "preserve_check_passed": True,
                "reason": "non-law-document",
                "title_count": 0,
                "part_count": 0,
                "chapter_count": 0,
                "section_count": 0,
                "article_count": 0,
                "item_split_count": 0,
                "space_cleanup_count": 0,
            },
        )
    if law_decision == "auto" and _is_non_law_document(lines):
        return (
            text,
            False,
            {
                "legal_structure_detected": False,
                "preserve_check_passed": True,
                "reason": "non-law-document",
                "title_count": 0,
                "part_count": 0,
                "chapter_count": 0,
                "section_count": 0,
                "article_count": 0,
                "item_split_count": 0,
                "space_cleanup_count": 0,
            },
        )

    has_part = False
    has_chapter = False
    has_section = False
    has_article = False

    structure_indexes: list[int] = []
    for idx, raw in enumerate(lines):
        content = _strip_heading_prefix(raw)
        if _RE_ARTICLE_HEAD.match(content):
            has_article = True
            structure_indexes.append(idx)
            continue
        if _RE_SECTION.match(content):
            has_section = True
            structure_indexes.append(idx)
            continue
        if _RE_CHAPTER.match(content):
            has_chapter = True
            structure_indexes.append(idx)
            continue
        if _RE_PART.match(content):
            has_part = True
            structure_indexes.append(idx)
            continue

    legal_structure_detected = has_article or (has_chapter and has_section) or (has_part and has_chapter)
    if not legal_structure_detected:
        return (
            text,
            False,
            {
                "legal_structure_detected": False,
                "preserve_check_passed": True,
                "reason": "legal-structure-not-detected",
                "title_count": 0,
                "part_count": 0,
                "chapter_count": 0,
                "section_count": 0,
                "article_count": 0,
                "item_split_count": 0,
                "space_cleanup_count": 0,
            },
        )

    first_structure_idx = min(structure_indexes) if structure_indexes else len(lines)
    title_idx = -1
    for idx, raw in enumerate(lines):
        if idx >= first_structure_idx:
            break
        if raw.strip():
            title_idx = idx
            break

    out_lines: list[str] = []
    title_count = 0
    part_count = 0
    chapter_count = 0
    section_count = 0
    article_count = 0
    item_split_count = 0

    for idx, raw in enumerate(lines):
        if raw == "":
            out_lines.append(raw)
            continue

        content = _strip_heading_prefix(raw)

        if idx == title_idx:
            out_lines.append(f"# {content}")
            title_count += 1
            continue

        if _RE_PART.match(content):
            out_lines.append(f"## {content}")
            part_count += 1
            continue

        if _RE_CHAPTER.match(content):
            out_lines.append(f"### {content}")
            chapter_count += 1
            continue

        if _RE_SECTION.match(content):
            out_lines.append(f"#### {content}")
            section_count += 1
            continue

        article_match = _RE_ARTICLE.match(content)
        if article_match:
            leading, article_token, rest = article_match.groups()
            if re.match(r"^\s*【[^】]+】", rest):
                out_lines.append(f"##### {content}")
                article_count += 1
                continue

            out_lines.append(f"##### {leading}{article_token}")
            article_count += 1
            if rest:
                if stage2_profile == "default":
                    split_lines, split_count = _split_item_and_subitem(rest)
                    out_lines.extend(split_lines)
                    item_split_count += split_count
                else:
                    out_lines.append(rest)
            continue

        if stage2_profile == "default":
            split_lines, split_count = _split_item_and_subitem(raw)
            out_lines.extend(split_lines)
            item_split_count += split_count
        else:
            out_lines.append(raw)

    out_lines, space_cleanup_count = _cleanup_extra_spaces(out_lines)

    new_text = "\n".join(out_lines)
    if had_trailing_newline:
        new_text += "\n"

    preserve_check_passed = _canonical_without_format(text) == _canonical_without_format(new_text)
    if not preserve_check_passed:
        return (
            text,
            False,
            {
                "legal_structure_detected": True,
                "preserve_check_passed": False,
                "reason": "preserve-check-failed",
                "title_count": 0,
                "part_count": 0,
                "chapter_count": 0,
                "section_count": 0,
                "article_count": 0,
                "item_split_count": 0,
                "space_cleanup_count": 0,
            },
        )

    applied = new_text != text
    return (
        new_text,
        applied,
        {
            "legal_structure_detected": True,
            "preserve_check_passed": True,
            "reason": "applied" if applied else "no-op",
            "title_count": title_count,
            "part_count": part_count,
            "chapter_count": chapter_count,
            "section_count": section_count,
            "article_count": article_count,
            "item_split_count": item_split_count,
            "space_cleanup_count": space_cleanup_count,
        },
    )
