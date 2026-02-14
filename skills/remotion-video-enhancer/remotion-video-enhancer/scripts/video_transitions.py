#!/usr/bin/env python3
"""
Video Transitions - Apply Remotion-style transitions using FFmpeg.

This script applies various transition effects to videos using FFmpeg,
inspired by Remotion's transition library.
"""

import argparse
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional


# =============================================================================
# Constants
# =============================================================================

DEFAULT_OUTPUT_PATH = "enhanced_video.mp4"
DEFAULT_RESOLUTION = "1920x1080"
DEFAULT_FPS = 30
DEFAULT_TRANSITION_DURATION = 1.0


# =============================================================================
# Video Transitions
# =============================================================================

class VideoTransitions:
    """Apply transitions to videos using FFmpeg."""

    def __init__(
        self,
        resolution: str = DEFAULT_RESOLUTION,
        fps: int = DEFAULT_FPS,
        default_duration: float = DEFAULT_TRANSITION_DURATION
    ):
        """
        Initialize video transitions.

        Args:
            resolution: Video resolution (e.g., "1920x1080").
            fps: Frames per second.
            default_duration: Default transition duration in seconds.
        """
        self.resolution = resolution
        self.fps = fps
        self.default_duration = default_duration

        print(f"视频转场处理器已初始化")
        print(f"  分辨率: {resolution}")
        print(f"  帧率: {fps} fps")
        print(f"  默认转场时长: {default_duration} 秒")

    def load_transitions(self, config_path: str) -> List[Dict[str, Any]]:
        """
        Load transition configuration from JSON.

        Args:
            config_path: Path to JSON config file.

        Returns:
            List of transition configurations.
        """
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config.get('transitions', [])

    def apply_fade_transition(
        self,
        input_path: str,
        output_path: str,
        duration: float,
        opacity_start: float = 0.0,
        opacity_end: float = 1.0
    ) -> bool:
        """
        Apply fade transition.

        Args:
            input_path: Input video path.
            output_path: Output video path.
            duration: Transition duration in seconds.
            opacity_start: Starting opacity (0.0-1.0).
            opacity_end: Ending opacity (0.0-1.0).

        Returns:
            True if successful, False otherwise.
        """
        # Build fade filter
        fade_filter = f'fade=t=in:st=0:d={duration}:alpha=1'

        cmd = [
            'ffmpeg',
            '-y',
            '-i', input_path,
            '-vf', fade_filter,
            '-c:a', 'copy',
            str(output_path)
        ]

        return self._run_ffmpeg(cmd, description="应用淡入效果")

    def apply_slide_transition(
        self,
        input_path: str,
        output_path: str,
        duration: float,
        direction: str = 'right'
    ) -> bool:
        """
        Apply slide transition.

        Args:
            input_path: Input video path.
            output_path: Output video path.
            duration: Transition duration in seconds.
            direction: Slide direction (left, right, up, down).

        Returns:
            True if successful, False otherwise.
        """
        # Map direction to crop coordinates
        direction_map = {
            'left': f'crop=iw-({duration}*iw/t):ih:{duration}*iw/t:0',
            'right': f'crop=iw-({duration}*iw/t):ih:0:0',
            'up': f'crop:iw:ih-({duration}*ih/t):0:{duration}*ih/t',
            'down': f'crop=iw:ih-({duration}*ih/t):0:0'
        }

        if direction not in direction_map:
            direction = 'right'

        slide_filter = direction_map[direction]

        cmd = [
            'ffmpeg',
            '-y',
            '-i', input_path,
            '-vf', slide_filter,
            '-c:a', 'copy',
            str(output_path)
        ]

        return self._run_ffmpeg(cmd, description=f"应用滑动效果 ({direction})")

    def apply_zoom_transition(
        self,
        input_path: str,
        output_path: str,
        duration: float,
        scale: float = 1.2,
        direction: str = 'in'
    ) -> bool:
        """
        Apply zoom transition.

        Args:
            input_path: Input video path.
            output_path: Output video path.
            duration: Transition duration in seconds.
            scale: Zoom scale factor.
            direction: Zoom direction (in, out).

        Returns:
            True if successful, False otherwise.
        """
        if direction == 'in':
            scale_filter = f'scale=iw*{scale}:ih*{scale},crop=iw:ih:(iw-iw/{scale})/2:(ih-ih/{scale})/2'
        else:
            scale_filter = f'scale=iw*{scale}:ih*{scale},crop=iw:ih:(iw-iw/{scale})/2:(ih-ih/{scale})/2'

        # Combine with zoom over time
        zoom_filter = f'zoompan=z=\'min(max(zoom,pzoom)+0.0015,{scale})\':d={int(duration*self.fps)}:x=\'iw/2-(iw/zoom/2)\':y=\'ih/2-(ih/zoom/2)\''

        cmd = [
            'ffmpeg',
            '-y',
            '-i', input_path,
            '-vf', zoom_filter,
            '-c:a', 'copy',
            str(output_path)
        ]

        return self._run_ffmpeg(cmd, description=f"应用缩放效果 ({direction})")

    def apply_blur_transition(
        self,
        input_path: str,
        output_path: str,
        duration: float,
        blur_radius: int = 20
    ) -> bool:
        """
        Apply blur transition.

        Args:
            input_path: Input video path.
            output_path: Output video path.
            duration: Transition duration in seconds.
            blur_radius: Blur radius.

        Returns:
            True if successful, False otherwise.
        """
        # Blur effect
        blur_filter = f'boxblur={blur_radius}:{blur_radius}'

        # Combine with fade
        combined_filter = f'[0:v]boxblur={blur_radius}:{blur_radius}[blurred];[0:v][blurred]xfade=transition=fade:duration={duration}:offset=0'

        cmd = [
            'ffmpeg',
            '-y',
            '-i', input_path,
            '-i', input_path,
            '-filter_complex', combined_filter,
            '-c:a', 'copy',
            str(output_path)
        ]

        return self._run_ffmpeg(cmd, description=f"应用模糊效果")

    def apply_rotation_transition(
        self,
        input_path: str,
        output_path: str,
        duration: float,
        angle: float = 90
    ) -> bool:
        """
        Apply rotation transition.

        Args:
            input_path: Input video path.
            output_path: Output video path.
            duration: Transition duration in seconds.
            angle: Rotation angle in degrees.

        Returns:
            True if successful, False otherwise.
        """
        # Rotate effect
        rotate_filter = f'rotate=\'{angle}*t/{duration}\':bilinear=0:fillcolor=black@0'

        cmd = [
            'ffmpeg',
            '-y',
            '-i', input_path,
            '-vf', rotate_filter,
            '-c:a', 'copy',
            str(output_path)
        ]

        return self._run_ffmpeg(cmd, description=f"应用旋转效果 ({angle}度)")

    def apply_transition(
        self,
        input_path: str,
        transition_config: Dict[str, Any],
        output_path: str
    ) -> bool:
        """
        Apply a specific transition based on configuration.

        Args:
            input_path: Input video path.
            transition_config: Transition configuration dictionary.
            output_path: Output video path.

        Returns:
            True if successful, False otherwise.
        """
        transition_type = transition_config.get('type', 'fade')
        duration = transition_config.get('duration', self.default_duration)
        params = transition_config.get('params', {})

        print(f"\n应用转场: {transition_type} (时长: {duration} 秒)")

        if transition_type == 'fade':
            return self.apply_fade_transition(
                input_path, output_path, duration,
                **params
            )
        elif transition_type == 'slide':
            return self.apply_slide_transition(
                input_path, output_path, duration,
                direction=params.get('direction', 'right')
            )
        elif transition_type == 'zoom':
            return self.apply_zoom_transition(
                input_path, output_path, duration,
                scale=params.get('scale', 1.2),
                direction=params.get('direction', 'in')
            )
        elif transition_type == 'blur':
            return self.apply_blur_transition(
                input_path, output_path, duration,
                blur_radius=params.get('blur_radius', 20)
            )
        elif transition_type == 'rotate':
            return self.apply_rotation_transition(
                input_path, output_path, duration,
                angle=params.get('angle', 90)
            )
        else:
            print(f"警告: 不支持的转场类型 '{transition_type}'，使用默认淡入效果")
            return self.apply_fade_transition(input_path, output_path, duration)

    def apply_transitions_to_video(
        self,
        input_path: str,
        transitions_config: List[Dict[str, Any]],
        output_path: str
    ) -> bool:
        """
        Apply all transitions to a video.

        Args:
            input_path: Input video path.
            transitions_config: List of transition configurations.
            output_path: Output video path.

        Returns:
            True if successful, False otherwise.
        """
        if not transitions_config:
            print("没有转场配置，直接复制视频")
            # Copy video without modifications
            cmd = ['ffmpeg', '-y', '-i', input_path, '-c', 'copy', output_path]
            return self._run_ffmpeg(cmd, description="复制视频")

        # Apply transitions sequentially
        current_input = input_path
        temp_files = []

        try:
            for i, transition in enumerate(transitions_config):
                if i == len(transitions_config) - 1:
                    # Last transition, use final output path
                    temp_output = output_path
                else:
                    # Temporary output
                    temp_output = f"temp_transition_{i}.mp4"
                    temp_files.append(temp_output)

                success = self.apply_transition(
                    current_input, transition, temp_output
                )

                if not success:
                    return False

                # Use output as next input
                current_input = temp_output

            print(f"\n✓ 所有转场已应用，输出: {output_path}")
            return True

        finally:
            # Clean up temporary files
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)

    def _run_ffmpeg(self, cmd: List[str], description: str = "FFmpeg 命令") -> bool:
        """
        Run FFmpeg command.

        Args:
            cmd: FFmpeg command list.
            description: Description of the operation.

        Returns:
            True if successful, False otherwise.
        """
        print(f"执行 {description}...")
        try:
            result = subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                text=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"错误：FFmpeg 执行失败")
            print(f"  命令: {' '.join(cmd)}")
            print(f"  错误信息: {e.stderr}")
            return False


# =============================================================================
# Main Function
# =============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Apply Remotion-style transitions to videos'
    )
    parser.add_argument(
        '--input', '-i',
        required=True,
        help='Input video file path'
    )
    parser.add_argument(
        '--transitions', '-t',
        required=True,
        help='Transition configuration JSON file'
    )
    parser.add_argument(
        '--output', '-o',
        default=DEFAULT_OUTPUT_PATH,
        help='Output video file path'
    )
    parser.add_argument(
        '--resolution', '-r',
        default=DEFAULT_RESOLUTION,
        help='Video resolution'
    )
    parser.add_argument(
        '--fps', '-f',
        type=int,
        default=DEFAULT_FPS,
        help='Frames per second'
    )
    parser.add_argument(
        '--transition-duration',
        type=float,
        default=DEFAULT_TRANSITION_DURATION,
        help='Default transition duration'
    )

    args = parser.parse_args()

    # Create transitions processor
    processor = VideoTransitions(
        resolution=args.resolution,
        fps=args.fps,
        default_duration=args.transition_duration
    )

    # Load transitions
    print(f"\n加载转场配置: {args.transitions}")
    transitions = processor.load_transitions(args.transitions)
    print(f"✓ 加载了 {len(transitions)} 个转场配置")

    # Apply transitions
    success = processor.apply_transitions_to_video(
        args.input,
        transitions,
        args.output
    )

    if success:
        print(f"\n完成！增强视频已保存到: {args.output}")
    else:
        print(f"\n失败：无法应用转场")


if __name__ == '__main__':
    main()
