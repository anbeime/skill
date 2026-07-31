"""
交易信号生成与发送模块
整合行情数据+情绪分析+技术指标，生成标准交易信号并通过HTTP发送
"""

import json
import time
import math
import requests
import numpy as np
from datetime import datetime
from typing import Optional


class SignalGenerator:
    """交易信号生成器"""
    
    def __init__(self, config: dict):
        self.config = config
        self.risk_config = config.get('risk', {})
    
    def generate(self, market_data: dict, indicators: dict, 
                 sentiment: dict, position_info: dict = None) -> dict:
        """
        生成交易信号
        
        Args:
            market_data: 实时行情数据
            indicators: 技术指标
            sentiment: 情绪分析结果
            position_info: 当前持仓信息 (可选)
        
        Returns:
            标准交易信号JSON
        """
        symbol = market_data.get('symbol', 'UNKNOWN')
        price = market_data.get('price', 0)
        
        # 1. 多因子评分
        scores = self._calc_factor_scores(indicators, sentiment)
        total_score = scores['total']
        
        # 2. 买入条件判断
        buy_conditions = self._check_buy_conditions(indicators, sentiment, total_score)
        
        # 3. 卖出条件判断
        sell_conditions = self._check_sell_conditions(indicators, sentiment, position_info)
        
        # 4. 风控检查
        risk_check = self._risk_check(market_data, indicators, position_info)
        
        # 5. 综合决策
        signal_type = self._make_decision(buy_conditions, sell_conditions, risk_check, total_score)
        
        # 6. 计算止损止盈
        atr = indicators.get('atr', price * 0.02)
        stop_loss_mult = self.risk_config.get('stop_loss_atr_mult', 2.0)
        take_profit_mult = self.risk_config.get('take_profit_atr_mult', 4.0)
        
        # 7. 计算建议仓位
        position_pct = self._calc_position(total_score, risk_check, sentiment)
        
        # 8. 风险等级
        risk_level = self._calc_risk_level(indicators, sentiment)
        
        # 9. 生成原因
        reason = self._generate_reason(signal_type, buy_conditions, sell_conditions, 
                                         scores, sentiment)
        
        signal = {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'symbol': symbol,
            'signal': signal_type,
            'price': price,
            'volume_ratio': market_data.get('volume_ratio', indicators.get('vol_ratio', 1.0)),
            'sentiment_score': sentiment.get('sentiment_score', 0),
            'sentiment_label': sentiment.get('sentiment_label', '中性'),
            'news_summary': sentiment.get('summary', '')[:200],
            'technical_score': total_score,
            'reason': reason,
            'stop_loss': round(price - atr * stop_loss_mult, 2) if signal_type == 'buy' else None,
            'take_profit': round(price + atr * take_profit_mult, 2) if signal_type == 'buy' else None,
            'position_pct': position_pct,
            'risk_level': risk_level,
            'factors': scores,
            'buy_conditions_met': sum(buy_conditions.values()),
            'buy_conditions_total': len(buy_conditions),
            'risk_passed': risk_check.get('passed', True),
            'risk_warnings': risk_check.get('warnings', [])
        }
        
        return signal
    
    def _calc_factor_scores(self, indicators: dict, sentiment: dict) -> dict:
        """计算各因子评分"""
        scores = {}
        
        # 动量因子 (30%)
        mom_5 = indicators.get('momentum_5d', 0)
        mom_20 = indicators.get('momentum_20d', 0)
        mom_60 = indicators.get('momentum_60d', 0)
        
        momentum_score = 50
        if mom_5 > 5: momentum_score += 15
        elif mom_5 > 2: momentum_score += 8
        elif mom_5 < -5: momentum_score -= 20
        if mom_20 > 10: momentum_score += 20
        elif mom_20 > 3: momentum_score += 10
        elif mom_20 < -10: momentum_score -= 25
        if mom_60 > 15: momentum_score += 10
        if mom_5 > 0 and mom_20 > 0 and mom_60 > 0:
            momentum_score += 10  # 三级共振
        scores['momentum'] = max(0, min(100, momentum_score))
        
        # 趋势因子 (25%)
        ma5 = indicators.get('ma5', 0)
        ma10 = indicators.get('ma10', 0)
        ma20 = indicators.get('ma20', 0)
        ma60 = indicators.get('ma60', 0)
        price = indicators.get('price', ma5)
        
        trend_score = 40
        if ma5 > ma10 > ma20 > ma60: trend_score += 30
        elif ma5 > ma10 > ma20: trend_score += 20
        if price > ma5 > ma20: trend_score += 10
        elif price < ma20: trend_score -= 15
        scores['trend'] = max(0, min(100, trend_score))
        
        # 量价因子 (20%)
        vol_ratio = indicators.get('vol_ratio', 1.0)
        volume_score = 50
        if vol_ratio > 2.0: volume_score += 15
        elif vol_ratio > 1.5: volume_score += 10
        if price > ma5 and vol_ratio > 1.2: volume_score += 15
        scores['volume'] = max(0, min(100, volume_score))
        
        # MACD因子 (15%)
        macd_hist = indicators.get('macd_hist', 0)
        macd_dif = indicators.get('macd_dif', 0)
        macd_score = 50
        if macd_dif > 0 and macd_hist > 0: macd_score += 25
        elif macd_hist < 0: macd_score -= 20
        if abs(macd_hist) > 0.1: macd_score += 10
        scores['macd'] = max(0, min(100, macd_score))
        
        # 情绪因子 (10%)
        sent_score = sentiment.get('sentiment_score', 0)
        sentiment_factor = 50 + sent_score * 0.3
        scores['sentiment'] = max(0, min(100, int(sentiment_factor)))
        
        # 综合评分
        total = (
            scores['momentum'] * 0.30 +
            scores['trend'] * 0.25 +
            scores['volume'] * 0.20 +
            scores['macd'] * 0.15 +
            scores['sentiment'] * 0.10
        )
        scores['total'] = int(total)
        
        return scores
    
    def _check_buy_conditions(self, indicators: dict, sentiment: dict, score: int) -> dict:
        """检查买入条件"""
        ma5 = indicators.get('ma5', 0)
        ma10 = indicators.get('ma10', 0)
        ma20 = indicators.get('ma20', 0)
        price = indicators.get('price', 0)
        vol_ratio = indicators.get('vol_ratio', 1.0)
        rsi = indicators.get('rsi', 50)
        macd_hist = indicators.get('macd_hist', 0)
        boll_middle = indicators.get('boll_middle', 0)
        sent_score = sentiment.get('sentiment_score', 0)
        
        return {
            'score_70': score >= 70,
            'ma_bullish': ma5 > ma10 > ma20 if ma5 > 0 else False,
            'macd_positive': macd_hist > 0,
            'volume_confirm': vol_ratio > 1.5,
            'boll_above_mid': price > boll_middle if boll_middle > 0 else False,
            'rsi_not_overbought': rsi < 80,
            'sentiment_positive': sent_score > 10
        }
    
    def _check_sell_conditions(self, indicators: dict, sentiment: dict, 
                                position: dict = None) -> dict:
        """检查卖出条件"""
        ma20 = indicators.get('ma20', 0)
        price = indicators.get('price', 0)
        rsi = indicators.get('rsi', 50)
        macd_hist = indicators.get('macd_hist', 0)
        vol_ratio = indicators.get('vol_ratio', 1.0)
        
        conditions = {
            'macd_death_cross': macd_hist < 0,
            'price_below_ma20': price < ma20 if ma20 > 0 else False,
            'rsi_overbought': rsi > 80,
            'volume_decline': vol_ratio > 1.3 and price < indicators.get('ma5', price)
        }
        
        # 持仓相关
        if position:
            entry_price = position.get('entry_price', 0)
            highest = position.get('highest', price)
            atr = indicators.get('atr', price * 0.02)
            
            pnl_pct = (price - entry_price) / entry_price if entry_price > 0 else 0
            
            conditions['atr_stop_loss'] = price <= entry_price - atr * self.risk_config.get('stop_loss_atr_mult', 2.0)
            conditions['trailing_stop'] = pnl_pct > 0.10 and price <= highest - atr * 1.5
            conditions['take_profit'] = price >= entry_price + atr * self.risk_config.get('take_profit_atr_mult', 4.0)
            conditions['time_stop'] = position.get('holding_days', 0) >= 20 and pnl_pct < 0.02
        
        return conditions
    
    def _risk_check(self, market_data: dict, indicators: dict, 
                    position: dict = None) -> dict:
        """风控检查"""
        warnings = []
        passed = True
        
        # 大盘状态检查
        # (简化处理, 实际应获取大盘数据)
        
        # 个股波动率检查
        vol = indicators.get('vol_ratio', 1.0)
        if vol > 3.0:
            warnings.append('成交量异常放大(>3倍)，可能存在风险')
        
        # RSI极端值
        rsi = indicators.get('rsi', 50)
        if rsi > 90:
            warnings.append('RSI严重超买(>90)，追高风险极大')
            passed = False
        elif rsi < 10:
            warnings.append('RSI严重超卖(<10)，注意底部反转')
        
        # 涨跌停检查
        change_pct = market_data.get('change_pct', 0)
        if abs(change_pct) > 9.5:
            warnings.append(f'涨跌幅{change_pct:.1f}%接近涨跌停，流动性风险')
        
        return {'passed': passed, 'warnings': warnings}
    
    def _make_decision(self, buy_cond: dict, sell_cond: dict, 
                       risk: dict, score: int) -> str:
        """综合决策"""
        if not risk.get('passed', True):
            return 'hold'
        
        # 卖出优先
        sell_triggers = ['atr_stop_loss', 'trailing_stop', 'take_profit', 'macd_death_cross']
        for trigger in sell_triggers:
            if sell_cond.get(trigger, False):
                return 'sell'
        
        # 买入判断
        buy_count = sum(buy_cond.values())
        if buy_cond.get('score_70', False) and buy_count >= 4:
            return 'buy'
        
        return 'hold'
    
    def _calc_position(self, score: int, risk: dict, sentiment: dict) -> float:
        """计算建议仓位(%)"""
        base_pct = 10  # 基础仓位10%
        
        # 评分加成
        if score >= 80: base_pct += 8
        elif score >= 70: base_pct += 5
        
        # 情绪加成
        sent = sentiment.get('sentiment_score', 0)
        if sent > 30: base_pct += 3
        elif sent < -20: base_pct -= 5
        
        # 风控限制
        max_pct = self.risk_config.get('max_position_pct', 20)
        return max(5, min(base_pct, max_pct))
    
    def _calc_risk_level(self, indicators: dict, sentiment: dict) -> str:
        """计算风险等级"""
        rsi = indicators.get('rsi', 50)
        vol_ratio = indicators.get('vol_ratio', 1.0)
        sent = sentiment.get('sentiment_score', 0)
        
        risk_score = 0
        if rsi > 80: risk_score += 2
        if rsi < 20: risk_score += 2
        if vol_ratio > 2.5: risk_score += 2
        if sent < -30: risk_score += 2
        
        if risk_score >= 4: return 'high'
        elif risk_score >= 2: return 'medium'
        else: return 'low'
    
    def _generate_reason(self, signal_type: str, buy_cond: dict, sell_cond: dict,
                          scores: dict, sentiment: dict) -> str:
        """生成决策原因"""
        parts = []
        
        if signal_type == 'buy':
            parts.append(f"综合评分{scores['total']}分")
            met = [k for k, v in buy_cond.items() if v]
            names = {
                'score_70': '评分达标', 'ma_bullish': '均线多头', 'macd_positive': 'MACD看多',
                'volume_confirm': '放量确认', 'boll_above_mid': '布林中轨上方',
                'rsi_not_overbought': 'RSI正常', 'sentiment_positive': '情绪利好'
            }
            met_names = [names.get(k, k) for k in met]
            parts.append('+'.join(met_names))
            if sentiment.get('sentiment_label'):
                parts.append(f"情绪{sentiment['sentiment_label']}")
        
        elif signal_type == 'sell':
            for trigger in ['atr_stop_loss', 'trailing_stop', 'take_profit', 'macd_death_cross']:
                if sell_cond.get(trigger, False):
                    names = {
                        'atr_stop_loss': 'ATR止损触发', 'trailing_stop': '移动止盈触发',
                        'take_profit': '止盈目标达成', 'macd_death_cross': 'MACD死叉'
                    }
                    parts.append(names.get(trigger, trigger))
                    break
        
        else:
            parts.append(f"综合评分{scores['total']}分(低于买入阈值)")
            met_count = sum(buy_cond.values())
            parts.append(f"技术条件仅满足{met_count}/{len(buy_cond)}")
        
        return ' | '.join(parts)


class SignalSender:
    """交易信号发送器"""
    
    def __init__(self, config: dict):
        self.config = config
        self.api_config = config.get('api', {})
        self.signal_log = []
    
    def send(self, signal: dict) -> bool:
        """发送交易信号到交易平台"""
        endpoint = self.api_config.get('signal_endpoint', '')
        if not endpoint:
            print(f"[信号] {signal['signal'].upper()} {signal['symbol']} @ {signal['price']} "
                  f"原因: {signal['reason']}")
            self._log_signal(signal)
            return True
        
        try:
            resp = requests.post(
                endpoint,
                json=signal,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            if resp.status_code == 200:
                print(f"[已发送] {signal['signal'].upper()} {signal['symbol']}")
                self._log_signal(signal, status='sent')
                return True
            else:
                print(f"[发送失败] HTTP {resp.status_code}")
                self._log_signal(signal, status='failed')
                return False
        except Exception as e:
            print(f"[发送异常] {e}")
            self._log_signal(signal, status='error')
            return False
    
    def _log_signal(self, signal: dict, status: str = 'generated'):
        """记录信号日志"""
        log_entry = {
            'timestamp': signal['timestamp'],
            'symbol': signal['symbol'],
            'signal': signal['signal'],
            'price': signal['price'],
            'score': signal['technical_score'],
            'reason': signal['reason'],
            'status': status
        }
        self.signal_log.append(log_entry)
        
        # 追加到CSV文件
        try:
            import os
            log_dir = self.config.get('log_dir', '.')
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, 'Trade_Diary.csv')
            
            import csv
            file_exists = os.path.exists(log_file)
            with open(log_file, 'a', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=log_entry.keys())
                if not file_exists:
                    writer.writeheader()
                writer.writerow(log_entry)
        except Exception:
            pass


if __name__ == '__main__':
    # 测试信号生成
    config = {
        'risk': {
            'stop_loss_atr_mult': 2.0,
            'take_profit_atr_mult': 4.0,
            'max_position_pct': 20
        }
    }
    
    gen = SignalGenerator(config)
    
    # 模拟数据
    market = {
        'symbol': '600519.SH',
        'price': 1680.00,
        'change_pct': 3.5,
        'volume_ratio': 1.8
    }
    
    ind = {
        'ma5': 1660, 'ma10': 1640, 'ma20': 1620, 'ma60': 1580,
        'macd_dif': 5.2, 'macd_dea': 3.1, 'macd_hist': 2.1,
        'rsi': 65, 'atr': 25.0,
        'boll_upper': 1720, 'boll_middle': 1650, 'boll_lower': 1580,
        'vol_ratio': 1.8, 'vol_ma20': 50000,
        'momentum_5d': 3.2, 'momentum_20d': 8.5, 'momentum_60d': 12.0,
        'price': 1680
    }
    
    sent = {
        'sentiment_score': 45,
        'sentiment_label': '利好',
        'summary': '白酒板块政策利好，多家券商上调评级',
        'recommendation': 'buy'
    }
    
    signal = gen.generate(market, ind, sent)
    print(json.dumps(signal, ensure_ascii=False, indent=2))
