"""Lightweight validation helpers for Office XML documents."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import defusedxml.ElementTree as ET


class BaseValidator:
    """Basic structural checks for unpacked Office documents."""

    required_files: Iterable[str] = ()

    def __init__(self, unpacked_dir: Path, original_file: Path, verbose: bool = False):
        self.unpacked_dir = Path(unpacked_dir)
        self.original_file = Path(original_file)
        self.verbose = verbose

    def validate(self) -> bool:
        if not self._check_required_files(self.required_files):
            return False
        return self._parse_xml_files(self.required_files)

    def _check_required_files(self, rel_paths: Iterable[str]) -> bool:
        missing = [p for p in rel_paths if not (self.unpacked_dir / p).exists()]
        if missing:
            if self.verbose:
                print(f"Missing required files: {missing}")
            return False
        return True

    def _parse_xml_files(self, rel_paths: Iterable[str]) -> bool:
        for rel_path in rel_paths:
            if not rel_path.endswith((".xml", ".rels")):
                continue
            file_path = self.unpacked_dir / rel_path
            try:
                ET.parse(file_path)
            except ET.ParseError as exc:
                if self.verbose:
                    print(f"Invalid XML in {rel_path}: {exc}")
                return False
        return True
