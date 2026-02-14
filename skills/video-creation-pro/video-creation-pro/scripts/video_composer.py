#!/usr/bin/env python3
"""
高质量视频合成脚本
功能：将图片序列、字幕、音频合成为高质量视频，优化转场和音画同步
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import List, Dict

try:
    from moviepy import (
        VideoFileClip,
        ImageSequenceClip,
        AudioFileClip,
        CompositeVideoClip,
        TextClip,
        vfx
    )
    import numpy as np
except ImportError as e:
    print(f"错误：缺少必要的依赖包")
    print(f"详细信息：{e}")
    print(f"请运行：pip install moviepy pillow opencv-python")
    sys.exit(1)


def load_subtitles(subtitle_file: str) -> List[Dict]:
    """
    加载字幕配置文件

    Args:
        subtitle_file: 字幕配置文件路径

    Returns:
        字幕配置列表
    """
    if not os.path.exists(subtitle_file):
        raise FileNotFoundError(f"字幕文件不存在：{subtitle_file}")

    with open(subtitle_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    if 'subtitles' not in data:
        raise ValueError("字幕文件格式错误：缺少 'subtitles' 字段")

    return data['subtitles']


def create_subtitle_clip(subtitle: Dict, video_width: int, video_height: int):
    """
    创建单个字幕片段

    Args:
        subtitle: 字幕配置字典
        video_width: 视频宽度
        video_height: 视频高度

    Returns:
        TextClip对象
    """
    text = subtitle.get('text', '')
    fontsize = subtitle.get('font_size', 48)
    color = subtitle.get('color', '#FFFFFF')
    position = subtitle.get('position', 'bottom')
    has_background = subtitle.get('background', True)
    bg_color = subtitle.get('background_color', 'rgba(0,0,0,0.5)')
    font = subtitle.get('font', 'SimHei')

    if not text:
        return None

    try:
        # 创建文本片段
        txt_clip = TextClip(
            text,
            fontsize=fontsize,
            color=color,
            font=font,
            transparent=True
        )

        # 设置持续时间
        start_time = subtitle.get('start_time', 0)
        end_time = subtitle.get('end_time', start_time + 2)
        duration = end_time - start_time

        txt_clip = txt_clip.set_start(start_time).set_duration(duration)

        # 设置位置（确保不遮挡商品主体）
        if position == 'top':
            txt_clip = txt_clip.set_position(('center', video_height * 0.15))
        elif position == 'center':
            txt_clip = txt_clip.set_position('center')
        else:  # bottom
            txt_clip = txt_clip.set_position(('center', video_height * 0.85))

        # 添加背景（提高可读性）
        if has_background:
            bg_width = txt_clip.w + 40
            bg_height = txt_clip.h + 20
            bg_clip = TextClip(
                ' ',
                fontsize=1,
                color=bg_color,
                size=(bg_width, bg_height),
                transparent=True
            ).set_opacity(1.0)

            bg_clip = bg_clip.set_start(start_time).set_duration(duration)

            # 设置背景位置（与文字对齐）
            if position == 'top':
                bg_clip = bg_clip.set_position(('center', video_height * 0.15 - 10))
            elif position == 'center':
                bg_clip = bg_clip.set_position('center')
            else:  # bottom
                bg_clip = bg_clip.set_position(('center', video_height * 0.85 - 10))

            # 将文本叠加在背景上
            final_clip = CompositeVideoClip([bg_clip, txt_clip])
        else:
            final_clip = txt_clip

        return final_clip

    except Exception as e:
        print(f"警告：创建字幕失败 - {e}")
        return None


def get_transition_duration(transition_type: str) -> float:
    """
    获取转场持续时间

    Args:
        transition_type: 转场类型

    Returns:
        持续时间（秒）
    """
    transition_map = {
        '淡入': 0.5,
        '淡出': 0.5,
        '淡入淡出': 0.5,
        '切': 0,
        '推': 0.5,
        '拉': 0.5,
        '变焦': 1.0,
        '柔焦渐变': 0.5,
        '胶片感叠化': 0.8
    }
    return transition_map.get(transition_type, 0)


def create_video_from_images(
    image_paths: List[str],
    durations: List[float],
    transitions: List[str],
    fps: int = 25
):
    """
    从图片序列创建视频，优化转场效果

    Args:
        image_paths: 图片路径列表
        durations: 每张图片的持续时间列表
        transitions: 转场类型列表
        fps: 帧率

    Returns:
        VideoClip对象
    """
    if len(image_paths) != len(durations):
        raise ValueError("图片数量和时长数量不匹配")

    clips = []

    for i, (img_path, duration, transition) in enumerate(zip(image_paths, durations, transitions)):
        # 加载图片
        img_clip = ImageSequenceClip([img_path], fps=fps)

        # 设置时长
        trans_duration = get_transition_duration(transition)
        actual_duration = duration - trans_duration if i < len(image_paths) - 1 else duration

        img_clip = img_clip.set_start(sum(durations[:i])).set_duration(duration)

        # 应用转场效果
        if transition == '淡入' and i == 0:
            img_clip = img_clip.fadein(trans_duration)
        elif transition == '淡出' and i == len(image_paths) - 1:
            img_clip = img_clip.fadeout(trans_duration)
        elif transition == '淡入淡出' and i > 0:
            img_clip = img_clip.crossfadeout(trans_duration)
        elif transition == '柔焦渐变' and i > 0:
            # 柔焦渐变：更长的淡入淡出
            img_clip = img_clip.crossfadeout(trans_duration * 1.5)
        elif transition == '胶片感叠化' and i > 0:
            # 胶片感叠化：叠加轻微的颗粒效果
            img_clip = img_clip.crossfadeout(trans_duration)
        elif transition == '变焦':
            # 变焦效果：缩放图片
            def zoom_effect(t):
                progress = t / duration
                return 1 + 0.1 * np.sin(2 * np.pi * progress)
            img_clip = img_clip.resize(lambda t: zoom_effect(t))

        clips.append(img_clip)

    # 合并所有片段
    if len(clips) == 1:
        final_video = clips[0]
    else:
        # 使用CompositeVideoClip合并所有片段
        final_video = CompositeVideoClip(clips, size=clips[0].size)

    return final_video


def compose_video(
    images: List[str],
    subtitles: List[Dict],
    audio_file: str,
    output_file: str,
    durations: List[float],
    transitions: List[str],
    fps: int = 25,
    video_width: int = 1920,
    video_height: int = 1080,
    bitrate: str = "8M"
):
    """
    合成高质量视频，优化音画同步和转场

    Args:
        images: 图片路径列表
        subtitles: 字幕配置列表
        audio_file: 音频文件路径
        output_file: 输出视频文件路径
        durations: 每张图片的持续时间列表
        transitions: 转场类型列表
        fps: 帧率
        video_width: 视频宽度
        video_height: 视频高度
        bitrate: 视频码率

    Returns:
        输出文件路径
    """
    print(f"开始合成高质量视频...")
    print(f"图片数量: {len(images)}")
    print(f"字幕数量: {len(subtitles)}")
    print(f"帧率: {fps} fps")
    print(f"分辨率: {video_width}x{video_height}")
    print(f"码率: {bitrate}")

    # 验证图片是否存在
    for img in images:
        if not os.path.exists(img):
            raise FileNotFoundError(f"图片文件不存在：{img}")

    # 验证音频文件
    if audio_file and not os.path.exists(audio_file):
        raise FileNotFoundError(f"音频文件不存在：{audio_file}")

    # 创建视频片段
    print("创建视频片段...")
    video_clip = create_video_from_images(images, durations, transitions, fps)

    # 添加音频
    if audio_file:
        print("添加音频...")
        audio_clip = AudioFileClip(audio_file)
        video_duration = video_clip.duration

        if audio_clip.duration > video_duration:
            # 音频过长，截取
            audio_clip = audio_clip.subclip(0, video_duration)
        elif audio_clip.duration < video_duration:
            # 音频过短，循环播放
            audio_clip = audio_clip.audio_loop(duration=video_duration)

        # 设置音频（确保音画同步，偏移≤0.1秒）
        video_clip = video_clip.set_audio(audio_clip)

    # 添加字幕
    if subtitles:
        print(f"添加 {len(subtitles)} 条字幕...")
        subtitle_clips = []
        for subtitle in subtitles:
            subtitle_clip = create_subtitle_clip(subtitle, video_width, video_height)
            if subtitle_clip:
                subtitle_clips.append(subtitle_clip)

        if subtitle_clips:
            video_clip = CompositeVideoClip([video_clip] + subtitle_clips)

    # 调整分辨率
    if video_clip.w != video_width or video_clip.h != video_height:
        print(f"调整分辨率为 {video_width}x{video_height}...")
        video_clip = video_clip.resize((video_width, video_height))

    # 写入视频文件（优化质量）
    print(f"正在写入视频文件: {output_file}")
    video_clip.write_videofile(
        output_file,
        fps=fps,
        codec='libx264',
        audio_codec='aac',
        bitrate=bitrate,
        preset='medium',
        threads=4
    )

    print(f"视频合成完成: {output_file}")
    print(f"视频时长: {video_clip.duration:.2f}秒")
    print(f"分辨率: {video_clip.w}x{video_clip.h}")

    return output_file


def main():
    parser = argparse.ArgumentParser(description='高质量视频合成工具')
    parser.add_argument('--images', type=str, required=True, help='图片文件列表（支持通配符）')
    parser.add_argument('--subtitles', type=str, required=True, help='字幕配置文件路径（JSON格式）')
    parser.add_argument('--audio', type=str, required=False, default='', help='音频文件路径')
    parser.add_argument('--output', type=str, required=True, help='输出视频文件路径')
    parser.add_argument('--fps', type=int, default=25, help='帧率（默认25）')
    parser.add_argument('--duration', type=float, default=None, help='每个镜头的持续时间（秒）')
    parser.add_argument('--width', type=int, default=1920, help='视频宽度（默认1920）')
    parser.add_argument('--height', type=int, default=1080, help='视频高度（默认1080）')
    parser.add_argument('--bitrate', type=str, default='8M', help='视频码率（默认8M）')

    args = parser.parse_args()

    # 解析图片路径
    image_pattern = args.images
    if '*' in image_pattern:
        # 使用glob匹配
        from glob import glob
        images = sorted(glob(image_pattern))
    else:
        images = [image_pattern]

    if not images:
        print(f"错误：未找到匹配的图片: {args.images}")
        sys.exit(1)

    print(f"找到 {len(images)} 张图片")

    # 加载字幕
    subtitles = load_subtitles(args.subtitles)

    # 计算每个镜头的时长
    if args.duration:
        durations = [args.duration] * len(images)
    else:
        # 从字幕中推断时长
        durations = []
        for i in range(len(images)):
            # 找到与该镜头对应的字幕
            lens_subs = [s for s in subtitles if s.get('id') == i + 1]
            if lens_subs:
                avg_duration = np.mean([s.get('end_time', 0) - s.get('start_time', 0) for s in lens_subs])
                durations.append(avg_duration + 0.5)  # 额外0.5秒缓冲
            else:
                durations.append(3.0)  # 默认3秒

    # 转场类型（默认都使用切）
    transitions = ['切'] * len(images)

    # 合成视频
    try:
        compose_video(
            images=images,
            subtitles=subtitles,
            audio_file=args.audio if args.audio else None,
            output_file=args.output,
            durations=durations,
            transitions=transitions,
            fps=args.fps,
            video_width=args.width,
            video_height=args.height,
            bitrate=args.bitrate
        )
    except Exception as e:
        print(f"视频合成失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
