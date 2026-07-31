#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
meituan-coupon-workbuddy 内嵌认证模块 v1.0.15
基于 meituan-c-user-auth v1.0.15 内嵌，用户无需单独安装 meituan-c-user-auth。
对接 EDS Claw 短信登录接口，管理 user_token 与 device_token。

用法示例：
  python auth.py version-check
  python auth.py status
  python auth.py token-verify
  python auth.py send-sms --phone 13812345678
  python auth.py verify --phone 13812345678 --code 123456
  python auth.py logout
  python auth.py clear-device-token
"""

import argparse
import hashlib
import json
import os
import random
import subprocess
import sys
import time
import warnings
from pathlib import Path

# 屏蔽 httpx/urllib3 的 SSL 不验证警告，避免污染 JSON stdout 输出
warnings.filterwarnings("ignore", message=".*ssl.*", category=UserWarning)
try:
    import urllib3
    urllib3.disable_warnings()
except ImportError:
    pass

# Windows PowerShell 编码修复：确保输出 UTF-8 避免中文乱码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ── 常量 ──────────────────────────────────────────────────────────────
AUTH_KEY       = "meituan-c-user-auth"
LOCAL_VERSION  = "1.0.34"  # 本文件的版本号，与 SKILL.md 中 version 字段保持一致

# 用户协议接受状态字段名
TERMS_ACCEPTED_KEY = "terms_accepted"

# Skill 公开主页（clawhub.ai，外网可访问）
SKILL_PAGE_URL = "https://clawhub.ai/meituan-zhengchang/meituan-coupon-workbuddy"

# ── mt-ug-ods-skill-cache 集成配置 ────────────────────────────────────
# 新存储方式：使用 mt-ug-ods-skill-cache CLI 管理认证数据

def _get_cli_path() -> Path:
    """获取 skill_cache_cli.py 路径（本地优先）"""
    import os
    # 1. 优先从环境变量读取
    env_path = os.environ.get("SKILL_CACHE_CLI_PATH")
    if env_path:
        return Path(env_path)
    # 2. 使用本 Skill 自带的 CLI
    return Path(__file__).parent / "skill_cache_cli.py"


def _get_python_exe() -> str:
    """获取 Python 执行路径"""
    import os
    env_python = os.environ.get("SKILL_CACHE_PYTHON")
    if env_python:
        return env_python
    # 默认使用系统 python3
    return sys.executable


# CLI 路径配置
CLI_PATH = _get_cli_path()
PYTHON_EXE = _get_python_exe()


def _get_workspace() -> str:
    """
    获取工作空间路径。

    优先级：
    1. 环境变量 SKILL_CACHE_WORKSPACE（用户显式指定）
    2. 环境变量 CLAUDE_WORKSPACE
    3. 环境变量 XIAOMEI_WORKSPACE
    4. 默认：~/.xiaomei-workspace

    设计说明：
    - 美团 Skill 统一使用 ~/.xiaomei-workspace/ 作为工作空间
    - 与 meituan-coupon-workbuddy 保持一致，确保 Token 互通
    - 其他非美团 Skill 建议让 CLI 自动探测或指定自己的路径

    注意：如果目录不存在会自动创建（兼容首次运行的纯净环境）
    """
    import os
    workspace = os.environ.get("SKILL_CACHE_WORKSPACE") \
        or os.environ.get("CLAUDE_WORKSPACE") \
        or os.environ.get("XIAOMEI_WORKSPACE") \
        or str(Path.home() / ".xiaomei-workspace")

    # 确保目录存在（兼容首次运行的纯净环境）
    Path(workspace).mkdir(parents=True, exist_ok=True)
    return workspace


def _cli_call(command: str, subcommand: str = None, args: list = None, raw_output: bool = False) -> dict:
    """
    调用 mt-ug-ods-skill-cache CLI

    Args:
        command: 主命令（如 auth, shared, read, write 等）
        subcommand: 子命令（如 get, set, list 等）
        args: 额外参数列表
        raw_output: 是否返回原始输出（用于 shared read 等直接返回内容的命令）

    Returns:
        CLI 返回的 JSON 字典，或原始内容字符串（raw_output=True 时）
    """
    import os
    args = args or []
    cmd = [PYTHON_EXE, str(CLI_PATH), command]
    if subcommand:
        cmd.append(subcommand)
    cmd.extend(args)

    # 配置环境变量，确保 CLI 能正确探测工作空间
    # 避免依赖 cwd 导致路径不一致的问题
    env = os.environ.copy()
    env.setdefault("SKILL_CACHE_WORKSPACE", _get_workspace())

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env)
        stdout = result.stdout.strip() if result.stdout else ""

        # raw_output 模式：直接返回原始内容
        if raw_output:
            return {"success": True, "content": stdout}

        # 尝试解析 JSON
        if stdout:
            try:
                return json.loads(stdout)
            except json.JSONDecodeError:
                # 非 JSON 输出，封装为 content
                return {"success": True, "content": stdout}
        return {"success": False, "error": "Empty output"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── 旧版兼容：传统文件存储路径 ─────────────────────────────────────────
# 保留用于向后兼容和自动迁移

def _resolve_legacy_auth_file() -> Path:
    """
    旧版 Token 存储路径（用于兼容迁移）
    1. 环境变量 XIAOMEI_AUTH_FILE（显式指定）
    2. ~/.xiaomei-workspace/mt_auth_tokens.json（小美搭档默认）

    注意：其他潜在历史位置（如 ~/.openclaw/workspace/auth_tokens.json）
    由 _get_legacy_auth_files() 处理，按优先级遍历。
    """
    import os
    env_path = os.environ.get("XIAOMEI_AUTH_FILE")
    if env_path:
        return Path(env_path)
    return Path.home() / ".xiaomei-workspace" / "mt_auth_tokens.json"


def _get_legacy_auth_files() -> list:
    """
    获取所有潜在的旧版 mt_auth_tokens.json 路径列表（按优先级排序）

    优先级：
    1. 环境变量 XIAOMEI_AUTH_FILE
    2. ~/.xiaomei-workspace/mt_auth_tokens.json (小美搭档默认)
    3. ~/.openclaw/workspace/auth_tokens.json (OpenClaw 默认)
    """
    import os
    files = []

    # 1. 环境变量（最高优先级）
    env_path = os.environ.get("XIAOMEI_AUTH_FILE")
    if env_path:
        files.append(Path(env_path))

    # 2. 小美搭档默认路径（新文件名）
    xiaomei_path = Path.home() / ".xiaomei-workspace" / "mt_auth_tokens.json"
    if xiaomei_path not in files:
        files.append(xiaomei_path)

    # 3. 小美搭档旧文件名（不带 mt_ 前缀的历史版本）
    xiaomei_old_path = Path.home() / ".xiaomei-workspace" / "auth_tokens.json"
    if xiaomei_old_path not in files:
        files.append(xiaomei_old_path)

    # 4. OpenClaw 默认路径（保留旧文件名）
    openclaw_path = Path.home() / ".openclaw" / "workspace" / "auth_tokens.json"
    if openclaw_path not in files:
        files.append(openclaw_path)

    return files


LEGACY_AUTH_FILE = _resolve_legacy_auth_file()


# ── 存储操作（新版：使用 CLI）──────────────────────────────────────────

def _migrate_from_legacy_if_needed() -> dict:
    """
    从旧版文件迁移到 mt-ug-ods-skill-cache

    迁移策略：
    1. 检查新位置（.shared/mt_auth_tokens.json）是否已有有效 token 数据
       - 使用 auth get 命令，返回的是已解析的 dict 数据（非包装结构）
       - "有效"定义为：存在 user_token 或 device_token（退出登录后仍有 device_token）
    2. 如果新位置无有效数据，遍历所有潜在的旧位置（优先级顺序）
    3. 将第一个找到的有效旧数据复制到新位置
    4. 保留旧文件不删除（兼容其他工具）

    注意：device_token 的存在也视为"已有数据"，避免退出登录后的重复迁移

    Returns:
        {"migrated": True/False, "reason": "...", "data": {...}, "source": "..."}
    """
    # 1. 检查新位置是否已有有效数据（使用 auth get 命令）
    # 注意：CLI auth get 只输出 result["data"] 到 stdout，不是完整的 {"success", "data", "found"} 结构
    # 所以 _cli_call 返回的直接是 data 本身：{"user_token": ..., "device_token": ...} 或 {}
    auth_data = _cli_call("auth", "get", [AUTH_KEY])

    # 检查是否有有效 token：user_token（登录态）或 device_token（已初始化）
    # 使用 device_token 作为判断条件，确保退出登录后（user_token=""）不会重复迁移
    if auth_data and isinstance(auth_data, dict) and (auth_data.get("user_token") or auth_data.get("device_token")):
        return {"migrated": False, "reason": "新位置已存在有效数据（user_token 或 device_token）"}

    # 2. 遍历所有潜在的旧文件位置
    legacy_files = _get_legacy_auth_files()
    legacy_data = None
    found_path = None

    for legacy_path in legacy_files:
        if legacy_path.exists():
            try:
                with open(legacy_path, "r", encoding="utf-8") as f:
                    legacy_data = json.load(f)
                # 验证数据有效性
                auth_data = legacy_data.get(AUTH_KEY, {})
                if auth_data.get("user_token") or auth_data.get("device_token"):
                    found_path = legacy_path
                    break  # 找到有效数据，停止遍历
            except Exception:
                continue  # 读取失败，尝试下一个

    if found_path is None:
        return {"migrated": False, "reason": "未找到有效的旧文件"}

    # 3. 将数据写入新位置（使用 shared write，迁移完整数据结构）
    # 迁移完整数据，包括 user_token、device_token、terms_accepted 等所有字段
    write_result = _cli_call("shared", "write", ["mt_auth_tokens.json", "--content", json.dumps(legacy_data)])

    if write_result.get("success"):
        return {
            "migrated": True,
            "reason": "迁移成功",
            "data": auth_data,
            "source": str(found_path),
            "new_path": write_result.get("path", "skills_local_cache/.shared/mt_auth_tokens.json")
        }
    else:
        return {
            "migrated": False,
            "reason": f"写入新位置失败: {write_result.get('error')}"
        }


def load_auth() -> dict:
    """
    加载认证数据（新版：使用 CLI）
    自动触发旧版迁移（只有新位置不存在时才检查）
    """
    # 先尝试迁移（只有新位置不存在时才执行）
    _migrate_from_legacy_if_needed()

    # 使用 shared read 获取完整的 mt_auth_tokens.json 内容
    # 注意：_cli_call 返回结果的嵌套结构与命令类型有关
    # - shared read: 文件存在时返回文件内容本身（dict），不存在时返回 {"success": False, "error": "..."}
    # - auth get: 直接返回查询的 auth_data 内容（dict）
    # 所以 shared read 需要检查 result.get("error") 来判断是否成功
    result = _cli_call("shared", "read", ["mt_auth_tokens.json"])
    if result and not result.get("error"):
        # 成功时 result 本身就是 mt_auth_tokens.json 的内容（可能是空 dict 或具体数据）
        if isinstance(result, dict):
            return result
    return {}


def save_auth(data: dict):
    """
    保存认证数据（新版：使用 CLI）
    同时更新 meituan-c-user-auth 的认证条目

    注意：迁移逻辑在 load_auth() 中已处理，此处无需重复调用
    """
    # 读取现有数据（内部已包含迁移检查）
    existing = load_auth()
    existing[AUTH_KEY] = data

    # 写入新位置
    _cli_call("shared", "write", ["mt_auth_tokens.json", "--content", json.dumps(existing, ensure_ascii=False)])


# 保留旧函数名用于兼容性
def get_token_data() -> dict:
    """获取本 Skill 的 Token 数据"""
    return load_auth().get(AUTH_KEY, {})


def save_token_data(token_data: dict):
    """保存本 Skill 的 Token 数据"""
    save_auth(token_data)


def get_terms_accepted() -> bool:
    """获取用户是否接受服务协议的状态"""
    token_data = get_token_data()
    return token_data.get(TERMS_ACCEPTED_KEY, False)


def set_terms_accepted(accepted: bool):
    """设置用户服务协议接受状态"""
    token_data = get_token_data()
    token_data[TERMS_ACCEPTED_KEY] = accepted
    save_token_data(token_data)


def logout_token_data():
    """
    退出登录：仅将 user_token 置为空字符串
    device_token 保持不变
    """
    token_data = get_token_data()
    token_data["user_token"] = ""
    save_token_data(token_data)

# 外网域名
BASE_URL = "https://peppermall.meituan.com"

# 接口路径
SMS_CODE_GET_PATH    = "/eds/claw/login/sms/code/get"
SMS_CODE_VERIFY_PATH = "/eds/claw/login/sms/code/verify"
TOKEN_VERIFY_PATH    = "/eds/claw/login/token/verify"



# ── 版本检测 ──────────────────────────────────────────────────────────

def _parse_version(text: str) -> str:
    """从文本中提取 version: "x.y.z" 格式的版本号"""
    import re
    m = re.search(r'version:\s*["\']([^"\']+)["\']', text)
    return m.group(1) if m else ""


def cmd_version_check(remote_version: str = ""):
    """
    检查本地 Skill 版本，与 clawhub.ai 上的远程版本对比。

    设计说明：
    远程版本需由调用方（小美）通过 WebFetch 访问 clawhub.ai 页面后，
    将解析到的版本字符串通过 --remote 参数传入。
    若未传入 --remote，则仅展示本地版本信息。
    """
    result = {
        "local_version": LOCAL_VERSION,
        "skill_page_url": SKILL_PAGE_URL,
    }

    remote_ver = remote_version.strip() if remote_version else ""

    if not remote_ver:
        # 未传入远程版本，仅展示本地版本
        result["remote_version"] = None
        result["up_to_date"] = None
        result["message"] = f"当前本地版本：{LOCAL_VERSION}"
        result["hint"] = f"如需检测最新版本，请访问：{SKILL_PAGE_URL}"
    elif remote_ver == LOCAL_VERSION:
        result["remote_version"] = remote_ver
        result["up_to_date"] = True
        result["message"] = f"✅ 当前已是最新版本 {LOCAL_VERSION}"
    else:
        result["remote_version"] = remote_ver
        result["up_to_date"] = False
        result["message"] = (
            f"⚠️ 发现新版本！本地：{LOCAL_VERSION}，最新：{remote_ver}。"
            f"建议前往以下地址更新以获取最新能力：{SKILL_PAGE_URL}"
        )
        result["upgrade_url"] = SKILL_PAGE_URL

    print(json.dumps(result, ensure_ascii=False))


# ── 设备ID生成 ────────────────────────────────────────────────────────

def generate_device_token(seed: str) -> str:
    """
    生成设备唯一标识（device_token）。
    算法：MD5（seed + 毫秒时间戳 + 0~1000随机整数）
    - 登录时（有完整手机号）：seed = 手机号
    - token-verify 时（无完整手机号）：seed = phone_masked（脱敏号）
    device_token 与设备绑定，一旦生成后永不覆盖。
    """
    ts_ms = int(time.time() * 1000)
    rand_int = random.randint(0, 1000)
    raw = f"{seed}{ts_ms}{rand_int}"
    return hashlib.md5(raw.encode("utf-8")).hexdigest()


# 注：存储操作函数已迁移到文件开头的"mt-ug-ods-skill-cache 集成配置"部分
# 保留此注释以便快速定位存储相关功能


# ── 命令：status（本地检查，不调用接口）────────────────────────────────

def cmd_status():
    """仅检查本地存储的 Token 是否存在，不调用远程接口，不做本地过期校验"""
    token_data = get_token_data()
    user_token = token_data.get("user_token")
    device_token = token_data.get("device_token")
    phone_masked = token_data.get("phone_masked", "")

    if user_token:
        print(json.dumps({
            "success": True,
            "valid": True,
            "user_token": user_token,
            "device_token": device_token,
            "phone_masked": phone_masked,
            "check_mode": "local"
        }, ensure_ascii=False))
    else:
        print(json.dumps({
            "success": True,
            "valid": False,
            "reason": "no_token",
            "device_token": device_token,
            "phone_masked": phone_masked,
            "check_mode": "local"
        }, ensure_ascii=False))


# ── 命令：token-verify（调用远程接口校验）─────────────────────────────

def cmd_token_verify():
    """调用 /eds/claw/login/token/verify 验证 Token 有效性"""
    import httpx

    token_data = get_token_data()
    user_token = token_data.get("user_token")
    phone_masked = token_data.get("phone_masked", "")

    if not user_token:
        # 无 token 时直接返回，不写入 device_token（避免覆盖已有数据）
        print(json.dumps({
            "success": True,
            "valid": False,
            "reason": "no_token",
            "phone_masked": phone_masked,
            "check_mode": "remote"
        }, ensure_ascii=False))
        return

    # 规则2：token-verify 时检查 device_token，不存在则用 phone_masked 生成并持久化
    # 注意：此逻辑必须在确认 user_token 存在后执行，避免在 no_token 情况下覆盖数据
    existing_device_token = token_data.get("device_token")
    if not existing_device_token:
        seed = phone_masked if phone_masked else "unknown"
        new_device_token = generate_device_token(seed)
        token_data["device_token"] = new_device_token
        save_token_data(token_data)
        existing_device_token = new_device_token

    url = BASE_URL + TOKEN_VERIFY_PATH
    try:
        resp = httpx.post(
            url,
            params={"token": user_token},
            headers={"Content-Type": "application/json"},
            timeout=10,
            verify=True
        )
        resp_data = resp.json()
        code = resp_data.get("code")

        if code == 0:
            # Token 有效
            print(json.dumps({
                "success": True,
                "valid": True,
                "user_token": user_token,
                "device_token": existing_device_token,
                "phone_masked": phone_masked,
                "check_mode": "remote"
            }, ensure_ascii=False))

        elif code == 20005:
            # Token 不存在或已过期（服务端确认）
            # 规则4：只将 user_token 置为空字符串，不删除 device_token
            logout_token_data()
            print(json.dumps({
                "success": True,
                "valid": False,
                "reason": "token_expired_or_invalid",
                "device_token": existing_device_token,
                "phone_masked": phone_masked,
                "check_mode": "remote",
                "message": resp_data.get("message", "用户未登录或 Token 已过期，请重新登录")
            }, ensure_ascii=False))

        else:
            # 其他错误（如系统繁忙），不修改本地缓存，降级为本地检查
            print(json.dumps({
                "success": False,
                "error": "TOKEN_VERIFY_ERROR",
                "code": code,
                "message": resp_data.get("message", "Token 校验失败"),
                "check_mode": "remote"
            }, ensure_ascii=False))
            sys.exit(1)

    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": "NETWORK_ERROR",
            "message": str(e)
        }, ensure_ascii=False))
        sys.exit(1)


# ── 命令：send-sms ────────────────────────────────────────────────────

def cmd_send_sms(phone: str):
    """调用 /eds/claw/login/sms/code/get 发送验证码"""
    import httpx

    # 读取已有 device_token，若不存在则先生成（此时还无法用手机号生成，用 phone 即可）
    existing = get_token_data()
    existing_dt = existing.get("device_token")
    if existing_dt:
        uuid_val = existing_dt
    else:
        uuid_val = generate_device_token(phone)
        # 提前持久化：send-sms 时即锁定 device_token，避免后续 verify 再生成不同值
        existing["device_token"] = uuid_val
        existing["phone_masked"] = phone[:3] + "****" + phone[-4:]
        save_token_data(existing)

    url = BASE_URL + SMS_CODE_GET_PATH
    body = {
        "mobile": phone,    # 接口字段名为 mobile
        "uuid": uuid_val    # 设备唯一标识，对接接口 uuid 扩展字段
    }

    try:
        resp = httpx.post(
            url,
            json=body,
            headers={"Content-Type": "application/json"},
            timeout=10,
            verify=True
        )
        resp_data = resp.json()
        code = resp_data.get("code")

        if code == 0:
            phone_masked = phone[:3] + "****" + phone[-4:]
            result = {
                "success": True,
                "phone_masked": phone_masked,
                "message": f"验证码已发送至手机号 {phone_masked}，请打开手机短信查看验证码，60秒内有效"
            }
            print(json.dumps(result, ensure_ascii=False))

        elif code == 20001:
            # 手机号 Token 加密服务失败，服务端问题，稍后重试
            print(json.dumps({
                "success": False,
                "error": "SMS_MOBILE_TOKEN_ENCRYPT_FAIL",
                "code": 20001,
                "message": "短信服务暂时不可用，请稍后重试"
            }, ensure_ascii=False))
            sys.exit(1)

        elif code == 20002:
            # 频控：验证码已存在
            print(json.dumps({
                "success": False,
                "error": "SMS_VERIFY_CODE_EXIST",
                "code": 20002,
                "message": "短信验证码已发送，请1分钟后再试"
            }, ensure_ascii=False))
            sys.exit(1)

        elif code == 20004:
            # 手机号未注册美团
            print(json.dumps({
                "success": False,
                "error": "CLAW_USER_NOT_REGISTERED",
                "code": 20004,
                "message": "该手机号未注册美团，请先下载美团APP并完成注册登录"
            }, ensure_ascii=False))
            sys.exit(1)

        elif code == 20006:
            # 单手机号日限（默认5次/天）
            print(json.dumps({
                "success": False,
                "error": "SMS_MOBILE_DAILY_LIMIT",
                "code": 20006,
                "message": "该手机号今日发送短信次数已达上限，请明天再试"
            }, ensure_ascii=False))
            sys.exit(1)

        elif code == 20007:
            # 全局日限（默认1000条/天）
            print(json.dumps({
                "success": False,
                "error": "SMS_DAILY_TOTAL_LIMIT",
                "code": 20007,
                "message": "短信发送总次数已达今日上限，请明天再试"
            }, ensure_ascii=False))
            sys.exit(1)

        elif code == 20010:
            # Rhino 限流触发，需用户完成安全验证，data.redirectUrl 为跳转链接
            data = resp_data.get("data") or {}
            redirect_url = data.get("redirectUrl", "")
            print(json.dumps({
                "success": False,
                "error": "SMS_SECURITY_VERIFY_REQUIRED",
                "code": 20010,
                "redirect_url": redirect_url,
                "message": (
                    "需要完成安全验证后才能接收短信验证码。"
                    f"请点击以下链接完成验证：{redirect_url}。"
                    "完成验证后，系统会自动发送短信验证码，请留意手机短信。"
                ) if redirect_url else "需要完成安全验证，请稍后重试"
            }, ensure_ascii=False))
            sys.exit(1)

        else:
            print(json.dumps({
                "success": False,
                "error": "SMS_SEND_FAILED",
                "code": code,
                "message": resp_data.get("message", "验证码发送失败")
            }, ensure_ascii=False))
            sys.exit(1)

    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": "NETWORK_ERROR",
            "message": str(e)
        }, ensure_ascii=False))
        sys.exit(1)


# ── 命令：verify ──────────────────────────────────────────────────────

def cmd_verify(phone: str, code: str):
    """调用 /eds/claw/login/sms/code/verify 验证验证码，成功后写入 user_token"""
    import httpx

    # 读取 device_token，此时 send-sms 应已持久化，直接复用
    existing = get_token_data()
    existing_dt = existing.get("device_token")
    if existing_dt:                                   # 规则5：存在且不为空则复用
        uuid_val = existing_dt
    else:                                             # 兜底：若未经 send-sms 直接调 verify
        uuid_val = generate_device_token(phone)
        existing["device_token"] = uuid_val
        save_token_data(existing)

    url = BASE_URL + SMS_CODE_VERIFY_PATH
    body = {
        "mobile": phone,            # 接口字段名为 mobile
        "smsVerifyCode": code,      # 接口字段名为 smsVerifyCode
        "uuid": uuid_val            # 设备唯一标识，对接接口 uuid 扩展字段
    }

    try:
        resp = httpx.post(
            url,
            json=body,
            headers={"Content-Type": "application/json"},
            timeout=10,
            verify=True
        )
        resp_data = resp.json()
        resp_code = resp_data.get("code")

        if resp_code == 0:
            # 成功，从 data.token 获取 Token
            data = resp_data.get("data") or {}
            user_token = data.get("token")
            if not user_token:
                print(json.dumps({
                    "success": False,
                    "error": "MISSING_TOKEN",
                    "message": "接口返回成功但 data.token 为空"
                }, ensure_ascii=False))
                sys.exit(1)

            phone_masked = phone[:3] + "****" + phone[-4:]

            # device_token：直接使用上方已确定的 uuid_val（send-sms 时已持久化，此处只做复用）
            # uuid_val 在本函数顶部已按"存在且不为空则复用，否则生成"的规则处理完毕
            device_token = uuid_val
            is_new_device = not bool(existing.get("device_token"))

            # 合并更新：保留已有字段（terms_accepted, cron_* 等），只更新认证相关字段
            token_data = get_token_data()  # 读取完整的现有数据
            token_data.update({
                "user_token": user_token,
                "device_token": device_token,
                "phone_masked": phone_masked,
                "authed_at": int(time.time())
            })
            save_token_data(token_data)

            result = {
                "success": True,
                "user_token": user_token,
                "device_token": device_token,
                "phone_masked": phone_masked,
                "message": "认证成功，user_token 已写入"
            }
            if is_new_device:
                result["device_token_generated"] = True
                result["hint"] = "首次认证，device_token 已生成并持久化"
            print(json.dumps(result, ensure_ascii=False))

        elif resp_code == 20003:
            print(json.dumps({
                "success": False,
                "error": "SMS_VERIFY_CODE_ERROR",
                "code": 20003,
                "message": "短信验证码错误或已过期，请重新获取"
            }, ensure_ascii=False))
            sys.exit(1)

        elif resp_code == 20004:
            print(json.dumps({
                "success": False,
                "error": "CLAW_USER_NOT_REGISTERED",
                "code": 20004,
                "message": "该手机号未注册美团，请先下载美团APP并完成注册登录"
            }, ensure_ascii=False))
            sys.exit(1)

        else:
            print(json.dumps({
                "success": False,
                "error": "VERIFY_FAILED",
                "code": resp_code,
                "message": resp_data.get("message", "验证失败，请重试")
            }, ensure_ascii=False))
            sys.exit(1)

    except Exception as e:
        print(json.dumps({
            "success": False,
            "error": "NETWORK_ERROR",
            "message": str(e)
        }, ensure_ascii=False))
        sys.exit(1)


# ── 命令：terms-check / terms-accept / terms-decline ──────────────────

def cmd_terms_check():
    """
    检查用户是否已接受服务协议

    首次使用时自动触发旧版文件迁移（如果新位置没有数据）
    """
    # 先触发旧版文件迁移（如果新位置没有数据）
    migration_result = _migrate_from_legacy_if_needed()

    accepted = get_terms_accepted()
    result = {
        "success": True,
        "terms_accepted": accepted,
        "message": "用户已接受服务协议" if accepted else "用户尚未接受服务协议"
    }

    # 如果发生了迁移，在返回结果中说明
    if migration_result.get("migrated"):
        result["migrated"] = True
        result["migration_source"] = migration_result.get("source")

    print(json.dumps(result, ensure_ascii=False))


def cmd_terms_accept():
    """用户接受服务协议"""
    set_terms_accepted(True)
    print(json.dumps({
        "success": True,
        "terms_accepted": True,
        "message": "已接受服务协议，可以继续使用"
    }, ensure_ascii=False))


def cmd_terms_decline():
    """用户拒绝服务协议"""
    set_terms_accepted(False)
    # 同时清除登录状态
    logout_token_data()
    print(json.dumps({
        "success": True,
        "terms_accepted": False,
        "message": "已拒绝服务协议，无法继续使用相关功能"
    }, ensure_ascii=False))


# ── 命令：logout ──────────────────────────────────────────────────────

def cmd_logout():
    """退出当前登录状态：仅将 user_token 置为空字符串，保留 device_token"""
    token_data = get_token_data()
    device_token = token_data.get("device_token")
    phone_masked = token_data.get("phone_masked", "")

    # 规则3+4：仅置空 user_token，device_token 保持不变
    logout_token_data()

    result = {
        "success": True,
        "message": "已退出登录，user_token 已清除，下次需重新验证登录",
        "device_token_preserved": bool(device_token),
        "phone_masked": phone_masked
    }
    print(json.dumps(result, ensure_ascii=False))


# ── 命令：clear-device-token ──────────────────────────────────────────

def cmd_clear_device_token():
    """清除设备标识（device_token），同时清除 user_token 和 phone_masked。
    仅在用户明确输入「清除设备标识」时调用，退出登录不触发此操作。
    """
    auth = load_auth()
    entry = auth.get(AUTH_KEY, {})

    had_device_token = bool(entry.get("device_token"))

    # 清除所有认证相关字段
    entry["user_token"] = ""
    entry["device_token"] = ""
    entry["phone_masked"] = ""
    auth[AUTH_KEY] = entry

    save_auth(auth)

    result = {
        "success": True,
        "message": "设备标识已清除，下次登录将生成新的 device_token",
        "device_token_cleared": had_device_token
    }
    print(json.dumps(result, ensure_ascii=False))


# ── 命令：定时任务管理 ─────────────────────────────────────────────────────────────

# 定时任务状态字段名
CRON_ENABLED_KEY = "cron_enabled"
CRON_TIME_KEY = "cron_time"
CRON_JOB_ID_KEY = "cron_job_id"  # 存储实际创建的 cron job ID（用于后续删除/修改）


def cmd_cron_status():
    """查询定时任务状态"""
    token_data = get_token_data()
    cron_enabled = token_data.get(CRON_ENABLED_KEY, False)
    cron_time = token_data.get(CRON_TIME_KEY, "")
    cron_job_id = token_data.get(CRON_JOB_ID_KEY, "")

    result = {
        "success": True,
        "cron_enabled": cron_enabled,
        "cron_time": cron_time if cron_enabled else None,
        "cron_job_id": cron_job_id if cron_enabled else None,
        "timezone": "Asia/Shanghai",
        "message": f"当前已设置每天 {cron_time} 自动领券（北京时间）" if cron_enabled else "暂未设置自动领券"
    }
    print(json.dumps(result, ensure_ascii=False))


def _detect_platform() -> str:
    """
    检测当前运行平台

    返回值:
        - "claude": Claude Desktop / Claude Code (支持 CronCreate)
        - "friday": Friday 广场 (支持 RemoteTrigger)
        - "clawhub": ClawHub (支持 claw cron)
        - "unknown": 未知平台
    """
    # 检测 Claude 环境
    if os.environ.get("CLAUDE_DESKTOP") or os.environ.get("CLAUDE_CODE"):
        return "claude"

    # 检测 Friday 广场
    if os.environ.get("FRIDAY_ENV") or os.environ.get("FRIDAY_SKILL_ID"):
        return "friday"

    # 检测 ClawHub
    if os.environ.get("CLAWHUB_ENV") or os.environ.get("OPENCLAW_AVAILABLE"):
        return "clawhub"

    # 默认检测 openclaw 命令是否存在
    try:
        result = subprocess.run(
            ["which", "openclaw"],
            capture_output=True,
            timeout=2
        )
        if result.returncode == 0:
            return "clawhub"
    except:
        pass

    return "unknown"


def _generate_cron_expression(hour: int, minute: int) -> str:
    """生成 cron 表达式

    Args:
        hour: 小时 (0-23)
        minute: 分钟 (0-59)

    返回:
        5字段 cron 表达式 (分 时 日 月 周)
    """
    return f"{minute} {hour} * * *"


def cmd_cron_set(time_str: str):
    """
    设置定时任务

    该命令为跨平台设计，根据检测到的平台返回对应的调度指令。
    调用方需根据返回的 platform 和 schedule_action 执行相应操作。

    Args:
        time_str: 时间字符串，格式 HH:MM（如 "10:00"）
    """
    import re

    # 验证时间格式
    if not re.match(r"^([0-1]?\d|2[0-3]):([0-5]\d)$", time_str):
        print(json.dumps({
            "success": False,
            "error": "INVALID_TIME_FORMAT",
            "message": "时间格式错误，请使用 HH:MM 格式（如 10:00、14:30）"
        }, ensure_ascii=False))
        sys.exit(1)

    # 标准化时间格式（补零）
    parts = time_str.split(":")
    hour = int(parts[0])
    minute = int(parts[1])
    normalized_time = f"{hour:02d}:{minute:02d}"

    # 保存本地状态
    token_data = get_token_data()
    token_data[CRON_ENABLED_KEY] = True
    token_data[CRON_TIME_KEY] = normalized_time
    save_token_data(token_data)

    # 检测平台并生成调度指令
    platform = _detect_platform()
    cron_expr = _generate_cron_expression(hour, minute)

    # 构建响应
    result = {
        "success": True,
        "cron_enabled": True,
        "cron_time": normalized_time,
        "platform": platform,
        "message": f"✅ 已设置每天 {normalized_time} 自动领券"
    }

    # 根据平台返回对应的调度动作
    if platform == "claude":
        result["schedule_action"] = "CronCreate"
        result["schedule_config"] = {
            "cron": cron_expr,
            "prompt": "执行 meituan-coupon-workbuddy Skill 帮用户自动领取美团红包，包括：1) 检查用户认证状态；2) 调用发券接口领取今日优惠券；3) 根据领券结果通知用户（成功或失败均需通知）。完成后请告诉用户领券结果。",
            "recurring": True,
            "durable": True
        }
    elif platform == "friday":
        result["schedule_action"] = "RemoteTrigger"
        result["schedule_config"] = {
            "trigger_name": f"meituan-coupon-daily-{normalized_time.replace(':', '')}",
            "schedule": cron_expr,
            "timezone": "Asia/Shanghai"
        }
    elif platform == "clawhub":
        result["schedule_action"] = "openclaw_cron"
        # 获取当前用户ID（优先从环境变量获取）
        user_id = os.environ.get("CLAWHUB_USER_ID") or os.environ.get("USER_ID") or "${USER_ID}"
        result["schedule_config"] = {
            "command": f"openclaw cron add --name '美团每日自动领券' --cron '{cron_expr}' --tz Asia/Shanghai --message '帮我领美团券，领完通知我' --channel daxiang --to user:{user_id} --announce --timeout-seconds 120 --session isolated",
            "notes": "Agent 需要从 inbound 上下文中获取 sender_id 替换 user_id 占位符"
        }
    else:
        # 未知平台，返回提示信息
        result["schedule_action"] = "manual"
        result["schedule_config"] = {
            "note": "未检测到支持的平台，请手动配置定时任务",
            "cron_expression": cron_expr,
            "suggested_command": f"请在支持的平台上创建每日 {normalized_time} 的定时任务"
        }
        result["message"] = f"✅ 已保存领券时间偏好 {normalized_time}，但未检测到自动调度平台，请手动配置定时任务"

    print(json.dumps(result, ensure_ascii=False))


def cmd_cron_disable():
    """取消定时任务"""
    token_data = get_token_data()

    token_data[CRON_ENABLED_KEY] = False
    # 保留 cron_time 字段作为历史记录，方便用户重新开启
    # 注意：cron_job_id 保留，用于 cron-status 查询历史记录
    save_token_data(token_data)

    print(json.dumps({
        "success": True,
        "cron_enabled": False,
        "message": "已关闭自动领券，需要时随时找我领券就行"
    }, ensure_ascii=False))


def cmd_cron_save_job_id(job_id: str, platform: str = ""):
    """
    保存平台返回的 cron job ID

    在平台成功创建定时任务后调用，保存 job ID 用于后续管理（如删除、修改）。

    Args:
        job_id: 平台返回的定时任务 ID（如 ClawHub 的 cron job ID）
        platform: 平台类型（可选，如 "clawhub", "friday", "claude"）
    """
    if not job_id:
        print(json.dumps({
            "success": False,
            "error": "MISSING_JOB_ID",
            "message": "job_id 不能为空"
        }, ensure_ascii=False))
        sys.exit(1)

    token_data = get_token_data()

    # 如果当前没有启用定时任务，给出警告但仍保存
    if not token_data.get(CRON_ENABLED_KEY, False):
        print(json.dumps({
            "success": False,
            "warning": "CRON_NOT_ENABLED",
            "message": "警告：定时任务未启用，但已保存 job_id。请先设置定时任务时间。"
        }, ensure_ascii=False))
        sys.exit(1)

    # 保存 job ID
    token_data[CRON_JOB_ID_KEY] = job_id
    save_token_data(token_data)

    result = {
        "success": True,
        "cron_job_id": job_id,
        "message": f"已保存定时任务 ID: {job_id}"
    }
    if platform:
        result["platform"] = platform

    print(json.dumps(result, ensure_ascii=False))


# ── 入口 ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="美团C端用户Agent认证工具")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # version-check
    p_vc = subparsers.add_parser("version-check", help="检查本地 Skill 版本，与远程广场版本对比")
    p_vc.add_argument("--remote", default="", help="从 Friday 广场获取到的远程版本号（可选）")

    # status - 本地检查
    subparsers.add_parser("status", help="本地检查 Token 是否存在")

    # token-verify - 远程校验
    subparsers.add_parser("token-verify", help="调用远程接口校验 Token 有效性")

    # send-sms
    p_sms = subparsers.add_parser("send-sms", help="发送短信验证码")
    p_sms.add_argument("--phone", required=True, help="手机号（11位）")

    # verify
    p_verify = subparsers.add_parser("verify", help="验证码核验并写入 Token")
    p_verify.add_argument("--phone", required=True, help="手机号（11位）")
    p_verify.add_argument("--code", required=True, help="6位短信验证码")

    # logout
    subparsers.add_parser("logout", help="退出登录，清除 user_token")

    # terms-check - 检查协议状态
    subparsers.add_parser("terms-check", help="检查用户是否已接受服务协议")

    # terms-accept - 接受协议
    subparsers.add_parser("terms-accept", help="接受服务协议")

    # terms-decline - 拒绝协议
    subparsers.add_parser("terms-decline", help="拒绝服务协议")

    # clear-device-token
    subparsers.add_parser("clear-device-token", help="清除设备标识（device_token），仅在用户明确要求时调用")

    # cron-status - 查询定时任务状态
    subparsers.add_parser("cron-status", help="查询定时自动领券状态")

    # cron-set - 设置定时任务
    p_cron_set = subparsers.add_parser("cron-set", help="设置每天定时自动领券时间")
    p_cron_set.add_argument("--time", required=True, help="时间，格式 HH:MM（如 10:00、21:30）")

    # cron-disable - 取消定时任务
    subparsers.add_parser("cron-disable", help="取消定时自动领券")

    # cron-save-job-id - 保存定时任务 ID（平台创建任务后调用）
    p_cron_save = subparsers.add_parser("cron-save-job-id", help="保存平台返回的定时任务 ID")
    p_cron_save.add_argument("--job-id", required=True, help="平台返回的定时任务 ID")
    p_cron_save.add_argument("--platform", default="", help="平台类型（可选，如 clawhub, friday, claude）")

    args = parser.parse_args()

    if args.command == "version-check":
        cmd_version_check(args.remote)
    elif args.command == "status":
        cmd_status()
    elif args.command == "token-verify":
        cmd_token_verify()
    elif args.command == "send-sms":
        cmd_send_sms(args.phone)
    elif args.command == "verify":
        cmd_verify(args.phone, args.code)
    elif args.command == "logout":
        cmd_logout()
    elif args.command == "terms-check":
        cmd_terms_check()
    elif args.command == "terms-accept":
        cmd_terms_accept()
    elif args.command == "terms-decline":
        cmd_terms_decline()
    elif args.command == "clear-device-token":
        cmd_clear_device_token()
    elif args.command == "cron-status":
        cmd_cron_status()
    elif args.command == "cron-set":
        cmd_cron_set(args.time)
    elif args.command == "cron-disable":
        cmd_cron_disable()
    elif args.command == "cron-save-job-id":
        cmd_cron_save_job_id(args.job_id, args.platform)


if __name__ == "__main__":
    main()
