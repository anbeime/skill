# Changelog

所有重要变更都会记录在这个文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [1.0.0] - 2026-01-14

### 新增 ✨
- Markdown 到 X Articles 自动转换
- 持久化浏览器认证（7天有效期）
- 智能图片处理（封面图 + 内容图）
- 一键发布命令
- 完全自包含（内置 browser_auth 框架）
- 认证管理命令（status/validate/reauth/clear）

### 技术亮点 🔧
- 使用 Patchright 绕过自动化检测
- 混合认证方案（user_data_dir + state.json）
- 配置驱动的验证策略
- 模块化设计，易于扩展

### 安全设计 🔐
- 只保存草稿，不自动发布
- 认证数据通过 .gitignore 排除
- 无硬编码凭据

### 文档 📖
- 完整的 README.md
- SKILL.md（Claude Code 技术文档）
- 故障排查指南
- 使用场景示例

### 致谢 🙏
基于 [@wshuyi 王树义老师](https://github.com/wshuyi/x-article-publisher-skill) 的原版改进。

---

## [Unreleased]

### 计划新增
- 自动生成标题功能
- 自动生成封面图功能
- 批量发布模式
- 发布历史记录

---

## 贡献

如果你发现 Bug 或有功能建议，欢迎：
- 提交 Issue: https://github.com/joeseesun/qiaomu-x-article-publisher/issues
- 提交 Pull Request

---

_格式说明:_
- `新增` - 新功能
- `变更` - 现有功能的变化
- `废弃` - 即将移除的功能
- `移除` - 已移除的功能
- `修复` - Bug 修复
- `安全` - 安全相关的修复
