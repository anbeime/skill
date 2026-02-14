# ~/.claude/skills/x-article-publisher/scripts/site_config.py
r"""
==============================================================================
X (Twitter) 站点配置 - Site Configuration for X Authentication
==============================================================================

PURPOSE:
  定义 X (Twitter) 的认证验证策略，使用共享浏览器认证框架

VALIDATION STRATEGY:
  1. URL 正则匹配 "^https://x\.com/home" (精确检查登录后跳转)
  2. DOM 元素 "nav[aria-label='Primary']" 存在 (主导航验证)

CRITICAL:
  X 对自动化检测敏感，使用真实 Chrome + 浏览器指纹保持一致性

ARCHITECTURE:
  Config-driven validation → BrowserAuthManager → Persistent authentication
"""

import sys
from pathlib import Path

# ============================================================================
# PATH CONFIGURATION - 使用skill内部的browser_auth库
# ============================================================================
SKILL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_DIR / "lib"))

from browser_auth import SiteConfig

# ============================================================================
# X (TWITTER) CONFIGURATION
# ============================================================================
X_TWITTER_CONFIG = SiteConfig(
    site_name="x-twitter",
    login_url="https://x.com/i/flow/login",

    # 验证策略：登录成功后跳转到 Home 时间线
    success_indicators={
        "url_pattern": r"^https://x\.com/home",              # 精确 URL 匹配
        "element_exists": "nav[aria-label='Primary']"        # 主导航元素验证
    },

    login_timeout_minutes=10  # 登录超时时间（包括 2FA 验证）
)
