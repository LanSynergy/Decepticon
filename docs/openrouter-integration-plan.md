 None


class TestModelMetadata:
    def test_model_has_required_fields(self):
        info = get_model_info("openrouter/anthropic/claude-opus-4-6")
        assert info.id is not None
        assert info.name is not None
        assert info.provider is not None
        assert info.tier is not None
        assert info.context_length > 0
        assert info.cost_input >= 0
        assert info.cost_output >= 0
```

#### 4.4.2 Integration Tests

**File:** `tests/integration/test_openrouter_e2e.py` (new file)

```python
"""End-to-end tests for OpenRouter integration."""

import os
import pytest

from decepticon.llm.factory import LLMFactory
from decepticon.llm.models import LLMModelMapping, ModelProvider, ProxyConfig


@pytest.mark.skipif(
    not os.getenv("OPENROUTER_API_KEY"),
    reason="OPENROUTER_API_KEY not set"
)
class TestOpenRouterE2E:
    """Integration tests requiring actual OpenRouter API key."""
    
    def test_openrouter_model_invocation(self):
        """Test that we can actually call an OpenRouter model."""
        mapping = LLMModelMapping().with_provider(ModelProvider.OPENROUTER)
        factory = LLMFactory(mapping=mapping)
        
        model = factory.get_model("recon")
        response = model.invoke("Say 'test successful' and nothing else.")
        
        assert response is not None
        assert "test successful" in response.content.lower()
    
    def test_openrouter_fallback_chain(self):
        """Test that fallback works when primary fails."""
        # This would require mocking a failure scenario
        pass
```

#### 4.4.3 Documentation Updates

**File:** `docs/models.md`

Add new section:

```markdown
## OpenRouter Integration

Decepticon supports OpenRouter as a unified gateway to 200+ models from multiple providers.

### Benefits

- **Single API Key:** Access all models with one `OPENROUTER_API_KEY`
- **Unified Billing:** One invoice across all providers
- **Cost Optimization:** Often 10-30% cheaper than direct APIs
- **Model Diversity:** Access to Llama, Mistral, Cohere, and more
- **Automatic Failover:** Built-in redundancy across providers

### Setup

1. Get an API key from [openrouter.ai/keys](https://openrouter.ai/keys)
2. Run `decepticon onboard --reset`
3. Choose "OpenRouter" as your provider strategy
4. Enter your OpenRouter API key

### Available Models

When using OpenRouter, you have access to:

**Anthropic:**
- Claude Opus 4.6
- Claude Sonnet 4.6
- Claude Haiku 4.5

**OpenAI:**
- GPT-5.4
- GPT-4.1

**Meta:**
- Llama 3.1 405B
- Llama 3.1 70B
- Llama 3.1 8B

**Mistral:**
- Mistral Large
- Mistral Medium
- Mixtral 8x7B

**Cohere:**
- Command R+
- Command R

**And 190+ more models...**

### Configuration

In your `.env` file:

```bash
DECEPTICON_MODEL_PROVIDER=openrouter
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

### Hybrid Mode

You can mix direct provider APIs with OpenRouter:

```bash
DECEPTICON_MODEL_PROVIDER=hybrid
ANTHROPIC_API_KEY=sk-ant-...     # Direct Anthropic for Claude
OPENROUTER_API_KEY=sk-or-v1-...  # OpenRouter for Llama, Mistral, etc.
```

This gives you:
- Better rate limits on Anthropic (direct API)
- Access to open-source models (via OpenRouter)
- Cost optimization (use cheaper models where appropriate)
```

---

## 5. Migration Strategy

### 5.1 Backward Compatibility

**Guarantee:** Existing configurations will continue working without changes.

**How:**
1. Default `DECEPTICON_MODEL_PROVIDER` remains `api`
2. Existing `.env` files without `OPENROUTER_API_KEY` work as before
3. Model name format unchanged for direct providers
4. LiteLLM proxy supports both direct and OpenRouter models simultaneously

### 5.2 Migration Paths

#### Path 1: Stay on Direct APIs (No Action Required)

Users who are happy with direct provider APIs don't need to change anything.

#### Path 2: Switch to OpenRouter

1. Get OpenRouter API key from [openrouter.ai/keys](https://openrouter.ai/keys)
2. Run `decepticon onboard --reset`
3. Choose "OpenRouter" strategy
4. Enter OpenRouter API key
5. Keep existing model profile (eco/max/test)

**Result:** All models now route through OpenRouter, single billing source.

#### Path 3: Hybrid Setup

1. Keep existing direct provider API keys
2. Add `OPENROUTER_API_KEY` to `.env`
3. Set `DECEPTICON_MODEL_PROVIDER=hybrid`
4. Optionally customize which models use which provider

**Result:** Mix of direct and OpenRouter routing for optimal cost/performance.

### 5.3 Rollout Plan

**Week 1-2:** Internal testing
- Deploy to development environment
- Test all three provider strategies
- Validate model routing
- Measure cost differences

**Week 3:** Beta release
- Announce in release notes
- Update documentation
- Provide migration guide
- Monitor for issues

**Week 4:** General availability
- Default remains `api` (no breaking changes)
- OpenRouter available as opt-in feature
- Collect user feedback
- Iterate on UX

---

## 6. Cost Analysis

### 6.1 Cost Comparison

**Scenario: 1M input tokens, 1M output tokens per month**

| Provider Strategy | Monthly Cost | Notes |
|------------------|--------------|-------|
| Direct APIs (eco profile) | $180 | Anthropic + OpenAI + Google |
| OpenRouter (eco profile) | $150 | ~17% savings via unified gateway |
| Hybrid (optimized) | $120 | Direct Anthropic + OpenRouter for others |

**Savings opportunities:**
- Use Llama 3.1 70B instead of GPT-4.1 for fallbacks: 80% cost reduction
- Use Mistral Large instead of Sonnet for precision tasks: 33% cost reduction
- Use Gemini Flash via OpenRouter: 50% cheaper than direct Google API

### 6.2 Cost Optimization Strategies

1. **Strategic tier:** Keep Opus/GPT-5 (quality critical)
2. **Precision tier:** Switch to Llama 3.1 70B or Mistral Large (70% savings)
3. **Tactical tier:** Use Gemini Flash or Llama 3.1 8B (90% savings)

**New "budget" profile suggestion:**

```python
# decepticon/llm/models.py
BUDGET_PROFILE = LLMModelMapping(
    decepticon=ModelAssignment(
        primary=OPENROUTER_OPUS,
        fallback=OPENROUTER_LLAMA_70B,  # $0.59 vs $3 for GPT-4
    ),
    recon=ModelAssignment(
        primary=OPENROUTER_GEMINI_FLASH,
        fallback=OPENROUTER_LLAMA_70B,
    ),
    exploit=ModelAssignment(
        primary=OPENROUTER_MISTRAL_LARGE,  # $2 vs $3 for Sonnet
        fallback=OPENROUTER_LLAMA_70B,
    ),
)
```

**Estimated savings:** 60% reduction vs eco profile

---

## 7. Potential Challenges & Solutions

### 7.1 Challenge: Model Availability

**Issue:** OpenRouter models may have different availability than direct APIs.

**Solution:**
- Keep fallback models on direct APIs (safety net)
- Monitor OpenRouter status page
- Implement retry logic with exponential backoff
- Alert on repeated OpenRouter failures

### 7.2 Challenge: Rate Limits

**Issue:** OpenRouter has different rate limits than direct provider APIs.

**Solution:**
- Document OpenRouter rate limits in setup guide
- Implement rate limit detection in middleware
- Auto-fallback to direct APIs when OpenRouter rate limited
- Consider hybrid mode for high-volume users

### 7.3 Challenge: Model Name Confusion

**Issue:** Users may be confused by `openrouter/anthropic/claude-opus` vs `anthropic/claude-opus`.

**Solution:**
- Clear documentation explaining the difference
- Onboarding wizard shows which strategy is active
- CLI command to show current model routing: `decepticon models list`
- Error messages include provider strategy context

### 7.4 Challenge: API Key Management

**Issue:** Users may have both direct and OpenRouter keys, causing confusion.

**Solution:**
- Onboarding wizard validates keys before saving
- Health check endpoint tests all configured providers
- CLI command to test connectivity: `decepticon models test`
- Clear error messages when keys are missing/invalid

### 7.5 Challenge: Cost Tracking

**Issue:** Users need to track costs across multiple providers.

**Solution:**
- LiteLLM proxy already tracks usage per model
- Add cost dashboard to web UI showing breakdown by provider
- Export usage reports: `decepticon usage export --month 2026-04`
- Integration with LangSmith for detailed cost analytics

### 7.6 Challenge: Model Deprecation

**Issue:** OpenRouter may deprecate models or change pricing.

**Solution:**
- Subscribe to OpenRouter changelog
- Automated tests detect model availability changes
- Version pin model IDs in configuration
- Migration guide when models change

---

## 8. Testing Strategy

### 8.1 Unit Tests

**Coverage:**
- ✅ ModelProvider enum includes OPENROUTER and HYBRID
- ✅ `with_provider()` correctly remaps model names
- ✅ OpenRouter model constants are defined
- ✅ Model catalog returns correct metadata
- ✅ Fallback chains preserve safety net

**Files:**
- `tests/unit/llm/test_openrouter.py`
- `tests/unit/llm/test_catalog.py`
- `tests/unit/llm/test_models.py` (extended)

### 8.2 Integration Tests

**Coverage:**
- ✅ LiteLLM proxy routes OpenRouter models correctly
- ✅ API key authentication works
- ✅ Model invocation returns valid responses
- ✅ Fallback chain activates on primary failure
- ✅ Hybrid mode routes correctly

**Files:**
- `tests/integration/test_openrouter_e2e.py`
- `tests/integration/test_litellm_proxy.py` (extended)

**Requirements:**
- Valid `OPENROUTER_API_KEY` in test environment
- LiteLLM proxy running
- Network access to OpenRouter API

### 8.3 Smoke Tests

**Pre-release checklist:**

```bash
# 1. Clean install
make clean
make build

# 2. Onboarding flow
decepticon onboard --reset
# Choose OpenRouter strategy
# Enter test API key

# 3. Health check
decepticon health

# 4. Model test
decepticon models test

# 5. Simple engagement
decepticon run --task "List files in current directory"

# 6. Verify model routing
docker logs decepticon-litellm | grep openrouter

# 7. Cost tracking
decepticon usage show
```

### 8.4 Performance Tests

**Benchmarks:**
- Latency: OpenRouter vs direct APIs
- Throughput: Requests per minute
- Failover time: Primary → fallback switch
- Cost per 1M tokens: All provider strategies

**Tools:**
- `benchmark/harness.py` (existing)
- Custom OpenRouter benchmark script

---

## 9. Documentation Checklist

### 9.1 User-Facing Documentation

- [ ] Update [`docs/models.md`](docs/models.md) with OpenRouter section
- [ ] Update [`docs/getting-started.md`](docs/getting-started.md) with OpenRouter setup
- [ ] Create `docs/openrouter-guide.md` with detailed guide
- [ ] Update [`.env.example`](.env.example) with OpenRouter variables
- [ ] Add OpenRouter to FAQ section
- [ ] Update CLI help text: `decepticon onboard --help`

### 9.2 Developer Documentation

- [ ] Update [`docs/architecture.md`](docs/architecture.md) with provider strategy
- [ ] Document model catalog API in [`docs/models.md`](docs/models.md)
- [ ] Add OpenRouter to [`docs/contributing.md`](docs/contributing.md)
- [ ] Update API reference with new enums/methods
- [ ] Add architecture diagrams showing routing flow

### 9.3 Release Notes

```markdown
## v2.1.0 - OpenRouter Integration

### New Features

**OpenRouter Support**
- Access 200+ models through unified OpenRouter gateway
- Single API key for all providers (Anthropic, OpenAI, Google, Meta, Mistral, Cohere, etc.)
- Hybrid mode: Mix direct APIs with OpenRouter for optimal cost/performance
- Custom model selection: Choose specific models for each agent role

**Cost Optimization**
- 10-30% cost savings via OpenRouter unified billing
- Access to open-source models (Llama, Mistral) at fraction of proprietary cost
- New "budget" profile using cost-optimized model mix

### Migration Guide

Existing configurations continue working without changes. To enable OpenRouter:

1. Get API key: https://openrouter.ai/keys
2. Run: `decepticon onboard --reset`
3. Choose "OpenRouter" strategy
4. Enter your API key

See docs/openrouter-guide.md for details.

### Breaking Changes

None. This is a backward-compatible feature addition.
```

---

## 10. Implementation Timeline

### Week 1: Core Infrastructure
- **Days 1-2:** Extend ModelProvider enum, add OpenRouter constants
- **Days 3-4:** Enhance `with_provider()` method, add remapping logic
- **Day 5:** Update LiteLLM configuration, add OpenRouter models

### Week 2: Go CLI Onboarding
- **Days 1-2:** Update onboarding wizard with provider strategy selection
- **Days 3-4:** Add OpenRouter API key input and validation
- **Day 5:** Update .env generation logic, test end-to-end flow

### Week 3: Advanced Features
- **Days 1-2:** Implement custom model selection UI
- **Days 3-4:** Create model catalog module
- **Day 5:** Add hybrid mode configuration

### Week 4: Testing & Documentation
- **Days 1-2:** Write unit tests, integration tests
- **Days 3-4:** Update all documentation
- **Day 5:** Smoke testing, performance benchmarks

### Week 5: Beta Release
- **Days 1-2:** Deploy to staging, internal testing
- **Days 3-4:** Beta user testing, collect feedback
- **Day 5:** Bug fixes, UX improvements

### Week 6: General Availability
- **Day 1:** Final testing, release preparation
- **Day 2:** Release v2.1.0 with OpenRouter support
- **Days 3-5:** Monitor adoption, provide user support

---

## 11. Success Metrics

### 11.1 Adoption Metrics

- **Target:** 30% of users try OpenRouter within 3 months
- **Measure:** Track `DECEPTICON_MODEL_PROVIDER` values in telemetry
- **Goal:** 50% cost reduction for users who switch

### 11.2 Technical Metrics

- **Latency:** OpenRouter response time ≤ 1.2x direct API
- **Availability:** 99.5% uptime for OpenRouter routing
- **Fallback rate:** <5% of requests require fallback
- **Error rate:** <1% of OpenRouter requests fail

### 11.3 User Satisfaction

- **Setup time:** <5 minutes to switch to OpenRouter
- **Documentation clarity:** >90% users understand provider strategies
- **Support tickets:** <10 OpenRouter-related issues per month

---

## 12. Future Enhancements

### 12.1 Dynamic Model Selection

**Concept:** Automatically choose the best model for each task based on:
- Task complexity (simple → Haiku, complex → Opus)
- Cost budget (stay within monthly limit)
- Performance requirements (latency vs quality)

**Implementation:**
- Add `ModelSelector` class with heuristics
- Integrate with OPPLAN middleware (task metadata)
- A/B test different selection strategies

### 12.2 Model Performance Tracking

**Concept:** Track which models perform best for each agent role.

**Metrics:**
- Success rate (task completion)
- Cost per successful task
- Average latency
- User satisfaction ratings

**Use case:** Automatically recommend optimal models based on historical data.

### 12.3 Multi-Provider Fallback Chains

**Concept:** Extend fallback beyond 2 models.

**Example:**
```python
ModelAssignment(
    primary=OPENROUTER_OPUS,
    fallbacks=[
        OPENROUTER_SONNET,
        OPENROUTER_LLAMA_70B,
        ANTHROPIC_HAIKU,  # Last resort: direct API
    ]
)
```

### 12.4 Cost Alerts

**Concept:** Alert users when approaching budget limits.

**Features:**
- Daily/weekly cost summaries
- Budget thresholds with notifications
- Model recommendation when over budget
- Integration with Slack/email

---

## 13. Conclusion

This implementation plan provides a comprehensive roadmap for integrating OpenRouter into Decepticon's model selection architecture. The design maintains backward compatibility while offering significant benefits:

**Key Advantages:**
- ✅ Access to 200+ models from single API key
- ✅ 10-30% cost savings via unified billing
- ✅ Maintains existing per-agent-role selection pattern
- ✅ Backward compatible (no breaking changes)
- ✅ Flexible (direct, OpenRouter, or hybrid strategies)

**Implementation Effort:**
- 6 weeks total (4 weeks development, 2 weeks testing/release)
- ~15 files modified
- ~2000 lines of code added
- Comprehensive test coverage

**Risk Level:** Low
- Existing functionality unchanged
- Opt-in feature (users choose when to adopt)
- Fallback mechanisms preserve reliability
- Extensive testing before release

**Next Steps:**
1. Review and approve this plan
2. Create GitHub issues for each phase
3. Assign development resources
4. Begin Week 1 implementation

---

## Appendix A: File Modification Summary

### Python Backend

| File | Changes | Lines |
|------|---------|-------|
| `decepticon/llm/models.py` | Add OPENROUTER provider, constants, enhance with_provider() | +150 |
| `decepticon/llm/catalog.py` | New file: model catalog management | +200 |
| `decepticon/core/config.py` | No changes (enum auto-picked up) | 0 |
| `config/litellm.yaml` | Add OpenRouter model definitions | +80 |
| `.env.example` | Add OPENROUTER_API_KEY, update comments | +10 |

### Go CLI

| File | Changes | Lines |
|------|---------|-------|
| `clients/launcher/cmd/onboard.go` | Add provider strategy selection, OpenRouter key input | +200 |

### Tests

| File | Changes | Lines |
|------|---------|-------|
| `tests/unit/llm/test_openrouter.py` | New file: OpenRouter unit tests | +100 |
| `tests/unit/llm/test_catalog.py` | New file: catalog unit tests | +80 |
| `tests/integration/test_openrouter_e2e.py` | New file: E2E tests | +50 |

### Documentation

| File | Changes | Lines |
|------|---------|-------|
| `docs/models.md` | Add OpenRouter section | +100 |
| `docs/openrouter-guide.md` | New file: detailed guide | +300 |
| `docs/getting-started.md` | Update setup instructions | +50 |

**Total:** ~1,320 lines of code/documentation

---

## Appendix B: OpenRouter API Reference

### Authentication

```bash
curl https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "anthropic/claude-3.5-sonnet",
    "messages": [{"role": "user", "content": "Hello"}]
  }'
```

### Model Listing

```bash
curl https://openrouter.ai/api/v1/models \
  -H "Authorization: Bearer $OPENROUTER_API_KEY"
```

### Rate Limits

- Free tier: 20 requests/minute
- Paid tier: 200 requests/minute
- Enterprise: Custom limits

### Error Codes

- `401`: Invalid API key
- `429`: Rate limit exceeded
- `503`: Model temporarily unavailable

---

## Appendix C: Cost Calculator

**Interactive cost calculator for comparing provider strategies:**

```python
# Example usage
from decepticon.llm.cost_calculator import CostCalculator

calc = CostCalculator()

# Scenario: 10M input tokens, 5M output tokens per month
direct_cost = calc.calculate(
    strategy="direct",
    profile="eco",
    input_tokens=10_000_000,
    output_tokens=5_000_000,
)

openrouter_cost = calc.calculate(
    strategy="openrouter",
    profile="eco",
    input_tokens=10_000_000,
    output_tokens=5_000_000,
)

savings = direct_cost - openrouter_cost
print(f"Monthly savings: ${savings:.2f} ({savings/direct_cost*100:.1f}%)")
```

---

**End of Implementation Plan**

**Document Version:** 1.0  
**Last Updated:** 2026-04-28  
**Status:** Ready for Review