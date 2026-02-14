#!/usr/bin/env python3
"""
视频分辨率调整脚本
使用 FFmpeg 调整视频分辨率
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


def scale_video(input_path, output_path, width, height, maintain_aspect=True):
    """
    调整视频分辨率

    参数:
        input_path: 输入视频文件路径
        output_path: 输出视频文件路径
        width: 目标宽度
        height: 目标高度
        maintain_aspect: 是否保持宽高比（默认 True）
    """
    check_file_exists(input_path)

    # 构建缩放滤镜参数
    if maintain_aspect:
        # 保持宽高比，使用 -2 确保是偶数
        if width > 0 and height > 0:
            scale_filter = f"scale={width}:{height}:force_original_aspect_ratio=decrease"
        elif width > 0:
            scale_filter = f"scale={width}:-2"
        elif height > 0:
            scale_filter = f"scale=-2:{height}"
        else:
            print("错误：必须指定宽度或高度")
            return False
    else:
        # 强制缩放到指定尺寸
        scale_filter = f"scale={width}:{height}"

    # 构建 FFmpeg 命令
    cmd = [
        "ffmpeg",
        "-i", input_path,
        "-vf", scale_filter,
        "-c:a", "copy",  # 音频直接复制
        "-y",  # 覆盖输出文件
        output_path
    ]

    print(f"正在调整视频分辨率: {input_path} -> {output_path}")
    print(f"目标尺寸: {width}x{height}, 保持宽高比: {maintain_aspect}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("视频分辨率调整完成！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"调整失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False


def main():
    parser = argparse.ArgumentParser(description="视频分辨率调整工具")
    parser.add_argument("--input", required=True, help="输入视频文件路径")
    parser.add_argument("--output", required=True, help="输出视频文件路径")
    parser.add_argument("--width", type=int, help="目标宽度")
    parser.add_argument("--height", type=int, help="目标高度")
    parser.add_argument("--maintain-aspect", action="store_true", default=True,
                       help="保持宽高比（默认启用）")

    args = parser.parse_args()

    if args.width is None and args.height is None:
        print("错误：必须指定宽度或高度")
        sys.exit(1)

    success = scale_video(
        args.input,
        args.output,
        args.width,
        args.height,
        args.maintain_aspect
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
