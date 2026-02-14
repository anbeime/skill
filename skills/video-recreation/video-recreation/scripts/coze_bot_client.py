#!/usr/bin/env python3
"""
Coze Bot API客户端
调用用户发布的Coze Bot进行视觉分析和内容处理
"""

import os
import sys
import base64
import json
import requests
from typing import List, Dict, Any, Optional
from .error_handler import retry_on_failure, ErrorLogger, safe_execute, global_error_logger


def encode_image_to_base64(image_path: str) -> str:
    """
    将图片编码为Base64

    参数:
        image_path: 图片路径

    返回:
        Base64编码的字符串
    """
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


@retry_on_failure(max_retries=3, retry_delay=1.0)
def call_coze_bot(
    message: str,
    image_path: Optional[str] = None,
    bot_id: str = None,
    user_id: str = "user_001",
    api_key: str = None,
    stream: bool = False
) -> Dict[str, Any]:
    """
    调用Coze Bot API

    参数:
        message: 用户消息
        image_path: 图片路径(可选)
        bot_id: Bot ID
        user_id: 用户ID
        api_key: API密钥
        stream: 是否流式响应

    返回:
        响应结果字典
    """
    # 获取配置
    bot_id = bot_id or os.getenv('COZE_BOT_ID')
    api_key = api_key or os.getenv('COZE_API_KEY')

    if not bot_id:
        raise ValueError("缺少Bot ID,请设置环境变量COZE_BOT_ID或通过参数传入")
    if not api_key:
        raise ValueError("缺少API Key,请设置环境变量COZE_API_KEY或通过参数传入")

    # 构建消息
    additional_messages = [
        {
            "content": message,
            "content_type": "text",
            "role": "user",
            "type": "question"
        }
    ]

    # 如果有图片,添加图片消息
    if image_path:
        base64_image = encode_image_to_base64(image_path)
        additional_messages.append({
            "content": f"data:image/jpeg;base64,{base64_image}",
            "content_type": "image",
            "role": "user",
            "type": "question"
        })

    # 构建请求
    url = "https://api.coze.cn/v3/chat"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "bot_id": bot_id,
        "user_id": user_id,
        "stream": stream,
        "additional_messages": additional_messages,
        "parameters": {}
    }

    response = requests.post(url, headers=headers, json=payload, timeout=60)

    if response.status_code != 200:
        raise Exception(f"API调用失败,状态码: {response.status_code}, 响应: {response.text}")

        return {
            'success': True,
            'status_code': response.status_code,
            'response': response.json()
        }

    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f"请求失败: {str(e)}"
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def analyze_image_with_coze_bot(
    image_path: str,
    prompt: str = "详细描述这张图片的内容,包括场景、人物、构图、光影等",
    bot_id: str = None,
    user_id: str = "user_001",
    api_key: str = None
) -> Dict[str, Any]:
    """
    使用Coze Bot分析图片

    参数:
        image_path: 图片路径
        prompt: 分析提示词
        bot_id: Bot ID
        user_id: 用户ID
        api_key: API密钥

    返回:
        分析结果字典
    """
    result = call_coze_bot(
        message=prompt,
        image_path=image_path,
        bot_id=bot_id,
        user_id=user_id,
        api_key=api_key,
        stream=False
    )

    if result['success']:
        # 提取回复内容
        response_data = result['response']

        # Coze API响应结构
        if 'messages' in response_data and len(response_data['messages']) > 0:
            # 获取最后一条消息
            last_message = response_data['messages'][-1]
            if 'content' in last_message:
                return {
                    'success': True,
                    'description': last_message['content'],
                    'raw_response': response_data
                }

        # 检查是否在data字段中
        if 'data' in response_data:
            return {
                'success': True,
                'description': str(response_data['data']),
                'raw_response': response_data
            }

        return {
            'success': False,
            'error': '无法解析API响应',
            'raw_response': response_data
        }
    else:
        return result


def batch_analyze_images_with_coze_bot(
    image_dir: str,
    prompt: str = "详细描述这张图片的内容,包括场景、人物、构图、光影等",
    bot_id: str = None,
    api_key: str = None,
    output_file: str = None
) -> Dict[str, Any]:
    """
    批量使用Coze Bot分析图片

    参数:
        image_dir: 图片目录
        prompt: 分析提示词
        bot_id: Bot ID
        api_key: API密钥
        output_file: 输出JSON文件路径(可选)

    返回:
        批量分析结果字典
    """
    import time
    from pathlib import Path

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
        for file in os.listdir(image_dir):
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_files.append(os.path.join(image_dir, file))
        image_files.sort()

        results['total_images'] = len(image_files)

        if len(image_files) == 0:
            raise ValueError("没有找到图片文件")

        print(f"找到 {len(image_files)} 张图片")

        # 批量分析
        for i, image_file in enumerate(image_files):
            print(f"\n分析图片 {i+1}/{len(image_files)}: {os.path.basename(image_file)}")

            # 调用Coze Bot分析
            analysis_result = analyze_image_with_coze_bot(
                image_path=image_file,
                prompt=prompt,
                bot_id=bot_id,
                api_key=api_key
            )

            # 构建结果
            frame_data = {
                'frame_file': os.path.basename(image_file),
                'frame_path': image_file,
            }

            if analysis_result['success']:
                frame_data['description'] = analysis_result['description']
                frame_data['analysis_status'] = 'success'
                results['analyzed_count'] += 1
                print(f"  ✅ 分析成功")
            else:
                frame_data['error'] = analysis_result.get('error', '未知错误')
                frame_data['analysis_status'] = 'failed'
                results['failed_count'] += 1
                print(f"  ❌ 分析失败: {frame_data['error']}")

            results['analysis'].append(frame_data)

            # 控制请求速率,避免频繁调用
            if i < len(image_files) - 1:
                print(f"  等待2秒...")
                time.sleep(2)

        # 保存结果
        if output_file:
            os.makedirs(os.path.dirname(output_file), exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n✅ 结果已保存到: {output_file}")

        print(f"\n批量分析完成:")
        print(f"  总图片数: {results['total_images']}")
        print(f"  分析成功: {results['analyzed_count']}")
        print(f"  分析失败: {results['failed_count']}")

    except Exception as e:
        results['success'] = False
        results['errors'].append(str(e))
        print(f"❌ 批量分析失败: {str(e)}")

    return results


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Coze Bot API客户端')
    parser.add_argument('--message', type=str, help='用户消息')
    parser.add_argument('--image', type=str, help='图片路径')
    parser.add_argument('--image_dir', type=str, help='图片目录(批量分析)')
    parser.add_argument('--prompt', type=str,
                       default='详细描述这张图片的内容,包括场景、人物、构图、光影等,适合AI视频创作参考。',
                       help='分析提示词')
    parser.add_argument('--bot_id', type=str, help='Bot ID(默认从环境变量COZE_BOT_ID读取)')
    parser.add_argument('--api_key', type=str, help='API Key(默认从环境变量COZE_API_KEY读取)')
    parser.add_argument('--output', type=str, help='输出JSON文件路径(批量分析时使用)')

    args = parser.parse_args()

    # 获取配置
    bot_id = args.bot_id or os.getenv('COZE_BOT_ID')
    api_key = args.api_key or os.getenv('COZE_API_KEY')

    # 示例配置(如果用户未配置)
    if not bot_id:
        bot_id = "7572557757883383858"
        print("使用默认Bot ID(可通过环境变量COZE_BOT_ID自定义)")

    if not api_key:
        api_key = "cztei_qHZQ0A5OSJjsmfZWmVb8bqu2BTbtB240YGbDYLhZpsIr8jER4aL4Aevyii8rnKfNs"
        print("使用默认API Key(可通过环境变量COZE_API_KEY自定义)")

    # 执行操作
    if args.image_dir:
        # 批量分析
        results = batch_analyze_images_with_coze_bot(
            image_dir=args.image_dir,
            prompt=args.prompt,
            bot_id=bot_id,
            api_key=api_key,
            output_file=args.output
        )
        sys.exit(0 if results['success'] else 1)

    elif args.image:
        # 单张图片分析
        result = analyze_image_with_coze_bot(
            image_path=args.image,
            prompt=args.message or args.prompt,
            bot_id=bot_id,
            api_key=api_key
        )

        if result['success']:
            print(f"\n分析结果:\n{result['description']}")
            sys.exit(0)
        else:
            print(f"\n分析失败: {result.get('error', '未知错误')}")
            sys.exit(1)

    elif args.message:
        # 纯文本对话
        result = call_coze_bot(
            message=args.message,
            bot_id=bot_id,
            api_key=api_key
        )

        if result['success']:
            print(f"\nBot回复:\n{json.dumps(result['response'], indent=2, ensure_ascii=False)}")
            sys.exit(0)
        else:
            print(f"\n调用失败: {result.get('error', '未知错误')}")
            sys.exit(1)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()
