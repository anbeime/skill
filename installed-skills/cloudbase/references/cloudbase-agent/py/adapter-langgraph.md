# LangGraph Adapter Guide

Complete guide for integrating LangGraph agents with CloudBase Agent Python SDK.

---

## Overview

The CloudBase Agent LangGraph adapter (`cloudbase_agent.langgraph`) provides seamless integration with LangGraph workflows, offering:

- **Native LangGraph Support**: Wrap any `CompiledStateGraph` as an CloudBase Agent agent
- **AG-UI Compatibility**: Automatic stability patches for frontend integration
- **Streaming Support**: Real-time message streaming to clients
- **Memory Persistence**: LangGraph checkpoint support for conversation history
- **Callback System**: Monitor agent events in real-time
- **Resource Cleanup**: Automatic cleanup after request completion

---

## Quick Start

### 1. Install Dependencies

```bash
pip install cloudbase_agent[langgraph]
```

This installs:
- `cloudbase-agent-langgraph` - LangGraph adapter
- `langgraph` - LangGraph framework
- `langchain` - LangChain core
- `langchain-openai` - OpenAI integration

### 2. Create Your First Agent

```python
# agent.py
from langgraph.graph import StateGraph, MessagesState, END, START
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage
from cloudbase_agent.langgraph import LangGraphAgent

# Define state
class State(MessagesState):
    pass

# Define chat node
def chat_node(state: State, config, writer):
    """Generate AI response."""
    chat_model = ChatOpenAI(model="gpt-4o-mini")
    system = SystemMessage(content="You are a helpful assistant.")
    messages = [system, *state["messages"]]
    
    chunks = []
    for chunk in chat_model.stream(messages, config):
        writer({"messages": [chunk]})  # Stream to client
        chunks.append(chunk)
    
    return {"messages": chunks}

# Build workflow
def build_workflow():
    graph = StateGraph(State)
    graph.add_node("chat", chat_node)
    graph.add_edge(START, "chat")
    graph.add_edge("chat", END)
    
    memory = MemorySaver()
    return graph.compile(checkpointer=memory)

# Wrap with CloudBase Agent
agent = LangGraphAgent(
    name="chatbot",
    description="A helpful conversational assistant",
    graph=build_workflow()
)
```

### 3. Deploy as HTTP Service

```python
# server.py
from cloudbase_agent.server import AgentServiceApp

AgentServiceApp().run(
    lambda: {"agent": agent},
    port=9000,
    enable_openai_endpoint=True
)
```

---

## LangGraphAgent Configuration

### Basic Configuration

```python
from cloudbase_agent.langgraph import LangGraphAgent

agent = LangGraphAgent(
    name="my-agent",  # Required: Agent identifier
    description="Agent description",  # Optional: For documentation
    graph=build_workflow(),  # Required: CompiledStateGraph
    use_callbacks=True,  # Optional: Enable callback system (default: False)
)
```

### Advanced Configuration

```python
agent = LangGraphAgent(
    name="advanced-agent",
    description="Advanced agent with full configuration",
    graph=compiled_graph,
    use_callbacks=True,
    
    # Add callbacks
    callbacks=[ConsoleLogger(), MetricsCollector()],
    
    # Add tool proxy for permission control
    tool_proxy=permission_checker,
)

# Add callbacks dynamically
agent.add_callback(DatabaseLogger())
```

---

## State Management

### Basic MessagesState

```python
from langgraph.graph import MessagesState

class State(MessagesState):
    """Simplest state - just conversation history."""
    pass
```

### Extended State with Tools

```python
from langgraph.graph import MessagesState
from typing import List, Any

class State(MessagesState):
    """State with tool support."""
    tools: List[Any]  # Available tools
```

### Custom State Fields

```python
from langgraph.graph import MessagesState
from typing import Optional

class State(MessagesState):
    """State with custom fields."""
    user_id: str  # User identifier
    context: Optional[dict]  # Additional context
    preference: str  # User preferences
```

---

## Streaming Response

### StreamWriter Pattern

LangGraph nodes receive a `writer` parameter for streaming:

```python
from langgraph.types import StreamWriter

def chat_node(state: State, config, writer: StreamWriter):
    """Node with streaming support."""
    
    chat_model = ChatOpenAI(model="gpt-4o-mini")
    
    chunks = []
    for chunk in chat_model.stream(messages, config):
        # Stream chunk to client immediately
        writer({"messages": [chunk]})
        
        # Collect for final state
        chunks.append(chunk)
    
    # Return collected chunks for state
    return {"messages": chunks}
```

### Handling Missing Writer

```python
def chat_node(state: State, config, writer: StreamWriter = None):
    """Node with fallback for missing writer."""
    
    # Provide no-op fallback
    if writer is None:
        def writer(x):
            pass
    
    # Use writer safely
    for chunk in chat_model.stream(messages):
        writer({"messages": [chunk]})
```

---

## Memory & Checkpointing

### In-Memory Checkpointer

For development and testing:

```python
from langgraph.checkpoint.memory import MemorySaver

def build_workflow():
    graph = StateGraph(State)
    # ... add nodes and edges ...
    
    memory = MemorySaver()  # In-memory storage
    return graph.compile(checkpointer=memory)
```

### Using Conversation ID

```bash
# Each conversation gets unique thread_id
curl -X POST http://localhost:9000/send-message \
  -H "Content-Type: application/json" \
  -d '{
    "conversationId": "user_123_conv_456",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

The `conversationId` is automatically mapped to LangGraph's `thread_id` for checkpoint retrieval.

### Persistent Checkpointer

For production with PostgreSQL:

```python
from langgraph.checkpoint.postgres import PostgresSaver

# Create PostgreSQL checkpointer
checkpointer = PostgresSaver.from_conn_string(
    "postgresql://user:pass@localhost/dbname"
)

def build_workflow():
    graph = StateGraph(State)
    # ... add nodes and edges ...
    
    return graph.compile(checkpointer=checkpointer)
```

---

## Tool Integration

### Defining Tools

```python
from typing import List, Any
from langchain_core.utils.function_calling import convert_to_openai_function

class State(MessagesState):
    tools: List[Any]

def chat_node(state: State, config, writer):
    chat_model = ChatOpenAI(model="gpt-4o-mini")
    
    # Get and bind tools
    tools = state.get("tools", [])
    if tools:
        # Convert tool definitions to OpenAI format
        tools_list = [convert_to_openai_function(tool) for tool in tools]
        chat_model = chat_model.bind_tools(tools_list)
    
    # Use model with tools
    for chunk in chat_model.stream(messages, config):
        writer({"messages": [chunk]})
```

### Providing Tools via API

```bash
curl -X POST http://localhost:9000/send-message \
  -H "Content-Type: application/json" \
  -d '{
    "conversationId": "conv_123",
    "messages": [{"role": "user", "content": "Search the web"}],
    "tools": [
      {
        "name": "search_web",
        "description": "Search the internet",
        "parameters": {
          "type": "object",
          "properties": {
            "query": {"type": "string"}
          },
          "required": ["query"]
        }
      }
    ]
  }'
```

---

## Callbacks

### Built-in Callback Interface

```python
class MyCallback:
    """Custom callback for monitoring."""
    
    async def on_text_message_content(self, event, buffer):
        """Called when text message content is streaming."""
        print(f"AI: {buffer}")
    
    async def on_tool_call_args(self, event, buffer, partial_args):
        """Called when tool call arguments are parsed."""
        tool_name = getattr(event, "tool_name", "unknown")
        print(f"Tool: {tool_name}, Args: {partial_args}")
    
    async def on_run_started(self, event):
        """Called when agent run starts."""
        print(f"Started: {event.run_id}")
    
    async def on_run_finished(self, event):
        """Called when agent run finishes."""
        print(f"Finished: {event.run_id}")
    
    async def on_run_error(self, event):
        """Called when an error occurs."""
        print(f"Error: {getattr(event, 'message', 'Unknown')}")
```

### Adding Callbacks

```python
# Method 1: During agent creation
agent = LangGraphAgent(
    name="my-agent",
    graph=workflow,
    use_callbacks=True,
    callbacks=[MyCallback()]
)

# Method 2: After creation
agent.add_callback(MyCallback())
```

---

## Error Handling

### AG-UI Protocol Errors

CloudBase Agent automatically converts exceptions to AG-UI error events:

```python
def chat_node(state: State, config, writer):
    try:
        # Your logic here
        result = dangerous_operation()
        return {"messages": [result]}
    except Exception as e:
        # Error is automatically formatted as AG-UI error event
        from langchain_core.messages import AIMessage
        return {"messages": [AIMessage(content=f"Error: {str(e)}")]}
```

### Custom Error Handling

```python
from cloudbase_agent.server.errors import install_exception_handlers
from fastapi import FastAPI

app = FastAPI()

# Install AG-UI error handlers
install_exception_handlers(app)

# Now all exceptions are converted to AG-UI error events
```

---

## Complete Example: Human-in-the-Loop

```python
#!/usr/bin/env python3
from typing import Optional
from langgraph.graph import StateGraph, MessagesState, END, START
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, AIMessage
from cloudbase_agent.langgraph import LangGraphAgent

class State(MessagesState):
    """State for human-in-the-loop workflow."""
    pending_approval: Optional[dict] = None

def chat_node(state: State, config, writer):
    """Generate AI response."""
    chat_model = ChatOpenAI(model="gpt-4o-mini")
    system = SystemMessage(content="You are a helpful assistant.")
    messages = [system, *state["messages"]]
    
    chunks = []
    for chunk in chat_model.stream(messages, config):
        writer({"messages": [chunk]})
        chunks.append(chunk)
    
    # Check if approval is needed
    final_message = chunks[-1] if chunks else AIMessage(content="")
    if "sensitive" in final_message.content.lower():
        return {
            "messages": chunks,
            "pending_approval": {
                "action": "send_message",
                "content": final_message.content
            }
        }
    
    return {"messages": chunks}

def approval_node(state: State, config, writer):
    """Wait for human approval."""
    if state.get("pending_approval"):
        writer({
            "messages": [AIMessage(
                content="This action requires approval. Please approve or reject."
            )]
        })
        # Workflow will interrupt here for human input
        return state
    return state

def should_wait_approval(state: State) -> str:
    """Decide if approval is needed."""
    if state.get("pending_approval"):
        return "approval"
    return END

def build_workflow():
    """Build human-in-the-loop workflow."""
    graph = StateGraph(State)
    
    graph.add_node("chat", chat_node)
    graph.add_node("approval", approval_node)
    
    graph.add_edge(START, "chat")
    graph.add_conditional_edges(
        "chat",
        should_wait_approval,
        {
            "approval": "approval",
            END: END
        }
    )
    
    memory = MemorySaver()
    return graph.compile(
        checkpointer=memory,
        interrupt_before=["approval"]  # Pause before approval
    )

# Create agent
agent = LangGraphAgent(
    name="human-in-the-loop",
    description="Agent with human approval workflow",
    graph=build_workflow(),
    use_callbacks=True
)

# Deploy
if __name__ == "__main__":
    from cloudbase_agent.server import AgentServiceApp
    AgentServiceApp().run(
        lambda: {"agent": agent},
        port=9000
    )
```

---

## Best Practices

### 1. Always Use MemorySaver

```python
# ✅ Correct: With memory
memory = MemorySaver()
workflow = graph.compile(checkpointer=memory)

# ❌ Wrong: No memory - conversations won't persist
workflow = graph.compile()
```

### 2. Stream Immediately

```python
# ✅ Correct: Stream as you generate
for chunk in model.stream(messages):
    writer({"messages": [chunk]})  # Immediate streaming
    chunks.append(chunk)

# ❌ Wrong: Collect first, then stream - defeats streaming purpose
chunks = list(model.stream(messages))
for chunk in chunks:
    writer({"messages": [chunk]})
```

### 3. Handle Missing Writer

```python
# ✅ Correct: Fallback for testing
def chat_node(state, config, writer=None):
    if writer is None:
        writer = lambda x: None
    
    # Use writer safely
    writer({"messages": [chunk]})

# ❌ Wrong: Assume writer always exists
def chat_node(state, config, writer):
    writer({"messages": [chunk]})  # Fails in tests
```

### 4. Use Environment Variables

```python
# .env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.7

# Load in code
from dotenv import load_dotenv
load_dotenv()

# Use in node
import os
chat_model = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
)
```

---

## Troubleshooting

### Issue: Conversation history not persisting

**Solution**: Ensure you're using a checkpointer:

```python
from langgraph.checkpoint.memory import MemorySaver

memory = MemorySaver()
workflow = graph.compile(checkpointer=memory)
```

### Issue: Streaming not working

**Solution**: Make sure you're calling `writer()` with proper format:

```python
# ✅ Correct format
writer({"messages": [chunk]})

# ❌ Wrong format
writer(chunk)  # Missing dict wrapper
```

### Issue: Tool calls not working

**Solution**: Ensure tools are in state and properly bound:

```python
class State(MessagesState):
    tools: List[Any]  # Add tools field

def chat_node(state, config, writer):
    tools = state.get("tools", [])
    if tools:
        tools_list = [convert_to_openai_function(t) for t in tools]
        model = model.bind_tools(tools_list)
```

---

## Next Steps

- **Server Deployment**: See `server-quickstart.md` for server configuration
- **Authentication**: See `authentication.md` for auth patterns
- **Observability**: Enable with `export AUTO_TRACES_STDOUT=true`
- **Examples**: Check `python-sdk/examples/langgraph/` for complete working examples
