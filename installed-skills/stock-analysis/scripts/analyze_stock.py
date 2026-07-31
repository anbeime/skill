#!/usr/bin/env python3
"""
股票技术分析脚本
计算技术指标、支撑位和压力位
"""

import json
import argparse
import sys
import numpy as np
import pandas as pd


def calculate_ma(data, period):
    """
    计算移动平均线
    
    Args:
        data: 价格数据列表
        period: 周期
    
    Returns:
        list: 移动平均线数据
    """
    if len(data) < period:
        return [None] * len(data)
    
    ma = []
    for i in range(len(data)):
        if i < period - 1:
            ma.append(None)
        else:
            ma.append(sum(data[i-period+1:i+1]) / period)
    
    return ma


def calculate_macd(close_prices, fast=12, slow=26, signal=9):
    """
    计算MACD指标
    
    Args:
        close_prices: 收盘价列表
        fast: 快线周期
        slow: 慢线周期
        signal: 信号线周期
    
    Returns:
        dict: MACD数据
    """
    if len(close_prices) < slow:
        return {
            'dif': [None] * len(close_prices),
            'dea': [None] * len(close_prices),
            'macd': [None] * len(close_prices)
        }
    
    # 计算EMA
    def ema(data, period):
        if len(data) < period:
            return [None] * len(data)
        
        multiplier = 2 / (period + 1)
        ema_data = [data[0]]
        
        for i in range(1, len(data)):
            if i < period - 1:
                ema_data.append(data[i])
            else:
                ema_value = (data[i] - ema_data[-1]) * multiplier + ema_data[-1]
                ema_data.append(ema_value)
        
        return ema_data
    
    ema_fast = ema(close_prices, fast)
    ema_slow = ema(close_prices, slow)
    
    # DIF = EMA(12) - EMA(26)
    dif = [fast - slow if fast and slow else None 
           for fast, slow in zip(ema_fast, ema_slow)]
    
    # DEA = EMA(DIF, 9)
    dif_valid = [d if d else 0 for d in dif]
    dea = ema(dif_valid, signal)
    
    # MACD = (DIF - DEA) * 2
    macd = [(d - s) * 2 if d and s else None 
            for d, s in zip(dif, dea)]
    
    return {
        'dif': dif,
        'dea': dea,
        'macd': macd
    }


def calculate_rsi(close_prices, period=14):
    """
    计算RSI指标
    
    Args:
        close_prices: 收盘价列表
        period: 周期
    
    Returns:
        list: RSI数据
    """
    if len(close_prices) < period + 1:
        return [None] * len(close_prices)
    
    deltas = []
    for i in range(1, len(close_prices)):
        deltas.append(close_prices[i] - close_prices[i-1])
    
    rsi = [None] * len(close_prices)
    
    for i in range(period, len(deltas)):
        gains = [d if d > 0 else 0 for d in deltas[i-period+1:i+1]]
        losses = [-d if d < 0 else 0 for d in deltas[i-period+1:i+1]]
        
        avg_gain = sum(gains) / period
        avg_loss = sum(losses) / period
        
        if avg_loss == 0:
            rsi[i+1] = 100
        else:
            rs = avg_gain / avg_loss
            rsi[i+1] = 100 - (100 / (1 + rs))
    
    return rsi


def calculate_support_resistance(historical_data, current_price):
    """
    计算支撑位和压力位
    
    Args:
        historical_data: 历史K线数据
        current_price: 当前价格
    
    Returns:
        dict: 支撑位和压力位
    """
    if not historical_data:
        return {
            'support_levels': [],
            'resistance_levels': []
        }
    
    lows = [item['low'] for item in historical_data]
    highs = [item['high'] for item in historical_data]
    
    # 寻找支撑位（近期低点）
    support_levels = []
    for i in range(2, len(lows) - 2):
        if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
           lows[i] < lows[i+1] and lows[i] < lows[i+2]:
            # 这是一个局部低点
            if lows[i] < current_price:  # 支撑位在当前价格下方
                support_levels.append({
                    'price': round(lows[i], 2),
                    'date': historical_data[i]['date']
                })
    
    # 寻找压力位（近期高点）
    resistance_levels = []
    for i in range(2, len(highs) - 2):
        if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
           highs[i] > highs[i+1] and highs[i] > highs[i+2]:
            # 这是一个局部高点
            if highs[i] > current_price:  # 压力位在当前价格上方
                resistance_levels.append({
                    'price': round(highs[i], 2),
                    'date': historical_data[i]['date']
                })
    
    # 按距离当前价格的远近排序
    support_levels.sort(key=lambda x: abs(x['price'] - current_price))
    resistance_levels.sort(key=lambda x: abs(x['price'] - current_price))
    
    # 只保留最近的3个支撑位和3个压力位
    return {
        'support_levels': support_levels[:3],
        'resistance_levels': resistance_levels[:3]
    }


def detect_gaps(historical_data):
    """
    识别K线缺口
    
    Args:
        historical_data: 历史K线数据
    
    Returns:
        dict: 缺口信息，包括向上缺口和向下缺口
    """
    if len(historical_data) < 2:
        return {
            'up_gaps': [],
            'down_gaps': [],
            'has_gaps': False
        }
    
    up_gaps = []  # 向上缺口（跳空高开）
    down_gaps = []  # 向下缺口（跳空低开）
    
    for i in range(len(historical_data) - 1):
        today = historical_data[i]
        yesterday = historical_data[i + 1]
        
        # 向上缺口：今日最低价 > 昨日最高价
        if today['low'] > yesterday['high']:
            gap_size = today['low'] - yesterday['high']
            gap_pct = (gap_size / yesterday['high']) * 100
            up_gaps.append({
                'date': today['date'],
                'yesterday_date': yesterday['date'],
                'yesterday_high': round(yesterday['high'], 2),
                'today_low': round(today['low'], 2),
                'gap_size': round(gap_size, 2),
                'gap_pct': round(gap_pct, 2),
                'price_range': [round(yesterday['high'], 2), round(today['low'], 2)],
                'role': '支撑位'  # 向上缺口通常构成支撑
            })
        
        # 向下缺口：今日最高价 < 昨日最低价
        elif today['high'] < yesterday['low']:
            gap_size = yesterday['low'] - today['high']
            gap_pct = (gap_size / yesterday['low']) * 100
            down_gaps.append({
                'date': today['date'],
                'yesterday_date': yesterday['date'],
                'yesterday_low': round(yesterday['low'], 2),
                'today_high': round(today['high'], 2),
                'gap_size': round(gap_size, 2),
                'gap_pct': round(gap_pct, 2),
                'price_range': [round(today['high'], 2), round(yesterday['low'], 2)],
                'role': '压力位'  # 向下缺口通常构成压力
            })
    
    has_gaps = len(up_gaps) > 0 or len(down_gaps) > 0
    
    return {
        'up_gaps': up_gaps,
        'down_gaps': down_gaps,
        'has_gaps': has_gaps
    }


def analyze_ma_trend(ma5, ma10, ma20, ma60):
    """
    分析均线排列趋势
    
    Args:
        ma5: MA5数据
        ma10: MA10数据
        ma20: MA20数据
        ma60: MA60数据
    
    Returns:
        dict: 趋势分析结果
    """
    if not all([ma5, ma10, ma20, ma60]):
        return {'trend': '数据不足', 'description': '数据不足，无法判断趋势'}
    
    # 获取最新的均线值
    ma5_latest = ma5[-1]
    ma10_latest = ma10[-1]
    ma20_latest = ma20[-1]
    ma60_latest = ma60[-1]
    
    if not all([ma5_latest, ma10_latest, ma20_latest, ma60_latest]):
        return {'trend': '数据不足', 'description': '数据不足，无法判断趋势'}
    
    # 判断均线排列
    if ma5_latest > ma10_latest > ma20_latest > ma60_latest:
        return {
            'trend': '多头排列',
            'description': '均线呈多头排列（MA5 > MA10 > MA20 > MA60），短期趋势向上',
            'strength': '强'
        }
    elif ma5_latest < ma10_latest < ma20_latest < ma60_latest:
        return {
            'trend': '空头排列',
            'description': '均线呈空头排列（MA5 < MA10 < MA20 < MA60），短期趋势向下',
            'strength': '强'
        }
    elif ma5_latest > ma10_latest and ma10_latest < ma20_latest:
        return {
            'trend': '缠绕整理',
            'description': '均线缠绕，趋势不明，处于整理状态',
            'strength': '弱'
        }
    elif ma5_latest > ma10_latest > ma20_latest:
        return {
            'trend': '短期向上',
            'description': '短期均线向上，中长期趋势待确认',
            'strength': '中'
        }
    elif ma5_latest < ma10_latest < ma20_latest:
        return {
            'trend': '短期向下',
            'description': '短期均线向下，中长期趋势待确认',
            'strength': '中'
        }
    else:
        return {
            'trend': '震荡',
            'description': '均线排列不明确，市场处于震荡状态',
            'strength': '弱'
        }


def analyze_macd_signal(macd_data):
    """
    分析MACD信号
    
    Args:
        macd_data: MACD数据
    
    Returns:
        dict: MACD信号分析
    """
    dif = macd_data['dif']
    dea = macd_data['dea']
    macd = macd_data['macd']
    
    if not all([dif, dea, macd]):
        return {'signal': '数据不足', 'description': '数据不足，无法判断MACD信号'}
    
    # 获取最新的值
    dif_latest = dif[-1]
    dea_latest = dea[-1]
    macd_latest = macd[-1]
    
    if not all([dif_latest, dea_latest, macd_latest]):
        return {'signal': '数据不足', 'description': '数据不足，无法判断MACD信号'}
    
    # 获取前一个值
    dif_prev = dif[-2]
    dea_prev = dea[-2]
    
    signals = []
    
    # 金叉判断
    if dif_prev <= dea_prev and dif_latest > dea_latest:
        signals.append('金叉（买入信号）')
    
    # 死叉判断
    if dif_prev >= dea_prev and dif_latest < dea_latest:
        signals.append('死叉（卖出信号）')
    
    # MACD柱状图分析
    if macd_latest > 0:
        if len(macd) > 1 and macd[-2] > 0 and macd_latest > macd[-2]:
            signals.append('MACD红柱放大（多头动能增强）')
        elif len(macd) > 1 and macd[-2] > 0 and macd_latest < macd[-2]:
            signals.append('MACD红柱缩小（多头动能减弱）')
    else:
        if len(macd) > 1 and macd[-2] < 0 and macd_latest < macd[-2]:
            signals.append('MACD绿柱放大（空头动能增强）')
        elif len(macd) > 1 and macd[-2] < 0 and macd_latest > macd[-2]:
            signals.append('MACD绿柱缩小（空头动能减弱）')
    
    if not signals:
        signals.append('无明显信号')
    
    return {
        'signal': signals,
        'dif': round(dif_latest, 4),
        'dea': round(dea_latest, 4),
        'macd': round(macd_latest, 4)
    }


def analyze_rsi_signal(rsi_data):
    """
    分析RSI信号
    
    Args:
        rsi_data: RSI数据
    
    Returns:
        dict: RSI信号分析
    """
    if not rsi_data or not rsi_data[-1]:
        return {'signal': '数据不足', 'description': '数据不足，无法判断RSI信号'}
    
    rsi_latest = rsi_data[-1]
    
    if rsi_latest >= 80:
        return {
            'value': round(rsi_latest, 2),
            'signal': '严重超买',
            'description': f'RSI={rsi_latest:.2f}，严重超买，回调风险较大'
        }
    elif rsi_latest >= 70:
        return {
            'value': round(rsi_latest, 2),
            'signal': '超买',
            'description': f'RSI={rsi_latest:.2f}，超买区域，注意回调风险'
        }
    elif rsi_latest <= 20:
        return {
            'value': round(rsi_latest, 2),
            'signal': '严重超卖',
            'description': f'RSI={rsi_latest:.2f}，严重超卖，可能存在反弹机会'
        }
    elif rsi_latest <= 30:
        return {
            'value': round(rsi_latest, 2),
            'signal': '超卖',
            'description': f'RSI={rsi_latest:.2f}，超卖区域，可能存在反弹'
        }
    else:
        return {
            'value': round(rsi_latest, 2),
            'signal': '正常',
            'description': f'RSI={rsi_latest:.2f}，处于正常区间'
        }


def analyze_volume(historical_data):
    """
    分析成交量
    
    Args:
        historical_data: 历史K线数据
    
    Returns:
        dict: 成交量分析
    """
    if len(historical_data) < 5:
        return {'description': '数据不足，无法分析成交量'}
    
    volumes = [item['volume'] for item in historical_data]
    avg_volume = sum(volumes[-5:]) / min(5, len(volumes))
    latest_volume = volumes[-1]
    
    volume_ratio = latest_volume / avg_volume if avg_volume > 0 else 0
    
    if volume_ratio >= 2:
        return {
            'description': '成交量显著放大',
            'volume_ratio': round(volume_ratio, 2),
            'signal': '放量'
        }
    elif volume_ratio >= 1.5:
        return {
            'description': '成交量适度放大',
            'volume_ratio': round(volume_ratio, 2),
            'signal': '温和放量'
        }
    elif volume_ratio <= 0.5:
        return {
            'description': '成交量显著萎缩',
            'volume_ratio': round(volume_ratio, 2),
            'signal': '缩量'
        }
    else:
        return {
            'description': '成交量正常',
            'volume_ratio': round(volume_ratio, 2),
            'signal': '正常'
        }


def perform_analysis(data_file):
    """
    执行完整的技术分析
    
    Args:
        data_file: 数据文件路径
    
    Returns:
        dict: 分析结果
    """
    # 读取数据文件
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"错误：读取数据文件失败 - {str(e)}")
        return None
    
    historical_data = data.get('historical', [])
    real_time_data = data.get('real_time', {})
    
    if not historical_data:
        print("错误：没有历史数据")
        return None
    
    # 提取收盘价
    close_prices = [item['close'] for item in historical_data]
    high_prices = [item['high'] for item in historical_data]
    low_prices = [item['low'] for item in historical_data]
    volumes = [item['volume'] for item in historical_data]
    
    current_price = real_time_data.get('current', close_prices[-1])
    
    # 计算技术指标
    ma5 = calculate_ma(close_prices, 5)
    ma10 = calculate_ma(close_prices, 10)
    ma20 = calculate_ma(close_prices, 20)
    ma60 = calculate_ma(close_prices, 60)
    
    macd_data = calculate_macd(close_prices)
    rsi_data = calculate_rsi(close_prices)
    
    support_resistance = calculate_support_resistance(historical_data, current_price)
    gap_analysis = detect_gaps(historical_data)
    ma_trend = analyze_ma_trend(ma5, ma10, ma20, ma60)
    macd_signal = analyze_macd_signal(macd_data)
    rsi_signal = analyze_rsi_signal(rsi_data)
    volume_analysis = analyze_volume(historical_data)
    
    # 构建分析结果
    analysis_result = {
        'stock_code': data.get('stock_code'),
        'stock_name': real_time_data.get('name', ''),
        'current_price': current_price,
        'analysis_time': data.get('fetch_time', ''),
        'technical_indicators': {
            'ma5': round(ma5[-1], 2) if ma5 and ma5[-1] else None,
            'ma10': round(ma10[-1], 2) if ma10 and ma10[-1] else None,
            'ma20': round(ma20[-1], 2) if ma20 and ma20[-1] else None,
            'ma60': round(ma60[-1], 2) if ma60 and ma60[-1] else None,
            'macd': macd_signal,
            'rsi': rsi_signal
        },
        'support_resistance': support_resistance,
        'gap_analysis': gap_analysis,
        'trend_analysis': ma_trend,
        'volume_analysis': volume_analysis
    }
    
    return analysis_result


def print_analysis(analysis_result):
    """
    打印分析结果
    
    Args:
        analysis_result: 分析结果
    """
    if not analysis_result:
        return
    
    print(f"\n{'='*50}")
    print(f"股票技术分析报告")
    print(f"{'='*50}")
    print(f"股票代码: {analysis_result['stock_code']}")
    print(f"股票名称: {analysis_result['stock_name']}")
    print(f"当前价格: {analysis_result['current_price']:.2f}")
    print(f"分析时间: {analysis_result['analysis_time']}")
    
    print(f"\n{'─'*50}")
    print("技术指标")
    print(f"{'─'*50}")
    ti = analysis_result['technical_indicators']
    ma5_str = f"{ti['ma5']:.2f}" if ti['ma5'] is not None else 'N/A'
    ma10_str = f"{ti['ma10']:.2f}" if ti['ma10'] is not None else 'N/A'
    ma20_str = f"{ti['ma20']:.2f}" if ti['ma20'] is not None else 'N/A'
    ma60_str = f"{ti['ma60']:.2f}" if ti['ma60'] is not None else 'N/A'
    print(f"MA5:  {ma5_str}")
    print(f"MA10: {ma10_str}")
    print(f"MA20: {ma20_str}")
    print(f"MA60: {ma60_str}")
    print(f"\nMACD:")
    print(f"  DIF: {ti['macd']['dif']}")
    print(f"  DEA: {ti['macd']['dea']}")
    print(f"  MACD: {ti['macd']['macd']}")
    print(f"  信号: {', '.join(ti['macd']['signal'])}")
    print(f"\nRSI:")
    print(f"  数值: {ti['rsi']['value']}")
    print(f"  信号: {ti['rsi']['signal']}")
    print(f"  说明: {ti['rsi']['description']}")
    
    print(f"\n{'─'*50}")
    print("趋势分析")
    print(f"{'─'*50}")
    ta = analysis_result['trend_analysis']
    print(f"趋势: {ta['trend']}")
    if 'strength' in ta:
        print(f"强度: {ta['strength']}")
    if 'description' in ta:
        print(f"说明: {ta['description']}")
    
    print(f"\n{'─'*50}")
    print("支撑位和压力位")
    print(f"{'─'*50}")
    sr = analysis_result['support_resistance']
    print(f"\n支撑位:")
    if sr['support_levels']:
        for i, level in enumerate(sr['support_levels'], 1):
            print(f"  {i}. {level['price']:.2f} (日期: {level['date']})")
    else:
        print(f"  下方无明显支撑位")
    
    print(f"\n压力位:")
    if sr['resistance_levels']:
        for i, level in enumerate(sr['resistance_levels'], 1):
            print(f"  {i}. {level['price']:.2f} (日期: {level['date']})")
    else:
        print(f"  上方无明显压力位")
    
    print(f"\n{'─'*50}")
    print("缺口分析")
    print(f"{'─'*50}")
    ga = analysis_result['gap_analysis']
    
    if not ga['has_gaps']:
        print(f"✓ 未见明显缺口")
    else:
        if ga['up_gaps']:
            print(f"\n向上缺口（构成潜在支撑位）：")
            for i, gap in enumerate(ga['up_gaps'], 1):
                print(f"  {i}. {gap['date']} 缺口范围: {gap['yesterday_high']:.2f} - {gap['today_low']:.2f}")
                print(f"     缺口大小: {gap['gap_size']:.2f} ({gap['gap_pct']:.2f}%)")
                print(f"     作用: {gap['role']}")
        
        if ga['down_gaps']:
            print(f"\n向下缺口（构成潜在压力位）：")
            for i, gap in enumerate(ga['down_gaps'], 1):
                print(f"  {i}. {gap['date']} 缺口范围: {gap['today_high']:.2f} - {gap['yesterday_low']:.2f}")
                print(f"     缺口大小: {gap['gap_size']:.2f} ({gap['gap_pct']:.2f}%)")
                print(f"     作用: {gap['role']}")
    
    print(f"\n{'─'*50}")
    print("成交量分析")
    print(f"{'─'*50}")
    va = analysis_result['volume_analysis']
    print(f"状态: {va['description']}")
    if 'volume_ratio' in va:
        print(f"量比: {va['volume_ratio']}")
    
    print(f"\n{'='*50}\n")


def main():
    parser = argparse.ArgumentParser(description='股票技术分析')
    parser.add_argument('--data_file', required=True, help='股票数据文件路径')
    parser.add_argument('--output', help='分析结果输出文件路径（可选）')
    
    args = parser.parse_args()
    
    print(f"正在分析股票数据: {args.data_file}")
    
    # 执行分析
    analysis_result = perform_analysis(args.data_file)
    
    if analysis_result:
        # 打印分析结果
        print_analysis(analysis_result)
        
        # 保存分析结果
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, ensure_ascii=False, indent=2)
            print(f"分析结果已保存到: {args.output}")
        
        print("✓ 技术分析完成")
    else:
        print("✗ 分析失败")
        sys.exit(1)


if __name__ == '__main__':
    main()
