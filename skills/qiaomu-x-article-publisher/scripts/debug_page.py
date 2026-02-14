#!/usr/bin/env python3
"""调试脚本 - 查看 X Articles 页面结构"""

import sys
import time
from pathlib import Path

from patchright.sync_api import sync_playwright

SKILL_DIR = Path(__file__).parent.parent
BROWSER_STATE_DIR = SKILL_DIR / "data" / "browser_state"
BROWSER_PROFILE_DIR = BROWSER_STATE_DIR / "browser_profile"
STATE_FILE = BROWSER_STATE_DIR / "state.json"

sys.path.insert(0, str(SKILL_DIR / "lib"))
from browser_auth import BrowserFactory

def main():
    print("🔍 调试 X Articles 页面...")

    playwright = sync_playwright().start()

    context = BrowserFactory.launch_persistent_context(
        playwright,
        user_data_dir=BROWSER_PROFILE_DIR,
        state_file=STATE_FILE,
        headless=False  # 显示浏览器
    )

    page = context.new_page()

    # 导航到 Articles
    print("📍 导航到 X Articles...")
    page.goto("https://x.com/compose/articles", wait_until="domcontentloaded")
    time.sleep(3)

    # 截图
    screenshot_path = "/tmp/x_articles_debug.png"
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"📸 截图已保存: {screenshot_path}")

    # 打印页面标题和URL
    print(f"📄 页面标题: {page.title()}")
    print(f"🔗 当前URL: {page.url}")

    # 查找所有按钮
    print("\n🔘 页面上的按钮:")
    buttons = page.query_selector_all("button")
    for i, btn in enumerate(buttons[:20]):  # 只打印前20个
        text = btn.inner_text().strip()[:50] if btn.inner_text() else ""
        print(f"  [{i}] {text}")

    # 查找所有链接
    print("\n🔗 页面上的链接:")
    links = page.query_selector_all("a")
    for i, link in enumerate(links[:20]):
        text = link.inner_text().strip()[:50] if link.inner_text() else ""
        href = link.get_attribute("href") or ""
        print(f"  [{i}] {text} -> {href[:50]}")

    # 查找可能的"create"相关元素
    print("\n🔍 查找 'create' 相关元素:")
    create_elements = page.query_selector_all("[data-testid*='create'], [aria-label*='create'], button:has-text('create'), a:has-text('create')")
    for elem in create_elements:
        print(f"  找到: {elem.inner_text()[:50]}")

    # 等待用户查看
    print("\n⏳ 浏览器将在 60 秒后关闭...")
    time.sleep(60)

    context.close()
    playwright.stop()

if __name__ == "__main__":
    main()
