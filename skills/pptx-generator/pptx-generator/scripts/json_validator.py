#!/usr/bin/env python3
"""
JSON Validator - Validate JSON format for PPT generation.

This module validates JSON data to ensure it conforms to the
expected format for PPT generation.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


# =============================================================================
# JSON Validator
# =============================================================================

class JSONValidator:
    """Validator for JSON format."""

    def __init__(self):
        """Initialize JSON validator."""
        self.errors = []
        self.warnings = []

    def validate(self, json_path: str) -> bool:
        """
        Validate JSON file.

        Args:
            json_path: Path to JSON file.

        Returns:
            True if valid, False otherwise.
        """
        print(f"验证 JSON 文件: {json_path}\n")

        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except FileNotFoundError:
            self.errors.append(f"文件不存在: {json_path}")
            return False
        except json.JSONDecodeError as e:
            self.errors.append(f"JSON 解析错误: {e}")
            return False

        # Validate structure
        self._validate_structure(data)

        # Print results
        self._print_results()

        return len(self.errors) == 0

    def _validate_structure(self, data: Dict[str, Any]) -> None:
        """
        Validate JSON structure.

        Args:
            data: JSON data dictionary.
        """
        # Check metadata
        if 'metadata' not in data:
            self.warnings.append("缺少 'metadata' 字段（推荐）")
        else:
            self._validate_metadata(data['metadata'])

        # Check slides
        if 'slides' not in data:
            self.errors.append("缺少 'slides' 字段（必需）")
            return

        if not isinstance(data['slides'], list):
            self.errors.append("'slides' 必须是数组")
            return

        if len(data['slides']) == 0:
            self.errors.append("'slides' 数组不能为空")
            return

        # Validate each slide
        for i, slide in enumerate(data['slides'], 1):
            self._validate_slide(slide, i)

    def _validate_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Validate metadata.

        Args:
            metadata: Metadata dictionary.
        """
        if not isinstance(metadata, dict):
            self.errors.append("'metadata' 必须是对象")
            return

        if 'title' not in metadata:
            self.warnings.append("metadata 中缺少 'title' 字段（推荐）")

        if 'author' not in metadata:
            self.warnings.append("metadata 中缺少 'author' 字段（可选）")

        if 'theme' not in metadata:
            self.warnings.append("metadata 中缺少 'theme' 字段（可选）")

    def _validate_slide(self, slide: Dict[str, Any], index: int) -> None:
        """
        Validate a slide.

        Args:
            slide: Slide data dictionary.
            index: Slide index.
        """
        if not isinstance(slide, dict):
            self.errors.append(f"幻灯片 {index} 必须是对象")
            return

        # Check title
        if 'title' not in slide:
            self.errors.append(f"幻灯片 {index} 缺少 'title' 字段（必需）")
        elif not isinstance(slide['title'], str):
            self.errors.append(f"幻灯片 {index} 的 'title' 必须是字符串")
        elif not slide['title'].strip():
            self.errors.append(f"幻灯片 {index} 的 'title' 不能为空")

        # Check content
        if 'content' not in slide:
            self.errors.append(f"幻灯片 {index} 缺少 'content' 字段（必需）")
        elif not isinstance(slide['content'], list):
            self.errors.append(f"幻灯片 {index} 的 'content' 必须是数组")
        elif len(slide['content']) == 0:
            self.warnings.append(f"幻灯片 {index} 的 'content' 数组为空")
        else:
            # Validate content items
            for j, item in enumerate(slide['content'], 1):
                if not isinstance(item, str):
                    self.errors.append(f"幻灯片 {index} 的 content[{j}] 必须是字符串")

        # Check optional fields
        if 'layout' in slide and not isinstance(slide['layout'], str):
            self.warnings.append(f"幻灯片 {index} 的 'layout' 应该是字符串")

        if 'notes' in slide and not isinstance(slide['notes'], str):
            self.warnings.append(f"幻灯片 {index} 的 'notes' 应该是字符串")

    def _print_results(self) -> None:
        """Print validation results."""
        if self.errors:
            print(f"❌ 发现 {len(self.errors)} 个错误：\n")
            for i, error in enumerate(self.errors, 1):
                print(f"  {i}. {error}")
            print()

        if self.warnings:
            print(f"⚠️  发现 {len(self.warnings)} 个警告：\n")
            for i, warning in enumerate(self.warnings, 1):
                print(f"  {i}. {warning}")
            print()

        if not self.errors and not self.warnings:
            print("✓ JSON 格式验证通过！\n")


# =============================================================================
# Main Function
# =============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Validate JSON format for PPT generation'
    )
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Input JSON file path'
    )

    args = parser.parse_args()

    # Create validator
    validator = JSONValidator()

    # Validate
    is_valid = validator.validate(args.input)

    # Exit with appropriate code
    sys.exit(0 if is_valid else 1)


if __name__ == '__main__':
    main()
