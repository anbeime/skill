# SpecStream (specstream)

SpecStream 实时网页数据引擎技能：提供高精度网页搜索、网页正文提取、远程 MCP 工具调用，以及兼容 Tavily、Exa、Brave、Serper、SearXNG 的免改代码替换端点。

## 核心能力

- **Search API (`GET https://api.specstream.ai/v1/web-search`)**: 支持快速档 (`speed=fast`, $1 / 1,000 次) 与默认档 ($5 / 1,000 次)，按返回结果计费。
- **Extract API (`POST https://api.specstream.ai/v1/extract`)**: 每次提取 1 到 20 个 URL ($0.80 / 1,000 页)，支持 `markdown` / `text` / `html` 格式，无正文页面不计费。
- **Remote MCP (`https://api.specstream.ai/mcp`)**: 基于 Streamable HTTP 的远程 MCP 服务，支持 OAuth 或 Bearer API Key 认证。
- **Drop-in 兼容端点**:
  - Tavily: `https://api.specstream.ai/tavily` (`POST /tavily/search`, `POST /tavily/extract`)
  - Exa: `https://api.specstream.ai/exa` (`POST /exa/search`, `POST /exa/contents`)
  - Brave: `https://api.specstream.ai` (`GET /res/v1/web/search`)
  - Serper: `https://api.specstream.ai/serper` (`POST /serper/search`)
  - SearXNG: `https://api.specstream.ai/searxng/<key>` (`GET /searxng/search?q=...&format=json`)

## 配置方式

在环境中使用 `SPECSTREAM_API_KEY`（可在 <https://specstream.ai/workspace> 创建并设置额度限制）：

```bash
export SPECSTREAM_API_KEY="your_api_key_here"
```

未配置密钥时，不会执行付费请求；可先通过免密钥端点查看支持的方言目录：

```bash
curl -sS "https://api.specstream.ai/v1/search-dialects"
```

## 参考文档

- Agent 完整接口说明: <https://specstream.ai/agents.md>
- 搜索 API: <https://specstream.ai/search-api>
- 提取 API: <https://specstream.ai/extract-api>
