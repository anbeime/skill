#!/usr/bin/env python3
"""
视频抽帧脚本
支持间隔抽帧、均匀采样,输出关键帧图片
"""

import os
import sys
import cv2
import argparse
from pathlib import Path
from typing import List, Dict, Any


def extract_frames(
    video_path: str,
    output_dir: str,
    interval: float = 1.0,
    max_frames: int = 10,
    start_time: float = 0,
    end_time: float = None,
    resolution: tuple = None
) -> Dict[str, Any]:
    """
    从视频中抽取关键帧

    参数:
        video_path: 视频文件路径
        output_dir: 输出目录
        interval: 抽帧间隔(秒)
        max_frames: 最大抽帧数
        start_time: 开始时间(秒)
        end_time: 结束时间(秒),None表示到视频结尾
        resolution: 输出分辨率,如(1920, 1080),None表示保持原分辨率

    返回:
        抽帧结果字典
    """
    results = {
        'success': True,
        'total_frames': 0,
        'output_files': [],
        'errors': []
    }

    try:
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)

        # 打开视频文件
        cap = cv2.VideoCapture(video_path)

        if not cap.isOpened():
            raise ValueError(f"无法打开视频文件: {video_path}")

        # 获取视频信息
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_duration = total_frames / fps

        print(f"视频信息:")
        print(f"  帧率: {fps:.2f} fps")
        print(f"  总帧数: {total_frames}")
        print(f"  时长: {video_duration:.2f} 秒")

        # 计算抽帧范围
        if end_time is None:
            end_time = video_duration

        if start_time >= end_time:
            raise ValueError(f"开始时间({start_time})必须小于结束时间({end_time})")

        # 计算抽帧间隔(帧数)
        frame_interval = int(interval * fps)

        # 计算起始和结束帧号
        start_frame = int(start_time * fps)
        end_frame = int(end_time * fps)

        # 设置起始帧
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        # 计算实际抽帧数
        available_frames = (end_frame - start_frame) // frame_interval
        actual_max_frames = min(max_frames, available_frames)

        print(f"\n抽帧配置:")
        print(f"  抽帧间隔: {interval} 秒 ({frame_interval} 帧)")
        print(f"  抽帧范围: {start_time}s - {end_time}s")
        print(f"  最大抽帧数: {max_frames}")
        print(f"  实际抽帧数: {actual_max_frames}")

        # 抽帧
        frame_count = 0
        extracted_count = 0

        while extracted_count < actual_max_frames:
            ret, frame = cap.read()

            if not ret:
                break

            current_time = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000.0

            # 检查是否在时间范围内
            if current_time > end_time:
                break

            # 按间隔抽帧
            if frame_count % frame_interval == 0:
                # 调整分辨率
                if resolution:
                    frame = cv2.resize(frame, resolution)

                # 生成文件名
                frame_filename = f"frame_{extracted_count + 1:05d}.jpg"
                frame_path = os.path.join(output_dir, frame_filename)

                # 保存图片
                cv2.imwrite(frame_path, frame, [cv2.IMWRITE_JPEG_QUALITY, 95])

                # 记录结果
                results['output_files'].append({
                    'filename': frame_filename,
                    'path': frame_path,
                    'timestamp': f"{int(current_time // 3600):02d}:{int((current_time % 3600) // 60):02d}:{int(current_time % 60):02d}",
                    'time_seconds': current_time
                })

                extracted_count += 1
                print(f"  抽取帧 {extracted_count}/{actual_max_frames}: {frame_filename} (时间: {current_time:.2f}s)")

            frame_count += 1

        results['total_frames'] = extracted_count

        # 释放资源
        cap.release()

        print(f"\n✅ 抽帧完成,共抽取 {extracted_count} 帧")
        print(f"输出目录: {output_dir}")

    except Exception as e:
        results['success'] = False
        results['errors'].append(str(e))
        print(f"❌ 抽帧失败: {str(e)}")

    return results


def main():
    parser = argparse.ArgumentParser(description='视频抽帧工具')
    parser.add_argument('--input', type=str, required=True, help='视频文件路径')
    parser.add_argument('--output', type=str, required=True, help='输出目录')
    parser.add_argument('--interval', type=float, default=1.0, help='抽帧间隔(秒),默认1秒')
    parser.add_argument('--max_frames', type=int, default=10, help='最大抽帧数,默认10')
    parser.add_argument('--start_time', type=float, default=0, help='开始时间(秒),默认0')
    parser.add_argument('--end_time', type=float, default=None, help='结束时间(秒),默认视频结尾')
    parser.add_argument('--resolution', type=str, default=None, help='输出分辨率,如1920x1080,默认保持原分辨率')

    args = parser.parse_args()

    # 解析分辨率
    resolution = None
    if args.resolution:
        try:
            width, height = map(int, args.resolution.split('x'))
            resolution = (width, height)
        except ValueError:
            print(f"❌ 分辨率格式错误,应为'宽x高',如1920x1080")
            sys.exit(1)

    # 执行抽帧
    results = extract_frames(
        video_path=args.input,
        output_dir=args.output,
        interval=args.interval,
        max_frames=args.max_frames,
        start_time=args.start_time,
        end_time=args.end_time,
        resolution=resolution
    )

    # 输出结果
    if results['success']:
        print("\n抽帧文件列表:")
        for frame_info in results['output_files']:
            print(f"  {frame_info['filename']} - {frame_info['timestamp']}")

        # 保存结果JSON
        import json
        result_file = os.path.join(args.output, 'extraction_info.json')
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"\n抽帧信息已保存到: {result_file}")

        sys.exit(0)
    else:
        print("\n抽帧过程中出现错误:")
        for error in results['errors']:
            print(f"  - {error}")
        sys.exit(1)


if __name__ == '__main__':
    main()
