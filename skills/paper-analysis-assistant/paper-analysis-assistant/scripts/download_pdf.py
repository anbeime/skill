#!/usr/bin/env python3
"""
下载 arXiv 论文 PDF
"""
import argparse
import os
import re
import requests
from urllib.parse import urlparse


def download_arxiv_pdf(arxiv_url: str, output_path: str) -> None:
    """
    从 arXiv 网址下载 PDF 文件

    Args:
        arxiv_url: arXiv 论文网址（支持 abs 或 pdf 格式）
        output_path: 输出 PDF 文件路径
    """
    # 提取 arXiv ID
    # 支持: https://arxiv.org/abs/2301.00001, https://arxiv.org/pdf/2301.00001.pdf
    arxiv_id = None

    # 尝试匹配 abs 格式
    match = re.search(r'arxiv\.org/abs/(\d+\.\d+)', arxiv_url)
    if match:
        arxiv_id = match.group(1)
    else:
        # 尝试匹配 pdf 格式
        match = re.search(r'arxiv\.org/pdf/(\d+\.\d+)', arxiv_url)
        if match:
            arxiv_id = match.group(1)
        else:
            # 尝试直接匹配数字点数字格式
            match = re.search(r'(\d{4}\.\d{4,5})', arxiv_url)
            if match:
                arxiv_id = match.group(1)

    if not arxiv_id:
        raise ValueError(f"无法从网址中提取 arXiv ID: {arxiv_url}")

    # 构建 PDF 下载链接
    pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

    print(f"正在下载: {pdf_url}")

    # 下载 PDF
    response = requests.get(pdf_url, stream=True, timeout=60)
    response.raise_for_status()

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # 保存文件
    with open(output_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)

    print(f"PDF 已保存到: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='下载 arXiv 论文 PDF')
    parser.add_argument('--url', required=True, help='arXiv 论文网址')
    parser.add_argument('--output', required=True, help='输出 PDF 文件路径')
    args = parser.parse_args()

    download_arxiv_pdf(args.url, args.output)


if __name__ == '__main__':
    main()
