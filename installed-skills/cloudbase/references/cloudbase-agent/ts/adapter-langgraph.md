# @cloudbase/agent-adapter-langgraph

Adapter that wraps a compiled LangGraph `StateGraph` workflow as an AG-UI compatible agent. Provides `ClientStateAnnotation` with pre-wired `messages` and `client.tools` fields for seamless AG-UI protocol integration.

## Installation

```bash
npm install @cloudbase/agent-adapter-langgraph@latest @langchain/langgraph @langchain/openai
```

**Important:** Always use `@latest` for `@cloudbase/agent-*` packages to get the newest stable releases. Do NOT specify version ranges like `^1.0.0` or exact versions like `1.0.0`, as the package versions may not follow semantic versioning expectations and such versions may not exist.

For projects requiring version locking, install first with `@latest`, then commit `package-lock.json`.

## Exports

```typescript
import {
  LanggraphAgent,
  ClientStateAnnotation,
  ClientState,
  CloudBaseSaver  // Tencent CloudBase checkpointer
} from "@cloudbase/agent-adapter-langgraph";
```

## Basic Usage

```typescript
import { LanggraphAgent } from "@cloudbase/agent-adapter-langgraph";

const agent = new LanggraphAgent({
  compiledWorkflow: graph,  // compiled StateGraph (required)
  logger: myLogger,         // optional
});
```

## Checkpointer (Required)

`LanggraphAgent` requires the workflow to be compiled with a checkpointer.

### MemorySaver (Development)

```typescript
import { MemorySaver } from "@langchain/langgraph";

const graph = workflow.compile({ checkpointer: new MemorySaver() });
```

### CloudBaseSaver (Production)

Persistent storage using Tencent CloudBase document database. On CloudBase cloud function/cloudrun, requests are authenticated - extract user ID from the JWT in Authorization header.

```typescript
import { run } from "@cloudbase/agent-server";
import { CloudBaseSaver, LanggraphAgent } from "@cloudbase/agent-adapter-langgraph";
import tcb from "@cloudbase/node-sdk";

const app = tcb.init({ env: process.env.CLOUDBASE_ENV_ID });

run({
  createAgent: ({ request }) => {
    // Extract user ID from JWT (sub field)
    const token = request.headers.get("Authorization")?.slice(7);
    const payload = JSON.parse(atob(token.split(".")[1]));
    const userId = payload.sub;

    const checkpointer = new CloudBaseSaver({
      db: app.database(),
      userId,  // Multi-tenant isolation
    });

    const graph = workflow.compile({ checkpointer });
    return { agent: new LanggraphAgent({ compiledWorkflow: graph }) };
  },
  port: 9000,
});
```

## Client Tools

Client tools are tools defined by the client, not the server. They let the agent request actions only the client can perform (e.g., show modal, navigate, access local storage). The flow:

1. **Client** defines tools with handlers and sends them in request
2. **Server** binds client tools alongside server tools, LLM can call any
3. **Server** detects client tool call → routes to END (doesn't execute)
4. **Client** receives `TOOL_CALL_*` events, executes handler locally
5. **Client** sends tool result back, agent resumes

### Server Side: Bind and Route

```typescript
import { ClientState } from "@cloudbase/agent-adapter-langgraph";

// 1. Bind client tools to model (alongside server tools)
async function chatNode(state: ClientState) {
  const clientTools = state.client?.tools || [];
  const modelWithTools = model.bindTools([...clientTools, ...serverTools]);
  // ...
}

// 2. Route client tool calls to END (let client handle)
function shouldContinue(state: ClientState): "tools" | "end" {
  const lastMessage = state.messages[state.messages.length - 1];
  if (lastMessage.tool_calls?.length > 0) {
    const hasServerToolCall = lastMessage.tool_calls.some(tc => serverToolNames.has(tc.name));
    if (hasServerToolCall) return "tools";  // Server executes
  }
  return "end";  // Client tool or no tool → end, client handles
}
```

## Complete Workflow Pattern

```typescript
import { StateGraph, START, END, Command } from "@langchain/langgraph";
import { ClientStateAnnotation, ClientState } from "@cloudbase/agent-adapter-langgraph";
import { MemorySaver } from "@langchain/langgraph";
import { ChatOpenAI } from "@langchain/openai";
import { SystemMessage } from "@langchain/core/messages";
import { RunnableConfig } from "@langchain/core/runnables";

async function chatNode(state: ClientState, config?: RunnableConfig) {
  const model = new ChatOpenAI({ model: "gpt-4o" });
  const modelWithTools = model.bindTools([...(state.client?.tools || [])], {
    parallel_tool_calls: false,  // Recommended: avoid race conditions
  });

  const response = await modelWithTools.invoke([
    new SystemMessage({ content: "You are a helpful assistant." }),
    ...state.messages,
  ], config);

  return new Command({ goto: END, update: { messages: [response] } });
}

const workflow = new StateGraph(ClientStateAnnotation)
  .addNode("chat_node", chatNode)
  .addEdge(START, "chat_node");

export const graph = workflow.compile({ checkpointer: new MemorySaver() });
```

## With @cloudbase/agent-server

Deploy your LangGraph workflow as an HTTP endpoint that speaks the AG-UI protocol. Clients can connect via SSE to stream events.

```typescript
import { run } from "@cloudbase/agent-server";
import { LanggraphAgent } from "@cloudbase/agent-adapter-langgraph";

run({
  createAgent: () => ({
    agent: new LanggraphAgent({ compiledWorkflow: graph })
  }),
  port: 3000
});
```
