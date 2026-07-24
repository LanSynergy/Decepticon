# Decepticon Project — Agent Context

**Critical non-obvious patterns discovered from codebase analysis.**

## Skills System — SKILL-FIRST Rule

**CRITICAL**: Skills must be loaded via `read_file()` before use. The skill catalog in system prompts is NOT sufficient for execution.

```python
# CORRECT: Load skill before using technique
read_file("/skills/recon/active-recon/SKILL.md")
# Then execute based on skill content

# WRONG: Acting from memory when skill exists
bash("nmap -sS target")  # Missing skill context
```

**Why**: Skills contain environment-specific paths, container setup, OPSEC guidance, and current tool versions that differ from general LLM knowledge.

### Skill Frontmatter Gotcha

`allowed-tools` must be a **space-separated string**, NOT a YAML list:

```yaml
# CORRECT
allowed-tools: Bash Read Write

# WRONG (will fail parsing)
allowed-tools:
  - Bash
  - Read
  - Write
```

**Location**: `decepticon/middleware/skills.py` parses this as a string split.

## Backend Routing — CompositeBackend

Skills live on **host filesystem**, execution happens in **Docker container**:

```python
# Skills: host FS via FilesystemBackend (read-only)
read_file("/skills/recon/active-recon/SKILL.md")  # ✓ Works

# Execution: Docker sandbox via DockerSandbox
bash("cat /skills/...")  # ✗ FAILS — /skills/ not mounted in container
```

**Architecture**: `CompositeBackend` routes `/skills/*` → host FS, everything else → Docker.

**Location**: `decepticon/agents/recon.py:85-88`

## OPPLAN vs TodoList

**DO NOT use TodoListMiddleware**. Decepticon uses domain-specific OPPLAN tracking:

- `OPPLANMiddleware` provides objective management tools
- Objectives have phases, MITRE ATT&CK IDs, OPSEC notes, C2 tier
- Hierarchical tree structure (parent_id relationships)
- Status transitions validated (PENDING → IN_PROGRESS → COMPLETED)

**Location**: `decepticon/middleware/opplan.py`

Generic todos are inappropriate for red team operations that require:
- Kill chain phase tracking
- Acceptance criteria validation
- Blocked-by dependency chains
- OPSEC risk assessment per objective

## Agent Creation Pattern

**All agents use `create_agent()` directly**, NOT `create_deep_agent()`:

```python
# CORRECT pattern (all 16 agents)
from langchain.agents import create_agent

agent = create_agent(
    llm,
    system_prompt=system_prompt,
    tools=tools,
    middleware=middleware,
    name="recon",
)
```

**Why**: Precise middleware stack control. Each agent selects middleware based on role:
- Recon: Skills + Filesystem + ModelFallback + Summarization
- Decepticon orchestrator: OPPLAN + SubAgent + no Skills
- Soundwave planner: OPPLAN only, no execution tools

**Location**: All files in `decepticon/agents/*.py`

## Tmux Execution — PS1 Marker Pattern

Bash tool uses **tmux sessions** with custom PS1 marker for completion detection:

```bash
PS1="[DCPTN:$?:$PWD] "
# Regex: \[DCPTN:(\d+):(.+?)\]
```

**Polling logic**:
1. Send command to tmux session
2. Poll `tmux capture-pane` every 0.5s
3. Count PS1 markers — when count increases, command completed
4. Extract exit code and cwd from final marker

**Gotchas**:
- Commands that kill the shell (e.g., `pkill bash`) destroy the session
- Auto-recovery attempts once, then returns error
- Size watchdog kills commands producing >5M chars
- Auto-background after 60s for long-running commands

**Location**: `decepticon/backends/docker_sandbox.py:46-496`

## Output Management — Multi-Tier Thresholds

Three output size thresholds with different behaviors:

```python
MAX_OUTPUT_CHARS = 30_000        # Truncate (head + tail)
AUTO_BACKGROUND_SECONDS = 60.0   # Background long commands
SIZE_WATCHDOG_CHARS = 5_000_000  # Force-kill (SIGINT)
```

**Truncation preserves context**:
- 60% head (18K chars) — headers, structure
- 40% tail (12K chars) — final results
- Middle summarized: "... N lines / M chars truncated ..."

**Location**: `decepticon/backends/docker_sandbox.py:51-573`

## Model Fallback Chains

Each agent role has primary + fallback model assignment:

```python
# Recon agent example
factory = LLMFactory()
llm = factory.get_model("recon")              # claude-haiku-4-5
fallback_models = factory.get_fallback_models("recon")  # gemini-2.5-flash

middleware.append(ModelFallbackMiddleware(*fallback_models))
```

**Profiles** (env: `DECEPTICON_MODEL_PROFILE`):
- `eco` — Haiku primary, Gemini fallback (production)
- `max` — Opus everywhere (high-value targets)
- `test` — Haiku-only (CI, no fallback)

**Location**: `decepticon/llm/factory.py`, `decepticon/llm/models.py`

## Knowledge Graph — Deterministic Node IDs

Neo4j nodes use **SHA1-based deterministic IDs** to prevent duplicates:

```python
# IP node: sha1(f"ip:{ip_address}")
# Domain node: sha1(f"domain:{fqdn}")
# Port node: sha1(f"port:{ip}:{port}:{protocol}")
```

**Why**: Idempotent ingestion. Running `kg_ingest_nmap_xml()` twice on the same scan creates nodes once, updates properties.

**Location**: `decepticon/tools/research/graph.py`

## Testing — Pytest Configuration

```bash
# Run tests in Docker (mirrors CI)
make test

# Run tests locally (requires uv sync --dev)
make test-local

# Parallel execution
uv run pytest -n auto

# Specific markers
uv run pytest -m asyncio
```

**Gotcha**: Some tests require Docker services (Neo4j, LiteLLM proxy). Use `make test` for full integration tests.

**Location**: `pyproject.toml:88-98`, `Makefile:153-157`

## Build Commands — Local vs OSS Flow

```bash
# Development (hot-reload)
make dev              # compose watch

# Pre-release verification (mirrors OSS launcher)
make smoke            # clean → build local → up --no-build --wait → health

# Quality gate (before PR)
make quality          # lint + test-local + cli build + web lint + web build
```

**Smoke test replicates OSS user experience** but uses locally-built images instead of pulling from GHCR.

**Location**: `Makefile:1-239`

## Environment Variables — Nested Config

Docker config uses **double-underscore nesting**:

```bash
# Override tmux poll interval
DECEPTICON_DOCKER__POLL_INTERVAL=0.25

# Override LLM timeout
DECEPTICON_LLM__TIMEOUT=180
```

**Pattern**: `DECEPTICON_<section>__<field>=value`

**Location**: `decepticon/core/config.py:77` (Pydantic `env_nested_delimiter`)

## Middleware Stack Order

**Order matters**. Typical agent stack (inside-out):

1. `DecepticonSkillsMiddleware` — Inject skill catalog, handle `read_file()` for skills
2. `FilesystemMiddleware` — File operations (ls/read/write/edit/grep/glob)
3. `ModelFallbackMiddleware` — Retry with fallback model on primary failure
4. `SummarizationMiddleware` — Auto-compact when context budget exceeded
5. `AnthropicPromptCachingMiddleware` — Cache system prompt (Anthropic only)
6. `PatchToolCallsMiddleware` — Repair dangling tool calls

**Location**: `decepticon/agents/recon.py:91-102`

## Exit Code Interpretation

Bash tool provides **semantic exit code hints**:

```
127 — command not found — tool may not be installed (try: apt-get install -y <pkg>)
137 — killed (SIGKILL) — likely OOM or size limit exceeded
139 — segmentation fault (SIGSEGV)
```

**Why**: Helps agents diagnose failures without manual interpretation.

**Location**: `decepticon/backends/docker_sandbox.py:59-82`