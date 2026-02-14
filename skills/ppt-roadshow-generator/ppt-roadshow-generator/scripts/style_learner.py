#!/usr/bin/env python3
"""
Brand Style Learner - Analyze and learn brand style from examples.

This module analyzes user-provided brand materials (PPTs, images, brand guidelines)
to extract color schemes, fonts, and design elements for consistent visual generation.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from PIL import Image, ImageColor
except ImportError:
    print("错误：缺少依赖库 Pillow")
    print("请安装依赖：pip install pillow")


# =============================================================================
# Constants
# =============================================================================

DEFAULT_OUTPUT_PATH = "brand_style.json"


# =============================================================================
# Brand Style Analyzer
# =============================================================================

class BrandStyleAnalyzer:
    """Analyzer for brand style from examples."""

    def __init__(self, examples_dir: Optional[str] = None):
        """
        Initialize brand style analyzer.

        Args:
            examples_dir: Directory containing brand examples (images, PPTs, etc.).
        """
        self.examples_dir = Path(examples_dir) if examples_dir else None
        self.style_data = {
            "colors": {
                "primary": "",
                "secondary": "",
                "accent": "",
                "background": "",
                "text": ""
            },
            "fonts": {
                "title": "",
                "body": "",
                "accent": ""
            },
            "design_elements": {
                "logo": "",
                "icons": [],
                "patterns": []
            },
            "layout_style": "",
            "overall_theme": ""
        }

    def analyze_images(self) -> Dict[str, Any]:
        """
        Analyze images to extract color palette.

        Returns:
            Extracted color palette.
        """
        if not self.examples_dir:
            print("未提供示例目录，跳过图像分析")
            return {}

        image_files = list(self.examples_dir.glob("*.png")) + \
                     list(self.examples_dir.glob("*.jpg")) + \
                     list(self.examples_dir.glob("*.jpeg"))

        if not image_files:
            print("未找到图片文件")
            return {}

        print(f"分析 {len(image_files)} 张图片...")

        # 简化的颜色提取：使用最常见的颜色
        all_colors = []
        for img_path in image_files[:5]:  # 只分析前 5 张
            try:
                img = Image.open(img_path)
                img = img.convert('RGB')
                colors = img.getcolors(1000)
                if colors:
                    # 提取前 5 种最常见颜色
                    sorted_colors = sorted(colors, key=lambda x: x[0], reverse=True)
                    all_colors.extend([c[1] for c in sorted_colors[:5]])
            except Exception as e:
                print(f"无法分析图片 {img_path}: {e}")

        # 提取主要颜色
        if all_colors:
            # 简化的逻辑：选择前几种颜色
            unique_colors = list(set(all_colors))[:5]

            if len(unique_colors) >= 1:
                self.style_data["colors"]["primary"] = self._rgb_to_hex(unique_colors[0])
            if len(unique_colors) >= 2:
                self.style_data["colors"]["secondary"] = self._rgb_to_hex(unique_colors[1])
            if len(unique_colors) >= 3:
                self.style_data["colors"]["accent"] = self._rgb_to_hex(unique_colors[2])

        print("✓ 颜色提取完成")
        return self.style_data

    def _rgb_to_hex(self, rgb: tuple) -> str:
        """Convert RGB tuple to hex string."""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"

    def analyze_style_description(self, description: str) -> Dict[str, Any]:
        """
        Analyze style description from user input.

        Args:
            description: User-provided style description.

        Returns:
            Extracted style information.
        """
        # 智能体分析后的结构化数据
        if description:
            # 这里应该由智能体分析，现在做简单处理
            self.style_data["overall_theme"] = description
            print(f"✓ 风格描述: {description}")

        return self.style_data

    def load_from_json(self, json_path: str) -> Dict[str, Any]:
        """
        Load brand style from JSON file.

        Args:
            json_path: Path to JSON file.

        Returns:
            Loaded style data.
        """
        with open(json_path, 'r', encoding='utf-8') as f:
            self.style_data = json.load(f)

        print(f"✓ 已加载品牌风格配置: {json_path}")
        return self.style_data

    def save_to_json(self, output_path: Optional[str] = None) -> str:
        """
        Save brand style to JSON file.

        Args:
            output_path: Output file path.

        Returns:
            Path to saved file.
        """
        output_path = output_path or DEFAULT_OUTPUT_PATH
        output_path = Path(output_path)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.style_data, f, indent=2, ensure_ascii=False)

        print(f"✓ 品牌风格配置已保存: {output_path}")
        return str(output_path)


# =============================================================================
# Main Function
# =============================================================================

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Learn brand style from examples'
    )
    parser.add_argument(
        '--examples-dir', '-d',
        help='Directory containing brand examples'
    )
    parser.add_argument(
        '--style-description', '-s',
        help='Style description from user'
    )
    parser.add_argument(
        '--output', '-o',
        default=DEFAULT_OUTPUT_PATH,
        help='Output JSON file path'
    )

    args = parser.parse_args()

    # Create analyzer
    analyzer = BrandStyleAnalyzer(examples_dir=args.examples_dir)

    # Analyze images if provided
    if args.examples_dir:
        analyzer.analyze_images()

    # Analyze style description if provided
    if args.style_description:
        analyzer.analyze_style_description(args.style_description)

    # Save to JSON
    output_path = analyzer.save_to_json(args.output)

    print(f"\n✓ 品牌风格学习完成")
    print(f"  输出文件: {output_path}")


if __name__ == '__main__':
    main()
