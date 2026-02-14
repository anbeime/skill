# Qiaomu X Article Publisher

> 🚀 一键发布 Markdown 文章到 X (Twitter) Articles，让写作更流畅

![Version](https://img.shields.io/badge/version-1.0.0-blue)
![Platform](https://img.shields.io/badge/platform-macOS-lightgrey)
![Python](https://img.shields.io/badge/python-3.9+-green)
![License](https://img.shields.io/badge/license-MIT-orange)

基于 [@wshuyi 王树义老师](https://github.com/wshuyi/x-article-publisher-skill) 的原版改进，添加持久化认证、完全自包含设计。

---

## 📖 为什么需要这个工具？

X Articles 是一个强大的长文发布平台，但直接在网页编辑器写作体验不够流畅：
- ❌ 格式工具栏操作繁琐
- ❌ 无法用熟悉的 Markdown 语法
- ❌ 缺少本地版本管理
- ❌ 需要手动上传图片
- ❌ 每次都要重新登录

**这个 Skill 解决了这些痛点**：
- ✅ 用 Markdown 写作，自动转换为 X Articles 格式
- ✅ 本地文件管理，配合 Git 版本控制
- ✅ **持久化登录，7天免重复认证**（新增）
- ✅ 智能图片处理，一键上传
- ✅ **完全自包含，开箱即用**（新增）

---

## ✨ 核心功能

### 🔐 持久化认证（新增）
一次登录，7天内无需重复认证。基于内置浏览器认证框架实现。

### 📝 Markdown 完整支持
自动转换以下格式：
- 标题（H1-H6）
- 粗体、斜体
- 列表（有序/无序）
- 引用块
- 代码块（转为引用样式）
- 超链接
- 图片（封面图 + 内容图）

### 🖼️ 智能图片处理
- 自动识别封面图（文章第一张图）
- 内容图片自动上传
- 支持本地路径和相对路径

### ⚡ 一键发布
单条命令完成所有步骤，只保存为草稿，不会自动发布（安全第一）。

---

## 🚀 快速开始

### 安装（与 Claude Code 对话）

**最简单的方式** - 直接告诉 Claude Code：
```
安装这个 Claude skill：https://github.com/joeseesun/qiaomu-x-article-publisher
```

Claude Code 会自动完成所有安装步骤！

### 手动安装

```bash
# 1. 克隆到 Claude skills 目录
git clone https://github.com/joeseesun/qiaomu-x-article-publisher.git \
  ~/.claude/skills/qiaomu-x-article-publisher

# 2. 安装 Python 依赖
pip install Pillow pyobjc-framework-Cocoa patchright

# 3. 首次认证
cd ~/.claude/skills/qiaomu-x-article-publisher/scripts
python auth_manager.py setup
```

---

## 📖 使用示例

### 示例 1：基本发布

```bash
cd ~/.claude/skills/qiaomu-x-article-publisher/scripts
python publish_article.py --file ~/articles/my-post.md
```

### 示例 2：与 Claude Code 协作

```
你：帮我写一篇关于 AI 的文章
Claude：[生成文章并保存]
你：发布到 X Articles
Claude：[自动调用 Skill 发布]
```

### 示例 3：自定义标题

```bash
python publish_article.py --file article.md --title "更吸引人的标题"
```

---

## 🎯 完整功能文档

查看完整功能、使用场景、故障排查请访问：
👉 [完整 README_FULL.md](./README_FULL.md)

---

## 📋 系统要求

- macOS
- Python 3.9+
- X Premium Plus 订阅

---

## 🔧 常见问题

**Q: 认证过期怎么办？**
A: `python auth_manager.py reauth`

**Q: 会自动发布吗？**
A: 不会，只保存为草稿，需手动发布

**Q: 支持 Windows/Linux 吗？**
A: 目前仅支持 macOS（使用 pyobjc 剪贴板功能）

---

## 📚 学习资源

- 📖 [OpenCode + OMO 玩Skill的教程](https://mp.weixin.qq.com/s/AQd9RV43SYGLhjB8l3SFtw) - 详细的 Skill 开发指南
- 🎓 [完整使用文档](./README_FULL.md) - 本项目详细文档

---

## 🙏 致谢

本项目基于 [@wshuyi 王树义老师](https://github.com/wshuyi/x-article-publisher-skill) 的原版改进：

**原版特点**：
- 开创性地实现了 Markdown 到 X Articles 的自动转换
- 清晰的代码架构和文档

**本版本改进**：
- ✨ 新增持久化认证（7天免登录）
- ✨ 完全自包含（内置 browser_auth 框架）
- ✨ 完善的文档和故障排查指南
- ✨ Claude Code 一键安装支持

感谢王树义老师的开源贡献！

---

## 📝 更新日志

### v1.0.0 (2026-01-14) - 首次发布 🎉
- Markdown 自动转换
- 持久化认证（7天）
- 智能图片处理
- 完全自包含
- 详细文档

查看完整更新日志：[CHANGELOG.md](./CHANGELOG.md)

---

## 🤝 贡献

欢迎贡献！查看 [CONTRIBUTING.md](./CONTRIBUTING.md) 了解如何参与。

---

## 📄 许可证

MIT License - 查看 [LICENSE](./LICENSE)

---

## 📞 联系方式

- 👤 作者：Qiaomu (乔木)
- 🐦 X (Twitter): [@vista8](https://x.com/vista8)
- 🌐 个人网站：[qiaomu.ai](https://qiaomu.ai/)
- 💻 GitHub: [@joeseesun](https://github.com/joeseesun)
- 📧 Email: vista8@gmail.com

---

**⭐ 如果这个工具对你有帮助，请给个 Star！**

_让 Markdown 写作与 X Articles 发布无缝衔接_ ✨
