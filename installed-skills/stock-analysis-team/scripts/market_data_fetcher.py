#!/usr/bin/env python3
"""
股票市场数据获取脚本

功能：
- 获取实时股票行情数据
- 计算技术指标（MA、MACD、RSI）
- 获取历史价格数据
- 支持A股和美股市场

依赖：
- yfinance: Yahoo Finance数据源
- ta: 技术分析库
- pandas: 数据处理
"""

import argparse
import json
import sys
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import yfinance as yf
import ta


def get_stock_data(symbol, market, period="1y", interval="1d"):
    """
    获取股票数据
    
    参数:
        symbol: 股票代码（如 600519.SH, AAPL）
        market: 市场（cn 或 us）
        period: 时间周期（1y=1年, 6mo=6个月, 3mo=3个月）
        interval: 数据间隔（1d=日线, 1h=小时线）
    
    返回:
        dict: 包含行情数据、技术指标的字典
    """
    try:
        # 处理A股代码格式（yfinance使用SS后缀）
        yf_symbol = symbol
        if market == "cn" and ".SH" in symbol:
            yf_symbol = symbol.replace(".SH", ".SS")
        elif market == "cn" and ".SZ" in symbol:
            yf_symbol = symbol.replace(".SZ", ".SZ")
        
        # 创建ticker对象
        ticker = yf.Ticker(yf_symbol)
        
        # 获取历史数据
        hist = ticker.history(period=period, interval=interval)
        
        if hist.empty:
            return {"error": f"无法获取股票 {symbol} 的数据，请检查股票代码是否正确"}
        
        # 获取当前基本信息
        info = ticker.info
        
        # 计算技术指标
        df = hist.copy()
        
        # 移动平均线
        df['MA5'] = df['Close'].rolling(window=5).mean()
        df['MA10'] = df['Close'].rolling(window=10).mean()
        df['MA20'] = df['Close'].rolling(window=20).mean()
        df['MA60'] = df['Close'].rolling(window=60).mean()
        
        # MACD
        df['MACD'] = ta.trend.MACD(df['Close']).macd()
        df['MACD_Signal'] = ta.trend.MACD(df['Close']).macd_signal()
        df['MACD_Diff'] = df['MACD'] - df['MACD_Signal']
        
        # RSI
        df['RSI'] = ta.momentum.RSIIndicator(df['Close']).rsi()
        
        # 布林带
        bb = ta.volatility.BollingerBands(df['Close'])
        df['BB_Upper'] = bb.bollinger_hband()
        df['BB_Middle'] = bb.bollinger_mavg()
        df['BB_Lower'] = bb.bollinger_lband()
        
        # 成交量移动平均
        df['Volume_MA5'] = df['Volume'].rolling(window=5).mean()
        df['Volume_MA10'] = df['Volume'].rolling(window=10).mean()
        
        # 获取最新数据
        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        
        # 构建返回结果
        result = {
            "symbol": symbol,
            "market": market,
            "company_name": info.get('longName', 'N/A'),
            "current_price": round(latest['Close'], 2),
            "price_change": round(latest['Close'] - prev['Close'], 2),
            "price_change_pct": round((latest['Close'] - prev['Close']) / prev['Close'] * 100, 2),
            "volume": int(latest['Volume']),
            "high_52w": info.get('fiftyTwoWeekHigh', 0),
            "low_52w": info.get('fiftyTwoWeekLow', 0),
            "market_cap": info.get('marketCap', 0),
            "pe_ratio": info.get('trailingPE', 0),
            "pb_ratio": info.get('priceToBook', 0),
            
            # 技术指标
            "technical_indicators": {
                "MA5": round(latest['MA5'], 2) if pd.notna(latest['MA5']) else None,
                "MA10": round(latest['MA10'], 2) if pd.notna(latest['MA10']) else None,
                "MA20": round(latest['MA20'], 2) if pd.notna(latest['MA20']) else None,
                "MA60": round(latest['MA60'], 2) if pd.notna(latest['MA60']) else None,
                "MACD": round(latest['MACD'], 4) if pd.notna(latest['MACD']) else None,
                "MACD_Signal": round(latest['MACD_Signal'], 4) if pd.notna(latest['MACD_Signal']) else None,
                "MACD_Diff": round(latest['MACD_Diff'], 4) if pd.notna(latest['MACD_Diff']) else None,
                "RSI": round(latest['RSI'], 2) if pd.notna(latest['RSI']) else None,
                "BB_Upper": round(latest['BB_Upper'], 2) if pd.notna(latest['BB_Upper']) else None,
                "BB_Middle": round(latest['BB_Middle'], 2) if pd.notna(latest['BB_Middle']) else None,
                "BB_Lower": round(latest['BB_Lower'], 2) if pd.notna(latest['BB_Lower']) else None,
            },
            
            # 趋势判断
            "trend_analysis": {
                "multi_bullish": check_bullish_alignment(df),  # 多头排列
                "ma_signal": get_ma_signal(latest),
                "macd_signal": "金叉" if latest['MACD_Diff'] > 0 else "死叉" if pd.notna(latest['MACD_Diff']) else "信号不明",
                "rsi_signal": get_rsi_signal(latest['RSI']) if pd.notna(latest['RSI']) else "信号不明",
            },
            
            # 历史价格数据（最近30天）
            "historical_data": [
                {
                    "date": idx.strftime('%Y-%m-%d'),
                    "open": round(row['Open'], 2),
                    "high": round(row['High'], 2),
                    "low": round(row['Low'], 2),
                    "close": round(row['Close'], 2),
                    "volume": int(row['Volume'])
                }
                for idx, row in df.tail(30).iterrows()
            ],
            
            "data_timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return result
        
    except Exception as e:
        return {"error": f"获取数据失败: {str(e)}"}


def check_bullish_alignment(df):
    """
    检查是否形成多头排列
    
    多头排列定义: MA5 > MA10 > MA20 > MA60
    """
    latest = df.iloc[-1]
    try:
        if (pd.notna(latest['MA5']) and pd.notna(latest['MA10']) and 
            pd.notna(latest['MA20']) and pd.notna(latest['MA60'])):
            return (latest['MA5'] > latest['MA10'] > latest['MA20'] > latest['MA60'])
    except:
        return False
    return False


def get_ma_signal(latest):
    """
    获取均线信号
    """
    current = latest['Close']
    if pd.notna(latest['MA5']):
        if current > latest['MA5'] > latest['MA10']:
            return "强势"
        elif current < latest['MA5'] < latest['MA10']:
            return "弱势"
        elif current > latest['MA5']:
            return "反弹"
        else:
            return "调整"
    return "信号不明"


def get_rsi_signal(rsi):
    """
    获取RSI信号
    """
    if rsi > 70:
        return "超买"
    elif rsi < 30:
        return "超卖"
    elif rsi > 50:
        return "强势"
    else:
        return "弱势"


def get_market_index(market):
    """
    获取市场指数数据
    """
    try:
        if market == "cn" or market == "both":
            # 上证指数
            sh_index = get_stock_data("000001.SS", "cn", period="1mo")
        
        if market == "us" or market == "both":
            # 标普500
            sp500 = get_stock_data("^GSPC", "us", period="1mo")
        
        return {
            "cn_market": sh_index if market in ["cn", "both"] else None,
            "us_market": sp500 if market in ["us", "both"] else None
        }
    except Exception as e:
        return {"error": f"获取市场指数失败: {str(e)}"}


def main():
    parser = argparse.ArgumentParser(description='获取股票市场数据')
    parser.add_argument('--symbol', type=str, help='股票代码（如 600519.SH 或 AAPL）')
    parser.add_argument('--market', type=str, choices=['cn', 'us', 'both'], help='市场类型（cn=A股, us=美股, both=双市）')
    parser.add_argument('--mode', type=str, choices=['stock', 'market', 'both'], default='stock', 
                       help='获取模式（stock=个股, market=大盘, both=两者）')
    parser.add_argument('--period', type=str, default='1y', help='数据周期（1y, 6mo, 3mo）')
    parser.add_argument('--interval', type=str, default='1d', help='数据间隔（1d=日线, 1h=小时线）')
    
    args = parser.parse_args()
    
    # 如果获取大盘数据
    if args.mode in ['market', 'both']:
        market_data = get_market_index(args.market)
        print(json.dumps(market_data, indent=2, ensure_ascii=False))
    
    # 如果获取个股数据
    if args.mode in ['stock', 'both']:
        if not args.symbol:
            print(json.dumps({"error": "个股模式需要提供 --symbol 参数"}, indent=2, ensure_ascii=False))
            sys.exit(1)
        
        stock_data = get_stock_data(args.symbol, args.market, args.period, args.interval)
        print(json.dumps(stock_data, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
