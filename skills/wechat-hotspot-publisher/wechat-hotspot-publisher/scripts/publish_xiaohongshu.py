#!/usr/bin/env python3
"""
小红书图文笔记发布脚本

功能：发布图文笔记到小红书
授权方式：ApiKey（auth_type=1）
凭证Key: COZE_XIAOHONGSHU_CREDENTIAL_7597373721971540014
"""

import os
import sys
import argparse
import json
from coze_workload_identity import requests


def get_xiaohongshu_credentials():
    """
    从环境变量获取小红书凭证
    """
    skill_id = "7597373721971540014"
    
    # 小红书需要Cookie和设备信息
    cookie = os.getenv(f"COZE_XIAOHONGSHU_CREDENTIAL_{skill_id}")
    
    if not cookie:
        raise ValueError(
            "未找到小红书凭证配置。\n"
            "请提供小红书Web端Cookie。\n"
            "获取方式：\n"
            "1. 浏览器登录小红书网页版 https://www.xiaohongshu.com\n"
            "2. 打开开发者工具（F12）\n"
            "3. 在Network中找到任意请求，复制Cookie值\n"
            "4. 注意：Cookie包含多个键值对，需要完整复制"
        )
    
    # 从Cookie中提取关键参数
    device_id = None
    a1 = None
    x_s = None
    
    # 简单解析Cookie（实际使用时可能需要更复杂的解析）
    for item in cookie.split(';'):
        item = item.strip()
        if 'device_id=' in item:
            device_id = item.split('=')[1]
        elif 'a1=' in item:
            a1 = item.split('=')[1]
        elif 'x-s=' in item:
            x_s = item.split('=')[1]
    
    return {
        'cookie': cookie,
        'device_id': device_id,
        'a1': a1,
        'x_s': x_s
    }


def publish_xiaohongshu_note(title, content, images=None, tags=None):
    """
    发布图文笔记到小红书
    
    Args:
        title: 笔记标题
        content: 笔记内容
        images: 图片URL列表
        tags: 标签列表
    
    Returns:
        dict: 发布结果
    """
    # 获取凭证
    creds = get_xiaohongshu_credentials()
    
    # 小红书API端点
    # 注意：小红书没有官方公开的发布API，以下为模拟实现
    # 实际使用时需要通过抓包分析真实的API端点
    
    url = "https://edith.xiaohongshu.com/api/sns/web/v1/note/publish"
    
    # 构建请求数据
    headers = {
        'Cookie': creds['cookie'],
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    data = {
        'type': 'normal',  # normal-普通笔记, video-视频笔记
        'title': title,
        'desc': content,
        'at_uid_list': [],
        'image_list': images if images else [],
        'tag_list': tags if tags else [],
        'poi_id': '',
        'post_time': 0,  # 0-立即发布
    }
    
    try:
        # 发送请求（实际API可能需要签名等）
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        # 小红书API返回格式
        result = response.json()
        
        if result.get('success') or result.get('code') == 0:
            note_id = result.get('data', {}).get('note_id', '')
            return {
                "success": True,
                "note_id": note_id,
                "message": "笔记发布成功",
                "url": f"https://www.xiaohongshu.com/explore/{note_id}"
            }
        else:
            raise Exception(f"小红书API错误: {result.get('msg', '未知错误')}")
            
    except requests.exceptions.RequestException as e:
        raise Exception(f"网络请求失败: {str(e)}")
    except json.JSONDecodeError:
        raise Exception("响应解析失败")


def main():
    parser = argparse.ArgumentParser(description="发布图文笔记到小红书")
    
    # 必需参数
    parser.add_argument("--title", required=True, help="笔记标题")
    parser.add_argument("--content", required=True, help="笔记内容")
    
    # 可选参数
    parser.add_argument("--images", help="图片URL列表，用逗号分隔")
    parser.add_argument("--tags", help="标签列表，用逗号分隔")
    
    args = parser.parse_args()
    
    try:
        print("正在准备发布小红书笔记...")
        
        # 处理参数
        images = args.images.split(',') if args.images else []
        tags = args.tags.split(',') if args.tags else []
        
        print(f"标题: {args.title}")
        print(f"内容长度: {len(args.content)} 字")
        print(f"图片数量: {len(images)}")
        print(f"标签数量: {len(tags)}")
        
        # 发布笔记
        print("\n正在发布...")
        result = publish_xiaohongshu_note(
            title=args.title,
            content=args.content,
            images=images,
            tags=tags
        )
        
        # 输出结果
        print("\n" + "="*50)
        print("✅ 发布成功！")
        print("="*50)
        print(f"笔记ID: {result['note_id']}")
        print(f"笔记链接: {result['url']}")
        print("\n请登录小红书查看发布的笔记")
        print("="*50)
        
        print("\nJSON输出:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 发布失败: {str(e)}", file=sys.stderr)
        
        # 错误提示
        if "Cookie" in str(e):
            print("\n💡 解决方案：", file=sys.stderr)
            print("请检查小红书Cookie是否正确", file=sys.stderr)
            print("1. 确认Cookie是否完整复制", file=sys.stderr)
            print("2. Cookie可能已过期，需要重新获取", file=sys.stderr)
            print("3. 尝试重新登录小红书网页版", file=sys.stderr)
        
        return 1


if __name__ == "__main__":
    sys.exit(main())
