# Getting Started

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) and Docker Compose v2
- An API key for at least one LLM provider:
  - **Direct API**: Anthropic, OpenAI, Google, or MiniMax
  - **OpenRouter**: Single API key for 200+ models ([openrouter.ai](https://openrouter.ai))
  - **OAuth**: Claude Code or Codex subscription

That's it. Everything else runs inside containers.

---

## Install

```bash
curl -fsSL https://decepticon.red/install | bash
```

This installs the `decepticon` CLI to your system.

---

## Configure

```bash
decepticon onboard
```

The interactive setup wizard guides you through:

1. **Authentication** — API key or OAuth (Claude Code, Codex)
2. **Provider Strategy** — Choose how to access LLM models:
   - **Direct API** — Separate keys for Anthropic, OpenAI, Google, etc.
   - **OpenRouter** — Single API key for 200+ models (recommended for simplicity)
   - **Hybrid** — Direct Anthropic + OpenRouter for others (recommended for production)
   - **OAuth** — Claude Code subscription (no API cost)
3. **API Keys** — Enter keys based on your provider strategy:
   - Direct API: Provider-specific keys (Anthropic, OpenAI, Google, MiniMax)
   - OpenRouter: Single `OPENROUTER_API_KEY` from [openrouter.ai](https://openrouter.ai)
   - Hybrid: `ANTHROPIC_API_KEY` + `OPENROUTER_API_KEY`
   - OAuth: Managed by launcher
4. **Model Profile** — `eco` (balanced), `max` (performance), or `test` (development)
5. **LangSmith** — Optional tracing for LLM observability

Configuration is saved to `~/.decepticon/.env`. Run `decepticon onboard --reset` to reconfigure.

### OpenRouter Setup (Recommended)

For simplified credential management and cost savings:

1. **Get an OpenRouter API key** at [openrouter.ai](https://openrouter.ai)
2. **Run onboarding**:
   ```bash
   decepticon onboard
   ```
3. **Select provider strategy**:
   - Choose **OpenRouter** for single-key simplicity
   - Choose **Hybrid** for best performance + cost balance
4. **Enter your OpenRouter key** when prompted

See the [OpenRouter Guide](openrouter-guide.md) for detailed setup instructions, cost optimization strategies, and troubleshooting.

---

## Launch

**Terminal CLI** (default):
```bash
decepticon
```

Starts all services (LiteLLM, LangGraph, Neo4j, sandbox) and opens the interactive terminal UI.

**Web Dashboard** (browser):

The web dashboard starts as part of the default stack — it's reachable at `http://localhost:3000` once `decepticon` (or `make dev` for contributors) is running.

---

## Try the Demo

The demo runs a complete autonomous kill chain against a local Metasploitable 2 target — no setup needed beyond your API key.

```bash
decepticon demo
```

**What happens:**
1. Metasploitable 2 is launched as a target VM
2. A pre-built engagement (RoE + OPPLAN) is loaded
3. The agent executes autonomously:
   - Port scan and service enumeration
   - vsftpd 2.3.4 backdoor exploitation
   - Sliver C2 implant deployment
   - Credential harvesting via C2 session
   - Internal network reconnaissance

The demo is read-only — it doesn't modify anything on your host.

---

## First Real Engagement

1. Launch Decepticon (`decepticon`) and open <http://localhost:3000>
2. The **Soundwave** agent interviews you to define the engagement:
   - Target scope (IP range, URL, Git repo, file upload, or local path)
   - Threat actor profile
   - Rules of Engagement (authorized scope, timing, exclusions)
3. Soundwave generates: **RoE → ConOps → Deconfliction Plan → OPPLAN**
4. You review and approve the OPPLAN
5. The autonomous loop begins

> **Important**: Only run Decepticon against systems you own or have explicit written authorization to test. See the disclaimer in the main README.

---

## Stopping Services

```bash
decepticon stop     # Stop all services, keep data
make clean          # Stop + remove all volumes (resets everything)
```

---

## Check Service Status

```bash
decepticon status        # Show running services
decepticon logs          # Follow LangGraph logs (default)
decepticon logs litellm  # Follow a specific service's logs
decepticon kg-health     # Diagnose the Neo4j knowledge graph
```

---

## Next Steps

| Topic | Doc |
|-------|-----|
| All CLI commands and keyboard shortcuts | [CLI Reference](cli-reference.md) |
| All `make` targets | [Makefile Reference](makefile-reference.md) |
| Agent roles and middleware | [Agents](agents.md) |
| Model profiles and fallback chain | [Models](models.md) |
| OpenRouter setup and cost optimization | [OpenRouter Guide](openrouter-guide.md) |
| Engagement workflow (RoE → Execution) | [Engagement Workflow](engagement-workflow.md) |
| Web dashboard features | [Web Dashboard](web-dashboard.md) |
| Contributing to Decepticon | [Contributing](contributing.md) |
