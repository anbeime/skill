#!/usr/bin/env python3
"""
股票数据获取脚本
从新浪财经API获取股票实时行情和历史K线数据
"""

import requests
import json
import argparse
import sys
from datetime import datetime, timedelta
import pandas as pd
import os


def fetch_real_time_quote(stock_code):
    """
    获取股票实时行情数据
    
    Args:
        stock_code: 股票代码（如 000001, sh600000, AAPL, 00700.HK）
    
    Returns:
        dict: 实时行情数据
    """
    # 新浪财经实时行情API
    # 格式：http://hq.sinajs.cn/list=股票代码
    # A股代码需要添加交易所前缀：sh或sz
    formatted_code = format_stock_code(stock_code)
    
    url = f"http://hq.sinajs.cn/list={formatted_code}"
    
    try:
        headers = {
            'Referer': 'http://finance.sina.com.cn',
            'User-Agent': 'Mozilla/5.0'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'gbk'
        
        if response.status_code == 200:
            data = response.text
            # 解析返回数据
            if 'var hq_str_' in data:
                content = data.split('"')[1]
                values = content.split(',')
                
                if len(values) >= 32:
                    return {
                        'name': values[0],
                        'open': float(values[1]) if values[1] else None,
                        'pre_close': float(values[2]) if values[2] else None,
                        'current': float(values[3]) if values[3] else None,
                        'high': float(values[4]) if values[4] else None,
                        'low': float(values[5]) if values[5] else None,
                        'bid': float(values[6]) if values[6] else None,
                        'ask': float(values[7]) if values[7] else None,
                        'volume': float(values[8]) if values[8] else None,
                        'amount': float(values[9]) if values[9] else None,
                        'date': values[30] if len(values) > 30 else '',
                        'time': values[31] if len(values) > 31 else ''
                    }
            
            print(f"警告：无法获取股票 {stock_code} 的实时数据")
            return None
        else:
            print(f"错误：API请求失败，状态码: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"错误：获取实时数据失败 - {str(e)}")
        return None


def format_stock_code(stock_code):
    """
    格式化股票代码以适应新浪财经API
    
    Args:
        stock_code: 原始股票代码
    
    Returns:
        str: 格式化后的股票代码
    """
    stock_code = stock_code.strip().upper()
    
    # 如果是6位数字（A股）
    if stock_code.isdigit() and len(stock_code) == 6:
        if stock_code.startswith('6'):
            return f"sh{stock_code}"
        elif stock_code.startswith(('0', '3')):
            return f"sz{stock_code}"
        elif stock_code.startswith(('8', '4')):
            return f"bj{stock_code}"
    
    # 如果已经有前缀
    if stock_code.startswith(('sh', 'sz', 'bj', 'hk')):
        return stock_code
    
    # 如果是港股或美股
    return stock_code


def fetch_historical_data(stock_code, days=30):
    """
    获取股票历史K线数据
    使用新浪财经历史数据接口
    
    Args:
        stock_code: 股票代码
        days: 获取天数
    
    Returns:
        list: 历史K线数据列表
    """
    # 新浪财经历史数据API
    # 格式：http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData
    formatted_code = format_stock_code(stock_code)
    
    # 移除交易所前缀用于API调用
    clean_code = stock_code
    if len(stock_code) > 6 and stock_code[2:].isdigit():
        clean_code = stock_code[2:]
    
    url = f"http://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData?symbol={formatted_code}&scale=240&ma=no&datalen={days}"
    
    try:
        headers = {
            'Referer': 'http://finance.sina.com.cn',
            'User-Agent': 'Mozilla/5.0'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'gbk'
        
        if response.status_code == 200:
            data = response.text
            # 解析JSON数据
            try:
                # 新浪返回的JSON格式特殊，需要处理
                if data.startswith('var'):
                    data = data.split('=', 1)[1].strip()
                
                historical_data = json.loads(data)
                
                # 格式化数据
                formatted_data = []
                for item in historical_data:
                    formatted_data.append({
                        'date': item.get('day', ''),
                        'open': float(item.get('open', 0)),
                        'high': float(item.get('high', 0)),
                        'low': float(item.get('low', 0)),
                        'close': float(item.get('close', 0)),
                        'volume': float(item.get('volume', 0))
                    })
                
                return formatted_data
            except json.JSONDecodeError:
                print(f"警告：解析历史数据失败")
                return []
        else:
            print(f"警告：获取历史数据失败，状态码: {response.status_code}")
            return []
            
    except Exception as e:
        print(f"警告：获取历史数据时出错 - {str(e)}")
        return []


def calculate_change(real_time_data, historical_data):
    """
    计算涨跌幅
    
    Args:
        real_time_data: 实时行情数据
        historical_data: 历史数据
    
    Returns:
        dict: 包含涨跌幅信息
    """
    if not real_time_data:
        return None
    
    current = real_time_data.get('current')
    pre_close = real_time_data.get('pre_close')
    
    if current and pre_close and pre_close > 0:
        change = current - pre_close
        change_percent = (change / pre_close) * 100
        
        return {
            'current': current,
            'pre_close': pre_close,
            'change': change,
            'change_percent': change_percent
        }
    
    return None


def save_to_file(stock_code, real_time_data, historical_data, output_dir='.'):
    """
    保存数据到文件
    
    Args:
        stock_code: 股票代码
        real_time_data: 实时行情数据
        historical_data: 历史数据
        output_dir: 输出目录
    
    Returns:
        str: 保存的文件路径
    """
    # 清理股票代码用于文件名
    clean_code = stock_code.replace('/', '_').replace('\\', '_')
    filename = f"stock_data_{clean_code}.json"
    filepath = os.path.join(output_dir, filename)
    
    data = {
        'stock_code': stock_code,
        'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'real_time': real_time_data,
        'historical': historical_data
    }
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"数据已保存到: {filepath}")
    return filepath


def main():
    parser = argparse.ArgumentParser(description='获取股票数据')
    parser.add_argument('--stock_code', required=True, help='股票代码（如 000001, sh600000, AAPL）')
    parser.add_argument('--days', type=int, default=30, help='获取历史数据天数（默认30天）')
    parser.add_argument('--output', default='.', help='输出目录（默认当前目录）')
    
    args = parser.parse_args()
    
    print(f"正在获取股票 {args.stock_code} 的数据...")
    
    # 获取实时行情
    real_time_data = fetch_real_time_quote(args.stock_code)
    
    if real_time_data:
        print(f"\n=== 实时行情 ===")
        print(f"股票名称: {real_time_data['name']}")
        print(f"当前价格: {real_time_data['current']:.2f}")
        print(f"开盘价: {real_time_data['open']:.2f}")
        print(f"最高价: {real_time_data['high']:.2f}")
        print(f"最低价: {real_time_data['low']:.2f}")
        print(f"昨收价: {real_time_data['pre_close']:.2f}")
        
        # 计算涨跌幅
        change_info = calculate_change(real_time_data, None)
        if change_info:
            print(f"涨跌额: {change_info['change']:+.2f}")
            print(f"涨跌幅: {change_info['change_percent']:+.2f}%")
    
    # 获取历史数据
    historical_data = fetch_historical_data(args.stock_code, args.days)
    
    if historical_data:
        print(f"\n=== 历史K线数据（最近{len(historical_data)}个交易日）===")
        print(f"日期范围: {historical_data[-1]['date']} 至 {historical_data[0]['date']}")
    
    # 保存数据
    filepath = save_to_file(args.stock_code, real_time_data, historical_data, args.output)
    
    if not real_time_data and not historical_data:
        print("\n错误：未能获取任何数据，请检查股票代码是否正确")
        sys.exit(1)
    
    print(f"\n✓ 数据获取完成，文件路径: {filepath}")


if __name__ == '__main__':
    main()
