# @cloudbase/agent-server

Deploy AG-UI compatible agents as HTTP servers.

## Installation

```bash
npm install @cloudbase/agent-server@latest
```

**Important:** Always use `@latest` for `@cloudbase/agent-*` packages. Do NOT use version ranges like `^1.0.0` or exact versions, as these versions may not exist. The packages do not follow traditional semantic versioning.

## Deployment Methods

### run() - Standalone

```typescript
import { run } from "@cloudbase/agent-server";
run({ createAgent: () => ({ agent }), port: 9000 });
```

### createExpressServer() - Get App

```typescript
import { createExpressServer } from "@cloudbase/agent-server";
const app = createExpressServer({ createAgent: () => ({ agent }) });
app.listen(9000);
```

### createExpressRoutes() - Add to Existing

```typescript
import { createExpressRoutes } from "@cloudbase/agent-server";
createExpressRoutes({ createAgent: () => ({ agent }), express: app, basePath: "/api/" });
```

## Endpoints Created

| Endpoint | Purpose |
|----------|---------|
| `/agui` | CopilotKit RPC endpoint |
| `/send-message` | AG-UI endpoint (SSE) |
| `/healthz` | Health check |
| `/chat/completions` | OpenAI-compatible endpoint |
| `/v1/aibot/bots/:agentId/...` | Same endpoints with bot ID (when no basePath) |

## AgentCreatorContext

```typescript
interface AgentCreatorContext {
  request: Request;      // Web Standard Request
  logger?: Logger;       // Pino-style logger (AGUI routes only)
  requestId?: string;    // Unique request ID (AGUI routes only)
}

createAgent: (ctx: AgentCreatorContext) => ({
  agent,                 // Your adapter instance
  cleanup?: () => void   // Called when request ends
})
```

## Cleanup Pattern

```typescript
createAgent: (ctx) => {
  const db = connectToDatabase();
  ctx.logger?.info("Connected to database");
  return {
    agent: new LanggraphAgent({ workflow }),
    cleanup: () => db.close()
  };
}
```

## All Options

```typescript
run({
  createAgent,
  port: 9000,
  basePath: "/api/",           // Custom base path (default: dual endpoints)
  cors: true,                  // or { origin: "https://..." }
  useAGUI: true,               // Enable /agui endpoint (default: true)
  aguiOptions: {
    runtimeOptions: {},        // CopilotRuntimeOptions
    endpointOptions: {}        // CreateCopilotRuntimeServerOptions
  },
  logger: createConsoleLogger("debug"),
  observability: { type: "otlp", url: "...", headers: {...} }
});
```

## Logger Exports

```typescript
import {
  noopLogger,           // Silent logger (default)
  createConsoleLogger,  // Console logger
  generateRequestId,
  extractRequestId,
  getOrGenerateRequestId
} from "@cloudbase/agent-server";

// Custom logger (Pino-style interface)
const logger = {
  info: (obj, msg) => console.log(msg, obj),
  error: (obj, msg) => console.error(msg, obj),
  debug: (obj, msg) => console.debug(msg, obj),
  child: (bindings) => ({ ...logger })
};
```

## Observability

Requires `@cloudbase/agent-observability` package:

```typescript
run({
  createAgent,
  observability: { type: "console" }  // Logs traces to stdout
});

// OTLP exporter (Langfuse, Jaeger, etc.)
run({
  createAgent,
  observability: {
    type: "otlp",
    url: "https://cloud.langfuse.com/api/public/otlp/v1/traces",
    headers: { Authorization: "Basic xxx" }
  }
});

// Multiple exporters
run({
  createAgent,
  observability: [
    { type: "console" },
    { type: "otlp", url: "http://localhost:4318/v1/traces" }
  ]
});
```

## Error Handling

```typescript
import { ErrorCode, isErrorWithCode } from "@cloudbase/agent-server";

// ErrorCode enum values for error handling
```
