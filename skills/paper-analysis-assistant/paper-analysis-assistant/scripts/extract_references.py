#!/usr/bin/env python3
"""
提取论文中的引用链接
"""
import argparse
import os
import re
import pandas as pd


def extract_references(txt_path: str, output_path: str) -> None:
    """
    提取论文中的引用链接和 arXiv 引用

    Args:
        txt_path: 文本文件路径
        output_path: 输出 csv 文件路径
    """
    print(f"正在提取引用链接: {txt_path}")

    # 读取文本
    with open(txt_path, 'r', encoding='utf-8') as f:
        text = f.read()

    references = []

    # 1. 提取 HTTP/HTTPS 链接
    url_pattern = r'https?://[^\s\)\]\}]+'
    urls = re.findall(url_pattern, text)
    for url in urls:
        references.append({
            'type': 'URL',
            'content': url,
            'context': 'Direct URL reference'
        })

    # 2. 提取 arXiv 引用（多种格式）
    # 格式: arXiv:2301.00001, arXiv preprint 2301.00001 等
    arxiv_patterns = [
        r'arXiv:\s*(\d{4}\.\d{4,5})',
        r'arXiv\s+preprint\s+(\d{4}\.\d{4,5})',
        r'\b(\d{4}\.\d{4,5})\s*\[arXiv\]'
    ]

    arxiv_ids = set()
    for pattern in arxiv_patterns:
        matches = re.findall(pattern, text)
        arxiv_ids.update(matches)

    for arxiv_id in arxiv_ids:
        references.append({
            'type': 'arXiv',
            'content': f'https://arxiv.org/abs/{arxiv_id}',
            'context': 'arXiv reference'
        })

    # 3. 提取 DOI 引用
    doi_pattern = r'doi:\s*(10\.\d{4,}/[^\s]+)'
    dois = re.findall(doi_pattern, text, re.IGNORECASE)
    for doi in dois:
        references.append({
            'type': 'DOI',
            'content': f'https://doi.org/{doi}',
            'context': 'DOI reference'
        })

    # 4. 提取常见的引用格式（如 [1], (Author et al., 2023)）
    # 这里只提取模式，具体内容需要更复杂的解析
    citation_pattern = r'\[\d+\]|\([A-Z][a-z]+(\s+et\s+al\.?|\s+and\s+[A-Z][a-z]+),\s+\d{4}\)'
    citations = re.findall(citation_pattern, text)
    for citation in set(citations):
        references.append({
            'type': 'Citation',
            'content': citation,
            'context': 'In-text citation'
        })

    # 转换为 DataFrame
    if references:
        df = pd.DataFrame(references)
    else:
        # 如果没有找到引用，创建空 DataFrame
        df = pd.DataFrame(columns=['type', 'content', 'context'])

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # 保存为 CSV
    df.to_csv(output_path, index=False, encoding='utf-8')

    print(f"引用列表已保存到: {output_path}")
    print(f"共找到 {len(references)} 个引用")

    if not df.empty:
        print(f"\n引用类型分布:")
        print(df['type'].value_counts())


def main():
    parser = argparse.ArgumentParser(description='提取论文中的引用链接')
    parser.add_argument('--txt', required=True, help='文本文件路径')
    parser.add_argument('--output', required=True, help='输出 csv 文件路径')
    args = parser.parse_args()

    extract_references(args.txt, args.output)


if __name__ == '__main__':
    main()
