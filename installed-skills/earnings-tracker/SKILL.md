---
name: earnings-tracker
description: AI 驱动的财报追踪器，自动扫描 A 股/美股财报日历，推送重要财报更新
description_zh: "AI 驱动的 A 股/美股财报追踪与智能分析推送"
description_en: "AI-powered earnings tracker for A-share and US stock financial reports"
version: 1.1.0
---

# Earnings Tracker - AI 驱动的财报追踪器

**自动扫描财报日历，推送重要财报更新**

---

## ✨ 核心功能

### 📅 **财报日历扫描**
- ✅ A 股预约披露时间表（AKShare）
- ✅ 美股财报日历（Yahoo Finance）
- ✅ 每周日自动扫描下周财报
- ✅ 筛选关注的公司

### 📊 **财报数据追踪**
- ✅ 业绩预告（提前信号）
- ✅ 业绩快报（快速概览）
- ✅ 正式财报（完整数据）
- ✅ 营收、净利润、同比增长

### 📈 **智能分析**
- ✅ 超预期/不及预期判断
- ✅ 关键指标提取
- ✅ AI 相关亮点识别
- ✅ 机构点评汇总

### 🔔 **自动推送**
- ✅ Discord 频道推送
- ✅ Telegram 话题推送
- ✅ 定时任务调度
- ✅ 一次性提醒

---

## 🚀 使用方法

### **1. 安装依赖**

```bash
pip install akshare
```

---

### **2. 配置关注的公司**

编辑 `config/settings.json`：

```json
{
  "watchlist": {
    "us": ["NVDA", "MSFT", "GOOGL", "META", "AMZN", "TSLA", "AMD"],
    "cn": ["600519", "000858", "601318", "000001"]
  },
  "schedule": {
    "weeklyScan": "Sunday 18:00",
    "reportScan": "after_market"
  }
}
```

---

### **3. 运行扫描**

```bash
node scripts/earnings-scanner.cjs
```

---

## 📋 工作流程

### **每周日 18:00 - 预扫描**
1. ✅ 扫描下周财报日历
2. ✅ 筛选关注的公司
3. ✅ 推送到 Discord/Telegram
4. ✅ 等待用户确认

### **用户确认后**
1. ✅ 为每个财报创建一次性提醒
2. ✅ 财报发布后搜索结果
3. ✅ 格式化摘要
4. ✅ 推送到指定频道

---

## 🌍 数据源

### **A 股（推荐）**

| 数据源 | 费用 | 接口 |
|--------|------|------|
| **AKShare** | 免费 | `stock_yysj_em()` - 预约披露时间表 |
| **AKShare** | 免费 | `stock_yjyg_em()` - 业绩预告 |
| **AKShare** | 免费 | `stock_yjkb_em()` - 业绩快报 |
| **AKShare** | 免费 | `stock_yjbb_em()` - 正式财报 |

### **美股**

| 数据源 | 费用 | 说明 |
|--------|------|------|
| Yahoo Finance | 免费 | 财报日历 |
| Alpha Vantage | 有限免费 | 财务数据 API |

---

## 📊 示例输出

### **财报日历扫描**

```
📅 下周财报日历 (2026-03-17 ~ 2026-03-21)

🇺🇸 美股：
• NVDA - 3月19日 盘后
• MSFT - 3月20日 盘后
• GOOGL - 3月18日 盘后

🇨🇳 A股：
• 600519 贵州茅台 - 3月20日
• 000858 五粮液 - 3月21日

请回复要跟踪的公司（例如：NVDA, 600519）
```

### **财报摘要推送**

```
📊 NVDA Q4 2025 财报摘要

💰 营收: $22.1B (预期 $20.4B) ✅ 超预期 8.3%
📈 EPS: $4.12 (预期 $3.95) ✅ 超预期 4.3%
📊 毛利率: 72.1% (同比 +2.3%)

🎯 关键亮点：
• 数据中心营收 $18.4B (同比 +409%)
• AI 芯片需求强劲
• 下季度指引超预期

📌 管理层指引：
• Q1 营收预期 $24B
• 毛利率维持 70%+

来源：Yahoo Finance, Seeking Alpha
```

---

## 🔧 配置文件

### `config/settings.json`

```json
{
  "watchlist": {
    "us": ["NVDA", "MSFT", "GOOGL", "META", "AMZN", "TSLA", "AMD"],
    "cn": ["600519", "000858", "601318", "000001"]
  },
  "schedule": {
    "weeklyScan": "Sunday 18:00",
    "reportScan": "after_market"
  },
  "notify": {
    "channel": "discord",
    "to": "channel:1478698808631361647"
  },
  "dataSources": {
    "cn": "akshare",
    "us": "yahoo_finance"
  }
}
```

---

## 📝 更新日志

### v1.0.0 (2026-03-14)
- ✅ 初始版本
- ✅ A 股财报日历扫描（AKShare）
- ✅ 美股财报日历扫描（Yahoo Finance）
- ✅ Discord/Telegram 推送
- ✅ 定时任务调度

---

**📊 轻松追踪财报，不错过重要信息！**
