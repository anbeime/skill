#!/usr/bin/env python3
"""
配音生成脚本
使用 Edge-TTS 引擎生成视频旁白和配音
"""

import os
import sys
from typing import Dict, Any, List
import json
from .error_handler import retry_on_failure, ErrorLogger

# 导入 Edge-TTS 生成器
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'temp_qwen3_tts', 'qwen3-tts-local', 'scripts'))
try:
    from tts_generator import LocalTTSGenerator
except ImportError:
    # 如果导入失败，使用占位实现
    LocalTTSGenerator = None

logger = ErrorLogger()


@retry_on_failure(max_retries=2, retry_delay=0.5)
def generate_voice(
    narration_data: Dict[str, Any],
    output_dir: str = "./output/voice"
) -> Dict[str, Any]:
    """
    生成视频配音

    参数:
        narration_data: 旁白数据,包含文本和音色要求
        output_dir: 输出目录

    返回:
        生成结果字典,包含成功/失败信息
    """
    os.makedirs(output_dir, exist_ok=True)

    results = {
        'success': True,
        'total_segments': 0,
        'generated': 0,
        'failed': 0,
        'voices': [],
        'errors': []
    }

    if LocalTTSGenerator is None:
        # 占位实现 - 如果没有Edge-TTS
        return _generate_voice_placeholder(narration_data, output_dir, results)

    # 使用 Edge-TTS 生成
    generator = LocalTTSGenerator()

    segments = narration_data.get('segments', [])
    results['total_segments'] = len(segments)

    if not segments:
        raise ValueError("旁白数据中没有段落")

    for i, segment in enumerate(segments, start=1):
        segment_id = segment.get('segment_id', f'S{i:02d}')
        text = segment.get('text', '')
        voice = segment.get('voice', 'zh-CN-XiaoxiaoNeural')  # 默认使用中文女声
        rate = segment.get('rate', '+0%')
        pitch = segment.get('pitch', '+0Hz')
        volume = segment.get('volume', '+0%')

        if not text:
            raise ValueError(f"段落{segment_id}缺少文本")

        # 生成文件名
        filename = f"voice_{segment_id}.mp3"
        filepath = os.path.join(output_dir, filename)

        try:
            # 调用 Edge-TTS 生成语音
            result = generator.generate_speech(
                text=text,
                voice=voice,
                output_file=filepath,
                rate=rate,
                pitch=pitch,
                volume=volume
            )

            if result.get('success'):
                results['generated'] += 1
                results['voices'].append({
                    'segment_id': segment_id,
                    'filepath': filepath,
                    'duration': result.get('duration', 0),
                    'text': text,
                    'voice': voice
                })
                logger.log_info(f"配音已生成: {filepath}")
            else:
                raise Exception(result.get('error', '未知错误'))

        except Exception as e:
            results['failed'] += 1
            results['errors'].append({
                'segment_id': segment_id,
                'error': str(e)
            })
            logger.log_error(f"生成配音失败 {segment_id}: {str(e)}")

    if results['failed'] > 0:
        results['success'] = False

    return results


def _generate_voice_placeholder(
    narration_data: Dict[str, Any],
    output_dir: str,
    results: Dict[str, Any]
) -> Dict[str, Any]:
    """
    占位实现 - 生成空白配音文件

    参数:
        narration_data: 旁白数据
        output_dir: 输出目录
        results: 结果字典

    返回:
        生成结果字典
    """
    import wave
    import struct

    segments = narration_data.get('segments', [])
    results['total_segments'] = len(segments)

    for i, segment in enumerate(segments, start=1):
        segment_id = segment.get('segment_id', f'S{i:02d}')
        text = segment.get('text', '')

        filename = f"voice_{segment_id}.wav"
        filepath = os.path.join(output_dir, filename)

        try:
            # 创建占位音频文件
            with wave.open(filepath, 'w') as wav_file:
                wav_file.setnchannels(1)  # 单声道
                wav_file.setsampwidth(2)  # 16位
                wav_file.setframerate(44100)  # 采样率

                duration = len(text) * 0.1  # 根据文本长度估算时长
                num_frames = int(44100 * duration)
                wav_file.writeframes(b'\x00\x00' * num_frames)

            results['generated'] += 1
            results['voices'].append({
                'segment_id': segment_id,
                'filepath': filepath,
                'duration': duration,
                'text': text,
                'voice': 'placeholder'
            })

            logger.log_info(f"配音已生成(占位): {filepath}")

        except Exception as e:
            results['failed'] += 1
            results['errors'].append({
                'segment_id': segment_id,
                'error': str(e)
            })
            logger.log_error(f"生成配音失败 {segment_id}: {str(e)}")

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


def list_available_voices() -> Dict[str, Any]:
    """
    列出所有可用的音色

    返回:
        音色列表字典
    """
    if LocalTTSGenerator is None:
        return {
            'success': False,
            'error': 'Edge-TTS 不可用，请安装 edge-tts'
        }

    generator = LocalTTSGenerator()
    return generator.list_voices()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="配音生成工具(Edge-TTS)")
    parser.add_argument("--input", required=True, help="旁白JSON文件路径")
    parser.add_argument("--output", default="./output/voice", help="输出目录")
    parser.add_argument("--list-voices", action="store_true", help="列出所有音色")

    args = parser.parse_args()

    if args.list_voices:
        result = list_available_voices()
        if result.get('success'):
            print("可用音色：")
            for lang, voices in result['voices'].items():
                print(f"\n  {lang}:")
                for voice in voices:
                    print(f"    - {voice['name']} ({voice['gender']})")
        else:
            print(f"获取音色列表失败: {result.get('error')}")
            exit(1)
    else:
        # 读取旁白数据
        with open(args.input, 'r', encoding='utf-8') as f:
            narration_data = json.load(f)

        # 验证数据
        if not validate_narration_data(narration_data):
            print("✗ 旁白数据格式无效")
            exit(1)

        # 生成配音
        result = generate_voice(
            narration_data=narration_data,
            output_dir=args.output
        )

        # 输出结果
        print(f"\n{'='*50}")
        print(f"配音生成完成")
        print(f"{'='*50}")
        print(f"总计段落: {result['total_segments']}")
        print(f"成功生成: {result['generated']}")
        print(f"失败: {result['failed']}")

        if result['errors']:
            print(f"\n错误列表:")
            for error in result['errors']:
                print(f"  - {error['segment_id']}: {error['error']}")

        if not result['success']:
            print("\n✗ 配音生成失败")
            exit(1)
        else:
            print("\n✓ 配音生成成功")
