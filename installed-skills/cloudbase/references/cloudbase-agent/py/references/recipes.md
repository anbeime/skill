# CloudBase Agent Recipes

Common patterns and complete examples for building agents with CloudBase Agent.

## Recipe 1: Basic Chat Agent

Complete example of a simple conversational agent.

```python
from cloudbase_agent.server import create_server, tool
from cloudbase_agent.langgraph import create_react_agent
from langchain_openai import ChatOpenAI

# Define tools
@tool
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    return f"Weather in {city}: Sunny, 22°C"

# Create model and agent
model = ChatOpenAI(model="gpt-4")
agent = create_react_agent(
    model=model,
    tools=[get_weather]
)

# Create server
server = create_server()
server.add_agent("/chat", agent)

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=8000)
```

## Recipe 2: Multi-Agent System

Orchestrate multiple specialized agents.

```python
from cloudbase_agent.langgraph import create_react_agent, create_router_agent

# Specialized agents
research_agent = create_react_agent(
    model=model,
    tools=[search_web, read_document],
    system_message="You are a research assistant."
)

writing_agent = create_react_agent(
    model=model,
    tools=[grammar_check, format_text],
    system_message="You are a writing assistant."
)

# Router agent
router = create_router_agent(
    agents={
        "research": research_agent,
        "writing": writing_agent
    },
    model=model
)

server.add_agent("/assistant", router)
```

## Recipe 3: Persistent Conversations

Maintain conversation history across sessions.

```python
from cloudbase_agent.server.storage import RedisStorage, ConversationStorage
from cloudbase_agent.langgraph import create_checkpointer

# Setup storage
storage = RedisStorage(url="redis://localhost:6379")
conv_storage = ConversationStorage(storage)
checkpointer = create_checkpointer(storage)

# Create agent with persistence
agent = create_react_agent(
    model=model,
    tools=tools,
    checkpointer=checkpointer
)

# Handle request with conversation ID
@server.post("/chat")
async def chat(request):
    conversation_id = request.conversation_id
    
    # Load conversation
    messages = await conv_storage.load_conversation(conversation_id)
    
    # Invoke agent
    result = await agent.ainvoke(
        {"messages": messages + [request.message]},
        config={"configurable": {"thread_id": conversation_id}}
    )
    
    # Save conversation
    await conv_storage.save_conversation(
        conversation_id,
        messages + [request.message, result["messages"][-1]]
    )
    
    return result
```

## Recipe 4: Streaming Responses

Stream agent responses in real-time.

```python
from cloudbase_agent.server import StreamingResponse

@server.post("/chat/stream")
async def chat_stream(request):
    async def generate():
        async for chunk in agent.astream(request.data):
            # Yield SSE format
            yield f"data: {json.dumps(chunk)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )
```

## Recipe 5: Human-in-the-Loop

Implement approval workflows.

```python
from cloudbase_agent.langgraph import interrupt
from cloudbase_agent.server.approval import ApprovalManager

approval_manager = ApprovalManager(storage)

@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email (requires approval)."""
    # Request approval
    approval_id = interrupt(
        "email_approval",
        data={"to": to, "subject": subject, "body": body}
    )
    
    # Wait for approval
    approved = approval_manager.wait_for_approval(approval_id)
    
    if approved:
        # Actually send email
        email_service.send(to, subject, body)
        return "Email sent successfully"
    else:
        return "Email cancelled by user"

# Approval endpoint
@server.post("/approve/{approval_id}")
async def approve(approval_id: str, approved: bool):
    await approval_manager.set_approval(approval_id, approved)
    return {"status": "ok"}
```

## Recipe 6: Tool-Based Generative UI

Generate UI components based on tool results.

```python
from cloudbase_agent.server import tool, ui_component

@tool
@ui_component("chart")
def analyze_data(dataset: str) -> dict:
    """Analyze dataset and return chart data."""
    data = load_dataset(dataset)
    analysis = perform_analysis(data)
    
    return {
        "type": "line_chart",
        "data": analysis["timeseries"],
        "config": {
            "xAxis": "date",
            "yAxis": "value",
            "title": f"Analysis of {dataset}"
        }
    }

# Frontend receives:
# {
#   "tool": "analyze_data",
#   "result": {...},
#   "ui": {
#     "component": "chart",
#     "props": {...}
#   }
# }
```

## Recipe 7: Rate Limiting

Implement request rate limiting.

```python
from cloudbase_agent.server.middleware import RateLimiter

rate_limiter = RateLimiter(
    storage=storage,
    requests_per_minute=60,
    burst=10
)

@server.post("/chat")
@rate_limiter.limit(key=lambda req: req.user_id)
async def chat(request):
    return await agent.ainvoke(request.data)
```

## Recipe 8: Authentication & Authorization

Secure agent endpoints.

```python
from cloudbase_agent.server.auth import APIKeyAuth, JWTAuth

# API Key auth
api_key_auth = APIKeyAuth(
    storage=storage,
    header="X-API-Key"
)

# JWT auth
jwt_auth = JWTAuth(
    secret="your-secret-key",
    algorithm="HS256"
)

@server.post("/chat")
@api_key_auth.require()
async def chat(request):
    user_id = request.auth.user_id
    return await agent.ainvoke(request.data)

@server.post("/admin/chat")
@jwt_auth.require(roles=["admin"])
async def admin_chat(request):
    return await admin_agent.ainvoke(request.data)
```

## Recipe 9: Error Recovery

Implement robust error handling.

```python
from cloudbase_agent.server.errors import AgentError, ToolError
from tenacity import retry, stop_after_attempt, retry_if_exception_type

@retry(
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type(ToolError)
)
async def invoke_with_retry(agent, input_data):
    try:
        return await agent.ainvoke(input_data)
    except ToolError as e:
        logger.warning(f"Tool error, retrying: {e}")
        raise
    except AgentError as e:
        logger.error(f"Agent error: {e}")
        return {"error": str(e), "fallback": "default_response"}
```

## Recipe 10: Monitoring & Alerting

Complete observability setup.

```python
from cloudbase_agent.server.observability import setup_observability
from cloudbase_agent.server.metrics import Counter, Histogram

# Setup
setup_observability(
    service_name="my-agent",
    enable_tracing=True,
    enable_metrics=True,
    enable_logging=True
)

# Custom metrics
agent_errors = Counter(
    "agent_errors_total",
    "Total agent errors",
    ["error_type"]
)

# Middleware
@server.middleware("http")
async def observability_middleware(request, call_next):
    with track_request(request):
        try:
            response = await call_next(request)
            return response
        except Exception as e:
            agent_errors.labels(error_type=type(e).__name__).inc()
            raise

# Alerts (example with Prometheus Alertmanager)
# rules.yml:
# - alert: HighErrorRate
#   expr: rate(agent_errors_total[5m]) > 0.1
#   annotations:
#     summary: "High error rate detected"
```

## Recipe 11: Background Tasks

Process long-running tasks asynchronously.

```python
from cloudbase_agent.server.tasks import TaskQueue

task_queue = TaskQueue(storage=storage)

@task_queue.task(name="process_document")
async def process_document(doc_id: str):
    """Process a document in the background."""
    document = load_document(doc_id)
    result = await agent.ainvoke({
        "task": "analyze",
        "document": document
    })
    save_result(doc_id, result)
    return result

@server.post("/documents/process")
async def submit_document(request):
    task_id = await process_document.delay(request.doc_id)
    return {"task_id": task_id, "status": "processing"}

@server.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    status = await task_queue.get_status(task_id)
    return status
```

## Recipe 12: Multi-Modal Agent

Handle text, images, and other media.

```python
from cloudbase_agent.server import tool
from langchain_openai import ChatOpenAI

@tool
def analyze_image(image_url: str) -> str:
    """Analyze an image and describe its contents."""
    # Vision model
    vision_model = ChatOpenAI(model="gpt-4-vision-preview")
    result = vision_model.invoke([
        {"type": "image_url", "image_url": image_url},
        {"type": "text", "text": "What's in this image?"}
    ])
    return result.content

# Multi-modal agent
agent = create_react_agent(
    model=ChatOpenAI(model="gpt-4-vision-preview"),
    tools=[analyze_image, search_web]
)
```

## See Also

- [Server Reference](./server.md) - Server API details
- [LangGraph Reference](./langgraph.md) - Agent patterns
- [Tools Reference](./tools.md) - Tool system
- [Storage Reference](./storage.md) - Data persistence
- [Observability Reference](./observability.md) - Monitoring
