#!/usr/bin/env python3
"""
视频合成主脚本
整合图片、音频、字幕,合成最终视频
"""

import os
import sys
from typing import Dict, Any, List
import json


def compose_video(project_config: Dict[str, Any],
                 output_file: str) -> Dict[str, Any]:
    """
    合成视频

    参数:
        project_config: 项目配置,包含素材路径和参数
        output_file: 输出视频文件路径

    返回:
        合成结果字典
    """
    results = {
        'success': True,
        'output_file': output_file,
        'errors': [],
        'warnings': []
    }

    try:
        from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, CompositeVideoClip, concatenate_videoclips
        from moviepy.config import change_settings
        change_settings({"IMAGEMAGICK_BINARY": "/usr/bin/convert"})

        # 获取素材路径
        images_dir = project_config.get('images_dir', './output/images')
        audio_file = project_config.get('audio_file', './output/audio/merged_audio.wav')
        subtitle_file = project_config.get('subtitle_file', './output/subtitles/subtitle.srt')

        # 获取视频参数
        width = project_config.get('width', 1920)
        height = project_config.get('height', 1080)
        fps = project_config.get('fps', 25)
        duration = project_config.get('duration', 30)
        bitrate = project_config.get('bitrate', '8000k')

        # 获取镜头列表
        shots = project_config.get('shots', [])

        if not shots:
            raise ValueError("项目中没有镜头数据")

        # 创建视频片段列表
        video_clips = []

        for i, shot in enumerate(shots):
            shot_id = shot.get('shot_id', f'L{i+1:02d}')
            image_file = os.path.join(images_dir, f"shot_{shot_id}.jpg")
            shot_duration = shot.get('duration', 3.0)
            transition = shot.get('transition', 'cut')

            # 检查图片是否存在
            if not os.path.exists(image_file):
                raise FileNotFoundError(f"图片文件不存在: {image_file}")

            # 加载图片并创建视频片段
            img_clip = ImageClip(image_file).set_duration(shot_duration).set_fps(fps)

            # 应用转场效果
            if transition == 'fade':
                img_clip = img_clip.fadein(0.3).fadeout(0.3)
            elif transition == 'crossfade':
                # 交叉淡入淡出需要特殊处理
                pass

            video_clips.append(img_clip)

        # 合并视频片段
        final_video = concatenate_videoclips(video_clips, method="compose")

        # 添加音频
        if os.path.exists(audio_file):
            audio_clip = AudioFileClip(audio_file)
            # 调整音频长度以匹配视频
            if audio_clip.duration > final_video.duration:
                audio_clip = audio_clip.subclip(0, final_video.duration)
            elif audio_clip.duration < final_video.duration:
                # 音频长度不足,循环音频
                audio_clip = audio_clip.loop(duration=final_video.duration)

            final_video = final_video.set_audio(audio_clip)

        # 添加字幕
        if os.path.exists(subtitle_file):
            from moviepy.editor import TextClip, CompositeVideoClip

            # 读取字幕文件
            subtitles = parse_subtitle_file(subtitle_file)

            # 创建字幕片段
            subtitle_clips = []
            for sub in subtitles:
                txt_clip = TextClip(sub['text'], fontsize=24, color='white', font='Arial')
                txt_clip = txt_clip.set_position('center').set_start(sub['start']).set_duration(sub['end'] - sub['start'])
                subtitle_clips.append(txt_clip)

            # 叠加字幕
            final_video = CompositeVideoClip([final_video] + subtitle_clips)

        # 确保输出目录存在
        output_dir = os.path.dirname(output_file)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # 写入视频文件
        final_video.write_videofile(
            output_file,
            fps=fps,
            codec='libx264',
            audio_codec='aac',
            bitrate=bitrate,
            preset='medium'
        )

        print(f"✅ 视频合成成功: {output_file}")

    except Exception as e:
        results['success'] = False
        results['errors'].append(str(e))
        print(f"❌ 视频合成失败: {str(e)}")

    return results


def parse_subtitle_file(subtitle_file: str) -> List[Dict[str, Any]]:
    """
    解析字幕文件

    参数:
        subtitle_file: 字幕文件路径

    返回:
        字幕条目列表
    """
    # TODO: 实现字幕文件解析
    # 这里需要解析SRT或ASS格式字幕文件

    # 临时返回空列表,需要替换为实际实现
    return []


def validate_project_config(project_config: Dict[str, Any]) -> Dict[str, Any]:
    """
    验证项目配置

    参数:
        project_config: 项目配置

    返回:
        验证结果字典
    """
    result = {
        'valid': True,
        'errors': [],
        'warnings': []
    }

    # 检查必需字段
    required_fields = ['images_dir', 'shots', 'width', 'height', 'fps', 'duration']
    for field in required_fields:
        if field not in project_config:
            result['errors'].append(f"缺少必需字段: {field}")

    # 检查素材目录
    images_dir = project_config.get('images_dir', '')
    if images_dir and not os.path.exists(images_dir):
        result['warnings'].append(f"图片目录不存在: {images_dir}")

    # 检查镜头数据
    shots = project_config.get('shots', [])
    if not shots:
        result['errors'].append("项目中没有镜头数据")

    # 检查每个镜头
    for i, shot in enumerate(shots):
        if 'shot_id' not in shot:
            result['warnings'].append(f"镜头{i+1}缺少shot_id")
        if 'duration' not in shot:
            result['errors'].append(f"镜头{i+1}缺少duration")

    # 检查视频参数
    width = project_config.get('width', 0)
    height = project_config.get('height', 0)
    fps = project_config.get('fps', 0)

    if width not in [1920, 1080, 720]:
        result['warnings'].append(f"宽度{width}可能不是标准分辨率")
    if height not in [1080, 1920, 720]:
        result['warnings'].append(f"高度{height}可能不是标准分辨率")
    if not (20 <= fps <= 60):
        result['warnings'].append(f"帧率{fps}可能不在合理范围(20-60)")

    if result['errors']:
        result['valid'] = False

    return result


def print_validation_result(result: Dict[str, Any]):
    """
    打印验证结果

    参数:
        result: 验证结果字典
    """
    if result['valid']:
        print("✅ 项目配置验证通过")
    else:
        print("❌ 项目配置验证失败")

    if result['errors']:
        print("\n错误:")
        for error in result['errors']:
            print(f"  - {error}")

    if result['warnings']:
        print("\n警告:")
        for warning in result['warnings']:
            print(f"  - {warning}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='视频合成脚本')
    parser.add_argument('--config', type=str, required=True,
                       help='项目配置JSON文件路径')
    parser.add_argument('--output', type=str, required=True,
                       help='输出视频文件路径')

    args = parser.parse_args()

    # 读取项目配置
    with open(args.config, 'r', encoding='utf-8') as f:
        project_config = json.load(f)

    # 验证项目配置
    validation_result = validate_project_config(project_config)
    print_validation_result(validation_result)

    if not validation_result['valid']:
        sys.exit(1)

    # 合成视频
    results = compose_video(
        project_config=project_config,
        output_file=args.output
    )

    # 返回状态码
    sys.exit(0 if results['success'] else 1)
