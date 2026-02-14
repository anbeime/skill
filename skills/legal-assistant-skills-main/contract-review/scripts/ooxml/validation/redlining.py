"""Minimal redlining validator placeholder."""

from __future__ import annotations

from .base import BaseValidator


class RedliningValidator(BaseValidator):
    required_files = (
        "word/document.xml",
    )
