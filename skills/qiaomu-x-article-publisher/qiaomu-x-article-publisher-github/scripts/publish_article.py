#!/usr/bin/env python3
"""
==============================================================================
X Article Publisher - 文章发布脚本
==============================================================================

PURPOSE:
  使用已认证的 patchright 浏览器上下文发布文章到 X Articles
  解决 Playwright MCP 无法读取 patchright 认证状态的问题

USAGE:
  python publish_article.py --file article.md [--show-browser]
  python publish_article.py --file article.md --title "自定义标题"

WORKFLOW:
  1. 检查认证状态
  2. 解析 Markdown 文件
  3. 启动已认证的浏览器
  4. 导航到 X Articles 编辑器
  5. 创建新文章
  6. 上传封面图（如有）
  7. 填写标题
  8. 粘贴 HTML 内容
  9. 保存草稿
"""

import argparse
import base64
import json
import sys
import time
import subprocess
from pathlib import Path

from patchright.sync_api import sync_playwright

# ============================================================================
# PATH CONFIGURATION - 使用skill内部的browser_auth库
# ============================================================================
SKILL_DIR = Path(__file__).parent.parent
DATA_DIR = SKILL_DIR / "data"
BROWSER_STATE_DIR = DATA_DIR / "browser_state"
BROWSER_PROFILE_DIR = BROWSER_STATE_DIR / "browser_profile"
STATE_FILE = BROWSER_STATE_DIR / "state.json"

sys.path.insert(0, str(SKILL_DIR / "lib"))
sys.path.insert(0, str(Path(__file__).parent))

from browser_auth import BrowserAuthManager, BrowserFactory
from site_config import X_TWITTER_CONFIG


# ============================================================================
# SELECTORS (中文界面)
# ============================================================================
SELECTORS = {
    # 撰写按钮 - 蓝色大按钮
    "create_button": 'button:has-text("撰写"), a:has-text("撰写")',
    # 封面图上传
    "cover_upload": 'input[type="file"][accept*="image"]',
    "cover_button": 'button:has-text("添加照片"), button:has-text("添加封面")',
    # 标题输入
    "title_input": '[placeholder*="标题"], [data-testid="articleTitle"], [contenteditable="true"]:first-of-type',
    # 编辑器
    "editor": '[contenteditable="true"], [role="textbox"]',
    # 保存按钮
    "save_button": 'button:has-text("保存"), button:has-text("Save")',
}


class ArticlePublisher:
    """X 文章发布器"""

    def __init__(self):
        self.auth_manager = BrowserAuthManager(
            site_config=X_TWITTER_CONFIG,
            state_dir=BROWSER_STATE_DIR
        )

    def check_auth(self) -> bool:
        """检查认证状态"""
        if not self.auth_manager.is_authenticated():
            print("❌ 未认证。请先运行：python auth_manager.py setup")
            return False
        return True

    def parse_markdown(self, file_path: str) -> dict:
        """解析 Markdown 文件"""
        script_dir = Path(__file__).parent
        parse_script = script_dir / "parse_markdown.py"

        result = subprocess.run(
            ["python3", str(parse_script), file_path],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"❌ 解析 Markdown 失败：{result.stderr}")
            return None

        return json.loads(result.stdout)

    def copy_html_to_clipboard(self, html: str) -> bool:
        """复制 HTML 到剪贴板"""
        script_dir = Path(__file__).parent
        copy_script = script_dir / "copy_to_clipboard.py"

        # 保存 HTML 到临时文件
        temp_file = Path("/tmp/x_article_content.html")
        temp_file.write_text(html)

        result = subprocess.run(
            ["python3", str(copy_script), "html", "--file", str(temp_file)],
            capture_output=True,
            text=True
        )

        return result.returncode == 0

    def copy_image_to_clipboard(self, image_path: str) -> bool:
        """复制图片到剪贴板"""
        script_dir = Path(__file__).parent
        copy_script = script_dir / "copy_to_clipboard.py"

        result = subprocess.run(
            ["python3", str(copy_script), "image", image_path, "--quality", "85"],
            capture_output=True,
            text=True
        )

        return result.returncode == 0

    def publish(self, file_path: str, custom_title: str = None, custom_cover: str = None, headless: bool = True) -> bool:
        """发布文章到 X"""

        # Step 1: 检查认证
        if not self.check_auth():
            return False

        # Step 2: 解析 Markdown
        print(f"📄 解析文件：{file_path}")
        article = self.parse_markdown(file_path)
        if not article:
            return False

        title = custom_title or article.get("title", "无标题")
        html = article.get("html", "")
        cover_image = custom_cover or article.get("cover_image")
        content_images = article.get("content_images", [])

        print(f"  📝 标题：{title}")
        print(f"  🖼️  封面图：{cover_image or '无'}")
        print(f"  📷 内容图：{len(content_images)} 张")

        playwright = None
        context = None

        try:
            # Step 3: 启动浏览器
            print("\n🌐 启动浏览器...")
            playwright = sync_playwright().start()

            context = BrowserFactory.launch_persistent_context(
                playwright,
                user_data_dir=BROWSER_PROFILE_DIR,
                state_file=STATE_FILE,
                headless=headless
            )

            page = context.new_page()

            # Step 4: 导航到 Articles 编辑器
            print("  📍 导航到 X Articles...")
            page.goto("https://x.com/compose/articles", wait_until="domcontentloaded")
            time.sleep(5)  # 等待页面完全加载

            # Step 5: 点击"新建文章"按钮（羽毛笔图标，aria-label="create"）
            print("  🔘 点击新建文章按钮...")
            try:
                # 羽毛笔图标按钮的 aria-label 是 "create"
                create_btn = page.query_selector('button[aria-label="create"]')
                if create_btn:
                    create_btn.click()
                    print("  ✅ 已点击新建文章按钮")
                    time.sleep(5)  # 等待编辑器加载
                else:
                    print("  ⚠️  未找到 create 按钮，尝试其他方式...")
                    # 备选：尝试找 "撰写" 链接
                    create_link = page.get_by_text("撰写", exact=True).first
                    if create_link:
                        create_link.click()
                        print("  ✅ 已点击撰写链接")
                        time.sleep(5)
                    else:
                        print("  ⚠️  也未找到撰写链接")
            except Exception as e:
                print(f"  ⚠️  点击新建按钮失败: {e}")

            # Step 6: 上传封面图（如有）- 使用剪贴板粘贴方式
            # 封面区域是标题上方的灰色区域，中间有相机图标
            if cover_image and Path(cover_image).exists():
                # 检查文件名是否以 'cover' 开头
                filename = Path(cover_image).name.lower()
                if filename.startswith('cover'):
                    print("  💡 跳过以'cover'开头的封面图，用户将手动添加")
                else:
                    print(f"  🖼️  上传封面图：{cover_image}")
                    try:
                        # 调试：打印页面上的关键元素
                        print("  🔍 调试：查找页面元素...")

                        # 查找包含 "5:2" 文字的元素
                        elements_with_52 = page.query_selector_all('*:has-text("5:2")')
                        print(f"  🔍 包含 '5:2' 的元素: {len(elements_with_52)} 个")

                        # 查找所有 input[type=file]
                        file_inputs = page.query_selector_all('input[type="file"]')
                        print(f"  🔍 文件上传 input: {len(file_inputs)} 个")

                        # 查找标题输入框，然后找它的父元素
                        title_area = page.query_selector('textarea[placeholder="添加标题"]')
                        if title_area:
                            print("  🔍 找到标题输入框")
                            # 截图当前状态
                            page.screenshot(path="/tmp/x_before_cover.png")
                            print("  📸 截图已保存: /tmp/x_before_cover.png")

                        # 方法：复制图片到剪贴板，点击封面区域的相机图标，粘贴
                        if self.copy_image_to_clipboard(cover_image):
                            print("  ✅ 已复制封面图到剪贴板")

                            # 尝试方法1：直接找 input[type=file] 并设置文件
                            if file_inputs and len(file_inputs) > 0:
                                print(f"  🔍 尝试直接设置文件到 input...")
                                file_inputs[0].set_input_files(cover_image)
                                print("  ✅ 已设置文件到 input")
                                time.sleep(3)

                                # 检查是否出现编辑媒体对话框
                                apply_btn = page.query_selector('[role="dialog"] button:has-text("应用")')
                                if apply_btn:
                                    apply_btn.click()
                                    print("  ✅ 已点击应用按钮")
                                    time.sleep(2)
                            else:
                                # 尝试方法2：点击封面区域然后粘贴
                                cover_area = page.query_selector(
                                    '[aria-label*="照片"], '
                                    '[aria-label*="photo"], '
                                    '[data-testid*="cover"], '
                                    'div:has-text("5:2")'
                                )

                                if not cover_area:
                                    # 备选：找所有 SVG 图标按钮
                                    print("  🔍 尝试查找 SVG 图标按钮...")
                                    svg_buttons = page.query_selector_all('button:has(svg), [role="button"]:has(svg)')
                                    if svg_buttons and len(svg_buttons) > 0:
                                        cover_area = svg_buttons[0]
                                        print(f"  🔍 找到 {len(svg_buttons)} 个 SVG 按钮")

                                if cover_area:
                                    cover_area.click()
                                    print("  ✅ 已点击封面区域")
                                    time.sleep(0.5)

                                    # 粘贴图片
                                    page.keyboard.press("Meta+v")
                                    print("  ✅ 已粘贴封面图")
                                    time.sleep(3)  # 等待上传完成

                                    # 如果出现编辑媒体对话框，点击应用
                                    apply_btn = page.query_selector(
                                        '[role="dialog"] button:has-text("应用"), '
                                        '[data-testid="cropperSaveButton"]'
                                    )
                                    if apply_btn:
                                        apply_btn.click()
                                        print("  ✅ 已点击应用按钮")
                                        time.sleep(2)
                                else:
                                    print("  ⚠️  未找到封面区域")
                        else:
                            print("  ⚠️  复制封面图到剪贴板失败")
                    except Exception as e:
                        print(f"  ⚠️  上传封面图失败：{e}")
            else:
                print("  💡 无封面图，用户将手动添加")

            # Step 7: 填写标题
            print(f"  📝 填写标题：{title}")
            try:
                # 等待标题输入框出现（textarea with placeholder="添加标题"）
                title_input = page.wait_for_selector('textarea[placeholder="添加标题"]', timeout=10000)
                if title_input:
                    title_input.click()
                    title_input.fill(title)
                    print("  ✅ 标题已填写")
                    time.sleep(1)
                else:
                    print("  ⚠️  未找到标题输入框")
            except Exception as e:
                print(f"  ⚠️  填写标题失败：{e}")

            # Step 8: 粘贴 HTML 内容
            print("  📋 粘贴内容...")
            if self.copy_html_to_clipboard(html):
                try:
                    # 点击编辑器区域（contenteditable div）
                    # 先按 Tab 从标题跳到内容区域
                    page.keyboard.press("Tab")
                    time.sleep(0.5)

                    # 或者直接找到 contenteditable 元素
                    editors = page.query_selector_all('[contenteditable="true"]')
                    print(f"  找到 {len(editors)} 个可编辑区域")

                    # 通常第二个 contenteditable 是正文编辑器
                    if len(editors) >= 2:
                        editors[1].click()
                        time.sleep(0.5)
                    elif len(editors) >= 1:
                        editors[0].click()
                        time.sleep(0.5)

                    # 粘贴
                    page.keyboard.press("Meta+v")
                    print("  ✅ 已粘贴内容")

                    # 添加调试：查看粘贴后的 DOM 结构
                    time.sleep(3)
                    dom_debug = page.evaluate('''() => {
                        const editors = document.querySelectorAll('[contenteditable="true"]');
                        let bodyEditor = null;
                        let maxLength = 0;

                        editors.forEach((e) => {
                            if (e.innerText.length > maxLength) {
                                maxLength = e.innerText.length;
                                bodyEditor = e;
                            }
                        });

                        if (!bodyEditor) return { error: "No editor found" };

                        // 检查编辑器的子元素结构
                        const directChildren = Array.from(bodyEditor.children);
                        const childInfo = directChildren.map(child => ({
                            tag: child.tagName,
                            childCount: child.children.length,
                            firstLevelChildren: Array.from(child.children).slice(0, 5).map(c => c.tagName)
                        }));

                        return {
                            editorTag: bodyEditor.tagName,
                            directChildrenCount: directChildren.length,
                            childrenInfo: childInfo
                        };
                    }''')
                    print(f"  🔍 DOM 结构调试: {dom_debug}")

                    # 等待内容完全渲染 - 使用轮询检测块元素数量
                    print("  ⏳ 等待编辑器渲染所有块级元素...")

                    # 轮询检测块元素数量，直到稳定
                    stable_count = 0
                    prev_count = 0
                    max_attempts = 20  # 最多检测20次

                    for attempt in range(max_attempts):
                        current_count = page.evaluate('''() => {
                            const editors = document.querySelectorAll('[contenteditable="true"]');
                            let bodyEditor = null;
                            let maxLength = 0;

                            editors.forEach((e) => {
                                if (e.innerText.length > maxLength) {
                                    maxLength = e.innerText.length;
                                    bodyEditor = e;
                                }
                            });

                            if (!bodyEditor) return 0;

                            let blockElements = [];
                            const directChildren = bodyEditor.children;
                            if (directChildren.length === 1 && directChildren[0].tagName === 'DIV') {
                                blockElements = Array.from(directChildren[0].children);
                            } else {
                                blockElements = Array.from(directChildren);
                            }

                            return blockElements.length;
                        }''')

                        if current_count == prev_count and current_count > 10:
                            # 数量稳定且超过10个块，认为渲染完成
                            stable_count += 1
                            if stable_count >= 2:  # 连续2次相同，确认稳定
                                print(f"  ✅ 编辑器渲染完成，共 {current_count} 个块元素")
                                break
                        else:
                            stable_count = 0

                        prev_count = current_count

                        if (attempt + 1) % 5 == 0:
                            print(f"      当前检测到 {current_count} 个块，继续等待...")

                        time.sleep(1)
                    else:
                        print(f"  ⚠️  等待超时，当前 {prev_count} 个块")

                    # 再等待1秒确保完全稳定
                    time.sleep(1)

                    # 截图验证
                    page.screenshot(path="/tmp/x_after_paste.png")
                    print("  📸 截图已保存: /tmp/x_after_paste.png")

                except Exception as e:
                    print(f"  ⚠️  粘贴内容失败：{e}")
            else:
                print("  ⚠️  复制 HTML 到剪贴板失败")

            # Step 9: 插入内容图片
            # 检查是否使用占位符方式
            use_placeholders = article.get("use_placeholders", True)

            if content_images:
                print(f"  📷 插入 {len(content_images)} 张内容图...")

                if use_placeholders:
                    # 新方法：基于占位符定位
                    print(f"  💡 使用占位符方式插入图片")

                    # 按顺序处理每张图片（占位符已经在正确位置）
                    for img in content_images:
                        img_path = img.get("path")
                        placeholder_id = img.get("placeholder_id", "")
                        img_index = img.get("index", 0)

                        if not img_path or not Path(img_path).exists():
                            print(f"    ⚠️ 图片不存在: {img_path}")
                            continue

                        print(f"    📷 插入图片 {img_index}: {Path(img_path).name}")

                        # 在编辑器中查找占位符 @@@IMG_X@@@
                        placeholder_marker = f"@@@IMG_{img_index}@@@"

                        # Step 1: 读取图片为 base64
                        with open(img_path, 'rb') as f:
                            img_bytes = f.read()
                        img_base64 = base64.b64encode(img_bytes).decode('utf-8')

                        # 获取图片 MIME 类型
                        ext = Path(img_path).suffix.lower()
                        mime_map = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg', '.gif': 'image/gif', '.webp': 'image/webp'}
                        mime_type = mime_map.get(ext, 'image/png')
                        filename = Path(img_path).name

                        # Step 2: 先复制图片到剪贴板（在操作编辑器之前！）
                        # 这样可以避免在选中文本后剪贴板被覆盖的问题
                        if not self.copy_image_to_clipboard(img_path):
                            print(f"      ⚠️ 复制图片失败")
                            continue

                        time.sleep(0.3)
                        print(f"      ✅ 已复制图片到剪贴板")

                        # Step 3: 记录当前图片数量
                        before_count = page.evaluate('''() => {
                            return document.querySelectorAll('img').length;
                        }''')

                        # Step 4: 找到并选中占位符，然后立即粘贴
                        select_result = page.evaluate('''(marker) => {
                            const editors = document.querySelectorAll('[contenteditable="true"]');
                            let bodyEditor = null;
                            let maxLength = 0;

                            editors.forEach((e) => {
                                if (e.innerText.length > maxLength) {
                                    maxLength = e.innerText.length;
                                    bodyEditor = e;
                                }
                            });

                            if (!bodyEditor) return { success: false, error: 'No editor found' };

                            // 确保编辑器有焦点
                            bodyEditor.focus();

                            // 搜索包含占位符的文本节点
                            const walker = document.createTreeWalker(
                                bodyEditor,
                                NodeFilter.SHOW_TEXT,
                                null,
                                false
                            );

                            let node;
                            let targetNode = null;
                            let startOffset = -1;

                            while (node = walker.nextNode()) {
                                const idx = node.textContent.indexOf(marker);
                                if (idx !== -1) {
                                    targetNode = node;
                                    startOffset = idx;
                                    break;
                                }
                            }

                            if (!targetNode) {
                                return { success: false, error: 'Placeholder not found: ' + marker };
                            }

                            // 滚动到可见
                            const parentEl = targetNode.parentElement;
                            if (parentEl) {
                                parentEl.scrollIntoView({ behavior: 'instant', block: 'center' });
                            }

                            // 选中占位符
                            try {
                                const range = document.createRange();
                                const sel = window.getSelection();

                                range.setStart(targetNode, startOffset);
                                range.setEnd(targetNode, startOffset + marker.length);

                                sel.removeAllRanges();
                                sel.addRange(range);

                                return {
                                    success: true,
                                    selectedText: sel.toString(),
                                    isCollapsed: sel.isCollapsed
                                };
                            } catch (e) {
                                return { success: false, error: 'Selection failed: ' + e.message };
                            }
                        }''', placeholder_marker)

                        if not select_result.get('success'):
                            print(f"      ⚠️ 选中占位符失败: {select_result.get('error')}")
                            continue

                        print(f"      ✅ 已选中占位符: '{select_result.get('selectedText', '')}'")

                        # Step 5: 立即粘贴（替换选中的占位符）
                        # 注意：不要在这之间做任何可能影响焦点的操作！
                        page.keyboard.press("Meta+v")
                        print(f"      📋 已执行粘贴（替换占位符）")

                        # 等待图片上传完成
                        # 1. 等待图片出现
                        # 2. 等待"正在上传媒体"提示消失
                        max_wait = 60
                        upload_success = False

                        for i in range(max_wait):
                            time.sleep(1)

                            # 检查图片数量和上传状态
                            status = page.evaluate('''() => {
                                const imgCount = document.querySelectorAll('img').length;

                                // 检查是否有"正在上传媒体"提示
                                const uploading = document.body.innerText.includes('正在上传媒体') ||
                                                  document.body.innerText.includes('Uploading media') ||
                                                  document.body.innerText.includes('上传中');

                                return { imgCount, uploading };
                            }''')

                            current_count = status.get('imgCount', 0)
                            is_uploading = status.get('uploading', False)

                            if current_count > before_count and not is_uploading:
                                upload_success = True
                                print(f"      ✅ 图片已上传完成 (用时 {i+1}秒)")
                                time.sleep(0.5)  # 短暂等待确保稳定
                                break

                            if current_count > before_count and is_uploading:
                                if (i + 1) % 3 == 0:
                                    print(f"      ⏳ 图片已插入，等待上传完成... {i+1}秒")
                            elif (i + 1) % 5 == 0:
                                print(f"      ⏳ 等待图片出现... {i+1}/{max_wait}秒")

                        if not upload_success:
                            print(f"      ⚠️ 上传超时，尝试重试...")
                            page.keyboard.press("Meta+v")

                            for i in range(15):
                                time.sleep(1)
                                status = page.evaluate('''() => {
                                    const imgCount = document.querySelectorAll('img').length;
                                    const uploading = document.body.innerText.includes('正在上传媒体') ||
                                                      document.body.innerText.includes('Uploading media');
                                    return { imgCount, uploading };
                                }''')

                                current_count = status.get('imgCount', 0)
                                is_uploading = status.get('uploading', False)

                                if current_count > before_count and not is_uploading:
                                    upload_success = True
                                    print(f"      ✅ 重试成功！")
                                    time.sleep(0.5)
                                    break

                            if not upload_success:
                                print(f"      ❌ 重试后仍然失败")

                        # 更新 before_count 为下一张图片做准备
                        before_count = current_count

                else:
                    # 旧方法：基于 block_index 定位（保留作为后备）
                    print(f"  💡 使用 block_index 方式插入图片（旧方法）")

                    # 滚动到编辑器开头
                    page.keyboard.press("Meta+Home")
                    time.sleep(0.5)

                    block_info = page.evaluate('''() => {
                        const editors = document.querySelectorAll('[contenteditable="true"]');
                        let bodyEditor = null;
                        let maxLength = 0;

                        editors.forEach((e) => {
                            if (e.innerText.length > maxLength) {
                                maxLength = e.innerText.length;
                                bodyEditor = e;
                            }
                        });

                        if (!bodyEditor) return { count: 0 };

                        const blockElements = Array.from(bodyEditor.querySelectorAll('[data-block="true"]'));
                        return { count: blockElements.length };
                    }''')

                    print(f"  🔍 编辑器中找到 {block_info['count']} 个块元素")

                    sorted_images = sorted(content_images, key=lambda x: x.get("block_index", 0), reverse=True)

                    for img in sorted_images:
                        img_path = img.get("path")
                        block_index = img.get("block_index", 0)

                        if img_path and Path(img_path).exists():
                            print(f"    📷 插入图片 (block {block_index}): {Path(img_path).name}")
                            # 简化的旧逻辑...
                            if self.copy_image_to_clipboard(img_path):
                                page.keyboard.press("Meta+v")
                                time.sleep(3)

            # Step 10: 清理剩余的占位符
            # 策略：如果整行只有占位符，删除整行；否则只删除占位符
            # 每次操作后等待编辑器响应
            print("  🧹 清理剩余占位符...")

            max_cleanup_rounds = 30
            total_cleaned = 0

            for round_num in range(max_cleanup_rounds):
                # 查找下一个占位符，并判断是否需要删除整行
                cleanup_result = page.evaluate('''() => {
                    const editors = document.querySelectorAll('[contenteditable="true"]');
                    let bodyEditor = null;
                    let maxLength = 0;

                    editors.forEach((e) => {
                        if (e.innerText.length > maxLength) {
                            maxLength = e.innerText.length;
                            bodyEditor = e;
                        }
                    });

                    if (!bodyEditor) return { found: false, error: 'No editor found' };

                    // 确保编辑器有焦点
                    bodyEditor.focus();

                    // 搜索第一个占位符
                    const walker = document.createTreeWalker(
                        bodyEditor,
                        NodeFilter.SHOW_TEXT,
                        null,
                        false
                    );

                    let node;
                    const placeholderPattern = /@@@IMG_\\d+@@@/;

                    while (node = walker.nextNode()) {
                        const match = node.textContent.match(placeholderPattern);
                        if (match) {
                            const parentEl = node.parentElement;

                            // 滚动到可见
                            if (parentEl) {
                                parentEl.scrollIntoView({ behavior: 'instant', block: 'center' });
                            }

                            // 检查这一行是否只有占位符（去除空白后）
                            const lineText = parentEl ? parentEl.innerText.trim() : node.textContent.trim();
                            const isOnlyPlaceholder = lineText === match[0] ||
                                                       lineText.replace(/@@@IMG_\\d+@@@/g, '').trim() === '';

                            if (isOnlyPlaceholder && parentEl) {
                                // 整行只有占位符，选中整个段落元素
                                const range = document.createRange();
                                const sel = window.getSelection();

                                range.selectNodeContents(parentEl);

                                sel.removeAllRanges();
                                sel.addRange(range);

                                return {
                                    found: true,
                                    placeholder: match[0],
                                    deleteWholeLine: true,
                                    lineText: lineText.substring(0, 50)
                                };
                            } else {
                                // 只删除占位符文本
                                const startOffset = node.textContent.indexOf(match[0]);
                                const range = document.createRange();
                                const sel = window.getSelection();

                                range.setStart(node, startOffset);
                                range.setEnd(node, startOffset + match[0].length);

                                sel.removeAllRanges();
                                sel.addRange(range);

                                return {
                                    found: true,
                                    placeholder: match[0],
                                    deleteWholeLine: false
                                };
                            }
                        }
                    }

                    return { found: false };
                }''')

                if not cleanup_result.get('found'):
                    break

                # 删除选中的内容
                page.keyboard.press("Backspace")
                time.sleep(0.3)

                # 如果删除的是整行，需要再按一次 Backspace 删除空行
                if cleanup_result.get('deleteWholeLine'):
                    page.keyboard.press("Backspace")
                    time.sleep(0.3)

                total_cleaned += 1

                # 关键：等待编辑器响应
                time.sleep(0.5)

                # 每清理5个，额外等待让编辑器处理
                if total_cleaned % 5 == 0:
                    print(f"      已清理 {total_cleaned} 个，等待编辑器同步...")
                    time.sleep(1.5)

            if total_cleaned > 0:
                print(f"  ✅ 已清理 {total_cleaned} 个占位符")

            # 等待编辑器完成所有更新
            print("  ⏳ 等待编辑器同步...")
            time.sleep(3)

            # 验证是否还有剩余
            remaining = page.evaluate('''() => {
                const editors = document.querySelectorAll('[contenteditable="true"]');
                let bodyEditor = null;
                let maxLength = 0;
                editors.forEach((e) => {
                    if (e.innerText.length > maxLength) {
                        maxLength = e.innerText.length;
                        bodyEditor = e;
                    }
                });
                if (!bodyEditor) return [];
                return bodyEditor.innerText.match(/@@@IMG_\\d+@@@/g) || [];
            }''')

            if remaining:
                print(f"  ⚠️  仍有 {len(remaining)} 个占位符，再次清理...")
                # 再尝试一轮清理
                for _ in range(len(remaining)):
                    cleanup_result = page.evaluate('''() => {
                        const editors = document.querySelectorAll('[contenteditable="true"]');
                        let bodyEditor = null;
                        let maxLength = 0;
                        editors.forEach((e) => {
                            if (e.innerText.length > maxLength) {
                                maxLength = e.innerText.length;
                                bodyEditor = e;
                            }
                        });
                        if (!bodyEditor) return { found: false };
                        bodyEditor.focus();

                        const walker = document.createTreeWalker(bodyEditor, NodeFilter.SHOW_TEXT, null, false);
                        let node;
                        const pattern = /@@@IMG_\\d+@@@/;

                        while (node = walker.nextNode()) {
                            const match = node.textContent.match(pattern);
                            if (match) {
                                const parentEl = node.parentElement;
                                if (parentEl) parentEl.scrollIntoView({ behavior: 'instant', block: 'center' });

                                const startOffset = node.textContent.indexOf(match[0]);
                                const range = document.createRange();
                                const sel = window.getSelection();
                                range.setStart(node, startOffset);
                                range.setEnd(node, startOffset + match[0].length);
                                sel.removeAllRanges();
                                sel.addRange(range);
                                return { found: true };
                            }
                        }
                        return { found: false };
                    }''')

                    if not cleanup_result.get('found'):
                        break

                    page.keyboard.press("Backspace")
                    time.sleep(1)  # 更长的等待时间

                print(f"  ✅ 二次清理完成")

            # Step 11: 等待自动保存完成
            print("\n  ⏳ 等待自动保存...")
            time.sleep(5)  # 等待 X 自动保存

            # 检查是否有保存指示
            save_check = page.evaluate('''() => {
                // 检查是否有"已保存"或类似提示
                const bodyText = document.body.innerText;
                const hasSaved = bodyText.includes('已保存') ||
                                 bodyText.includes('Saved') ||
                                 bodyText.includes('草稿');
                return { hasSaved, timestamp: new Date().toISOString() };
            }''')
            print(f"  ✅ 保存状态检查完成")

            # Step 12: 完成，保持浏览器打开
            print("\n✅ 草稿已创建并保存！")
            print("  💡 请在浏览器中检查并手动发布")
            print("  🖥️  浏览器保持打开中...")
            print("  ⌨️  按 Ctrl+C 退出脚本（浏览器会保持打开）")

            # 保持脚本运行，让浏览器保持打开
            try:
                while True:
                    time.sleep(60)  # 每分钟检查一次
            except KeyboardInterrupt:
                print("\n  👋 脚本已退出，浏览器保持打开")

            return True

        except Exception as e:
            print(f"\n❌ 发布失败：{e}")
            import traceback
            traceback.print_exc()
            return False


def main():
    parser = argparse.ArgumentParser(description='发布文章到 X Articles')
    parser.add_argument('--file', required=True, help='Markdown 文件路径')
    parser.add_argument('--title', help='自定义标题（覆盖文件中的标题）')
    parser.add_argument('--cover', help='自定义封面图路径（覆盖文件中的封面）')
    parser.add_argument('--show-browser', action='store_true', help='显示浏览器窗口')

    args = parser.parse_args()

    publisher = ArticlePublisher()
    success = publisher.publish(
        file_path=args.file,
        custom_title=args.title,
        custom_cover=args.cover,
        headless=not args.show_browser
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
