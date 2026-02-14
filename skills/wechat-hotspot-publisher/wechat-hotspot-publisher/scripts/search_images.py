#!/usr/bin/env python3
"""
图片搜索脚本

功能：使用Unsplash API搜索高质量图片
用途：为文章配图、封面图等
"""

import sys
import argparse
import json
from typing import List, Dict
from coze_workload_identity import requests


class ImageSearcher:
    """图片搜索器"""
    
    def __init__(self, api_key: str = None):
        """
        初始化图片搜索器
        
        Args:
            api_key: Unsplash API Key（可选，不提供则使用公开API）
        """
        self.api_key = api_key
        self.base_url = "https://api.unsplash.com"
    
    def search(self, query: str, per_page: int = 10, orientation: str = "landscape") -> List[Dict]:
        """
        搜索图片
        
        Args:
            query: 搜索关键词
            per_page: 返回数量（默认10）
            orientation: 方向（landscape-横图, portrait-竖图, squary-正方形）
        
        Returns:
            图片列表
        """
        url = f"{self.base_url}/search/photos"
        
        params = {
            'query': query,
            'per_page': per_page,
            'orientation': orientation,
            'order_by': 'relevant'  # 相关性排序
        }
        
        headers = {}
        if self.api_key:
            headers['Authorization'] = f"Client-ID {self.api_key}"
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            images = []
            for item in results:
                image = {
                    'id': item.get('id'),
                    'url': item.get('urls', {}).get('regular'),
                    'thumb_url': item.get('urls', {}).get('small'),
                    'full_url': item.get('urls', {}).get('full'),
                    'description': item.get('description', ''),
                    'alt_text': item.get('alt_description', ''),
                    'width': item.get('width'),
                    'height': item.get('height'),
                    'photographer': item.get('user', {}).get('name', ''),
                    'source': 'unsplash'
                }
                images.append(image)
            
            return images
            
        except requests.exceptions.RequestException as e:
            print(f"搜索图片失败: {str(e)}", file=sys.stderr)
            return []
    
    def search_cover(self, query: str, ratio: str = "2.35:1") -> List[Dict]:
        """
        搜索封面图（特定比例）
        
        Args:
            query: 搜索关键词
            ratio: 宽高比（2.35:1, 16:9, 4:3等）
        
        Returns:
            图片列表
        """
        # Unsplash API不直接支持自定义比例，返回横图即可
        # 实际使用时可以通过CSS调整显示比例
        return self.search(query, per_page=5, orientation="landscape")
    
    def get_placeholder(self, width: int = 1200, height: int = 512, text: str = "Cover Image") -> str:
        """
        获取占位图URL
        
        Args:
            width: 宽度
            height: 高度
            text: 占位文字
        
        Returns:
            占位图URL
        """
        # 使用placeholder.com服务
        return f"https://via.placeholder.com/{width}x{height}?text={text}"


def main():
    parser = argparse.ArgumentParser(description="图片搜索工具")
    
    parser.add_argument("--query", required=True, help="搜索关键词")
    parser.add_argument("--count", type=int, default=10, help="返回图片数量（默认10）")
    parser.add_argument("--orientation", 
                       choices=['landscape', 'portrait', 'squary'],
                       default='landscape',
                       help="图片方向（默认landscape）")
    parser.add_argument("--cover", action='store_true',
                       help="搜索封面图（2.35:1比例）")
    parser.add_argument("--api-key", help="Unsplash API Key（可选）")
    parser.add_argument("--output", 
                       default="output/images.json",
                       help="输出文件路径")
    parser.add_argument("--placeholder", action='store_true',
                       help="生成占位图而不是搜索")
    
    args = parser.parse_args()
    
    try:
        searcher = ImageSearcher(args.api_key)
        
        if args.placeholder:
            # 生成占位图
            if args.cover:
                width, height = 1200, 512  # 2.35:1
            else:
                width, height = 800, 600
            
            placeholder_url = searcher.get_placeholder(width, height, args.query)
            
            result = {
                'query': args.query,
                'placeholder': True,
                'image': {
                    'url': placeholder_url,
                    'width': width,
                    'height': height,
                    'source': 'placeholder'
                }
            }
            
            print(f"✅ 占位图已生成: {placeholder_url}")
            print(f"尺寸: {width}x{height}")
            
        else:
            # 搜索图片
            print(f"正在搜索图片: {args.query}")
            
            if args.cover:
                images = searcher.search_cover(args.query)
                print("封面图模式（2.35:1比例）")
            else:
                images = searcher.search(args.query, args.count, args.orientation)
            
            result = {
                'query': args.query,
                'count': len(images),
                'images': images
            }
            
            print(f"✅ 搜索到 {len(images)} 张图片")
            
            # 显示前3张
            print("\n📷 图片预览:")
            for i, img in enumerate(images[:3], 1):
                print(f"\n{i}. {img.get('description', '无描述')}")
                print(f"   尺寸: {img.get('width')}x{img.get('height')}")
                print(f"   链接: {img.get('url')}")
                if img.get('photographer'):
                    print(f"   摄影师: {img.get('photographer')}")
        
        # 保存结果
        import os
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n已保存到: {args.output}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 操作失败: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
