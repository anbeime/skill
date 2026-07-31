# Custom Adapter Development

This guide explains how to build custom AG-UI protocol adapters in Python.

## Overview

An adapter bridges an Agent framework (LangGraph, LangChain, custom logic) to the AG-UI protocol. It translates framework events into standardized AG-UI events that clients can consume.

## AbstractAgent Interface

All adapters must implement the `AbstractAgent` interface:

```python
from typing import Any, AsyncGenerator
from cloudbase_agent.core import RunAgentInput, Event

class AbstractAgent:
    """Abstract base class for all AG-UI protocol adapters."""
    
    async def run(self, run_input: RunAgentInput) -> AsyncGenerator[Event, None]:
        """
        Execute the agent and yield AG-UI protocol events.
        
        :param run_input: Input data containing messages, state, tools, etc.
        :yields: AG-UI protocol events
        """
        raise NotImplementedError
```

## Event Types

AG-UI protocol defines these event types:

```python
from cloudbase_agent.core import EventType

class EventType:
    RUN_STARTED = "RUN_STARTED"
    RUN_FINISHED = "RUN_FINISHED"
    TEXT_MESSAGE_START = "TEXT_MESSAGE_START"
    TEXT_MESSAGE_CONTENT = "TEXT_MESSAGE_CONTENT"
    TEXT_MESSAGE_END = "TEXT_MESSAGE_END"
    TOOL_CALL_START = "TOOL_CALL_START"
    TOOL_CALL_ARGS_CHUNK = "TOOL_CALL_ARGS_CHUNK"
    TOOL_CALL_END = "TOOL_CALL_END"
    TOOL_RESULT = "TOOL_RESULT"
    STATE_SNAPSHOT = "STATE_SNAPSHOT"
    ERROR = "ERROR"
```

## Minimal Adapter Example

```python
from typing import Any, AsyncGenerator
from cloudbase_agent.core import RunAgentInput, Event, EventType
from uuid import uuid4

class SimpleEchoAgent:
    """Simplest possible adapter - echoes user messages."""
    
    async def run(self, run_input: RunAgentInput) -> AsyncGenerator[Event, None]:
        """Echo back the user's message."""
        # 1. Yield RUN_STARTED
        yield Event(type=EventType.RUN_STARTED, runId=run_input.runId)
        
        # 2. Get last user message
        last_message = run_input.messages[-1] if run_input.messages else None
        user_content = last_message.get("content", "") if last_message else ""
        
        # 3. Generate response
        message_id = str(uuid4())
        response_text = f"Echo: {user_content}"
        
        # 4. Yield TEXT_MESSAGE events
        yield Event(
            type=EventType.TEXT_MESSAGE_START,
            runId=run_input.runId,
            messageId=message_id,
            role="assistant"
        )
        
        yield Event(
            type=EventType.TEXT_MESSAGE_CONTENT,
            runId=run_input.runId,
            messageId=message_id,
            content=response_text
        )
        
        yield Event(
            type=EventType.TEXT_MESSAGE_END,
            runId=run_input.runId,
            messageId=message_id
        )
        
        # 5. Yield RUN_FINISHED
        yield Event(type=EventType.RUN_FINISHED, runId=run_input.runId)
```

Deploy it:

```python
from cloudbase_agent.server import AgentServiceApp

AgentServiceApp().run(lambda: SimpleEchoAgent(), port=8000)
```

## Streaming Response Pattern

For LLM streaming responses:

```python
from openai import AsyncOpenAI

class StreamingLLMAgent:
    """Agent with streaming LLM responses."""
    
    def __init__(self, api_key: str):
        self.client = AsyncOpenAI(api_key=api_key)
    
    async def run(self, run_input: RunAgentInput) -> AsyncGenerator[Event, None]:
        yield Event(type=EventType.RUN_STARTED, runId=run_input.runId)
        
        # Convert messages to OpenAI format
        messages = [
            {"role": msg["role"], "content": msg["content"]}
            for msg in run_input.messages
        ]
        
        # Stream response
        message_id = str(uuid4())
        yield Event(
            type=EventType.TEXT_MESSAGE_START,
            runId=run_input.runId,
            messageId=message_id,
            role="assistant"
        )
        
        stream = await self.client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            stream=True
        )
        
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                yield Event(
                    type=EventType.TEXT_MESSAGE_CONTENT,
                    runId=run_input.runId,
                    messageId=message_id,
                    content=content
                )
        
        yield Event(
            type=EventType.TEXT_MESSAGE_END,
            runId=run_input.runId,
            messageId=message_id
        )
        
        yield Event(type=EventType.RUN_FINISHED, runId=run_input.runId)
```

## Tool Calling Pattern

For agents that call tools:

```python
class ToolCallingAgent:
    """Agent with tool calling support."""
    
    async def run(self, run_input: RunAgentInput) -> AsyncGenerator[Event, None]:
        yield Event(type=EventType.RUN_STARTED, runId=run_input.runId)
        
        # Decide to call a tool
        tool_call_id = str(uuid4())
        tool_name = "get_weather"
        tool_args = {"location": "San Francisco"}
        
        # 1. Yield TOOL_CALL_START
        yield Event(
            type=EventType.TOOL_CALL_START,
            runId=run_input.runId,
            toolCallId=tool_call_id,
            toolName=tool_name
        )
        
        # 2. Yield TOOL_CALL_ARGS_CHUNK (can stream args)
        import json
        args_json = json.dumps(tool_args)
        yield Event(
            type=EventType.TOOL_CALL_ARGS_CHUNK,
            runId=run_input.runId,
            toolCallId=tool_call_id,
            argsChunk=args_json
        )
        
        # 3. Yield TOOL_CALL_END
        yield Event(
            type=EventType.TOOL_CALL_END,
            runId=run_input.runId,
            toolCallId=tool_call_id
        )
        
        # 4. Execute tool (if server-side tool)
        result = await self.execute_tool(tool_name, tool_args)
        
        # 5. Yield TOOL_RESULT
        yield Event(
            type=EventType.TOOL_RESULT,
            runId=run_input.runId,
            toolCallId=tool_call_id,
            result=result
        )
        
        # 6. Continue with response using tool result
        # ... (yield TEXT_MESSAGE events)
        
        yield Event(type=EventType.RUN_FINISHED, runId=run_input.runId)
```

## State Snapshot Pattern

For stateful agents:

```python
class StatefulAgent:
    """Agent that maintains and shares state."""
    
    async def run(self, run_input: RunAgentInput) -> AsyncGenerator[Event, None]:
        yield Event(type=EventType.RUN_STARTED, runId=run_input.runId)
        
        # Process and update state
        current_state = run_input.state or {}
        current_state["message_count"] = current_state.get("message_count", 0) + 1
        current_state["last_message_time"] = time.time()
        
        # ... (process messages)
        
        # Yield STATE_SNAPSHOT
        yield Event(
            type=EventType.STATE_SNAPSHOT,
            runId=run_input.runId,
            snapshot=current_state
        )
        
        yield Event(type=EventType.RUN_FINISHED, runId=run_input.runId)
```

## Error Handling Pattern

```python
class RobustAgent:
    """Agent with proper error handling."""
    
    async def run(self, run_input: RunAgentInput) -> AsyncGenerator[Event, None]:
        try:
            yield Event(type=EventType.RUN_STARTED, runId=run_input.runId)
            
            # Your logic here
            # ...
            
            yield Event(type=EventType.RUN_FINISHED, runId=run_input.runId)
            
        except Exception as e:
            # Yield ERROR event
            yield Event(
                type=EventType.ERROR,
                runId=run_input.runId,
                error={
                    "code": "AGENT_ERROR",
                    "message": str(e),
                    "details": {"traceback": traceback.format_exc()}
                }
            )
            
            # Still yield RUN_FINISHED
            yield Event(type=EventType.RUN_FINISHED, runId=run_input.runId)
```

## Complete Example: Custom Framework Adapter

```python
from typing import Any, AsyncGenerator
from cloudbase_agent.core import RunAgentInput, Event, EventType
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)

class MyCustomFrameworkAgent:
    """
    Adapter for a custom agent framework.
    
    This example shows how to integrate any custom agent logic
    with the AG-UI protocol.
    """
    
    def __init__(self, config: dict):
        """
        Initialize the adapter.
        
        :param config: Configuration for your custom framework
        """
        self.config = config
        # Initialize your framework here
        self.agent = self._initialize_agent()
    
    def _initialize_agent(self):
        """Initialize your custom agent framework."""
        # Your framework initialization logic
        return CustomFrameworkAgent(self.config)
    
    async def run(self, run_input: RunAgentInput) -> AsyncGenerator[Event, None]:
        """
        Execute agent and yield AG-UI protocol events.
        
        :param run_input: Input from AG-UI client
        :yields: AG-UI protocol events
        """
        try:
            # 1. Start
            yield Event(type=EventType.RUN_STARTED, runId=run_input.runId)
            logger.info(f"Run started: {run_input.runId}")
            
            # 2. Extract input data
            messages = run_input.messages
            state = run_input.state or {}
            tools = run_input.tools or []
            
            # 3. Get user context (if auth middleware is used)
            user_id = self._get_user_id(state)
            logger.info(f"User: {user_id}")
            
            # 4. Execute your custom framework
            message_id = str(uuid4())
            
            # Start message
            yield Event(
                type=EventType.TEXT_MESSAGE_START,
                runId=run_input.runId,
                messageId=message_id,
                role="assistant"
            )
            
            # Your framework's execution (can be streaming)
            async for chunk in self.agent.process(messages, state):
                # Handle different chunk types
                if chunk["type"] == "text":
                    yield Event(
                        type=EventType.TEXT_MESSAGE_CONTENT,
                        runId=run_input.runId,
                        messageId=message_id,
                        content=chunk["content"]
                    )
                
                elif chunk["type"] == "tool_call":
                    yield Event(
                        type=EventType.TOOL_CALL_START,
                        runId=run_input.runId,
                        toolCallId=chunk["id"],
                        toolName=chunk["name"]
                    )
                    
                    yield Event(
                        type=EventType.TOOL_CALL_ARGS_CHUNK,
                        runId=run_input.runId,
                        toolCallId=chunk["id"],
                        argsChunk=chunk["args"]
                    )
                    
                    yield Event(
                        type=EventType.TOOL_CALL_END,
                        runId=run_input.runId,
                        toolCallId=chunk["id"]
                    )
                
                elif chunk["type"] == "state_update":
                    yield Event(
                        type=EventType.STATE_SNAPSHOT,
                        runId=run_input.runId,
                        snapshot=chunk["state"]
                    )
            
            # End message
            yield Event(
                type=EventType.TEXT_MESSAGE_END,
                runId=run_input.runId,
                messageId=message_id
            )
            
            # 5. Finish
            yield Event(type=EventType.RUN_FINISHED, runId=run_input.runId)
            logger.info(f"Run finished: {run_input.runId}")
            
        except Exception as e:
            logger.error(f"Error in run: {e}", exc_info=True)
            
            yield Event(
                type=EventType.ERROR,
                runId=run_input.runId,
                error={
                    "code": "AGENT_ERROR",
                    "message": str(e)
                }
            )
            
            yield Event(type=EventType.RUN_FINISHED, runId=run_input.runId)
    
    def _get_user_id(self, state: dict) -> str:
        """Extract user ID from state (set by auth middleware)."""
        return state.get("__request_context__", {}).get("user", {}).get("id", "anonymous")
```

## Testing Your Adapter

### Unit Test

```python
import pytest
from cloudbase_agent.core import RunAgentInput

@pytest.mark.asyncio
async def test_adapter_basic_flow():
    """Test basic event flow."""
    adapter = MyCustomFrameworkAgent(config={})
    
    run_input = RunAgentInput(
        runId="test-run",
        threadId="test-thread",
        messages=[{"role": "user", "content": "Hello"}]
    )
    
    events = []
    async for event in adapter.run(run_input):
        events.append(event)
    
    # Verify event sequence
    assert events[0].type == EventType.RUN_STARTED
    assert events[-1].type == EventType.RUN_FINISHED
    
    # Verify message events
    message_events = [e for e in events if "MESSAGE" in e.type]
    assert len(message_events) >= 3  # START, CONTENT, END

@pytest.mark.asyncio
async def test_adapter_error_handling():
    """Test error handling."""
    adapter = MyCustomFrameworkAgent(config={"force_error": True})
    
    run_input = RunAgentInput(
        runId="test-error",
        threadId="test-thread",
        messages=[]
    )
    
    events = []
    async for event in adapter.run(run_input):
        events.append(event)
    
    # Verify ERROR event is emitted
    error_events = [e for e in events if e.type == EventType.ERROR]
    assert len(error_events) == 1
```

### Integration Test

```python
from fastapi.testclient import TestClient
from cloudbase_agent.server import AgentServiceApp

def test_adapter_via_http():
    """Test adapter through HTTP server."""
    app_instance = AgentServiceApp()
    fastapi_app = app_instance.build(
        create_agent=lambda: MyCustomFrameworkAgent(config={})
    )
    
    client = TestClient(fastapi_app)
    
    response = client.post(
        "/send-message",
        json={
            "messages": [{"role": "user", "content": "Hello"}],
            "runId": "test-run",
            "threadId": "test-thread"
        },
        headers={"Accept": "text/event-stream"}
    )
    
    assert response.status_code == 200
    
    # Parse SSE events
    lines = response.text.split("\n")
    events = []
    for line in lines:
        if line.startswith("data: "):
            import json
            event_data = json.loads(line[6:])
            events.append(event_data)
    
    # Verify event flow
    assert events[0]["type"] == "RUN_STARTED"
    assert events[-1]["type"] == "RUN_FINISHED"
```

## Best Practices

1. **Always yield RUN_STARTED first** - Clients expect this
2. **Always yield RUN_FINISHED last** - Even after errors
3. **Use proper event sequence** - START → CONTENT → END for messages
4. **Handle errors gracefully** - Yield ERROR event, don't raise exceptions
5. **Stream when possible** - Better UX with incremental updates
6. **Log important events** - Helps with debugging
7. **Extract user context** - Use `state.__request_context__.user` if available
8. **Validate input** - Check required fields before processing
9. **Use type hints** - Better IDE support and catch errors early
10. **Write tests** - Both unit and integration tests

## Common Pitfalls

### ❌ Not yielding RUN_STARTED/FINISHED

```python
async def run(self, run_input):
    # Missing RUN_STARTED
    yield Event(type=EventType.TEXT_MESSAGE_CONTENT, content="Hello")
    # Missing RUN_FINISHED
```

### ❌ Raising exceptions instead of ERROR events

```python
async def run(self, run_input):
    if error:
        raise Exception("Error")  # ❌ Breaks SSE stream
```

Should be:

```python
async def run(self, run_input):
    if error:
        yield Event(type=EventType.ERROR, error={"message": "Error"})
        yield Event(type=EventType.RUN_FINISHED)
```

### ❌ Not handling missing state

```python
user_id = run_input.state["__request_context__"]["user"]["id"]  # ❌ May crash
```

Should be:

```python
user_id = run_input.state.get("__request_context__", {}).get("user", {}).get("id")
```

## Examples

See `/python-sdk/examples/` for complete examples:
- `langgraph/` - LangGraph adapter patterns
- `langchain/` - LangChain adapter patterns
- `coze/` - Third-party API integration

## Next Steps

- Deploy your adapter: [server-quickstart.md](server-quickstart.md)
- Understand protocol details: [agui-protocol.md](agui-protocol.md)
- Add authentication: [authentication.md](authentication.md)
- Build UI: [ui-clients.md](ui-clients.md)
