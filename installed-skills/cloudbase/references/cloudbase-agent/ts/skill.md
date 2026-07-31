---
name: cloudbase-agent
description: "Build and deploy AI agents with Cloudbase Agent (TypeScript), a TypeScript SDK implementing the AG-UI protocol. Use when: (1) deploying agent servers with @cloudbase/agent-server, (2) using LangGraph adapter with ClientStateAnnotation, (3) using LangChain adapter with clientTools(), (4) building custom adapters that implement AbstractAgent, (5) understanding AG-UI protocol events, (6) building web UI clients with @ag-ui/client, (7) building WeChat Mini Program UIs with @cloudbase/agent-ui-miniprogram."
alwaysApply: true
---

# Cloudbase Agent (TypeScript)

TypeScript SDK for deploying AI agents as HTTP services using the AG-UI protocol.

> **Note:** This skill is for **TypeScript/JavaScript** projects only.

## When to use this skill

Use this skill for **AI agent development** when you need to:

- Deploy AI agents as HTTP services with AG-UI protocol support
- Build agent backends using LangGraph or LangChain frameworks
- Create custom agent adapters implementing the AbstractAgent interface
- Understand AG-UI protocol events and message streaming
- Build web UI clients that connect to AG-UI compatible agents
- Build WeChat Mini Program UIs for AI agent interactions

**Do NOT use for:**
- Simple AI model calling without agent capabilities (use `ai-model-*` skills)
- CloudBase cloud functions (use `cloud-functions` skill)
- CloudRun backend services without agent features (use `cloudrun-development` skill)

## How to use this skill (for a coding agent)

1. **Choose the right adapter**
   - Use LangGraph adapter for stateful, graph-based workflows
   - Use LangChain adapter for chain-based agent patterns
   - Build custom adapter for specialized agent logic

2. **Deploy the agent server**
   - Use `@cloudbase/agent-server` to expose HTTP endpoints
   - Configure CORS, logging, and observability as needed
   - **Prefer deploying to CloudBase using `manageAgent` MCP tool** (see [agent-deployment](agent-deployment.md))
   - **Before deploy, read Dependency Alignment Policy in [agent-deployment](agent-deployment.md) to avoid cloud build dependency errors**

3. **Build the UI client**
   - Use `@ag-ui/client` for web applications
   - Use `@cloudbase/agent-ui-miniprogram` for WeChat Mini Programs
   - Connect to the agent server's `/send-message` or `/agui` endpoints

4. **Follow the routing table below** to find detailed documentation for each task

## Routing

| Task | Read |
|------|------|
| Deploy agent to CloudBase (**read this first**) | [agent-deployment](agent-deployment.md) |
| Deploy agent server (@cloudbase/agent-server) | [server-quickstart](server-quickstart.md) |
| Use LangGraph adapter | [adapter-langgraph](adapter-langgraph.md) |
| Use LangChain adapter | [adapter-langchain](adapter-langchain.md) |
| Build custom adapter | [adapter-development](adapter-development.md) |
| Understand AG-UI protocol | [agui-protocol](agui-protocol.md) |
| Build UI client (Web or Mini Program) | [ui-clients](ui-clients.md) |
| Deep-dive @cloudbase/agent-ui-miniprogram | [ui-miniprogram](ui-miniprogram.md) |

## Quick Start

**Prerequisites:** Node.js >= 20 is required.

**1. Install dependencies:**

```bash
npm install @cloudbase/agent-server@latest @cloudbase/agent-adapter-langgraph@latest
```

**Critical:** Always use `@latest` for all `@cloudbase/agent-*` packages. For dependency version rules, see [Dependency Alignment Policy](agent-deployment.md#dependency-alignment-policy-critical) in agent-deployment.md.

**2. Create and run your agent:**

```typescript
import { run } from "@cloudbase/agent-server";
import { LanggraphAgent } from "@cloudbase/agent-adapter-langgraph";

run({
  createAgent: () => ({ agent: new LanggraphAgent({ workflow }) }),
  port: 9000,
});
```


