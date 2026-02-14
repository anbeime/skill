#!/usr/bin/env python3
"""
简单旁白音频生成脚本
使用系统TTS或占位音频
"""

import os
import json
import subprocess


def generate_narration_audio(script_path: str, output_dir: str):
    """
    生成旁白音频（静音占位）

    参数:
        script_path: 分镜脚本路径
        output_dir: 输出目录
    """
    with open(script_path, 'r', encoding='utf-8') as f:
        script = json.load(f)

    total_duration = script['duration']

    print(f"正在生成旁白音频（静音占位）...")
    print(f"总时长: {total_duration}秒")
    print(f"注意: 实际使用时需要替换为真实的旁白音频")

    output_path = os.path.join(output_dir, "narration.mp3")

    # 使用ffmpeg生成静音音频（作为占位）
    cmd = [
        "ffmpeg",
        "-f", "lavfi",
        "-i", f"anullsrc=r=44100:cl=mono",
        "-t", str(total_duration),
        "-q:a", "9",
        "-y",
        output_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        if result.returncode == 0:
            # 获取文件大小
            size = os.path.getsize(output_path)

            print(f"\n✓ 旁白音频已生成: {output_path}")
            print(f"大小: {size / 1024:.1f} KB")
            print(f"注意: 这是静音占位音频，实际使用时需要替换为真实的旁白")
        else:
            print(f"\n✗ 旁白音频生成失败")
            print(f"错误: {result.stderr}")
            raise Exception(f"ffmpeg失败: {result.stderr}")

    except Exception as e:
        print(f"\n✗ 旁白音频生成失败: {str(e)}")
        raise


if __name__ == "__main__":
    script_path = "./output/script.json"
    output_dir = "./output/audio"

    os.makedirs(output_dir, exist_ok=True)

    generate_narration_audio(script_path, output_dir)
