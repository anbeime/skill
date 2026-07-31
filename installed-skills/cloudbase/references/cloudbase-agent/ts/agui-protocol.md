# AG-UI Protocol

Open, event-based protocol for agent-UI communication. Server streams events to client via SSE.

## Event Patterns

**Start-Content-End**: For streaming content
```
TEXT_MESSAGE_START → TEXT_MESSAGE_CONTENT (repeat) → TEXT_MESSAGE_END
TOOL_CALL_START → TOOL_CALL_ARGS (repeat) → TOOL_CALL_END
```

**Lifecycle**: Wraps every agent run
```
RUN_STARTED → [events] → RUN_FINISHED | RUN_ERROR
```

**Snapshot-Delta**: For state sync
```
STATE_SNAPSHOT (full state) → STATE_DELTA (JSON Patch updates)
```

## Core Events

| Event | Key Fields |
|-------|------------|
| `RUN_STARTED` | threadId, runId |
| `RUN_FINISHED` | threadId, runId |
| `RUN_ERROR` | message, code? |
| `TEXT_MESSAGE_START` | messageId, role |
| `TEXT_MESSAGE_CONTENT` | messageId, delta |
| `TEXT_MESSAGE_END` | messageId |
| `TOOL_CALL_START` | toolCallId, toolCallName, parentMessageId? |
| `TOOL_CALL_ARGS` | toolCallId, delta |
| `TOOL_CALL_END` | toolCallId |
| `TOOL_CALL_RESULT` | toolCallId, messageId, content |
| `STATE_SNAPSHOT` | snapshot |
| `STATE_DELTA` | delta (RFC 6902 JSON Patch) |
| `MESSAGES_SNAPSHOT` | messages[] |

## Input Types

```typescript
interface RunAgentInput {
  threadId: string;
  runId: string;
  messages: Message[];
  tools: Tool[];
  state?: unknown;
  context?: Context[];
  forwardedProps?: Record<string, unknown>;
}

interface Message {
  id: string;
  role: "user" | "assistant" | "system" | "tool";
  content: string;
  name?: string;                    // for tool messages
  toolCalls?: ToolCall[];           // for assistant messages
  toolCallId?: string;              // for tool messages
}

interface ToolCall {
  id: string;
  type: "function";
  function: { name: string; arguments: string };
}

interface Tool {
  name: string;
  description: string;
  parameters?: JSONSchema;
}
```

## Tool Execution Flow

**Server-executed tools:**
1. Agent emits `TOOL_CALL_START/ARGS/END`
2. Server executes tool
3. Server emits `TOOL_CALL_RESULT`
4. Agent continues with result

**Client tools:**
1. Agent emits `TOOL_CALL_START/ARGS/END`
2. Server emits `RUN_FINISHED` (run pauses)
3. Client executes tool locally
4. Client sends new request with tool result in messages
5. Agent continues

## Full Reference

For complete protocol specification: https://docs.ag-ui.com/concepts/events
