from prometheus_client import Counter, Histogram

# 메트릭 정의
TOOL_CALL_COUNT = Counter(
    "mcp_tool_calls_total", 
    "Total tool calls", 
    ["tool_name", "status"]
)
TOOL_LATENCY = Histogram(
    "mcp_tool_latency_seconds", 
    "Tool execution latency", 
    ["tool_name"]
)
AUTH_FAILURES = Counter(
    "mcp_auth_failures_total", 
    "Authentication failures"
)