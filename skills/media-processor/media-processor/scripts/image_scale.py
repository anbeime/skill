#!/usr/bin/env python3
"""
图像缩放脚本
使用 ImageMagick 调整图像尺寸
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


def scale_image(input_path, output_path, width, height, maintain_aspect=True, filter_type="lanczos"):
    """
    缩放图像

    参数:
        input_path: 输入图像文件路径
        output_path: 输出图像文件路径
        width: 目标宽度
        height: 目标高度
        maintain_aspect: 是否保持宽高比（默认 True）
        filter_type: 缩放滤镜（lanczos, bilinear, nearest, gaussian）
    """
    check_file_exists(input_path)

    # 构建缩放参数
    if maintain_aspect:
        # 保持宽高比
        if width > 0 and height > 0:
            scale_param = f"{width}x{height}"
        elif width > 0:
            scale_param = f"{width}"
        elif height > 0:
            scale_param = f"x{height}"
        else:
            print("错误：必须指定宽度或高度")
            return False
    else:
        # 强制缩放到指定尺寸
        scale_param = f"{width}x{height}!"

    # 构建 ImageMagick 命令
    try:
        cmd = ["magick", input_path, "-filter", filter_type, "-resize", scale_param, output_path]
    except:
        cmd = ["convert", input_path, "-filter", filter_type, "-resize", scale_param, output_path]

    print(f"正在缩放图像: {input_path} -> {output_path}")
    print(f"目标尺寸: {width}x{height}, 保持宽高比: {maintain_aspect}, 滤镜: {filter_type}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("图像缩放完成！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"缩放失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False


def main():
    parser = argparse.ArgumentParser(description="图像缩放工具")
    parser.add_argument("--input", required=True, help="输入图像文件路径")
    parser.add_argument("--output", required=True, help="输出图像文件路径")
    parser.add_argument("--width", type=int, help="目标宽度")
    parser.add_argument("--height", type=int, help="目标高度")
    parser.add_argument("--maintain-aspect", action="store_true", default=True,
                       help="保持宽高比（默认启用）")
    parser.add_argument("--filter", default="lanczos",
                       help="缩放滤镜（lanczos, bilinear, nearest, gaussian，默认 lanczos）")

    args = parser.parse_args()

    if args.width is None and args.height is None:
        print("错误：必须指定宽度或高度")
        sys.exit(1)

    success = scale_image(
        args.input,
        args.output,
        args.width,
        args.height,
        args.maintain_aspect,
        args.filter
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
