#!/usr/bin/env python3
"""
HTML报告生成脚本

功能：
- 生成专业的HTML格式股票分析报告
- 内嵌CSS样式，支持响应式设计
- 嵌入图表和图片
- 支持数据表格展示

依赖：
- jinja2: HTML模板引擎
- pandas: 数据处理
"""

import argparse
import json
import os
import sys
from datetime import datetime
from jinja2 import Template


# HTML模板（包含内嵌CSS）
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ company_name }} - 股票分析报告</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        
        /* Header */
        .header {
            background: linear-gradient(135deg, #2E86AB 0%, #A23B72 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header .meta {
            display: flex;
            justify-content: center;
            gap: 30px;
            margin-top: 20px;
            flex-wrap: wrap;
        }
        
        .header .meta-item {
            background: rgba(255,255,255,0.2);
            padding: 10px 20px;
            border-radius: 25px;
            backdrop-filter: blur(10px);
        }
        
        .risk-badge {
            display: inline-block;
            padding: 8px 20px;
            border-radius: 20px;
            font-weight: bold;
            margin-left: 10px;
        }
        
        .risk-low { background: #4CAF50; color: white; }
        .risk-medium { background: #FF9800; color: white; }
        .risk-high { background: #f44336; color: white; }
        
        /* Sections */
        .section {
            padding: 40px;
            border-bottom: 1px solid #eee;
        }
        
        .section:last-child {
            border-bottom: none;
        }
        
        .section-title {
            font-size: 1.8em;
            color: #2E86AB;
            margin-bottom: 25px;
            padding-bottom: 10px;
            border-bottom: 3px solid #2E86AB;
            display: flex;
            align-items: center;
        }
        
        .section-title::before {
            content: '';
            display: inline-block;
            width: 8px;
            height: 30px;
            background: #2E86AB;
            margin-right: 15px;
            border-radius: 4px;
        }
        
        /* Core Conclusion */
        .core-conclusion {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }
        
        .core-conclusion h2 {
            margin-bottom: 20px;
            font-size: 1.5em;
        }
        
        .conclusion-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }
        
        .conclusion-item {
            background: rgba(255,255,255,0.2);
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        
        .conclusion-item .label {
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 10px;
        }
        
        .conclusion-item .value {
            font-size: 2em;
            font-weight: bold;
        }
        
        /* Company Info */
        .company-info {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }
        
        .info-card {
            background: #f8f9fa;
            padding: 25px;
            border-radius: 10px;
            border-left: 4px solid #2E86AB;
        }
        
        .info-card h3 {
            color: #2E86AB;
            margin-bottom: 15px;
            font-size: 1.2em;
        }
        
        .info-card ul {
            list-style: none;
        }
        
        .info-card li {
            padding: 8px 0;
            border-bottom: 1px solid #e0e0e0;
            display: flex;
            justify-content: space-between;
        }
        
        .info-card li:last-child {
            border-bottom: none;
        }
        
        /* Tables */
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            border-radius: 8px;
            overflow: hidden;
        }
        
        .data-table thead {
            background: linear-gradient(135deg, #2E86AB 0%, #A23B72 100%);
            color: white;
        }
        
        .data-table th,
        .data-table td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .data-table tbody tr:hover {
            background: #f5f5f5;
            transition: background 0.3s;
        }
        
        .rating-good { color: #4CAF50; font-weight: bold; }
        .rating-neutral { color: #FF9800; font-weight: bold; }
        .rating-bad { color: #f44336; font-weight: bold; }
        
        /* Charts */
        .charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 30px;
        }
        
        .chart-container {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }
        
        .chart-container h3 {
            color: #2E86AB;
            margin-bottom: 15px;
        }
        
        .chart-container img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        /* Risk Assessment */
        .risk-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .risk-item {
            background: white;
            border: 2px solid #e0e0e0;
            padding: 20px;
            border-radius: 10px;
            transition: all 0.3s;
        }
        
        .risk-item:hover {
            transform: translateY(-5px);
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
        }
        
        .risk-item h4 {
            color: #2E86AB;
            margin-bottom: 15px;
            font-size: 1.1em;
        }
        
        .risk-score {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-top: 10px;
        }
        
        .risk-bar {
            flex: 1;
            height: 20px;
            background: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin: 0 15px;
        }
        
        .risk-fill {
            height: 100%;
            background: linear-gradient(90deg, #4CAF50 0%, #FF9800 50%, #f44336 100%);
            border-radius: 10px;
            transition: width 0.5s ease;
        }
        
        /* Trading Points */
        .trading-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        
        .trading-table th {
            background: #2E86AB;
            color: white;
            padding: 15px;
            text-align: center;
            font-weight: bold;
        }
        
        .trading-table td {
            padding: 15px;
            text-align: center;
            border: 1px solid #e0e0e0;
        }
        
        .trading-table tbody tr:nth-child(even) {
            background: #f9f9f9;
        }
        
        .buy { background: #4CAF50 !important; color: white; }
        .sell { background: #f44336 !important; color: white; }
        .hold { background: #FF9800 !important; color: white; }
        
        /* Footer */
        .footer {
            background: #f8f9fa;
            padding: 30px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
            border-top: 1px solid #e0e0e0;
        }
        
        .disclaimer {
            background: #fff3cd;
            border: 1px solid #ffc107;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
            text-align: left;
        }
        
        .disclaimer strong {
            color: #856404;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .header h1 {
                font-size: 1.8em;
            }
            
            .section {
                padding: 20px;
            }
            
            .charts-grid {
                grid-template-columns: 1fr;
            }
            
            .company-info {
                grid-template-columns: 1fr;
            }
        }
        
        /* Print Styles */
        @media print {
            body {
                background: white;
                padding: 0;
            }
            
            .container {
                box-shadow: none;
            }
            
            .section {
                page-break-inside: avoid;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>{{ company_name }}</h1>
            <div class="meta">
                <div class="meta-item">股票代码: {{ symbol }}</div>
                <div class="meta-item">分析日期: {{ analysis_date }}</div>
                <div class="meta-item">
                    风险等级: 
                    <span class="risk-badge {{ risk_class }}">{{ risk_level }} ({{ risk_score }}/10)</span>
                </div>
            </div>
        </div>
        
        <!-- Core Conclusion -->
        <div class="section">
            <h2 class="section-title">核心结论</h2>
            <div class="core-conclusion">
                <h2>{{ one_line_summary }}</h2>
                <div class="conclusion-grid">
                    <div class="conclusion-item">
                        <div class="label">投资建议</div>
                        <div class="value">{{ recommendation }}</div>
                    </div>
                    <div class="conclusion-item">
                        <div class="label">预期收益</div>
                        <div class="value">{{ expected_return }}</div>
                    </div>
                    <div class="conclusion-item">
                        <div class="label">最大风险</div>
                        <div class="value">{{ max_risk }}</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Company Overview -->
        <div class="section">
            <h2 class="section-title">公司概览</h2>
            <div class="company-info">
                <div class="info-card">
                    <h3>基本信息</h3>
                    <ul>
                        <li><span>公司名称</span><span>{{ company_name }}</span></li>
                        <li><span>所属行业</span><span>{{ industry }}</span></li>
                        <li><span>总市值</span><span>{{ market_cap }}</span></li>
                        <li><span>当前股价</span><span>{{ current_price }}</span></li>
                    </ul>
                </div>
                <div class="info-card">
                    <h3>关键财务指标</h3>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>指标</th>
                                <th>数值</th>
                                <th>评级</th>
                            </tr>
                        </thead>
                        <tbody>
                            {{ financial_indicators_rows }}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
        
        <!-- Technical Charts -->
        <div class="section">
            <h2 class="section-title">技术分析图表</h2>
            <div class="charts-grid">
                {{ chart_sections }}
            </div>
        </div>
        
        <!-- Fundamental Analysis -->
        <div class="section">
            <h2 class="section-title">基本面分析</h2>
            <h3>财务健康度评分: {{ fundamental_score }}/10</h3>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>评估维度</th>
                        <th>评分</th>
                        <th>说明</th>
                    </tr>
                </thead>
                <tbody>
                    {{ fundamental_rows }}
                </tbody>
            </table>
        </div>
        
        <!-- Risk Assessment -->
        <div class="section">
            <h2 class="section-title">风险评估</h2>
            <h3>综合风险评分: {{ overall_risk_score }}/10</h3>
            <div class="risk-grid">
                {{ risk_items }}
            </div>
        </div>
        
        <!-- Trading Points -->
        <div class="section">
            <h2 class="section-title">投资建议</h2>
            <h3>精确买卖点位</h3>
            <table class="trading-table">
                <thead>
                    <tr>
                        <th>操作</th>
                        <th>价格区间</th>
                        <th>理由</th>
                        <th>仓位比例</th>
                    </tr>
                </thead>
                <tbody>
                    {{ trading_rows }}
                </tbody>
            </table>
        </div>
        
        <!-- Footer -->
        <div class="footer">
            <p>报告生成时间: {{ generation_time }}</p>
            <div class="disclaimer">
                <strong>免责声明：</strong>
                <p>本报告由AI分析系统生成，仅供参考，不构成任何投资建议。股票投资存在风险，市场有风险，投资需谨慎。</p>
                <p>本报告基于历史数据和公开信息分析，不保证未来表现。投资者应根据自身风险承受能力独立做出投资决策。</p>
            </div>
        </div>
    </div>
</body>
</html>
"""


def generate_html_report(data, charts_dir, output_path):
    """
    生成HTML报告
    
    参数:
        data: 报告数据字典
        charts_dir: 图表目录
        output_path: 输出文件路径
    
    返回:
        dict: 生成结果
    """
    try:
        # 创建Jinja2模板
        template = Template(HTML_TEMPLATE)
        
        # 准备数据
        template_data = {
            'company_name': data.get('company_name', 'N/A'),
            'symbol': data.get('symbol', 'N/A'),
            'analysis_date': data.get('analysis_date', datetime.now().strftime('%Y-%m-%d')),
            'risk_level': data.get('risk_level', '中等风险'),
            'risk_score': data.get('risk_score', 5),
            'risk_class': get_risk_class(data.get('risk_score', 5)),
            'one_line_summary': data.get('one_line_summary', '暂无总结'),
            'recommendation': data.get('recommendation', '持有'),
            'expected_return': data.get('expected_return', '+0%'),
            'max_risk': data.get('max_risk', '-0%'),
            'industry': data.get('industry', 'N/A'),
            'market_cap': data.get('market_cap', 'N/A'),
            'current_price': data.get('current_price', 'N/A'),
            'fundamental_score': data.get('fundamental_score', 5),
            'overall_risk_score': data.get('overall_risk_score', 5),
            'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'financial_indicators_rows': generate_financial_rows(data.get('financial_indicators', [])),
            'chart_sections': generate_chart_sections(data.get('charts', []), charts_dir),
            'fundamental_rows': generate_fundamental_rows(data.get('fundamental_details', [])),
            'risk_items': generate_risk_items(data.get('risk_details', [])),
            'trading_rows': generate_trading_rows(data.get('trading_points', []))
        }
        
        # 渲染HTML
        html_content = template.render(**template_data)
        
        # 保存文件
        output_dir = os.path.dirname(output_path)
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        return {
            'success': True,
            'file_path': output_path,
            'file_size': len(html_content)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def get_risk_class(score):
    """根据风险分数返回CSS类名"""
    if score <= 3:
        return 'risk-low'
    elif score <= 6:
        return 'risk-medium'
    else:
        return 'risk-high'


def generate_financial_rows(indicators):
    """生成财务指标表格行"""
    rows = []
    for item in indicators:
        rating_class = get_rating_class(item.get('rating', '中性'))
        rows.append(f'''
                    <tr>
                        <td>{item.get('metric', 'N/A')}</td>
                        <td>{item.get('value', 'N/A')}</td>
                        <td class="{rating_class}">{item.get('rating', 'N/A')}</td>
                    </tr>
                ''')
    return '\n'.join(rows)


def get_rating_class(rating):
    """根据评级返回CSS类名"""
    if rating in ['优秀', '高', '偏低', '良好']:
        return 'rating-good'
    elif rating in ['一般', '中']:
        return 'rating-neutral'
    else:
        return 'rating-bad'


def generate_chart_sections(charts, charts_dir):
    """生成图表部分"""
    sections = []
    chart_types = {
        'price_chart': '股价走势图',
        'candlestick': 'K线图与成交量',
        'macd': 'MACD指标',
        'rsi': 'RSI指标'
    }
    
    for chart in charts:
        chart_type = chart.get('type', 'unknown')
        chart_name = chart_types.get(chart_type, chart_type)
        chart_path = os.path.join(charts_dir, chart.get('filename', ''))
        
        sections.append(f'''
                <div class="chart-container">
                    <h3>{chart_name}</h3>
                    <img src="{chart_path}" alt="{chart_name}">
                </div>
            ''')
    
    return '\n'.join(sections)


def generate_fundamental_rows(details):
    """生成基本面分析行"""
    rows = []
    for item in details:
        rows.append(f'''
                    <tr>
                        <td>{item.get('dimension', 'N/A')}</td>
                        <td>{item.get('score', 'N/A')}/10</td>
                        <td>{item.get('description', 'N/A')}</td>
                    </tr>
                ''')
    return '\n'.join(rows)


def generate_risk_items(details):
    """生成风险评估项"""
    items = []
    for item in details:
        score = item.get('score', 0)
        weight = item.get('weight', 0)
        weighted_score = score * weight
        percentage = (score / 10) * 100
        
        items.append(f'''
                <div class="risk-item">
                    <h4>{item.get('dimension', 'N/A')} (权重{weight*100}%)</h4>
                    <div class="risk-score">
                        <span>{score}/10</span>
                        <div class="risk-bar">
                            <div class="risk-fill" style="width: {percentage}%"></div>
                        </div>
                        <span>{weighted_score:.1f}</span>
                    </div>
                </div>
            ''')
    
    return '\n'.join(items)


def generate_trading_rows(points):
    """生成交易点位行"""
    rows = []
    action_classes = {
        '买入': 'buy',
        '卖出': 'sell',
        '止损': 'sell',
        '止盈': 'sell',
        '观望建议': 'hold'
    }
    
    for point in points:
        action = point.get('action', '观望建议')
        action_class = action_classes.get(action, 'hold')
        
        rows.append(f'''
                    <tr class="{action_class}">
                        <td>{action}</td>
                        <td>{point.get('price_range', 'N/A')}</td>
                        <td>{point.get('reason', 'N/A')}</td>
                        <td>{point.get('position', 'N/A')}</td>
                    </tr>
                ''')
    
    return '\n'.join(rows)


def main():
    parser = argparse.ArgumentParser(description='生成HTML格式股票分析报告')
    parser.add_argument('--data', type=str, required=True, help='报告数据JSON文件')
    parser.add_argument('--charts-dir', type=str, default='./charts', help='图表目录')
    parser.add_argument('--output', type=str, default='report.html', help='输出HTML文件路径')
    
    args = parser.parse_args()
    
    # 读取数据文件
    with open(args.data, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 生成HTML报告
    result = generate_html_report(data, args.charts_dir, args.output)
    
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
