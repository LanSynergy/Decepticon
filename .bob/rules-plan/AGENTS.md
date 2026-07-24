# Decepticon Plan Mode — Agent Context

**Non-obvious architectural constraints for planning changes.**

## Skills System Architecture

### Skill Loading Constraint

Skills MUST remain on host filesystem because:
1. **Version control** - Skills are code, must be in git
2. **Security boundary** - Agents cannot modify their own knowledge
3. **Hot reload** - Skill updates without container rebuild
4. **Multi-agent sharing** - All 16 agents access same skill library

**Implication**: Any skill system redesign must preserve host FS access.

**Location**: `decepticon/agents/recon.py:85-88` (CompositeBackend routing)

### Skill Frontmatter Parsing

`allowed-tools` as space-separated string is load-bearing:

```python
# Current: O(1) string split
tools = frontmatter["allowed-tools"].split()

# If changed to YAML list: O(n) parsing + validation
```

**Constraint**: Middleware parses frontmatter on every agent init. String split is intentionally fast.

**Location**: `decepticon/middleware/skills.py`

## Backend Architecture Constraints

### CompositeBackend Routing

Two-tier routing is architectural:

```
/skills/*  → FilesystemBackend (host, read-only)
default    → DockerSandbox (container, read-write)
```

**Why not unified**: Security isolation. Agents must not write to `/skills/`.

**Implication**: Any new backend must support route-based delegation.

**Location**: `deepagents.backends.CompositeBackend`

### DockerSandbox Isolation

Sandbox container has NO network access to host by default:

```yaml
# docker-compose.yml
sandbox:
  networks:
    - decepticon-net  # Internal only
```

**Constraint**: Agents cannot reach host services (localhost:8080). Use service names (neo4j:7687).

**Location**: `docker-compose.yml`

## OPPLAN Architecture

### Why Not Generic Task System

OPPLAN schema is domain-specific by design:

```python
class Objective:
    phase: ObjectivePhase          # Kill chain phase
    mitre_attack_ids: list[str]    # ATT&CK techniques
    opsec_level: OpsecLevel        # STEALTH/BALANCED/AGGRESSIVE
    c2_tier: C2Tier                # C2 infrastructure tier
    blocked_by: list[str]          # Dependency graph
```

**Constraint**: Generic task systems (Jira, Asana) lack red team semantics.

**Implication**: OPPLAN cannot be replaced with off-the-shelf task tracking.

**Location**: `decepticon/middleware/opplan.py`, `decepticon/core/schemas.py`

### Objective Hierarchy Limits

```python
MAX_DEPTH = 3  # Parent → Child → Grandchild
```

**Why**: Deeper hierarchies cause:
- Context explosion (entire tree in prompt)
- Circular dependency risk
- Agent confusion (too many levels)

**Constraint**: Objective expansion must enforce depth limit.

**Location**: `decepticon/middleware/opplan.py:809-952`

## Agent Creation Pattern

### Why create_agent() Not create_deep_agent()

`create_deep_agent()` provides:
- Generic middleware stack (wrong for specialized agents)
- TodoListMiddleware (conflicts with OPPLAN)
- SubAgentMiddleware (conflicts with Decepticon orchestrator)

**Architectural decision**: Each agent role needs precise middleware control.

**Implication**: New agents must use `create_agent()` with explicit middleware.

**Location**: All `decepticon/agents/*.py` files

### Middleware Stack Constraints

Middleware order is load-bearing:

```python
# CORRECT order (inside-out execution)
[Skills, Filesystem, Fallback, Summarization, Caching, Patch]

# WRONG - Caching before Skills breaks skill injection
[Caching, Skills, ...]
```

**Why**: Each middleware wraps the next. Order determines execution flow.

**Constraint**: New middleware must be inserted at correct position.

**Location**: `decepticon/agents/recon.py:91-102`

## Tmux Session Architecture

### Why Tmux Not Direct Exec

Direct `docker exec` is stateless:
- Each call = new shell process
- No session persistence
- No interactive input
- No background jobs

**Architectural choice**: Tmux provides persistent sessions.

**Implication**: Replacing tmux requires equivalent session management.

**Location**: `decepticon/backends/docker_sandbox.py:87-496`

### PS1 Marker Protocol

```bash
PS1="[DCPTN:$?:$PWD] "
```

**Protocol design**:
- Marker counting (not regex matching) for robustness
- Exit code + cwd in single marker (atomic state)
- Unique prefix (won't collide with tool output)

**Constraint**: Any PS1 change must preserve marker counting logic.

**Location**: `decepticon/backends/docker_sandbox.py:46`

## Output Management Architecture

### Three-Tier Threshold Design

```python
30K   → Truncate (context preservation)
60s   → Background (agent productivity)
5M    → Kill (resource protection)
```

**Design rationale**:
- 30K = LLM context budget (Haiku 200K tokens ≈ 800K chars, leave room for history)
- 60s = Human attention span (agents should multitask like humans)
- 5M = Docker memory limit (prevent OOM kills)

**Constraint**: Thresholds are empirically tuned. Changes require benchmarking.

**Location**: `decepticon/backends/docker_sandbox.py:51-56`

### Truncation Algorithm

Asymmetric 60/40 split is empirically optimized:

```python
head_chars = int(MAX_OUTPUT_CHARS * 0.6)  # Headers, structure
tail_chars = MAX_OUTPUT_CHARS - head_chars  # Results, findings
```

**Why**: Security tool output patterns (nmap, nuclei) have high-value head/tail.

**Constraint**: Symmetric 50/50 loses critical context.

**Location**: `decepticon/backends/docker_sandbox.py:553-573`

## Model Configuration Architecture

### Profile System Design

Three profiles for different engagement contexts:

```
eco  → Cost-optimized (production)
max  → Accuracy-first (high-value targets)
test → Deterministic (CI/CD)
```

**Architectural choice**: Profile-based, not per-agent config.

**Why**: Engagement-wide consistency. All agents use same profile.

**Implication**: Per-agent model override requires architecture change.

**Location**: `decepticon/llm/models.py`

### Fallback Chain Architecture

```python
primary → fallback → error
```

**Why not retry primary**: Different failure modes need different models:
- Rate limit → fallback (different provider)
- Context length → fallback (larger context window)
- Model unavailable → fallback (different provider)

**Constraint**: Fallback must be different provider (not just different model).

**Location**: `decepticon/llm/factory.py:104-115`

## Knowledge Graph Architecture

### Why Neo4j Not Relational

Graph database chosen for:
- Native graph algorithms (shortest path, centrality)
- Relationship-first data model (attack chains are graphs)
- Cypher query language (expressive path queries)

**SQL limitations**:
- Recursive CTEs are verbose
- No native graph algorithms
- Join-heavy queries for paths

**Constraint**: Replacing Neo4j requires equivalent graph capabilities.

**Location**: `docs/knowledge-graph.md`

### Deterministic ID Design

SHA1-based node IDs enable:
- Idempotent ingestion (same scan twice = same nodes)
- Distributed ingestion (multiple agents, no coordination)
- Efficient lookups (hash-based, O(1))

**Constraint**: Sequential IDs would require coordination (single writer).

**Location**: `decepticon/tools/research/graph.py`

## Testing Architecture

### Two-Tier Test Strategy

```bash
make test        # Docker (integration, mirrors CI)
make test-local  # Local (unit, fast iteration)
```

**Architectural choice**: Separate commands for different test contexts.

**Why**: Integration tests need Docker services (Neo4j, LiteLLM). Unit tests don't.

**Constraint**: New tests must choose appropriate tier.

**Location**: `Makefile:153-157`, `pyproject.toml:88-98`

### Pytest Async Mode

```toml
asyncio_mode = "auto"
```

**Why auto not strict**: LangGraph agents are async. Tests must match runtime.

**Constraint**: Sync tests would miss async bugs (race conditions, deadlocks).

**Location**: `pyproject.toml:89`

## Build System Architecture

### Smoke Test Design

`make smoke` replicates OSS user flow:

```bash
clean → build local → up --no-build --wait → health
```

**Why**: Catch issues that only appear in OSS deployment:
- Missing env vars (defaults wrong)
- Image build failures (Dockerfile issues)
- Service startup order (depends_on wrong)

**Constraint**: Smoke test must match OSS launcher exactly.

**Location**: `Makefile:106-126`

### Quality Gate Design

```bash
make quality = lint + test-local + cli + web
```

**Why this combination**: Catches issues across all surfaces:
- Python backend (lint + test-local)
- Node CLI (typecheck + build + test)
- Next.js web (lint + build)

**Constraint**: New components must add quality checks.

**Location**: `Makefile:174`

## Environment Configuration Architecture

### Nested Delimiter Design

```bash
DECEPTICON_DOCKER__POLL_INTERVAL=0.25
```

**Why double underscore**: Pydantic convention for nested config.

**Constraint**: Single underscore would conflict with field names (e.g., `max_output_chars`).

**Location**: `decepticon/core/config.py:77`

### Config Override Pattern

```python
class DecepticonConfig(BaseSettings):
    model_config = {"env_prefix": "DECEPTICON_", "env_nested_delimiter": "__"}
```

**Architectural choice**: Environment variables override code defaults.

**Why**: Docker deployments need runtime config without rebuilds.

**Constraint**: All config must support env var override.

**Location**: `decepticon/core/config.py:64-83`