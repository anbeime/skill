#!/usr/bin/env python3
"""
视觉分析脚本
调用视觉模型API分析图片,生成描述和提示词
"""

import os
import sys
import base64
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import requests


def encode_image(image_path: str) -> str:
    """
    将图片编码为Base64

    参数:
        image_path: 图片路径

    返回:
        Base64编码的字符串
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def analyze_image_with_vision_api(
    image_path: str,
    api_key: str,
    api_base: str,
    model: str,
    prompt: str,
    detail: str = "standard"
) -> Dict[str, Any]:
    """
    调用视觉模型API分析单张图片

    参数:
        image_path: 图片路径
        api_key: API密钥
        api_base: API基础URL
        model: 模型名称
        prompt: 分析提示词
        detail: 分析详细程度(brief/standard/detailed)

    返回:
        分析结果字典
    """
    # 编码图片
    base64_image = encode_image(image_path)

    # 构建请求
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": detail
                        }
                    }
                ]
            }
        ],
        "max_tokens": 1000
    }

    # 发送请求
    try:
        response = requests.post(
            f"{api_base}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()

        data = response.json()

        # 提取分析结果
        if 'choices' in data and len(data['choices']) > 0:
            content = data['choices'][0]['message']['content']
            return {
                'success': True,
                'content': content,
                'raw_response': data
            }
        else:
            return {
                'success': False,
                'error': 'API响应格式异常',
                'raw_response': data
            }

    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'API请求失败: {str(e)}'
        }


def batch_analyze_images(
    input_path: str,
    output_file: str,
    api_key: str,
    api_base: str,
    model: str,
    prompt: str,
    detail: str = "standard",
    batch_size: int = 5
) -> Dict[str, Any]:
    """
    批量分析图片

    参数:
        input_path: 图片目录或单张图片路径
        output_file: 输出JSON文件路径
        api_key: API密钥
        api_base: API基础URL
        model: 模型名称
        prompt: 分析提示词
        detail: 分析详细程度
        batch_size: 批量处理大小

    返回:
        分析结果字典
    """
    results = {
        'success': True,
        'total_images': 0,
        'analyzed_count': 0,
        'failed_count': 0,
        'analysis': [],
        'errors': []
    }

    try:
        # 收集图片文件
        image_files = []

        if os.path.isfile(input_path):
            # 单张图片
            image_files.append(input_path)
        elif os.path.isdir(input_path):
            # 图片目录
            for file in os.listdir(input_path):
                if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                    image_files.append(os.path.join(input_path, file))
            image_files.sort()  # 按文件名排序
        else:
            raise ValueError(f"输入路径不存在: {input_path}")

        results['total_images'] = len(image_files)

        if len(image_files) == 0:
            raise ValueError("没有找到图片文件")

        print(f"找到 {len(image_files)} 张图片")

        # 读取抽帧信息(如果存在)
        extraction_info = None
        if os.path.isdir(input_path):
            info_file = os.path.join(input_path, 'extraction_info.json')
            if os.path.exists(info_file):
                with open(info_file, 'r', encoding='utf-8') as f:
                    extraction_info = json.load(f)

        # 批量分析
        for i, image_file in enumerate(image_files):
            print(f"\n分析图片 {i+1}/{len(image_files)}: {os.path.basename(image_file)}")

            # 调用视觉API
            analysis_result = analyze_image_with_vision_api(
                image_path=image_file,
                api_key=api_key,
                api_base=api_base,
                model=model,
                prompt=prompt,
                detail=detail
            )

            # 构建结果
            frame_data = {
                'frame_file': os.path.basename(image_file),
                'frame_path': image_file,
            }

            # 添加时间戳(如果存在抽帧信息)
            if extraction_info and 'output_files' in extraction_info:
                for frame_info in extraction_info['output_files']:
                    if frame_info['filename'] == os.path.basename(image_file):
                        frame_data['timestamp'] = frame_info['timestamp']
                        frame_data['time_seconds'] = frame_info['time_seconds']
                        break

            if analysis_result['success']:
                frame_data['description'] = analysis_result['content']
                frame_data['analysis_status'] = 'success'
                results['analyzed_count'] += 1
                print(f"  ✅ 分析成功")
            else:
                frame_data['error'] = analysis_result.get('error', '未知错误')
                frame_data['analysis_status'] = 'failed'
                results['failed_count'] += 1
                print(f"  ❌ 分析失败: {frame_data['error']}")

            results['analysis'].append(frame_data)

            # 控制请求速率
            if (i + 1) % batch_size == 0:
                print(f"\n已处理 {i+1} 张图片,暂停2秒...")
                import time
                time.sleep(2)

        # 保存结果
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)

        print(f"\n✅ 分析完成:")
        print(f"  总图片数: {results['total_images']}")
        print(f"  分析成功: {results['analyzed_count']}")
        print(f"  分析失败: {results['failed_count']}")
        print(f"  结果已保存到: {output_file}")

    except Exception as e:
        results['success'] = False
        results['errors'].append(str(e))
        print(f"❌ 批量分析失败: {str(e)}")

    return results


def main():
    parser = argparse.ArgumentParser(description='视觉模型图片分析工具')
    parser.add_argument('--input', type=str, required=True, help='图片目录或单张图片路径')
    parser.add_argument('--output', type=str, required=True, help='输出JSON文件路径')
    parser.add_argument('--prompt', type=str,
                       default='详细描述这张图片的场景内容,包括人物、环境、构图、光影、色调等,适合AI视频创作参考。',
                       help='分析提示词')
    parser.add_argument('--api_key', type=str, default=None,
                       help='视觉模型API密钥(默认从环境变量VISION_API_KEY读取)')
    parser.add_argument('--api_base', type=str, default=None,
                       help='API基础URL(默认从环境变量VISION_API_BASE读取)')
    parser.add_argument('--model', type=str, default=None,
                       help='模型名称(默认从环境变量VISION_MODEL读取)')
    parser.add_argument('--detail', type=str, default='standard',
                       choices=['low', 'standard', 'high'],
                       help='分析详细程度,默认standard')
    parser.add_argument('--batch_size', type=int, default=5,
                       help='批量处理大小,默认5')

    args = parser.parse_args()

    # 获取API配置
    api_key = args.api_key or os.getenv('VISION_API_KEY')
    api_base = args.api_base or os.getenv('VISION_API_BASE', 'https://api.openai.com/v1')
    model = args.model or os.getenv('VISION_MODEL', 'gpt-4-vision-preview')

    if not api_key:
        print("❌ 缺少API密钥,请设置环境变量VISION_API_KEY或使用--api_key参数")
        sys.exit(1)

    print(f"API配置:")
    print(f"  API Base: {api_base}")
    print(f"  Model: {model}")
    print(f"  Prompt: {args.prompt[:100]}...")
    print()

    # 执行批量分析
    results = batch_analyze_images(
        input_path=args.input,
        output_file=args.output,
        api_key=api_key,
        api_base=api_base,
        model=model,
        prompt=args.prompt,
        detail=args.detail,
        batch_size=args.batch_size
    )

    # 返回状态码
    sys.exit(0 if results['success'] else 1)


if __name__ == '__main__':
    main()
