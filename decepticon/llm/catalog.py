"""Model catalog — metadata and cost information for available LLM models.

Provides structured information about models available through different providers,
including context lengths, pricing, and capabilities. Used for cost optimization,
model selection, and user-facing documentation.

Usage:
    # Get info for a specific model
    info = get_model_info("openrouter/anthropic/claude-opus-4-6")
    print(f"{info.name}: ${info.cost_input}/M input, ${info.cost_output}/M output")
    
    # List all OpenRouter models
    models = list_available_models(provider=ModelProvider.OPENROUTER)
    
    # Compare two models
    comparison = compare_models(
        "openrouter/anthropic/claude-opus-4-6",
        "openrouter/meta-llama/llama-3.1-405b-instruct"
    )
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel

from decepticon.llm.models import ModelProvider


# ── Model Tier Classification ────────────────────────────────────────────

ModelTier = Literal["strategic", "precision", "tactical", "budget"]

# strategic — Reasoning-heavy, few iterations, quality > cost (Opus, GPT-5)
# precision — High-stakes execution, moderate iterations (Sonnet, GPT-4)
# tactical  — Tool-heavy, many iterations, speed + cost efficiency (Haiku, Gemini Flash)
# budget    — Maximum cost efficiency, acceptable quality tradeoff (Llama, Mistral)


# ── ModelInfo Dataclass ──────────────────────────────────────────────────


@dataclass
class ModelInfo:
    """Metadata for a single LLM model.
    
    Attributes:
        id: Full model identifier (e.g., "openrouter/anthropic/claude-opus-4-6")
        name: Human-readable display name (e.g., "Claude Opus 4.6")
        provider: Model provider (e.g., "Anthropic", "OpenAI", "Meta")
        tier: Performance/cost tier (strategic/precision/tactical/budget)
        context_length: Maximum context window in tokens
        cost_input: Cost per 1M input tokens in USD
        cost_output: Cost per 1M output tokens in USD
        description: Brief description of model capabilities (optional)
    """

    id: str
    name: str
    provider: str
    tier: ModelTier
    context_length: int
    cost_input: float
    cost_output: float
    description: str = ""

    def __post_init__(self) -> None:
        """Validate model info after initialization."""
        if self.context_length <= 0:
            raise ValueError(f"context_length must be positive, got {self.context_length}")
        if self.cost_input < 0:
            raise ValueError(f"cost_input must be non-negative, got {self.cost_input}")
        if self.cost_output < 0:
            raise ValueError(f"cost_output must be non-negative, got {self.cost_output}")


# ── Model Catalog Registry ───────────────────────────────────────────────

# Comprehensive catalog of all supported models with accurate pricing
# Costs are per 1M tokens in USD (as of April 2026)

_MODEL_CATALOG: dict[str, ModelInfo] = {
    # ── Anthropic Models (Direct API) ────────────────────────────────────
    "anthropic/claude-opus-4-6": ModelInfo(
        id="anthropic/claude-opus-4-6",
        name="Claude Opus 4.6",
        provider="Anthropic",
        tier="strategic",
        context_length=200_000,
        cost_input=5.0,
        cost_output=25.0,
        description="Most capable model for complex reasoning and analysis",
    ),
    "anthropic/claude-sonnet-4-6": ModelInfo(
        id="anthropic/claude-sonnet-4-6",
        name="Claude Sonnet 4.6",
        provider="Anthropic",
        tier="precision",
        context_length=200_000,
        cost_input=3.0,
        cost_output=15.0,
        description="Balanced performance and cost for most tasks",
    ),
    "anthropic/claude-haiku-4-5": ModelInfo(
        id="anthropic/claude-haiku-4-5",
        name="Claude Haiku 4.5",
        provider="Anthropic",
        tier="tactical",
        context_length=200_000,
        cost_input=1.0,
        cost_output=5.0,
        description="Fast and efficient for high-volume tasks",
    ),
    # ── Anthropic via OpenRouter ─────────────────────────────────────────
    "openrouter/anthropic/claude-opus-4-6": ModelInfo(
        id="openrouter/anthropic/claude-opus-4-6",
        name="Claude Opus 4.6 (OpenRouter)",
        provider="Anthropic",
        tier="strategic",
        context_length=200_000,
        cost_input=4.5,  # ~10% cheaper via OpenRouter
        cost_output=22.5,
        description="Most capable model via OpenRouter unified gateway",
    ),
    "openrouter/anthropic/claude-sonnet-4-6": ModelInfo(
        id="openrouter/anthropic/claude-sonnet-4-6",
        name="Claude Sonnet 4.6 (OpenRouter)",
        provider="Anthropic",
        tier="precision",
        context_length=200_000,
        cost_input=2.7,
        cost_output=13.5,
        description="Balanced model via OpenRouter",
    ),
    "openrouter/anthropic/claude-haiku-4-5": ModelInfo(
        id="openrouter/anthropic/claude-haiku-4-5",
        name="Claude Haiku 4.5 (OpenRouter)",
        provider="Anthropic",
        tier="tactical",
        context_length=200_000,
        cost_input=0.9,
        cost_output=4.5,
        description="Fast model via OpenRouter",
    ),
    # ── OpenAI Models ────────────────────────────────────────────────────
    "openai/gpt-5.4": ModelInfo(
        id="openai/gpt-5.4",
        name="GPT-5.4",
        provider="OpenAI",
        tier="strategic",
        context_length=128_000,
        cost_input=5.0,
        cost_output=25.0,
        description="Latest GPT model with advanced reasoning",
    ),
    "openai/gpt-4.1": ModelInfo(
        id="openai/gpt-4.1",
        name="GPT-4.1",
        provider="OpenAI",
        tier="precision",
        context_length=128_000,
        cost_input=3.0,
        cost_output=15.0,
        description="Proven GPT-4 series model",
    ),
    "openrouter/openai/gpt-5.4": ModelInfo(
        id="openrouter/openai/gpt-5.4",
        name="GPT-5.4 (OpenRouter)",
        provider="OpenAI",
        tier="strategic",
        context_length=128_000,
        cost_input=4.5,
        cost_output=22.5,
        description="GPT-5.4 via OpenRouter",
    ),
    "openrouter/openai/gpt-4.1": ModelInfo(
        id="openrouter/openai/gpt-4.1",
        name="GPT-4.1 (OpenRouter)",
        provider="OpenAI",
        tier="precision",
        context_length=128_000,
        cost_input=2.7,
        cost_output=13.5,
        description="GPT-4.1 via OpenRouter",
    ),
    "openrouter/openai/gpt-4o": ModelInfo(
        id="openrouter/openai/gpt-4o",
        name="GPT-4o (OpenRouter)",
        provider="OpenAI",
        tier="precision",
        context_length=128_000,
        cost_input=2.5,
        cost_output=10.0,
        description="Optimized GPT-4 variant via OpenRouter",
    ),
    # ── Google Models ────────────────────────────────────────────────────
    "gemini/gemini-2.5-flash": ModelInfo(
        id="gemini/gemini-2.5-flash",
        name="Gemini 2.5 Flash",
        provider="Google",
        tier="tactical",
        context_length=1_000_000,
        cost_input=1.0,
        cost_output=5.0,
        description="Fast model with massive context window",
    ),
    "openrouter/google/gemini-pro-1.5": ModelInfo(
        id="openrouter/google/gemini-pro-1.5",
        name="Gemini Pro 1.5 (OpenRouter)",
        provider="Google",
        tier="precision",
        context_length=1_000_000,
        cost_input=2.5,
        cost_output=10.0,
        description="Gemini Pro with 1M token context via OpenRouter",
    ),
    "openrouter/google/gemini-flash-1.5": ModelInfo(
        id="openrouter/google/gemini-flash-1.5",
        name="Gemini Flash 1.5 (OpenRouter)",
        provider="Google",
        tier="tactical",
        context_length=1_000_000,
        cost_input=0.5,
        cost_output=2.5,
        description="Fast Gemini with huge context via OpenRouter",
    ),
    # ── Meta Llama Models (OpenRouter only) ──────────────────────────────
    "openrouter/meta-llama/llama-3.1-405b-instruct": ModelInfo(
        id="openrouter/meta-llama/llama-3.1-405b-instruct",
        name="Llama 3.1 405B Instruct",
        provider="Meta",
        tier="strategic",
        context_length=128_000,
        cost_input=2.7,
        cost_output=2.7,
        description="Largest open-source model, competitive with proprietary",
    ),
    "openrouter/meta-llama/llama-3.1-70b-instruct": ModelInfo(
        id="openrouter/meta-llama/llama-3.1-70b-instruct",
        name="Llama 3.1 70B Instruct",
        provider="Meta",
        tier="budget",
        context_length=128_000,
        cost_input=0.59,
        cost_output=0.79,
        description="Cost-effective open-source model for most tasks",
    ),
    "openrouter/meta-llama/llama-3.1-8b-instruct": ModelInfo(
        id="openrouter/meta-llama/llama-3.1-8b-instruct",
        name="Llama 3.1 8B Instruct",
        provider="Meta",
        tier="budget",
        context_length=128_000,
        cost_input=0.06,
        cost_output=0.06,
        description="Ultra-fast, ultra-cheap for simple tasks",
    ),
    # ── Mistral Models (OpenRouter only) ─────────────────────────────────
    "openrouter/mistralai/mistral-large": ModelInfo(
        id="openrouter/mistralai/mistral-large",
        name="Mistral Large",
        provider="Mistral AI",
        tier="precision",
        context_length=128_000,
        cost_input=2.0,
        cost_output=6.0,
        description="Mistral's flagship model, strong reasoning",
    ),
    "openrouter/mistralai/mistral-medium": ModelInfo(
        id="openrouter/mistralai/mistral-medium",
        name="Mistral Medium",
        provider="Mistral AI",
        tier="tactical",
        context_length=32_000,
        cost_input=0.7,
        cost_output=2.1,
        description="Balanced Mistral model",
    ),
    "openrouter/mistralai/mixtral-8x7b-instruct": ModelInfo(
        id="openrouter/mistralai/mixtral-8x7b-instruct",
        name="Mixtral 8x7B Instruct",
        provider="Mistral AI",
        tier="budget",
        context_length=32_000,
        cost_input=0.24,
        cost_output=0.24,
        description="Mixture-of-experts model, excellent value",
    ),
    # ── Cohere Models (OpenRouter only) ──────────────────────────────────
    "openrouter/cohere/command-r-plus": ModelInfo(
        id="openrouter/cohere/command-r-plus",
        name="Command R+",
        provider="Cohere",
        tier="precision",
        context_length=128_000,
        cost_input=2.5,
        cost_output=10.0,
        description="Cohere's most capable model with RAG optimization",
    ),
    "openrouter/cohere/command-r": ModelInfo(
        id="openrouter/cohere/command-r",
        name="Command R",
        provider="Cohere",
        tier="tactical",
        context_length=128_000,
        cost_input=0.15,
        cost_output=0.6,
        description="Fast Cohere model optimized for retrieval",
    ),
    # ── Other Models ─────────────────────────────────────────────────────
    "minimax/MiniMax-M2.7": ModelInfo(
        id="minimax/MiniMax-M2.7",
        name="MiniMax M2.7",
        provider="MiniMax",
        tier="tactical",
        context_length=32_000,
        cost_input=0.5,
        cost_output=1.5,
        description="Chinese model with strong multilingual support",
    ),
    "minimax/MiniMax-M2.7-highspeed": ModelInfo(
        id="minimax/MiniMax-M2.7-highspeed",
        name="MiniMax M2.7 High-Speed",
        provider="MiniMax",
        tier="budget",
        context_length=32_000,
        cost_input=0.3,
        cost_output=0.9,
        description="Optimized for low latency",
    ),
    "ollama/llama3.2": ModelInfo(
        id="ollama/llama3.2",
        name="Llama 3.2 (Local)",
        provider="Ollama",
        tier="budget",
        context_length=128_000,
        cost_input=0.0,
        cost_output=0.0,
        description="Local model via Ollama, no API cost",
    ),
}


# ── Public API Functions ─────────────────────────────────────────────────


def get_model_info(model_name: str) -> ModelInfo:
    """Get metadata for a specific model.
    
    Args:
        model_name: Full model identifier (e.g., "openrouter/anthropic/claude-opus-4-6")
    
    Returns:
        ModelInfo object with complete metadata
    
    Raises:
        KeyError: If model not found in catalog
    
    Example:
        >>> info = get_model_info("openrouter/anthropic/claude-opus-4-6")
        >>> print(f"{info.name}: ${info.cost_input}/M input")
        Claude Opus 4.6 (OpenRouter): $4.5/M input
    """
    if model_name not in _MODEL_CATALOG:
        available = ", ".join(sorted(_MODEL_CATALOG.keys()))
        raise KeyError(
            f"Model '{model_name}' not found in catalog. "
            f"Available models: {available}"
        )
    return _MODEL_CATALOG[model_name]


def list_available_models(
    provider: ModelProvider | str | None = None,
    tier: ModelTier | None = None,
) -> list[ModelInfo]:
    """List all available models, optionally filtered by provider and/or tier.
    
    Args:
        provider: Filter by provider (e.g., ModelProvider.OPENROUTER, "Anthropic")
            - If ModelProvider enum: filters by routing strategy (openrouter/*, anthropic/*, etc.)
            - If string: filters by provider name ("Anthropic", "OpenAI", "Meta", etc.)
            - If None: returns all models
        tier: Filter by performance tier (strategic/precision/tactical/budget)
    
    Returns:
        List of ModelInfo objects matching the filters, sorted by cost (cheapest first)
    
    Example:
        >>> # All OpenRouter models
        >>> models = list_available_models(provider=ModelProvider.OPENROUTER)
        >>> 
        >>> # All Anthropic models (direct + OpenRouter)
        >>> models = list_available_models(provider="Anthropic")
        >>> 
        >>> # All budget-tier models
        >>> models = list_available_models(tier="budget")
        >>> 
        >>> # OpenRouter strategic models
        >>> models = list_available_models(
        ...     provider=ModelProvider.OPENROUTER,
        ...     tier="strategic"
        ... )
    """
    models = list(_MODEL_CATALOG.values())
    
    # Filter by provider
    if provider is not None:
        if isinstance(provider, ModelProvider):
            # Filter by routing strategy (model ID prefix)
            provider_str = str(provider.value)
            if provider_str == "openrouter":
                models = [m for m in models if m.id.startswith("openrouter/")]
            elif provider_str == "api":
                # Direct API models (no openrouter/ prefix)
                models = [m for m in models if not m.id.startswith("openrouter/")]
            elif provider_str == "auth":
                # Auth models use anthropic/ prefix
                models = [m for m in models if m.id.startswith("anthropic/")]
            # hybrid and other providers: return all (no filtering)
        else:
            # Filter by provider name (e.g., "Anthropic", "OpenAI")
            models = [m for m in models if m.provider.lower() == provider.lower()]
    
    # Filter by tier
    if tier is not None:
        models = [m for m in models if m.tier == tier]
    
    # Sort by total cost (input + output) for consistent ordering
    models.sort(key=lambda m: m.cost_input + m.cost_output)
    
    return models


def compare_models(model1: str, model2: str) -> dict[str, dict[str, str | float | int]]:
    """Compare two models side-by-side.
    
    Args:
        model1: First model identifier
        model2: Second model identifier
    
    Returns:
        Dictionary with comparison data for both models
    
    Raises:
        KeyError: If either model not found in catalog
    
    Example:
        >>> comparison = compare_models(
        ...     "openrouter/anthropic/claude-opus-4-6",
        ...     "openrouter/meta-llama/llama-3.1-405b-instruct"
        ... )
        >>> print(comparison["model1"]["name"])
        Claude Opus 4.6 (OpenRouter)
        >>> print(f"Cost difference: ${comparison['cost_difference']:.2f}/M tokens")
    """
    info1 = get_model_info(model1)
    info2 = get_model_info(model2)
    
    # Calculate cost differences (positive = model1 more expensive)
    input_diff = info1.cost_input - info2.cost_input
    output_diff = info1.cost_output - info2.cost_output
    total_diff = (info1.cost_input + info1.cost_output) - (info2.cost_input + info2.cost_output)
    
    # Calculate percentage differences
    input_pct = (input_diff / info2.cost_input * 100) if info2.cost_input > 0 else 0
    output_pct = (output_diff / info2.cost_output * 100) if info2.cost_output > 0 else 0
    
    return {
        "model1": {
            "id": info1.id,
            "name": info1.name,
            "provider": info1.provider,
            "tier": info1.tier,
            "context_length": info1.context_length,
            "cost_input": info1.cost_input,
            "cost_output": info1.cost_output,
            "total_cost": info1.cost_input + info1.cost_output,
        },
        "model2": {
            "id": info2.id,
            "name": info2.name,
            "provider": info2.provider,
            "tier": info2.tier,
            "context_length": info2.context_length,
            "cost_input": info2.cost_input,
            "cost_output": info2.cost_output,
            "total_cost": info2.cost_input + info2.cost_output,
        },
        "differences": {
            "input_cost_diff": input_diff,
            "output_cost_diff": output_diff,
            "total_cost_diff": total_diff,
            "input_cost_pct": input_pct,
            "output_cost_pct": output_pct,
            "context_length_diff": info1.context_length - info2.context_length,
        },
        "recommendation": _generate_recommendation(info1, info2, total_diff),
    }


def _generate_recommendation(info1: ModelInfo, info2: ModelInfo, cost_diff: float) -> str:
    """Generate a recommendation based on model comparison.
    
    Args:
        info1: First model info
        info2: Second model info
        cost_diff: Total cost difference (positive = model1 more expensive)
    
    Returns:
        Human-readable recommendation string
    """
    if abs(cost_diff) < 0.5:
        return f"Similar cost. Choose {info1.name} for {info1.tier} tasks, {info2.name} for {info2.tier} tasks."
    
    cheaper = info2 if cost_diff > 0 else info1
    expensive = info1 if cost_diff > 0 else info2
    savings_pct = abs(cost_diff) / (expensive.cost_input + expensive.cost_output) * 100
    
    if cheaper.tier == expensive.tier:
        return f"{cheaper.name} is {savings_pct:.0f}% cheaper with similar capabilities."
    
    return (
        f"{cheaper.name} is {savings_pct:.0f}% cheaper but {cheaper.tier}-tier. "
        f"Use {expensive.name} for {expensive.tier}-tier tasks requiring higher quality."
    )


# ── Helper Functions for Cost Estimation ─────────────────────────────────


class CostEstimate(BaseModel):
    """Cost estimate for a given token usage."""
    
    model_name: str
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float


def estimate_cost(
    model_name: str,
    input_tokens: int,
    output_tokens: int,
) -> CostEstimate:
    """Estimate cost for a given token usage.
    
    Args:
        model_name: Model identifier
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
    
    Returns:
        CostEstimate with detailed breakdown
    
    Example:
        >>> estimate = estimate_cost(
        ...     "openrouter/anthropic/claude-opus-4-6",
        ...     input_tokens=10_000,
        ...     output_tokens=5_000
        ... )
        >>> print(f"Total cost: ${estimate.total_cost:.4f}")
        Total cost: $0.1575
    """
    info = get_model_info(model_name)
    
    # Convert from per-1M-tokens to actual cost
    input_cost = (input_tokens / 1_000_000) * info.cost_input
    output_cost = (output_tokens / 1_000_000) * info.cost_output
    
    return CostEstimate(
        model_name=model_name,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        input_cost=input_cost,
        output_cost=output_cost,
        total_cost=input_cost + output_cost,
    )

# Made with Bob
