#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lightweight XML helpers for OOXML editing.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, Iterable, List, Optional

from defusedxml import minidom


def _matches_attrs(node, attrs: Optional[Dict[str, str]]) -> bool:
    if not attrs:
        return True
    for key, value in attrs.items():
        if node.getAttribute(key) != value:
            return False
    return True


def _parse_fragment(fragment: str) -> List[minidom.Node]:
    wrapper = f"<root>{fragment}</root>"
    frag_dom = minidom.parseString(wrapper)
    nodes = []
    for child in frag_dom.documentElement.childNodes:
        if child.nodeType == child.ELEMENT_NODE:
            nodes.append(child)
    return nodes


class XMLEditor:
    """Simple XML editor built on minidom."""

    def __init__(self, xml_path: str | Path):
        self.xml_path = Path(xml_path)
        if not self.xml_path.exists():
            raise FileNotFoundError(f"XML not found: {self.xml_path}")
        self.dom = minidom.parse(str(self.xml_path))

    def save(self) -> None:
        data = self.dom.toxml(encoding="utf-8")
        self.xml_path.write_bytes(data)

    def get_nodes(self, tag: Optional[str] = None, attrs: Optional[Dict[str, str]] = None) -> List[minidom.Element]:
        if tag:
            nodes = self.dom.getElementsByTagName(tag)
        else:
            nodes = self.dom.getElementsByTagName("*")
        return [node for node in nodes if _matches_attrs(node, attrs)]

    def get_node(self, tag: Optional[str] = None, attrs: Optional[Dict[str, str]] = None, line_number: Optional[int] = None):
        nodes = self.get_nodes(tag=tag, attrs=attrs)
        if line_number is not None:
            index = max(line_number - 1, 0)
            return nodes[index] if index < len(nodes) else None
        return nodes[0] if nodes else None

    def append_to(self, parent, xml_fragment: str) -> List[minidom.Node]:
        nodes = _parse_fragment(xml_fragment)
        inserted = []
        for node in nodes:
            imported = self.dom.importNode(node, deep=True)
            parent.appendChild(imported)
            inserted.append(imported)
        return inserted

    def insert_before(self, node, xml_fragment: str) -> List[minidom.Node]:
        parent = node.parentNode
        if parent is None:
            return []
        nodes = _parse_fragment(xml_fragment)
        inserted = []
        for frag in nodes:
            imported = self.dom.importNode(frag, deep=True)
            parent.insertBefore(imported, node)
            inserted.append(imported)
        return inserted

    def insert_after(self, node, xml_fragment: str) -> List[minidom.Node]:
        parent = node.parentNode
        if parent is None:
            return []
        nodes = _parse_fragment(xml_fragment)
        inserted = []
        reference = node.nextSibling
        for frag in nodes:
            imported = self.dom.importNode(frag, deep=True)
            parent.insertBefore(imported, reference)
            inserted.append(imported)
        return inserted
