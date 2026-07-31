"""
新闻情绪分析模块
分析财经新闻，判断市场情绪，输出情绪评分和交易建议
"""

import re
from datetime import datetime
from typing import List, Dict


# 情绪词典
POSITIVE_WORDS = [
    '上涨', '增长', '突破', '利好', '超预期', '创新高', '反弹', '暴涨', '涨停',
    '回购', '增持', '大单', '净流入', '看多', '牛市', '利好', '龙头', '领涨',
    '盈利', '扭亏', '中标', '签约', '获批', '升级', '扩张', '分红', '高送转',
    '的政策', '降准', '降息', '刺激', '扶持', '减税', '改革', '开放',
    '强势', '向好', '企稳', '回暖', '复苏', '景气', '繁荣', '加速',
    '买入', '增持', '推荐', '超配', '看好', '目标价', '上调评级',
    'AI', '人工智能', '新能源', '芯片', '半导体', '算力', '大模型'
]

NEGATIVE_WORDS = [
    '下跌', '暴跌', '跌停', '利空', '不及预期', '创新低', '回调', '崩盘',
    '减持', '清仓', '抛售', '净流出', '看空', '熊市', '利空', '领跌',
    '亏损', '下滑', '下降', '缩减', '退市', 'ST', '警示', '处罚',
    '收紧', '加息', '通胀', '制裁', '关税', '贸易战', '地缘',
    '疲软', '低迷', '萎缩', '恶化', '放缓', '压力', '风险', '不确定',
    '卖出', '减持', '低配', '看淡', '下调评级', '下调目标价',
    '泡沫', '高估', '过热', '监管', '约谈', '调查', '违规'
]

INTENSIFIERS = ['大幅', '显著', '强烈', '极度', '严重', '暴涨', '暴跌', '断崖', '狂飙']
NEGATORS = ['不', '未', '没有', '并非', '并非', '难以', '乏力', '不及']


class SentimentAnalyzer:
    """新闻情绪分析器"""
    
    def __init__(self, config: dict = None):
        self.config = config or {}
    
    def analyze(self, symbol: str, news_list: List[Dict]) -> dict:
        """
        分析新闻列表，输出情绪评分和判断
        
        Args:
            symbol: 股票代码
            news_list: 新闻列表 [{title, content, time, source}, ...]
        
        Returns:
            情绪分析结果
        """
        if not news_list:
            return {
                'symbol': symbol,
                'sentiment_score': 0,
                'sentiment_label': '中性',
                'news_count': 0,
                'positive_count': 0,
                'negative_count': 0,
                'summary': '无相关新闻',
                'recommendation': 'hold',
                'confidence': 0,
                'timestamp': datetime.now().isoformat()
            }
        
        total_score = 0
        positive_count = 0
        negative_count = 0
        news_details = []
        
        for i, news in enumerate(news_list):
            title = news.get('title', '')
            content = news.get('content', '')
            text = f"{title} {content}"
            
            # 计算单条新闻情绪
            score = self._calc_sentiment_score(text)
            total_score += score
            
            if score > 10:
                positive_count += 1
            elif score < -10:
                negative_count += 1
            
            news_details.append({
                'index': i + 1,
                'title': title[:50],
                'score': score,
                'label': '利好' if score > 10 else ('利空' if score < -10 else '中性')
            })
        
        # 计算综合情绪
        avg_score = total_score / len(news_list) if news_list else 0
        avg_score = max(-100, min(100, avg_score * 2))  # 放大并限制范围
        
        # 情绪标签
        if avg_score >= 30:
            label = '强烈利好'
        elif avg_score >= 10:
            label = '利好'
        elif avg_score >= -10:
            label = '中性'
        elif avg_score >= -30:
            label = '利空'
        else:
            label = '强烈利空'
        
        # 交易建议
        if avg_score >= 20:
            recommendation = 'buy'
        elif avg_score <= -20:
            recommendation = 'sell'
        else:
            recommendation = 'hold'
        
        # 置信度
        news_count = len(news_list)
        confidence = min(90, 30 + news_count * 10 + abs(avg_score) * 0.3)
        
        # 生成摘要
        summary = self._generate_summary(news_details, avg_score)
        
        return {
            'symbol': symbol,
            'sentiment_score': int(avg_score),
            'sentiment_label': label,
            'news_count': news_count,
            'positive_count': positive_count,
            'negative_count': negative_count,
            'summary': summary,
            'recommendation': recommendation,
            'confidence': int(confidence),
            'details': news_details[:5],
            'timestamp': datetime.now().isoformat()
        }
    
    def _calc_sentiment_score(self, text: str) -> float:
        """计算单条文本的情绪分数 (-50 ~ +50)"""
        score = 0
        text_lower = text.lower()
        
        # 正面词匹配
        for word in POSITIVE_WORDS:
            count = len(re.findall(word, text))
            if count > 0:
                weight = 5
                # 检查是否有加强词
                for intensifier in INTENSIFIERS:
                    if intensifier in text:
                        weight = 10
                        break
                score += count * weight
        
        # 负面词匹配
        for word in NEGATIVE_WORDS:
            count = len(re.findall(word, text))
            if count > 0:
                weight = -5
                for intensifier in INTENSIFIERS:
                    if intensifier in text:
                        weight = -10
                        break
                score += count * weight
        
        # 否定词反转
        for neg in NEGATORS:
            # 简化处理：如果否定词后面紧跟正面词，则减分
            for pos in POSITIVE_WORDS[:20]:  # 只检查高频正面词
                pattern = f"{neg}.*?{pos}"
                if re.search(pattern, text):
                    score -= 5
        
        return max(-50, min(50, score))
    
    def _generate_summary(self, details: list, avg_score: float) -> str:
        """生成情绪摘要"""
        if not details:
            return "暂无相关新闻"
        
        positives = [d for d in details if d['score'] > 10]
        negatives = [d for d in details if d['score'] < -10]
        
        parts = []
        if positives:
            top_pos = max(positives, key=lambda x: x['score'])
            parts.append(f"正面消息{len(positives)}条，如「{top_pos['title']}」")
        if negatives:
            top_neg = min(negatives, key=lambda x: x['score'])
            parts.append(f"负面消息{len(negatives)}条，如「{top_neg['title']}」")
        
        if avg_score > 20:
            parts.append("整体情绪偏积极，市场信心较强")
        elif avg_score < -20:
            parts.append("整体情绪偏悲观，需注意风险")
        else:
            parts.append("市场情绪中性，多空分歧较大")
        
        return "；".join(parts)


if __name__ == '__main__':
    import sys
    analyzer = SentimentAnalyzer()
    
    # 测试
    test_news = [
        {'title': '贵州茅台：一季度营收同比增长20%，超市场预期', 'content': '', 'source': '财联社'},
        {'title': '白酒板块获多家券商上调评级，行业景气度持续回升', 'content': '', 'source': '东方财富'},
        {'title': '茅台集团拟回购股份不超过200亿元', 'content': '', 'source': '新浪财经'},
        {'title': '消费复苏趋势明显，高端白酒需求旺盛', 'content': '', 'source': '财联社'},
        {'title': '监管层关注白酒价格波动，提醒理性投资', 'content': '', 'source': '东方财富'},
    ]
    
    result = analyzer.analyze('600519.SH', test_news)
    print(f"情绪评分: {result['sentiment_score']}")
    print(f"情绪标签: {result['sentiment_label']}")
    print(f"交易建议: {result['recommendation']}")
    print(f"置信度: {result['confidence']}%")
    print(f"摘要: {result['summary']}")
    print(f"\n详情:")
    for d in result.get('details', []):
        print(f"  {d['index']}. [{d['label']}] {d['title']} (分:{d['score']})")
