# CloudBase Agent Storage System Reference

## Overview

CloudBase Agent provides a unified storage interface for managing agent state, conversation history, and persistent data.

## Storage Interface

### Basic Operations

```python
from cloudbase_agent.server.storage import Storage

# Initialize storage
storage = Storage(backend="redis", url="redis://localhost:6379")

# Store data
await storage.set("key", {"data": "value"})

# Retrieve data
data = await storage.get("key")

# Delete data
await storage.delete("key")

# Check existence
exists = await storage.exists("key")
```

## Storage Backends

### Redis Backend

```python
from cloudbase_agent.server.storage import RedisStorage

storage = RedisStorage(
    url="redis://localhost:6379",
    db=0,
    decode_responses=True,
    max_connections=10
)
```

### Memory Backend (Development)

```python
from cloudbase_agent.server.storage import MemoryStorage

storage = MemoryStorage()  # In-memory, no persistence
```

### PostgreSQL Backend

```python
from cloudbase_agent.server.storage import PostgresStorage

storage = PostgresStorage(
    connection_string="postgresql://user:pass@localhost/cloudbase_agent_db",
    table_name="agent_storage"
)
```

## Conversation Storage

### Store Conversation State

```python
from cloudbase_agent.server.storage import ConversationStorage

conv_storage = ConversationStorage(storage)

# Save conversation
await conv_storage.save_conversation(
    conversation_id="conv_123",
    messages=[
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ],
    metadata={"user_id": "user_456"}
)

# Load conversation
conversation = await conv_storage.load_conversation("conv_123")
```

### Conversation History

```python
# Get all conversations for a user
conversations = await conv_storage.list_conversations(
    user_id="user_456",
    limit=10,
    offset=0
)

# Search conversations
results = await conv_storage.search_conversations(
    query="agent features",
    user_id="user_456"
)
```

## Checkpointing

### LangGraph Checkpointer

```python
from cloudbase_agent.langgraph import create_checkpointer

# Create checkpointer from storage
checkpointer = create_checkpointer(storage)

# Use with LangGraph
graph = create_react_agent(
    model=model,
    tools=tools,
    checkpointer=checkpointer
)
```

### Manual Checkpointing

```python
# Save checkpoint
await checkpointer.put(
    config={"configurable": {"thread_id": "thread_123"}},
    checkpoint={
        "values": graph_state,
        "next": ["tool_node"],
        "metadata": {"step": 5}
    }
)

# Load checkpoint
checkpoint = await checkpointer.get(
    config={"configurable": {"thread_id": "thread_123"}}
)
```

## TTL and Expiration

```python
# Set data with TTL
await storage.set("temp_key", {"data": "value"}, ttl=3600)  # 1 hour

# Update TTL
await storage.expire("temp_key", ttl=7200)  # 2 hours

# Get TTL
remaining = await storage.ttl("temp_key")
```

## Batch Operations

```python
# Batch set
await storage.mset({
    "key1": {"value": 1},
    "key2": {"value": 2},
    "key3": {"value": 3}
})

# Batch get
values = await storage.mget(["key1", "key2", "key3"])

# Batch delete
await storage.delete_many(["key1", "key2", "key3"])
```

## Namespacing

```python
# Create namespaced storage
user_storage = storage.namespace("user:123")

# Operations are automatically prefixed
await user_storage.set("preferences", {"theme": "dark"})
# Actually stores at "user:123:preferences"

# Nested namespaces
session_storage = user_storage.namespace("session:456")
# Keys stored at "user:123:session:456:*"
```

## Transactions

### Redis Transactions

```python
async with storage.transaction() as txn:
    await txn.set("counter", 0)
    value = await txn.get("counter")
    await txn.set("counter", value + 1)
    # Auto-commits on successful exit
```

### PostgreSQL Transactions

```python
async with storage.transaction() as txn:
    await txn.execute("UPDATE users SET balance = balance - 100 WHERE id = 1")
    await txn.execute("UPDATE users SET balance = balance + 100 WHERE id = 2")
    # Auto-commits or rolls back
```

## Serialization

### Custom Serializers

```python
from cloudbase_agent.server.storage import Storage, JSONSerializer, PickleSerializer

# JSON serializer (default)
storage = Storage(backend="redis", serializer=JSONSerializer())

# Pickle serializer (Python objects)
storage = Storage(backend="redis", serializer=PickleSerializer())

# Custom serializer
class CustomSerializer:
    def serialize(self, obj):
        return msgpack.packb(obj)
    
    def deserialize(self, data):
        return msgpack.unpackb(data)

storage = Storage(backend="redis", serializer=CustomSerializer())
```

## Monitoring

### Storage Metrics

```python
# Get storage stats
stats = await storage.stats()
# Returns: {
#     "keys_count": 1234,
#     "memory_usage": 5242880,  # bytes
#     "hit_rate": 0.95
# }

# Health check
is_healthy = await storage.health_check()
```

## Migration

### Data Migration

```python
from cloudbase_agent.server.storage import migrate_storage

# Migrate from Redis to PostgreSQL
await migrate_storage(
    source=redis_storage,
    destination=postgres_storage,
    batch_size=100,
    transform_fn=lambda k, v: (k, transform(v))
)
```

## Best Practices

1. **Use Namespacing**: Organize keys with namespaces to avoid collisions
2. **Set Appropriate TTLs**: Use TTL for temporary data to prevent memory bloat
3. **Batch Operations**: Use batch operations for multiple keys to reduce latency
4. **Connection Pooling**: Configure connection pools for production workloads
5. **Error Handling**: Always handle storage errors gracefully
6. **Monitoring**: Track storage metrics and set up alerts

## Common Patterns

### Session Management

```python
class SessionManager:
    def __init__(self, storage: Storage):
        self.storage = storage.namespace("sessions")
    
    async def create_session(self, user_id: str) -> str:
        session_id = generate_session_id()
        await self.storage.set(
            session_id,
            {"user_id": user_id, "created_at": datetime.now()},
            ttl=3600  # 1 hour
        )
        return session_id
    
    async def get_session(self, session_id: str) -> dict | None:
        return await self.storage.get(session_id)
```

### Rate Limiting

```python
async def rate_limit(user_id: str, limit: int = 100, window: int = 3600):
    key = f"rate_limit:{user_id}"
    count = await storage.get(key) or 0
    
    if count >= limit:
        raise RateLimitError("Too many requests")
    
    await storage.set(key, count + 1, ttl=window)
```

## See Also

- [Server Reference](./server.md) - Server configuration
- [LangGraph Reference](./langgraph.md) - Checkpointing integration
- [Recipes](./recipes.md) - Storage use cases
