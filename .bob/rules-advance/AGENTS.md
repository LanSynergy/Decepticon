# Decepticon Advance Mode — Agent Context

**Non-obvious rules for advance coding with MCP/Browser tools.**

## Skills System with MCP

### Skill Loading via MCP Filesystem

When using MCP filesystem tools, skills are still on host:

```python
# CORRECT: Use standard read_file for skills
read_file("/skills/recon/active-recon/SKILL.md")

# WRONG: MCP filesystem doesn't have /skills/ access
mcp_read_file("/skills/...")  # Will fail
```

**Why**: Skills route through `CompositeBackend` with `FilesystemBackend`, not MCP.

## Browser Tool Integration

### Skill-First for Web Recon

Load web recon skills before browser automation:

```python
# CORRECT: Load skill, then use browser
read_file("/skills/recon/web-recon/SKILL.md")
# Follow skill guidance for browser automation

# WRONG: Browser automation without skill context
browser_navigate("https://target.com")  # Missing OPSEC guidance
```

**Why**: Skills contain anti-detection patterns, rate limiting, and session management.

## MCP Server Configuration

### Docker Network Access

MCP servers must be on `decepticon-net` to reach services:

```yaml
# docker-compose.yml
services:
  mcp-server:
    networks:
      - decepticon-net
```

**Why**: Neo4j, LiteLLM proxy, sandbox all on internal network.

## Backend Routing with MCP

### Three-Tier Filesystem

```python
# Skills: Host FS (CompositeBackend route)
read_file("/skills/...")  # ✓ Works

# Workspace: Docker bind mount
bash("cat /workspace/...")  # ✓ Works

# MCP: External filesystem access
mcp_read_file("/external/...")  # ✓ Works (if MCP configured)
```

**Pattern**: Skills → host, workspace → Docker, external → MCP.

## OPPLAN with MCP Tools

### Tool Restrictions in Objectives

OPPLAN objectives can restrict tool usage:

```python
objective = {
    "allowed_tools": ["Bash", "Read", "Write"],  # No MCP/Browser
    "opsec_level": "STEALTH",
}
```

**Why**: High OPSEC objectives may prohibit browser fingerprinting.

**Location**: `decepticon/middleware/opplan.py`

## Browser Automation Patterns

### Session Management

Browser sessions persist across tool calls:

```python
# Session created on first navigate
browser_navigate("https://target.com")

# Reuse session for subsequent actions
browser_click("selector")
browser_screenshot()

# Explicit cleanup
browser_close()
```

**Gotcha**: Unclosed sessions consume memory. Always close after objective completion.

## MCP Knowledge Graph Integration

### External Data Ingestion

MCP can feed external data into Neo4j:

```python
# MCP fetches external intel
external_data = mcp_fetch_threat_intel(domain)

# Ingest into KG
kg_add_node(node_type="threat_actor", properties=external_data)
```

**Pattern**: MCP → Python dict → KG tools.

## Environment Variables for MCP

### MCP Server Discovery

```bash
# MCP servers configured via env
DECEPTICON_MCP_SERVERS='[{"name":"browser","url":"http://mcp-browser:8080"}]'
```

**Format**: JSON array of server configs.

**Location**: `decepticon/core/config.py` (if MCP support added)

## Testing with MCP

### Mock MCP Servers

```python
# tests/unit/mcp/test_integration.py
@pytest.fixture
def mock_mcp_server():
    """Mock MCP server for testing."""
    return MockMCPServer(responses={"read": "content"})
```

**Why**: Integration tests shouldn't depend on external MCP servers.

## Middleware Stack with MCP

### MCP Middleware Placement

```python
middleware = [
    DecepticonSkillsMiddleware(...),  # Skills first
    FilesystemMiddleware(...),
    MCPMiddleware(...),  # After filesystem, before fallback
    ModelFallbackMiddleware(...),
    SummarizationMiddleware(...),
]
```

**Why**: MCP tools need filesystem context but should fail over to model fallback.

## Browser OPSEC

### Anti-Detection Headers

Skills contain browser fingerprint randomization:

```python
# From /skills/recon/web-recon/SKILL.md
headers = {
    "User-Agent": random_user_agent(),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": previous_url,
}
```

**Pattern**: Load skill → extract headers → configure browser.

## MCP Error Handling

### Graceful Degradation

```python
try:
    result = mcp_tool(...)
except MCPConnectionError:
    # Fall back to bash/curl
    result = bash("curl -s https://...")
```

**Why**: MCP servers may be unavailable; agents should continue with core tools.

## Knowledge Graph via MCP

### Remote Graph Queries

MCP can query external graph databases:

```python
# Query external threat intel graph
external_nodes = mcp_graph_query("MATCH (n:ThreatActor) RETURN n")

# Merge into local KG
for node in external_nodes:
    kg_add_node(node_type="threat_actor", properties=node)
```

**Pattern**: External query → local ingestion → unified graph.

## Build System with MCP

### MCP Profile

```bash
# Start with MCP servers
make dev PROFILE=mcp

# Smoke test with MCP
make smoke PROFILE=mcp
```

**Location**: `Makefile` (if MCP profile added)

## Browser Session Limits

### Concurrent Session Cap

```python
MAX_BROWSER_SESSIONS = 3  # Per agent instance
```

**Why**: Browser automation is memory-intensive; limit concurrent sessions.

**Location**: Browser tool implementation (if added)