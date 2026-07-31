# Building UI Clients

Connect your UI to AG-UI endpoints served by @cloudbase/agent-server.

## Web Applications

Use `@ag-ui/client` (official AG-UI SDK):

```bash
npm install @ag-ui/client@latest
```

```typescript
import { HttpAgent } from "@ag-ui/client";

const agent = new HttpAgent({ url: "http://localhost:9000/send-message" });

for await (const event of agent.run({
  threadId: "thread-1",
  runId: "run-1",
  messages: [{ id: "m1", role: "user", content: "Hello" }]
})) {
  console.log(event.type, event);
}
```

See AG-UI documentation for full API: https://docs.ag-ui.com

## WeChat Mini Program

Use `@cloudbase/agent-ui-miniprogram` (headless behavior mixin):

```bash
npm install @cloudbase/agent-ui-miniprogram@latest
```

```typescript
import { createAGUIBehavior, CloudbaseTransport } from "@cloudbase/agent-ui-miniprogram";

Component({
  behaviors: [createAGUIBehavior({
    transport: new CloudbaseTransport({ botId: "your-bot-id" })
  })],
  methods: {
    onSend() {
      this.agui.sendMessage(this.data.inputText);
    }
  }
});
// State: this.data.agui.uiMessages, this.data.agui.isRunning
```

Beyond basic usage, the package offers more `createAGUIBehavior` options, `this.agui.*` namespace methods, state getters, and UIMessage format for rendering.
