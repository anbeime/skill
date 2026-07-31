# Server Quickstart Guide

This guide shows you how to create and deploy CloudBase Agent Python agents as HTTP services using FastAPI.

---

## Three Deployment Methods

CloudBase Agent Python SDK provides three flexible deployment methods, each suited for different use cases:

### Method 1: Core Adapters (Maximum Flexibility)

Use `create_send_message_adapter()` and `create_openai_adapter()` directly for complete control over routes.

```python
from fastapi import FastAPI
from cloudbase_agent.server import (
    create_send_message_adapter,
    create_openai_adapter,
    RunAgentInput,
    OpenAIChatCompletionRequest
)
from cloudbase_agent.server.errors import install_exception_handlers

app = FastAPI()

# Required: Install exception handlers for AG-UI protocol compatibility
install_exception_handlers(app)

# Define routes manually
@app.post("/my-agent/send-message")
async def send_message(request: RunAgentInput):
    return await create_send_message_adapter(create_agent, request)

@app.post("/my-agent/chat/completions")
async def openai_endpoint(request: OpenAIChatCompletionRequest):
    return await create_openai_adapter(create_agent, request)
```

**Advantages:**
- Full control over route paths
- Easy to add custom middleware per route
- Clear separation of concerns
- Ideal for complex multi-agent systems

**Use when:**
- You need custom route structures
- You want fine-grained control
- You're building complex applications

### Method 2: AgentServiceApp with Custom Routes (Recommended)

Use `AgentServiceApp.build()` for automatic features with flexibility:

```python
from fastapi import FastAPI
from cloudbase_agent.server import AgentServiceApp, HealthzConfig

# Create main app
main_app = FastAPI(title="My Service")

# Build agent app with automatic features
agent_app = AgentServiceApp()
agent_fastapi = agent_app.build(
    create_agent,
    base_path="",
    enable_cors=False,  # Handle in main app
    enable_openai_endpoint=True,
    enable_healthz=True,
    healthz_config=HealthzConfig(
        service_name="my-agent",
        version="1.0.0"
    )
)

# Mount to main app
main_app.mount("/my-agent", agent_fastapi)
```

**Advantages:**
- Automatic health check endpoints
- Built-in OpenAI compatibility
- Less boilerplate code
- Modular agent deployment

**Use when:**
- You want automatic health checks
- You're deploying multiple agents
- You need both CloudBase Agent native and OpenAI endpoints

### Method 3: One-Line Deployment (Simplest)

For single-agent deployments, use the one-line approach:

```python
from cloudbase_agent.server import AgentServiceApp, HealthzConfig

AgentServiceApp().run(
    create_agent,
    port=9000,
    enable_openai_endpoint=True,
    healthz_config=HealthzConfig(
        service_name="my-agent",
        version="1.0.0"
    )
)
```

**Advantages:**
- Extremely simple (one line!)
- Perfect for prototyping
- Automatic CORS and health checks
- No boilerplate needed

**Use when:**
- You have a single agent
- You want the fastest way to start
- You don't need custom routes

---

## Agent Creator Pattern

All three methods use an "agent creator" function that returns an `AgentCreatorResult`:

```python
from cloudbase_agent.langgraph import LangGraphAgent
from cloudbase_agent.server import AgentCreatorResult

def create_agent() -> AgentCreatorResult:
    """Create agent with optional cleanup."""
    
    agent = LangGraphAgent(
        name="my-agent",
        description="A helpful assistant",
        graph=build_workflow(),
        use_callbacks=True
    )
    
    # Optional: Add callbacks
    agent.add_callback(ConsoleLogger())
    
    # Optional: Define cleanup function
    def cleanup():
        # Close connections, release resources, etc.
        print("Cleanup completed")
    
    return {"agent": agent, "cleanup": cleanup}
```

**Why use creator functions?**
- Agent instance is created fresh per request
- Ensures proper isolation
- Automatic cleanup after request completes
- Supports resource management (DB connections, file handles, etc.)

---

## Complete Example: Multi-Agent Server

Here's a production-ready example with multiple agents:

```python
#!/usr/bin/env python3
import logging
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from cloudbase_agent.langgraph import LangGraphAgent
from cloudbase_agent.server import (
    AgentCreatorResult,
    AgentServiceApp,
    HealthzConfig,
    OpenAIChatCompletionRequest,
    RunAgentInput,
    create_openai_adapter,
    create_send_message_adapter,
)
from cloudbase_agent.server.errors import install_exception_handlers

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)

# Import your agent workflows
from agents.chat.agent import build_chat_workflow
from agents.assistant.agent import build_assistant_workflow

# Initialize workflows
chat_workflow = build_chat_workflow()
assistant_workflow = build_assistant_workflow()


# Agent creator for chat bot
def create_chat_agent() -> AgentCreatorResult:
    agent = LangGraphAgent(
        name="chatbot",
        description="A conversational assistant",
        graph=chat_workflow,
        use_callbacks=True
    )
    return {"agent": agent}


# Agent creator for assistant
def create_assistant_agent() -> AgentCreatorResult:
    agent = LangGraphAgent(
        name="assistant",
        description="A helpful AI assistant",
        graph=assistant_workflow,
        use_callbacks=True
    )
    
    def cleanup():
        print(f"Cleanup for {agent.name}")
    
    return {"agent": agent, "cleanup": cleanup}


def main():
    # Method 1: Using core adapters
    app = FastAPI(
        title="CloudBase Agent Multi-Agent Server",
        version="1.0.0"
    )
    
    # Install exception handlers (required for Method 1)
    install_exception_handlers(app)
    
    # Add CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Chat bot endpoints
    @app.post("/chatbot/send-message")
    async def chatbot_send_message(request: RunAgentInput):
        return await create_send_message_adapter(create_chat_agent, request)
    
    @app.post("/chatbot/chat/completions")
    async def chatbot_openai(request: OpenAIChatCompletionRequest):
        return await create_openai_adapter(create_chat_agent, request)
    
    # Assistant endpoints
    @app.post("/assistant/send-message")
    async def assistant_send_message(request: RunAgentInput):
        return await create_send_message_adapter(create_assistant_agent, request)
    
    @app.post("/assistant/chat/completions")
    async def assistant_openai(request: OpenAIChatCompletionRequest):
        return await create_openai_adapter(create_assistant_agent, request)
    
    # Health check
    @app.get("/healthz")
    def healthz():
        from datetime import datetime
        import platform
        
        return {
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "version": "1.0.0",
            "python_version": platform.python_version(),
            "agents": [
                {"name": "chatbot", "endpoints": ["/chatbot/send-message", "/chatbot/chat/completions"]},
                {"name": "assistant", "endpoints": ["/assistant/send-message", "/assistant/chat/completions"]},
            ]
        }
    
    uvicorn.run(app, host="0.0.0.0", port=9000)


if __name__ == "__main__":
    main()
```

---

## Testing Your Server

### 1. CloudBase Agent Native Endpoint

```bash
curl -X POST http://localhost:9000/chatbot/send-message \
  -H "Content-Type: application/json" \
  -d '{
    "conversationId": "conv_123",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

### 2. OpenAI-Compatible Endpoint

```bash
curl -X POST http://localhost:9000/chatbot/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "chatbot",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ],
    "stream": true
  }'
```

### 3. Using OpenAI Python Client

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:9000",
    api_key="dummy"  # Not required for local
)

response = client.chat.completions.create(
    model="chatbot",
    messages=[{"role": "user", "content": "Hello!"}],
    stream=True
)

for chunk in response:
    print(chunk.choices[0].delta.content, end="")
```

### 4. Health Check

```bash
curl http://localhost:9000/healthz
```

---

## Callbacks for Monitoring

Add callbacks to your agent for real-time monitoring:

```python
class ConsoleLogger:
    """Log agent events to console."""
    
    async def on_text_message_content(self, event, buffer):
        print(f"[AI] {buffer}", end="", flush=True)
    
    async def on_tool_call_args(self, event, buffer, partial_args):
        tool_name = getattr(event, "tool_name", "unknown")
        if partial_args:
            print(f"\n[TOOL] {tool_name}: {partial_args}")
    
    async def on_run_started(self, event):
        print(f"\n{'=' * 60}")
        print(f"Run Started: {event.run_id}")
        print(f"{'=' * 60}")
    
    async def on_run_finished(self, event):
        print(f"\n{'=' * 60}")
        print(f"Run Finished: {event.run_id}")
        print(f"{'=' * 60}\n")
    
    async def on_run_error(self, event):
        print(f"\nERROR: {getattr(event, 'message', 'Unknown')}\n")


def create_agent() -> AgentCreatorResult:
    agent = LangGraphAgent(
        name="my-agent",
        graph=build_workflow(),
        use_callbacks=True  # Enable callbacks
    )
    
    # Add console logger
    agent.add_callback(ConsoleLogger())
    
    return {"agent": agent}
```

---

## Production Considerations

### 1. Use Environment Variables

```python
# .env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_TEMPERATURE=0.7
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional

# Load in code
from dotenv import load_dotenv
load_dotenv()
```

### 2. Enable Observability

```bash
export AUTO_TRACES_STDOUT=true
python server.py
```

Or programmatically:

```python
from cloudbase_agent.observability import ConsoleTraceConfig, enable_tracing

enable_tracing(ConsoleTraceConfig())
```

### 3. Add Authentication Middleware

See `authentication.md` for details on implementing JWT-based authentication.

### 4. Configure CORS Properly

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend.com"],  # Specific origins in production
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)
```

### 5. Use Production Server

```bash
# Install gunicorn
pip install gunicorn uvicorn[standard]

# Run with multiple workers
gunicorn server:app.app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:9000
```

---

## Next Steps

- **LangGraph Integration**: See `adapter-langgraph.md` for detailed LangGraph usage
- **Coze Integration**: See `adapter-coze.md` for Coze platform integration
- **Authentication**: See `authentication.md` for auth patterns
- **Custom Adapters**: See `adapter-development.md` for creating custom framework adapters
