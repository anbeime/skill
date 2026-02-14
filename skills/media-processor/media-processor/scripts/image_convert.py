#!/usr/bin/env python3
"""
图像格式转换脚本
使用 ImageMagick 将图像从一种格式转换为另一种格式
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


def convert_image(input_path, output_path, output_format, quality=85):
    """
    转换图像格式

    参数:
        input_path: 输入图像文件路径
        output_path: 输出图像文件路径
        output_format: 输出格式（如 jpg, png, gif, webp）
        quality: 图像质量 1-100（默认 85）
    """
    check_file_exists(input_path)

    # 验证质量参数
    if quality < 1 or quality > 100:
        print("错误：质量参数必须在 1-100 之间")
        return False

    # 构建 ImageMagick 命令
    # 使用 magick 命令（新版本）或 convert 命令（旧版本）
    try:
        cmd = ["magick", input_path, "-quality", str(quality), output_path]
    except:
        cmd = ["convert", input_path, "-quality", str(quality), output_path]

    print(f"正在转换图像: {input_path} -> {output_path}")
    print(f"目标格式: {output_format}, 质量: {quality}")

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("图像转换完成！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"转换失败: {e}")
        print(f"错误输出: {e.stderr}")
        return False


def main():
    parser = argparse.ArgumentParser(description="图像格式转换工具")
    parser.add_argument("--input", required=True, help="输入图像文件路径")
    parser.add_argument("--output", required=True, help="输出图像文件路径")
    parser.add_argument("--format", required=True, help="输出格式（如 jpg, png, gif, webp）")
    parser.add_argument("--quality", type=int, default=85, help="图像质量 1-100（默认 85）")

    args = parser.parse_args()

    # 确保输出文件扩展名与格式一致
    if not args.output.lower().endswith(f".{args.format.lower()}"):
        print(f"警告：输出文件扩展名可能与指定格式不匹配")
        print(f"建议：输出文件应以 .{args.format.lower()} 结尾")

    # 处理 PNG 转换为 JPG 的透明背景问题
    if args.format.lower() in ["jpg", "jpeg"]:
        print("提示：PNG 转 JPG 时，透明背景会被填充为白色")

    success = convert_image(
        args.input,
        args.output,
        args.format,
        args.quality
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
