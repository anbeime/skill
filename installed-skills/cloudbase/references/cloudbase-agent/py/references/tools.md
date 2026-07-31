# CloudBase Agent Tools System Reference

## Overview

CloudBase Agent provides a flexible tool system for integrating external capabilities into agents.

## Core Concepts

### Tool Definition

```python
from cloudbase_agent.server import tool

@tool
def search_database(query: str, limit: int = 10) -> list[dict]:
    """Search the database for matching records.
    
    Args:
        query: Search query string
        limit: Maximum number of results to return
        
    Returns:
        List of matching records
    """
    # Implementation
    return results
```

### Tool Registry

```python
from cloudbase_agent.server import ToolRegistry

# Create registry
registry = ToolRegistry()

# Register tools
registry.register(search_database)
registry.register(update_record)

# Get all tools
tools = registry.get_tools()
```

## Built-in Tool Types

### HTTP Tools

```python
from cloudbase_agent.server.tools import HttpTool

http_tool = HttpTool(
    name="fetch_data",
    method="GET",
    url="https://api.example.com/data",
    headers={"Authorization": "Bearer TOKEN"}
)
```

### Database Tools

```python
from cloudbase_agent.server.tools import DatabaseTool

db_tool = DatabaseTool(
    name="query_users",
    connection_string="postgresql://localhost/mydb",
    query="SELECT * FROM users WHERE active = true"
)
```

## Tool Execution

### Synchronous Execution

```python
result = await tool.execute({"query": "search term", "limit": 5})
```

### Async Tool Support

```python
@tool
async def async_search(query: str) -> dict:
    """Async tool example."""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.example.com/search?q={query}")
        return response.json()
```

## Tool Validation

### Input Validation

```python
from pydantic import BaseModel, Field

class SearchParams(BaseModel):
    query: str = Field(..., min_length=1, max_length=100)
    limit: int = Field(default=10, ge=1, le=100)

@tool
def validated_search(params: SearchParams) -> list[dict]:
    """Tool with Pydantic validation."""
    return search(params.query, params.limit)
```

## Error Handling

```python
from cloudbase_agent.server.tools import ToolError

@tool
def safe_operation(data: dict) -> dict:
    """Tool with error handling."""
    try:
        result = risky_operation(data)
        return {"success": True, "data": result}
    except ValueError as e:
        raise ToolError(f"Invalid input: {e}")
    except Exception as e:
        raise ToolError(f"Operation failed: {e}")
```

## Tool Metadata

```python
@tool(
    name="custom_name",
    description="Detailed description",
    tags=["search", "database"],
    version="1.0.0"
)
def advanced_tool(param: str) -> dict:
    """Advanced tool with metadata."""
    return {}
```

## Tool Composition

### Chaining Tools

```python
@tool
def fetch_and_process(query: str) -> dict:
    """Chain multiple operations."""
    # Fetch data
    raw_data = fetch_data(query)
    
    # Process data
    processed = process_data(raw_data)
    
    # Store results
    store_results(processed)
    
    return {"status": "complete", "count": len(processed)}
```

## Integration with Agents

### LangGraph Integration

```python
from cloudbase_agent.langgraph import create_react_agent

agent = create_react_agent(
    model=model,
    tools=[search_database, update_record, async_search]
)
```

### Custom Tool Nodes

```python
from langgraph.prebuilt import ToolNode

tool_node = ToolNode([search_database, update_record])

# Add to graph
graph.add_node("tools", tool_node)
```

## Best Practices

1. **Clear Descriptions**: Write detailed docstrings for AI to understand tool purpose
2. **Type Hints**: Always use type hints for parameters and return values
3. **Error Handling**: Catch and wrap errors with meaningful messages
4. **Validation**: Use Pydantic models for complex input validation
5. **Async Support**: Use async tools for I/O-bound operations
6. **Idempotency**: Make tools safe to retry when possible

## Common Patterns

### Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@tool
@retry(stop=stop_after_attempt(3), wait=wait_exponential())
async def resilient_api_call(endpoint: str) -> dict:
    """API call with automatic retries."""
    async with httpx.AsyncClient() as client:
        response = await client.get(endpoint)
        response.raise_for_status()
        return response.json()
```

### Caching Results

```python
from functools import lru_cache

@tool
@lru_cache(maxsize=100)
def cached_lookup(key: str) -> dict:
    """Cached database lookup."""
    return db.query(key)
```

## See Also

- [Server Reference](./server.md) - Server configuration
- [LangGraph Reference](./langgraph.md) - Agent integration
- [Recipes](./recipes.md) - Common use cases
