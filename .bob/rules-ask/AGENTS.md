# Decepticon Ask Mode — Agent Context

**Non-obvious documentation context for answering questions.**

## Skills System Documentation

### Skill Catalog Structure

Skills are NOT flat documentation - they're executable knowledge:

```
skills/
├── recon/
│   ├── active-recon/SKILL.md      # Loaded at runtime
│   │   └── references/            # Supporting docs
│   └── passive-recon/SKILL.md
└── shared/
    └── opsec/SKILL.md              # Cross-cutting concerns
```

**Key insight**: Each SKILL.md is a runtime-loaded knowledge module, not static docs.

**Location**: `skills/` directory structure

### Skill Frontmatter Semantics

```yaml
---
name: active-recon
allowed-tools: Bash Read Write  # Space-separated, NOT list
metadata:
  subdomain: reconnaissance      # Kill chain phase
  when_to_use: "port scan, nmap" # Trigger keywords
  mitre_attack: T1595, T1595.001 # ATT&CK techniques
---
```

**Non-obvious**: `allowed-tools` parsing as string split is intentional for middleware efficiency.

**Location**: `decepticon/middleware/skills.py:122-150`

## Architecture Documentation

### Backend Routing Rationale

CompositeBackend exists because:
1. Skills must be read-only (prevent agent modification)
2. Skills live on host (version controlled)
3. Execution happens in Docker (isolation)

**Not documented elsewhere**: This is a security boundary, not just convenience.

**Location**: `decepticon/agents/recon.py:85-88`

### Why No create_deep_agent()

`create_deep_agent()` provides:
- Generic middleware stack
- TodoListMiddleware (wrong for red team)
- SubAgentMiddleware (conflicts with Decepticon orchestrator)

**Design decision**: Decepticon needs precise middleware control per agent role.

**Location**: All `decepticon/agents/*.py` files use `create_agent()`

## OPPLAN System Documentation

### OPPLAN vs Generic Task Tracking

OPPLAN is NOT a todo list because:
- Objectives have kill chain phases (RECON → INITIAL_ACCESS → ...)
- MITRE ATT&CK technique tracking
- OPSEC level per objective (STEALTH, BALANCED, AGGRESSIVE)
- C2 tier requirements (TIER_1, TIER_2, TIER_3)
- Blocked-by dependency chains
- Acceptance criteria validation

**Key insight**: Red team operations require domain-specific task semantics.

**Location**: `decepticon/middleware/opplan.py`, `docs/design/opplan-middleware.md`

### Objective Hierarchy

```python
OBJ-001: "Enumerate network"
  ├── OBJ-002: "Port scan 192.168.1.0/24"
  └── OBJ-003: "Service fingerprinting"
```

**Non-obvious**: Hierarchical objectives enable progressive disclosure - parent blocked until children complete.

**Location**: `decepticon/middleware/opplan.py:809-952` (objective_expand)

## Tmux Session Documentation

### Why Tmux Instead of Direct Exec

Direct `docker exec` limitations:
- No session persistence (each call is new shell)
- No interactive input support (passwords, y/n prompts)
- No background job management
- No output streaming for long commands

**Tmux solves**: Persistent sessions + interactive input + background jobs.

**Location**: `decepticon/backends/docker_sandbox.py:87-496`

### PS1 Marker Design

```bash
PS1="[DCPTN:$?:$PWD] "
```

**Why this format**:
- `$?` = exit code (success/failure detection)
- `$PWD` = current directory (context tracking)
- `DCPTN` prefix = unique marker (won't collide with command output)

**Non-obvious**: Marker counting (not regex matching) enables detection even when output contains similar patterns.

**Location**: `decepticon/backends/docker_sandbox.py:46`

## Output Management Documentation

### Three-Tier Threshold Rationale

```python
30K chars   → Truncate (preserve context)
60 seconds  → Background (free agent for other work)
5M chars    → Kill (prevent memory exhaustion)
```

**Design decision**: Balance between:
- Context preservation (agents need output to decide next steps)
- Resource limits (prevent OOM)
- Agent productivity (don't block on long scans)

**Location**: `decepticon/backends/docker_sandbox.py:51-56`

### Asymmetric Truncation

60% head / 40% tail because:
- Headers contain structure (nmap service banners, nuclei templates)
- Tail contains results (found vulnerabilities, open ports)
- Middle is often repetitive (scan progress, closed ports)

**Non-obvious**: This is empirically optimized for security tool output patterns.

**Location**: `decepticon/backends/docker_sandbox.py:553-573`

## Model Configuration Documentation

### Profile Design

```
eco  → Haiku + Gemini fallback  (production, cost-optimized)
max  → Opus everywhere           (high-value targets, accuracy-first)
test → Haiku only, no fallback   (CI, deterministic)
```

**Why three profiles**: Different engagement contexts require different cost/accuracy tradeoffs.

**Location**: `decepticon/llm/models.py`

### Fallback Chain Rationale

Primary failure triggers fallback because:
- Rate limits (Anthropic 429)
- Model unavailability (provider outage)
- Context length exceeded (Haiku 200K → Gemini 2M)

**Non-obvious**: Fallback is per-agent-role, not global. Recon uses Gemini fallback, Soundwave doesn't.

**Location**: `decepticon/llm/factory.py:104-115`

## Knowledge Graph Documentation

### Deterministic IDs Design

SHA1-based node IDs enable:
- Idempotent ingestion (same scan twice = same nodes)
- Distributed ingestion (multiple agents, no ID collision)
- Efficient lookups (hash-based, not sequential scan)

**Non-obvious**: This is a graph database best practice, not Decepticon-specific.

**Location**: `decepticon/tools/research/graph.py`

### Why Neo4j Not SQLite

Graph database chosen because:
- Attack chains are graphs (lateral movement, privilege escalation paths)
- Cypher queries for path finding (shortest path to domain admin)
- Relationship-first data model (IP → Port → Service → Vulnerability)

**SQL limitations**: Recursive CTEs are verbose, no native graph algorithms.

**Location**: `docs/knowledge-graph.md`

## Testing Documentation

### Why Two Test Commands

```bash
make test        # Docker (full integration, mirrors CI)
make test-local  # Local (fast iteration, requires uv sync --dev)
```

**Rationale**:
- `make test` = pre-commit verification (catches Docker-specific issues)
- `make test-local` = TDD workflow (faster feedback loop)

**Location**: `Makefile:153-157`

### Pytest Async Mode

```toml
asyncio_mode = "auto"
```

**Why auto**: LangGraph agents are async, tests must match. Manual mode requires `@pytest.mark.asyncio` on every test.

**Location**: `pyproject.toml:89`

## Build System Documentation

### Smoke Test Purpose

`make smoke` replicates OSS user experience:
1. Clean state (down + volumes)
2. Build from local code (not GHCR pull)
3. Start with `--no-build --wait` (OSS launcher flow)
4. Health checks (KG + Neo4j + Web)

**Why**: Catch issues that only appear in OSS deployment (missing env vars, wrong defaults).

**Location**: `Makefile:106-126`

### Quality Gate Components

```bash
make quality = lint + test-local + cli build + web lint + web build
```

**Why this combination**: Catches issues across all deployment surfaces (Python backend, Node CLI, Next.js web).

**Location**: `Makefile:174`

## Environment Variables Documentation

### Nested Delimiter Rationale

```bash
DECEPTICON_DOCKER__POLL_INTERVAL=0.25
```

**Why double underscore**: Pydantic convention for nested config. Single underscore would conflict with field names containing underscores.

**Location**: `decepticon/core/config.py:77`

### Config Override Pattern

```python
class DecepticonConfig(BaseSettings):
    model_config = {"env_prefix": "DECEPTICON_", "env_nested_delimiter": "__"}
```

**Non-obvious**: This enables runtime tuning without code changes (critical for Docker deployments).

**Location**: `decepticon/core/config.py:64-83`