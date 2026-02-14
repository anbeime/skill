#!/usr/bin/env python3
"""
HTML Animations - Generate HTML viewer with Framer Motion animations.

This script generates an interactive HTML viewer with smooth animations
powered by Framer Motion, inspired by Remotion's interactivity features.
"""

import argparse
import json
import shutil
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime


# =============================================================================
# Constants
# =============================================================================

DEFAULT_TEMPLATE_PATH = "assets/templates/enhanced_viewer.html"
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
    """
    with open(input_path, 'r', encoding='utf-8') as fr:
        return json.load(fr)


def load_animation_plan(plan_path: str) -> Dict[str, Any]:
    """
    Load animation plan from JSON file.

    Args:
        plan_path: Path to animation plan JSON file.

    Returns:
        Parsed animation plan.
    """
    if not Path(plan_path).exists():
        return None

    with open(plan_path, 'r', encoding='utf-8') as fr:
        return json.load(fr)


# =============================================================================
# Generate HTML with Framer Motion
# =============================================================================

def generate_framer_motion_html(
    ppt_data: Dict[str, Any],
    template_path: str,
    output_path: str,
    animation_plan: Dict[str, Any] = None
) -> None:
    """
    Generate HTML viewer with Framer Motion animations.

    Args:
        ppt_data: PPT data in JSON format.
        template_path: Path to HTML template.
        output_path: Path to output HTML file.
        animation_plan: Animation plan (optional).
    """
    # Read template
    with open(template_path, 'r', encoding='utf-8') as f:
        template = f.read()

    # Create slides data for template
    slides = ppt_data.get('slides', [])
    metadata = ppt_data.get('metadata', {})

    # Generate slides HTML with animation classes
    slides_html = ""
    element_animations = {}

    if animation_plan:
        # Extract element animations
        for anim in animation_plan.get('element_animations', []):
            page_idx = anim['page_index']
            element_type = anim['element']

            if page_idx not in element_animations:
                element_animations[page_idx] = {}

            element_animations[page_idx][element_type] = anim

    for idx, slide in enumerate(slides, 1):
        # Get animation config for this slide
        slide_animations = element_animations.get(idx, {})

        # Title animation
        title_anim = slide_animations.get('title', {})
        title_variant = title_anim.get('type', 'fadeInUp')
        title_delay = title_anim.get('delay', 0.1)
        title_duration = title_anim.get('duration', 0.6)

        # Content animation
        content_anim = slide_animations.get('content', {})
        content_variant = content_anim.get('type', 'fadeInUp')
        content_delay = content_anim.get('delay', 0.3)
        content_duration = content_anim.get('duration', 0.5)
        content_stagger = content_anim.get('stagger', 0.1)

        slide_html = f"""
        <div class="slide" data-index="{idx}">
            <div class="slide-content">
                <motion.h2
                    initial={{ opacity: 0, y: 50 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{
                        duration: {title_duration},
                        delay: {title_delay},
                        ease: "easeOut"
                    }}
                >
                    {slide.get('title', '')}
                </motion.h2>
                <motion.ul
                    initial={{ opacity: 0, y: 30 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{
                        duration: {content_duration},
                        delay: {content_delay},
                        ease: "easeOut",
                        staggerChildren: {content_stagger}
                    }}
                >
"""
        for content_item in slide.get('content', []):
            slide_html += f"""                    <motion.li
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ duration: 0.4 }}
                    >
                        {content_item}
                    </motion.li>
"""

        slide_html += f"""                </motion.ul>
                <motion.div
                    className="slide-number"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ duration: 0.4, delay: 0.8 }}
                >
                    {idx} / {len(slides)}
                </motion.div>
            </div>
        </div>
"""
        slides_html += slide_html

    # Generate page transition variants
    if animation_plan and animation_plan.get('transitions'):
        first_transition = animation_plan['transitions'][0]
        transition_type = first_transition.get('type', 'fade')

        if transition_type == 'slide':
            page_variants = {
                'enter': { 'x': '100%', opacity: 0 },
                'center': { 'x': 0, opacity: 1 },
                'exit': { 'x': '-100%', opacity: 0 }
            }
        elif transition_type == 'zoom':
            page_variants = {
                'enter': { 'scale': 0.9, opacity: 0 },
                'center': { 'scale': 1, opacity: 1 },
                'exit': { 'scale': 1.1, opacity: 0 }
            }
        elif transition_type == 'fade':
            page_variants = {
                'enter': { 'opacity': 0 },
                'center': { 'opacity': 1 },
                'exit': { 'opacity': 0 }
            }
        else:
            page_variants = {
                'enter': { 'opacity': 0 },
                'center': { 'opacity': 1 },
                'exit': { 'opacity': 0 }
            }

        page_variants_json = json.dumps(page_variants, indent=16).replace('\n', '\n' + ' ' * 24)
    else:
        page_variants_json = json.dumps({
            'enter': { 'opacity': 0 },
            'center': { 'opacity': 1 },
            'exit': { 'opacity': 0 }
        }, indent=16).replace('\n', '\n' + ' ' * 24)

    # Replace placeholders in template
    html_content = template.replace('{{TITLE}}', metadata.get('title', 'Presentation'))
    html_content = html_content.replace('{{SLIDES}}', slides_html)
    html_content = html_content.replace('{{TOTAL_SLIDES}}', str(len(slides)))
    html_content = html_content.replace('{{PAGE_VARIANTS}}', page_variants_json)

    # Write output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"✓ Framer Motion HTML 已生成: {output_path}")


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
    css_source = template_dir / "enhanced_viewer.css"
    css_dest = output_dir / "enhanced_viewer.css"
    if css_source.exists():
        shutil.copy2(css_source, css_dest)
        print(f"✓ CSS 已复制: {css_dest}")

    # Copy JS file if exists
    js_source = template_dir / "enhanced_viewer.js"
    js_dest = output_dir / "enhanced_viewer.js"
    if js_source.exists():
        shutil.copy2(js_source, js_dest)
        print(f"✓ JS 已复制: {js_dest}")


# =============================================================================
# Main Function
# =============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate HTML viewer with Framer Motion animations'
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
        '--animation-plan', '-a',
        help='Animation plan JSON file (optional)'
    )
    parser.add_argument(
        '--output-dir', '-o',
        default=OUTPUT_BASE_DIR,
        help='Output directory'
    )

    args = parser.parse_args()

    # Load PPT data
    print(f"加载 PPT 数据: {args.input}")
    ppt_data = load_ppt_data(args.input)

    # Load animation plan (optional)
    animation_plan = None
    if args.animation_plan:
        print(f"加载动画计划: {args.animation_plan}")
        animation_plan = load_animation_plan(args.animation_plan)
        if animation_plan:
            print(f"✓ 动画计划已加载")

    # Create output directory
    print(f"\n创建输出目录...")
    output_dir = create_output_directory(args.output_dir)
    print(f"输出目录: {output_dir}")

    # Copy assets
    template_dir = Path(args.template).parent
    copy_template_assets(output_dir, template_dir)

    # Generate HTML viewer
    print(f"\n生成 Framer Motion HTML...")
    output_path = output_dir / "animated_viewer.html"
    generate_framer_motion_html(
        ppt_data,
        args.template,
        str(output_path),
        animation_plan
    )

    print(f"\n完成！动画播放器已保存到: {output_path}")


if __name__ == '__main__':
    main()
