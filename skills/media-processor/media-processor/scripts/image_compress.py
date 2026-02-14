#!/usr/bin/env python3
"""
图像压缩脚本
使用 ImageMagick 压缩图像，减小文件体积
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


def compress_image(input_path, output_path, quality=85, method="standard"):
    """
    压缩图像

    参数:
        input_path: 输入图像文件路径
        output_path: 输出图像文件路径
        quality: 图像质量 1-100（默认 85）
        method: 压缩方法（standard, progressive, minimal）
            - standard: 标准压缩
            - progressive: 渐进式 JPEG（适合网络传输）
            - minimal: 最小体积（使用 4:2:0 色度采样）
    """
    check_file_exists(input_path)

    # 验证质量参数
    if quality < 1 or quality > 100:
        print("错误：质量参数必须在 1-100 之间")
        return False

    # 构建 ImageMagick 命令
    try:
        cmd = ["magick", input_path]
    except:
        cmd = ["convert", input_path]

    # 添加质量参数
    cmd.extend(["-quality", str(quality)])

    # 根据压缩方法添加参数
    if method == "progressive":
        cmd.extend(["-interlace", "Plane"])
    elif method == "minimal":
        cmd.extend(["-strip", "-sampling-factor", "4:2:0"])
    elif method == "standard":
        cmd.extend(["-strip"])

    cmd.append(output_path)

    print(f"正在压缩图像: {input_path} -> {output_path}")
    print(f"质量: {quality}, 压缩方法: {method}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("图像压缩完成！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"压缩失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False


def main():
    parser = argparse.ArgumentParser(description="图像压缩工具")
    parser.add_argument("--input", required=True, help="输入图像文件路径")
    parser.add_argument("--output", required=True, help="输出图像文件路径")
    parser.add_argument("--quality", type=int, default=85, help="图像质量 1-100（默认 85）")
    parser.add_argument("--method", default="standard",
                       choices=["standard", "progressive", "minimal"],
                       help="压缩方法（standard, progressive, minimal，默认 standard）")

    args = parser.parse_args()

    success = compress_image(
        args.input,
        args.output,
        args.quality,
        args.method
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
