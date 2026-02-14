#!/usr/bin/env python3
"""调试编辑器页面结构"""

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
    print("🔍 调试 X Articles 编辑器...")

    playwright = sync_playwright().start()

    context = BrowserFactory.launch_persistent_context(
        playwright,
        user_data_dir=BROWSER_PROFILE_DIR,
        state_file=STATE_FILE,
        headless=False
    )

    page = context.new_page()

    # 先导航到文章列表页
    print("📍 导航到文章列表页...")
    page.goto("https://x.com/compose/articles", wait_until="domcontentloaded")
    time.sleep(5)

    # 查找并点击右上角的"新建文章"按钮（羽毛笔图标）
    print("🔍 查找新建文章按钮...")

    # 尝试多种选择器找到这个按钮
    create_selectors = [
        'a[href="/compose/articles/new"]',  # 直接链接
        'button[aria-label*="新建"]',
        'button[aria-label*="撰写"]',
        'button[aria-label*="Create"]',
        'button[aria-label*="Compose"]',
        '[data-testid="createArticle"]',
        '[data-testid="newArticle"]',
        'svg[aria-label*="新建"]',
    ]

    for selector in create_selectors:
        try:
            elem = page.query_selector(selector)
            if elem:
                print(f"  ✅ 找到: {selector}")
                elem.click()
                time.sleep(3)
                break
        except:
            pass
    else:
        # 如果没找到，尝试用位置查找（右上角区域的按钮）
        print("  ⚠️  未通过选择器找到，尝试查找页面上所有可点击元素...")

        # 打印所有 a 标签
        links = page.query_selector_all("a")
        print(f"\n  📎 所有链接 ({len(links)}):")
        for i, link in enumerate(links[:30]):
            href = link.get_attribute("href") or ""
            text = link.inner_text().strip()[:30] if link.inner_text() else ""
            aria = link.get_attribute("aria-label") or ""
            if "article" in href.lower() or "compose" in href.lower():
                print(f"    [{i}] href='{href}' text='{text}' aria='{aria}'")

        # 打印所有按钮
        buttons = page.query_selector_all("button")
        print(f"\n  🔘 所有按钮 ({len(buttons)}):")
        for i, btn in enumerate(buttons[:20]):
            aria = btn.get_attribute("aria-label") or ""
            text = btn.inner_text().strip()[:30] if btn.inner_text() else ""
            testid = btn.get_attribute("data-testid") or ""
            print(f"    [{i}] aria='{aria}' text='{text}' testid='{testid}'")

    print("  等待编辑器加载...")
    time.sleep(5)

    # 截图
    screenshot_path = "/tmp/x_editor_debug.png"
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"📸 截图已保存: {screenshot_path}")

    print(f"🔗 当前URL: {page.url}")

    # 查找输入框
    print("\n📝 查找输入框:")
    inputs = page.query_selector_all("input, textarea, [contenteditable='true']")
    for i, inp in enumerate(inputs[:15]):
        placeholder = inp.get_attribute("placeholder") or ""
        tag = inp.evaluate("el => el.tagName")
        print(f"  [{i}] <{tag}> placeholder='{placeholder[:30]}'")

    # 查找所有 contenteditable 元素
    print("\n✏️  contenteditable 元素:")
    editables = page.query_selector_all("[contenteditable='true']")
    for i, ed in enumerate(editables[:10]):
        text = ed.inner_text()[:50] if ed.inner_text() else ""
        print(f"  [{i}] '{text}'")

    # 查找按钮
    print("\n🔘 按钮:")
    buttons = page.query_selector_all("button")
    for i, btn in enumerate(buttons[:15]):
        text = btn.inner_text().strip()[:30] if btn.inner_text() else ""
        if text:
            print(f"  [{i}] {text}")

    # 检查页面 HTML 结构
    print("\n📄 主内容区域:")
    main_content = page.query_selector('main, [role="main"], [data-testid="primaryColumn"]')
    if main_content:
        html = main_content.inner_html()[:500]
        print(f"  内容: {html[:200]}...")
    else:
        print("  未找到 main 内容区域")

    # 检查是否有弹窗或 modal
    print("\n🪟 弹窗/Modal:")
    modals = page.query_selector_all('[role="dialog"], [aria-modal="true"], .modal')
    for i, modal in enumerate(modals[:5]):
        text = modal.inner_text()[:100] if modal.inner_text() else ""
        print(f"  [{i}] {text}")

    # 检查所有文本内容
    print("\n📝 页面可见文本:")
    body_text = page.inner_text("body")[:500]
    print(f"  {body_text}")

    print("\n⏳ 浏览器将在 60 秒后关闭...")
    time.sleep(60)

    context.close()
    playwright.stop()

if __name__ == "__main__":
    main()
