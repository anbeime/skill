#!/usr/bin/env python3
"""Unpack Office files (.docx, .pptx, .xlsx) into a directory."""

import random
import sys
import zipfile
from pathlib import Path


def unpack_document(input_file: str, output_dir: str) -> None:
    """
    Unpack an Office file into a directory.

    Args:
        input_file: Path to the Office file (.docx, .pptx, .xlsx)
        output_dir: Directory to extract contents to
    """
    input_path = Path(input_file)
    output_path = Path(output_dir)

    if not input_path.is_file():
        raise FileNotFoundError(f"Input file not found: {input_file}")

    output_path.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(input_path, "r") as archive:
        archive.extractall(output_path)

    if input_path.suffix.lower() == ".docx":
        suggested_rsid = "".join(random.choices("0123456789ABCDEF", k=8))
        print(f"Suggested RSID for edit session: {suggested_rsid}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python unpack.py <office_file> <output_dir>")
    unpack_document(sys.argv[1], sys.argv[2])
