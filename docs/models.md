# Models

Decepticon routes LLM requests through a [LiteLLM](https://github.com/BerriAI/litellm) proxy, which supports Anthropic, OpenAI, and Google backends with automatic failover.

---

## Model Profiles

Three profiles control which models are assigned to which agent roles.

### `eco` — Production (default)

Balanced cost and performance. Recommended for most engagements.

| Role | Primary | Fallback |
|------|---------|---------|
| Orchestrator | `claude-opus-4-6` | `gpt-5.4` |
| Planner | `claude-opus-4-6` | `gpt-5.4` |
| Soundwave | `claude-haiku-4-5` | `gemini-2.5-flash` |
| Exploit | `claude-sonnet-4-6` | `gpt-4.1` |
| Recon | `claude-haiku-4-5` | `gemini-2.5-flash` |
| Post-Exploit | `claude-sonnet-4-6` | `gpt-4.1` |

### `max` — High-value targets

Opus or Sonnet everywhere. Use for complex engagements where accuracy matters more than cost.

| Role | Primary | Fallback |
|------|---------|---------|
| Orchestrator | `claude-opus-4-6` | `gpt-5.4` |
| Planner | `claude-opus-4-6` | `claude-sonnet-4-6` |
| Soundwave | `claude-sonnet-4-6` | `claude-haiku-4-5` |
| Exploit | `claude-opus-4-6` | `claude-sonnet-4-6` |
| Recon | `claude-sonnet-4-6` | `claude-opus-4-6` |
| Post-Exploit | `claude-opus-4-6` | `claude-sonnet-4-6` |

### `test` — Development / CI

Haiku everywhere. No fallback. Minimizes cost during development and automated testing.

| Role | Primary | Fallback |
|------|---------|---------|
| All roles | `claude-haiku-4-5` | — |

---

## Setting the Profile

In your `.env` file (edit with `decepticon config`):

```bash
DECEPTICON_MODEL_PROFILE=eco    # eco | max | test
```

The default is `eco` if not set.

---

## OpenRouter Integration

Decepticon supports [OpenRouter](https://openrouter.ai) as a unified gateway to 200+ LLM models through a single API key. This provides significant benefits for red team operations:

### Benefits

**Single API Key Management**
- One `OPENROUTER_API_KEY` replaces multiple provider keys
- Simplified credential management in multi-operator environments
- Reduced attack surface (fewer API keys to secure)

**Cost Savings**
- OpenRouter models are ~10% cheaper than direct API access
- Access to open-source models (Llama, Mistral, Mixtral) at fraction of proprietary cost
- Pay-per-use with no minimum commitments

**Model Diversity**
- 200+ models from 20+ providers
- Easy experimentation with new models without new API keys
- Access to specialized models (coding, reasoning, multilingual)

**Operational Flexibility**
- Switch models without code changes
- A/B test different models for specific agent roles
- Fallback to alternative providers during outages

### Setup

1. **Get an OpenRouter API key** at [openrouter.ai](https://openrouter.ai)

2. **Add to your `.env` file**:
   ```bash
   OPENROUTER_API_KEY=sk-or-v1-...
   ```

3. **Choose a provider strategy**:
   ```bash
   DECEPTICON_MODEL_PROVIDER=openrouter  # Route all models through OpenRouter
   # OR
   DECEPTICON_MODEL_PROVIDER=hybrid      # Direct Anthropic + OpenRouter for others
   ```

### Provider Strategies

Decepticon supports four provider strategies:

#### `api` (Default)
Direct API access to each provider. Requires separate API keys for Anthropic, OpenAI, Google, etc.

```bash
DECEPTICON_MODEL_PROVIDER=api
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
```

#### `openrouter`
Route **all** models through OpenRouter. Single API key, unified billing.

```bash
DECEPTICON_MODEL_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-...
```

**Model remapping**:
- `anthropic/claude-opus-4-6` → `openrouter/anthropic/claude-opus-4-6`
- `openai/gpt-5.4` → `openrouter/openai/gpt-5.4`
- `gemini/gemini-2.5-flash` → `openrouter/google/gemini-flash-1.5`

#### `hybrid` (Recommended)
Best of both worlds: direct Anthropic API for better rate limits, OpenRouter for everything else.

```bash
DECEPTICON_MODEL_PROVIDER=hybrid
ANTHROPIC_API_KEY=sk-ant-...
OPENROUTER_API_KEY=sk-or-v1-...
```

**Routing logic**:
- Anthropic models → Direct API (better rate limits)
- OpenAI, Google, Llama, Mistral → OpenRouter (cost savings)
- Fallbacks use opposite provider for resilience

#### `auth`
Claude Code OAuth subscription (no API cost for Anthropic models).

```bash
DECEPTICON_MODEL_PROVIDER=auth
# OAuth token managed by launcher
```

### Available OpenRouter Models

Decepticon's model catalog includes 15+ OpenRouter models across four tiers:

**Strategic Tier** (complex reasoning, high-stakes operations)
- `openrouter/anthropic/claude-opus-4-6` — $4.50/$22.50 per 1M tokens
- `openrouter/openai/gpt-5.4` — $4.50/$22.50 per 1M tokens
- `openrouter/meta-llama/llama-3.1-405b-instruct` — $2.70/$2.70 per 1M tokens

**Precision Tier** (balanced performance)
- `openrouter/anthropic/claude-sonnet-4-6` — $2.70/$13.50 per 1M tokens
- `openrouter/openai/gpt-4.1` — $2.25/$11.25 per 1M tokens
- `openrouter/mistralai/mistral-large` — $2.70/$8.10 per 1M tokens

**Tactical Tier** (high-volume, tool-heavy)
- `openrouter/anthropic/claude-haiku-4-5` — $0.90/$4.50 per 1M tokens
- `openrouter/google/gemini-flash-1.5` — $0.075/$0.30 per 1M tokens
- `openrouter/meta-llama/llama-3.1-70b-instruct` — $0.59/$0.79 per 1M tokens

**Budget Tier** (development, testing)
- `openrouter/meta-llama/llama-3.1-8b-instruct` — $0.06/$0.06 per 1M tokens
- `openrouter/mistralai/mixtral-8x7b-instruct` — $0.24/$0.24 per 1M tokens

See the [OpenRouter Guide](openrouter-guide.md) for complete model list and selection criteria.

### Configuration Examples

**Cost-optimized engagement** (hybrid strategy):
```bash
DECEPTICON_MODEL_PROFILE=eco
DECEPTICON_MODEL_PROVIDER=hybrid
ANTHROPIC_API_KEY=sk-ant-...
OPENROUTER_API_KEY=sk-or-v1-...
```

**Maximum performance** (direct API):
```bash
DECEPTICON_MODEL_PROFILE=max
DECEPTICON_MODEL_PROVIDER=api
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

**Single-key simplicity** (OpenRouter only):
```bash
DECEPTICON_MODEL_PROFILE=eco
DECEPTICON_MODEL_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-...
```

**Development/testing** (cheapest possible):
```bash
DECEPTICON_MODEL_PROFILE=test
DECEPTICON_MODEL_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-...
# Uses claude-haiku-4-5 via OpenRouter: $0.90/$4.50 per 1M tokens
```

### Cost Comparison

Example engagement (1M input tokens, 500K output tokens):

| Strategy | Primary Cost | Fallback Cost | Total |
|----------|-------------|---------------|-------|
| Direct API (eco) | Haiku: $1.00 + $2.50 = $3.50 | Gemini: $0.04 + $0.15 = $0.19 | **$3.69** |
| OpenRouter (eco) | Haiku: $0.90 + $2.25 = $3.15 | Gemini: $0.04 + $0.15 = $0.19 | **$3.34** (9% savings) |
| Hybrid (eco) | Haiku: $1.00 + $2.50 = $3.50 | Gemini: $0.04 + $0.15 = $0.19 | **$3.69** |
| OpenRouter Llama 70B | Llama: $0.59 + $0.40 = $0.99 | — | **$0.99** (73% savings) |

**Key insight**: OpenRouter enables access to high-quality open-source models (Llama 3.1 70B) at a fraction of proprietary model costs, while maintaining comparable performance for many red team tasks.

### Troubleshooting

**"Model not found" errors**
- Verify model ID format: `openrouter/provider/model-name`
- Check [OpenRouter docs](https://openrouter.ai/docs) for current model availability
- Some models require credits or special access

**Rate limiting**
- OpenRouter has per-model rate limits (varies by model)
- Use `hybrid` strategy to keep Anthropic on direct API (better limits)
- Consider upgrading OpenRouter plan for higher limits

**Cost tracking**
- OpenRouter dashboard shows per-model usage
- LiteLLM proxy logs include model routing decisions
- Use `decepticon catalog compare` to estimate costs before engagement

See the [OpenRouter Guide](openrouter-guide.md) for detailed troubleshooting and optimization strategies.

---

## Fallback Chain

`ModelFallbackMiddleware` handles failover transparently. When the primary model returns an error (provider outage, rate limit, context length exceeded), it automatically retries with the fallback model.

The switch is seamless — the agent continues with no interruption.

---

## Supported Models

Models are referenced using LiteLLM's `provider/model` format in `decepticon/llm/models.py`.

| Provider | Model ID | Notes |
|----------|----------|-------|
| Anthropic | `anthropic/claude-opus-4-6` | Most capable |
| Anthropic | `anthropic/claude-sonnet-4-6` | Balanced |
| Anthropic | `anthropic/claude-haiku-4-5` | Fast, low cost |
| OpenAI | `openai/gpt-5.4` | GPT fallback for Opus |
| OpenAI | `openai/gpt-4.1` | GPT fallback for Sonnet |
| Google | `gemini/gemini-2.5-flash` | Gemini fallback for Haiku |

Any model supported by LiteLLM can be added. Edit `config/litellm.yaml` to add new providers or routes.

---

## LiteLLM Proxy

All LLM traffic flows through the LiteLLM proxy container (`port 4000`). This provides:

- **Unified API** — agents use one endpoint regardless of backend
- **Usage tracking** — token consumption per model, per agent role
- **Rate limiting** — configurable per provider
- **Billing aggregation** — cost attribution across providers

Configuration: `config/litellm.yaml`

Authentication: set `LITELLM_MASTER_KEY` in your `.env` file.
