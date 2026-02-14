#!/usr/bin/env python3
"""
Roadshow Composer - Synthesize complete roadshow video.

This module synthesizes a complete roadshow video from images, audio,
subtitles, and transitions using FFmpeg.
"""

import json
import os
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional


# =============================================================================
# Constants
# =============================================================================

DEFAULT_OUTPUT_PATH = "roadshow_video.mp4"
DEFAULT_RESOLUTION = "1920x1080"
DEFAULT_FPS = 30
DEFAULT_TRANSITION_DURATION = 1.0


# =============================================================================
# Roadshow Composer
# =============================================================================

class RoadshowComposer:
    """Composer for complete roadshow video."""

    def __init__(
        self,
        resolution: str = DEFAULT_RESOLUTION,
        fps: int = DEFAULT_FPS,
        transition_duration: float = DEFAULT_TRANSITION_DURATION
    ):
        """
        Initialize roadshow composer.

        Args:
            resolution: Video resolution (e.g., "1920x1080").
            fps: Frames per second.
            transition_duration: Transition duration in seconds.
        """
        self.resolution = resolution
        self.fps = fps
        self.transition_duration = transition_duration

        print(f"路演视频合成器已初始化")
        print(f"  分辨率: {resolution}")
        print(f"  帧率: {fps} fps")
        print(f"  转场时长: {transition_duration} 秒")

    def collect_materials(
        self,
        images_dir: str,
        audio_dir: str,
        subtitles_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Collect and validate all materials.

        Args:
            images_dir: Directory containing slide images.
            audio_dir: Directory containing audio files.
            subtitles_path: Path to SRT subtitle file (optional).

        Returns:
            Dictionary with collected materials.
        """
        materials = {
            'images': [],
            'voiceover': None,
            'background_music': None,
            'subtitles': None
        }

        # Collect images
        images_path = Path(images_dir)
        if images_path.exists():
            images = sorted(images_path.glob("slide-*.png"))
            materials['images'] = [str(img) for img in images]
            print(f"✓ 找到 {len(images)} 张图片")

        # Collect voiceover
        voiceover_path = Path(audio_dir) / "voiceover.mp3"
        if voiceover_path.exists():
            materials['voiceover'] = str(voiceover_path)
            print(f"✓ 找到配音: {voiceover_path}")

        # Collect background music
        bg_music_path = Path(audio_dir) / "background_music.mp3"
        if bg_music_path.exists():
            materials['background_music'] = str(bg_music_path)
            print(f"✓ 找到背景音乐: {bg_music_path}")

        # Collect subtitles
        if subtitles_path and Path(subtitles_path).exists():
            materials['subtitles'] = subtitles_path
            print(f"✓ 找到字幕: {subtitles_path}")

        return materials

    def create_slideshow_video(
        self,
        images: List[str],
        output_path: str,
        duration_per_slide: float = 5.0
    ) -> bool:
        """
        Create slideshow video from images.

        Args:
            images: List of image file paths.
            output_path: Output video file path.
            duration_per_slide: Duration for each slide in seconds.

        Returns:
            True if successful, False otherwise.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create file list for FFmpeg concat
        list_file = output_path.parent / "filelist.txt"
        with open(list_file, 'w', encoding='utf-8') as f:
            for img in images:
                f.write(f"file '{img}'\n")
                f.write(f"duration {duration_per_slide}\n")

        # Build FFmpeg command
        cmd = [
            'ffmpeg',
            '-y',  # Overwrite output file
            '-f', 'concat',
            '-safe', '0',
            '-i', str(list_file),
            '-vf', f'scale={self.resolution}:force_original_aspect_ratio=decrease,pad={self.resolution}:(ow-iw)/2:(oh-ih)/2',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-r', str(self.fps),
            str(output_path)
        ]

        print(f"执行 FFmpeg 命令...")
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"✓ 幻灯片视频已生成: {output_path}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"错误：FFmpeg 执行失败 - {e}")
            print(f"  stderr: {e.stderr}")
            return False

    def add_audio_to_video(
        self,
        video_path: str,
        voiceover_path: str,
        background_music_path: Optional[str],
        output_path: str
    ) -> bool:
        """
        Add audio tracks to video.

        Args:
            video_path: Input video file path.
            voiceover_path: Voiceover audio file path.
            background_music_path: Background music file path (optional).
            output_path: Output video file path.

        Returns:
            True if successful, False otherwise.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build FFmpeg command
        inputs = ['-i', video_path, '-i', voiceover_path]
        audio_filter = f'[1:a]'

        if background_music_path:
            inputs.extend(['-i', background_music_path])
            # Mix voiceover and background music
            audio_filter = f'[1:a][2:a]amix=inputs=2:duration=first:dropout_transition=2'

        cmd = [
            'ffmpeg',
            '-y',
        ] + inputs + [
            '-filter_complex', audio_filter,
            '-c:v', 'copy',
            '-c:a', 'aac',
            '-shortest',
            str(output_path)
        ]

        print(f"添加音频到视频...")
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"✓ 音频已添加: {output_path}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"错误：添加音频失败 - {e}")
            print(f"  stderr: {e.stderr}")
            return False

    def burn_subtitles(
        self,
        video_path: str,
        subtitles_path: str,
        output_path: str
    ) -> bool:
        """
        Burn subtitles into video.

        Args:
            video_path: Input video file path.
            subtitles_path: SRT subtitle file path.
            output_path: Output video file path.

        Returns:
            True if successful, False otherwise.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Build FFmpeg command
        cmd = [
            'ffmpeg',
            '-y',
            '-i', video_path,
            '-vf', f"subtitles={subtitles_path}:force_style='Fontsize=24,PrimaryColour=&H00FFFFFF,BackColour=&H80000000'",
            '-c:a', 'copy',
            str(output_path)
        ]

        print(f"烧录字幕...")
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"✓ 字幕已烧录: {output_path}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"错误：烧录字幕失败 - {e}")
            print(f"  stderr: {e.stderr}")
            return False

    def compose_roadshow(
        self,
        images_dir: str,
        audio_dir: str,
        subtitles_path: Optional[str] = None,
        output_path: str = DEFAULT_OUTPUT_PATH
    ) -> bool:
        """
        Compose complete roadshow video.

        Args:
            images_dir: Directory containing slide images.
            audio_dir: Directory containing audio files.
            subtitles_path: Path to SRT subtitle file (optional).
            output_path: Output video file path.

        Returns:
            True if successful, False otherwise.
        """
        print("=" * 60)
        print("开始合成路演视频")
        print("=" * 60)

        # Collect materials
        materials = self.collect_materials(images_dir, audio_dir, subtitles_path)

        if not materials['images']:
            print("错误：未找到图片")
            return False

        if not materials['voiceover']:
            print("错误：未找到配音")
            return False

        temp_video = None
        current_video = None

        try:
            # Step 1: Create slideshow from images
            print("\n步骤 1/3: 创建幻灯片视频")
            temp_video = Path(output_path).parent / "temp_slideshow.mp4"
            success = self.create_slideshow_video(
                images=materials['images'],
                output_path=str(temp_video)
            )

            if not success:
                return False

            # Step 2: Add audio
            print("\n步骤 2/3: 添加音频")
            video_with_audio = Path(output_path).parent / "temp_with_audio.mp4"
            success = self.add_audio_to_video(
                video_path=str(temp_video),
                voiceover_path=materials['voiceover'],
                background_music_path=materials['background_music'],
                output_path=str(video_with_audio)
            )

            if not success:
                return False

            current_video = video_with_audio

            # Step 3: Add subtitles if available
            if materials['subtitles']:
                print("\n步骤 3/3: 添加字幕")
                success = self.burn_subtitles(
                    video_path=str(current_video),
                    subtitles_path=materials['subtitles'],
                    output_path=output_path
                )

                if not success:
                    return False
            else:
                print("\n步骤 3/3: 跳过字幕（未提供）")
                # Just rename the video with audio
                Path(current_video).rename(output_path)

            print("\n" + "=" * 60)
            print("✓ 路演视频合成完成")
            print("=" * 60)
            print(f"输出文件: {output_path}")

            return True

        except Exception as e:
            print(f"错误：合成失败 - {e}")
            return False

        finally:
            # Clean up temporary files
            if temp_video and temp_video.exists():
                temp_video.unlink()
            if current_video and current_video.exists() and current_video.name != Path(output_path).name:
                current_video.unlink()


# =============================================================================
# Main Function
# =============================================================================

def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Compose complete roadshow video'
    )
    parser.add_argument(
        '--images', '-i',
        required=True,
        help='Directory containing slide images'
    )
    parser.add_argument(
        '--audio', '-a',
        required=True,
        help='Directory containing audio files'
    )
    parser.add_argument(
        '--subtitles', '-s',
        help='SRT subtitle file path (optional)'
    )
    parser.add_argument(
        '--style-brand', '-b',
        help='Brand style JSON file path (optional)'
    )
    parser.add_argument(
        '--output', '-o',
        default=DEFAULT_OUTPUT_PATH,
        help='Output video file path'
    )

    args = parser.parse_args()

    # Create composer
    composer = RoadshowComposer()

    # Compose roadshow video
    success = composer.compose_roadshow(
        images_dir=args.images,
        audio_dir=args.audio,
        subtitles_path=args.subtitles,
        output_path=args.output
    )

    if not success:
        print("\n✗ 路演视频合成失败")
        exit(1)


if __name__ == '__main__':
    main()
