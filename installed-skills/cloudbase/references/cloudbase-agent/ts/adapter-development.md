# Building Custom Adapters

An adapter bridges your AI framework to the AG-UI protocol. It converts AG-UI input (messages, tools, state) into your framework's format, and converts your framework's streaming output into AG-UI events.

**Prerequisites:** Deep understanding of both your AI framework's API and the AG-UI protocol events.

**When to build your own:** No existing adapter for your framework (check AG-UI ecosystem first).

Extend `AbstractAgent` and implement `run()` that returns `Observable<BaseEvent>`.

## Structure

```typescript
import { AbstractAgent, RunAgentInput, BaseEvent, EventType } from "@ag-ui/client";
import { Observable, Subscriber } from "rxjs";

export class MyAdapter extends AbstractAgent {
  run(input: RunAgentInput): Observable<BaseEvent> {
    return new Observable((subscriber) => this._run(subscriber, input));
  }

  private async _run(subscriber: Subscriber<BaseEvent>, input: RunAgentInput) {
    const { messages, runId, threadId, tools } = input;

    subscriber.next({ type: EventType.RUN_STARTED, threadId, runId });

    try {
      // 1. Convert AG-UI input to your framework's format
      // 2. Call your framework
      // 3. Convert your framework's output to AG-UI events (see Event Sequence below)

      subscriber.next({ type: EventType.RUN_FINISHED, threadId, runId });
    } catch (error) {
      subscriber.next({ type: EventType.RUN_ERROR, message: error.message });
    }
    subscriber.complete();
  }
}
```

## Event Sequence (Brief)

**Text:** `TEXT_MESSAGE_START` → `TEXT_MESSAGE_CONTENT` (repeat) → `TEXT_MESSAGE_END`

**Tool call:** `TOOL_CALL_START` → `TOOL_CALL_ARGS` → `TOOL_CALL_END`

**Tool result (server-executed tools only):** `TOOL_CALL_RESULT`

Always emit full lifecycle. `parentMessageId` links tool calls to their parent message.

For complete event reference, see [AG-UI Protocol](https://docs.ag-ui.com/concepts/events).
