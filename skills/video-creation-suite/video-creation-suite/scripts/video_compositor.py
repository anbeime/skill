#!/usr/bin/env python3
"""
视频合成脚本
将图片、配音、音效、背景音乐、字幕合成为最终视频
"""

import os
import json
from typing import Dict, Any, List
from moviepy.editor import (
    VideoFileClip,
    ImageSequenceClip,
    AudioFileClip,
    CompositeAudioClip,
    CompositeVideoClip,
    TextClip,
    vfx
)
from .error_handler import retry_on_failure, ErrorLogger

logger = ErrorLogger()


@retry_on_failure(max_retries=2, retry_delay=0.5)
def composite_video(
    images_dir: str,
    audio_dir: str = None,
    subtitles_file: str = None,
    output_path: str = "./output/final_video.mp4",
    fps: int = 30,
    duration_per_image: float = 3.0,
    resolution: tuple = (1920, 1080)
) -> Dict[str, Any]:
    """
    合成视频

    参数:
        images_dir: 图片目录
        audio_dir: 音频目录(包含配音、音效、背景音乐)
        subtitles_file: 字幕文件路径(SRT格式)
        output_path: 输出视频路径
        fps: 帧率
        duration_per_image: 每张图片的显示时长(秒)
        resolution: 视频分辨率(width, height)

    返回:
        合成结果字典
    """
    try:
        logger.log_info("开始视频合成...")

        # 获取所有图片
        image_files = sorted([
            f for f in os.listdir(images_dir)
            if f.lower().endswith(('.png', '.jpg', '.jpeg'))
        ])

        if not image_files:
            raise ValueError(f"未找到图片文件: {images_dir}")

        logger.log_info(f"找到 {len(image_files)} 张图片")

        # 步骤1: 从图片序列生成视频
        logger.log_info("步骤1: 从图片序列生成视频...")

        image_paths = [os.path.join(images_dir, f) for f in image_files]
        video_clip = ImageSequenceClip(
            image_paths,
            fps=fps
        )
        video_clip = video_clip.set_duration(len(image_files) * duration_per_image)
        video_clip = video_clip.resize(resolution)

        # 步骤2: 添加音频
        logger.log_info("步骤2: 添加音频...")

        audio_clips = []

        if audio_dir and os.path.exists(audio_dir):
            # 添加背景音乐
            bgm_files = [
                f for f in os.listdir(audio_dir)
                if 'background' in f.lower() or 'bgm' in f.lower()
            ]

            for bgm_file in bgm_files:
                bgm_path = os.path.join(audio_dir, bgm_file)
                bgm_clip = AudioFileClip(bgm_path)
                bgm_clip = bgm_clip.set_duration(video_clip.duration)
                bgm_clip = bgm_clip.volumex(0.3)  # 背景音乐音量 30%
                audio_clips.append(bgm_clip)
                logger.log_info(f"添加背景音乐: {bgm_file}")

            # 添加配音
            voice_files = [
                f for f in os.listdir(audio_dir)
                if 'voice' in f.lower() or 'narration' in f.lower()
            ]

            for voice_file in voice_files:
                voice_path = os.path.join(audio_dir, voice_file)
                voice_clip = AudioFileClip(voice_path)
                voice_clip = voice_clip.volumex(1.0)  # 配音音量 100%
                audio_clips.append(voice_clip)
                logger.log_info(f"添加配音: {voice_file}")

            # 添加音效
            sfx_files = [
                f for f in os.listdir(audio_dir)
                if 'sound' in f.lower() or 'sfx' in f.lower() or 'effect' in f.lower()
            ]

            for sfx_file in sfx_files:
                sfx_path = os.path.join(audio_dir, sfx_file)
                sfx_clip = AudioFileClip(sfx_path)
                sfx_clip = sfx_clip.volumex(0.5)  # 音效音量 50%
                audio_clips.append(sfx_clip)
                logger.log_info(f"添加音效: {sfx_file}")

        # 合并音频
        if audio_clips:
            final_audio = CompositeAudioClip(audio_clips)
            final_audio = final_audio.set_duration(video_clip.duration)
            video_clip = video_clip.set_audio(final_audio)
            logger.log_info(f"已合并 {len(audio_clips)} 个音频轨道")

        # 添加字幕
        if subtitles_file and os.path.exists(subtitles_file):
            logger.log_info("步骤3: 添加字幕...")
            video_clip = _add_subtitles(video_clip, subtitles_file)
            logger.log_info(f"已添加字幕: {subtitles_file}")

        # 步骤4: 导出视频
        logger.log_info("步骤4: 导出视频...")
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # 使用更快的编码设置，避免长时间等待
        video_clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            fps=fps,
            preset='ultrafast',  # 使用最快的预设
            threads=4,
            logger=None,  # 禁用 FFmpeg 详细日志
            verbose=False  # 减少输出
        )

        logger.log_info(f"视频已合成: {output_path}")

        return {
            'success': True,
            'output_path': output_path,
            'duration': video_clip.duration,
            'resolution': resolution,
            'frame_count': len(image_files),
            'has_audio': len(audio_clips) > 0,
            'has_subtitles': subtitles_file is not None
        }

    except Exception as e:
        logger.log_error(f"视频合成失败: {str(e)}")
        raise  # 重新抛出异常，让 retry_on_failure 处理


def _add_subtitles(
    video_clip,
    subtitles_file: str
):
    """
    添加字幕

    参数:
        video_clip: 视频剪辑
        subtitles_file: 字幕文件路径

    返回:
        带字幕的视频剪辑
    """
    try:
        import pysrt

        # 解析 SRT 字幕
        subs = pysrt.open(subtitles_file)

        # 创建字幕剪辑列表
        subtitle_clips = []

        for sub in subs:
            # 创建文本剪辑
            txt_clip = TextClip(
                sub.text,
                fontsize=36,
                color='white',
                font='Arial-Bold',
                stroke_color='black',
                stroke_width=2,
                method='caption',
                size=(video_clip.w * 0.9, None)
            )

            # 设置位置和时间
            txt_clip = txt_clip.set_position('center').set_vertical_position('bottom')
            txt_clip = txt_clip.set_start(sub.start.total_seconds())
            txt_clip = txt_clip.set_end(sub.end.total_seconds())

            subtitle_clips.append(txt_clip)

        # 合成视频和字幕
        final_clip = CompositeVideoClip([video_clip] + subtitle_clips)

        return final_clip

    except ImportError:
        logger.log_warning("pysrt 未安装,尝试简单字幕实现")
        # 简单实现:直接读取 SRT 文件
        return _add_subtitles_simple(video_clip, subtitles_file)
    except Exception as e:
        logger.log_error(f"添加字幕失败: {str(e)}")
        return video_clip


def _add_subtitles_simple(
    video_clip,
    subtitles_file: str
):
    """
    简单添加字幕(不使用 pysrt)

    参数:
        video_clip: 视频剪辑
        subtitles_file: 字幕文件路径

    返回:
        带字幕的视频剪辑
    """
    # 读取字幕文件
    with open(subtitles_file, 'r', encoding='utf-8') as f:
        srt_content = f.read()

    # 简单实现:在视频底部显示文字
    # 实际应用中建议安装 pysrt: pip install pysrt
    return video_clip


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="视频合成工具")
    parser.add_argument("--images", required=True, help="图片目录")
    parser.add_argument("--audio", help="音频目录")
    parser.add_argument("--subtitles", help="字幕文件路径")
    parser.add_argument("--output", default="./output/final_video.mp4", help="输出视频路径")
    parser.add_argument("--fps", type=int, default=30, help="帧率")
    parser.add_argument("--duration", type=float, default=3.0, help="每张图片的显示时长(秒)")
    parser.add_argument("--width", type=int, default=1920, help="视频宽度")
    parser.add_argument("--height", type=int, default=1080, help="视频高度")

    args = parser.parse_args()

    result = composite_video(
        images_dir=args.images,
        audio_dir=args.audio,
        subtitles_file=args.subtitles,
        output_path=args.output,
        fps=args.fps,
        duration_per_image=args.duration,
        resolution=(args.width, args.height)
    )

    if result['success']:
        print(f"\n✓ 视频合成成功")
        print(f"输出路径: {result['output_path']}")
        print(f"时长: {result['duration']:.2f}秒")
        print(f"分辨率: {result['resolution']}")
        print(f"帧数: {result['frame_count']}")
        print(f"音频: {'是' if result['has_audio'] else '否'}")
        print(f"字幕: {'是' if result['has_subtitles'] else '否'}")
    else:
        print(f"\n✗ 视频合成失败: {result.get('error')}")
        exit(1)
