# Decepticon Code Mode — Agent Context

**Non-obvious coding rules for the Decepticon project.**

## Skills System Implementation

### Skill Loading Pattern

Skills MUST be loaded before execution:

```python
# CORRECT: Load skill first
skill_content = read_file("/skills/recon/active-recon/SKILL.md")
# Parse and follow skill instructions
bash("nmap -sS target")

# WRONG: Direct execution without skill context
bash("nmap -sS target")  # Missing environment-specific guidance
```

### Skill Frontmatter Format

`allowed-tools` is a **space-separated string**, not a YAML list:

```yaml
---
name: active-recon
allowed-tools: Bash Read Write  # CORRECT
---

# WRONG - will fail parsing
allowed-tools:
  - Bash
  - Read
```

**Parser location**: `decepticon/middleware/skills.py`

## Backend Architecture

### CompositeBackend Routing

Two separate filesystems:

```python
# Host filesystem (read-only skills)
read_file("/skills/recon/active-recon/SKILL.md")  # ✓ Works

# Docker container filesystem
bash("cat /skills/...")  # ✗ FAILS - /skills/ not mounted
bash("cat /workspace/...")  # ✓ Works - /workspace/ is bind-mounted
```

**Implementation**: `decepticon/agents/recon.py:85-88`

```python
backend = CompositeBackend(
    default=sandbox,
    routes={"/skills/": FilesystemBackend(root_dir=_REPO_ROOT / "skills", virtual_mode=True)},
)
```

## Agent Creation

### Use create_agent() Directly

**Never use `create_deep_agent()`**. All 16 agents use `create_agent()`:

```python
from langchain.agents import create_agent

agent = create_agent(
    llm,
    system_prompt=system_prompt,
    tools=tools,
    middleware=middleware,
    name="recon",
)
```

**Why**: Precise middleware control per agent role.

**Pattern location**: All `decepticon/agents/*.py` files

### Middleware Stack Order

Order is critical (inside-out execution):

```python
middleware = [
    DecepticonSkillsMiddleware(backend=backend, sources=["/skills/recon/"]),
    FilesystemMiddleware(backend=backend),
    ModelFallbackMiddleware(*fallback_models),
    create_summarization_middleware(llm, backend),
    AnthropicPromptCachingMiddleware(unsupported_model_behavior="ignore"),
    PatchToolCallsMiddleware(),
]
```

## Tmux Session Management

### PS1 Marker Pattern

Command completion detected via PS1 marker counting:

```python
PS1_PATTERN = re.compile(r"\[DCPTN:(\d+):(.+?)\]")
# Polls until marker count increases
```

**Implementation**: `decepticon/backends/docker_sandbox.py:46`

### Session Lifecycle

```python
# Session cache is process-wide
TmuxSessionManager._initialized: set[str] = set()
TmuxSessionManager._init_lock: threading.RLock = threading.RLock()

# Auto-recovery on session death
try:
    baseline = self._capture()
except RuntimeError as e:
    if "no server running" in str(e):
        # Invalidate cache and retry once
        TmuxSessionManager._initialized.discard(self.session)
        self.initialize()
```

## Output Management

### Three-Tier Thresholds

```python
MAX_OUTPUT_CHARS = 30_000        # Truncate with head+tail
AUTO_BACKGROUND_SECONDS = 60.0   # Background long commands
SIZE_WATCHDOG_CHARS = 5_000_000  # Force-kill with SIGINT
```

### Truncation Algorithm

```python
def _truncate(text: str) -> str:
    if len(text) <= MAX_OUTPUT_CHARS:
        return text
    head_chars = int(MAX_OUTPUT_CHARS * 0.6)  # 60% head
    tail_chars = MAX_OUTPUT_CHARS - head_chars  # 40% tail
    # Middle summarized with line/char counts
```

**Location**: `decepticon/backends/docker_sandbox.py:553-573`

## OPPLAN System

### Use OPPLANMiddleware, Not TodoList

```python
# CORRECT
from decepticon.middleware.opplan import OPPLANMiddleware

middleware.append(OPPLANMiddleware())

# WRONG - generic todos inappropriate for red team ops
from deepagents.middleware.todolist import TodoListMiddleware
```

### Objective Schema

```python
class Objective:
    id: str
    title: str
    phase: ObjectivePhase  # RECON, INITIAL_ACCESS, etc.
    status: ObjectiveStatus  # PENDING, IN_PROGRESS, COMPLETED
    parent_id: str | None  # Hierarchical tree
    mitre_attack_ids: list[str]
    opsec_level: OpsecLevel
    c2_tier: C2Tier
    blocked_by: list[str]  # Dependency tracking
```

**Location**: `decepticon/middleware/opplan.py`

## Model Configuration

### LLM Factory Pattern

```python
factory = LLMFactory()
llm = factory.get_model("recon")  # Primary model
fallback_models = factory.get_fallback_models("recon")  # Fallback chain

# Profiles (env: DECEPTICON_MODEL_PROFILE)
# eco  - Haiku primary, Gemini fallback
# max  - Opus everywhere
# test - Haiku only, no fallback
```

**Location**: `decepticon/llm/factory.py`

## Environment Configuration

### Nested Config Pattern

```bash
# Pydantic env_nested_delimiter="__"
DECEPTICON_DOCKER__POLL_INTERVAL=0.25
DECEPTICON_DOCKER__MAX_OUTPUT_CHARS=50000
DECEPTICON_LLM__TIMEOUT=180
```

**Config class**: `decepticon/core/config.py:77`

```python
class DecepticonConfig(BaseSettings):
    model_config = {"env_prefix": "DECEPTICON_", "env_nested_delimiter": "__"}
```

## Knowledge Graph

### Deterministic Node IDs

```python
import hashlib

def _node_id(node_type: str, key: str) -> str:
    return hashlib.sha1(f"{node_type}:{key}".encode()).hexdigest()

# Examples
ip_id = _node_id("ip", "192.168.1.1")
domain_id = _node_id("domain", "example.com")
port_id = _node_id("port", f"{ip}:{port}:{protocol}")
```

**Why**: Idempotent ingestion - same scan ingested twice creates nodes once.

**Location**: `decepticon/tools/research/graph.py`

## Testing

### Test Execution

```bash
# In Docker (full integration)
make test

# Locally (requires uv sync --dev)
make test-local

# Parallel
uv run pytest -n auto
```

### Pytest Config

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
markers = ["asyncio: mark test as async (pytest-asyncio)"]
```

**Location**: `pyproject.toml:88-98`

## Build System

### Make Targets

```bash
# Development
make dev          # Hot-reload (compose watch)
make cli          # Interactive CLI (forces rebuild)

# Pre-release verification
make smoke        # Clean → build → up → health (mirrors OSS)

# Quality gate
make quality      # lint + test-local + cli + web
```

**Smoke test**: Replicates OSS launcher flow with local images.

**Location**: `Makefile:1-239`

## Exit Code Semantics

Bash tool provides semantic hints:

```python
_EXIT_CODE_MESSAGES = {
    127: "command not found — tool may not be installed (try: apt-get install -y <pkg>)",
    137: "killed (SIGKILL) — likely OOM or size limit exceeded",
    139: "segmentation fault (SIGSEGV)",
}
```

**Location**: `decepticon/backends/docker_sandbox.py:59-82`