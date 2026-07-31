#!/usr/bin/env python3
"""
股票图表生成脚本

功能：
- 生成股价走势折线图
- 生成K线图（蜡烛图）
- 生成成交量柱状图
- 生成技术指标图（MACD、RSI）
- 生成财务数据对比图

依赖：
- matplotlib: 绘图库
- pandas: 数据处理
- yfinance: 数据源
"""

import argparse
import json
import sys
import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib import font_manager
import yfinance as yf
import numpy as np

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial Unicode MS', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False


def generate_price_chart(symbol, market, period="1y", output_dir="."):
    """
    生成股价走势折线图
    
    参数:
        symbol: 股票代码
        market: 市场（cn 或 us）
        period: 时间周期
        output_dir: 输出目录
    
    返回:
        dict: 包含图表路径的信息
    """
    try:
        # 处理代码格式
        yf_symbol = symbol
        if market == "cn" and ".SH" in symbol:
            yf_symbol = symbol.replace(".SH", ".SS")
        elif market == "cn" and ".SZ" in symbol:
            yf_symbol = symbol.replace(".SZ", ".SZ")
        
        # 获取数据
        ticker = yf.Ticker(yf_symbol)
        hist = ticker.history(period=period)
        
        if hist.empty:
            return {"error": f"无法获取股票 {symbol} 的数据"}
        
        # 计算移动平均线
        hist['MA5'] = hist['Close'].rolling(window=5).mean()
        hist['MA20'] = hist['Close'].rolling(window=20).mean()
        hist['MA60'] = hist['Close'].rolling(window=60).mean()
        
        # 创建图表
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # 绘制股价线
        ax.plot(hist.index, hist['Close'], label='Close Price', linewidth=2, color='#2E86AB')
        
        # 绘制移动平均线
        ax.plot(hist.index, hist['MA5'], label='MA5', linewidth=1, color='#F18F01', alpha=0.8)
        ax.plot(hist.index, hist['MA20'], label='MA20', linewidth=1, color='#C73E1D', alpha=0.8)
        ax.plot(hist.index, hist['MA60'], label='MA60', linewidth=1, color='#3B1F2B', alpha=0.8)
        
        # 设置标题和标签
        ax.set_title(f'{symbol} Stock Price Trend', fontsize=16, fontweight='bold')
        ax.set_xlabel('Date', fontsize=12)
        ax.set_ylabel('Price', fontsize=12)
        ax.legend(loc='best')
        ax.grid(True, alpha=0.3)
        
        # 格式化x轴
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.xticks(rotation=45)
        
        plt.tight_layout()
        
        # 保存图表
        output_path = os.path.join(output_dir, f'{symbol}_price_chart.png')
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return {
            "success": True,
            "chart_type": "price_trend",
            "file_path": output_path,
            "symbol": symbol
        }
        
    except Exception as e:
        return {"error": f"生成价格图表失败: {str(e)}"}


def generate_candlestick_chart(symbol, market, period="3mo", output_dir="."):
    """
    生成K线图（蜡烛图）
    
    参数:
        symbol: 股票代码
        market: 市场
        period: 时间周期
        output_dir: 输出目录
    
    返回:
        dict: 包含图表路径的信息
    """
    try:
        # 处理代码格式
        yf_symbol = symbol
        if market == "cn" and ".SH" in symbol:
            yf_symbol = symbol.replace(".SH", ".SS")
        elif market == "cn" and ".SZ" in symbol:
            yf_symbol = symbol.replace(".SZ", ".SZ")
        
        # 获取数据
        ticker = yf.Ticker(yf_symbol)
        hist = ticker.history(period=period)
        
        if hist.empty:
            return {"error": f"无法获取股票 {symbol} 的数据"}
        
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [3, 1]})
        
        # 绘制K线
        width = 0.6
        width2 = 0.1
        
        up = hist[hist['Close'] >= hist['Open']]
        down = hist[hist['Close'] < hist['Open']]
        
        # 绘制上涨的K线
        ax1.bar(up.index, up['Close'] - up['Open'], width, bottom=up['Open'], color='#00C853', alpha=0.7)
        ax1.bar(up.index, up['High'] - up['Close'], width2, bottom=up['Close'], color='#00C853', alpha=0.7)
        ax1.bar(up.index, up['Low'] - up['Open'], width2, bottom=up['Open'], color='#00C853', alpha=0.7)
        
        # 绘制下跌的K线
        ax1.bar(down.index, down['Close'] - down['Open'], width, bottom=down['Open'], color='#D50000', alpha=0.7)
        ax1.bar(down.index, down['High'] - down['Open'], width2, bottom=down['Open'], color='#D50000', alpha=0.7)
        ax1.bar(down.index, down['Low'] - down['Close'], width2, bottom=down['Close'], color='#D50000', alpha=0.7)
        
        ax1.set_title(f'{symbol} Candlestick Chart', fontsize=16, fontweight='bold')
        ax1.set_ylabel('Price', fontsize=12)
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        
        # 绘制成交量
        colors = ['#00C853' if close >= open_ else '#D50000' 
                 for close, open_ in zip(hist['Close'], hist['Open'])]
        ax2.bar(hist.index, hist['Volume'], width=0.6, color=colors, alpha=0.7)
        ax2.set_ylabel('Volume', fontsize=12)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.grid(True, alpha=0.3)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        
        plt.tight_layout()
        
        # 保存图表
        output_path = os.path.join(output_dir, f'{symbol}_candlestick.png')
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return {
            "success": True,
            "chart_type": "candlestick",
            "file_path": output_path,
            "symbol": symbol
        }
        
    except Exception as e:
        return {"error": f"生成K线图失败: {str(e)}"}


def generate_macd_chart(symbol, market, period="1y", output_dir="."):
    """
    生成MACD指标图
    
    参数:
        symbol: 股票代码
        market: 市场
        period: 时间周期
        output_dir: 输出目录
    
    返回:
        dict: 包含图表路径的信息
    """
    try:
        # 处理代码格式
        yf_symbol = symbol
        if market == "cn" and ".SH" in symbol:
            yf_symbol = symbol.replace(".SH", ".SS")
        elif market == "cn" and ".SZ" in symbol:
            yf_symbol = symbol.replace(".SZ", ".SZ")
        
        # 获取数据
        ticker = yf.Ticker(yf_symbol)
        hist = ticker.history(period=period)
        
        if hist.empty:
            return {"error": f"无法获取股票 {symbol} 的数据"}
        
        # 计算MACD
        hist['EMA12'] = hist['Close'].ewm(span=12, adjust=False).mean()
        hist['EMA26'] = hist['Close'].ewm(span=26, adjust=False).mean()
        hist['MACD'] = hist['EMA12'] - hist['EMA26']
        hist['Signal'] = hist['MACD'].ewm(span=9, adjust=False).mean()
        hist['Histogram'] = hist['MACD'] - hist['Signal']
        
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [2, 1]})
        
        # 绘制价格
        ax1.plot(hist.index, hist['Close'], label='Close Price', linewidth=2, color='#2E86AB')
        ax1.set_title(f'{symbol} Price & MACD', fontsize=16, fontweight='bold')
        ax1.set_ylabel('Price', fontsize=12)
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        
        # 绘制MACD
        ax2.plot(hist.index, hist['MACD'], label='MACD', linewidth=1.5, color='#2196F3')
        ax2.plot(hist.index, hist['Signal'], label='Signal', linewidth=1.5, color='#FF9800')
        
        # 绘制柱状图
        colors = ['#00C853' if h >= 0 else '#D50000' for h in hist['Histogram']]
        ax2.bar(hist.index, hist['Histogram'], width=0.8, color=colors, alpha=0.5)
        
        ax2.set_ylabel('MACD', fontsize=12)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.legend(loc='best')
        ax2.grid(True, alpha=0.3)
        ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        
        plt.tight_layout()
        
        # 保存图表
        output_path = os.path.join(output_dir, f'{symbol}_macd.png')
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return {
            "success": True,
            "chart_type": "macd",
            "file_path": output_path,
            "symbol": symbol
        }
        
    except Exception as e:
        return {"error": f"生成MACD图表失败: {str(e)}"}


def generate_rsi_chart(symbol, market, period="1y", output_dir="."):
    """
    生成RSI指标图
    
    参数:
        symbol: 股票代码
        market: 市场
        period: 时间周期
        output_dir: 输出目录
    
    返回:
        dict: 包含图表路径的信息
    """
    try:
        # 处理代码格式
        yf_symbol = symbol
        if market == "cn" and ".SH" in symbol:
            yf_symbol = symbol.replace(".SH", ".SS")
        elif market == "cn" and ".SZ" in symbol:
            yf_symbol = symbol.replace(".SZ", ".SZ")
        
        # 获取数据
        ticker = yf.Ticker(yf_symbol)
        hist = ticker.history(period=period)
        
        if hist.empty:
            return {"error": f"无法获取股票 {symbol} 的数据"}
        
        # 计算RSI
        delta = hist['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        hist['RSI'] = 100 - (100 / (1 + rs))
        
        # 创建图表
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), gridspec_kw={'height_ratios': [2, 1]})
        
        # 绘制价格
        ax1.plot(hist.index, hist['Close'], label='Close Price', linewidth=2, color='#2E86AB')
        ax1.set_title(f'{symbol} Price & RSI', fontsize=16, fontweight='bold')
        ax1.set_ylabel('Price', fontsize=12)
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)
        ax1.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        
        # 绘制RSI
        ax2.plot(hist.index, hist['RSI'], label='RSI', linewidth=2, color='#9C27B0')
        ax2.axhline(y=70, color='#D50000', linestyle='--', linewidth=1, label='Overbought (70)')
        ax2.axhline(y=30, color='#00C853', linestyle='--', linewidth=1, label='Oversold (30)')
        ax2.axhline(y=50, color='black', linestyle='-', linewidth=0.5, alpha=0.5)
        
        # 填充超买超卖区域
        ax2.fill_between(hist.index, 70, 100, color='#D50000', alpha=0.1)
        ax2.fill_between(hist.index, 0, 30, color='#00C853', alpha=0.1)
        
        ax2.set_ylabel('RSI', fontsize=12)
        ax2.set_xlabel('Date', fontsize=12)
        ax2.set_ylim(0, 100)
        ax2.legend(loc='best')
        ax2.grid(True, alpha=0.3)
        ax2.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        
        plt.tight_layout()
        
        # 保存图表
        output_path = os.path.join(output_dir, f'{symbol}_rsi.png')
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        return {
            "success": True,
            "chart_type": "rsi",
            "file_path": output_path,
            "symbol": symbol
        }
        
    except Exception as e:
        return {"error": f"生成RSI图表失败: {str(e)}"}


def generate_summary_dashboard(symbol, market, period="1y", output_dir="."):
    """
    生成综合分析仪表盘（包含所有关键图表）
    
    参数:
        symbol: 股票代码
        market: 市场
        period: 时间周期
        output_dir: 输出目录
    
    返回:
        dict: 包含所有图表路径的信息
    """
    try:
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        
        results = {
            "symbol": symbol,
            "market": market,
            "charts": []
        }
        
        # 生成各个图表
        charts = [
            ('price_chart', generate_price_chart),
            ('candlestick', generate_candlestick_chart),
            ('macd', generate_macd_chart),
            ('rsi', generate_rsi_chart)
        ]
        
        for chart_name, chart_func in charts:
            result = chart_func(symbol, market, period, output_dir)
            if result.get('success'):
                results["charts"].append({
                    "type": chart_name,
                    "path": result["file_path"]
                })
            else:
                results["charts"].append({
                    "type": chart_name,
                    "error": result.get("error")
                })
        
        return results
        
    except Exception as e:
        return {"error": f"生成综合仪表盘失败: {str(e)}"}


def main():
    parser = argparse.ArgumentParser(description='生成股票图表')
    parser.add_argument('--symbol', type=str, required=True, help='股票代码')
    parser.add_argument('--market', type=str, choices=['cn', 'us'], required=True, help='市场类型')
    parser.add_argument('--period', type=str, default='1y', help='数据周期')
    parser.add_argument('--chart-type', type=str, 
                       choices=['price', 'candlestick', 'macd', 'rsi', 'all'], 
                       default='all', help='图表类型')
    parser.add_argument('--output-dir', type=str, default='.', help='输出目录')
    
    args = parser.parse_args()
    
    if args.chart_type == 'all':
        result = generate_summary_dashboard(args.symbol, args.market, args.period, args.output_dir)
    else:
        chart_functions = {
            'price': generate_price_chart,
            'candlestick': generate_candlestick_chart,
            'macd': generate_macd_chart,
            'rsi': generate_rsi_chart
        }
        result = chart_functions[args.chart_type](args.symbol, args.market, args.period, args.output_dir)
    
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
