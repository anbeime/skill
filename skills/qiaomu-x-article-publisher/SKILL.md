---
name: x-article-publisher
description: 自媒体创作者与内容创作者在需要将 Markdown 长文发布到 X (Twitter) Articles 编辑器时使用。技能自动将 Markdown 转换为富文本并完美保留排版，支持持久化免密登录与封面上传，一键完成发布，大幅提升长文分发效率。
---

# X Article Publisher

Publish Markdown content to X (Twitter) Articles editor, preserving formatting with rich text conversion.

## Prerequisites

- X Premium Plus subscription
- Python 3.9+ with dependencies: `pip install Pillow pyobjc-framework-Cocoa patchright`

## 🎉 首次使用：一次认证，告别重复登录

**X Article Publisher 现在支持持久化认证，无需每次手动登录！**

### 🔧 初始化认证（仅需一次）

首次使用前，运行认证设置：

```bash
cd ~/.claude/skills/x-article-publisher/scripts
python auth_manager.py setup
```

**流程：**
1. ✅ 浏览器窗口自动打开 X 登录页面
2. 🔐 手动登录你的 X 账号（需 Premium+ 订阅）
3. ✅ 完成 2FA 验证（如已启用）
4. 🏠 登录成功后自动跳转到 Home 时间线
5. 💾 认证状态自动保存（有效期 7 天）

### 📋 认证管理命令

```bash
# 检查认证状态
python auth_manager.py status

# 验证认证是否有效
python auth_manager.py validate

# 清除认证数据（需重新登录）
python auth_manager.py clear

# 重新认证（清除 + 设置）
python auth_manager.py reauth
```

### 🚀 自动化工作流

认证设置完成后，skill 执行时会自动：
1. ✅ 检查认证状态
2. 🔓 如已认证，直接使用保存的浏览器状态（无需登录）
3. ⚠️ 如未认证，提示运行 `auth_manager.py setup`

**注意**：认证数据存储在 `~/.claude/skills/x-article-publisher/data/browser_state/`，已通过 .gitignore 排除，不会提交到 Git。

---

## Scripts

Located in `~/.claude/skills/x-article-publisher/scripts/`:

### publish_article.py (主脚本 - 一键发布)
**推荐使用** - 自动完成所有发布步骤：
```bash
# 基本用法（默认显示浏览器）
python publish_article.py --file article.md

# 隐藏浏览器（后台运行）
python publish_article.py --file article.md --headless

# 自定义标题
python publish_article.py --file article.md --title "自定义标题"
```

### parse_markdown.py
Parse Markdown and extract structured data:
```bash
python parse_markdown.py <markdown_file> [--output json|html] [--html-only]
```
Returns JSON with: title, cover_image, content_images (with block_index for positioning), html, total_blocks

### copy_to_clipboard.py
Copy image or HTML to system clipboard:
```bash
# Copy image (with optional compression)
python copy_to_clipboard.py image /path/to/image.jpg [--quality 80]

# Copy HTML for rich text paste
python copy_to_clipboard.py html --file /path/to/content.html
```

## Workflow (简化版)

**前提**：已完成认证设置（`python auth_manager.py setup`）

### 🚀 一键发布（推荐）

直接运行 publish_article.py，自动完成所有步骤：

```bash
cd ~/.claude/skills/x-article-publisher/scripts
python publish_article.py --file /path/to/article.md
```

脚本会自动：
1. ✅ 检查认证状态
2. 📄 解析 Markdown 文件
3. 🌐 启动已认证的浏览器
4. 📍 导航到 X Articles 编辑器
5. 🔘 点击 create 按钮
6. 🖼️ 上传封面图（如有）
7. 📝 填写标题
8. 📋 粘贴 HTML 内容
9. ✅ 保存草稿（**不会自动发布**）

### 手动工作流（高级用户）

如需更精细控制，可分步执行：
1. Parse Markdown: `python parse_markdown.py article.md`
2. 手动操作浏览器发布

---

## 🧠 智能增强功能

### 智能标题生成

当文章没有 H1 标题时，`parse_markdown.py` 会返回 `needs_title_generation: true`。

**Claude 应该自动：**
1. 阅读文章内容，理解核心观点
2. 生成一个吸引人点击的标题（15-25字为佳）
3. 使用 `--title "生成的标题"` 参数发布

**好标题的特点：**
- 包含数字或具体细节（"3个方法"、"90%的人不知道"）
- 激发好奇心（"为什么..."、"如何..."、"...的真相"）
- 与读者切身相关
- 避免标题党，但要有吸引力

**示例：**
```bash
# 解析文章
python parse_markdown.py article.md

# 如果 needs_title_generation: true，Claude 生成标题后：
python publish_article.py --file article.md --title "AI时代，普通人的3个生存法则"
```

### 智能封面图生成

当文章没有封面图时，`parse_markdown.py` 会返回 `needs_cover_generation: true`。

**Claude 应该自动：**
1. 阅读文章，提炼核心概念（1-3个关键词）
2. 调用 `gemini-image-generator` 或 `jimeng-image-generator` skill 生成封面图
3. 封面图风格建议：
   - 简洁大气，避免复杂细节
   - 可以是抽象概念的可视化
   - 或是带有核心关键词的文字海报
4. 将生成的图片路径插入到文章开头作为封面

**封面图生成提示词模板：**
```
为一篇关于「{文章主题}」的文章生成封面图。
风格：简洁、现代、科技感
元素：{1-3个核心视觉元素}
文字：可选，如果加文字只放{1-3个关键词}
尺寸：16:9 横版
```

**工作流示例：**
```bash
# 1. 解析文章
python parse_markdown.py article.md
# 输出: needs_cover_generation: true

# 2. Claude 调用生图 skill 生成封面（假设保存到 /tmp/cover.png）

# 3. 将封面图插入文章开头，或手动上传
```

**注意**：封面图上传目前需要在浏览器中手动操作，脚本会打开编辑器后等待用户操作。

---

## 技术细节

### parse_markdown.py 输出格式

```json
{
  "title": "Article Title",
  "title_source": "h1",           // "h1", "h2", "first_line", or "none"
  "needs_title_generation": false, // true if no H1 title
  "cover_image": "/path/to/first-image.jpg",
  "needs_cover_generation": false, // true if no cover image
  "content_images": [
    {"path": "/path/to/img2.jpg", "block_index": 5}
  ],
  "html": "<p>Content...</p><h2>Section</h2>...",
  "total_blocks": 45
}
```

**字段说明：**
- `title_source`: 标题来源
  - `h1`: 来自 H1 标题（最理想）
  - `h2`: 来自第一个 H2 标题
  - `first_line`: 来自第一行文本
  - `none`: 无法提取标题
- `needs_title_generation`: 是否需要 Claude 生成更好的标题
- `needs_cover_generation`: 是否需要 Claude 生成封面图

## Critical Rules

1. **NEVER auto-publish** - Only save as draft
2. **NO automatic cover images** - User adds cover manually, never insert first image as cover
3. **Clean placeholders** - Remove all remaining `@@@IMG_X@@@` markers after image insertion
4. **H1 title handling** - H1 is used as title only, not included in body

## Supported Formatting

- H2 headers (## )
- Blockquotes (> )
- Code blocks (converted to blockquotes)
- Bold text (**)
- Hyperlinks ([text](url))
- Ordered/Unordered lists
- Paragraphs

## Example

User: "Publish /path/to/article.md to X"

```bash
cd ~/.claude/skills/x-article-publisher/scripts
python publish_article.py --file /path/to/article.md
```

Output:
```
📄 解析文件：/path/to/article.md
  📝 标题：文章标题
  🖼️  封面图：/path/to/cover.jpg
  📷 内容图：2 张

🌐 启动浏览器...
  📍 导航到 X Articles...
  🔘 点击 create 按钮...
  📝 填写标题...
  📋 粘贴内容...

✅ 草稿已创建！
  💡 请在浏览器中检查并手动发布
  🖥️  浏览器保持打开，请检查草稿并手动发布
  ⏎  完成后按回车键关闭浏览器...
```



**技术经验参考**: 浏览器自动化调试技巧详见 [skill-development-guide](../skill-development-guide/technical-lessons.md)
