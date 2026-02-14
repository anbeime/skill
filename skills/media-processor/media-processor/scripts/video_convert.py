#!/usr/bin/env python3
"""
视频格式转换脚本
使用 FFmpeg 将视频从一种格式转换为另一种格式
"""

import argparse
import subprocess
import sys
import os


def check_file_exists(file_path):
    """检查文件是否存在"""
    if not os.path.exists(file_path):
        print(f"错误：输入文件不存在: {file_path}")
        sys.exit(1)


def convert_video(input_path, output_path, output_format, video_codec="libx264", audio_codec="aac"):
    """
    转换视频格式

    参数:
        input_path: 输入视频文件路径
        output_path: 输出视频文件路径
        output_format: 输出格式（如 mp4, avi, mov, mkv）
        video_codec: 视频编码器（默认 libx264）
        audio_codec: 音频编码器（默认 aac）
    """
    check_file_exists(input_path)

    # 构建 FFmpeg 命令
    cmd = [
        "ffmpeg",
        "-i", input_path,
        "-c:v", video_codec,
        "-c:a", audio_codec,
        "-y",  # 覆盖输出文件
        output_path
    ]

    print(f"正在转换视频: {input_path} -> {output_path}")
    print(f"视频编码器: {video_codec}, 音频编码器: {audio_codec}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("视频转换完成！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"转换失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False


def main():
    parser = argparse.ArgumentParser(description="视频格式转换工具")
    parser.add_argument("--input", required=True, help="输入视频文件路径")
    parser.add_argument("--output", required=True, help="输出视频文件路径")
    parser.add_argument("--format", required=True, help="输出格式（如 mp4, avi, mov, mkv）")
    parser.add_argument("--video-codec", default="libx264", help="视频编码器（默认 libx264）")
    parser.add_argument("--audio-codec", default="aac", help="音频编码器（默认 aac）")

    args = parser.parse_args()

    # 确保输出文件扩展名与格式一致
    if not args.output.lower().endswith(f".{args.format.lower()}"):
        print(f"警告：输出文件扩展名可能与指定格式不匹配")
        print(f"建议：输出文件应以 .{args.format.lower()} 结尾")

    success = convert_video(
        args.input,
        args.output,
        args.format,
        args.video_codec,
        args.audio_codec
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
