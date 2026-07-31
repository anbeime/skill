# QMT（迅投量化交易终端）

[QMT](http://www.thinktrader.net)（Quant Market Trading）是迅投科技开发的专业量化交易平台。提供完整的桌面客户端，内置Python策略开发、回测引擎和实盘交易功能，支持中国证券市场全品种。

> ⚠️ **需要通过券商开通QMT权限**。QMT仅在Windows上运行。可通过国金、华鑫、中泰、东方财富等券商获取。

## 两种运行模式

| 模式 | 说明 |
|---|---|
| **QMT（完整版）** | 完整桌面GUI，内置Python编辑器、图表和回测引擎 |
| **miniQMT** | 极简模式 — 通过外部Python使用xtquant SDK |

## 内置Python策略框架

QMT提供事件驱动策略框架，内置Python运行时。

### 策略生命周期

```python
def init(ContextInfo):
    """初始化函数 - 策略启动时调用一次"""
    ContextInfo.set_universe(['000001.SZ', '600519.SH'])

def handlebar(ContextInfo):
    """K线处理函数 - 每根K线触发一次"""
    close = ContextInfo.get_market_data(['close'], stock_code='000001.SZ', period='1d', count=20)

def stop(ContextInfo):
    """停止函数 - 策略停止时调用"""
    pass
```

### 获取行情数据

```python
def handlebar(ContextInfo):
    # 获取K线数据
    data = ContextInfo.get_market_data(
        ['open', 'high', 'low', 'close', 'volume'],
        stock_code='000001.SZ',
        period='1d',
        count=20
    )
    # 获取历史数据
    history = ContextInfo.get_history_data(20, '1d', 'close', stock_code='000001.SZ')
    # 获取板块股票列表
    stocks = ContextInfo.get_stock_list_in_sector('沪深A股')
    # 获取财务数据
    fin = ContextInfo.get_financial_data('000001.SZ')
```

### 下单操作

```python
def handlebar(ContextInfo):
    # 限价买入
    order_shares('000001.SZ', 100, 'fix', 11.50, ContextInfo)
    # 限价卖出
    order_shares('000001.SZ', -100, 'fix', 12.00, ContextInfo)
    # 按目标金额买入
    order_target_value('000001.SZ', 100000, 'fix', 11.50, ContextInfo)
    # 撤单
    cancel('order_id', ContextInfo)
```

### 查询持仓与账户

```python
def handlebar(ContextInfo):
    positions = get_trade_detail_data('your_account', 'stock', 'position')
    for pos in positions:
        print(pos.m_strInstrumentID, pos.m_nVolume, pos.m_dMarketValue)
    orders = get_trade_detail_data('your_account', 'stock', 'order')
    account = get_trade_detail_data('your_account', 'stock', 'account')
```

## 回测

QMT内置回测引擎：
1. 在内置Python编辑器中编写策略
2. 设置回测参数（日期范围、初始资金、手续费、滑点）
3. 点击"运行回测"
4. 查看结果：资金曲线、最大回撤、夏普比率、交易记录

### 回测参数设置

```python
def init(ContextInfo):
    ContextInfo.capital = 1000000
    ContextInfo.set_commission(0.0003)
    ContextInfo.set_slippage(0.01)
    ContextInfo.set_benchmark('000300.SH')
```

## 内置函数参考

### 行情数据函数

| 函数 | 说明 |
|------|------|
| `ContextInfo.get_market_data(fields, stock_code, period, count)` | 获取K线数据 |
| `ContextInfo.get_history_data(count, period, field, stock_code)` | 获取历史数据序列 |
| `ContextInfo.get_stock_list_in_sector(sector)` | 获取板块成分股 |
| `ContextInfo.get_financial_data(stock_code)` | 获取财务数据 |
| `ContextInfo.get_instrument_detail(stock_code)` | 获取合约详情 |
| `ContextInfo.get_full_tick(stock_list)` | 获取全推行情快照 |

### 交易函数

| 函数 | 说明 |
|------|------|
| `order_shares(code, volume, style, price, ContextInfo)` | 按股数下单 |
| `order_target_value(code, value, style, price, ContextInfo)` | 按目标市值下单 |
| `order_lots(code, lots, style, price, ContextInfo)` | 按手数下单 |
| `order_percent(code, percent, style, price, ContextInfo)` | 按组合比例下单 |
| `cancel(order_id, ContextInfo)` | 撤单 |
| `get_trade_detail_data(account, market, data_type)` | 查询交易数据 |

### 交易数据类型

| data_type | 说明 | 常用字段 |
|-----------|------|----------|
| `'position'` | 持仓 | `m_strInstrumentID`, `m_nVolume`, `m_dMarketValue` |
| `'order'` | 委托 | `m_strOrderSysID`, `m_nVolumeTraded`, `m_dLimitPrice` |
| `'deal'` | 成交 | `m_strTradeID`, `m_dPrice`, `m_nVolume` |
| `'account'` | 账户 | `m_dAvailable`, `m_dBalance`, `m_dMarketValue` |

---

**来源**: [openclaw/skills](https://github.com/openclaw/skills) v1.2.0  
**官方文档**: http://dict.thinktrader.net/freshman/rookie.html
