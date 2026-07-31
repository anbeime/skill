# Agent Deployment Guide

## Core Principle

**Always use the `manageAgent` MCP tool to deploy Agent services.**

It natively supports SSE streaming, session persistence, and Node.js 20 runtime — purpose-built for Agent scenarios.

Do **NOT** use `createFunction` or `manageCloudRun` for Agent deployment.

## Why HTTP Cloud Functions First

| Dimension | HTTP Cloud Functions | CloudRun |
|-----------|---------------------|----------|
| SSE Streaming | ✅ Native support | ✅ Supported |
| WebSocket | ✅ Native support | ✅ Supported |
| Deployment Complexity | Low (no Dockerfile needed) | High (container config required) |
| Cost | Pay-per-invocation, scales to zero | Pay-per-instance-hour |
| Cold Start | Yes, mitigated with provisioned instances | Yes, mitigated with min instances |
| Supported Runtimes | Node.js, Python | Any |

## Deployment Steps (HTTP Cloud Functions)

1. Ensure project has `scf_bootstrap` startup script (see below)
2. Deploy using `manageAgent` MCP tool with `runtime="Nodejs20.19"`:

```
manageAgent(action="create", runtime="Nodejs20.19", installDependency=true, targetPath="...")
```

3. Set environment variables (OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_MODEL, etc.)
4. Verify SSE connectivity

> ⚠️ **CRITICAL**: Always set `installDependency=true` to let cloud install dependencies automatically. Without this, you'll get `ERR_MODULE_NOT_FOUND` errors.

> For server code and adapter usage, see [server-quickstart](server-quickstart.md) and [adapter-langgraph](adapter-langgraph.md).

## Dependency Alignment Policy (CRITICAL)

**Always use `latest` for `@cloudbase/agent-*` and `@langchain/*` packages. Never specify version ranges.**

**Reference example** (adapt based on your actual dependencies):

```json
{
  "dependencies": {
    "@cloudbase/agent-server": "latest",
    "@cloudbase/agent-adapter-langgraph": "latest",
    "@langchain/langgraph": "latest",
    "@langchain/openai": "latest"
  }
}
```

> **Why?** `@cloudbase/agent-adapter-langgraph` has peer dependency on specific `@langchain/core` versions. Specifying version ranges like `^0.3.44` causes `[ResourceNotFound.Package] Dependency error` during cloud build.

---

## Node.js Runtime Version

**Always select Node.js 20 runtime** (`runtime="Nodejs20"`):

- Full compatibility with all `@cloudbase/agent-*` packages
- ES Module support (`"type": "module"` in package.json)
- Stable and well-tested on the CloudBase platform

Do **NOT** use Node.js 16 or earlier — many SDK features require Node.js >= 20.

## Startup Script (scf_bootstrap)

The startup script must be named `scf_bootstrap` (no file extension), placed in the project root, and have executable permissions:

```bash
#!/bin/sh
node src/index.js
```

```bash
chmod +x scf_bootstrap
```

> **IMPORTANT**: The `scf_bootstrap` script should be minimal — just start the Node.js application. Do NOT include `npm install` in this script. Dependencies are handled during deployment.

> **NOTE**: Use `#!/bin/sh` (not `#!/bin/bash`) for maximum compatibility. The entry point should match your actual server entry file.

## Port & CORS

- Your server **should** listen on port `9000` (the default for CloudBase Agent)
- In production (CloudBase), CORS is handled by the API gateway — no need to enable it in code
- For local development, conditionally enable CORS via an environment variable (e.g., `ENABLE_CORS=true`)

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `OPENAI_API_KEY` | ✅ | OpenAI API key or compatible service key |
| `OPENAI_BASE_URL` | ✅ | API base URL, e.g. `https://api.openai.com/v1` |
| `OPENAI_MODEL` | ✅ | Model name, e.g. `gpt-4o` or `gpt-3.5-turbo` |
| `LOG_LEVEL` | ❌ | Log level: `trace`/`debug`/`info`/`warn`/`error`/`fatal` (default: `info`) |
| `ENABLE_CORS` | ❌ | Set to `true` to enable CORS (local dev only) |

## When to Use CloudRun Instead

Despite HTTP Cloud Functions being preferred, use CloudRun in these cases:

- Custom Docker image required (special system-level dependencies like FFmpeg, Chromium, etc.)
- Resource requirements exceed Cloud Function limits
- Persistent local file storage needed
- Need to install native C extensions that require specific OS packages

For CloudRun deployment, use a Dockerfile:

```dockerfile
FROM node:20-alpine
WORKDIR /app

COPY package*.json ./
RUN npm i --production

COPY src ./src

ENV NODE_ENV=production
EXPOSE 9000

CMD ["node", "src/index.js"]
```

## Summary

| Decision | Choice |
|----------|--------|
| **Deployment tool** | `manageAgent` MCP tool (MUST USE) |
| **Node.js runtime** | Node.js 20.19 (MUST USE, `runtime="Nodejs20.19"`) |
| **Dependency install** | `installDependency=true` (MUST SET, or get `ERR_MODULE_NOT_FOUND`) |
| **Default platform** | HTTP Cloud Functions |
| **Fallback platform** | CloudRun (only for special requirements) |
| **Startup script** | `scf_bootstrap` — `#!/bin/sh` + `node src/index.js` |
| **Port** | Listen on port `9000` |
| **CORS** | Production uses API gateway; local dev via `ENABLE_CORS` env var |
| **Module system** | ES Modules (`"type": "module"` in package.json) |
