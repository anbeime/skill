# -*- coding: utf-8 -*-
"""
美团优惠领取工具（meituan-coupon-workbuddy）- 权益包发放脚本
接口：POST /eds/standard/equity/pkg/issue/claw
用法：python issue.py --token <user_token> --phone-masked <phone_masked>
"""

import argparse
import io
import sys

# Windows PowerShell 编码修复：确保输出 UTF-8 避免中文乱码
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import hashlib
import json
from datetime import datetime

from common import (
    _UTC8, BASE_URL, TASK_TYPE,
    load_history, save_history,
    load_phone_history, save_phone_history,
    load_config, format_coupon,
)

ISSUE_PATH = "/eds/standard/equity/pkg/issue/claw"


def gen_redeem_code(user_token: str, phone_masked: str, date_str: str) -> str:
    """
    生成当天领券唯一键
    规则：MD5(user_token + "_" + phone_masked + "_" + YYYYMMDD)

    说明：phone_masked 是脱敏手机号（如 152****0460），不同用户去掉中间4位后
    可能产生碰撞，因此在 MD5 原始串中额外加入 user_token 以保证唯一性。
    """
    raw = f"{user_token}_{phone_masked}_{date_str}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


def save_redeem_code(sub_channel_code: str, user_token: str, date_str: str, redeem_code: str, phone_masked: str = ""):
    """
    将兑换码写入历史文件。

    同时写入两份：
    1. mt_ods_coupon_history.json — token 维度（原有逻辑，不变）
       结构：history[subChannelCode][user_token][date][coupon] = [codes]
    2. mt_ods_coupon_phone_history.json — phone_masked 维度（新增，兜底）
       结构：history[subChannelCode][phone_masked][date][coupon] = [codes]

    每次写入前检查是否已存在，避免重复追加。
    """
    # ── 1. 原有 token 维度写入（不变）──
    history = load_history()
    channel_data = history.setdefault(sub_channel_code, {})
    token_data = channel_data.setdefault(user_token, {})
    date_data = token_data.setdefault(date_str, {})
    codes = date_data.setdefault(TASK_TYPE, [])
    if redeem_code not in codes:
        codes.append(redeem_code)
    save_history(history)

    # ── 2. 新增 phone_masked 维度写入（兜底）──
    if phone_masked:
        phone_history = load_phone_history()
        p_channel = phone_history.setdefault(sub_channel_code, {})
        p_phone = p_channel.setdefault(phone_masked, {})
        p_date = p_phone.setdefault(date_str, {})
        p_codes = p_date.setdefault(TASK_TYPE, [])
        if redeem_code not in p_codes:
            p_codes.append(redeem_code)
        save_phone_history(phone_history)


def main():
    parser = argparse.ArgumentParser(description="美团权益包发放")
    parser.add_argument("--token", required=True, help="用户 user_token")
    parser.add_argument("--phone-masked", required=True, help="脱敏手机号（用于生成 redeem_code）")
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

    # 获取当天领券唯一键：优先复用历史记录，无则新生成（不提前写入，发券成功后再写）
    today = datetime.now(_UTC8).strftime("%Y%m%d")
    history = load_history()
    existing_codes = (
        history.get(sub_channel_code, {})
               .get(args.token, {})
               .get(today, {})
               .get(TASK_TYPE, [])
    )

    # 兜底：token 维度无记录时，查 phone_masked 维度（解决重新登录后 token 变化问题）
    if not existing_codes and args.phone_masked:
        phone_history = load_phone_history()
        existing_codes = (
            phone_history.get(sub_channel_code, {})
                         .get(args.phone_masked, {})
                         .get(today, {})
                         .get(TASK_TYPE, [])
        )

    if existing_codes:
        # 当天已有领取记录，复用最后一个 equityPkgRedeemCode（避免重复生成）
        redeem_code = existing_codes[-1]
    else:
        # 当天首次领取，生成新的 equityPkgRedeemCode（发券成功后再写入历史文件）
        redeem_code = gen_redeem_code(args.token, args.phone_masked, today)

    # 构造请求
    body = {
        "subChannelCode": sub_channel_code,
        "token": args.token,
        "equityPkgRedeemCode": redeem_code
    }

    try:
        resp = httpx.post(
            BASE_URL + ISSUE_PATH,
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
    data = resp_data.get("data")

    # 错误码映射
    ERROR_MAP = {
        4009: ("ACTIVITY_ENDED", "活动已结束，暂时无法领取"),
        4010: ("ALREADY_RECEIVED", "你今天已经通过小美领取过美团权益了，明天再来哦～"),
        4011: ("QUOTA_EXHAUSTED", "抱歉，本次活动权益已发放完毕，下次早点来哦～"),
    }

    if code == 0:
        # 发券成功（code=0），保存兑换码到历史文件（首次领取时才写，复用历史 code 不重复写）
        is_first_issue = not bool(existing_codes)
        if is_first_issue:
            save_redeem_code(sub_channel_code, args.token, today, redeem_code, phone_masked=args.phone_masked)

        success_list = data.get("successEquityList", [])
        formatted_coupons = [format_coupon(e, lch=lch) for e in success_list]

        print(json.dumps({
            "success": True,
            "code": 0,
            "is_first_issue": is_first_issue,
            # is_first_issue=true  → 本次首次领取成功，向用户展示"🎉 领取成功！"
            # is_first_issue=false → 今日已领取过，不可重复领取，向用户展示：
            #   "⚠️ 今天已经领取过了，不能重复领取。以下是上次领取的券信息：" + coupons
            "redeem_code": redeem_code,
            "request_id": data.get("requestId", ""),
            "issue_status": data.get("equityPkgIssueStatus"),
            "coupon_count": len(formatted_coupons),
            "coupons": formatted_coupons
        }, ensure_ascii=False))

    elif code in ERROR_MAP:
        err_key, err_msg = ERROR_MAP[code]
        print(json.dumps({
            "success": False,
            "code": code,
            "error": err_key,
            "message": err_msg
        }, ensure_ascii=False))

    else:
        print(json.dumps({
            "success": False,
            "code": code,
            "error": "SYSTEM_ERROR",
            "message": f"系统繁忙，请稍后重试（错误码：{code}，{message}）"
        }, ensure_ascii=False))


if __name__ == "__main__":
    main()
