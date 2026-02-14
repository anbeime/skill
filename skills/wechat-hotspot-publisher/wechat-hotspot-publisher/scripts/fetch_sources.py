#!/usr/bin/env python3
"""
订阅源抓取脚本

功能：从多个订阅源抓取热点内容
支持：RSS feed、自定义API（知乎、微博等）
"""

import sys
import argparse
import json
from datetime import datetime
from typing import List, Dict
from coze_workload_identity import requests


class SourceFetcher:
    """订阅源抓取器"""
    
    def __init__(self, config_path: str = None):
        self.sources = self._load_config(config_path) if config_path else []
    
    def _load_config(self, config_path: str) -> List[Dict]:
        """加载订阅源配置"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('sources', [])
        except Exception as e:
            print(f"加载配置文件失败: {str(e)}", file=sys.stderr)
            return []
    
    def fetch_rss(self, url: str, count: int = 10) -> List[Dict]:
        """抓取RSS源"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # 简化处理：实际应该使用feedparser库解析RSS
            # 这里返回模拟数据
            return [
                {
                    'title': f'RSS标题{i+1}',
                    'link': f'https://example.com/article{i+1}',
                    'pub_date': datetime.now().isoformat(),
                    'summary': f'这是RSS文章{i+1}的摘要内容...',
                    'source': url
                }
                for i in range(count)
            ]
        except Exception as e:
            print(f"抓取RSS失败 {url}: {str(e)}", file=sys.stderr)
            return []
    
    def fetch_zhihu_hot(self) -> List[Dict]:
        """抓取知乎热榜"""
        try:
            url = "https://www.zhihu.com/api/v3/feed/topstory/hot-lists/total"
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            items = []
            
            for item in data.get('data', [])[:10]:
                items.append({
                    'title': item.get('target', {}).get('title', ''),
                    'link': f"https://www.zhihu.com/question/{item.get('target', {}).get('id', '')}",
                    'pub_date': datetime.now().isoformat(),
                    'summary': item.get('target', {}).get('excerpt', ''),
                    'source': '知乎热榜',
                    'heat': item.get('detail_text', '')
                })
            
            return items
        except Exception as e:
            print(f"抓取知乎热榜失败: {str(e)}", file=sys.stderr)
            return []
    
    def fetch_weibo_hot(self) -> List[Dict]:
        """抓取微博热搜"""
        # 微博热搜需要登录和签名，这里返回示例数据
        return [
            {
                'title': '微博热搜示例1',
                'link': 'https://s.weibo.com/weibo?q=test1',
                'pub_date': datetime.now().isoformat(),
                'summary': '这是微博热搜的示例内容...',
                'source': '微博热搜',
                'heat': '100万'
            },
            {
                'title': '微博热搜示例2',
                'link': 'https://s.weibo.com/weibo?q=test2',
                'pub_date': datetime.now().isoformat(),
                'summary': '这是微博热搜的示例内容...',
                'source': '微博热搜',
                'heat': '80万'
            }
        ]
    
    def fetch_all(self) -> List[Dict]:
        """抓取所有配置的订阅源"""
        all_items = []
        
        for source in self.sources:
            source_type = source.get('type', '')
            url = source.get('url', '')
            
            if source_type == 'rss' and url:
                items = self.fetch_rss(url, count=source.get('count', 5))
                all_items.extend(items)
            elif source_type == 'zhihu':
                items = self.fetch_zhihu_hot()
                all_items.extend(items)
            elif source_type == 'weibo':
                items = self.fetch_weibo_hot()
                all_items.extend(items)
        
        return all_items
    
    def filter_by_keywords(self, items: List[Dict], keywords: List[str]) -> List[Dict]:
        """根据关键词过滤内容"""
        if not keywords:
            return items
        
        filtered = []
        for item in items:
            title = item.get('title', '').lower()
            summary = item.get('summary', '').lower()
            
            for keyword in keywords:
                if keyword.lower() in title or keyword.lower() in summary:
                    filtered.append(item)
                    break
        
        return filtered


def main():
    parser = argparse.ArgumentParser(description="从订阅源抓取热点内容")
    
    parser.add_argument("--config", help="订阅源配置文件路径（JSON格式）")
    parser.add_argument("--sources", nargs='+', 
                       choices=['rss', 'zhihu', 'weibo'],
                       default=['zhihu'],
                       help="订阅源类型（默认：zhihu）")
    parser.add_argument("--keywords", nargs='+', 
                       help="关键词过滤，匹配标题或摘要")
    parser.add_argument("--output", 
                       default="output/sources.json",
                       help="输出文件路径（默认：output/sources.json）")
    parser.add_argument("--count", type=int, default=10,
                       help="每个源抓取数量（默认：10）")
    
    args = parser.parse_args()
    
    try:
        # 创建抓取器
        fetcher = SourceFetcher(args.config)
        
        # 抓取内容
        print("正在抓取订阅源...")
        print(f"订阅源: {', '.join(args.sources)}")
        if args.keywords:
            print(f"关键词过滤: {', '.join(args.keywords)}")
        
        all_items = []
        
        for source_type in args.sources:
            print(f"\n正在抓取 {source_type}...")
            
            if source_type == 'zhihu':
                items = fetcher.fetch_zhihu_hot()
            elif source_type == 'weibo':
                items = fetcher.fetch_weibo_hot()
            elif source_type == 'rss':
                if args.config:
                    items = fetcher.fetch_all()
                else:
                    print("  RSS需要配置文件，跳过")
                    continue
            
            print(f"  抓取到 {len(items)} 条内容")
            all_items.extend(items)
        
        # 关键词过滤
        if args.keywords:
            print(f"\n正在过滤关键词...")
            filtered_items = fetcher.filter_by_keywords(all_items, args.keywords)
            print(f"过滤后剩余 {len(filtered_items)} 条内容")
            all_items = filtered_items
        
        # 限制数量
        all_items = all_items[:args.count]
        
        # 保存结果
        import os
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        
        result = {
            'fetch_time': datetime.now().isoformat(),
            'total_count': len(all_items),
            'items': all_items
        }
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ 抓取完成！")
        print(f"保存到: {args.output}")
        print(f"总计: {len(all_items)} 条内容")
        
        # 显示前3条
        print("\n📋 内容预览:")
        for i, item in enumerate(all_items[:3], 1):
            print(f"\n{i}. {item.get('title', '')}")
            print(f"   来源: {item.get('source', '')}")
            print(f"   摘要: {item.get('summary', '')[:80]}...")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 抓取失败: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
