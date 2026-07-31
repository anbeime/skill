# @cloudbase/agent-adapter-langchain

Adapter that wraps LangChain's `createAgent()` as an AG-UI compatible agent. Provides `LangchainAgent` wrapper class and `clientTools()` middleware for client tools support.

## Basic Usage

```typescript
import { createAgent as createLangchainAgent } from "langchain";
import { MemorySaver } from "@langchain/langgraph";
import { ChatOpenAI } from "@langchain/openai";
import { LangchainAgent, clientTools } from "@cloudbase/agent-adapter-langchain";

const model = new ChatOpenAI({ model: "gpt-4o" });
const checkpointer = new MemorySaver();

const lcAgent = createLangchainAgent({
  model,
  checkpointer,
  middleware: [clientTools()],
});

const agent = new LangchainAgent({ agent: lcAgent });
```

## Checkpointer (Required)

`LangchainAgent` requires the agent to be created with a checkpointer.

### MemorySaver (Development)

```typescript
import { MemorySaver } from "@langchain/langgraph";

const lcAgent = createLangchainAgent({
  model,
  checkpointer: new MemorySaver(),
  middleware: [clientTools()],
});
```

### CloudBaseSaver (Production)

Persistent storage using Tencent CloudBase document database. On CloudBase cloud function/cloudrun, requests are authenticated - extract user ID from the JWT in Authorization header.

```typescript
import { run } from "@cloudbase/agent-server";
import { LangchainAgent, clientTools } from "@cloudbase/agent-adapter-langchain";
import { CloudBaseSaver } from "@cloudbase/agent-adapter-langgraph";
import { createAgent as createLangchainAgent } from "langchain";
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

    const lcAgent = createLangchainAgent({
      model,
      checkpointer,
      middleware: [clientTools()],
    });

    return { agent: new LangchainAgent({ agent: lcAgent }) };
  },
  port: 9000,
});
```

## With @cloudbase/agent-server

```typescript
import { run } from "@cloudbase/agent-server";

run({
  createAgent: () => ({ agent }),
  port: 9000,
});
```

## clientTools() Middleware

Enables client-defined tools in your LangChain agent:

- **Injects client tools** - Adds client tools to the LLM's available tool list
- **Routes to END** - When a client tool is called, skips ToolNode and routes to END so client can execute
