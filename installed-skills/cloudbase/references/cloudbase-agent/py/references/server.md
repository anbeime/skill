# Server Reference (`cloudbase_agent.server`)

FastAPI-based HTTP server with dual-protocol support (AG-UI + OpenAI).

## Exports

| Export | Purpose |
|--------|---------|
| `AgentServiceApp` | FastAPI wrapper with CORS, healthz, middleware |
| `create_send_message_adapter` | AG-UI native SSE streaming adapter |
| `create_openai_adapter` | OpenAI-compatible `/chat/completions` adapter |
| `RunAgentInput` | Request model (messages, thread_id, run_id, state, tools, context, forwarded_props) |
| `OpenAIChatCompletionRequest` | OpenAI-compatible request model |
| `AgentCreatorResult` | TypedDict: `{"agent": ..., "cleanup": optional_fn}` |
| `HealthzConfig` | Health check config (service_name, version, custom_checks) |

## Three Deployment Methods

### Method 1: One-line (simplest)

```python
AgentServiceApp().run(create_agent, port=9000)
```

### Method 2: Build + customize (recommended for multi-agent)

```python
app = AgentServiceApp()
fastapi_app = app.build(
    create_agent,
    base_path="/api",
    enable_openai_endpoint=True,
    enable_healthz=True,
)
# Add custom routes to fastapi_app...
uvicorn.run(fastapi_app, host="0.0.0.0", port=9000)
```

### Method 3: Core adapters (maximum flexibility)

```python
from fastapi import FastAPI
from cloudbase_agent.server import create_send_message_adapter, create_openai_adapter

app = FastAPI()

@app.post("/my-agent/send-message")
async def send_message(request: RunAgentInput):
    return await create_send_message_adapter(create_my_agent, request)

@app.post("/my-agent/chat/completions")
async def chat(request: OpenAIChatCompletionRequest):
    return await create_openai_adapter(create_my_agent, request)
```

## AgentServiceApp Constructor

```python
AgentServiceApp(
    observability=None,  # Optional[ObservabilityConfig | List[ObservabilityConfig]]
)
```

## AgentServiceApp Methods

| Method | Returns | Purpose |
|--------|---------|---------|
| `.set_cors_config(allow_origins, allow_credentials, allow_methods, allow_headers)` | self | Configure CORS |
| `.use(middleware)` | self | Register middleware (generator pattern) |
| `.build(create_agent, base_path, enable_cors, enable_openai_endpoint, enable_healthz, healthz_config)` | FastAPI | Build configured app |
| `.run(create_agent, base_path, host, port, enable_openai_endpoint, enable_healthz, healthz_config)` | None | Build + run with uvicorn |

## Middleware Pattern

Middlewares use Python's generator pattern with `yield` — code before yield runs pre-processing, code after yield runs post-processing (onion model).

```python
def my_middleware(input_data: RunAgentInput, request: Request):
    # Pre-processing (runs before agent)
    auth = request.headers.get("Authorization")
    if auth and auth.startswith("Bearer "):
        if not input_data.forwarded_props:
            input_data.forwarded_props = {}
        input_data.forwarded_props["user_id"] = decode_jwt(auth[7:])
    
    yield  # Control passes to agent
    
    # Post-processing (runs after agent, optional)
    print("Request completed")

app = AgentServiceApp()
app.use(my_middleware)
app.run(create_agent, port=9000)
```

## Agent Creator Pattern

Factory function called per-request. Supports optional cleanup callback:

```python
def create_agent() -> AgentCreatorResult:
    db = connect_database()
    agent = LangGraphAgent(graph=workflow, name="my-agent")
    
    def cleanup():
        db.close()  # Guaranteed to run after stream completes
    
    return {"agent": agent, "cleanup": cleanup}
```

## Multi-Agent Server

### Option A: Manual routes

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from cloudbase_agent.server import create_send_message_adapter, create_openai_adapter, RunAgentInput, OpenAIChatCompletionRequest
from cloudbase_agent.server.errors import install_exception_handlers

app = FastAPI(title="Multi-Agent Server")
install_exception_handlers(app)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.post("/agentic_chat/send-message")
async def chat_send(request: RunAgentInput):
    return await create_send_message_adapter(create_chat_agent, request)

@app.post("/agentic_chat/chat/completions")
async def chat_openai(request: OpenAIChatCompletionRequest):
    return await create_openai_adapter(create_chat_agent, request)

@app.post("/human_in_the_loop/send-message")
async def hitl_send(request: RunAgentInput):
    return await create_send_message_adapter(create_hitl_agent, request)
```

### Option B: Mount sub-apps

```python
main_app = FastAPI()
chat_app = AgentServiceApp().build(create_chat_agent, enable_openai_endpoint=True)
hitl_app = AgentServiceApp().build(create_hitl_agent, enable_openai_endpoint=True)
main_app.mount("/agentic_chat", chat_app)
main_app.mount("/human_in_the_loop", hitl_app)
```
