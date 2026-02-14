#!/usr/bin/env python3
"""
生成交互式网页
"""
import argparse
import os
import pandas as pd


def generate_html(txt_path: str, word_freq_path: str, output_path: str) -> None:
    """
    生成交互式 HTML 网页

    Args:
        txt_path: 文本文件路径
        word_freq_path: 词频统计文件路径
        output_path: 输出 html 文件路径
    """
    print(f"正在生成交互式网页...")

    # 读取文本
    with open(txt_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # 读取词频统计
    df = pd.read_csv(word_freq_path)
    top_words = df.head(50)

    # 生成 HTML
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>论文分析报告</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        .subtitle {{
            color: #7f8c8d;
            margin-bottom: 30px;
            font-size: 14px;
        }}
        .section {{
            margin-bottom: 40px;
        }}
        h2 {{
            color: #34495e;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .paper-content {{
            background: #f9f9f9;
            padding: 20px;
            border-radius: 5px;
            max-height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
            font-size: 14px;
        }}
        .word-cloud {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            padding: 20px;
            background: #f0f3f4;
            border-radius: 5px;
        }}
        .word-tag {{
            padding: 8px 16px;
            background: #3498db;
            color: white;
            border-radius: 20px;
            font-size: 12px;
            transition: all 0.3s;
        }}
        .word-tag:hover {{
            background: #2980b9;
            transform: scale(1.1);
        }}
        .word-freq {{
            font-weight: bold;
            margin-left: 5px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 32px;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .stat-label {{
            font-size: 14px;
            opacity: 0.9;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #34495e;
            color: white;
        }}
        tr:hover {{
            background: #f5f5f5;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>论文分析报告</h1>
        <p class="subtitle">自动生成于分析助手</p>

        <div class="section">
            <h2>统计概览</h2>
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">{len(text):,}</div>
                    <div class="stat-label">总字符数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(text.split()):,}</div>
                    <div class="stat-label">总词数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{len(top_words):,}</div>
                    <div class="stat-label">高频词汇</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{top_words['frequency'].sum():,}</div>
                    <div class="stat-label">词频总和</div>
                </div>
            </div>
        </div>

        <div class="section">
            <h2>高频词汇云</h2>
            <div class="word-cloud">
"""

    # 添加词汇云
    max_freq = top_words['frequency'].max()
    for _, row in top_words.iterrows():
        size = 12 + (row['frequency'] / max_freq) * 8
        opacity = 0.7 + (row['frequency'] / max_freq) * 0.3
        html_content += f'<span class="word-tag" style="font-size: {size}px; opacity: {opacity};">{row["word"]}<span class="word-freq">({row["frequency"]})</span></span>\n'

    html_content += """            </div>
        </div>

        <div class="section">
            <h2>词频统计表</h2>
            <table>
                <thead>
                    <tr>
                        <th>排名</th>
                        <th>单词</th>
                        <th>出现次数</th>
                    </tr>
                </thead>
                <tbody>
"""

    # 添加词频表格
    for idx, row in top_words.iterrows():
        html_content += f'                    <tr><td>{idx + 1}</td><td>{row["word"]}</td><td>{row["frequency"]}</td></tr>\n'

    html_content += """                </tbody>
            </table>
        </div>

        <div class="section">
            <h2>论文内容预览</h2>
            <div class="paper-content">
"""
    preview_text = text[:5000]
    if len(text) > 5000:
        preview_text += '\\n\\n...(内容过长，仅显示前5000字符)...'
    html_content += preview_text
    html_content += """
            </div>
        </div>
    </div>
</body>
</html>"""

    # 确保输出目录存在
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    # 保存 HTML
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)

    print(f"交互式网页已保存到: {output_path}")


def main():
    parser = argparse.ArgumentParser(description='生成交互式网页')
    parser.add_argument('--txt', required=True, help='文本文件路径')
    parser.add_argument('--word_freq', required=True, help='词频统计文件路径')
    parser.add_argument('--output', required=True, help='输出 html 文件路径')
    args = parser.parse_args()

    generate_html(args.txt, args.word_freq, args.output)


if __name__ == '__main__':
    main()
