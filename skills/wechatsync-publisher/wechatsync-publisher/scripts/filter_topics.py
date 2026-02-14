#!/usr/bin/env python3
"""
选题筛选脚本
使用10分制打分系统筛选优质选题

评分标准：
- 热度：4分（当前热点程度）
- 争议性：2分（是否有争议或讨论点）
- 价值：3分（实用价值/信息密度）
- 相关性：1分（与目标受众的相关性）

使用方法：
python filter_topics.py --topics "AI技术,AI伦理,人工智能" --threshold 7
"""

import argparse
import json
import sys


def filter_topics(topics, threshold=7):
    """
    筛选选题

    Args:
        topics: 主题列表（格式：["主题1:热度,争议性,价值,相关性"]）
        threshold: 分数阈值，>=7分进入推荐池

    Returns:
        dict: 筛选结果
    """
    recommendations = []

    for topic_data in topics:
        # 解析主题和评分
        if ":" in topic_data:
            parts = topic_data.split(":")
            topic = parts[0]
            scores = parts[1].split(",") if len(parts) > 1 else ["5", "3", "4", "5"]
        else:
            topic = topic_data
            # 默认评分
            scores = ["5", "3", "4", "5"]

        # 转换为整数
        try:
            heat = int(scores[0]) if len(scores) > 0 else 5  # 热度
            controversy = int(scores[1]) if len(scores) > 1 else 3  # 争议性
            value = int(scores[2]) if len(scores) > 2 else 4  # 价值
            relevance = int(scores[3]) if len(scores) > 3 else 5  # 相关性
        except ValueError:
            heat, controversy, value, relevance = 5, 3, 4, 5

        # 计算总分
        total = heat + controversy + value + relevance

        # 判断是否达到阈值
        if total >= threshold:
            recommendations.append({
                "topic": topic,
                "heat": heat,
                "controversy": controversy,
                "value": value,
                "relevance": relevance,
                "total": total
            })

    # 按总分降序排序
    recommendations.sort(key=lambda x: x["total"], reverse=True)

    return {
        "success": True,
        "threshold": threshold,
        "total_topics": len(topics),
        "recommended_count": len(recommendations),
        "recommendations": recommendations
    }


def main():
    """主函数，处理命令行参数"""
    parser = argparse.ArgumentParser(description="选题筛选脚本")
    parser.add_argument("--topics", required=True, help="主题列表，用逗号分隔（格式：主题:热度,争议性,价值,相关性）")
    parser.add_argument("--threshold", type=int, default=7, help="分数阈值（默认7分）")

    args = parser.parse_args()

    # 解析主题列表
    topics = [topic.strip() for topic in args.topics.split(",")]

    # 筛选选题
    result = filter_topics(
        topics=topics,
        threshold=args.threshold
    )

    # 输出结果
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 返回退出码
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
