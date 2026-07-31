---
name: auto-trading
description: 全自动AI量化交易系统。集成行情采集、新闻情绪分析、多因子信号生成、自动下单执行、动态风控和可视化监控的完整交易链路。支持A股/港股/美股，可对接QMT/发明者量化等平台。
description_zh: "全自动AI量化交易技能，支持行情采集、情绪分析、信号生成、自动交易、风控和监控"
description_en: "Fully automated AI quantitative trading system with market data, sentiment analysis, signal generation, auto-execution, risk control and monitoring"
version: 1.0.0
dependency:
  python:
    - requests>=2.28.0
    - numpy>=1.24.0
    - pandas>=2.0.0
    - beautifulsoup4>=4.12.0
    - flask>=3.0.0
    - plotly>=5.18.0
    - akshare>=1.12.0
---

# 全自动AI量化交易系统

## 任务目标
- 本 Skill 用于：构建从行情采集→情绪分析→信号生成→自动下单→风控监控的**全链路无人值守交易系统**
- 能力包含：实时行情抓取、新闻舆情情绪分析、多维度交易信号生成、自动下单执行、ATR动态风控、可视化仪表板监控
- 触发条件：用户要求自动交易、无人值守盯盘、AI辅助交易时使用

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    AI 交易大脑 (ClawdBot)                │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ 行情采集  │→│ 情绪分析  │→│ 信号生成  │              │
│  └──────────┘  └──────────┘  └──────────┘              │
│       ↓                            ↓                   │
│  ┌──────────┐              ┌──────────┐              │
│  │ 多因子评分│              │ 风控检查  │              │
│  └──────────┘              └──────────┘              │
│                                    ↓                    │
│                            ┌──────────┐              │
│                            │ 信号发送  │──→ HTTP API  │
│                            └──────────┘              │
└─────────────────────────────────────────────────────────┘
                     ↓ HTTP POST (JSON)
┌─────────────────────────────────────────────────────────┐
│              交易平台 (QMT / FMZ 发明者量化)             │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │ 信号接收  │→│ 交易执行  │→│ 持仓管理  │              │
│  └──────────┘  └──────────┘  └──────────┘              │
│                                    ↓                    │
│                            ┌──────────┐              │
│                            │ 止损风控  │              │
│                            └──────────┘              │
└─────────────────────────────────────────────────────────┘
                     ↓ 状态回传
┌─────────────────────────────────────────────────────────┐
│                 可视化监控仪表板                          │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐          │
│  │权益概览│ │止损监控│ │AI信号  │ │交易记录│          │
│  └────────┘ └────────┘ └────────┘ └────────┘          │
└─────────────────────────────────────────────────────────┘
```

## 前置准备

### 依赖安装
```bash
pip install requests numpy pandas beautifulsoup4 flask plotly akshare
```

### 平台配置
1. **QMT**: 确保QMT客户端已启动并登录
2. **FMZ发明者量化**: 注册并创建API Key
3. **数据源**: AKShare(免费) / 通联数据(付费) / Tushare(付费)

### 配置文件
编辑 `scripts/config.json`:
```json
{
  "platform": "qmt",
  "market": "cn",
  "watchlist": ["600519.SH", "000858.SZ", "00700.HK", "AAPL.US"],
  "scan_interval": 300,
  "risk": {
    "max_position_pct": 20,
    "max_drawdown_pct": 15,
    "stop_loss_atr_mult": 2.0,
    "take_profit_atr_mult": 4.0,
    "daily_loss_limit_pct": 3
  },
  "api": {
    "signal_endpoint": "http://localhost:8080/api/signal",
    "dashboard_port": 5000
  },
  "notification": {
    "enabled": false,
    "type": "webhook",
    "url": ""
  }
}
```

## 操作步骤

### 标准流程

1. **行情数据采集**
   - 执行 `python scripts/market_fetcher.py --config config.json`
   - 获取实时价格、成交量、技术指标
   - 数据源优先级：AKShare > Tushare > Yahoo Finance
   - 输出：标准化的市场数据JSON

2. **新闻情绪分析**
   - 执行 `python scripts/sentiment_analyzer.py --config config.json`
   - 抓取最新财经新闻（财联社/东方财富/新浪财经）
   - AI分析新闻情绪（利好/利空/中性）
   - 综合情绪评分（-100 到 +100）
   - 输出：情绪分析报告JSON

3. **多因子信号生成**
   - 执行 `python scripts/signal_generator.py --config config.json`
   - 整合行情数据 + 情绪分析 + 技术指标
   - 多因子评分：动量/趋势/量价/波动率/MACD/RSI
   - 生成标准交易信号JSON

4. **风控检查**
   - 检查市场状态（强势/正常/弱势）
   - 检查账户持仓和资金
   - 检查止损风控条件
   - 通过后才发送交易信号

5. **信号发送**
   - 通过HTTP POST发送JSON到交易平台API
   - 信号格式：标准JSON
   - 记录到 Trade_Diary.csv

6. **自动执行**（交易平台端）
   - QMT/FMZ 接收信号并执行交易
   - 止损止盈自动监控
   - 持仓状态回传

7. **可视化监控**
   - 启动 `python dashboard/app.py`
   - 实时查看权益、持仓、信号、风控状态

### 交易信号JSON格式
```json
{
  "timestamp": "2026-04-04 14:30:00",
  "symbol": "600519.SH",
  "signal": "buy",
  "price": 1680.00,
  "volume_ratio": 1.8,
  "sentiment_score": 65,
  "sentiment_label": "利好",
  "news_summary": "白酒板块受政策利好催化...",
  "technical_score": 78,
  "reason": "MACD金叉+放量突破+情绪利好+评分78",
  "stop_loss": 1620.00,
  "take_profit": 1800.00,
  "position_pct": 15,
  "risk_level": "medium"
}
```

## 资源索引
- 行情采集：见 [scripts/market_fetcher.py](scripts/market_fetcher.py)
- 情绪分析：见 [scripts/sentiment_analyzer.py](scripts/sentiment_analyzer.py)
- 信号生成：见 [scripts/signal_generator.py](scripts/signal_generator.py)
- 信号发送：见 [scripts/signal_sender.py](scripts/signal_sender.py)
- 监控仪表板：见 [dashboard/app.py](dashboard/app.py)
- 信号格式：见 [references/signal_format.md](references/signal_format.md)
- 风控规则：见 [references/risk_rules.md](references/risk_rules.md)
- QMT对接：见 [references/qmt_integration.md](references/qmt_integration.md)
- FMZ对接：见 [references/fmz_integration.md](references/fmz_integration.md)

## 注意事项
- **投资有风险，入市需谨慎**，所有交易决策仅供参考
- 建议先用模拟盘测试至少1个月，验证策略有效性
- AI情绪分析存在误差，不应作为唯一决策依据
- 必须设置止损，单笔最大亏损不超过本金2%
- 全自动交易前，建议先半自动运行观察1-2周
- 交易日志定期审计，发现异常及时暂停

## 使用示例

### 示例1：A股全自动交易
```bash
# 1. 启动监控仪表板
python dashboard/app.py --port 5000

# 2. 启动自动交易循环
python scripts/auto_trade_loop.py --config config.json --interval 300
```

### 示例2：单次信号生成
```bash
python scripts/signal_generator.py --symbol 600519.SH --market cn
```

### 示例3：情绪分析
```bash
python scripts/sentiment_analyzer.py --symbol 600519.SH --sources cls,eastmoney
```
