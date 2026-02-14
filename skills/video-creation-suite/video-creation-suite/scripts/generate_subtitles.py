#!/usr/bin/env python3
"""
生成分镜字幕和旁白脚本
根据分镜脚本生成字幕文件和旁白文本
"""

import json
import os
from pathlib import Path


def generate_subtitles(script_path: str, output_srt: str):
    """
    生成SRT字幕文件

    参数:
        script_path: 分镜脚本路径
        output_srt: 输出SRT文件路径
    """
    with open(script_path, 'r', encoding='utf-8') as f:
        script = json.load(f)

    scenes = script['scenes']

    with open(output_srt, 'w', encoding='utf-8') as f:
        current_time = 0

        for idx, scene in enumerate(scenes, 1):
            # 计算时间范围
            start_time = current_time
            end_time = start_time + scene['duration']

            # 格式化SRT时间 (HH:MM:SS,mmm)
            def format_time(seconds):
                hours = int(seconds // 3600)
                minutes = int((seconds % 3600) // 60)
                secs = int(seconds % 60)
                millisecs = int((seconds - int(seconds)) * 1000)
                return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"

            start_str = format_time(start_time)
            end_str = format_time(end_time)

            # 写入SRT格式
            f.write(f"{idx}\n")
            f.write(f"{start_str} --> {end_str}\n")
            f.write(f"{scene['subtitle']}\n")
            f.write(f"{scene['narration']}\n")
            f.write("\n")

            # 更新当前时间
            current_time = end_time

    print(f"✓ 字幕文件已生成: {output_srt}")


def generate_narration_text(script_path: str, output_txt: str):
    """
    生成旁白文本文件

    参数:
        script_path: 分镜脚本路径
        output_txt: 输出文本文件路径
    """
    with open(script_path, 'r', encoding='utf-8') as f:
        script = json.load(f)

    scenes = script['scenes']

    with open(output_txt, 'w', encoding='utf-8') as f:
        f.write(f"《{script['title']}》旁白文本\n\n")

        for idx, scene in enumerate(scenes, 1):
            f.write(f"[{scene['duration']}s] {scene['subtitle']}\n")
            f.write(f"{scene['narration']}\n\n")

    print(f"✓ 旁白文本已生成: {output_txt}")


if __name__ == "__main__":
    # 脚本路径
    script_path = "./output/script.json"

    # 输出路径
    output_srt = "./output/subtitles/subtitles.srt"
    output_txt = "./output/subtitles/narration.txt"

    # 确保目录存在
    os.makedirs(os.path.dirname(output_srt), exist_ok=True)

    # 生成字幕
    generate_subtitles(script_path, output_srt)

    # 生成旁白文本
    generate_narration_text(script_path, output_txt)
