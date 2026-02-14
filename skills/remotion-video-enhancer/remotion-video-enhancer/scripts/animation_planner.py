#!/usr/bin/env python3
"""
Animation Planner - Generate structured animation configuration.

This script analyzes input content and generates a structured
animation plan that can be used by video_transitions.py and
html_animations.py.
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List


# =============================================================================
# Constants
# =============================================================================

ANIMATION_STYLES = {
    'minimal': {
        'transitions': ['fade'],
        'duration_range': (0.5, 1.0),
        'easing': 'linear'
    },
    'dynamic': {
        'transitions': ['slide', 'zoom', 'fade'],
        'duration_range': (1.0, 1.5),
        'easing': 'ease-in-out'
    },
    'cinematic': {
        'transitions': ['blur', 'dissolve', 'zoom'],
        'duration_range': (1.5, 2.0),
        'easing': 'ease-in-out'
    },
    'playful': {
        'transitions': ['bounce', 'elastic', 'rotate'],
        'duration_range': (0.8, 1.2),
        'easing': 'ease-out'
    }
}

TRANSITION_CONFIGS = {
    'fade': {
        'description': '经典淡入淡出效果',
        'params': ['opacity']
    },
    'slide': {
        'description': '滑动过渡',
        'params': ['direction', 'distance']
    },
    'zoom': {
        'description': '推拉镜头效果',
        'params': ['scale', 'direction']
    },
    'flip': {
        'description': '3D 翻转效果',
        'params': ['axis', 'direction']
    },
    'rotate': {
        'description': '旋转过渡',
        'params': ['angle', 'direction']
    },
    'blur': {
        'description': '模糊过渡',
        'params': ['blur_radius']
    },
    'dissolve': {
        'description': '像素溶解效果',
        'params': ['pixel_size']
    },
    'bounce': {
        'description': '弹性动画',
        'params': ['bounce_factor']
    },
    'elastic': {
        'description': '弹性效果',
        'params': ['elasticity']
    }
}


# =============================================================================
# Animation Planner
# =============================================================================

class AnimationPlanner:
    """Planner for structured animation configuration."""

    def __init__(self, style: str = 'dynamic'):
        """
        Initialize animation planner.

        Args:
            style: Animation style (minimal, dynamic, cinematic, playful).
        """
        if style not in ANIMATION_STYLES:
            raise ValueError(f"Invalid style: {style}. Must be one of: {list(ANIMATION_STYLES.keys())}")

        self.style = style
        self.style_config = ANIMATION_STYLES[style]

        print(f"动画规划器已初始化")
        print(f"  风格: {style}")
        print(f"  可用转场: {', '.join(self.style_config['transitions'])}")
        print(f"  时长范围: {self.style_config['duration_range'][0]}-{self.style_config['duration_range'][1]} 秒")
        print(f"  缓动曲线: {self.style_config['easing']}")

    def analyze_input(self, input_path: str) -> Dict[str, Any]:
        """
        Analyze input file and extract content structure.

        Args:
            input_path: Path to input file (JSON, video, or image directory).

        Returns:
            Dictionary with analysis results.
        """
        input_path = Path(input_path)

        if not input_path.exists():
            raise FileNotFoundError(f"Input not found: {input_path}")

        analysis = {
            'type': None,
            'content': None,
            'page_count': 0
        }

        # Detect input type
        if input_path.is_file() and input_path.suffix == '.json':
            analysis['type'] = 'json'
            with open(input_path, 'r', encoding='utf-8') as f:
                analysis['content'] = json.load(f)
            analysis['page_count'] = len(analysis['content'].get('slides', []))
            print(f"✓ 检测到 JSON 输入，共 {analysis['page_count']} 页")

        elif input_path.is_file() and input_path.suffix in ['.mp4', '.mov', '.avi']:
            analysis['type'] = 'video'
            analysis['content'] = str(input_path)
            print(f"✓ 检测到视频输入: {input_path.name}")

        elif input_path.is_dir():
            images = list(input_path.glob('slide-*.png'))
            if images:
                analysis['type'] = 'images'
                analysis['content'] = sorted(images)
                analysis['page_count'] = len(images)
                print(f"✓ 检测到图片输入，共 {analysis['page_count']} 张")
            else:
                raise ValueError(f"未在目录中找到 slide-*.png 文件: {input_path}")

        else:
            raise ValueError(f"不支持的输入类型: {input_path}")

        return analysis

    def generate_transition_plan(
        self,
        analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate transition plan based on analysis.

        Args:
            analysis: Input analysis results.

        Returns:
            List of transition configurations.
        """
        plan = []
        page_count = analysis['page_count']

        if page_count == 0:
            return plan

        # Generate transitions for each page
        for i in range(max(1, page_count)):
            # Select transition type cyclically
            transition_type = self.style_config['transitions'][i % len(self.style_config['transitions'])]
            transition_config = TRANSITION_CONFIGS[transition_type]

            # Generate parameters
            transition = {
                'page_index': i + 1,
                'type': transition_type,
                'duration': 1.0,  # Default duration
                'easing': self.style_config['easing'],
                'params': {}
            }

            # Add type-specific parameters
            if transition_type == 'slide':
                transition['params']['direction'] = ['right', 'left', 'up', 'down'][i % 4]
                transition['params']['distance'] = '100%'
            elif transition_type == 'zoom':
                transition['params']['scale'] = 1.2 if i % 2 == 0 else 0.8
                transition['params']['direction'] = 'in' if i % 2 == 0 else 'out'
            elif transition_type == 'flip':
                transition['params']['axis'] = ['x', 'y'][i % 2]
                transition['params']['direction'] = 'right'
            elif transition_type == 'rotate':
                transition['params']['angle'] = 90 if i % 2 == 0 else -90
                transition['params']['direction'] = 'clockwise' if i % 2 == 0 else 'counter-clockwise'
            elif transition_type == 'blur':
                transition['params']['blur_radius'] = 20
            elif transition_type == 'dissolve':
                transition['params']['pixel_size'] = 8
            elif transition_type == 'bounce':
                transition['params']['bounce_factor'] = 0.3
            elif transition_type == 'elastic':
                transition['params']['elasticity'] = 0.5

            plan.append(transition)

        print(f"✓ 生成了 {len(plan)} 个转场配置")
        return plan

    def generate_element_animations(
        self,
        analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate element-level animations for HTML viewer.

        Args:
            analysis: Input analysis results.

        Returns:
            List of element animation configurations.
        """
        animations = []

        if analysis['type'] != 'json':
            return animations

        content = analysis['content']
        slides = content.get('slides', [])

        for i, slide in enumerate(slides):
            # Title animation
            animations.append({
                'page_index': i + 1,
                'element': 'title',
                'type': 'fadeInUp',
                'delay': 0.1,
                'duration': 0.6,
                'stagger': 0.1
            })

            # Content items animation
            content_count = len(slide.get('content', []))
            animations.append({
                'page_index': i + 1,
                'element': 'content',
                'type': 'fadeInUp',
                'delay': 0.3,
                'duration': 0.5,
                'stagger': 0.1,
                'count': content_count
            })

            # Slide number animation
            animations.append({
                'page_index': i + 1,
                'element': 'slideNumber',
                'type': 'fadeIn',
                'delay': 0.8,
                'duration': 0.4
            })

        print(f"✓ 生成了 {len(animations)} 个元素动画配置")
        return animations

    def generate_plan(
        self,
        input_path: str,
        output_path: str
    ) -> bool:
        """
        Generate complete animation plan.

        Args:
            input_path: Path to input file.
            output_path: Path to output JSON file.

        Returns:
            True if successful, False otherwise.
        """
        try:
            # Analyze input
            print(f"\n分析输入: {input_path}")
            analysis = self.analyze_input(input_path)

            # Generate transition plan
            print(f"\n生成转场计划...")
            transitions = self.generate_transition_plan(analysis)

            # Generate element animations
            print(f"\n生成元素动画...")
            element_animations = self.generate_element_animations(analysis)

            # Build complete plan
            plan = {
                'metadata': {
                    'style': self.style,
                    'input_type': analysis['type'],
                    'page_count': analysis['page_count'],
                    'transition_count': len(transitions),
                    'element_animation_count': len(element_animations)
                },
                'transitions': transitions,
                'element_animations': element_animations
            }

            # Write to file
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(plan, f, indent=2, ensure_ascii=False)

            print(f"\n✓ 动画配置已生成: {output_path}")
            return True

        except Exception as e:
            print(f"\n✗ 错误: {e}")
            return False


# =============================================================================
# Main Function
# =============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate animation configuration'
    )
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Input file or directory'
    )
    parser.add_argument(
        '--style', '-s',
        default='dynamic',
        choices=['minimal', 'dynamic', 'cinematic', 'playful'],
        help='Animation style'
    )
    parser.add_argument(
        '--output', '-o',
        default='animation_plan.json',
        help='Output JSON file path'
    )

    args = parser.parse_args()

    # Create planner
    planner = AnimationPlanner(style=args.style)

    # Generate plan
    success = planner.generate_plan(
        input_path=args.input,
        output_path=args.output
    )

    if success:
        print(f"\n完成！动画配置已保存到: {args.output}")
    else:
        print(f"\n失败：无法生成动画配置")


if __name__ == '__main__':
    main()
