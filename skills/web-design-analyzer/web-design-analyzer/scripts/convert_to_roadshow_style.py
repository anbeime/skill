#!/usr/bin/env python3
"""
Design System to Roadshow Brand Style Converter

将 web-design-analyzer 输出的设计系统转换为 ppt-roadshow-generator 可用的品牌风格配置

转换逻辑：
1. 颜色格式转换：数组 → 对象
2. 字段映射：typography → fonts
3. 智能推断：layout_style 和 overall_theme
"""

import json
import argparse
import re
from pathlib import Path
from typing import Dict, Any, Optional


# =============================================================================
# Style Keywords for Inference
# =============================================================================

BUSINESS_KEYWORDS = [
    "professional", "business", "corporate", "enterprise", "formal",
    "minimalist", "clean", "elegant", "refined"
]

TECH_KEYWORDS = [
    "modern", "tech", "cyber", "futuristic", "digital", "innovation",
    "gradient", "glassmorphism", "neomorphism"
]

CREATIVE_KEYWORDS = [
    "creative", "playful", "vibrant", "bold", "dynamic", "energetic",
    "artistic", "expressive", "unique"
]

MINIMALIST_KEYWORDS = [
    "minimalist", "simple", "minimal", "clean", "basic", "essential"
]


# =============================================================================
# Converter
# =============================================================================

class DesignSystemConverter:
    """Converter from design system to roadshow brand style."""

    def __init__(self, input_data: Dict[str, Any]):
        """
        Initialize converter with input design system data.

        Args:
            input_data: Design system JSON from web-design-analyzer
        """
        self.input_data = input_data
        self.output_data = {
            "colors": {
                "primary": "",
                "secondary": "",
                "accent": "",
                "background": "#ffffff",
                "text": "#2c3e50"
            },
            "fonts": {
                "title": "Arial Bold",
                "body": "Arial",
                "accent": "Arial Italic"
            },
            "design_elements": {
                "logo": "",
                "icons": [],
                "patterns": []
            },
            "layout_style": "minimalist",
            "overall_theme": ""
        }

    def convert_colors(self) -> None:
        """Convert colors from array format to object format."""
        colors = self.input_data.get("colors", [])

        if not colors:
            print("警告：未找到颜色信息，使用默认值")
            self.output_data["colors"]["primary"] = "#3498db"
            self.output_data["colors"]["secondary"] = "#2980b9"
            self.output_data["colors"]["accent"] = "#e74c3c"
            return

        # 映射颜色角色
        color_map = {}
        for color_item in colors:
            role = color_item.get("role", "").lower()
            hex_code = color_item.get("hex", "")

            if not hex_code:
                continue

            # 映射角色到输出字段
            if role in ["primary", "main"]:
                color_map["primary"] = hex_code
            elif role in ["secondary", "sub"]:
                color_map["secondary"] = hex_code
            elif role in ["accent", "highlight"]:
                color_map["accent"] = hex_code
            elif role in ["background", "bg"]:
                color_map["background"] = hex_code
            elif role in ["text", "foreground"]:
                color_map["text"] = hex_code

        # 如果映射不全，使用顺序填充
        if "primary" not in color_map and len(colors) >= 1:
            color_map["primary"] = colors[0].get("hex", "#3498db")
        if "secondary" not in color_map and len(colors) >= 2:
            color_map["secondary"] = colors[1].get("hex", "#2980b9")
        if "accent" not in color_map and len(colors) >= 3:
            color_map["accent"] = colors[2].get("hex", "#e74c3c")

        # 更新输出
        for key, value in color_map.items():
            if value:
                self.output_data["colors"][key] = value

        print("✓ 颜色转换完成")

    def convert_fonts(self) -> None:
        """Convert typography to fonts object."""
        typography = self.input_data.get("typography", "")

        if not typography:
            print("警告：未找到排版信息，使用默认字体")
            return

        # 尝试解析 typography 字符串
        # typography 可能是字符串或对象
        if isinstance(typography, str):
            # 从字符串中提取字体信息
            # 常见格式："Helvetica", "Arial", "SF Pro Display"
            font_name = typography.strip()
            if font_name:
                self.output_data["fonts"]["title"] = f"{font_name} Bold"
                self.output_data["fonts"]["body"] = font_name
                self.output_data["fonts"]["accent"] = f"{font_name} Italic"
        elif isinstance(typography, dict):
            # 如果是对象，直接映射
            self.output_data["fonts"]["title"] = typography.get("title", "Arial Bold")
            self.output_data["fonts"]["body"] = typography.get("body", "Arial")
            self.output_data["fonts"]["accent"] = typography.get("accent", "Arial Italic")

        print("✓ 字体转换完成")

    def infer_layout_style(self) -> None:
        """Infer layout style from style_name and components."""
        style_name = self.input_data.get("style_name", "").lower()
        components = str(self.input_data.get("components", "")).lower()

        # 合并文本用于分析
        combined_text = f"{style_name} {components}"

        # 检查关键词
        if any(kw in combined_text for kw in BUSINESS_KEYWORDS):
            self.output_data["layout_style"] = "business"
        elif any(kw in combined_text for kw in TECH_KEYWORDS):
            self.output_data["layout_style"] = "tech"
        elif any(kw in combined_text for kw in CREATIVE_KEYWORDS):
            self.output_data["layout_style"] = "creative"
        elif any(kw in combined_text for kw in MINIMALIST_KEYWORDS):
            self.output_data["layout_style"] = "minimalist"
        else:
            # 默认使用 minimalist
            self.output_data["layout_style"] = "minimalist"

        print(f"✓ 推断布局风格: {self.output_data['layout_style']}")

    def infer_overall_theme(self) -> None:
        """Infer overall theme from style_name."""
        style_name = self.input_data.get("style_name", "")

        if style_name:
            self.output_data["overall_theme"] = style_name
        else:
            self.output_data["overall_theme"] = "Modern Design Style"

        print(f"✓ 设置整体主题: {self.output_data['overall_theme']}")

    def convert(self) -> Dict[str, Any]:
        """
        Execute full conversion.

        Returns:
            Converted brand style data.
        """
        print("开始转换设计系统为路演品牌风格...")

        self.convert_colors()
        self.convert_fonts()
        self.infer_layout_style()
        self.infer_overall_theme()

        print("✓ 转换完成")
        return self.output_data


# =============================================================================
# Main Function
# =============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="将 web-design-analyzer 输出转换为 ppt-roadshow-generator 品牌风格",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        "--input", "-i",
        type=str,
        required=True,
        help="web-design-analyzer 输出的 JSON 文件路径"
    )
    parser.add_argument(
        "--output", "-o",
        type=str,
        default="brand_style.json",
        help="输出的 brand_style.json 文件路径（默认: brand_style.json）"
    )

    args = parser.parse_args()

    # 读取输入文件
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"错误：输入文件不存在: {args.input}")
        return 1

    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"错误：JSON 解析失败: {e}")
        return 1

    # 执行转换
    converter = DesignSystemConverter(input_data)
    output_data = converter.convert()

    # 保存输出文件
    output_path = Path(args.output)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"\n✓ 品牌风格配置已保存: {output_path}")
    except Exception as e:
        print(f"错误：无法写入输出文件: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
