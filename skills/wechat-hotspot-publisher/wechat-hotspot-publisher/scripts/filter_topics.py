#!/usr/bin/env python3
"""
智能选题筛选系统

功能：10分制打分筛选热点话题
评分维度：热度(4分) + 争议性(2分) + 价值(3分) + 相关性(1分)
"""

import sys
import argparse
import json
from datetime import datetime
from typing import List, Dict, Optional


class TopicFilter:
    """选题筛选器"""
    
    def __init__(self, user_keywords: List[str] = None):
        """
        初始化筛选器
        
        Args:
            user_keywords: 用户关注的关键词，用于相关性评分
        """
        self.user_keywords = [k.lower() for k in user_keywords] if user_keywords else []
    
    def score_heat(self, item: Dict) -> int:
        """
        评分：热度/趋势（4分）
        
        评分标准：
        - 4分：当前非常热门（知乎热榜Top10、微博热搜Top20）
        - 3分：热门（知乎热榜Top30、微博热搜Top50）
        - 2分：较热（有一定讨论量）
        - 1分：普通（讨论量一般）
        - 0分：冷门
        """
        # 尝试从数据中提取热度信息
        source = item.get('source', '')
        heat_str = item.get('heat', '')
        rank = item.get('rank', 999)  # 排名
        
        if source == '知乎热榜':
            if rank <= 10:
                return 4
            elif rank <= 30:
                return 3
            elif rank <= 50:
                return 2
            else:
                return 1
        elif source == '微博热搜':
            if rank <= 20:
                return 4
            elif rank <= 50:
                return 3
            elif rank <= 80:
                return 2
            else:
                return 1
        else:
            # RSS或其他源，根据热度字符串判断
            if heat_str:
                # 简化处理：假设有热度值就给分
                return 2
            return 1
    
    def score_controversy(self, item: Dict) -> int:
        """
        评分：争议性（2分）
        
        评分标准：
        - 2分：具有明显争议性、对立观点、可引发讨论
        - 1分：有一定争议性
        - 0分：无明显争议
        """
        title = item.get('title', '')
        summary = item.get('summary', '')
        text = (title + ' ' + summary).lower()
        
        # 争议性关键词
        controversy_keywords = [
            '争议', '批评', '质疑', '反驳', '反对',
            '冲突', '辩论', '讨论', '争议', '问题',
            '质疑', '负面', '不利', '反驳', '对立'
        ]
        
        count = sum(1 for kw in controversy_keywords if kw in text)
        
        if count >= 2:
            return 2
        elif count >= 1:
            return 1
        else:
            return 0
    
    def score_value(self, item: Dict) -> int:
        """
        评分：价值（3分）
        
        评分标准：
        - 3分：高价值（实用、可操作、信息密度高）
        - 2分：中等价值（有启发性）
        - 1分：一般价值
        - 0分：低价值
        """
        title = item.get('title', '')
        summary = item.get('summary', '')
        text = (title + ' ' + summary).lower()
        
        # 价值关键词
        value_keywords = [
            '教程', '指南', '方法', '技巧', '原理',
            '分析', '解读', '详解', '深入', '学习',
            '实践', '经验', '总结', '技巧', '方案',
            '如何', '怎么', '最佳', '优化', '提升'
        ]
        
        count = sum(1 for kw in value_keywords if kw in text)
        
        # 检查标题长度（通常详细标题价值更高）
        title_length = len(title)
        length_score = 0
        if title_length > 20:
            length_score = 1
        
        if count >= 3:
            return 3
        elif count >= 2:
            return 2
        elif count >= 1:
            return 1
        elif length_score:
            return 1
        else:
            return 0
    
    def score_relevance(self, item: Dict) -> int:
        """
        评分：相关性（1分）
        
        评分标准：
        - 1分：与用户关注的关键词高度相关
        - 0分：无关或相关性低
        """
        if not self.user_keywords:
            # 如果没有配置关键词，默认给1分
            return 1
        
        title = item.get('title', '')
        summary = item.get('summary', '')
        text = (title + ' ' + summary).lower()
        
        # 检查是否包含用户关键词
        for keyword in self.user_keywords:
            if keyword in text:
                return 1
        
        return 0
    
    def score_item(self, item: Dict) -> Dict:
        """
        对单个选题进行评分
        
        Args:
            item: 选题数据
        
        Returns:
            包含评分详情的字典
        """
        heat_score = self.score_heat(item)
        controversy_score = self.score_controversy(item)
        value_score = self.score_value(item)
        relevance_score = self.score_relevance(item)
        
        total_score = heat_score + controversy_score + value_score + relevance_score
        
        return {
            'title': item.get('title', ''),
            'link': item.get('link', ''),
            'source': item.get('source', ''),
            'original_item': item,
            'scores': {
                '热度/趋势': heat_score,
                '争议性': controversy_score,
                '价值': value_score,
                '相关性': relevance_score
            },
            'total_score': total_score,
            'recommend': total_score >= 7  # ≥7分推荐
        }
    
    def filter_topics(self, items: List[Dict], min_score: int = 7) -> Dict:
        """
        批量评分并筛选选题
        
        Args:
            items: 选题列表
            min_score: 最低推荐分数（默认7）
        
        Returns:
            包含评分结果的字典
        """
        scored_items = [self.score_item(item) for item in items]
        
        # 按总分排序
        scored_items.sort(key=lambda x: x['total_score'], reverse=True)
        
        # 筛选推荐选题
        recommended = [item for item in scored_items if item['recommend']]
        
        return {
            'total_items': len(items),
            'recommended_count': len(recommended),
            'min_score': min_score,
            'all_items': scored_items,
            'recommended': recommended
        }


def main():
    parser = argparse.ArgumentParser(description="智能选题筛选系统")
    
    parser.add_argument("--input", required=True, 
                       help="输入文件路径（JSON格式，包含items数组）")
    parser.add_argument("--output", 
                       default="output/filtered_topics.json",
                       help="输出文件路径（默认：output/filtered_topics.json）")
    parser.add_argument("--keywords", nargs='+',
                       help="用户关注的关键词（用于相关性评分）")
    parser.add_argument("--min-score", type=int, default=7,
                       help="最低推荐分数（默认：7）")
    parser.add_argument("--show-all", action='store_true',
                       help="显示所有选题，而不仅仅是推荐选题")
    
    args = parser.parse_args()
    
    try:
        # 读取输入文件
        with open(args.input, 'r', encoding='utf-8') as f:
            input_data = json.load(f)
        
        items = input_data.get('items', [])
        
        if not items:
            print("输入文件中没有找到items数据", file=sys.stderr)
            sys.exit(1)
        
        print(f"正在评分 {len(items)} 个选题...")
        
        # 创建筛选器并评分
        filter = TopicFilter(args.keywords)
        result = filter.filter_topics(items, args.min_score)
        
        # 保存结果
        import os
        os.makedirs(os.path.dirname(args.output), exist_ok=True)
        
        output_data = {
            'filter_time': datetime.now().isoformat(),
            'keywords': args.keywords,
            'min_score': args.min_score,
            'statistics': {
                'total': result['total_items'],
                'recommended': result['recommended_count'],
                'rejected': result['total_items'] - result['recommended_count']
            },
            'recommended': result['recommended'],
            'all_items': result['all_items'] if args.show_all else []
        }
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        # 显示结果
        print("\n" + "="*50)
        print("评分结果")
        print("="*50)
        print(f"总选题数: {result['total_items']}")
        print(f"推荐选题（≥{args.min_score}分）: {result['recommended_count']}")
        print(f"已保存到: {args.output}")
        
        # 显示推荐选题
        print("\n📋 推荐选题（按分数排序）:")
        print("="*50)
        
        for i, item in enumerate(result['recommended'][:10], 1):  # 显示前10个
            print(f"\n{i}. {item['title']}")
            print(f"   来源: {item['source']}")
            print(f"   总分: {item['total_score']}/10")
            print(f"   评分: 热度{item['scores']['热度/趋势']}分 + 争议性{item['scores']['争议性']}分 + 价值{item['scores']['价值']}分 + 相关性{item['scores']['相关性']}分")
            
            if item.get('link'):
                print(f"   链接: {item['link']}")
        
        if result['recommended_count'] == 0:
            print("\n⚠️  没有达到推荐分数的选题")
            print("提示：可以降低 --min-score 参数查看更多选题")
        
        print("\n" + "="*50)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ 筛选失败: {str(e)}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
