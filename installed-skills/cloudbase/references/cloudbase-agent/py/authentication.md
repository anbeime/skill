# Authentication and User Context

This guide explains how to implement authentication and manage user context in CloudBase Agent Python SDK using the framework's reserved fields pattern.

## Overview

CloudBase Agent uses a standardized approach for passing user context through the request lifecycle:

```
HTTP Request (JWT in header)
  ↓ (middleware extracts)
state["__request_context__"]["user"]["id"]
state["__request_context__"]["user"]["jwt"]
  ↓ (available to)
Agent / Adapter / Tools
```

## Framework Reserved Fields

CloudBase Agent reserves specific fields in `state` for user authentication:

| Field | Type | Description | Access |
|-------|------|-------------|--------|
| `state["__request_context__"]["user"]["id"]` | `str` | User identifier | Read-only (set by middleware) |
| `state["__request_context__"]["user"]["jwt"]` | `dict` | JWT payload | Read-only (set by middleware) |

**⚠️ Security Warning**: These fields are set by authentication middleware and should be treated as read-only. Modifying them in your agent logic may lead to security vulnerabilities.

## Implementation Pattern

### 1. Authentication Middleware (Write)

Middleware extracts user information from the request and injects it into `state`:

```python
import jwt
from fastapi import Request
from cloudbase_agent.server.send_message.models import RunAgentInput
from typing import Generator

def auth_middleware(
    input_data: RunAgentInput, 
    request: Request
) -> Generator[None, None, None]:
    """
    Extract user from JWT and inject into state.
    
    This middleware:
    1. Extracts JWT from Authorization header
    2. Verifies the token
    3. Injects user info into framework reserved fields
    """
    # Extract token
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "")
    
    if token:
        try:
            # Verify JWT (use your own secret and algorithm)
            jwt_payload = jwt.decode(
                token, 
                "your-secret-key", 
                algorithms=["HS256"]
            )
            
            # Initialize state if needed
            if input_data.state is None:
                input_data.state = {}
            
            # ✅ Inject into framework reserved fields
            input_data.state["__request_context__"] = {
                "user": {
                    "id": jwt_payload["sub"],  # User ID from JWT sub claim
                    "jwt": jwt_payload         # Full JWT payload
                }
            }
            
        except jwt.InvalidTokenError as e:
            # Handle invalid token (log but don't block in this example)
            print(f"Invalid JWT token: {e}")
            # You could raise an exception here to block the request
            # raise InvalidRequestError(message="Invalid authentication token")
    
    yield  # Continue to next middleware or agent
```

### 2. Register Middleware

```python
from cloudbase_agent.server import AgentServiceApp

app = AgentServiceApp()
app.use(auth_middleware)  # Register before run()
app.run(create_agent, port=8000)
```

### 3. Adapter/Agent (Read)

In your adapter or agent, read the user information:

```python
def get_user_id_from_state(state: dict) -> str:
    """
    Safely extract user ID from framework reserved field.
    
    :param state: Agent state dictionary
    :return: User ID string
    :raises ValueError: If user ID not found
    """
    request_context = state.get("__request_context__", {})
    user = request_context.get("user", {})
    user_id = user.get("id")
    
    if not user_id:
        raise ValueError(
            "user_id is required but not found in "
            "state.__request_context__.user.id. "
            "Please ensure auth middleware is registered."
        )
    
    return user_id

# Usage in agent
def my_agent_function(state: dict):
    user_id = get_user_id_from_state(state)
    jwt_payload = state.get("__request_context__", {}).get("user", {}).get("jwt", {})
    
    # Use user_id and jwt_payload for your logic
    user_data = fetch_user_data(user_id)
    # ...
```

## Example: Complete Authentication Flow

### Step 1: Define Authentication Middleware

```python
# auth.py
import jwt
from fastapi import Request, HTTPException
from cloudbase_agent.server.send_message.models import RunAgentInput
from cloudbase_agent.server.errors.exceptions import InvalidRequestError
from typing import Generator

# Your JWT configuration
JWT_SECRET = "your-secret-key"
JWT_ALGORITHM = "HS256"

def jwt_auth_middleware(
    input_data: RunAgentInput,
    request: Request
) -> Generator[None, None, None]:
    """
    JWT authentication middleware.
    
    Extracts and verifies JWT, then injects user info into state.
    Raises error if token is invalid or missing for protected routes.
    """
    # Extract Authorization header
    auth_header = request.headers.get("Authorization", "")
    
    if not auth_header:
        raise InvalidRequestError(
            message="Missing Authorization header",
            details={"header": "Authorization"}
        )
    
    # Parse Bearer token
    if not auth_header.startswith("Bearer "):
        raise InvalidRequestError(
            message="Invalid Authorization header format. Expected 'Bearer <token>'",
            details={"format": "Bearer <token>"}
        )
    
    token = auth_header[7:]  # Remove "Bearer " prefix
    
    try:
        # Verify and decode JWT
        jwt_payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )
        
        # Validate required claims
        if "sub" not in jwt_payload:
            raise InvalidRequestError(
                message="JWT missing 'sub' claim",
                details={"claim": "sub"}
            )
        
        # Initialize state if needed
        if input_data.state is None:
            input_data.state = {}
        
        # Inject user info into framework reserved fields
        input_data.state["__request_context__"] = {
            "user": {
                "id": jwt_payload["sub"],
                "jwt": jwt_payload
            }
        }
        
        # Log successful authentication (optional)
        print(f"Authenticated user: {jwt_payload['sub']}")
        
    except jwt.ExpiredSignatureError:
        raise InvalidRequestError(
            message="JWT token has expired",
            details={"error": "expired"}
        )
    except jwt.InvalidTokenError as e:
        raise InvalidRequestError(
            message=f"Invalid JWT token: {str(e)}",
            details={"error": "invalid_token"}
        )
    
    yield  # Continue to agent execution
```

### Step 2: Use in Coze Adapter

```python
# agent.py
from cloudbase_agent.coze import CozeAgentAdapter
from cloudbase_agent.server import AgentServiceApp
from auth import jwt_auth_middleware

def create_agent():
    """
    Create Coze agent.
    User ID will be automatically extracted from state by the adapter.
    """
    return CozeAgentAdapter(
        bot_id="your-bot-id",
        api_key="your-api-key"
    )

# Start server with auth middleware
app = AgentServiceApp()
app.use(jwt_auth_middleware)  # Register auth middleware
app.run(create_agent, port=8000)
```

### Step 3: Coze Adapter Internal Logic

The Coze adapter reads user ID automatically:

```python
# Inside cloudbase_agent.coze.agent.py (framework code)
class CozeAgentAdapter:
    def _get_user_id(self, run_input: RunAgentInput) -> str:
        """Get user_id from state.__request_context__.user.id."""
        state = run_input.state or {}
        
        # Read from framework reserved field
        request_context = state.get("__request_context__", {})
        user_info = request_context.get("user", {})
        user_id = user_info.get("id")
        
        if not user_id:
            raise ValueError(
                "user_id is required but not found in "
                "state.__request_context__.user.id. "
                "Please ensure auth middleware is registered."
            )
        
        return user_id.strip()
```

## Custom User Context Fields

You can add custom fields alongside framework reserved fields:

```python
def auth_middleware(input_data: RunAgentInput, request: Request):
    """Auth middleware with custom fields."""
    # Verify JWT
    jwt_payload = verify_jwt(extract_token(request))
    
    # Initialize state
    if input_data.state is None:
        input_data.state = {}
    
    # Set framework reserved fields + custom fields
    input_data.state["__request_context__"] = {
        "user": {
            "id": jwt_payload["sub"],       # ← Framework reserved
            "jwt": jwt_payload,             # ← Framework reserved
        },
        # ✅ Custom fields (allowed)
        "tenant_id": jwt_payload.get("tenant_id"),
        "permissions": jwt_payload.get("permissions", []),
        "session_id": request.headers.get("X-Session-ID"),
    }
    
    yield

# Usage in agent
def my_agent(state: dict):
    # Read framework reserved fields
    user_id = state["__request_context__"]["user"]["id"]
    
    # Read custom fields
    tenant_id = state["__request_context__"].get("tenant_id")
    permissions = state["__request_context__"].get("permissions", [])
    
    if "admin" not in permissions:
        raise PermissionError("Admin permission required")
```

## Security Best Practices

### 1. Use Strong Secrets

```python
import os

JWT_SECRET = os.environ.get("JWT_SECRET_KEY")
if not JWT_SECRET or len(JWT_SECRET) < 32:
    raise ValueError("JWT_SECRET_KEY must be at least 32 characters")
```

### 2. Validate All Claims

```python
def validate_jwt_payload(payload: dict) -> None:
    """Validate JWT payload structure."""
    required_claims = ["sub", "exp", "iat"]
    
    for claim in required_claims:
        if claim not in payload:
            raise ValueError(f"Missing required claim: {claim}")
    
    # Validate expiration (PyJWT does this automatically, but double-check)
    import time
    if payload["exp"] < time.time():
        raise ValueError("Token expired")
```

### 3. Implement Token Refresh

```python
def refresh_token_middleware(input_data, request):
    """Check token expiration and handle refresh."""
    jwt_payload = input_data.state.get("__request_context__", {}).get("user", {}).get("jwt", {})
    
    # Check if token expires soon (e.g., within 5 minutes)
    if jwt_payload.get("exp", 0) - time.time() < 300:
        # Add header to response suggesting refresh
        request.state.should_refresh_token = True
    
    yield
```

### 4. Rate Limit by User

```python
from collections import defaultdict
from time import time

user_request_counts = defaultdict(list)

def rate_limit_by_user_middleware(input_data, request):
    """Rate limit per user ID."""
    user_id = input_data.state.get("__request_context__", {}).get("user", {}).get("id")
    
    if user_id:
        now = time()
        # Clean old requests
        user_request_counts[user_id] = [
            t for t in user_request_counts[user_id]
            if now - t < 60  # 1-minute window
        ]
        
        if len(user_request_counts[user_id]) >= 10:
            raise Exception(f"Rate limit exceeded for user {user_id}")
        
        user_request_counts[user_id].append(now)
    
    yield
```

## Testing Authentication

### Unit Test

```python
import pytest
from fastapi import Request
from cloudbase_agent.server.send_message.models import RunAgentInput
from auth import jwt_auth_middleware

def test_auth_middleware_with_valid_token():
    """Test middleware with valid JWT."""
    # Create mock request with valid token
    token = create_test_jwt({"sub": "user123"})
    request = Request(scope={
        "type": "http",
        "headers": [(b"authorization", f"Bearer {token}".encode())]
    })
    
    input_data = RunAgentInput(
        messages=[],
        runId="test-run",
        threadId="test-thread"
    )
    
    # Execute middleware
    gen = jwt_auth_middleware(input_data, request)
    next(gen)
    
    # Verify user info was injected
    assert input_data.state["__request_context__"]["user"]["id"] == "user123"

def test_auth_middleware_with_missing_token():
    """Test middleware rejects missing token."""
    request = Request(scope={"type": "http", "headers": []})
    input_data = RunAgentInput(messages=[], runId="test", threadId="test")
    
    with pytest.raises(InvalidRequestError):
        gen = jwt_auth_middleware(input_data, request)
        next(gen)
```

### Integration Test

```python
from fastapi.testclient import TestClient

def test_authenticated_request():
    """Test full request with authentication."""
    client = TestClient(app)
    
    token = create_test_jwt({"sub": "user123"})
    
    response = client.post(
        "/send-message",
        json={"messages": [{"role": "user", "content": "Hello"}]},
        headers={"Authorization": f"Bearer {token}"}
    )
    
    assert response.status_code == 200
```

## Migration from forwarded_props

If you're migrating from the old `forwarded_props` pattern:

### Before (Old Pattern)

```python
# ❌ Old: forwarded_props
def create_jwt_preprocessor():
    def jwt_preprocessor(request: RunAgentInput, http_context: Request):
        user_id = extract_user_id_from_request(http_context)
        if not request.forwarded_props:
            request.forwarded_props = {}
        request.forwarded_props["user_id"] = user_id
    return jwt_preprocessor
```

### After (New Pattern)

```python
# ✅ New: state.__request_context__
def auth_middleware(input_data: RunAgentInput, request: Request):
    user_id = extract_user_id_from_request(request)
    
    if input_data.state is None:
        input_data.state = {}
    
    input_data.state["__request_context__"] = {
        "user": {"id": user_id}
    }
    yield
```

## Summary

| Aspect | Implementation |
|--------|---------------|
| **Write (Middleware)** | `state["__request_context__"]["user"]["id"] = user_id` |
| **Read (Adapter)** | `state.get("__request_context__", {}).get("user", {}).get("id")` |
| **Security** | Verify JWT, validate claims, use strong secrets |
| **Custom Fields** | Add alongside reserved fields in `__request_context__` |
| **Testing** | Unit test middleware, integration test full flow |

## Next Steps

- Learn about [server deployment](server-quickstart.md)
- Understand [middleware patterns](server-quickstart.md#middleware-system)
- Integrate with [Coze adapter](adapter-coze.md)
- Build [UI clients](ui-clients.md)
