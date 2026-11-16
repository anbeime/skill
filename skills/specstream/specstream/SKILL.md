---
name: specstream
description: Live web search, webpage content extraction, and remote MCP tools via the SpecStream API, including drop-in routes for Tavily, Exa, Brave, Serper, and SearXNG.
version: 1.0.0
author: SpecStream
tags: [web-search, web-extract, mcp, research, specstream]
dependencies: [python>=3.8, curl]
license: MIT
---

# SpecStream Web Data Skill

SpecStream provides live web search (`GET /v1/web-search`), webpage content extraction (`POST /v1/extract`), structured Deep Search, research reports, a remote MCP server (`https://api.specstream.ai/mcp`), and drop-in endpoints compatible with Tavily, Exa, Brave, Serper, and SearXNG.

## 任务目标

本技能帮助 AI Agent 按需检索实时网页信息、提取网页正文与元数据，或在已有搜索客户端中通过切换 Base URL 无缝迁移至 SpecStream。

- 实时网页搜索: 通过 `GET /v1/web-search` 获取最新网页结果，支持快速模式 (`speed=fast`) 与默认模式。
- 网页正文提取: 通过 `POST /v1/extract` 批量读取 1 到 20 个 URL，返回清洗后的正文、标题、发布时间、邮箱与读取来源。
- 兼容迁移路线: 原生兼容 Tavily、Exa、Brave、Serper、SearXNG 等接口格式，仅需替换请求地址与密钥。
- 远程 MCP 接入: 通过 `https://api.specstream.ai/mcp` (Streamable HTTP) 直接调用搜索与研究工具。
- 触发条件: 当用户需要查询实时网页事实、抓取指定网页正文、将现有搜索配置切换到 SpecStream 或连接 SpecStream MCP 时触发。

## 使用方式

调用付费接口前需读取环境变量 `SPECSTREAM_API_KEY`。若未设置密钥，不发起付费请求，可先查看免密钥的公开文档与方言列表，并提示用户设置密钥。

### 输入

调用时根据任务类型提供查询词、目标 URL 列表或兼容接口类型。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `q` | string | 搜索时必填 | 搜索关键词或自然语言问题，1 到 2000 字符 |
| `speed` | string | 否 | 搜索档位，`fast` ($1/1,000) 或默认 ($5/1,000) |
| `num` | integer | 否 | 返回结果条数，默认最多 10 条 |
| `urls` | list[string] | 提取时必填 | 待读取的公开 `http`/`https` 地址列表，单次 1 到 20 个 |
| `format` | string | 否 | 提取输出格式：`markdown`、`text` 或 `html` |
| `SPECSTREAM_API_KEY` | env var | 付费调用必填 | Bearer Token；未配置时不执行付费请求 |

### 输出

接口统一返回 `{"data": ...}` JSON 结构，包含结果条目、`request_id`、`took_ms` 与实际计费金额 `price_usd`。

```json
{
  "data": {
    "results": [
      {
        "title": "Example Page",
        "url": "https://example.com",
        "snippet": "Extracted summary from the live page."
      }
    ],
    "request_id": "req_01",
    "took_ms": 420,
    "price_usd": 0.001
  }
}
```

## 核心逻辑

执行时按以下步骤选择免密钥检查或正式 API 调用。

### 步骤 1: 检查凭证与只读元数据

先检查 `SPECSTREAM_API_KEY` 是否存在。若未配置密钥，仅允许读取公开文档 `https://specstream.ai/agents.md` 或免密钥方言目录 `GET https://api.specstream.ai/v1/search-dialects`，不执行任何会产生费用的请求，并告知用户在 `https://specstream.ai/workspace` 获取密钥。

### 步骤 2: 选择合适端点与计费档位

根据任务选择对应接口，避免不必要的开销：

1. 单一事实或快速检索: 调用 `GET https://api.specstream.ai/v1/web-search?q=...&speed=fast` ($1/1,000 次，最多 10 条结果)；需要更高精度时省略 `speed=fast` 使用默认档 ($5/1,000 次)。
2. 已知 URL 抓取正文: 调用 `POST https://api.specstream.ai/v1/extract` ($0.80/1,000 页，无正文页不计费)。
3. 已有搜索客户端迁移: 仅修改 Base URL 为 `https://api.specstream.ai` 对应前缀，沿用原请求体与响应解析逻辑。
4. 代理工具直连: 连接 MCP 地址 `https://api.specstream.ai/mcp`，使用 OAuth 或 `Authorization: Bearer $SPECSTREAM_API_KEY` 后通过 `tools/list` 发现工具。

### 步骤 3: 发送请求与安全重试

在并发或网络抖动场景下，请求头可携带 `Idempotency-Key` (最长 128 字符)，确保同一请求不会重复扣费。收到 `503` 时遵循响应头 `Retry-After` 等待后重试。

## 注意事项

- 未配置 `SPECSTREAM_API_KEY` 时，不得伪造凭证或尝试付费调用；公开端点 `/v1/search-dialects` 无需密钥且不计费。
- 切勿在代码、日志或技能文档中硬编码真实 API Key，一律使用环境变量 `$SPECSTREAM_API_KEY`。
- 提取接口单次最多传入 20 个 URL，请求体不超过 20 MB；无正文或被拦截的页面按规范不计费。
- 完整参数、错误码与 SDK 说明以官方文档 `https://specstream.ai/agents.md` 为准。

## 示例

以下示例均以环境变量 `SPECSTREAM_API_KEY` 传入凭证，未设置密钥时请勿直接执行付费请求。

### 示例 1: 快速网页搜索与正文提取

**输入:**

```bash
curl -sS "https://api.specstream.ai/v1/web-search?q=python+3.13+release+notes&speed=fast&num=5" \
  -H "Authorization: Bearer $SPECSTREAM_API_KEY"
```

```bash
curl -sS -X POST "https://api.specstream.ai/v1/extract" \
  -H "Authorization: Bearer $SPECSTREAM_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://docs.python.org/3/whatsnew/3.13.html"], "format": "markdown"}'
```

**输出:**

```json
{
  "data": {
    "results": [
      {
        "url": "https://docs.python.org/3/whatsnew/3.13.html",
        "status": "ok",
        "title": "What's New In Python 3.13",
        "read_from": "live",
        "text": "Summary of release highlights..."
      }
    ],
    "price_usd": 0.0008
  }
}
```

### 示例 2: 替换现有搜索 SDK 与免密钥查看方言列表

**输入:**

```bash
curl -sS "https://api.specstream.ai/v1/search-dialects"
```

```python
from tavily import TavilyClient
import os

client = TavilyClient(
    api_key=os.environ["SPECSTREAM_API_KEY"],
    api_base_url="https://api.specstream.ai/tavily",
)
results = client.search("latest PostgreSQL LTS release", max_results=5)
```

**输出:**

```json
{
  "results": [
    {
      "title": "PostgreSQL: Versioning Policy",
      "url": "https://www.postgresql.org/support/versioning/",
      "content": "Current supported major versions and end-of-life dates..."
    }
  ]
}
```
