#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minimal DOCX comment editor for contract review.
"""

from __future__ import annotations

import html
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from .utilities import XMLEditor

COMMENTS_CONTENT_TYPE = (
    "application/vnd.openxmlformats-officedocument.wordprocessingml.comments+xml"
)
COMMENTS_REL_TYPE = (
    "http://schemas.openxmlformats.org/officeDocument/2006/relationships/comments"
)


class Document:
    """Edit an unpacked .docx directory to insert comments."""

    def __init__(self, unpacked_path: str | Path, author: str = "Contract Review Assistant", initials: str = "CR"):
        self.unpacked_path = Path(unpacked_path)
        if not self.unpacked_path.exists():
            raise FileNotFoundError(f"Unpacked path not found: {self.unpacked_path}")

        self.word_path = self.unpacked_path / "word"
        self.document_path = self.word_path / "document.xml"
        self.comments_path = self.word_path / "comments.xml"
        self.rels_path = self.word_path / "_rels" / "document.xml.rels"
        self.content_types_path = self.unpacked_path / "[Content_Types].xml"

        self.author = author
        self.initials = initials
        self._editors: Dict[str, XMLEditor] = {}

        self._ensure_comments_part()
        self.next_comment_id = self._get_next_comment_id()

    def __getitem__(self, xml_path: str) -> XMLEditor:
        if xml_path not in self._editors:
            target = self.unpacked_path / xml_path
            self._editors[xml_path] = XMLEditor(target)
        return self._editors[xml_path]

    def save(self, validate: bool = False) -> None:
        _ = validate
        for editor in self._editors.values():
            editor.save()

    def get_paragraph_text(self, paragraph) -> str:
        text_parts = []
        for run in paragraph.getElementsByTagName("w:r"):
            for text_node in run.getElementsByTagName("w:t"):
                if text_node.firstChild:
                    text_parts.append(text_node.firstChild.nodeValue)
        return "".join(text_parts)

    def find_paragraph_by_text(self, search_text, allow_fallback: bool = True):
        editor = self["word/document.xml"]
        paragraphs = editor.dom.getElementsByTagName("w:p")
        search_keywords = [search_text] if isinstance(search_text, str) else search_text

        for keyword in search_keywords:
            for para in paragraphs:
                if keyword in self.get_paragraph_text(para):
                    return para

        if not allow_fallback:
            raise ValueError(f"Paragraph not found for: {search_text}")

        for para in paragraphs[:20]:
            if self.get_paragraph_text(para).strip():
                return para
        return paragraphs[0] if paragraphs else None

    def add_comment(self, start, end, text: str, risk_level: str = "中风险") -> int:
        _ = end
        para = self._get_paragraph_node(start)
        if para is None:
            raise ValueError("Comment target paragraph not found")

        comment_id = self.next_comment_id
        self.next_comment_id += 1

        reviewer = self._get_reviewer_by_risk_level(risk_level)
        author = reviewer["author"]
        initials = reviewer["initials"]
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

        self._insert_comment_range(para, comment_id)
        self._append_comment_reference(para, comment_id)
        self._append_comment_entry(comment_id, author, initials, timestamp, text)

        return comment_id

    def verify_comments(self) -> dict:
        result = {"total": 0, "found": 0, "missing": 0, "comment_list": []}
        if not self.comments_path.exists():
            return result

        comments_editor = self["word/comments.xml"]
        comment_nodes = _find_by_local_name(comments_editor.dom, "comment")
        result["total"] = len(comment_nodes)

        document_editor = self["word/document.xml"]
        range_nodes = _find_by_local_name(document_editor.dom, "commentRangeStart")
        result["found"] = len(range_nodes)
        result["missing"] = max(result["total"] - result["found"], 0)

        for node in comment_nodes:
            comment_id = node.getAttribute("w:id") or node.getAttribute("id")
            author = node.getAttribute("w:author") or node.getAttribute("author")
            preview = _extract_first_text(node)
            result["comment_list"].append({
                "id": comment_id,
                "author": author,
                "preview": preview,
            })

        return result

    def _ensure_comments_part(self) -> None:
        self._ensure_comments_xml()
        self._ensure_comments_relationship()
        self._ensure_comments_content_type()

    def _ensure_comments_xml(self) -> None:
        if self.comments_path.exists():
            return
        xml = (
            "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\"?>"
            "<w:comments xmlns:w=\"http://schemas.openxmlformats.org/wordprocessingml/2006/main\"/>"
        )
        self.comments_path.write_text(xml, encoding="utf-8")

    def _ensure_comments_relationship(self) -> None:
        if not self.rels_path.exists():
            raise FileNotFoundError(f"Missing rels file: {self.rels_path}")

        rels_editor = self["word/_rels/document.xml.rels"]
        root = rels_editor.dom.documentElement

        for rel in _find_by_local_name(rels_editor.dom, "Relationship"):
            if rel.getAttribute("Type") == COMMENTS_REL_TYPE:
                return

        next_id = _next_relationship_id(rels_editor.dom)
        rel = rels_editor.dom.createElement("Relationship")
        rel.setAttribute("Id", next_id)
        rel.setAttribute("Type", COMMENTS_REL_TYPE)
        rel.setAttribute("Target", "comments.xml")
        root.appendChild(rel)

    def _ensure_comments_content_type(self) -> None:
        if not self.content_types_path.exists():
            raise FileNotFoundError(f"Missing content types file: {self.content_types_path}")

        types_editor = self["[Content_Types].xml"]
        root = types_editor.dom.documentElement
        for override in _find_by_local_name(types_editor.dom, "Override"):
            if override.getAttribute("PartName") == "/word/comments.xml":
                return

        override = types_editor.dom.createElement("Override")
        override.setAttribute("PartName", "/word/comments.xml")
        override.setAttribute("ContentType", COMMENTS_CONTENT_TYPE)
        root.appendChild(override)

    def _get_next_comment_id(self) -> int:
        if not self.comments_path.exists():
            return 0
        comments_editor = self["word/comments.xml"]
        max_id = -1
        for node in _find_by_local_name(comments_editor.dom, "comment"):
            raw = node.getAttribute("w:id") or node.getAttribute("id")
            if raw:
                try:
                    max_id = max(max_id, int(raw))
                except ValueError:
                    continue
        return max_id + 1

    def _insert_comment_range(self, paragraph, comment_id: int) -> None:
        doc = self["word/document.xml"].dom
        start_elem = doc.createElement("w:commentRangeStart")
        start_elem.setAttribute("w:id", str(comment_id))

        first_elem = _first_element_child(paragraph)
        if first_elem is not None:
            paragraph.insertBefore(start_elem, first_elem)
        else:
            paragraph.appendChild(start_elem)

    def _append_comment_reference(self, paragraph, comment_id: int) -> None:
        doc = self["word/document.xml"].dom
        end_elem = doc.createElement("w:commentRangeEnd")
        end_elem.setAttribute("w:id", str(comment_id))
        paragraph.appendChild(end_elem)

        run = doc.createElement("w:r")
        ref = doc.createElement("w:commentReference")
        ref.setAttribute("w:id", str(comment_id))
        run.appendChild(ref)
        paragraph.appendChild(run)

    def _append_comment_entry(self, comment_id: int, author: str, initials: str, timestamp: str, text: str) -> None:
        comments_editor = self["word/comments.xml"]
        root = comments_editor.dom.documentElement

        comment = comments_editor.dom.createElement("w:comment")
        comment.setAttribute("w:id", str(comment_id))
        comment.setAttribute("w:author", author)
        comment.setAttribute("w:initials", initials)
        comment.setAttribute("w:date", timestamp)

        lines = text.splitlines() or [""]
        for line in lines:
            para = comments_editor.dom.createElement("w:p")
            run = comments_editor.dom.createElement("w:r")
            text_elem = comments_editor.dom.createElement("w:t")
            if _needs_space_preserve(line):
                text_elem.setAttribute("xml:space", "preserve")
            text_elem.appendChild(comments_editor.dom.createTextNode(html.escape(line)))
            run.appendChild(text_elem)
            para.appendChild(run)
            comment.appendChild(para)

        root.appendChild(comment)

    def _get_reviewer_by_risk_level(self, risk_level: str) -> dict:
        risk_reviewers = {
            "高风险": {"author": "高风险", "initials": "高风险"},
            "中风险": {"author": "中风险", "initials": "中风险"},
            "低风险": {"author": "低风险", "initials": "低风险"},
        }
        english_reviewers = {
            "high": {"author": "High Risk", "initials": "H"},
            "medium": {"author": "Medium Risk", "initials": "M"},
            "low": {"author": "Low Risk", "initials": "L"},
        }

        if not risk_level:
            return risk_reviewers["中风险"]
        if risk_level in risk_reviewers:
            return risk_reviewers[risk_level]

        normalized = risk_level.strip().lower().replace("-", " ")
        normalized = " ".join(normalized.split()).replace(" risk", "")
        if normalized in english_reviewers:
            return english_reviewers[normalized]
        return risk_reviewers["中风险"]

    def _get_paragraph_node(self, node):
        current = node
        while current is not None:
            if getattr(current, "tagName", None) == "w:p":
                return current
            current = current.parentNode
        return None


def _needs_space_preserve(text: str) -> bool:
    if text.startswith(" ") or text.endswith(" "):
        return True
    if "  " in text:
        return True
    return False


def _first_element_child(node):
    child = node.firstChild
    while child is not None:
        if child.nodeType == child.ELEMENT_NODE:
            return child
        child = child.nextSibling
    return None


def _find_by_local_name(dom, local: str) -> List:
    matches = []
    for node in dom.getElementsByTagName("*"):
        if node.tagName.split(":")[-1] == local:
            matches.append(node)
    return matches


def _extract_first_text(node) -> str:
    for text_node in node.getElementsByTagName("w:t"):
        if text_node.firstChild:
            return text_node.firstChild.nodeValue
    return ""


def _next_relationship_id(dom) -> str:
    max_id = 0
    for rel in _find_by_local_name(dom, "Relationship"):
        rid = rel.getAttribute("Id")
        if rid.startswith("rId"):
            try:
                max_id = max(max_id, int(rid[3:]))
            except ValueError:
                continue
    return f"rId{max_id + 1}"
