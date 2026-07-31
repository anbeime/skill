# 交易信号标准格式

## 买入信号 (Buy Signal)
```json
{
  "timestamp": "2026-04-04 14:30:00",
  "symbol": "600519.SH",
  "signal": "buy",
  "price": 1680.00,
  "target_shares": 100,
  "volume_ratio": 1.8,
  "sentiment_score": 65,
  "sentiment_label": "利好",
  "news_summary": "白酒板块受政策利好催化，多家券商上调评级",
  "technical_score": 78,
  "reason": "MACD金叉+放量突破MA20+情绪利好+综合评分78",
  "stop_loss": 1620.00,
  "take_profit": 1800.00,
  "position_pct": 15,
  "risk_level": "medium",
  "factors": {
    "momentum_score": 72,
    "trend_score": 80,
    "volume_score": 75,
    "volatility_score": 65,
    "macd_score": 85,
    "rsi_score": 60,
    "boll_score": 70
  }
}
```

## 卖出信号 (Sell Signal)
```json
{
  "timestamp": "2026-04-04 10:15:00",
  "symbol": "600519.SH",
  "signal": "sell",
  "price": 1750.00,
  "target_shares": 100,
  "reason": "移动止盈触发: 最高1780 → 止盈线1720",
  "stop_loss": null,
  "take_profit": null,
  "pnl_pct": 4.17,
  "hold_days": 5,
  "exit_type": "trailing_stop"
}
```

## 观望信号 (Hold Signal)
```json
{
  "timestamp": "2026-04-04 11:00:00",
  "symbol": "600519.SH",
  "signal": "hold",
  "price": 1700.00,
  "reason": "综合评分58(低于阈值70)，技术条件仅满足2/5",
  "technical_score": 58
}
```

## 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| timestamp | string | ✅ | 信号生成时间 ISO 8601 |
| symbol | string | ✅ | 股票代码（如600519.SH） |
| signal | string | ✅ | buy/sell/hold |
| price | float | ✅ | 当前价格 |
| target_shares | int | ❌ | 建议交易股数（100的整数倍） |
| volume_ratio | float | ❌ | 量比（当前量/20日均量） |
| sentiment_score | int | ❌ | 情绪评分（-100到+100） |
| sentiment_label | string | ❌ | 利好/利空/中性 |
| news_summary | string | ❌ | 新闻摘要（限200字） |
| technical_score | int | ❌ | 技术综合评分（0-100） |
| reason | string | ✅ | 决策原因说明 |
| stop_loss | float | ❌ | 建议止损价 |
| take_profit | float | ❌ | 建议止盈价 |
| position_pct | float | ❌ | 建议仓位占比（%） |
| risk_level | string | ❌ | low/medium/high |
| factors | object | ❌ | 各因子评分明细 |
