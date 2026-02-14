#!/usr/bin/env python3
"""
合成视频脚本
根据分镜脚本合成最终视频
"""

import os
import sys
import json
import subprocess


def composite_video_from_script(script_path: str, images_dir: str, audio_dir: str, subtitles_path: str, output_path: str):
    """
    根据分镜脚本合成视频

    参数:
        script_path: 分镜脚本路径
        images_dir: 图片目录
        audio_dir: 音频目录
        subtitles_path: 字幕文件路径
        output_path: 输出视频路径
    """
    # 读取分镜脚本
    with open(script_path, 'r', encoding='utf-8') as f:
        script = json.load(f)

    print(f"正在合成视频: {script['title']}")
    print(f"分辨率: {script['resolution'][0]}x{script['resolution'][1]}")
    print(f"帧率: {script['fps']}")
    print(f"总时长: {script['duration']}秒")
    print(f"场景数: {len(script['scenes'])}\n")

    # 计算每张图片的显示时长
    scenes = script['scenes']
    fps = script['fps']
    resolution = script['resolution']

    # 创建临时文件列表
    concat_file = "/tmp/concat_list.txt"
    with open(concat_file, 'w') as f:
        for scene in scenes:
            # 使用绝对路径
            image_path = os.path.abspath(os.path.join(images_dir, scene['image']))
            # 每张图片显示指定的时长
            duration = scene['duration']
            # 使用loop和t参数来控制时长
            f.write(f"file '{image_path}'\n")
            f.write(f"duration {duration}\n")

    # 步骤1: 从图片序列生成视频
    print("步骤1: 从图片序列生成视频...")
    temp_video = "/tmp/temp_video.mp4"

    cmd1 = [
        "ffmpeg",
        "-f", "concat",
        "-safe", "0",
        "-i", concat_file,
        "-vf", f"fps={fps},scale={resolution[0]}:{resolution[1]}:force_original_aspect_ratio=decrease,pad={resolution[0]}:{resolution[1]}:(ow-iw)/2:(oh-ih)/2",
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-pix_fmt", "yuv420p",
        "-y",
        temp_video
    ]

    try:
        result = subprocess.run(cmd1, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            print(f"✗ 步骤1失败")
            print(f"错误: {result.stderr}")
            raise Exception(f"FFmpeg步骤1失败: {result.stderr}")
        print("✓ 步骤1完成\n")
    except subprocess.TimeoutExpired:
        print("✗ 步骤1超时")
        raise Exception("FFmpeg步骤1超时")
    except Exception as e:
        print(f"✗ 步骤1失败: {str(e)}")
        raise

    # 步骤2: 添加音频
    print("步骤2: 添加音频...")

    # 合并背景音乐和旁白
    temp_audio = "/tmp/temp_audio.mp3"

    bgm_path = os.path.join(audio_dir, "background_music.mp3")
    narration_path = os.path.join(audio_dir, "narration.mp3")

    if os.path.exists(bgm_path) and os.path.exists(narration_path):
        # 混合两个音频
        cmd2a = [
            "ffmpeg",
            "-i", bgm_path,
            "-i", narration_path,
            "-filter_complex", "[0:a]volume=0.3[a0];[1:a]volume=1.0[a1];[a0][a1]amix=inputs=2:duration=first",
            "-y",
            temp_audio
        ]
        result = subprocess.run(cmd2a, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            print(f"⚠️  音频混合失败，仅使用旁白: {result.stderr}")
            temp_audio = narration_path
    elif os.path.exists(narration_path):
        temp_audio = narration_path
    else:
        temp_audio = None

    # 步骤3: 合并视频和音频
    print("步骤3: 合并视频和音频...")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if temp_audio:
        cmd3 = [
            "ffmpeg",
            "-i", temp_video,
            "-i", temp_audio,
            "-c:v", "copy",
            "-c:a", "aac",
            "-shortest",
            "-y",
            output_path
        ]
    else:
        cmd3 = [
            "ffmpeg",
            "-i", temp_video,
            "-c:v", "copy",
            "-y",
            output_path
        ]

    try:
        result = subprocess.run(cmd3, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            print(f"✗ 步骤3失败")
            print(f"错误: {result.stderr}")
            raise Exception(f"FFmpeg步骤3失败: {result.stderr}")
        print("✓ 步骤3完成\n")
    except subprocess.TimeoutExpired:
        print("✗ 步骤3超时")
        raise Exception("FFmpeg步骤3超时")
    except Exception as e:
        print(f"✗ 步骤3失败: {str(e)}")
        raise

    # 步骤4: 添加字幕（可选）
    if subtitles_path and os.path.exists(subtitles_path):
        print("步骤4: 添加字幕...")
        final_output = output_path.replace(".mp4", "_subtitled.mp4")

        cmd4 = [
            "ffmpeg",
            "-i", output_path,
            "-vf", f"subtitles='{subtitles_path}':force_style='Fontsize=24,PrimaryColour=&H00FFFFFF,BackColour=&H80000000,BorderStyle=1'",
            "-c:a", "copy",
            "-y",
            final_output
        ]

        try:
            result = subprocess.run(cmd4, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                print(f"⚠️  字幕添加失败: {result.stderr}")
                print("继续使用未添加字幕的视频\n")
            else:
                print("✓ 字幕添加完成\n")
                output_path = final_output
        except Exception as e:
            print(f"⚠️  字幕添加失败: {str(e)}")
            print("继续使用未添加字幕的视频\n")

    # 清理临时文件
    try:
        os.remove(concat_file)
        os.remove(temp_video)
        if temp_audio and temp_audio.startswith("/tmp"):
            os.remove(temp_audio)
    except:
        pass

    # 检查输出文件
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path)
        print(f"\n✓ 视频合成成功!")
        print(f"输出路径: {output_path}")
        print(f"文件大小: {file_size / 1024 / 1024:.1f} MB")
    else:
        print(f"\n✗ 视频合成失败")
        raise Exception("输出文件不存在")


if __name__ == "__main__":
    script_path = "./output/script.json"
    images_dir = "./output/images"
    audio_dir = "./output/audio"
    subtitles_path = "./output/subtitles/subtitles.srt"
    output_path = "./output/final/three_body_video.mp4"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    try:
        composite_video_from_script(script_path, images_dir, audio_dir, subtitles_path, output_path)
    except Exception as e:
        print(f"\n✗ 视频合成失败: {str(e)}")
        sys.exit(1)
