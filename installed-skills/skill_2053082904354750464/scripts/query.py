# -*- coding: utf-8 -*-
"""
美团优惠领取工具（meituan-coupon-workbuddy）- 用户领券记录查询脚本
接口：POST /eds/standard/equity/pkg/claw/result/query
用法：
  python query.py --token <user_token> --dates 20260323         # 查单天
  python query.py --token <user_token> --dates 20260320,20260323 # 查区间（含首尾）
"""

import argparse
import io
import sys

# Windows PowerShell 编码修复：确保输出 UTF-8 避免中文乱码
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import json
from datetime import datetime, timedelta

from common import (
    BASE_URL, TASK_TYPE,
    load_history, load_phone_history,
    load_config, format_coupon,
)

QUERY_PATH = "/eds/standard/equity/pkg/claw/result/query"


def get_date_range(date_str: str) -> list:
    """
    解析日期参数，返回日期列表（YYYYMMDD 格式）
    - 单日期："20260323" → ["20260323"]
    - 区间："20260320,20260323" → ["20260320", "20260321", "20260322", "20260323"]
    """
    parts = [p.strip() for p in date_str.split(",")]
    if len(parts) == 1:
        return [parts[0]]
    elif len(parts) == 2:
        start = datetime.strptime(parts[0], "%Y%m%d")
        end = datetime.strptime(parts[1], "%Y%m%d")
        if start > end:
            start, end = end, start
        result = []
        cur = start
        while cur <= end:
            result.append(cur.strftime("%Y%m%d"))
            cur += timedelta(days=1)
        return result
    else:
        print(json.dumps({
            "success": False,
            "error": "INVALID_DATE_FORMAT",
            "message": f"日期格式错误：{date_str}，请输入单个日期（20260323）或区间（20260320,20260323）"
        }, ensure_ascii=False))
        sys.exit(1)


def get_redeem_codes_by_dates(sub_channel_code: str, user_token: str, dates: list, phone_masked: str = "") -> list:
    """
    从历史文件中获取指定渠道、用户、日期范围内的 coupon 兑换码列表。

    查找顺序：
    1. 先查 mt_ods_coupon_history.json（token 维度）
    2. 若无结果且提供了 phone_masked，再查 mt_ods_coupon_phone_history.json（phone 维度）
    """
    # ── 1. 先查 token 维度 ──
    history = load_history()
    token_data = history.get(sub_channel_code, {}).get(user_token, {})
    codes = []
    for date in dates:
        date_codes = token_data.get(date, {}).get(TASK_TYPE, [])
        codes.extend(date_codes)

    # ── 2. token 维度无结果，兜底查 phone_masked 维度 ──
    if not codes and phone_masked:
        phone_history = load_phone_history()
        phone_data = phone_history.get(sub_channel_code, {}).get(phone_masked, {})
        for date in dates:
            date_codes = phone_data.get(date, {}).get(TASK_TYPE, [])
            codes.extend(date_codes)

    # 去重，保持顺序
    seen = set()
    unique_codes = []
    for c in codes:
        if c not in seen:
            seen.add(c)
            unique_codes.append(c)
    return unique_codes


def main():
    parser = argparse.ArgumentParser(description="美团权益领取记录查询")
    parser.add_argument("--token", required=True, help="用户 user_token")
    parser.add_argument("--phone-masked", default="", help="脱敏手机号（可选，用于兜底查询 phone 维度历史）")
    parser.add_argument("--dates", required=True,
                        help="查询日期，单天如 20260323，区间如 20260320,20260323")
    args = parser.parse_args()

    import httpx

    config = load_config()
    sub_channel_code = config.get("subChannelCode")
    lch = config.get("lch", "")
    if not sub_channel_code:
        print(json.dumps({
            "success": False,
            "error": "CONFIG_INVALID",
            "message": "配置文件缺少 subChannelCode 字段"
        }, ensure_ascii=False))
        sys.exit(1)

    # 解析日期范围
    dates = get_date_range(args.dates)

    # 从历史文件获取兑换码（先查 token 维度，无结果再查 phone_masked 维度）
    redeem_codes = get_redeem_codes_by_dates(sub_channel_code, args.token, dates, phone_masked=args.phone_masked)

    if not redeem_codes:
        print(json.dumps({
            "success": True,
            "code": 0,
            "query_dates": dates,
            "redeem_code_count": 0,
            "records": [],
            "message": f"在 {dates[0]}{'~' + dates[-1] if len(dates) > 1 else ''} 期间未找到领取记录（本地无兑换码存档）"
        }, ensure_ascii=False))
        return

    # 构造请求
    body = {
        "subChannelCode": sub_channel_code,
        "token": args.token,
        "equityPkgRedeemCodeList": redeem_codes
    }

    try:
        resp = httpx.post(
            BASE_URL + QUERY_PATH,
            json=body,
            headers={"Content-Type": "application/json"},
            timeout=15,
            verify=True
        )
        resp_data = resp.json()
    except httpx.TimeoutException:
        print(json.dumps({
            "success": False,
            "error": "TIMEOUT",
            "message": "请求超时，请稍后重试"
        }, ensure_ascii=False))
        sys.exit(1)
    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": "NETWORK_ERROR",
            "message": f"网络异常：{str(e)}"
        }, ensure_ascii=False))
        sys.exit(1)

    code = resp_data.get("code")
    message = resp_data.get("message", "")
    data = resp_data.get("data", [])

    if code == 0:
        # 格式化每条记录
        records = []
        for item in (data or []):
            redeem_code = item.get("equityRedeemCode", "")
            success_list = item.get("successEquityList", [])
            records.append({
                "redeem_code": redeem_code,
                "coupon_count": len(success_list),
                "coupons": [format_coupon(e, lch=lch) for e in success_list]
            })

        print(json.dumps({
            "success": True,
            "code": 0,
            "query_dates": dates,
            "redeem_code_count": len(redeem_codes),
            "record_count": len(records),
            "records": records
        }, ensure_ascii=False))
    else:
        print(json.dumps({
            "success": False,
            "code": code,
            "error": "API_ERROR",
            "message": f"查询失败（错误码：{code}，{message}）"
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
