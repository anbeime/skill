# Coze Adapter

This guide covers using the Coze platform integration with CloudBase Agent Python SDK.

## Overview

The Coze adapter allows you to use Coze's hosted AI bots as your backend, while still exposing them through the AG-UI protocol. This is useful when:

- You want to leverage Coze's bot building capabilities
- You need to integrate Coze bots into AG-UI-compatible frontends
- You want unified authentication and middleware with other adapters

## Installation

Coze adapter is included in the `cloudbase-agent-coze` package:

```bash
pip install cloudbase-agent-coze
```

## Basic Usage

```python
from cloudbase_agent.coze import CozeAgentAdapter
from cloudbase_agent.server import AgentServiceApp

def create_agent():
    return CozeAgentAdapter(
        bot_id="your-bot-id",
        api_key="your-api-key"
    )

AgentServiceApp().run(create_agent, port=8000)
```

## Configuration

### Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `bot_id` | `str` | Coze bot identifier |
| `api_key` | `str` | Coze API key |

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `base_url` | `str` | `https://api.coze.com` | Coze API endpoint |
| `debug_mode` | `bool` | `False` | Enable debug logging |

### Example with All Options

```python
adapter = CozeAgentAdapter(
    bot_id="bot_1234567890",
    api_key="sk-1234567890",
    base_url="https://api.coze.com",
    debug_mode=True
)
```

## Authentication Integration

The Coze adapter automatically extracts user ID from the request context set by authentication middleware.

### Server Setup with Auth

```python
from cloudbase_agent.server import AgentServiceApp
from cloudbase_agent.coze import CozeAgentAdapter
import jwt

def auth_middleware(input_data, request):
    """Extract user from JWT and inject into state."""
    token = request.headers.get("Authorization", "").replace("Bearer ", "")
    
    if token:
        jwt_payload = jwt.decode(token, "your-secret", algorithms=["HS256"])
        
        if input_data.state is None:
            input_data.state = {}
        
        # Inject user ID (Coze adapter reads from here)
        input_data.state["__request_context__"] = {
            "user": {
                "id": jwt_payload["sub"],
                "jwt": jwt_payload
            }
        }
    
    yield

def create_agent():
    return CozeAgentAdapter(
        bot_id="your-bot-id",
        api_key="your-api-key"
    )

app = AgentServiceApp()
app.use(auth_middleware)
app.run(create_agent, port=8000)
```

### User ID Extraction

The Coze adapter reads user ID from:
```python
state["__request_context__"]["user"]["id"]
```

This is used as the `user_id` parameter when calling Coze API, enabling:
- User-specific conversation history
- Multi-tenant isolation
- Personalized responses

## Environment Variables

For production, use environment variables:

```bash
# .env
COZE_BOT_ID=bot_1234567890
COZE_API_KEY=sk-1234567890
COZE_BASE_URL=https://api.coze.com  # optional
```

```python
import os
from cloudbase_agent.coze import CozeAgentAdapter

def create_agent():
    return CozeAgentAdapter(
        bot_id=os.getenv("COZE_BOT_ID"),
        api_key=os.getenv("COZE_API_KEY"),
        base_url=os.getenv("COZE_BASE_URL", "https://api.coze.com")
    )
```

## Error Handling

The Coze adapter handles common errors and emits AG-UI ERROR events:

### Common Errors

| Error | Description | Solution |
|-------|-------------|----------|
| `user_id not found` | No user ID in state | Ensure auth middleware is registered |
| `Invalid API key` | Coze API key is invalid | Check COZE_API_KEY |
| `Bot not found` | Bot ID doesn't exist | Verify COZE_BOT_ID |
| `Rate limit exceeded` | Too many requests | Implement rate limiting middleware |

### Custom Error Handling

```python
from cloudbase_agent.coze import CozeAgentAdapter

def create_agent():
    adapter = CozeAgentAdapter(
        bot_id="your-bot-id",
        api_key="your-api-key",
        debug_mode=True  # Enable debug logging
    )
    return adapter
```

## Features

### Streaming Responses

Coze adapter automatically streams responses from the Coze API:

```
TEXT_MESSAGE_START
TEXT_MESSAGE_CONTENT (chunk 1)
TEXT_MESSAGE_CONTENT (chunk 2)
...
TEXT_MESSAGE_END
```

### Tool Support

If your Coze bot uses tools, tool calls are automatically handled and streamed as AG-UI TOOL_CALL events.

### Conversation History

Coze maintains conversation history on their platform. Pass `threadId` in requests to continue conversations:

```json
{
  "messages": [...],
  "threadId": "conversation-123"
}
```

## Complete Example

```python
# app.py
import os
import jwt
from cloudbase_agent.server import AgentServiceApp
from cloudbase_agent.coze import CozeAgentAdapter
from cloudbase_agent.server.send_message.models import RunAgentInput
from fastapi import Request
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# JWT configuration
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "dev-secret")
JWT_ALGORITHM = "HS256"

def auth_middleware(input_data: RunAgentInput, request: Request):
    """Extract user from JWT and inject into state."""
    auth_header = request.headers.get("Authorization", "")
    
    if not auth_header.startswith("Bearer "):
        logger.warning("Missing or invalid Authorization header")
        # For development, use a default user ID
        if input_data.state is None:
            input_data.state = {}
        input_data.state["__request_context__"] = {
            "user": {"id": "anonymous"}
        }
        yield
        return
    
    token = auth_header[7:]
    
    try:
        jwt_payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        
        if input_data.state is None:
            input_data.state = {}
        
        input_data.state["__request_context__"] = {
            "user": {
                "id": jwt_payload["sub"],
                "jwt": jwt_payload
            }
        }
        
        logger.info(f"Authenticated user: {jwt_payload['sub']}")
        
    except jwt.InvalidTokenError as e:
        logger.error(f"JWT validation failed: {e}")
        raise
    
    yield

def logging_middleware(input_data, request):
    """Log request details."""
    logger.info(f"Request: {request.url.path}")
    logger.info(f"Run ID: {input_data.runId}")
    logger.info(f"Thread ID: {input_data.threadId}")
    
    yield
    
    logger.info("Request completed")

def create_agent():
    """Create Coze agent adapter."""
    return CozeAgentAdapter(
        bot_id=os.getenv("COZE_BOT_ID"),
        api_key=os.getenv("COZE_API_KEY"),
        debug_mode=os.getenv("DEBUG", "false").lower() == "true"
    )

# Create and configure app
app = AgentServiceApp()
app.set_cors_config(allow_origins=["*"])
app.use(logging_middleware)
app.use(auth_middleware)

if __name__ == "__main__":
    app.run(
        create_agent,
        port=int(os.getenv("PORT", "8000")),
        host="0.0.0.0"
    )
```

## Deployment

### Local Development

```bash
export COZE_BOT_ID=your-bot-id
export COZE_API_KEY=your-api-key
export JWT_SECRET_KEY=your-dev-secret

python app.py
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

ENV PORT=8000

CMD ["python", "app.py"]
```

```bash
docker build -t coze-agent .
docker run -p 8000:8000 \
  -e COZE_BOT_ID=your-bot-id \
  -e COZE_API_KEY=your-api-key \
  -e JWT_SECRET_KEY=your-secret \
  coze-agent
```

### CloudRun (Tencent Cloud)

```yaml
# cloudbaserc.json
{
  "envId": "your-env-id",
  "services": [{
    "name": "coze-agent",
    "path": "./",
    "runtime": "Python3.9",
    "port": 8000,
    "env": {
      "COZE_BOT_ID": "${COZE_BOT_ID}",
      "COZE_API_KEY": "${COZE_API_KEY}",
      "JWT_SECRET_KEY": "${JWT_SECRET_KEY}"
    }
  }]
}
```

## Testing

```python
import pytest
from cloudbase_agent.coze import CozeAgentAdapter
from cloudbase_agent.core import RunAgentInput

@pytest.mark.asyncio
async def test_coze_adapter():
    """Test Coze adapter basic flow."""
    adapter = CozeAgentAdapter(
        bot_id="test-bot",
        api_key="test-key"
    )
    
    run_input = RunAgentInput(
        runId="test-run",
        threadId="test-thread",
        messages=[{"role": "user", "content": "Hello"}],
        state={"__request_context__": {"user": {"id": "test-user"}}}
    )
    
    events = []
    async for event in adapter.run(run_input):
        events.append(event)
    
    # Verify event flow
    assert events[0].type == "RUN_STARTED"
    assert events[-1].type == "RUN_FINISHED"
```

## Troubleshooting

### "user_id not found" Error

**Problem**: Coze adapter can't find user ID in state.

**Solution**: Ensure auth middleware is registered and sets `state.__request_context__.user.id`:
```python
app.use(auth_middleware)  # Register before run()
```

### "Invalid API key" Error

**Problem**: Coze API key is invalid.

**Solution**: 
1. Check your Coze API key
2. Verify it's correctly set in environment variables
3. Test with Coze API directly

### Rate Limiting

**Problem**: Hitting Coze API rate limits.

**Solution**: Implement rate limiting middleware:
```python
def rate_limit_middleware(input_data, request):
    # Implement rate limiting logic
    yield
```

## Examples

See `/python-sdk/examples/coze/` for complete examples.

## Next Steps

- Learn about [authentication](authentication.md)
- Deploy your server: [server-quickstart.md](server-quickstart.md)
- Build UI: [ui-clients.md](ui-clients.md)
