---
name: cloudbase-agent-python
description: "Build production-ready AI agent backends using the CloudBase Agent Python SDK — create agents with LangGraph/CrewAI/LlamaIndex, serve them via FastAPI with AG-UI protocol streaming + OpenAI-compatible endpoints, add tools (bash, filesystem, MCP, code execution), memory (in-memory, TDAI, MySQL, MongoDB), observability (OpenTelemetry/Langfuse), and middleware (auth, logging). Use this skill when the user wants to create an AI agent server, build a chatbot backend, set up human-in-the-loop workflows, integrate MCP tools, add agent observability, or deploy an agent API — even if they don't explicitly mention 'CloudBase Agent.'"
alwaysApply: true
---

# CloudBase Agent Python SDK

Build production-ready AI agent backends with multi-framework support, streaming
protocol, rich tools, persistent memory, and full observability.

> **Note:** This skill is for **Python** projects only.

## When to use this skill

Use this skill for **AI agent development** when you need to:

- Deploy AI agents as HTTP services with AG-UI protocol support
- Build agent backends using LangGraph, CrewAI, or LlamaIndex frameworks
- Create custom agent adapters implementing the AbstractAgent interface
- Understand AG-UI protocol events and message streaming
- Build production-ready agent servers with FastAPI

**Do NOT use for:**
- Simple AI model calling without agent capabilities (use `ai-model-*` skills)
- CloudBase cloud functions (use `cloud-functions` skill)
- CloudRun backend services without agent features (use `cloudrun-development` skill)
- TypeScript/JavaScript agent projects (use `cloudbase-agent` skill, refer to the `ts/` sub-directory)

## How to use this skill (for a coding agent)

1. **Choose the right adapter**
   - Use LangGraph adapter for stateful, graph-based workflows
   - Use CrewAI adapter for multi-agent collaboration patterns
   - Build custom adapter for specialized agent logic

2. **Write agent code** — follow the adapter-specific doc from the Routing table

3. **Deploy the agent server** — follow the **blocking deployment pipeline** in [agent-deployment](agent-deployment.md)

## Routing (Execution Order)

> ⚠️ **Deployment is a BLOCKING 4-step pipeline.** Steps marked ✅ BLOCKING
> must be completed AND verified before proceeding to the next step.
> Do NOT call `manageAgent` until all blocking steps pass.

| Step | Task | Document | Blocking? |
|------|------|----------|-----------|
| 0 | **Choose adapter & write agent code** | See "Adapter Selection" below | — |
| 1 | **Ensure Python 3.10** | [agent-deployment](agent-deployment.md) § Step 1 | ✅ BLOCKING |
| 2 | **Build env/ (one-shot)** | [agent-deployment](agent-deployment.md) § Step 2 | ✅ BLOCKING |
| 3 | **Verify env/ integrity** | [agent-deployment](agent-deployment.md) § Step 3 | ✅ BLOCKING |
| 4 | **Deploy with manageAgent** | [agent-deployment](agent-deployment.md) § Step 4 | — |

### Adapter Selection (Step 0)

| Framework | Read | Install |
|-----------|------|---------|
| LangGraph (stateful graphs) | [adapter-langgraph](adapter-langgraph.md) | `cloudbase-agent-langgraph` |
| CrewAI (multi-agent crews) | [adapter-development](adapter-development.md) | `cloudbase-agent-crewai` |
| Coze platform | [adapter-coze](adapter-coze.md) | `cloudbase-agent-coze` |
| Custom / raw FastAPI | [server-quickstart](server-quickstart.md) + [adapter-development](adapter-development.md) | `cloudbase-agent-server` |

### Additional References (read on demand, NOT required for deployment)

| Task | Read |
|------|------|
| Server setup, middleware, multi-agent, CORS | [server-quickstart](server-quickstart.md) |
| Authentication and user context | [authentication](authentication.md) |

## Quick Start (Framework-Agnostic)

**Prerequisites:** Python >= 3.10 is required.

**1. Install dependencies (pick ONE adapter):**

```bash
# Option A: LangGraph-based agent
pip install cloudbase-agent-langgraph

# Option B: CrewAI-based agent
pip install cloudbase-agent-crewai

# Option C: Custom / minimal
pip install cloudbase-agent-server
```

**2. Create server entry point:**

```python
# server.py — this pattern works with ANY adapter
import os
from dotenv import load_dotenv
load_dotenv()

from cloudbase_agent.server import AgentServiceApp, AgentCreatorResult

# Import your agent (framework-specific, see adapter docs)
# from agents.chat.agent import create_my_agent

def create_agent() -> AgentCreatorResult:
    agent = create_my_agent()  # Your agent factory
    return {"agent": agent}

app = AgentServiceApp()
app.set_cors_config(allow_origins=["*"])

if __name__ == "__main__":
    port = int(os.environ.get("SCF_RUNTIME_PORT", "9000"))
    app.run(create_agent, port=port, host="0.0.0.0")
```

**3. Deploy to CloudBase:**

Follow the **4-step deployment pipeline** in [agent-deployment](agent-deployment.md).

---

## Architecture

```
Client (React / MiniProgram / curl)
   │  HTTP POST + SSE streaming
   ▼
┌─────────────────────────────────────────────┐
│  AgentServiceApp (FastAPI)                   │
│  ├─ /send-message      ← AG-UI SSE         │
│  ├─ /chat/completions  ← OpenAI-compat      │
│  └─ Middleware chain (onion model)           │
├─────────────────────────────────────────────┤
│  Agent Layer                                 │
│  ├─ LangGraphAgent  ├─ CrewAIAgent          │
│  ├─ LlamaIndexAgent ├─ CozeAgent/DifyAgent  │
│  └─ BaseAgent (extend for custom)           │
├──────────────────┬──────────────────────────┤
│  Tools           │  Storage                  │
│  Bash/FS/Code/MCP│  Memory + LongTermMemory  │
├─────────────────────────────────────────────┤
│  Observability (OpenTelemetry + Langfuse)    │
└─────────────────────────────────────────────┘
```

## Installation

CloudBase Agent Python SDK is published to PyPI as separate packages. **Note: PyPI package names use hyphens (`cloudbase-agent-*`), and Python imports use the same namespace (`cloudbase_agent.*`)**.

```bash
# Core + Server + LangGraph (most common)
pip install cloudbase-agent-langgraph

# Individual packages
pip install cloudbase-agent-core        # Core framework
pip install cloudbase-agent-server      # FastAPI server
pip install cloudbase-agent-langgraph   # LangGraph integration
pip install cloudbase-agent-tools       # Tool system
pip install cloudbase-agent-storage     # Memory/Storage
pip install cloudbase-agent-observability  # OpenTelemetry/Langfuse
pip install cloudbase-agent-coze        # Coze platform
pip install cloudbase-agent-crewai      # CrewAI integration
```

**Import Note**: All packages share the `cloudbase_agent` namespace:
```python
# After installing cloudbase-agent-langgraph, import from cloudbase_agent
from cloudbase_agent.langgraph import LangGraphAgent
from cloudbase_agent.server import AgentServiceApp
from cloudbase_agent.tools import create_bash_tool
```

## Reference Documents

Based on what the user needs, read the corresponding reference document.
**Only read the relevant reference — don't load all of them.**

| User Need | Reference | What It Covers |
|-----------|-----------|---------------|
| **Deploying agent to CloudBase** | Read [agent-deployment](agent-deployment.md) | **manageAgent MCP tool (MUST USE)**, 4-step blocking pipeline, Python 3.10, env/ build, verification |
| Server setup, deployment, middleware, multi-agent, CORS | Read `references/server.md` | AgentServiceApp 3 deployment methods, middleware (generator/yield/onion model), multi-agent server, Agent Creator pattern, health checks |
| LangGraph agent, callbacks, tool proxy, HITL, checkpoints | Read `references/langgraph.md` | LangGraphAgent constructor, AgentCallback protocol, ToolProxy, human-in-the-loop with interrupt(), TDAICheckpointSaver, client-defined tools |
| Tools: bash, filesystem, code execution, MCP, custom tools | Read `references/tools.md` | create_bash_tool, 8 file tools, code executors, MCPToolkit/CloudBaseMCPServer, @tool decorator, BaseTool, framework adapters |
| Memory, persistence, short/long-term, MySQL, MongoDB | Read `references/storage.md` | InMemoryMemory, TDAIMemory, MySQLMemory, MongoDBMemory, TDAILongTermMemory, Mem0LongTermMemory, LangGraph checkpoint |
| Tracing, monitoring, Langfuse, OpenTelemetry | Read `references/observability.md` | ConsoleTraceConfig, OTLPTraceConfig, setup_observability, env vars, manual observation spans |
| Common patterns, JWT auth, MCP integration, production | Read `references/recipes.md` | JWT middleware, MCP + LangGraph, production deployment, adding tools to agents, client-defined tools |

## Key Imports Quick Reference

```python
# Server
from cloudbase_agent.server import AgentServiceApp, AgentCreatorResult
from cloudbase_agent.server import create_send_message_adapter, create_openai_adapter
from cloudbase_agent.server import RunAgentInput, OpenAIChatCompletionRequest

# Agents
from cloudbase_agent.langgraph import LangGraphAgent
from cloudbase_agent.crewai import CrewAIAgent

# Tools
from cloudbase_agent.tools import create_bash_tool, create_read_tool, create_write_tool
from cloudbase_agent.tools import MCPToolkit, CloudBaseMCPServer, CloudBaseTool
from cloudbase_agent.tools import tool, BaseTool  # custom tools

# Storage
from cloudbase_agent.storage import InMemoryMemory, TDAIMemory
from cloudbase_agent.storage import TDAILongTermMemory, Mem0LongTermMemory
from cloudbase_agent.langgraph import TDAICheckpointSaver, TDAIStore

# Observability
from cloudbase_agent.observability import ConsoleTraceConfig, OTLPTraceConfig, setup_observability

# Schemas
from cloudbase_agent.schemas import Message, MessageRole, StreamEvent, EventType
```

## Project Structure Convention

```
my-agent-project/
├── agents/
│   ├── agentic_chat/agent.py      # build_workflow() → agent instance
│   ├── human_in_the_loop/agent.py
│   └── __init__.py
├── server.py                       # Main entry: AgentServiceApp().run(...)
├── scf_bootstrap                   # CloudBase startup script (required for deployment)
├── .env                            # OPENAI_API_KEY, etc.
└── requirements.txt
```

## Environment Variables

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key |
| `AUTO_TRACES_STDOUT` | Enable console tracing (`true`) |
| `LANGFUSE_PUBLIC_KEY` / `LANGFUSE_SECRET_KEY` | Langfuse keys |
| `TDAI_ENDPOINT` / `TDAI_API_KEY` | TDAI memory/checkpoint endpoint |
| `SCF_RUNTIME_PORT` | CloudBase runtime port (set automatically during deployment) |

## Key Design Decisions

1. **Agent Creator Pattern**: Every request creates a fresh agent via factory function. Supports cleanup callbacks for resource release.
2. **Dual Protocol**: Every agent supports both AG-UI native (SSE + rich events) and OpenAI-compatible (`/chat/completions`).
3. **Middleware = Generator**: Use `yield` — pre-yield = pre-processing, post-yield = post-processing (onion model).
4. **Namespace Package**: `cloudbase_agent` spans multiple PyPI packages (cloudbase-agent-core, cloudbase-agent-server, cloudbase-agent-langgraph, etc.). PyPI names use hyphens, but all imports use `from cloudbase_agent.xxx import ...`.
5. **Observability Auto-Integration**: Install `cloudbase-agent-observability` and tracing works automatically — zero config needed.
6. **Deploy with manageAgent**: Always use the `manageAgent` MCP tool for CloudBase deployment. Follow the **4-step blocking pipeline** in [agent-deployment](agent-deployment.md).
