"""Lightweight DOCX validation (structure + XML well-formedness)."""

from __future__ import annotations

from .base import BaseValidator


class DOCXSchemaValidator(BaseValidator):
    required_files = (
        "[Content_Types].xml",
        "word/document.xml",
        "word/_rels/document.xml.rels",
    )
