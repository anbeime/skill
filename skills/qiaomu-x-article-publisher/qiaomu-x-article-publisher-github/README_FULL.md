# Qiaomu X Article Publisher - 完整文档

完整功能文档、使用场景、故障排查和开发指南。

## 目录

- [详细使用方法](#详细使用方法)
- [典型工作流](#典型工作流)
- [技术架构](#技术架构)
- [故障排查](#故障排查)
- [路线图](#路线图)
- [贡献指南](#贡献指南)

---

## 详细使用方法

### Markdown 格式示例

```markdown
# 为什么每个开发者都应该学会写作

![封面图](./cover.png)

写作不仅是记录思考，更是深度思考的催化剂。

## 写作的三个好处

1. **强迫你组织思路** - 模糊的想法无法写成清晰的文字
2. **建立个人品牌** - 优质内容吸引同类人
3. **异步沟通的力量** - 写一次，影响无数人

> "Writing is thinking on paper."

## 如何开始

最简单的方法：**每天写 500 字**。
```

### 命令行选项

```bash
# 基本发布
python publish_article.py --file article.md

# 自定义标题
python publish_article.py --file article.md --title "更吸引人的标题"

# 显示浏览器（调试用）
python publish_article.py --file article.md --show-browser
```

### 认证管理

```bash
# 查看认证状态
python auth_manager.py status

# 验证认证是否有效
python auth_manager.py validate

# 重新认证
python auth_manager.py reauth

# 清除认证数据
python auth_manager.py clear
```

---

## 典型工作流

### 场景 1：日常写作发布

```bash
# 1. 用你喜欢的编辑器写 Markdown
vim ~/articles/new-post.md

# 2. 一键发布
cd ~/.claude/skills/qiaomu-x-article-publisher/scripts
python publish_article.py --file ~/articles/new-post.md

# 3. 在浏览器中检查草稿
# 4. 满意后手动点击"发布"
```

### 场景 2：与 Claude Code 协作

```
你：帮我写一篇关于 AI 代理的文章

Claude：[生成文章内容，保存为 Markdown]

你：发布到 X Articles

Claude：[自动调用 Skill 发布]
```

### 场景 3：批量发布

```bash
#!/bin/bash
# 批量发布脚本
for file in ~/articles/*.md; do
  echo "发布: $file"
  python publish_article.py --file "$file"
  sleep 5  # 避免频率限制
done
```

---

## 技术架构

### 核心设计哲学

1. **完全自包含** - 内置 browser_auth 框架，无需外部依赖
2. **安全第一** - 只保存草稿，不自动发布；认证数据加密存储
3. **用户友好** - 单条命令完成所有操作
4. **可扩展** - 模块化设计，易于添加新功能

### 目录结构

```
qiaomu-x-article-publisher/
├── scripts/              
│   ├── publish_article.py   # 主发布脚本
│   ├── auth_manager.py      # 认证管理
│   ├── parse_markdown.py    # Markdown 解析器
│   ├── site_config.py       # X 站点配置
│   └── copy_to_clipboard.py # 剪贴板工具
├── lib/                  
│   └── browser_auth/     # 浏览器认证框架（内置）
├── data/                 
│   ├── auth_info.json    # 认证元数据（gitignore）
│   └── browser_state/    # 浏览器状态（gitignore）
├── README.md             # 简洁版说明
├── README_FULL.md        # 本文件（完整文档）
├── SKILL.md              # Claude Code 技术文档
├── CHANGELOG.md          # 变更日志
└── metadata.json         # Skill 元数据
```

---

## 故障排查

### 问题 1：导入 browser_auth 失败

**错误**: `ModuleNotFoundError: No module named 'browser_auth'`

**原因**: Skill 目录不完整

**解决**:
```bash
ls ~/.claude/skills/qiaomu-x-article-publisher/lib/browser_auth/
# 如果不存在，重新克隆仓库
```

### 问题 2：认证失效

**现象**: 提示"认证已过期"

**解决**:
```bash
python auth_manager.py reauth
```

### 问题 3：找不到"撰写"按钮

**原因**:
1. X 界面语言不是中文
2. Premium Plus 订阅未激活

**解决**:
1. 在 X 设置中将语言改为中文
2. 检查订阅：https://twitter.com/i/premium_plus_sign_up

### 问题 4：图片上传失败

**原因**: 图片路径不正确

**解决**:
```bash
# 检查图片是否存在
ls /path/to/image.jpg

# 使用绝对路径或相对路径
```

---

## 路线图

### v1.0（当前）
- ✅ Markdown 自动转换
- ✅ 持久化认证
- ✅ 图片上传
- ✅ 完全自包含

### v1.1（计划）
- [ ] 自动生成标题（集成 Claude）
- [ ] 自动生成封面图
- [ ] 批量发布模式
- [ ] 发布历史记录

### v1.2（未来）
- [ ] 支持表格、脚注
- [ ] 草稿同步到本地
- [ ] 发布时间预约
- [ ] 发布统计分析

---

## 贡献指南

欢迎贡献！

### 开发环境设置

```bash
git clone https://github.com/[your-username]/qiaomu-x-article-publisher.git
cd qiaomu-x-article-publisher
pip install Pillow pyobjc-framework-Cocoa patchright
```

### 提交 Pull Request

1. Fork 这个仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交改动 (`git commit -m 'Add AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

查看 [README.md](./README.md) 返回简洁版说明
