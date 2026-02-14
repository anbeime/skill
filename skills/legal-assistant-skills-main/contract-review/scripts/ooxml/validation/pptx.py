"""Lightweight PPTX validation (structure + XML well-formedness)."""

from __future__ import annotations

from .base import BaseValidator


class PPTXSchemaValidator(BaseValidator):
    required_files = (
        "[Content_Types].xml",
        "ppt/presentation.xml",
    )
