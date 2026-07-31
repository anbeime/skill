#!/usr/bin/env python3
"""
Earnings Tracker - AI 驱动的财报追踪器（中国版）

功能：
1. 扫描 A 股财报日历（AKShare）
2. 筛选关注的公司
3. 推送到 Discord/Telegram
"""

import json
import sys
from datetime import datetime, timedelta

try:
    import akshare as ak
except ImportError:
    print("❌ 请先安装 akshare: pip install akshare")
    sys.exit(1)

# 配置
CONFIG = {
    "watchlist": {
        "us": ["NVDA", "MSFT", "GOOGL", "META", "AMZN", "TSLA", "AMD"],
        "cn": ["600519", "000858", "601318", "000001"]
    },
    "notify": {
        "channel": "discord",
        "to": "channel:1478698808631361647"
    }
}

def get_cn_earnings_calendar():
    """获取 A 股财报预约披露时间表"""
    try:
        print(f"\n📊 获取 A 股财报预约披露时间表...")
        
        # 尝试获取最近几个季度的数据
        now = datetime.now()
        quarters = []
        
        # 当前季度和下一季度
        current_quarter = (now.month - 1) // 3 + 1
        for q in [current_quarter, current_quarter + 1]:
            if q <= 4:
                date_str = f"{now.year}{q:02d}31"
            else:
                date_str = f"{now.year + 1}01{q-4:02d}31"
            quarters.append(date_str)
        
        print(f"  🔍 查询季度: {', '.join(quarters)}")
        
        all_earnings = []
        for date_str in quarters:
            try:
                df = ak.stock_yysj_em(date=date_str)
                if df is not None and not df.empty:
                    # 筛选关注的公司
                    watchlist = CONFIG["watchlist"]["cn"]
                    my_stocks = df[df["股票代码"].isin(watchlist)]
                    
                    for _, row in my_stocks.iterrows():
                        all_earnings.append({
                            "code": row["股票代码"],
                            "name": row["股票简称"],
                            "date": row.get("首次预约时间", "待定"),
                            "type": "cn"
                        })
            except Exception as e:
                print(f"  ⚠️  查询 {date_str} 失败: {e}")
                continue
        
        if all_earnings:
            print(f"  ✅ 找到 {len(all_earnings)} 个 A 股财报预约")
            return all_earnings
        else:
            print("  ℹ️  本季度暂无关注公司的财报预约")
            return []
    
    except Exception as e:
        print(f"  ❌ 获取 A 股财报日历失败: {e}")
        return []

def get_cn_performance_forecast():
    """获取 A 股业绩预告（提前信号）"""
    try:
        print(f"\n📊 获取 A 股业绩预告...")
        df = ak.stock_yjyg_em()
        
        if df is not None and not df.empty:
            # 筛选关注的公司
            watchlist = CONFIG["watchlist"]["cn"]
            my_stocks = df[df["股票代码"].isin(watchlist)]
            
            if not my_stocks.empty:
                print(f"  ✅ 找到 {len(my_stocks)} 个业绩预告")
                
                forecasts = []
                for _, row in my_stocks.iterrows():
                    forecasts.append({
                        "code": row["股票代码"],
                        "name": row["股票简称"],
                        "type": row.get("预告类型", "未知"),
                        "change": row.get("净利润增减", "未知")
                    })
                
                return forecasts
        
        print("  ℹ️  暂无业绩预告")
        return []
    
    except Exception as e:
        print(f"  ❌ 获取业绩预告失败: {e}")
        return []

def format_earnings_report(cn_earnings, cn_forecasts):
    """格式化财报报告"""
    report = []
    report.append("📅 下周财报日历（中国版）\n")
    report.append("=" * 50)
    
    if cn_earnings:
        report.append("\n🇨🇳 A股财报预约：\n")
        for e in cn_earnings:
            report.append(f"• {e['code']} {e['name']} - {e['date']}")
    
    if cn_forecasts:
        report.append("\n📈 业绩预告：\n")
        for f in cn_forecasts:
            report.append(f"• {f['code']} {f['name']} - {f['type']} ({f['change']})")
    
    if not cn_earnings and not cn_forecasts:
        report.append("\nℹ️  本周暂无关注公司的财报\n")
    
    report.append("\n" + "=" * 50)
    report.append("\n请回复要跟踪的公司（例如：600519, NVDA）")
    
    return "\n".join(report)

def main():
    print("📊 Earnings Tracker 启动（中国版）\n")
    print("=" * 50)
    
    # 获取 A 股财报日历
    cn_earnings = get_cn_earnings_calendar()
    
    # 获取业绩预告
    cn_forecasts = get_cn_performance_forecast()
    
    # 格式化报告
    report = format_earnings_report(cn_earnings, cn_forecasts)
    print("\n" + report)
    
    # 保存结果
    result = {
        "timestamp": datetime.now().isoformat(),
        "cn_earnings": cn_earnings,
        "cn_forecasts": cn_forecasts,
        "report": report
    }
    
    output_file = "/Users/xufan65/.openclaw/workspace/memory/earnings-calendar.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ 结果已保存到: {output_file}")
    print("\n" + "=" * 50)
    print("✅ Earnings Tracker 完成\n")

if __name__ == "__main__":
    main()
