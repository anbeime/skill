[← Awesome JEV](../README.zh-CN.md#discovery)

# 用 Agent 搜索项目

描述你想做的事，让 Agent 从同一份项目目录和场景索引里选择参考实现。检索不需要 BeatAPI 账号或 API Key。

## 安装

```bash
npx skills add BeatAPI/awesome-jev
```

在希望使用 Skill 的项目目录中运行，再按安装器提示选择 Agent。需要 Node.js/npm；宿主支持范围以安装器为准。

[Skill source](../skills/awesome-jev/SKILL.md) · [Installer documentation](https://skills.sh/docs/cli)

## 可以这样问

- 我想筛选与品牌相关的新闻，帮我找 JEV 项目，并说明每个项目值得参考哪一部分。
- 找适合 Agent 记忆重排的 Python 项目，区分直接匹配和需要改造的思路。
- 比较适合编程 Agent 的 JEV 模型路由项目，给出实现证据链接。

## 会得到什么

少量精选结果：GitHub 链接、匹配理由、具体参考部分与证据状态。Agent 读取当前公开目录，不依赖安装时冻结的项目列表；读取失败时会明确说明。

## 手动安装

将 `skills/awesome-jev` 文件夹复制到宿主支持的 Skill 目录。例如 Codex 可放到 `~/.codex/skills/awesome-jev`，然后开启新会话。安装的是检索说明，不会安装或运行推荐项目。

## 维护者本地预览

本次改动合并前，可在仓库中用 `npx skills add . --list` 验证发现，再运行 `npx skills add .` 从本地安装。上面的远程安装命令需等 Skill 进入默认分支后才能使用。
