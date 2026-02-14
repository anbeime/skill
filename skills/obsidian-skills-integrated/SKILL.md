# Obsidian Skills - 官方知识管理技能集

## 简介

由 Obsidian CEO Steph Ango (kepano) 亲自开源的官方技能集，为 AI Agent 提供专业的 Obsidian 操作能力。

**项目地址**: https://github.com/kepano/obsidian-skills  
**GitHub Star**: 9.4k+  
**开源协议**: MIT License  
**技术规范**: 遵循 [Agent Skills specification](https://agentskills.io/specification)

## 核心价值

✅ **官方背书** - Obsidian CEO 亲自开发，质量和兼容性有保障  
✅ **填补空白** - 为本地技能库增加专业的知识管理能力  
✅ **标准规范** - 遵循 Agent Skills 规范，易于集成和维护  
✅ **协同增强** - 与现有技能形成完整工作流闭环  

## 包含技能

### 1. obsidian-markdown
**功能**: 处理 Obsidian 专属 Markdown 语法

**核心能力**:
- ✅ 双向链接 (Wikilinks): `[[笔记名称]]`
- ✅ 内容嵌入 (Embed): `![[文件名]]`
- ✅ 标注块 (Callouts): `> [!INFO]`
- ✅ 前置元数据 (Properties/Frontmatter): YAML 格式
- ✅ 标签系统: `#标签名`
- ✅ 数学公式: LaTeX 语法
- ✅ 图表支持: Mermaid 等

**解决痛点**: 通用 AI 模型常破坏 Obsidian 专属语法，导致双链失效、Callout 格式错乱、Frontmatter 被误删。

### 2. json-canvas
**功能**: 创建和编辑 Obsidian Canvas 画布文件

**核心能力**:
- ✅ 多种节点类型: 文本/文件/链接/组节点
- ✅ 连接边 (Edges): 建立节点间关系
- ✅ 精确定位: x/y 坐标、z-index 层级
- ✅ 颜色标识: 十六进制颜色支持
- ✅ 格式验证: 严格的 JSON 结构校验

**应用场景**: 思维导图、知识图谱、流程图、项目看板。

### 3. obsidian-bases
**功能**: 操作 Obsidian 1.9+ 原生数据库

**核心能力**:
- ✅ 视图管理: 创建、编辑多种视图类型
- ✅ 过滤器: 复杂条件筛选
- ✅ 公式系统: 正确的函数调用语法
- ✅ 汇总项: 数据统计与聚合

**解决痛点**: AI 生成的数据库公式"看起来对却跑不起来"，过滤器语法错误导致视图失效。

## 快速使用

### 示例 1: 创建笔记
```
请用 obsidian-markdown 创建一篇关于"人工智能发展史"的笔记，包含：
- 双链引用相关概念
- 使用 INFO Callout 标注重点
- 添加 tags 和 date 元数据
```

### 示例 2: 生成思维导图
```
请用 json-canvas 生成《三国演义》人物关系图，包含：
- 主要人物节点（刘备、关羽、张飞、曹操、孙权等）
- 关系连接线（结义、对抗、联盟）
- 按势力分组并用颜色区分
```

### 示例 3: 创建数据库
```
请用 obsidian-bases 创建一个读书清单数据库，包含：
- 字段：书名、作者、评分、状态、阅读日期
- 视图：按评分排序
- 过滤器：仅显示已读书籍
```

## 版本要求

- **Obsidian 1.0+**: obsidian-markdown, json-canvas
- **Obsidian 1.9+**: obsidian-bases（数据库功能）

**建议**: 升级到最新版 Obsidian 以获得完整功能支持。

## 与其他技能的协同

### 工作流 1: 内容创作全流程
```
obsidian-markdown (创建笔记)
    ↓
article-illustrator (自动配图)
    ↓
baoyu-post-to-wechat (发布到公众号)
```

**实施要点**:
- article-illustrator 输出图片时使用 Obsidian 语法: `![[image.png]]`
- 发布前自动转换 Obsidian 专属语法为目标平台格式

### 工作流 2: 知识可视化
```
obsidian-markdown (结构化笔记)
    ↓
json-canvas (知识图谱)
    ↓
ppt-generator (演示文稿)
```

**实施要点**:
- json-canvas 快速生成知识网络
- ppt-generator 支持读取 Canvas 作为输入源

### 工作流 3: 项目管理
```
obsidian-bases (项目数据库)
    ↓
json-canvas (项目看板)
    ↓
intelligent-content-system (报告生成)
```

**实施要点**:
- obsidian-bases 管理任务、进度、资源
- json-canvas 可视化项目状态
- intelligent-content-system 自动生成项目报告

## 潜在冲突与解决方案

### 冲突 1: baoyu-format-markdown 格式化冲突 ⚠️

**问题**: baoyu-format-markdown 可能破坏 Obsidian 专属语法（双链/Callout/Frontmatter）

**解决方案**:
- **Obsidian 库内**: 优先使用 `obsidian-markdown`
- **外部文档**: 使用 `baoyu-format-markdown`
- **判断依据**: 检测文件路径是否在 Obsidian vault 内

### 冲突 2: ai-drawio 功能重叠 🔄

**问题**: json-canvas 与 ai-drawio 都能生成可视化图表

**解决方案**: 保留两者，按场景划分
- **知识图谱/思维导图** → `json-canvas` (Obsidian 原生，无缝集成)
- **复杂技术流程图** → `ai-drawio` (专业工具，功能更强)

## 使用建议

### 最佳实践
1. ✅ 在 Obsidian vault 内工作时，始终使用 obsidian-skills
2. ✅ 创建笔记前明确格式要求（标签、Callout 类型等）
3. ✅ 批量操作前先做单文件测试，避免格式问题
4. ✅ 定期更新技能，跟随 Obsidian 版本保持适配

### 注意事项
- ⚠️ obsidian-bases 需要 Obsidian 1.9+，旧版本用户无法使用
- ⚠️ 生成的 .canvas 文件需在 Obsidian 中打开查看
- ⚠️ 避免在非 Obsidian 环境使用这些技能（价值有限）

## 后续维护

### 版本同步
```bash
cd D:\tool\skills\obsidian-skills-integrated
# 下载最新版本
Invoke-WebRequest -Uri "https://github.com/kepano/obsidian-skills/archive/refs/heads/main.zip" -OutFile "update.zip"
# 解压并更新
Expand-Archive -Path "update.zip" -DestinationPath "temp" -Force
# 手动对比更新内容
```

**建议频率**: 每月检查一次更新

### 关注渠道
- [GitHub Releases](https://github.com/kepano/obsidian-skills/releases)
- [Obsidian 官方博客](https://obsidian.md/blog)
- [Agent Skills 规范更新](https://agentskills.io/specification)

## 参考资源

### 官方文档
- [Obsidian 官方帮助](https://help.obsidian.md/)
- [Obsidian Flavored Markdown](https://help.obsidian.md/obsidian-flavored-markdown)
- [Obsidian Bases 语法](https://help.obsidian.md/bases/syntax)
- [JSON Canvas 规范](https://jsoncanvas.org/)

### 社区资源
- [GitHub 仓库](https://github.com/kepano/obsidian-skills)
- [Agent Skills 规范](https://agentskills.io/specification)
- [Obsidian 论坛](https://forum.obsidian.md/)

## 技能对比

| 技能 | 功能领域 | 输出格式 | Obsidian 集成 | 使用优先级 |
|------|---------|---------|--------------|-----------|
| obsidian-markdown | Markdown 处理 | .md | 原生支持 | ⭐⭐⭐⭐⭐ |
| json-canvas | 可视化 | .canvas | 原生支持 | ⭐⭐⭐⭐⭐ |
| obsidian-bases | 数据库 | .base | 原生支持 | ⭐⭐⭐⭐ |
| baoyu-format-markdown | Markdown 格式化 | .md | 潜在冲突 | ⭐⭐⭐ |
| ai-drawio | 流程图 | .drawio | 需导出 | ⭐⭐⭐ |
| article-illustrator | 配图 | 图片 | 协同增强 | ⭐⭐⭐⭐ |
| ppt-generator | 演示文稿 | .pptx | 协同增强 | ⭐⭐⭐ |

## 常见问题

### Q1: 与现有技能冲突怎么办？
**A**: 按场景隔离使用，Obsidian 库内优先使用 obsidian-skills，外部文档使用其他技能。

### Q2: 不用 Obsidian 有必要整合吗？
**A**: 不建议。这些技能专为 Obsidian 设计，脱离 Obsidian 价值有限。

### Q3: 如何更新到最新版本？
**A**: 每月从 GitHub 下载最新版本，手动对比更新内容后替换文件。

### Q4: 能否只整合部分技能？
**A**: 可以。建议至少整合 obsidian-markdown + json-canvas，obsidian-bases 可选（需 Obsidian 1.9+）。

### Q5: 生成的文件在哪里查看？
**A**: 
- `.md` 文件：任何文本编辑器或 Obsidian
- `.canvas` 文件：必须在 Obsidian 中打开
- `.base` 文件：必须在 Obsidian 1.9+ 中打开

## 总结

### 核心优势
✅ **官方权威** - Obsidian CEO 亲自开发，9.4k+ Star  
✅ **功能完整** - 覆盖笔记、可视化、数据库三大核心场景  
✅ **标准规范** - 遵循 Agent Skills 规范，易于维护  
✅ **协同增强** - 与现有技能形成完整工作流  

### 适用人群
- ✅ Obsidian 深度用户
- ✅ 知识管理爱好者
- ✅ 内容创作者
- ✅ 项目管理人员

### 预期收益
- 📝 笔记管理效率提升 **10 倍**
- 🎨 知识可视化时间缩短 **90%**
- 🔗 内容创作工作流完整闭环
- 🚀 技能库整体能力质的飞跃

---

**整合完成时间**: 2026-02-09  
**技能版本**: 基于 GitHub main 分支  
**下次更新建议**: 2026-03-09 (一个月后)  
**维护状态**: ✅ 已整合，定期更新
