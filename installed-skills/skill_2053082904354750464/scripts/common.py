# -*- coding: utf-8 -*-
"""
美团优惠领取工具（meituan-coupon-workbuddy）- 公共模块
提取 issue.py 和 query.py 中共用的常量、工具函数和数据读写逻辑。
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── 常量 ──────────────────────────────────────────────────────────────
_UTC8 = timezone(timedelta(hours=8))
BASE_URL = "https://peppermall.meituan.com"
# 任务类型 key（一期固定为 coupon，二期扩展时新增）
TASK_TYPE = "coupon"

# subChannelCode 存放在独立配置文件中，不硬编码在此脚本
CONFIG_FILE = Path(__file__).parent / "config.json"

# Skill 私有数据管理（使用 mt-ug-ods-skill-cache CLI）
SKILL_NAME = "meituan-coupon-workbuddy"
HISTORY_FILENAME = "mt_ods_coupon_history.json"
PHONE_HISTORY_FILENAME = "mt_ods_coupon_phone_history.json"

# 旧版历史文件路径（用于兼容迁移）
OLD_HISTORY_FILE = Path.home() / ".xiaomei-workspace" / "mt_ods_coupon_history.json"


# ── CLI 工具函数 ──────────────────────────────────────────────────────

def _get_cli_path() -> Path:
    """获取 skill_cache_cli.py 路径（本地优先）"""
    env_path = os.environ.get("SKILL_CACHE_CLI_PATH")
    if env_path:
        return Path(env_path)
    return Path(__file__).parent / "skill_cache_cli.py"


def _get_python_exe() -> str:
    """获取 Python 执行路径"""
    env_python = os.environ.get("SKILL_CACHE_PYTHON")
    if env_python:
        return env_python
    return sys.executable


def _get_workspace() -> str:
    """
    获取工作空间路径

    优先级：
    1. SKILL_CACHE_WORKSPACE 环境变量
    2. CLAUDE_WORKSPACE 环境变量
    3. XIAOMEI_WORKSPACE 环境变量
    4. 默认 ~/.xiaomei-workspace（与 skill_cache_cli.py 兼容）
    """
    workspace = os.environ.get("SKILL_CACHE_WORKSPACE") \
        or os.environ.get("CLAUDE_WORKSPACE") \
        or os.environ.get("XIAOMEI_WORKSPACE") \
        or str(Path.home() / ".xiaomei-workspace")

    Path(workspace).mkdir(parents=True, exist_ok=True)
    return workspace


def _cli_call(command: str, subcommand: str = None, args: list = None, raw_output: bool = False) -> dict:
    """调用 mt-ug-ods-skill-cache CLI"""
    args = args or []
    cmd = [_get_python_exe(), str(_get_cli_path()), command]
    if subcommand:
        cmd.append(subcommand)
    cmd.extend(args)

    env = os.environ.copy()
    env.setdefault("SKILL_CACHE_WORKSPACE", _get_workspace())

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env)
        stdout = result.stdout.strip() if result.stdout else ""

        if raw_output:
            return {"success": True, "content": stdout}

        if stdout:
            try:
                return json.loads(stdout)
            except json.JSONDecodeError:
                return {"success": True, "content": stdout}
        return {"success": False, "error": "Empty output"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── 数据读写 ──────────────────────────────────────────────────────────

def _load_from_cache(filename: str) -> dict:
    """从 skill-cache 读取 JSON 数据文件，返回字典或空 dict"""
    result = _cli_call("read", args=[SKILL_NAME, filename])
    if result and isinstance(result, dict):
        if result.get("success") is not None:
            content = result.get("content")
            if content:
                try:
                    return json.loads(content) if isinstance(content, str) else content
                except json.JSONDecodeError:
                    pass
        elif "error" not in result:
            return result
    return {}


def _save_to_cache(filename: str, data: dict):
    """将 JSON 数据写入 skill-cache"""
    _cli_call("write", args=[SKILL_NAME, filename, "--content", json.dumps(data, ensure_ascii=False)])


def _migrate_old_history() -> dict:
    """检查并迁移旧版历史文件到新位置"""
    if OLD_HISTORY_FILE.exists():
        try:
            with open(OLD_HISTORY_FILE, encoding="utf-8") as f:
                old_data = json.load(f)
            save_history(old_data)
            return old_data
        except Exception:
            pass
    return {}


def load_history() -> dict:
    """加载本 Skill 的私有领券历史数据（自动处理旧版迁移）"""
    data = _load_from_cache(HISTORY_FILENAME)
    if data:
        return data
    migrated = _migrate_old_history()
    if migrated:
        return migrated
    return {}


def save_history(data: dict):
    """保存本 Skill 的私有领券历史数据"""
    _save_to_cache(HISTORY_FILENAME, data)


def load_phone_history() -> dict:
    """加载 phone_masked 维度的领券历史数据"""
    return _load_from_cache(PHONE_HISTORY_FILENAME)


def save_phone_history(data: dict):
    """保存 phone_masked 维度的领券历史数据"""
    _save_to_cache(PHONE_HISTORY_FILENAME, data)


def load_config() -> dict:
    """加载 config.json，读取 subChannelCode 等敏感配置"""
    if not CONFIG_FILE.exists():
        print(json.dumps({
            "success": False,
            "error": "CONFIG_NOT_FOUND",
            "message": f"配置文件不存在：{CONFIG_FILE}，请联系管理员初始化"
        }, ensure_ascii=False))
        sys.exit(1)
    with open(CONFIG_FILE, encoding="utf-8") as f:
        return json.load(f)


# ── 格式化工具 ────────────────────────────────────────────────────────

def format_timestamp_ms(ts_ms: int) -> str:
    """毫秒时间戳转可读日期（UTC+8）"""
    if not ts_ms:
        return "-"
    try:
        return datetime.fromtimestamp(ts_ms / 1000, tz=_UTC8).strftime("%Y-%m-%d")
    except Exception:
        return str(ts_ms)


def append_lch_param(url: str, lch: str) -> str:
    """
    在跳转链接后拼接 lch 参数
    - lch 为空/None → 原样返回
    - url 已有参数（含 ?）→ 追加 &lch=xxx
    - url 无参数 → 追加 ?lch=xxx
    """
    if not lch or not url:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}lch={lch}"


def format_coupon(equity: dict, lch: str = "") -> dict:
    """格式化单张券信息"""
    price_limit_type = equity.get("priceLimitType", 1)
    price_limit_amount_str = equity.get("priceLimitAmountYuanStr", "")
    discount_amount_str = equity.get("discountAmountYuanStr", "")

    if price_limit_type == 1:
        use_condition = "无门槛"
    elif price_limit_type in (2, 3):
        use_condition = f"满{price_limit_amount_str}元可用"
    else:
        use_condition = f"满{price_limit_amount_str}元可用" if price_limit_amount_str else "-"

    jump_url = append_lch_param(equity.get("jumpUrl", ""), lch)

    return {
        "name": equity.get("userEquityName", "-"),
        "discount_amount": discount_amount_str,
        "use_condition": use_condition,
        "valid_start": format_timestamp_ms(equity.get("beginTime")),
        "valid_end": format_timestamp_ms(equity.get("endTime")),
        "issue_time": format_timestamp_ms(equity.get("issueTime")),
        "jump_url": jump_url,
        "user_equity_id": equity.get("userEquityId", "")
    }
