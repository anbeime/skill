#!/usr/bin/env python3
"""
音频生成脚本
调用TTS接口,根据文本生成旁白/配音音频
"""

import os
import sys
from typing import Dict, Any, List
import json
from .error_handler import retry_on_failure, ErrorLogger

logger = ErrorLogger()


@retry_on_failure(max_retries=2, retry_delay=0.5)
def generate_audio(narration_data: Dict[str, Any],
                   output_dir: str = "./output/audio",
                   voice_style: str = "male_young") -> Dict[str, Any]:
    """
    根据旁白数据生成音频

    参数:
        narration_data: 旁白数据,包含文本和音色要求
        output_dir: 输出目录
        voice_style: 音色风格

    返回:
        生成结果字典,包含成功/失败信息
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)

    results = {
        'success': True,
        'total_segments': 0,
        'generated': 0,
        'failed': 0,
        'audios': [],
        'errors': []
    }

    # 获取旁白段落数据
    segments = narration_data.get('segments', [])
    results['total_segments'] = len(segments)

    if not segments:
        raise ValueError("旁白数据中没有段落")

    # 遍历每个段落,生成音频
    for i, segment in enumerate(segments, start=1):
        segment_id = segment.get('segment_id', f'S{i:02d}')
        text = segment.get('text', '')
        voice = segment.get('voice', voice_style)
        speed = segment.get('speed', 1.0)
        emotion = segment.get('emotion', 'neutral')

        if not text:
            raise ValueError(f"段落{segment_id}缺少文本")

        # 生成文件名
        filename = f"narration_{segment_id}.wav"
        filepath = os.path.join(output_dir, filename)

        # 占位实现 - 创建空白音频文件
        # 实际应调用TTS API
        import wave

        try:
            # 创建一个1秒的空白WAV文件
            with wave.open(filepath, 'w') as wav_file:
                wav_file.setnchannels(1)  # 单声道
                wav_file.setsampwidth(2)  # 16位
                wav_file.setframerate(44100)  # 采样率
                # 写入静音数据
                duration = len(text) * 0.1  # 根据文本长度估算时长
                num_frames = int(44100 * duration)
                wav_file.writeframes(b'\x00\x00' * num_frames)

            results['generated'] += 1
            results['audios'].append({
                'segment_id': segment_id,
                'filepath': filepath,
                'duration': duration,
                'text': text,
                'voice': voice
            })

            logger.log_info(f"音频已生成(占位): {filepath}")

        except Exception as e:
            results['failed'] += 1
            results['errors'].append({
                'segment_id': segment_id,
                'error': str(e)
            })
            logger.log_error(f"生成音频失败 {segment_id}: {str(e)}")

    # 判断整体是否成功
    if results['failed'] > 0:
        results['success'] = False

    return results


def validate_narration_data(narration_data: Dict[str, Any]) -> bool:
    """
    验证旁白数据格式

    参数:
        narration_data: 旁白数据字典

    返回:
        是否有效
    """
    if not isinstance(narration_data, dict):
        return False

    segments = narration_data.get('segments', [])
    if not isinstance(segments, list):
        return False

    for segment in segments:
        if not isinstance(segment, dict):
            return False
        if 'text' not in segment:
            return False

    return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="音频生成工具")
    parser.add_argument("--input", required=True, help="旁白JSON文件路径")
    parser.add_argument("--output", default="./output/audio", help="输出目录")
    parser.add_argument("--voice", default="male_young", help="音色风格")

    args = parser.parse_args()

    # 读取旁白数据
    with open(args.input, 'r', encoding='utf-8') as f:
        narration_data = json.load(f)

    # 验证数据
    if not validate_narration_data(narration_data):
        print("✗ 旁白数据格式无效")
        exit(1)

    # 生成音频
    result = generate_audio(
        narration_data=narration_data,
        output_dir=args.output,
        voice_style=args.voice
    )

    # 输出结果
    print(f"\n{'='*50}")
    print(f"音频生成完成")
    print(f"{'='*50}")
    print(f"总计段落: {result['total_segments']}")
    print(f"成功生成: {result['generated']}")
    print(f"失败: {result['failed']}")

    if result['errors']:
        print(f"\n错误列表:")
        for error in result['errors']:
            print(f"  - {error['segment_id']}: {error['error']}")

    if not result['success']:
        print("\n✗ 音频生成失败")
        exit(1)
    else:
        print("\n✓ 音频生成成功")
