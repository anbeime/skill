#!/usr/bin/env python3
"""
Pack an unpacked Office directory into a .docx, .pptx, or .xlsx file.
"""

import argparse
import sys
import zipfile
from pathlib import Path

import defusedxml.ElementTree as ET


DOC_REQUIRED = {
    ".docx": ["[Content_Types].xml", "word/document.xml", "word/_rels/document.xml.rels"],
    ".pptx": ["[Content_Types].xml", "ppt/presentation.xml"],
    ".xlsx": ["[Content_Types].xml", "xl/workbook.xml"],
}


def pack_document(input_dir: str, output_file: str, validate: bool = False) -> bool:
    """
    Pack a directory into an Office file (.docx/.pptx/.xlsx).

    Args:
        input_dir: Path to unpacked Office document directory
        output_file: Path to output Office file
        validate: If True, run lightweight structural checks

    Returns:
        bool: True if successful, False if validation failed
    """
    input_path = Path(input_dir)
    output_path = Path(output_file)

    if not input_path.is_dir():
        raise ValueError(f"{input_dir} is not a directory")
    if output_path.suffix.lower() not in DOC_REQUIRED:
        raise ValueError(f"{output_file} must be a .docx, .pptx, or .xlsx file")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for item in sorted(input_path.rglob("*")):
            if item.is_file():
                archive.write(item, item.relative_to(input_path))

    if validate:
        if not validate_document(output_path):
            output_path.unlink(missing_ok=True)
            return False

    return True


def validate_document(doc_path: Path) -> bool:
    """Lightweight validation: required files exist and XML parses."""
    suffix = doc_path.suffix.lower()
    required = DOC_REQUIRED.get(suffix, [])

    try:
        with zipfile.ZipFile(doc_path, "r") as archive:
            names = set(archive.namelist())
            missing = [name for name in required if name not in names]
            if missing:
                print(f"Validation error: missing files: {missing}", file=sys.stderr)
                return False

            for name in required:
                if name.endswith((".xml", ".rels")):
                    with archive.open(name) as handle:
                        try:
                            ET.parse(handle)
                        except ET.ParseError as exc:
                            print(f"Validation error: invalid XML in {name}: {exc}", file=sys.stderr)
                            return False
    except zipfile.BadZipFile as exc:
        print(f"Validation error: invalid zip file: {exc}", file=sys.stderr)
        return False

    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Pack a directory into an Office file")
    parser.add_argument("input_directory", help="Unpacked Office document directory")
    parser.add_argument("output_file", help="Output Office file (.docx/.pptx/.xlsx)")
    parser.add_argument("--force", action="store_true", help="Skip validation")
    args = parser.parse_args()

    success = pack_document(
        args.input_directory,
        args.output_file,
        validate=not args.force,
    )

    if args.force:
        print("Warning: Skipped validation, file may be corrupt", file=sys.stderr)
    elif not success:
        print("Contents would produce an invalid file.", file=sys.stderr)
        print("Use --force to skip validation and pack anyway.", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
