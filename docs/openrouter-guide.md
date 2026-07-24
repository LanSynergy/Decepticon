# OpenRouter Integration Guide

Complete guide to using OpenRouter with Decepticon for cost-effective, flexible LLM access in red team operations.

---

## Table of Contents

- [Overview](#overview)
- [Quick Start](#quick-start)
- [Provider Strategies](#provider-strategies)
- [Model Selection](#model-selection)
- [Cost Optimization](#cost-optimization)
- [Advanced Configuration](#advanced-configuration)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

## Overview

[OpenRouter](https://openrouter.ai) is a unified LLM gateway that provides access to 200+ models from 20+ providers through a single API key. For red team operations, this offers:

### Key Benefits

**Operational Simplicity**
- Single API key replaces multiple provider credentials
- Reduced credential management overhead
- Simplified multi-operator deployments
- Smaller attack surface (fewer secrets to protect)

**Cost Efficiency**
- ~10% cheaper than direct API access for proprietary models
- Access to high-quality open-source models (Llama, Mistral) at fraction of cost
- Pay-per-use with no minimum commitments
- Transparent pricing across all models

**Flexibility**
- 200+ models available instantly
- Easy experimentation without new API keys
- Switch models without code changes
- Access to specialized models (coding, reasoning, multilingual)

**Resilience**
- Automatic failover across providers
- Multiple model options for each tier
- Reduced dependency on single provider
- Better uptime through diversity

### When to Use OpenRouter

**Ideal for:**
- Budget-conscious engagements
- Multi-model experimentation
- Access to open-source models (Llama, Mistral)
- Simplified credential management
- Development and testing

**Consider direct API when:**
- Maximum rate limits needed (Anthropic direct has higher limits)
- Lowest latency critical (direct API slightly faster)
- Provider-specific features required (e.g., Claude Code OAuth)

---

## Quick Start

### 1. Get an OpenRouter API Key

1. Visit [openrouter.ai](https://openrouter.ai)
2. Sign up or log in
3. Navigate to **Keys** section
4. Create a new API key
5. Add credits to your account (minimum $5 recommended)

### 2. Configure Decepticon

Add your OpenRouter key to `.env`:

```bash
# Edit configuration
decepticon config

# Add OpenRouter key
OPENROUTER_API_KEY=sk-or-v1-...

# Choose provider strategy
DECEPTICON_MODEL_PROVIDER=openrouter  # or hybrid
```

### 3. Verify Setup

```bash
# Start Decepticon
decepticon up

# Test with a simple command
decepticon chat "Test OpenRouter integration"

# Check logs for model routing
docker logs decepticon-litellm-1 | grep openrouter
```

You should see requests routing through OpenRouter models.

---

## Provider Strategies

Decepticon supports four provider strategies. Choose based on your priorities:

### Strategy Comparison

| Strategy | API Keys Required | Cost | Rate Limits | Complexity | Best For |
|----------|------------------|------|-------------|------------|----------|
| `api` | Multiple (Anthropic, OpenAI, Google) | Highest | Best | Medium | Maximum performance |
| `openrouter` | Single (OpenRouter) | Lower | Good | Lowest | Simplicity, cost savings |
| `hybrid` | Two (Anthropic + OpenRouter) | Balanced | Best | Medium | **Recommended** |
| `auth` | None (OAuth) | Free (Anthropic) | Limited | High | Claude Code subscribers |

### `api` — Direct Provider Access (Default)

**Configuration:**
```bash
DECEPTICON_MODEL_PROVIDER=api
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
```

**Routing:**
- All models use direct provider APIs
- No OpenRouter involvement
- Requires separate API key for each provider

**Pros:**
- Highest rate limits (especially Anthropic)
- Lowest latency (no proxy overhead)
- Direct provider support

**Cons:**
- Multiple API keys to manage
- Higher cost (no OpenRouter discount)
- More complex credential management

**Use when:**
- Maximum rate limits required
- Lowest latency critical
- Already have all provider API keys

### `openrouter` — Unified Gateway

**Configuration:**
```bash
DECEPTICON_MODEL_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-...
```

**Routing:**
- **All** models route through OpenRouter
- Single API key for everything
- Automatic model remapping:
  - `anthropic/claude-opus-4-6` → `openrouter/anthropic/claude-opus-4-6`
  - `openai/gpt-5.4` → `openrouter/openai/gpt-5.4`
  - `gemini/gemini-2.5-flash` → `openrouter/google/gemini-flash-1.5`

**Pros:**
- Simplest setup (one API key)
- ~10% cost savings on proprietary models
- Access to 200+ models instantly
- Unified billing and usage tracking

**Cons:**
- Lower rate limits than direct Anthropic API
- Slight latency overhead (~50-100ms)
- Dependent on OpenRouter uptime

**Use when:**
- Simplicity is priority
- Cost optimization important
- Experimenting with multiple models
- Development and testing

### `hybrid` — Best of Both Worlds (Recommended)

**Configuration:**
```bash
DECEPTICON_MODEL_PROVIDER=hybrid
ANTHROPIC_API_KEY=sk-ant-...
OPENROUTER_API_KEY=sk-or-v1-...
```

**Routing:**
- **Anthropic models** → Direct API (better rate limits)
- **All other models** → OpenRouter (cost savings)
- Fallbacks use opposite provider for resilience

**Example routing (eco profile):**
```
Recon agent:
  Primary: anthropic/claude-haiku-4-5 (direct API)
  Fallback: openrouter/google/gemini-flash-1.5 (OpenRouter)

Exploit agent:
  Primary: anthropic/claude-sonnet-4-6 (direct API)
  Fallback: openrouter/openai/gpt-4.1 (OpenRouter)
```

**Pros:**
- Best rate limits on Anthropic (direct API)
- Cost savings on non-Anthropic models
- Access to open-source models (Llama, Mistral)
- Provider diversity for resilience

**Cons:**
- Two API keys to manage
- Slightly more complex setup

**Use when:**
- Production engagements (recommended)
- Need Anthropic rate limits + cost optimization
- Want access to open-source models
- Balancing performance and cost

### `auth` — Claude Code OAuth

**Configuration:**
```bash
DECEPTICON_MODEL_PROVIDER=auth
# OAuth token managed by launcher
```

**Routing:**
- Anthropic models → OAuth subscription (no API cost)
- Non-Anthropic models → Direct API (requires keys)

**Pros:**
- Free Anthropic usage (if subscribed)
- No API key management for Anthropic

**Cons:**
- Requires Claude Code subscription
- Lower rate limits than API
- Complex OAuth flow

**Use when:**
- You have Claude Code subscription
- Want to minimize API costs
- Comfortable with OAuth complexity

---

## Model Selection

OpenRouter provides access to 200+ models. Decepticon's catalog includes 15+ carefully selected models across four tiers.

### Model Tiers

#### Strategic Tier
**Use for:** Complex reasoning, high-stakes operations, orchestration

| Model | Provider | Cost (Input/Output per 1M) | Context | Notes |
|-------|----------|---------------------------|---------|-------|
| `openrouter/anthropic/claude-opus-4-6` | Anthropic | $4.50 / $22.50 | 200K | Best reasoning |
| `openrouter/openai/gpt-5.4` | OpenAI | $4.50 / $22.50 | 128K | Strong alternative |
| `openrouter/meta-llama/llama-3.1-405b-instruct` | Meta | $2.70 / $2.70 | 128K | Open-source, 40% cheaper |

**Recommendation:** Use Opus for orchestration, Llama 405B for cost-sensitive strategic tasks.

#### Precision Tier
**Use for:** Exploitation, source code analysis, precise tool calling

| Model | Provider | Cost (Input/Output per 1M) | Context | Notes |
|-------|----------|---------------------------|---------|-------|
| `openrouter/anthropic/claude-sonnet-4-6` | Anthropic | $2.70 / $13.50 | 200K | Best tool calling |
| `openrouter/openai/gpt-4.1` | OpenAI | $2.25 / $11.25 | 128K | Strong reasoning |
| `openrouter/mistralai/mistral-large` | Mistral | $2.70 / $8.10 | 128K | European option |

**Recommendation:** Sonnet for exploitation, Mistral Large for cost-conscious precision work.

#### Tactical Tier
**Use for:** Reconnaissance, high-volume operations, tool-heavy tasks

| Model | Provider | Cost (Input/Output per 1M) | Context | Notes |
|-------|----------|---------------------------|---------|-------|
| `openrouter/anthropic/claude-haiku-4-5` | Anthropic | $0.90 / $4.50 | 200K | Fast, reliable |
| `openrouter/google/gemini-flash-1.5` | Google | $0.075 / $0.30 | 1M | Huge context, cheap |
| `openrouter/meta-llama/llama-3.1-70b-instruct` | Meta | $0.59 / $0.79 | 128K | Best value |

**Recommendation:** Llama 70B for most tactical work (85% cheaper than Haiku, comparable quality).

#### Budget Tier
**Use for:** Development, testing, low-stakes operations

| Model | Provider | Cost (Input/Output per 1M) | Context | Notes |
|-------|----------|---------------------------|---------|-------|
| `openrouter/meta-llama/llama-3.1-8b-instruct` | Meta | $0.06 / $0.06 | 128K | Extremely cheap |
| `openrouter/mistralai/mixtral-8x7b-instruct` | Mistral | $0.24 / $0.24 | 32K | Good quality/cost |

**Recommendation:** Llama 8B for development, Mixtral for testing that needs better quality.

### Model Selection Criteria

**Choose Anthropic (Opus/Sonnet/Haiku) when:**
- Tool calling precision critical (exploitation, post-exploit)
- Long context needed (200K tokens)
- Proven reliability required
- Budget allows

**Choose OpenAI (GPT-5/GPT-4) when:**
- Anthropic unavailable (outage, rate limit)
- Specific GPT capabilities needed
- Fallback from Anthropic

**Choose Llama (405B/70B/8B) when:**
- Cost optimization priority
- Open-source preference
- Comparable quality acceptable
- High-volume operations

**Choose Mistral/Mixtral when:**
- European data residency required
- Cost-conscious precision work
- Alternative to Anthropic/OpenAI

**Choose Gemini Flash when:**
- Massive context needed (1M tokens)
- Extremely low cost required
- Tactical/reconnaissance work

---

## Cost Optimization

### Strategy 1: Use Hybrid Provider

**Setup:**
```bash
DECEPTICON_MODEL_PROVIDER=hybrid
ANTHROPIC_API_KEY=sk-ant-...
OPENROUTER_API_KEY=sk-or-v1-...
```

**Savings:**
- Keep Anthropic on direct API (better rate limits)
- Route OpenAI/Google through OpenRouter (~10% savings)
- Access to cheap open-source models

**Example engagement cost (1M input, 500K output):**
- Direct API: $3.69
- Hybrid: $3.34 (9% savings)
- Hybrid with Llama 70B fallback: $1.99 (46% savings)

### Strategy 2: Replace Tactical Tier with Llama 70B

**Custom profile:**
```python
# In decepticon/llm/models.py or via environment override
mapping = LLMModelMapping(
    recon=ModelAssignment(
        primary="openrouter/meta-llama/llama-3.1-70b-instruct",
        fallback="openrouter/google/gemini-flash-1.5",
    ),
    # ... other roles
)
```

**Savings:**
- Llama 70B: $0.59/$0.79 per 1M tokens
- vs Haiku: $1.00/$5.00 per 1M tokens
- **85% cost reduction** on tactical operations

**Quality trade-off:**
- Llama 70B comparable to Haiku for most tasks
- Slightly lower tool calling precision
- May need more iterations for complex reasoning

### Strategy 3: Use Budget Models for Development

**Setup:**
```bash
DECEPTICON_MODEL_PROFILE=test
DECEPTICON_MODEL_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-...
```

**Override Haiku with Llama 8B:**
```bash
# In .env
DECEPTICON_MODEL_OVERRIDE_ALL=openrouter/meta-llama/llama-3.1-8b-instruct
```

**Savings:**
- Llama 8B: $0.06/$0.06 per 1M tokens
- vs Haiku: $1.00/$5.00 per 1M tokens
- **98% cost reduction** for development

### Strategy 4: Monitor and Optimize

**Use catalog tools:**
```bash
# Compare models
decepticon catalog compare \
  openrouter/anthropic/claude-haiku-4-5 \
  openrouter/meta-llama/llama-3.1-70b-instruct

# Estimate engagement cost
decepticon catalog estimate \
  --model openrouter/meta-llama/llama-3.1-70b-instruct \
  --input-tokens 1000000 \
  --output-tokens 500000
```

**Track usage:**
- OpenRouter dashboard shows per-model costs
- LiteLLM proxy logs include token counts
- Export usage data for analysis

### Cost Comparison Table

Typical engagement (1M input tokens, 500K output tokens):

| Configuration | Primary Cost | Fallback Cost | Total | Savings |
|---------------|-------------|---------------|-------|---------|
| Direct API (eco) | Haiku: $3.50 | Gemini: $0.19 | **$3.69** | Baseline |
| OpenRouter (eco) | Haiku: $3.15 | Gemini: $0.19 | **$3.34** | 9% |
| Hybrid (eco) | Haiku: $3.50 | Gemini: $0.19 | **$3.69** | 0% |
| OpenRouter Llama 70B | Llama: $0.99 | Gemini: $0.19 | **$1.18** | 68% |
| OpenRouter Llama 8B | Llama: $0.09 | — | **$0.09** | 98% |

**Key insight:** Switching tactical tier (recon, scanner) to Llama 70B provides massive cost savings with minimal quality impact.

---

## Advanced Configuration

### Custom Model Assignments

Override specific agent roles:

```bash
# In .env
DECEPTICON_MODEL_OVERRIDE_RECON=openrouter/meta-llama/llama-3.1-70b-instruct
DECEPTICON_MODEL_OVERRIDE_SCANNER=openrouter/meta-llama/llama-3.1-8b-instruct
```

### LiteLLM Configuration

Add OpenRouter models to `config/litellm.yaml`:

```yaml
model_list:
  # Custom OpenRouter model
  - model_name: openrouter/custom-model
    litellm_params:
      model: openrouter/provider/model-name
      api_key: os.environ/OPENROUTER_API_KEY
      api_base: https://openrouter.ai/api/v1
```

### Rate Limiting

Configure per-model rate limits:

```yaml
# In config/litellm.yaml
router_settings:
  routing_strategy: least-busy
  num_retries: 3
  timeout: 120

  # Per-model limits
  model_group_alias:
    openrouter_tactical:
      - openrouter/meta-llama/llama-3.1-70b-instruct
      - openrouter/google/gemini-flash-1.5
    
  rpm_limit:
    openrouter_tactical: 100  # 100 requests per minute
```

### Fallback Chains

Configure multi-level fallbacks:

```python
# In decepticon/llm/models.py
recon=ModelAssignment(
    primary="anthropic/claude-haiku-4-5",
    fallback="openrouter/meta-llama/llama-3.1-70b-instruct",
    # Add tertiary fallback via middleware
)
```

### Cost Alerts

Monitor spending with OpenRouter webhooks:

```bash
# Set spending limit in OpenRouter dashboard
# Configure webhook for alerts
curl -X POST https://openrouter.ai/api/v1/webhooks \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -d '{
    "url": "https://your-webhook-endpoint.com/alerts",
    "events": ["credit.low", "credit.depleted"]
  }'
```

---

## Troubleshooting

### "Model not found" Error

**Symptom:**
```
Error: Model 'openrouter/provider/model-name' not found
```

**Causes:**
1. Model ID format incorrect
2. Model not available on OpenRouter
3. Model requires special access

**Solutions:**
```bash
# Verify model ID format
# Correct: openrouter/anthropic/claude-opus-4-6
# Wrong: openrouter/claude-opus-4-6

# Check OpenRouter docs for current models
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"

# Use catalog to list available models
decepticon catalog list --provider openrouter
```

### Rate Limiting

**Symptom:**
```
Error: Rate limit exceeded for model X
```

**Causes:**
1. OpenRouter per-model rate limits
2. Account tier limits
3. Burst traffic

**Solutions:**
```bash
# Check current limits in OpenRouter dashboard
# Upgrade account tier for higher limits

# Use hybrid strategy to keep Anthropic on direct API
DECEPTICON_MODEL_PROVIDER=hybrid

# Configure fallback to different model
# Edit decepticon/llm/models.py to add fallback
```

### High Latency

**Symptom:**
Requests taking >2 seconds

**Causes:**
1. OpenRouter proxy overhead
2. Model cold start
3. Network latency

**Solutions:**
```bash
# Use hybrid strategy for latency-sensitive operations
DECEPTICON_MODEL_PROVIDER=hybrid

# Keep strategic tier on direct API
# Only route tactical tier through OpenRouter

# Monitor latency
docker logs decepticon-litellm-1 | grep "response_time"
```

### Cost Overruns

**Symptom:**
Higher than expected OpenRouter charges

**Causes:**
1. Using expensive models unintentionally
2. High token usage
3. Fallback chains triggering

**Solutions:**
```bash
# Check OpenRouter dashboard for usage breakdown
# Identify high-cost models

# Use catalog to estimate costs before engagement
decepticon catalog estimate \
  --model openrouter/anthropic/claude-opus-4-6 \
  --input-tokens 1000000 \
  --output-tokens 500000

# Set spending limits in OpenRouter dashboard
# Configure cost alerts

# Switch to cheaper models for tactical tier
DECEPTICON_MODEL_OVERRIDE_RECON=openrouter/meta-llama/llama-3.1-70b-instruct
```

### Authentication Errors

**Symptom:**
```
Error: Invalid API key
```

**Causes:**
1. API key not set
2. API key expired
3. Insufficient credits

**Solutions:**
```bash
# Verify API key is set
echo $OPENROUTER_API_KEY

# Check key format (should start with sk-or-v1-)
# Regenerate key in OpenRouter dashboard if needed

# Add credits to account
# Minimum $5 recommended for testing
```

### Model Availability

**Symptom:**
Model works sometimes, fails other times

**Causes:**
1. Model temporarily unavailable
2. Provider outage
3. Model deprecated

**Solutions:**
```bash
# Check OpenRouter status page
# Configure robust fallback chain

# Use multiple models in same tier
recon=ModelAssignment(
    primary="openrouter/meta-llama/llama-3.1-70b-instruct",
    fallback="openrouter/google/gemini-flash-1.5",
)

# Monitor model availability
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  | jq '.data[] | select(.id | contains("llama"))'
```

---

## FAQ

### General Questions

**Q: Do I need OpenRouter for Decepticon?**
A: No. OpenRouter is optional. Decepticon works with direct API access (default). OpenRouter provides cost savings and simplified credential management.

**Q: Can I use both direct API and OpenRouter?**
A: Yes. Use `hybrid` provider strategy to keep Anthropic on direct API and route others through OpenRouter.

**Q: How much does OpenRouter cost?**
A: Pay-per-use, no subscription. Prices are ~10% cheaper than direct API for proprietary models. Open-source models (Llama, Mistral) are 70-90% cheaper.

**Q: Is OpenRouter secure for red team operations?**
A: OpenRouter is a proxy service. Your prompts pass through their infrastructure. For sensitive operations, consider:
- Using direct API for sensitive prompts
- Reviewing OpenRouter's privacy policy
- Using hybrid strategy (Anthropic direct, others via OpenRouter)

### Setup Questions

**Q: How do I get an OpenRouter API key?**
A: Visit [openrouter.ai](https://openrouter.ai), sign up, navigate to Keys section, create new key. Add minimum $5 credits to start.

**Q: Which provider strategy should I use?**
A: 
- **Production:** `hybrid` (best balance)
- **Development:** `openrouter` (simplest)
- **Maximum performance:** `api` (direct)
- **Cost optimization:** `openrouter` with Llama models

**Q: Can I switch strategies mid-engagement?**
A: Yes. Change `DECEPTICON_MODEL_PROVIDER` in `.env` and restart. Existing state preserved.

### Model Questions

**Q: Which models should I use?**
A:
- **Strategic:** Opus or Llama 405B
- **Precision:** Sonnet or Mistral Large
- **Tactical:** Llama 70B (best value)
- **Budget:** Llama 8B or Mixtral

**Q: How does Llama 70B compare to Claude Haiku?**
A: Comparable quality for most tasks, 85% cheaper. Slightly lower tool calling precision. Excellent for reconnaissance and high-volume operations.

**Q: Can I use models not in the catalog?**
A: Yes. Add to `config/litellm.yaml` or use `DECEPTICON_MODEL_OVERRIDE_*` environment variables.

### Cost Questions

**Q: How much can I save with OpenRouter?**
A:
- Proprietary models: ~10% savings
- Switching to Llama 70B: ~85% savings on tactical tier
- Switching to Llama 8B: ~98% savings for development

**Q: How do I track costs?**
A: OpenRouter dashboard shows per-model usage. LiteLLM proxy logs include token counts. Use `decepticon catalog estimate` for projections.

**Q: What's the cheapest viable configuration?**
A:
```bash
DECEPTICON_MODEL_PROFILE=test
DECEPTICON_MODEL_PROVIDER=openrouter
DECEPTICON_MODEL_OVERRIDE_ALL=openrouter/meta-llama/llama-3.1-8b-instruct
```
Llama 8B everywhere: $0.06/$0.06 per 1M tokens.

### Technical Questions

**Q: Does OpenRouter add latency?**
A: Yes, ~50-100ms proxy overhead. Use `hybrid` strategy to keep latency-sensitive operations on direct API.

**Q: What are OpenRouter's rate limits?**
A: Varies by model and account tier. Generally lower than direct API. Check OpenRouter dashboard for current limits.

**Q: Can I use OpenRouter with Claude Code OAuth?**
A: No. OAuth (`auth` provider) is for direct Anthropic API only. Use `hybrid` to combine OAuth Anthropic with OpenRouter for other models.

**Q: How do fallbacks work with OpenRouter?**
A: Same as direct API. `ModelFallbackMiddleware` retries with fallback model on primary failure. Fallbacks can be OpenRouter or direct API models.

### Troubleshooting Questions

**Q: "Model not found" error?**
A: Verify model ID format (`openrouter/provider/model-name`). Check OpenRouter docs for current availability. Some models require special access.

**Q: High costs unexpectedly?**
A: Check OpenRouter dashboard for usage breakdown. Verify you're using intended models. Consider switching tactical tier to Llama 70B.

**Q: Authentication failing?**
A: Verify `OPENROUTER_API_KEY` is set and starts with `sk-or-v1-`. Check account has sufficient credits. Regenerate key if needed.

**Q: Models unavailable intermittently?**
A: Check OpenRouter status page. Configure robust fallback chains. Some models have limited availability.

---

## Additional Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Model List](https://openrouter.ai/models)
- [OpenRouter Pricing](https://openrouter.ai/docs/pricing)
- [Decepticon Model Catalog](models.md)
- [LiteLLM Documentation](https://docs.litellm.ai)

---

**Need help?** Open an issue on GitHub or ask in the Decepticon community.

<!-- Made with Bob -->