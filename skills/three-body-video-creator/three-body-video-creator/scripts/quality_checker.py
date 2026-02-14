#!/usr/bin/env python3
"""
视频技术指标检测工具
用于检测《三体》赛道视频的技术规范符合性
"""

import os
import sys
from typing import Dict, Tuple, Any


def check_video_quality(video_path: str,
                       expected_resolution: Tuple[int, int] = (1920, 1080),
                       expected_duration: int = 510,
                       expected_fps: int = 30,
                       audio_sample_rate: int = 44100) -> Dict[str, Any]:
    """
    检测视频技术指标

    参数:
        video_path: 视频文件路径
        expected_resolution: 期望分辨率 (宽, 高)
        expected_duration: 期望时长(秒)
        expected_fps: 期望帧率
        audio_sample_rate: 期望音频采样率

    返回:
        检测结果字典,包含各项指标的状态和详细信息
    """
    try:
        import cv2
        from moviepy.editor import VideoFileClip
    except ImportError as e:
        return {
            'success': False,
            'error': f'缺少必要依赖库: {str(e)}。请先安装: pip install opencv-python moviepy'
        }

    # 检查文件是否存在
    if not os.path.exists(video_path):
        return {
            'success': False,
            'error': f'视频文件不存在: {video_path}'
        }

    results = {
        'success': True,
        'file_path': video_path,
        'file_size_mb': 0,
        'resolution': {},
        'duration': {},
        'fps': {},
        'audio': {},
        'overall': False
    }

    try:
        # 获取文件大小
        file_size = os.path.getsize(video_path) / (1024 * 1024)
        results['file_size_mb'] = round(file_size, 2)

        # 使用OpenCV检测视频信息
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise Exception("无法打开视频文件")

        # 检测分辨率
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_resolution = (width, height)

        resolution_match = actual_resolution == expected_resolution
        results['resolution'] = {
            'expected': expected_resolution,
            'actual': actual_resolution,
            'match': resolution_match
        }

        # 检测帧率
        actual_fps = int(cap.get(cv2.CAP_PROP_FPS))
        fps_match = actual_fps == expected_fps
        results['fps'] = {
            'expected': expected_fps,
            'actual': actual_fps,
            'match': fps_match
        }

        # 检测时长
        actual_duration = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) / actual_fps
        duration_match = abs(actual_duration - expected_duration) <= 10  # 允许10秒误差
        results['duration'] = {
            'expected': expected_duration,
            'actual': round(actual_duration, 1),
            'match': duration_match
        }

        cap.release()

        # 使用MoviePy检测音频信息
        try:
            clip = VideoFileClip(video_path)
            if clip.audio is not None:
                actual_sample_rate = int(clip.audio.fps)
                audio_channels = clip.audio.nchannels

                audio_match = actual_sample_rate == audio_sample_rate
                results['audio'] = {
                    'expected_sample_rate': audio_sample_rate,
                    'actual_sample_rate': actual_sample_rate,
                    'channels': audio_channels,
                    'match': audio_match
                }
            else:
                results['audio'] = {
                    'has_audio': False,
                    'match': False
                }
            clip.close()
        except Exception as e:
            results['audio'] = {
                'error': str(e),
                'match': False
            }

        # 判定整体是否合格
        all_checks = [
            results['resolution']['match'],
            results['duration']['match'],
            results['fps']['match'],
            results['audio'].get('match', False)
        ]
        results['overall'] = all(all_checks)

        return results

    except Exception as e:
        return {
            'success': False,
            'error': f'检测过程中发生错误: {str(e)}'
        }


def print_quality_report(results: Dict[str, Any]):
    """
    打印质量检测报告

    参数:
        results: check_video_quality() 返回的检测结果
    """
    if not results['success']:
        print(f"❌ 检测失败: {results.get('error', '未知错误')}")
        return

    print("=" * 60)
    print("《三体》视频技术指标检测报告")
    print("=" * 60)
    print(f"文件路径: {results['file_path']}")
    print(f"文件大小: {results['file_size_mb']} MB")
    print()

    # 分辨率
    res = results['resolution']
    status = "✅ 通过" if res['match'] else "❌ 不合格"
    print(f"分辨率: {status}")
    print(f"  期望: {res['expected'][0]}x{res['expected'][1]}")
    print(f"  实际: {res['actual'][0]}x{res['actual'][1]}")
    print()

    # 时长
    dur = results['duration']
    status = "✅ 通过" if dur['match'] else "❌ 不合格"
    print(f"时长: {status}")
    print(f"  期望: {dur['expected']}秒 ({dur['expected'] // 60}分{dur['expected'] % 60}秒)")
    print(f"  实际: {dur['actual']}秒 ({int(dur['actual'] // 60)}分{int(dur['actual'] % 60)}秒)")
    print()

    # 帧率
    fps = results['fps']
    status = "✅ 通过" if fps['match'] else "❌ 不合格"
    print(f"帧率: {status}")
    print(f"  期望: {fps['expected']} fps")
    print(f"  实际: {fps['actual']} fps")
    print()

    # 音频
    audio = results['audio']
    if 'error' in audio:
        print(f"音频: ❌ 检测失败 - {audio['error']}")
    elif 'has_audio' in audio and not audio['has_audio']:
        print(f"音频: ❌ 未检测到音频轨道")
    else:
        status = "✅ 通过" if audio['match'] else "❌ 不合格"
        print(f"音频: {status}")
        print(f"  采样率: {audio['actual_sample_rate']} Hz")
        print(f"  声道数: {audio['channels']}")
    print()

    # 总体结果
    overall_status = "✅ 全部合格" if results['overall'] else "❌ 存在不合格项"
    print("=" * 60)
    print(f"总体结果: {overall_status}")
    print("=" * 60)

    if not results['overall']:
        print("\n不合格项:")
        if not results['resolution']['match']:
            print("  - 分辨率不符合要求")
        if not results['duration']['match']:
            print("  - 时长不符合要求")
        if not results['fps']['match']:
            print("  - 帧率不符合要求")
        if not results['audio'].get('match', False):
            print("  - 音频参数不符合要求")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='《三体》视频技术指标检测工具')
    parser.add_argument('video_path', type=str, help='视频文件路径')
    parser.add_argument('--resolution', type=str, default='1920x1080',
                       help='期望分辨率 (格式: WIDTHxHEIGHT)')
    parser.add_argument('--duration', type=int, default=510,
                       help='期望时长(秒)')
    parser.add_argument('--fps', type=int, default=30,
                       help='期望帧率')
    parser.add_argument('--audio-rate', type=int, default=44100,
                       help='期望音频采样率')

    args = parser.parse_args()

    # 解析分辨率
    try:
        width, height = map(int, args.resolution.split('x'))
        resolution = (width, height)
    except:
        print("错误: 分辨率格式不正确,应为 WIDTHxHEIGHT (例如: 1920x1080)")
        sys.exit(1)

    # 执行检测
    results = check_video_quality(
        video_path=args.video_path,
        expected_resolution=resolution,
        expected_duration=args.duration,
        expected_fps=args.fps,
        audio_sample_rate=args.audio_rate
    )

    # 打印报告
    print_quality_report(results)

    # 返回状态码
    sys.exit(0 if results.get('success', False) and results.get('overall', False) else 1)
