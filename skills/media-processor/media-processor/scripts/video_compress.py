#!/usr/bin/env python3
"""
视频压缩脚本
使用 FFmpeg 压缩视频，通过 CRF 或码率控制文件大小
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


def compress_video(input_path, output_path, crf=None, bitrate=None, preset="medium"):
    """
    压缩视频

    参数:
        input_path: 输入视频文件路径
        output_path: 输出视频文件路径
        crf: CRF 值（18-34，数值越小质量越高）
        bitrate: 目标码率（如 2M, 1500k）
        preset: 编码预设（ultrafast, superfast, veryfast, faster, fast, medium, slow, slower, veryslow）
    """
    check_file_exists(input_path)

    if crf is None and bitrate is None:
        print("错误：必须指定 crf 或 bitrate 中的一个")
        sys.exit(1)

    # 构建 FFmpeg 命令
    cmd = [
        "ffmpeg",
        "-i", input_path,
        "-c:v", "libx264",
        "-preset", preset,
    ]

    # 添加质量控制参数
    if crf is not None:
        cmd.extend(["-crf", str(crf)])
        print(f"使用 CRF 模式: {crf}")
    if bitrate is not None:
        cmd.extend(["-b:v", bitrate])
        print(f"使用码率模式: {bitrate}")

    cmd.extend([
        "-c:a", "aac",
        "-b:a", "128k",
        "-y",  # 覆盖输出文件
        output_path
    ])

    print(f"正在压缩视频: {input_path} -> {output_path}")
    print(f"编码预设: {preset}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("视频压缩完成！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"压缩失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False


def main():
    parser = argparse.ArgumentParser(description="视频压缩工具")
    parser.add_argument("--input", required=True, help="输入视频文件路径")
    parser.add_argument("--output", required=True, help="输出视频文件路径")
    parser.add_argument("--crf", type=int, help="CRF 值（18-34，数值越小质量越高）")
    parser.add_argument("--bitrate", help="目标码率（如 2M, 1500k）")
    parser.add_argument("--preset", default="medium",
                       help="编码预设（默认 medium）")

    args = parser.parse_args()

    # 验证 CRF 范围
    if args.crf is not None and (args.crf < 18 or args.crf > 34):
        print("警告：CRF 值建议在 18-34 之间")

    success = compress_video(
        args.input,
        args.output,
        args.crf,
        args.bitrate,
        args.preset
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
