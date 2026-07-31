#!/usr/bin/env python3
"""
增强版HTML报告生成脚本

功能：
- 生成专业、丰富的HTML格式股票分析报告
- 包含多种图表：股价走势图、K线图、MACD、RSI、财务趋势图、情绪趋势图、风险雷达图
- 支持公司Logo和产品图片嵌入
- 使用Plotly生成交互式图表
- 响应式设计，支持移动端

依赖：
- jinja2: HTML模板引擎
- pandas: 数据处理
- plotly: 交互式图表生成
- matplotlib: 静态图表
"""

import argparse
import json
import os
import sys
import base64
from datetime import datetime
from jinja2 import Template
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np


# 增强版HTML模板（包含更丰富的图表和图片）
ENHANCED_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ company_name }} - 股票分析报告</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
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
            max-width: 1400px;
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
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .header-left {
            flex: 1;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .company-logo {
            width: 120px;
            height: 120px;
            border-radius: 15px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.3);
            border: 4px solid rgba(255,255,255,0.3);
        }
        
        .header .meta {
            display: flex;
            gap: 20px;
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
            padding: 10px 25px;
            border-radius: 25px;
            font-weight: bold;
            font-size: 1.1em;
        }
        
        .risk-low { background: #4CAF50; }
        .risk-medium { background: #FF9800; }
        .risk-high { background: #f44336; }
        
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
            margin-bottom: 30px;
            padding-bottom: 15px;
            border-bottom: 3px solid #2E86AB;
            display: flex;
            align-items: center;
        }
        
        .section-title::before {
            content: '';
            display: inline-block;
            width: 8px;
            height: 35px;
            background: linear-gradient(135deg, #2E86AB 0%, #A23B72 100%);
            margin-right: 15px;
            border-radius: 4px;
        }
        
        /* Core Conclusion */
        .core-conclusion {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 35px;
            border-radius: 15px;
            margin-bottom: 30px;
        }
        
        .core-conclusion h2 {
            margin-bottom: 25px;
            font-size: 1.6em;
        }
        
        .conclusion-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 25px;
            margin-top: 25px;
        }
        
        .conclusion-item {
            background: rgba(255,255,255,0.25);
            padding: 25px;
            border-radius: 12px;
            text-align: center;
            backdrop-filter: blur(10px);
            transition: transform 0.3s;
        }
        
        .conclusion-item:hover {
            transform: translateY(-5px);
        }
        
        .conclusion-item .label {
            font-size: 0.95em;
            opacity: 0.9;
            margin-bottom: 12px;
        }
        
        .conclusion-item .value {
            font-size: 2.2em;
            font-weight: bold;
        }
        
        /* Company Info */
        .company-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
            margin-bottom: 30px;
        }
        
        .info-card {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 30px;
            border-radius: 15px;
            border-left: 5px solid #2E86AB;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }
        
        .info-card h3 {
            color: #2E86AB;
            margin-bottom: 20px;
            font-size: 1.3em;
        }
        
        .info-card ul {
            list-style: none;
        }
        
        .info-card li {
            padding: 12px 0;
            border-bottom: 1px solid #dee2e6;
            display: flex;
            justify-content: space-between;
            font-size: 1.05em;
        }
        
        .info-card li:last-child {
            border-bottom: none;
        }
        
        /* Product Images Gallery */
        .image-gallery {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        
        .image-card {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 3px 10px rgba(0,0,0,0.1);
        }
        
        .image-card img {
            width: 100%;
            height: 200px;
            object-fit: cover;
            border-radius: 8px;
            margin-bottom: 10px;
        }
        
        .image-card p {
            color: #666;
            font-size: 0.9em;
        }
        
        /* Tables */
        .data-table {
            width: 100%;
            border-collapse: collapse;
            margin: 25px 0;
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
            border-radius: 12px;
            overflow: hidden;
        }
        
        .data-table thead {
            background: linear-gradient(135deg, #2E86AB 0%, #A23B72 100%);
            color: white;
        }
        
        .data-table th,
        .data-table td {
            padding: 18px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .data-table tbody tr:hover {
            background: #f5f5f5;
            transition: background 0.3s;
        }
        
        .rating-good { color: #4CAF50; font-weight: bold; font-size: 1.1em; }
        .rating-neutral { color: #FF9800; font-weight: bold; font-size: 1.1em; }
        .rating-bad { color: #f44336; font-weight: bold; font-size: 1.1em; }
        
        /* Charts Section */
        .charts-section {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
        }
        
        .chart-wrapper {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }
        
        .chart-wrapper h3 {
            color: #2E86AB;
            margin-bottom: 20px;
            font-size: 1.3em;
            text-align: center;
        }
        
        .chart-wrapper .plotly-graph-div {
            margin: 0 auto;
        }
        
        /* Static Charts Grid */
        .static-charts-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(550px, 1fr));
            gap: 30px;
        }
        
        .static-chart-container {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 3px 15px rgba(0,0,0,0.1);
        }
        
        .static-chart-container h3 {
            color: #2E86AB;
            margin-bottom: 15px;
        }
        
        .static-chart-container img {
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.15);
        }
        
        /* Risk Assessment */
        .risk-dashboard {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 25px;
        }
        
        .risk-card {
            background: white;
            border: 2px solid #e0e0e0;
            padding: 25px;
            border-radius: 12px;
            transition: all 0.3s;
            box-shadow: 0 3px 15px rgba(0,0,0,0.1);
        }
        
        .risk-card:hover {
            transform: translateY(-8px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.2);
            border-color: #2E86AB;
        }
        
        .risk-card h4 {
            color: #2E86AB;
            margin-bottom: 20px;
            font-size: 1.2em;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .risk-score {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-top: 15px;
            font-size: 1.1em;
        }
        
        .risk-bar-container {
            flex: 1;
            height: 25px;
            background: #e0e0e0;
            border-radius: 12px;
            overflow: hidden;
            margin: 0 20px;
            box-shadow: inset 0 2px 5px rgba(0,0,0,0.1);
        }
        
        .risk-bar {
            height: 100%;
            background: linear-gradient(90deg, #4CAF50 0%, #8BC34A 50%, #FFC107 75%, #f44336 100%);
            border-radius: 12px;
            transition: width 1s ease;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }
        
        /* Trading Points */
        .trading-table {
            width: 100%;
            border-collapse: collapse;
            margin: 25px 0;
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        }
        
        .trading-table th {
            background: linear-gradient(135deg, #2E86AB 0%, #A23B72 100%);
            color: white;
            padding: 18px;
            text-align: center;
            font-weight: bold;
            font-size: 1.1em;
        }
        
        .trading-table td {
            padding: 18px;
            text-align: center;
            border: 1px solid #e0e0e0;
            font-size: 1.05em;
        }
        
        .trading-table tbody tr:nth-child(even) {
            background: #f9f9f9;
        }
        
        .trading-table tbody tr:hover {
            background: #e3f2fd;
            transition: background 0.3s;
        }
        
        .buy { background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%) !important; color: white; font-weight: bold; }
        .sell { background: linear-gradient(135deg, #f44336 0%, #da190b 100%) !important; color: white; font-weight: bold; }
        .hold { background: linear-gradient(135deg, #FF9800 0%, #f57c00 100%) !important; color: white; font-weight: bold; }
        
        /* Footer */
        .footer {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 40px;
            text-align: center;
            color: #666;
            font-size: 0.95em;
            border-top: 1px solid #dee2e6;
        }
        
        .disclaimer {
            background: linear-gradient(135deg, #fff3cd 0%, #ffeeba 100%);
            border: 2px solid #ffc107;
            padding: 25px;
            border-radius: 12px;
            margin-top: 25px;
            text-align: left;
        }
        
        .disclaimer strong {
            color: #856404;
            font-size: 1.1em;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .header {
                flex-direction: column;
                text-align: center;
                gap: 20px;
            }
            
            .header h1 {
                font-size: 1.8em;
            }
            
            .company-logo {
                width: 80px;
                height: 80px;
            }
            
            .section {
                padding: 25px;
            }
            
            .static-charts-grid {
                grid-template-columns: 1fr;
            }
            
            .conclusion-grid {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Header with Logo -->
        <div class="header">
            <div class="header-left">
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
            {% if company_logo %}
            <img src="{{ company_logo }}" alt="{{ company_name }} Logo" class="company-logo">
            {% endif %}
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
            <div class="company-grid">
                <div class="info-card">
                    <h3>基本信息</h3>
                    <ul>
                        <li><span>公司名称</span><span>{{ company_name }}</span></li>
                        <li><span>所属行业</span><span>{{ industry }}</span></li>
                        <li><span>总市值</span><span>{{ market_cap }}</span></li>
                        <li><span>流通市值</span><span>{{ float_cap }}</span></li>
                        <li><span>当前股价</span><span>{{ current_price }}</span></li>
                        <li><span>52周最高</span><span>{{ high_52w }}</span></li>
                        <li><span>52周最低</span><span>{{ low_52w }}</span></li>
                    </ul>
                </div>
                <div class="info-card">
                    <h3>关键财务指标</h3>
                    <table class="data-table">
                        <thead>
                            <tr>
                                <th>指标</th>
                                <th>数值</th>
                                <th>行业平均</th>
                                <th>评级</th>
                            </tr>
                        </thead>
                        <tbody>
                            {{ financial_indicators_rows }}
                        </tbody>
                    </table>
                </div>
            </div>
            
            {% if product_images %}
            <h3 style="color: #2E86AB; margin-bottom: 20px;">业务产品展示</h3>
            <div class="image-gallery">
                {{ product_images_html }}
            </div>
            {% endif %}
        </div>
        
        <!-- Interactive Charts -->
        <div class="section">
            <h2 class="section-title">交互式技术分析图表</h2>
            <div class="charts-section">
                <div class="chart-wrapper">
                    <h3>股价走势与移动平均线</h3>
                    <div id="priceChart"></div>
                </div>
                
                <div class="chart-wrapper">
                    <h3>MACD指标</h3>
                    <div id="macdChart"></div>
                </div>
                
                <div class="chart-wrapper">
                    <h3>RSI指标</h3>
                    <div id="rsiChart"></div>
                </div>
            </div>
        </div>
        
        <!-- Static Technical Charts -->
        <div class="section">
            <h2 class="section-title">技术分析图表</h2>
            <div class="static-charts-grid">
                {{ static_chart_sections }}
            </div>
        </div>
        
        <!-- Fundamental Analysis with Trend Charts -->
        <div class="section">
            <h2 class="section-title">基本面分析</h2>
            <h3>财务健康度评分: {{ fundamental_score }}/10</h3>
            
            <div class="charts-section">
                <div class="chart-wrapper">
                    <h3>财务数据趋势</h3>
                    <div id="fundamentalTrendChart"></div>
                </div>
            </div>
            
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
        
        <!-- Sentiment Analysis -->
        <div class="section">
            <h2 class="section-title">情绪与新闻分析</h2>
            
            <div class="charts-section">
                <div class="chart-wrapper">
                    <h3>市场情绪趋势</h3>
                    <div id="sentimentTrendChart"></div>
                </div>
            </div>
            
            <h3>当前情绪指标</h3>
            <table class="data-table">
                <thead>
                    <tr>
                        <th>指标</th>
                        <th>当前值</th>
                        <th>历史分位</th>
                        <th>信号</th>
                    </tr>
                </thead>
                <tbody>
                    {{ sentiment_rows }}
                </tbody>
            </table>
        </div>
        
        <!-- Risk Assessment -->
        <div class="section">
            <h2 class="section-title">风险评估</h2>
            <h3>综合风险评分: {{ overall_risk_score }}/10</h3>
            
            <div class="charts-section">
                <div class="chart-wrapper">
                    <h3>风险维度雷达图</h3>
                    <div id="riskRadarChart"></div>
                </div>
            </div>
            
            <div class="risk-dashboard">
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
            <p><strong>报告生成时间:</strong> {{ generation_time }}</p>
            <p><strong>数据来源:</strong> Yahoo Finance、公开财报、市场新闻</p>
            <div class="disclaimer">
                <strong>⚠️ 免责声明：</strong>
                <p>本报告由AI分析系统生成，仅供参考，不构成任何投资建议。股票投资存在风险，市场有风险，投资需谨慎。</p>
                <p>本报告基于历史数据和公开信息分析，不保证未来表现。投资者应根据自身风险承受能力独立做出投资决策。</p>
            </div>
        </div>
    </div>
    
    <!-- Plotly Charts Script -->
    <script>
        // Price Chart
        var priceTrace = {
            x: {{ price_dates }},
            y: {{ price_values }},
            type: 'scatter',
            mode: 'lines',
            name: '收盘价',
            line: {color: '#2E86AB', width: 2}
        };
        
        var ma5Trace = {
            x: {{ price_dates }},
            y: {{ ma5_values }},
            type: 'scatter',
            mode: 'lines',
            name: 'MA5',
            line: {color: '#F18F01', width: 1.5}
        };
        
        var ma20Trace = {
            x: {{ price_dates }},
            y: {{ ma20_values }},
            type: 'scatter',
            mode: 'lines',
            name: 'MA20',
            line: {color: '#C73E1D', width: 1.5}
        };
        
        var priceLayout = {
            title: '',
            xaxis: {title: '日期'},
            yaxis: {title: '价格'},
            hovermode: 'x unified',
            template: 'plotly_white'
        };
        
        Plotly.newPlot('priceChart', [priceTrace, ma5Trace, ma20Trace], priceLayout, {responsive: true});
        
        // MACD Chart
        var macdTrace = {
            x: {{ price_dates }},
            y: {{ macd_values }},
            type: 'scatter',
            mode: 'lines',
            name: 'MACD',
            line: {color: '#2196F3'}
        };
        
        var signalTrace = {
            x: {{ price_dates }},
            y: {{ macd_signal_values }},
            type: 'scatter',
            mode: 'lines',
            name: 'Signal',
            line: {color: '#FF9800'}
        };
        
        var macdLayout = {
            title: '',
            xaxis: {title: '日期'},
            yaxis: {title: 'MACD'},
            hovermode: 'x unified',
            template: 'plotly_white'
        };
        
        Plotly.newPlot('macdChart', [macdTrace, signalTrace], macdLayout, {responsive: true});
        
        // RSI Chart
        var rsiTrace = {
            x: {{ price_dates }},
            y: {{ rsi_values }},
            type: 'scatter',
            mode: 'lines',
            name: 'RSI',
            line: {color: '#9C27B0', width: 2}
        };
        
        var overboughtLine = {
            x: {{ price_dates }},
            y: Array({{ price_dates|length }}).fill(70),
            type: 'scatter',
            mode: 'lines',
            name: '超买线(70)',
            line: {color: '#f44336', dash: 'dash'}
        };
        
        var oversoldLine = {
            x: {{ price_dates }},
            y: Array({{ price_dates|length }}).fill(30),
            type: 'scatter',
            mode: 'lines',
            name: '超卖线(30)',
            line: {color: '#4CAF50', dash: 'dash'}
        };
        
        var rsiLayout = {
            title: '',
            xaxis: {title: '日期'},
            yaxis: {title: 'RSI', range: [0, 100]},
            hovermode: 'x unified',
            template: 'plotly_white'
        };
        
        Plotly.newPlot('rsiChart', [rsiTrace, overboughtLine, oversoldLine], rsiLayout, {responsive: true});
        
        {% if fundamental_trend_data %}
        // Fundamental Trend Chart
        var revenueTrace = {
            x: {{ fundamental_dates }},
            y: {{ revenue_values }},
            type: 'bar',
            name: '营收',
            marker: {color: '#2E86AB'}
        };
        
        var profitTrace = {
            x: {{ fundamental_dates }},
            y: {{ profit_values }},
            type: 'bar',
            name: '净利润',
            marker: {color: '#A23B72'}
        };
        
        var fundamentalLayout = {
            title: '',
            barmode: 'group',
            xaxis: {title: '季度'},
            yaxis: {title: '金额（亿元）'},
            template: 'plotly_white'
        };
        
        Plotly.newPlot('fundamentalTrendChart', [revenueTrace, profitTrace], fundamentalLayout, {responsive: true});
        {% endif %}
        
        {% if sentiment_trend_data %}
        // Sentiment Trend Chart
        var sentimentTrace = {
            x: {{ sentiment_dates }},
            y: {{ sentiment_values }},
            type: 'scatter',
            mode: 'lines+markers',
            name: '情绪评分',
            line: {color: '#FF9800', width: 3},
            marker: {size: 8}
        };
        
        var sentimentLayout = {
            title: '',
            xaxis: {title: '日期'},
            yaxis: {title: '情绪评分', range: [0, 10]},
            template: 'plotly_white'
        };
        
        Plotly.newPlot('sentimentTrendChart', [sentimentTrace], sentimentLayout, {responsive: true});
        {% endif %}
        
        // Risk Radar Chart
        var radarData = [{
            type: 'scatterpolar',
            r: [{{ risk_radar_values }}],
            theta: ['基本面风险', '技术面风险', '情绪面风险', '消息面风险', '市场环境风险'],
            fill: 'toself',
            name: '风险评分'
        }];
        
        var radarLayout = {
            polar: {
                radialaxis: {
                    visible: true,
                    range: [0, 10]
                }
            },
            showlegend: false,
            title: ''
        };
        
        Plotly.newPlot('riskRadarChart', radarData, radarLayout, {responsive: true});
    </script>
</body>
</html>
"""


def generate_enhanced_html_report(data, charts_dir, output_path):
    """
    生成增强版HTML报告（包含交互式图表和图片）
    
    参数:
        data: 报告数据字典
        charts_dir: 图表目录
        output_path: 输出文件路径
    
    返回:
        dict: 生成结果
    """
    try:
        # 创建Jinja2模板
        template = Template(ENHANCED_HTML_TEMPLATE)
        
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
            'float_cap': data.get('float_cap', 'N/A'),
            'current_price': data.get('current_price', 'N/A'),
            'high_52w': data.get('high_52w', 'N/A'),
            'low_52w': data.get('low_52w', 'N/A'),
            'fundamental_score': data.get('fundamental_score', 5),
            'overall_risk_score': data.get('overall_risk_score', 5),
            'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'company_logo': data.get('company_logo', ''),
            'financial_indicators_rows': generate_financial_rows(data.get('financial_indicators', [])),
            'static_chart_sections': generate_static_chart_sections(data.get('charts', []), charts_dir),
            'fundamental_rows': generate_fundamental_rows(data.get('fundamental_details', [])),
            'risk_items': generate_risk_items(data.get('risk_details', [])),
            'trading_rows': generate_trading_rows(data.get('trading_points', [])),
            'sentiment_rows': generate_sentiment_rows(data.get('sentiment_indicators', [])),
            'product_images_html': generate_product_images(data.get('product_images', [])),
            
            # 交互式图表数据
            'price_dates': json.dumps(data.get('price_dates', [])),
            'price_values': json.dumps(data.get('price_values', [])),
            'ma5_values': json.dumps(data.get('ma5_values', [])),
            'ma20_values': json.dumps(data.get('ma20_values', [])),
            'macd_values': json.dumps(data.get('macd_values', [])),
            'macd_signal_values': json.dumps(data.get('macd_signal_values', [])),
            'rsi_values': json.dumps(data.get('rsi_values', [])),
            
            # 财务趋势数据
            'fundamental_trend_data': data.get('fundamental_trend_data'),
            'fundamental_dates': json.dumps(data.get('fundamental_dates', [])),
            'revenue_values': json.dumps(data.get('revenue_values', [])),
            'profit_values': json.dumps(data.get('profit_values', [])),
            
            # 情绪趋势数据
            'sentiment_trend_data': data.get('sentiment_trend_data'),
            'sentiment_dates': json.dumps(data.get('sentiment_dates', [])),
            'sentiment_values': json.dumps(data.get('sentiment_values', [])),
            
            # 风险雷达图数据
            'risk_radar_values': ','.join([str(r.get('score', 5)) for r in data.get('risk_details', [])])
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
                        <td>{item.get('industry_avg', 'N/A')}</td>
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


def generate_static_chart_sections(charts, charts_dir):
    """生成静态图表部分"""
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
                <div class="static-chart-container">
                    <h3>{chart_name}</h3>
                    <img src="{chart_path}" alt="{chart_name}">
                </div>
            ''')
    
    return '\n'.join(sections)


def generate_product_images(images):
    """生成产品图片HTML"""
    if not images:
        return ''
    
    html = []
    for img in images:
        html.append(f'''
                <div class="image-card">
                    <img src="{img.get('url', '')}" alt="{img.get('caption', '产品图片')}">
                    <p>{img.get('caption', '产品图片')}</p>
                </div>
            ''')
    
    return '\n'.join(html)


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
                <div class="risk-card">
                    <h4>{item.get('dimension', 'N/A')} <span>(权重{weight*100}%)</span></h4>
                    <div class="risk-score">
                        <span>{score}/10</span>
                        <div class="risk-bar-container">
                            <div class="risk-bar" style="width: {percentage}%"></div>
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


def generate_sentiment_rows(indicators):
    """生成情绪指标表格行"""
    rows = []
    for item in indicators:
        signal_class = get_rating_class(item.get('signal', '中性'))
        rows.append(f'''
                    <tr>
                        <td>{item.get('metric', 'N/A')}</td>
                        <td>{item.get('value', 'N/A')}</td>
                        <td>{item.get('percentile', 'N/A')}</td>
                        <td class="{signal_class}">{item.get('signal', 'N/A')}</td>
                    </tr>
                ''')
    
    return '\n'.join(rows)


def main():
    parser = argparse.ArgumentParser(description='生成增强版HTML格式股票分析报告')
    parser.add_argument('--data', type=str, required=True, help='报告数据JSON文件')
    parser.add_argument('--charts-dir', type=str, default='./charts', help='图表目录')
    parser.add_argument('--output', type=str, default='enhanced_report.html', help='输出HTML文件路径')
    
    args = parser.parse_args()
    
    # 读取数据文件
    with open(args.data, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 生成HTML报告
    result = generate_enhanced_html_report(data, args.charts_dir, args.output)
    
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
