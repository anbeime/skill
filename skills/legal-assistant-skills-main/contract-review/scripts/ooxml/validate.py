#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run lightweight validation on unpacked Office documents."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from validation import DOCXSchemaValidator, PPTXSchemaValidator, RedliningValidator


def _validators_for(ext: str):
    if ext == ".docx":
        return [DOCXSchemaValidator, RedliningValidator]
    if ext == ".pptx":
        return [PPTXSchemaValidator]
    return None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate unpacked Office XML")
    parser.add_argument("unpacked_dir", help="Unpacked directory path")
    parser.add_argument("--original", required=True, help="Original file (.docx/.pptx/.xlsx)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    args = parser.parse_args(argv)

    unpacked_dir = Path(args.unpacked_dir)
    original_file = Path(args.original)

    if not unpacked_dir.is_dir():
        print(f"Error: {unpacked_dir} is not a directory")
        return 1
    if not original_file.is_file():
        print(f"Error: {original_file} is not a file")
        return 1

    validators = _validators_for(original_file.suffix.lower())
    if not validators:
        print(f"Error: validation not supported for {original_file.suffix}")
        return 1

    success = True
    for validator_cls in validators:
        validator = validator_cls(unpacked_dir, original_file, verbose=args.verbose)
        if not validator.validate():
            success = False

    if success:
        print("Validation completed successfully.")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
