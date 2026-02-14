#!/usr/bin/env python3
"""
文本转语音（使用 pyttsx3）
"""
import argparse
import os
import pyttsx3


def text_to_speech(txt_path: str, output_path: str, voice_rate: int = 150) -> None:
    """
    将文本转换为语音文件

    Args:
        txt_path: 文本文件路径
        output_path: 输出 wav 文件路径
        voice_rate: 语音速率（默认 150）
    """
    print(f"正在进行文本转语音: {txt_path}")

    # 读取文本
    with open(txt_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # 限制文本长度，避免生成过大的语音文件
    max_length = 50000  # 限制为前 50000 个字符
    if len(text) > max_length:
        text = text[:max_length]
        print(f"警告: 文本过长，仅使用前 {max_length} 个字符")

    # 初始化语音引擎
    engine = pyttsx3.init()

    # 设置语音速率
    engine.setProperty('rate', voice_rate)

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # 保存为语音文件
    try:
        engine.save_to_file(text, output_path)
        engine.runAndWait()
        print(f"语音文件已保存到: {output_path}")
    except Exception as e:
        raise Exception(f"语音合成失败: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description='文本转语音')
    parser.add_argument('--txt', required=True, help='文本文件路径')
    parser.add_argument('--output', required=True, help='输出 wav 文件路径')
    parser.add_argument('--rate', type=int, default=150, help='语音速率（默认 150）')
    args = parser.parse_args()

    text_to_speech(args.txt, args.output, args.rate)


if __name__ == '__main__':
    main()
