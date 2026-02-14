#!/usr/bin/env python3
"""
图片质量检测工具
用于检测短视频分镜图片的质量,识别肢体异常、模糊、变形等问题
"""

import os
import sys
from typing import Dict, Tuple, Any, List
import numpy as np
from PIL import Image, ImageFilter, ImageEnhance


def check_image_quality(image_path: str,
                       expected_resolution: Tuple[int, int] = (1920, 1080),
                       check_limb_anomaly: bool = True,
                       check_blur: bool = True,
                       check_deformation: bool = True,
                       min_sharpness: float = 100.0) -> Dict[str, Any]:
    """
    检测图片质量

    参数:
        image_path: 图片文件路径
        expected_resolution: 期望分辨率 (宽, 高)
        check_limb_anomaly: 是否检测肢体异常
        check_blur: 是否检测模糊
        check_deformation: 是否检测变形
        min_sharpness: 最小清晰度阈值

    返回:
        检测结果字典,包含各项指标的状态和详细信息
    """
    try:
        from PIL import Image
        import numpy as np
        import cv2
    except ImportError as e:
        return {
            'success': False,
            'error': f'缺少必要依赖库: {str(e)}。请先安装: pip install opencv-python pillow numpy'
        }

    # 检查文件是否存在
    if not os.path.exists(image_path):
        return {
            'success': False,
            'error': f'图片文件不存在: {image_path}'
        }

    results = {
        'success': True,
        'file_path': image_path,
        'file_size_mb': 0,
        'resolution': {},
        'sharpness': {},
        'noise': {},
        'limb_anomaly': {},
        'deformation': {},
        'overall': False
    }

    try:
        # 打开图片
        img = Image.open(image_path)
        img_array = np.array(img)

        # 获取文件大小
        file_size = os.path.getsize(image_path) / (1024 * 1024)
        results['file_size_mb'] = round(file_size, 2)

        # 检测分辨率
        width, height = img.size
        actual_resolution = (width, height)
        resolution_match = actual_resolution == expected_resolution
        results['resolution'] = {
            'expected': expected_resolution,
            'actual': actual_resolution,
            'match': resolution_match
        }

        # 检测清晰度(使用Laplacian方差)
        if check_blur:
            try:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
                sharpness_match = laplacian_var >= min_sharpness

                results['sharpness'] = {
                    'value': round(laplacian_var, 2),
                    'threshold': min_sharpness,
                    'match': sharpness_match
                }
            except Exception as e:
                results['sharpness'] = {
                    'error': str(e),
                    'match': False
                }

        # 检测噪点(使用标准差)
        if check_blur:
            try:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                noise_std = np.std(gray)
                noise_match = noise_std < 60.0  # 阈值可根据实际情况调整

                results['noise'] = {
                    'value': round(noise_std, 2),
                    'threshold': 60.0,
                    'match': noise_match
                }
            except Exception as e:
                results['noise'] = {
                    'error': str(e),
                    'match': False
                }

        # 检测肢体异常(基于边缘检测和连通区域)
        if check_limb_anomaly:
            try:
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                edges = cv2.Canny(gray, 50, 150)

                # 查找轮廓
                contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                # 筛选可能的肢体区域(基于面积和长宽比)
                limb_regions = []
                for cnt in contours:
                    area = cv2.contourArea(cnt)
                    if area > 5000:  # 最小面积阈值
                        x, y, w, h = cv2.boundingRect(cnt)
                        aspect_ratio = float(h) / w if w > 0 else 0
                        limb_regions.append({
                            'area': area,
                            'aspect_ratio': aspect_ratio,
                            'position': (x, y, w, h)
                        })

                # 简单异常检测逻辑(实际项目中需要更复杂的AI模型)
                # 这里使用基于数量的简单规则作为示例
                limb_count = len(limb_regions)
                limb_anomaly = limb_count > 8 or limb_count < 2  # 可根据实际情况调整

                results['limb_anomaly'] = {
                    'limb_regions_count': limb_count,
                    'regions': limb_regions[:5],  # 仅保存前5个区域示例
                    'match': not limb_anomaly
                }
            except Exception as e:
                results['limb_anomaly'] = {
                    'error': str(e),
                    'match': False
                }

        # 检测变形(基于透视变换特征)
        if check_deformation:
            try:
                # 使用Harris角点检测
                gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                corners = cv2.goodFeaturesToTrack(gray, maxCorners=100, qualityLevel=0.01, minDistance=10)

                if corners is not None and len(corners) > 0:
                    # 计算角点的分布均匀性
                    corners = np.int32(corners)
                    x_coords = corners[:, 0, 0]
                    y_coords = corners[:, 0, 1]

                    x_std = np.std(x_coords)
                    y_std = np.std(y_coords)

                    # 如果角点分布不均匀,可能存在变形
                    deformation = (x_std < 50 or y_std < 50) or (x_std > 500 or y_std > 500)
                    deformation_match = not deformation

                    results['deformation'] = {
                        'corner_count': len(corners),
                        'x_std': round(x_std, 2),
                        'y_std': round(y_std, 2),
                        'match': deformation_match
                    }
                else:
                    results['deformation'] = {
                        'corner_count': 0,
                        'match': False
                    }
            except Exception as e:
                results['deformation'] = {
                    'error': str(e),
                    'match': False
                }

        # 判定整体是否合格
        all_checks = []
        all_checks.append(results['resolution']['match'])

        if check_blur:
            all_checks.append(results['sharpness'].get('match', False))
            all_checks.append(results['noise'].get('match', False))

        if check_limb_anomaly:
            all_checks.append(results['limb_anomaly'].get('match', False))

        if check_deformation:
            all_checks.append(results['deformation'].get('match', False))

        results['overall'] = all(all_checks)

        # 收集问题
        issues = []
        if not results['resolution']['match']:
            issues.append(f"分辨率不符合要求: 期望{expected_resolution}, 实际{actual_resolution}")
        if check_blur and not results['sharpness'].get('match', False):
            issues.append(f"图片模糊: 清晰度{results['sharpness'].get('value', 0)}低于阈值{min_sharpness}")
        if check_blur and not results['noise'].get('match', False):
            issues.append(f"噪点过多: 标准差{results['noise'].get('value', 0)}超过阈值60.0")
        if check_limb_anomaly and not results['limb_anomaly'].get('match', False):
            issues.append(f"肢体异常: 检测到{results['limb_anomaly'].get('limb_regions_count', 0)}个肢体区域,可能存在多余肢体或畸形")
        if check_deformation and not results['deformation'].get('match', False):
            issues.append("图片变形: 角点分布异常")

        results['issues'] = issues

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
        results: check_image_quality() 返回的检测结果
    """
    if not results['success']:
        print(f"❌ 检测失败: {results.get('error', '未知错误')}")
        return

    print("=" * 60)
    print("图片质量检测报告")
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

    # 清晰度
    if 'sharpness' in results and 'error' not in results['sharpness']:
        sharp = results['sharpness']
        status = "✅ 通过" if sharp['match'] else "❌ 不合格"
        print(f"清晰度: {status}")
        print(f"  数值: {sharp['value']}")
        print(f"  阈值: {sharp['threshold']}")
        print()

    # 噪点
    if 'noise' in results and 'error' not in results['noise']:
        noise = results['noise']
        status = "✅ 通过" if noise['match'] else "❌ 不合格"
        print(f"噪点: {status}")
        print(f"  标准差: {noise['value']}")
        print(f"  阈值: {noise['threshold']}")
        print()

    # 肢体异常
    if 'limb_anomaly' in results and 'error' not in results['limb_anomaly']:
        limb = results['limb_anomaly']
        status = "✅ 通过" if limb['match'] else "❌ 不合格"
        print(f"肢体异常: {status}")
        print(f"  检测区域数: {limb['limb_regions_count']}")
        if not limb['match']:
            print("  ⚠️  可能存在多余肢体或畸形")
        print()

    # 变形
    if 'deformation' in results and 'error' not in results['deformation']:
        deform = results['deformation']
        status = "✅ 通过" if deform['match'] else "❌ 不合格"
        print(f"图片变形: {status}")
        print(f"  角点数: {deform.get('corner_count', 0)}")
        print(f"  X分布标准差: {deform.get('x_std', 0)}")
        print(f"  Y分布标准差: {deform.get('y_std', 0)}")
        print()

    # 总体结果
    overall_status = "✅ 全部合格" if results['overall'] else "❌ 存在不合格项"
    print("=" * 60)
    print(f"总体结果: {overall_status}")
    print("=" * 60)

    if not results['overall']:
        print("\n问题列表:")
        for i, issue in enumerate(results.get('issues', []), 1):
            print(f"  {i}. {issue}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='图片质量检测工具')
    parser.add_argument('image_path', type=str, help='图片文件路径')
    parser.add_argument('--resolution', type=str, default='1920x1080',
                       help='期望分辨率 (格式: WIDTHxHEIGHT)')
    parser.add_argument('--min-sharpness', type=float, default=100.0,
                       help='最小清晰度阈值')
    parser.add_argument('--no-limb-check', action='store_true',
                       help='跳过肢体异常检测')
    parser.add_argument('--no-blur-check', action='store_true',
                       help='跳过模糊检测')
    parser.add_argument('--no-deformation-check', action='store_true',
                       help='跳过变形检测')

    args = parser.parse_args()

    # 解析分辨率
    try:
        width, height = map(int, args.resolution.split('x'))
        resolution = (width, height)
    except:
        print("错误: 分辨率格式不正确,应为 WIDTHxHEIGHT (例如: 1920x1080)")
        sys.exit(1)

    # 执行检测
    results = check_image_quality(
        image_path=args.image_path,
        expected_resolution=resolution,
        check_limb_anomaly=not args.no_limb_check,
        check_blur=not args.no_blur_check,
        check_deformation=not args.no_deformation_check,
        min_sharpness=args.min_sharpness
    )

    # 打印报告
    print_quality_report(results)

    # 返回状态码
    sys.exit(0 if results.get('success', False) and results.get('overall', False) else 1)
