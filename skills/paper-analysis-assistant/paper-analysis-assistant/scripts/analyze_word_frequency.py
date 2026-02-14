#!/usr/bin/env python3
"""
词频分析，过滤停用词
"""
import argparse
import os
import re
import pandas as pd
import sys


def load_stopwords(stopwords_path: str) -> set:
    """
    加载停用词列表

    Args:
        stopwords_path: 停用词文件路径

    Returns:
        停用词集合
    """
    stopwords = set()
    try:
        with open(stopwords_path, 'r', encoding='utf-8') as f:
            for line in f:
                word = line.strip().lower()
                if word:
                    stopwords.add(word)
    except FileNotFoundError:
        print(f"警告: 停用词文件未找到: {stopwords_path}")

    return stopwords


def analyze_word_frequency(txt_path: str, output_path: str, stopwords_path: str = None) -> None:
    """
    分析文本词频，过滤停用词

    Args:
        txt_path: 文本文件路径
        output_path: 输出 csv 文件路径
        stopwords_path: 停用词文件路径
    """
    print(f"正在进行词频分析: {txt_path}")

    # 加载停用词
    if stopwords_path and os.path.exists(stopwords_path):
        stopwords = load_stopwords(stopwords_path)
    else:
        # 如果没有提供停用词文件，使用默认停用词（只过滤一些常见的）
        stopwords = {'the', 'and', 'is', 'in', 'to', 'of', 'a', 'for', 'that', 'it', 'on', 'with',
                    'as', 'this', 'are', 'be', 'was', 'at', 'by', 'an', 'or', 'from', 'but',
                    'not', 'which', 'we', 'you', 'their', 'they', 'have', 'has', 'had', 'can'}

    # 读取文本
    with open(txt_path, 'r', encoding='utf-8') as f:
        text = f.read().lower()

    # 使用正则表达式提取单词
    words = re.findall(r'\b[a-z]{3,}\b', text)

    # 过滤停用词
    filtered_words = [word for word in words if word not in stopwords]

    # 统计词频
    word_freq = {}
    for word in filtered_words:
        word_freq[word] = word_freq.get(word, 0) + 1

    # 转换为 DataFrame
    df = pd.DataFrame(list(word_freq.items()), columns=['word', 'frequency'])
    df = df.sort_values('frequency', ascending=False).reset_index(drop=True)

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # 保存为 CSV
    df.to_csv(output_path, index=False, encoding='utf-8')

    print(f"词频统计已保存到: {output_path}")
    print(f"总词数: {len(words)}, 过滤后词数: {len(filtered_words)}, 唯一词数: {len(word_freq)}")
    print(f"前10个高频词:\n{df.head(10)}")


def main():
    parser = argparse.ArgumentParser(description='词频分析，过滤停用词')
    parser.add_argument('--txt', required=True, help='文本文件路径')
    parser.add_argument('--output', required=True, help='输出 csv 文件路径')
    parser.add_argument('--stopwords', help='停用词文件路径（可选）')
    args = parser.parse_args()

    # 默认停用词路径
    default_stopwords = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                    'references', 'stopwords.txt')

    stopwords_path = args.stopwords if args.stopwords else default_stopwords
    analyze_word_frequency(args.txt, args.output, stopwords_path)


if __name__ == '__main__':
    main()
