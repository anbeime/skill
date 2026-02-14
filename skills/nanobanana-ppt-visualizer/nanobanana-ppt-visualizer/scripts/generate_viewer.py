#!/usr/bin/env python3
"""
PPT Viewer Generator - Generate HTML viewer for PPT slides.

This script creates an interactive HTML viewer for PPT slides,
supporting keyboard navigation and full-screen playback.
"""

import argparse
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List


# =============================================================================
# Constants
# =============================================================================

DEFAULT_TEMPLATE_PATH = "assets/templates/viewer.html"
OUTPUT_BASE_DIR = "outputs"


# =============================================================================
# Load JSON Data
# =============================================================================

def load_ppt_data(input_path: str) -> Dict[str, Any]:
    """
    Load PPT data from JSON file.

    Args:
        input_path: Path to JSON file.

    Returns:
        Parsed JSON data.

    Raises:
        FileNotFoundError: If file does not exist.
        json.JSONDecodeError: If JSON is invalid.
    """
    with open(input_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# =============================================================================
# Generate Viewer HTML
# =============================================================================

def generate_viewer_html(
    ppt_data: Dict[str, Any],
    template_path: str,
    output_path: str
) -> None:
    """
    Generate HTML viewer from PPT data.

    Args:
        ppt_data: PPT data in JSON format.
        template_path: Path to HTML template.
        output_path: Path to output HTML file.
    """
    # Read template
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    # Create slides data for template
    slides = ppt_data.get('slides', [])
    metadata = ppt_data.get('metadata', {})

    # Generate slides HTML
    slides_html = ""
    for idx, slide in enumerate(slides, 1):
        slide_html = f"""
        <div class="slide" data-index="{idx}">
            <div class="slide-content">
                <h2>{slide.get('title', '')}</h2>
                <ul>
"""
        for content_item in slide.get('content', []):
            slide_html += f"                    <li>{content_item}</li>\n"

        slide_html += f"""                </ul>
                <div class="slide-number">{idx} / {len(slides)}</div>
            </div>
        </div>
"""
        slides_html += slide_html

    # Replace placeholders in template
    html_content = template.replace('{{TITLE}}', metadata.get('title', 'Presentation'))
    html_content = html_content.replace('{{SLIDES}}', slides_html)
    html_content = html_content.replace('{{TOTAL_SLIDES}}', str(len(slides)))

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✓ HTML viewer generated: {output_path}")


# =============================================================================
# Create Output Directory
# =============================================================================

def create_output_directory(base_dir: str = OUTPUT_BASE_DIR) -> Path:
    """
    Create output directory with timestamp.

    Args:
        base_dir: Base directory for outputs.

    Returns:
        Path to created output directory.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = Path(base_dir) / timestamp
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create images subdirectory
    images_dir = output_dir / "images"
    images_dir.mkdir(exist_ok=True)

    return output_dir


# =============================================================================
# Copy Assets
# =============================================================================

def copy_template_assets(
    output_dir: Path,
    template_dir: Path = Path("assets/templates")
) -> None:
    """
    Copy CSS and JS assets to output directory.

    Args:
        output_dir: Output directory.
        template_dir: Template directory containing assets.
    """
    # Copy CSS file if exists
    css_source = template_dir / "viewer.css"
    css_dest = output_dir / "viewer.css"
    if css_source.exists():
        shutil.copy2(css_source, css_dest)
        print(f"✓ CSS copied: {css_dest}")

    # Copy JS file if exists
    js_source = template_dir / "viewer.js"
    js_dest = output_dir / "viewer.js"
    if js_source.exists():
        shutil.copy2(js_source, js_dest)
        print(f"✓ JS copied: {js_dest}")


# =============================================================================
# Main Function
# =============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate HTML viewer for PPT slides'
    )
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Input JSON file path'
    )
    parser.add_argument(
        '--template', '-t',
        default=DEFAULT_TEMPLATE_PATH,
        help='HTML template path'
    )
    parser.add_argument(
        '--output-dir', '-o',
        default=OUTPUT_BASE_DIR,
        help='Output directory'
    )

    args = parser.parse_args()

    # Load PPT data
    print(f"Loading PPT data from: {args.input}")
    ppt_data = load_ppt_data(args.input)

    # Create output directory
    print("Creating output directory...")
    output_dir = create_output_directory(args.output_dir)
    print(f"Output directory: {output_dir}")

    # Copy assets
    template_dir = Path(args.template).parent
    copy_template_assets(output_dir, template_dir)

    # Generate HTML viewer
    print("Generating HTML viewer...")
    output_html = output_dir / "index.html"
    generate_viewer_html(ppt_data, args.template, output_html)

    # Create placeholder for images
    images_dir = output_dir / "images"
    metadata = ppt_data.get('metadata', {})
    slides = ppt_data.get('slides', [])

    # Create style.json with metadata
    style_data = {
        "title": metadata.get('title', ''),
        "author": metadata.get('author', ''),
        "total_slides": len(slides),
        "style": "default"
    }

    style_json = output_dir / "style.json"
    with open(style_json, 'w', encoding='utf-8') as f:
        json.dump(style_data, f, indent=2, ensure_ascii=False)

    print(f"✓ Style data saved: {style_json}")
    print(f"\n✓ Viewer generation complete!")
    print(f"  Open in browser: {output_html}")


if __name__ == '__main__':
    main()
