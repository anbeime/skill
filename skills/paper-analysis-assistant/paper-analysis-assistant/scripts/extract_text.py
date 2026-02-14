#!/usr/bin/env python3
"""
从 PDF 文件中提取纯文本
"""
import argparse
import os
import pdfplumber


def extract_text_from_pdf(pdf_path: str, output_path: str) -> None:
    """
    从 PDF 文件中提取纯文本

    Args:
        pdf_path: PDF 文件路径
        output_path: 输出 txt 文件路径
    """
    print(f"正在提取文本: {pdf_path}")

    text_content = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    # 清理文本
                    text = text.strip()
                    # 移除多余的空行
                    text = '\n'.join(line for line in text.split('\n') if line.strip())
                    text_content.append(text)

        # 合并所有页面内容
        full_text = '\n\n'.join(text_content)

        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        # 保存文本
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(full_text)

        print(f"文本已保存到: {output_path}")
        print(f"提取了 {len(pdfplumber.open(pdf_path).pages)} 页，{len(full_text)} 个字符")

    except Exception as e:
        raise Exception(f"提取 PDF 文本失败: {str(e)}")


def main():
    parser = argparse.ArgumentParser(description='从 PDF 文件中提取纯文本')
    parser.add_argument('--pdf', required=True, help='PDF 文件路径')
    parser.add_argument('--output', required=True, help='输出 txt 文件路径')
    args = parser.parse_args()

    extract_text_from_pdf(args.pdf, args.output)


if __name__ == '__main__':
    main()
