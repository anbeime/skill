# QMT 平台对接指南

## 环境要求
- QMT 客户端已安装并登录
- miniQMT 模式已开启
- Python 3.6+ 环境

## 对接方式

### 方式一：通过QMT Python API直接交易

将信号生成器与QMT API集成：

```python
# 在 auto_trade_loop.py 中替换 SignalSender

class QMTSignalSender:
    def __init__(self, config):
        from xtquant import xttrader
        self.xt = xttrader.XtQuantTrader()
        self.account_id = config.get('qmt_account', '')
        self.xt.start()
    
    def send(self, signal):
        if signal['signal'] == 'buy':
            self.xt.order_stock(
                self.account_id, signal['symbol'],
                xtconstant.STOCK_BUY,
                signal['target_shares'],
                xtconstant.FIX_PRICE, signal['price'],
                xtconstant.AUTO_SPLIT
            )
        elif signal['signal'] == 'sell':
            self.xt.order_stock(
                self.account_id, signal['symbol'],
                xtconstant.STOCK_SELL,
                signal['target_shares'],
                xtconstant.FIX_PRICE, signal['price'],
                xtconstant.AUTO_SPLIT
            )
```

### 方式二：通过QMT策略接收HTTP信号

在QMT策略中监听HTTP信号：

```python
# QMT策略代码
import json
import requests

def init(C):
    C.signal_endpoint = 'http://localhost:5000/api/signals'
    C.last_signal_id = 0

def handlebar(C):
    try:
        resp = requests.get(C.signal_endpoint, timeout=3)
        signals = resp.json()
        
        for signal in signals:
            signal_id = hash(signal['timestamp'])
            if signal_id > C.last_signal_id:
                C.last_signal_id = signal_id
                
                if signal['signal'] == 'buy':
                    shares = int(100000 * signal['position_pct'] / 100 / signal['price'] / 100) * 100
                    passorder(23, 1101, C.accountid, signal['symbol'], 5, -1, shares, 'AI', 0, '', C)
                elif signal['signal'] == 'sell':
                    pos = get_position(C, signal['symbol'])
                    if pos:
                        passorder(24, 1101, C.accountid, signal['symbol'], 5, -1, pos['volume'], 'AI', 0, '', C)
    except:
        pass
```

## 注意事项
1. QMT交易需在交易时间内执行
2. 建议先用模拟盘测试
3. 确保QMT客户端保持运行
4. 注意A股T+1交易规则
