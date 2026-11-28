---
name: keenable-web-search
description: 联网搜索与网页读取技能。需要训练数据之外的实时信息时使用：新闻动态、论文与一手资料、官方文档、公司与市场调研、事实核查与引用出处。自带两个 Python 脚本（仅用标准库），调用 Keenable 免 Key 公共接口，无需注册、无需安装依赖。不用于本地文件操作。
version: 1.0.0
author: keenableai
tags:
  - web-search
  - search
  - research
  - news
  - keyless
license: MIT
---

# Keenable 联网搜索

用 Keenable 搜索引擎联网检索实时信息，返回可引用的网页标题、URL 和摘要，并能把网页读成 Markdown。免 Key、零依赖。

## 任务目标

- 本技能用于：在回答依赖网络上的最新信息时，先联网搜索，再读取相关网页，最后带出处作答
- 能力包含：网页搜索（标题、URL、摘要）、按站点和发布日期筛选、把网页读成干净的 Markdown
- 触发条件：用户问到新闻、最新版本、价格、政策、论文、文档、公司信息等模型训练数据之外或可能过时的内容；用户要求"搜一下""查一下""给出处"

## 使用方式

两个脚本都在 `scripts/` 目录下：`search.py` 搜索，`fetch.py` 读取网页。

### 输入

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| query | string | 是 | 自然语言查询，描述理想的网页，而不是零散关键词 |
| --site | string | 否 | 只搜一个站点，例如 `arxiv.org` |
| --published-after | string | 否 | 发布日期下限，`YYYY-MM-DD` |
| --published-before | string | 否 | 发布日期上限，`YYYY-MM-DD` |
| --max-results | int | 否 | 返回条数 1-50，默认 10 |
| --json | flag | 否 | 输出原始 JSON |

读取网页：`scripts/fetch.py <url>`，可选 `--max-chars`（默认 20000）和 `--json`。

### 输出

搜索结果为编号列表，每条包含标题、URL 和最多 400 字的摘要：

```
1. <标题>
   <URL>
   <摘要>
```

`--json` 时输出接口原始返回：

```json
{
  "results": [
    {"title": "...", "url": "https://...", "snippet": "...", "acquired_at": "..."}
  ]
}
```

## 核心逻辑

先搜索，再读原文，最后带出处作答。

### 步骤 1: 搜索

```bash
python3 scripts/search.py "欧盟 AI 法案 2025 年生效时间表"
```

查询写成一句完整的话。时效性强的问题加 `--published-after`，只要某个站点的内容加 `--site`。宽泛的问题拆成几个聚焦的查询分别搜索。

### 步骤 2: 读取原文

摘要只是线索。依赖某条结论之前，先读取最相关的一两个网页：

```bash
python3 scripts/fetch.py "https://eur-lex.europa.eu/eli/reg/2024/1689/oj"
```

### 步骤 3: 带出处作答

根据读到的原文回答，在结论后附上来源 URL。来源之间有冲突时，优先采用官方或一手来源，并说明分歧。

## 注意事项

- 免 Key：脚本调用 `https://api.keenable.ai/v1/search/public` 和 `/v1/fetch/public`，请求里带 `X-Keenable-Title: anbeime-skill` 作为应用标识，无需注册
- 频率限制：免 Key 每个 IP 每秒 10 次、每小时 1000 次；遇到 429 稍等再试。需要更高额度时在 [keenable.ai](https://keenable.ai) 获取 API Key 并设置环境变量 `KEENABLE_API_KEY`，脚本会自动改用带 Key 的接口
- 发送的内容：只有查询文本（或要读取的 URL）和应用标识；设置了 Key 时附带 Key
- 无依赖：仅用 Python 3 标准库（`urllib`），不需要 `pip install`
- 也可以用 MCP：支持 MCP 的客户端可直接添加免 Key 的 `https://api.keenable.ai/mcp-public`（Streamable HTTP），工具为 `search_web_pages` 和 `fetch_page_content`

## 示例

以下命令在技能目录下执行。

### 示例 1: 新闻动态

**输入:**
```
python3 scripts/search.py "DeepSeek 最新模型发布" --published-after 2026-10-01 --max-results 5
```

**输出:**
```
1. <新闻标题>
   https://...
   <摘要>
2. ...
```

### 示例 2: 指定站点查论文并读取原文

**输入:**
```
python3 scripts/search.py "diffusion models for inverse problems" --site arxiv.org --max-results 5
python3 scripts/fetch.py "https://arxiv.org/abs/<论文编号>"
```

**输出:**
```
# <论文标题>
https://arxiv.org/abs/<论文编号>

<论文页面的 Markdown 正文>
```

### 示例 3: 查官方文档

**输入:**
```
python3 scripts/search.py "Python asyncio TaskGroup 官方文档" --site docs.python.org
```

**输出:**
```
1. asyncio.TaskGroup ...
   https://docs.python.org/3/library/asyncio-task.html
   <摘要>
```
