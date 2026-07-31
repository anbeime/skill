# CloudBase Agent Observability Reference

## Overview

CloudBase Agent provides comprehensive observability features including logging, metrics, and distributed tracing.

## Logging

### Basic Configuration

```python
from cloudbase_agent.server import create_server
import logging

server = create_server(
    log_level="INFO",
    log_format="json",  # or "text"
    log_output="stdout"  # or file path
)
```

### Structured Logging

```python
from cloudbase_agent.server.logging import get_logger

logger = get_logger(__name__)

# Structured log with context
logger.info(
    "Agent request received",
    extra={
        "conversation_id": "conv_123",
        "user_id": "user_456",
        "agent_type": "react",
        "duration_ms": 150
    }
)
```

### Log Levels

```python
logger.debug("Detailed debugging information")
logger.info("General information")
logger.warning("Warning messages")
logger.error("Error messages", exc_info=True)
logger.critical("Critical errors")
```

## Metrics

### Prometheus Metrics

```python
from cloudbase_agent.server.metrics import (
    Counter,
    Histogram,
    Gauge,
    Summary
)

# Define metrics
requests_total = Counter(
    "agent_requests_total",
    "Total agent requests",
    ["agent_type", "status"]
)

request_duration = Histogram(
    "agent_request_duration_seconds",
    "Request duration in seconds",
    ["agent_type"],
    buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
)

active_conversations = Gauge(
    "active_conversations",
    "Number of active conversations"
)

# Use metrics
requests_total.labels(agent_type="react", status="success").inc()
request_duration.labels(agent_type="react").observe(1.23)
active_conversations.set(42)
```

### Metrics Endpoint

```python
from cloudbase_agent.server import create_server

server = create_server(
    enable_metrics=True,
    metrics_path="/metrics"  # Default Prometheus endpoint
)
```

### Custom Metrics

```python
from cloudbase_agent.server.metrics import register_metric

# Register custom metric
tool_calls = Counter(
    "agent_tool_calls_total",
    "Total tool calls",
    ["tool_name", "status"]
)
register_metric(tool_calls)

# Use in tool
@tool
def my_tool(param: str) -> dict:
    try:
        result = do_work(param)
        tool_calls.labels(tool_name="my_tool", status="success").inc()
        return result
    except Exception as e:
        tool_calls.labels(tool_name="my_tool", status="error").inc()
        raise
```

## Distributed Tracing

### OpenTelemetry Setup

```python
from cloudbase_agent.server.tracing import configure_tracing

configure_tracing(
    service_name="my-agent-service",
    exporter="otlp",  # or "jaeger", "zipkin"
    endpoint="http://localhost:4317",
    sample_rate=1.0  # Sample all traces (0.0 to 1.0)
)
```

### Automatic Instrumentation

```python
from cloudbase_agent.server import create_server

# Enable automatic tracing
server = create_server(
    enable_tracing=True,
    trace_agent_runs=True,
    trace_tool_calls=True,
    trace_llm_calls=True
)
```

### Manual Tracing

```python
from cloudbase_agent.server.tracing import trace, get_current_span

@trace(name="custom_operation")
async def custom_operation(param: str):
    # Current span auto-created
    span = get_current_span()
    span.set_attribute("param_length", len(param))
    
    # Nested spans
    with trace("sub_operation"):
        result = await sub_operation(param)
    
    span.set_attribute("result_size", len(result))
    return result
```

### Trace Context Propagation

```python
from cloudbase_agent.server.tracing import inject_trace_context, extract_trace_context

# Inject context into HTTP headers
headers = {}
inject_trace_context(headers)

# Make HTTP request with context
async with httpx.AsyncClient() as client:
    response = await client.get(url, headers=headers)

# Extract context from incoming request
context = extract_trace_context(request.headers)
```

## Agent Run Tracking

### Automatic Tracking

```python
from cloudbase_agent.langgraph import create_react_agent

# Automatic run tracking enabled
agent = create_react_agent(
    model=model,
    tools=tools,
    enable_observability=True
)

# Each run automatically tracked with:
# - Run ID
# - Duration
# - Token usage
# - Tool calls
# - Errors
```

### Custom Run Metadata

```python
from cloudbase_agent.server.observability import track_run

@track_run(
    run_type="react_agent",
    metadata={"version": "1.0.0"}
)
async def invoke_agent(input_data: dict):
    result = await agent.ainvoke(input_data)
    return result
```

## Error Tracking

### Sentry Integration

```python
from cloudbase_agent.server.errors import configure_error_tracking

configure_error_tracking(
    dsn="https://xxx@sentry.io/xxx",
    environment="production",
    release="1.0.0",
    traces_sample_rate=0.1
)
```

### Error Context

```python
from cloudbase_agent.server.errors import capture_exception, set_error_context

set_error_context({
    "conversation_id": "conv_123",
    "user_id": "user_456"
})

try:
    result = risky_operation()
except Exception as e:
    capture_exception(e, extra={
        "operation": "risky_operation",
        "input": input_data
    })
    raise
```

## Health Checks

### Health Check Endpoint

```python
from cloudbase_agent.server import create_server

server = create_server(
    enable_health_check=True,
    health_check_path="/health"
)
```

### Custom Health Checks

```python
from cloudbase_agent.server.health import HealthCheck, HealthStatus

class DatabaseHealthCheck(HealthCheck):
    name = "database"
    
    async def check(self) -> HealthStatus:
        try:
            await db.execute("SELECT 1")
            return HealthStatus.HEALTHY
        except Exception as e:
            return HealthStatus.UNHEALTHY, str(e)

# Register
server.add_health_check(DatabaseHealthCheck())
```

## Performance Monitoring

### APM Integration

```python
from cloudbase_agent.server.apm import configure_apm

configure_apm(
    service_name="my-agent",
    server_url="http://apm-server:8200",
    environment="production"
)
```

### Performance Metrics

```python
from cloudbase_agent.server.metrics import track_performance

@track_performance(metric_name="agent_processing")
async def process_request(data: dict):
    # Automatically tracks:
    # - Duration
    # - Memory usage
    # - CPU time
    return await agent.ainvoke(data)
```

## Dashboard Integration

### Grafana Dashboard

CloudBase Agent provides pre-built Grafana dashboards:

```bash
# Import dashboard
curl -X POST http://grafana:3000/api/dashboards/import \
  -H "Content-Type: application/json" \
  -d @dashboards/cloudbase-agent-overview.json
```

### Custom Dashboards

Key metrics to monitor:

- `agent_requests_total` - Request volume
- `agent_request_duration_seconds` - Latency
- `agent_errors_total` - Error rate
- `active_conversations` - Concurrent users
- `llm_tokens_total` - Token usage
- `tool_calls_total` - Tool usage

## Best Practices

1. **Structured Logging**: Always use structured logs with context
2. **Metrics Labels**: Use consistent label names across metrics
3. **Trace Sampling**: Adjust sample rate based on traffic volume
4. **Error Context**: Include relevant context when capturing errors
5. **Health Checks**: Implement health checks for all dependencies
6. **Alerts**: Set up alerts for critical metrics

## Common Patterns

### Request Tracking

```python
from cloudbase_agent.server.observability import RequestTracker

async def handle_request(request):
    tracker = RequestTracker(request)
    
    try:
        result = await process_request(request.data)
        tracker.success(result)
        return result
    except Exception as e:
        tracker.error(e)
        raise
    finally:
        tracker.finalize()
```

### Performance Profiling

```python
from cloudbase_agent.server.profiling import profile

@profile(enabled=True)
async def expensive_operation(data):
    # Automatically profiles:
    # - Function calls
    # - Memory allocations
    # - I/O operations
    return await process(data)
```

## Troubleshooting

### High Latency

1. Check `agent_request_duration_seconds` histogram
2. Review trace spans to identify slow operations
3. Monitor `llm_response_time` metrics
4. Check tool execution times

### Error Spikes

1. Check `agent_errors_total` counter
2. Review error logs with `level=error`
3. Check Sentry for error details
4. Analyze error traces

### Memory Issues

1. Monitor `process_memory_bytes` gauge
2. Check for memory leaks in traces
3. Review conversation storage TTL settings
4. Analyze heap dumps if needed

## See Also

- [Server Reference](./server.md) - Server configuration
- [Storage Reference](./storage.md) - Storage monitoring
- [Recipes](./recipes.md) - Observability patterns
