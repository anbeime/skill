# @cloudbase/agent-ui-miniprogram

WeChat Mini Program SDK for AG-UI protocol. Headless behavior mixin pattern.

## Installation

```bash
npm install @cloudbase/agent-ui-miniprogram@latest
```

## Basic Usage

```typescript
import { createAGUIBehavior, CloudbaseTransport } from "@cloudbase/agent-ui-miniprogram";

const transport = new CloudbaseTransport({ botId: "your-bot-id" });

Component({
  behaviors: [createAGUIBehavior({ transport })],
  methods: {
    onSend() {
      this.agui.sendMessage(this.data.inputText);
    }
  }
});
```

## createAGUIBehavior Options

```typescript
createAGUIBehavior({
  transport,              // Transport instance (CloudbaseTransport)
  messages: [],           // Initial message history
  tools: [{               // Client tools the agent can invoke
    name: "get_weather",
    description: "Get weather",
    parameters: { type: "object", properties: { city: { type: "string" } } },
    handler: async ({ args }) => ({ temp: 72 })
  }],
  threadId: "custom-id",  // Custom thread ID (auto-generated if omitted)
  contexts: [],           // Additional context objects
  onRawEvent: (event) => {} // Callback for each raw AG-UI event
})
```

## Namespace Methods (this.agui.*)

| Method | Description |
|--------|-------------|
| `init({ transport, threadId? })` | Initialize transport at runtime |
| `sendMessage(text \| Message[])` | Send message and run agent |
| `appendMessage(message)` | Add message without running agent |
| `setMessages(messages)` | Replace entire message history |
| `reset()` | Reset to initial state |
| `setThreadId(id)` | Change thread ID |
| `addTool(tool)` | Register a client tool |
| `removeTool(name)` | Remove tool by name |
| `updateTool(name, updates)` | Update tool properties |
| `clearTools()` | Remove all tools |

## State Getters (this.agui.* or this.data.agui.*)

| Property | Type | Description |
|----------|------|-------------|
| `messages` | `Message[]` | Raw message history |
| `uiMessages` | `UIMessage[]` | Messages formatted for UI rendering |
| `isRunning` | `boolean` | Agent is processing |
| `runId` | `string \| null` | Current run ID |
| `activeToolCalls` | `ToolCallState[]` | Tool calls in progress |
| `error` | `AGUIClientError \| null` | Last error |
| `threadId` | `string` | Current thread ID |
| `tools` | `Tool[]` | Registered tools (definitions only) |
| `contexts` | `Context[]` | Context objects |
| `config` | `CreateAGUIBehaviorOptions` | Current configuration |

## CloudbaseTransport

Production transport for WeChat Cloud Development:

```typescript
import { CloudbaseTransport } from "@cloudbase/agent-ui-miniprogram";

const transport = new CloudbaseTransport({
  botId: "bot-xxxxxx"  // From Cloud Development console
});
```

Requires `wx.cloud.extend.AI.bot.sendMessage` API.

## Imperative Pattern

Use `aguiBehavior` (no static config) for runtime-only initialization:

```typescript
import { aguiBehavior, CloudbaseTransport } from "@cloudbase/agent-ui-miniprogram";

Component({
  behaviors: [aguiBehavior],
  lifetimes: {
    attached() {
      this.agui.init({
        transport: new CloudbaseTransport({ botId: "my-bot" })
      });
    }
  }
});
```

## Client Tool Example

```typescript
Component({
  behaviors: [createAGUIBehavior({ transport })],
  lifetimes: {
    attached() {
      this.agui.addTool({
        name: "show_toast",
        description: "Show a toast message",
        parameters: {
          type: "object",
          properties: { title: { type: "string" } },
          required: ["title"]
        },
        handler: async ({ args }) => {
          wx.showToast({ title: args.title });
          return { success: true };
        }
      });
    }
  }
});
```

## UIMessage Format

`uiMessages` groups consecutive same-role messages with parts:

```typescript
interface UIMessage {
  id: string;
  role: "user" | "assistant";
  parts: (TextPart | ToolPart)[];
}

interface TextPart { type: "text"; text: string; }
interface ToolPart {
  type: "tool";
  toolCallId: string;
  name: string;
  args?: Record<string, unknown>;
  status: "pending" | "ready" | "executing" | "completed" | "failed";
  result?: unknown;
  error?: AGUIClientError;
}
```

