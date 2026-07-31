"""
全自动交易循环 + 可视化监控仪表板
启动后自动定时扫描、分析、生成信号，并提供Web监控界面
"""

import json
import os
import sys
import time
import threading
import csv
from datetime import datetime
from flask import Flask, render_template_string, jsonify, request

# 添加脚本目录到路径
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
sys.path.insert(0, SCRIPT_DIR)

from market_fetcher import MarketFetcher, calc_technical_indicators
from sentiment_analyzer import SentimentAnalyzer
from signal_generator import SignalGenerator, SignalSender


# ===================== 全局状态 =====================

class TradingState:
    """全局交易状态"""
    def __init__(self):
        self.config = {}
        self.signals = []          # 最近信号列表
        self.positions = {}        # 当前持仓 {symbol: info}
        self.equity_history = []   # 权益曲线
        self.latest_signals = {}   # 每只股票最新信号
        self.is_running = False
        self.last_scan_time = None
        self.total_pnl = 0
        self.initial_capital = 1000000
    
    def to_dict(self):
        return {
            'is_running': self.is_running,
            'last_scan': self.last_scan_time,
            'signal_count': len(self.signals),
            'position_count': len(self.positions),
            'total_pnl': self.total_pnl,
            'latest_signals': self.latest_signals,
            'recent_signals': self.signals[-20:][::-1]
        }

state = TradingState()


# ===================== HTML 模板 =====================

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>AI自动交易监控系统</title>
    <meta http-equiv="refresh" content="30">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, sans-serif; background: #0a0a1a; color: #e0e0e0; padding: 20px; }
        .header { background: linear-gradient(135deg, #1a1a3e, #2d1b69); border-radius: 12px; padding: 20px 30px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; }
        .header h1 { font-size: 22px; background: linear-gradient(90deg, #00d2ff, #7b2ff7); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
        .status { display: flex; align-items: center; gap: 8px; }
        .status-dot { width: 10px; height: 10px; border-radius: 50%; background: #4caf50; animation: pulse 2s infinite; }
        .status-dot.offline { background: #f44336; animation: none; }
        @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }
        .grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 20px; }
        .card { background: #1a1a2e; border-radius: 12px; padding: 20px; border: 1px solid #2a2a4a; }
        .card-label { font-size: 13px; color: #888; margin-bottom: 8px; }
        .card-value { font-size: 24px; font-weight: 700; }
        .positive { color: #e53935; }
        .negative { color: #43a047; }
        .section { background: #1a1a2e; border-radius: 12px; padding: 20px; margin-bottom: 20px; border: 1px solid #2a2a4a; }
        .section h2 { font-size: 16px; margin-bottom: 16px; padding-bottom: 8px; border-bottom: 1px solid #2a2a4a; color: #aaa; }
        table { width: 100%; border-collapse: collapse; font-size: 13px; }
        th { text-align: left; padding: 8px 12px; background: #12122a; color: #888; font-weight: 600; }
        td { padding: 8px 12px; border-bottom: 1px solid #1a1a3a; }
        tr:hover { background: #1a1a3a; }
        .badge { display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 600; }
        .badge-buy { background: #e53935; color: white; }
        .badge-sell { background: #43a047; color: white; }
        .badge-hold { background: #555; color: white; }
        .badge-low { background: #43a047; color: white; }
        .badge-medium { background: #ff9800; color: white; }
        .badge-high { background: #e53935; color: white; }
        .footer { text-align: center; padding: 20px; color: #555; font-size: 12px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🤖 AI 自动交易监控系统</h1>
        <div class="status">
            <div class="status-dot {{ 'offline' if not data.is_running }}"></div>
            <span>{{ '运行中' if data.is_running else '已停止' }}</span>
            <span style="color:#555;margin-left:12px;">上次扫描: {{ data.last_scan or '-' }}</span>
        </div>
    </div>
    
    <div class="grid">
        <div class="card">
            <div class="card-label">监控信号数</div>
            <div class="card-value">{{ data.signal_count }}</div>
        </div>
        <div class="card">
            <div class="card-label">当前持仓</div>
            <div class="card-value">{{ data.position_count }}</div>
        </div>
        <div class="card">
            <div class="card-label">累计盈亏</div>
            <div class="card-value {{ 'positive' if data.total_pnl >= 0 else 'negative' }}">{{ "{:+,.0f}".format(data.total_pnl) }} 元</div>
        </div>
        <div class="card">
            <div class="card-label">系统状态</div>
            <div class="card-value" style="font-size:18px;">{{ '🟢 正常' if data.is_running else '🔴 停止' }}</div>
        </div>
    </div>
    
    <div class="section">
        <h2>📡 最新 AI 信号</h2>
        {% if data.latest_signals %}
        <table>
            <tr><th>代码</th><th>信号</th><th>价格</th><th>评分</th><th>情绪</th><th>原因</th><th>风险</th></tr>
            {% for sym, sig in data.latest_signals.items() %}
            <tr>
                <td>{{ sym }}</td>
                <td><span class="badge badge-{{ sig.signal }}">{{ sig.signal|upper }}</span></td>
                <td>{{ sig.price }}</td>
                <td>{{ sig.technical_score }}</td>
                <td>{{ sig.sentiment_label }} ({{ sig.sentiment_score }})</td>
                <td style="max-width:300px;font-size:11px;color:#999;">{{ sig.reason[:60] }}...</td>
                <td><span class="badge badge-{{ sig.risk_level }}">{{ sig.risk_level }}</span></td>
            </tr>
            {% endfor %}
        {% else %}
        <p style="color:#555;padding:20px;">暂无信号数据</p>
        {% endif %}
        </table>
    </div>
    
    <div class="section">
        <h2>📋 最近信号记录</h2>
        {% if data.recent_signals %}
        <table>
            <tr><th>时间</th><th>代码</th><th>信号</th><th>价格</th><th>评分</th><th>情绪</th><th>原因</th></tr>
            {% for sig in data.recent_signals %}
            <tr>
                <td>{{ sig.timestamp }}</td>
                <td>{{ sig.symbol }}</td>
                <td><span class="badge badge-{{ sig.signal }}">{{ sig.signal|upper }}</span></td>
                <td>{{ sig.price }}</td>
                <td>{{ sig.technical_score }}</td>
                <td>{{ sig.sentiment_label }}</td>
                <td style="max-width:250px;font-size:11px;color:#999;">{{ sig.reason[:50] }}</td>
            </tr>
            {% endfor %}
        {% else %}
        <p style="color:#555;padding:20px;">暂无信号记录</p>
        {% endif %}
        </table>
    </div>
    
    <div class="footer">
        ⚠️ 本系统仅供学习研究，不构成投资建议。AI决策存在误差，投资有风险，入市需谨慎。
    </div>
</body>
</html>
'''


# ===================== Flask 应用 =====================

app = Flask(__name__)

@app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_HTML, data=state.to_dict())

@app.route('/api/status')
def api_status():
    return jsonify(state.to_dict())

@app.route('/api/signals')
def api_signals():
    return jsonify(state.signals[-50:][::-1])

@app.route('/api/positions')
def api_positions():
    return jsonify(state.positions)


# ===================== 自动交易循环 =====================

def load_config(config_path: str) -> dict:
    """加载配置文件"""
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'platform': 'qmt',
        'market': 'cn',
        'watchlist': ['600519.SH', '000858.SZ'],
        'scan_interval': 300,
        'risk': {
            'stop_loss_atr_mult': 2.0,
            'take_profit_atr_mult': 4.0,
            'max_position_pct': 20
        }
    }


def run_scan_cycle():
    """执行一次完整的扫描→分析→信号生成循环"""
    watchlist = state.config.get('watchlist', [])
    market = state.config.get('market', 'cn')
    
    fetcher = MarketFetcher(state.config)
    analyzer = SentimentAnalyzer(state.config)
    generator = SignalGenerator(state.config)
    sender = SignalSender(state.config)
    
    for symbol in watchlist:
        try:
            # 1. 采集行情
            market_data = fetcher.fetch_realtime(symbol, market)
            if 'error' in market_data:
                continue
            
            # 2. 获取历史K线并计算技术指标
            history = fetcher.fetch_history(symbol, 60, market)
            indicators = calc_technical_indicators(history) if 'error' not in history else {}
            if 'error' in indicators:
                continue
            indicators['price'] = market_data.get('price', 0)
            
            # 3. 获取新闻并分析情绪
            news = fetcher.fetch_news(symbol, 5)
            sentiment = analyzer.analyze(symbol, news)
            
            # 4. 获取持仓信息
            position = state.positions.get(symbol)
            
            # 5. 生成交易信号
            signal = generator.generate(market_data, indicators, sentiment, position)
            
            # 6. 发送信号
            sender.send(signal)
            
            # 7. 更新状态
            state.latest_signals[symbol] = signal
            state.signals.append(signal)
            if signal['signal'] == 'buy':
                state.positions[symbol] = {
                    'entry_price': signal['price'],
                    'entry_time': signal['timestamp'],
                    'highest': signal['price'],
                    'holding_days': 0
                }
            elif signal['signal'] == 'sell' and symbol in state.positions:
                pos = state.positions.pop(symbol)
                pnl = (signal['price'] - pos['entry_price']) * 100
                state.total_pnl += pnl
            
        except Exception as e:
            print(f"[错误] {symbol}: {e}")
    
    state.last_scan_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def auto_trade_loop(interval: int = 300):
    """自动交易循环"""
    print(f"[启动] 自动交易循环，扫描间隔: {interval}秒")
    state.is_running = True
    
    while state.is_running:
        try:
            print(f"\n[扫描] {datetime.now().strftime('%H:%M:%S')} 开始扫描...")
            run_scan_cycle()
            print(f"[完成] 扫描结束，下次扫描: {interval}秒后")
        except Exception as e:
            print(f"[异常] {e}")
        
        # 等待下一次扫描
        for _ in range(interval):
            if not state.is_running:
                break
            time.sleep(1)


# ===================== 主入口 =====================

def main():
    import argparse
    parser = argparse.ArgumentParser(description='AI自动交易监控系统')
    parser.add_argument('--config', type=str, default='config.json', help='配置文件路径')
    parser.add_argument('--port', type=int, default=5000, help='仪表板端口')
    parser.add_argument('--interval', type=int, default=300, help='扫描间隔(秒)')
    parser.add_argument('--once', action='store_true', help='仅执行一次扫描')
    parser.add_argument('--symbol', type=str, help='指定扫描的股票代码')
    args = parser.parse_args()
    
    # 加载配置
    config_path = os.path.join(SKILL_DIR, 'scripts', args.config)
    state.config = load_config(config_path)
    
    if args.symbol:
        state.config['watchlist'] = [args.symbol]
    
    print("=" * 50)
    print("  AI 自动交易监控系统")
    print(f"  监控标的: {', '.join(state.config.get('watchlist', []))}")
    print(f"  扫描间隔: {args.interval}秒")
    print(f"  仪表板: http://localhost:{args.port}")
    print("=" * 50)
    
    if args.once:
        # 单次扫描模式
        run_scan_cycle()
        print("\n[完成] 单次扫描结束")
        return
    
    # 启动自动交易循环（后台线程）
    trade_thread = threading.Thread(target=auto_trade_loop, args=(args.interval,), daemon=True)
    trade_thread.start()
    
    # 启动Web仪表板
    print(f"\n[仪表板] http://localhost:{args.port}")
    app.run(host='0.0.0.0', port=args.port, debug=False, threaded=True)


if __name__ == '__main__':
    main()
