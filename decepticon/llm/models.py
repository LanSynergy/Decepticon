"""LLM model definitions — per-role model assignments with profile-based presets.

Two orthogonal axes control model selection:

  Profile  — which model tier to use (cost/performance tradeoff)
  Provider — how to authenticate (api key vs OAuth subscription)

Profiles:
  eco  — Balanced Anthropic-first ensemble (production engagements)
  max  — Maximum performance, Opus everywhere (high-value targets)
  test — Haiku-only, cheapest possible (development and CI)

Providers:
  api  — API keys (x-api-key header), standard LiteLLM routing
  auth — Claude Code OAuth subscription (Bearer token), no API cost

Usage:
  mapping = LLMModelMapping.from_profile("eco").with_provider("auth")

  DECEPTICON_MODEL_PROFILE=eco   (env var, default: eco)
  DECEPTICON_MODEL_PROVIDER=auth (env var, default: api)

With provider=auth, all anthropic/* primary models are automatically
remapped to auth/* so they route through the OAuth handler.
Fallbacks stay on the api provider as a paid safety net.

Profiles (April 2026):

  eco:
    Orchestrator  Opus 4.6        → GPT-5.4         $5/$25
    Soundwave     Haiku 4.5       → Gemini 2.5 Flash $1/$5
    Exploit       Sonnet 4.6      → GPT-4.1         $3/$15
    Recon         Haiku 4.5       → Gemini 2.5 Flash $1/$5
    PostExploit   Sonnet 4.6      → GPT-4.1         $3/$15

  max:
    Orchestrator  Opus 4.6        → GPT-5.4         $5/$25
    Soundwave     Sonnet 4.6      → Haiku 4.5       $3/$15
    Exploit       Opus 4.6        → Sonnet 4.6      $5/$25
    Recon         Sonnet 4.6      → Opus 4.6        $3/$15
    PostExploit   Opus 4.6        → Sonnet 4.6      $5/$25

  test:
    All roles     Haiku 4.5       → (none)           $1/$5

Model names use LiteLLM provider-prefix format for direct proxy routing.
Fallbacks activate via ModelFallbackMiddleware on API failure (outage, rate limit).
"""

from __future__ import annotations

import os
from enum import StrEnum

from pydantic import BaseModel, Field, field_validator

from decepticon.core.logging import get_logger

log = get_logger("llm.models")


class ModelProfile(StrEnum):
    """Model cost/performance profile (tier)."""

    ECO = "eco"
    MAX = "max"
    TEST = "test"


class ModelProvider(StrEnum):
    """Authentication provider for LLM requests.

    api        — API keys via x-api-key header (default)
    auth       — Claude Code OAuth subscription via Bearer token, no API cost
    openrouter — OpenRouter unified gateway (single API key for 200+ models)
    hybrid     — Mixed strategy (direct Anthropic + OpenRouter for others)
    """

    API = "api"
    AUTH = "auth"
    OPENROUTER = "openrouter"
    HYBRID = "hybrid"


# ── Model constants ──────────────────────────────────────────────────────

# Direct provider models (API keys)
OPUS = "anthropic/claude-opus-4-6"
SONNET = "anthropic/claude-sonnet-4-6"
HAIKU = "anthropic/claude-haiku-4-5"
GPT_5 = "openai/gpt-5.4"
GPT_4 = "openai/gpt-4.1"
GEMINI_FLASH = "gemini/gemini-2.5-flash"
MINIMAX = "minimax/MiniMax-M2.7"
MINIMAX_HIGHSPEED = "minimax/MiniMax-M2.7-highspeed"
OLLAMA_LOCAL = "ollama/llama3.2"

# OpenRouter models (unified gateway)
# Anthropic via OpenRouter
OPENROUTER_OPUS = "openrouter/anthropic/claude-opus-4-6"
OPENROUTER_SONNET = "openrouter/anthropic/claude-sonnet-4-6"
OPENROUTER_HAIKU = "openrouter/anthropic/claude-haiku-4-5"

# OpenAI via OpenRouter
OPENROUTER_GPT_5 = "openrouter/openai/gpt-5.4"
OPENROUTER_GPT_4 = "openrouter/openai/gpt-4.1"
OPENROUTER_GPT_4O = "openrouter/openai/gpt-4o"

# Google via OpenRouter
OPENROUTER_GEMINI_PRO = "openrouter/google/gemini-pro-1.5"
OPENROUTER_GEMINI_FLASH = "openrouter/google/gemini-flash-1.5"

# Meta Llama via OpenRouter
OPENROUTER_LLAMA_405B = "openrouter/meta-llama/llama-3.1-405b-instruct"
OPENROUTER_LLAMA_70B = "openrouter/meta-llama/llama-3.1-70b-instruct"
OPENROUTER_LLAMA_8B = "openrouter/meta-llama/llama-3.1-8b-instruct"

# Mistral via OpenRouter
OPENROUTER_MISTRAL_LARGE = "openrouter/mistralai/mistral-large"
OPENROUTER_MISTRAL_MEDIUM = "openrouter/mistralai/mistral-medium"
OPENROUTER_MIXTRAL_8X7B = "openrouter/mistralai/mixtral-8x7b-instruct"

# Cohere via OpenRouter
OPENROUTER_COMMAND_R_PLUS = "openrouter/cohere/command-r-plus"
OPENROUTER_COMMAND_R = "openrouter/cohere/command-r"


class ProxyConfig(BaseModel):
    """LiteLLM proxy connection settings."""

    url: str = "http://localhost:4000"
    api_key: str = "sk-decepticon-master"
    timeout: int = 120
    max_retries: int = 2


class ModelAssignment(BaseModel):
    """Primary + fallback model for an agent role."""

    primary: str
    fallback: str | None = None
    temperature: float = 0.7
    max_tokens: int | None = None

    @field_validator("temperature")
    @classmethod
    def validate_temperature(cls, v: float) -> float:
        if not 0.0 <= v <= 2.0:
            raise ValueError("temperature must be between 0.0 and 2.0")
        return v


class LLMModelMapping(BaseModel):
    """Role → model assignment mapping.

    Model names use LiteLLM provider-prefix format for direct routing.
    Use from_profile() to get a preset configuration.
    """

    # ── Strategic tier ──────────────────────────────────────────────
    # Reasoning-heavy, few iterations, quality > cost

    decepticon: ModelAssignment = Field(
        default_factory=lambda: ModelAssignment(
            primary=OPUS,
            fallback=GPT_5,
            temperature=0.4,
        )
    )

    # ── Document tier ──────────────────────────────────────────────
    # Structured JSON generation from interviews, schema-guided output

    soundwave: ModelAssignment = Field(
        default_factory=lambda: ModelAssignment(
            primary=HAIKU,
            fallback=GEMINI_FLASH,
            temperature=0.4,
        )
    )

    # ── Precision tier ──────────────────────────────────────────────
    # High-stakes execution, moderate iterations, precision critical

    exploit: ModelAssignment = Field(
        default_factory=lambda: ModelAssignment(
            primary=SONNET,
            fallback=GPT_4,
            temperature=0.3,
        )
    )

    analyst: ModelAssignment = Field(
        default_factory=lambda: ModelAssignment(
            # Source review + chain reasoning benefits from higher-tier
            # reasoning. Sonnet primary, Opus fallback so the chain
            # planner gets a smarter model when rate limits hit.
            primary=SONNET,
            fallback=OPUS,
            temperature=0.2,
        )
    )

    reverser: ModelAssignment = Field(
        default_factory=lambda: ModelAssignment(
            primary=SONNET,
            fallback=OPUS,
            temperature=0.2,
        )
    )

    contract_auditor: ModelAssignment = Field(
        default_factory=lambda: ModelAssignment(
            primary=OPUS,
            fallback=SONNET,
            temperature=0.2,
        )
    )

    cloud_hunter: ModelAssignment = Field(
        default_factory=lambda: ModelAssignment(
            primary=SONNET,
            fallback=OPUS,
            temperature=0.2,
        )
    )

    ad_operator: ModelAssignment = Field(
        default_factory=lambda: ModelAssignment(
            primary=SONNET,
            fallback=OPUS,
            temperature=0.2,
        )
    )

    # ── Tactical tier ───────────────────────────────────────────────
    # Tool-heavy, many iterations, speed + cost efficiency matter

    recon: ModelAssignment = Field(
        default_factory=lambda: ModelAssignment(
            primary=HAIKU,
            fallback=GEMINI_FLASH,
            temperature=0.3,
        )
    )

    postexploit: ModelAssignment = Field(
        default_factory=lambda: ModelAssignment(
            primary=SONNET,
            fallback=GPT_4,
            temperature=0.3,
        )
    )

    defender: ModelAssignment = Field(
        default_factory=lambda: ModelAssignment(
            primary=SONNET,
            fallback=HAIKU,
            temperature=0.2,
        )
    )

    # ── Vulnresearch pipeline tier ─────────────────────────────────
    # Five specialist sub-agents with scale-tuned model assignments.

    vulnresearch: ModelAssignment = Field(
        default_factory=lambda: ModelAssignment(
            primary=OPUS,
            fallback=GPT_5,
            temperature=0.4,
        )
    )

    scanner: ModelAssignment = Field(
        default_factory=lambda: ModelAssignment(
            primary=HAIKU,
            fallback=GEMINI_FLASH,
            temperature=0.2,
        )
    )

    detector: ModelAssignment = Field(
        default_factory=lambda: ModelAssignment(
            primary=SONNET,
            fallback=GPT_4,
            temperature=0.2,
        )
    )

    verifier: ModelAssignment = Field(
        default_factory=lambda: ModelAssignment(
            primary=SONNET,
            fallback=GPT_4,
            temperature=0.2,
        )
    )

    patcher: ModelAssignment = Field(
        default_factory=lambda: ModelAssignment(
            primary=OPUS,
            fallback=SONNET,
            temperature=0.2,
        )
    )

    exploiter: ModelAssignment = Field(
        default_factory=lambda: ModelAssignment(
            primary=OPUS,
            fallback=SONNET,
            temperature=0.2,
        )
    )

    def get_assignment(self, role: str) -> ModelAssignment:
        """Get model assignment for a role.

        Raises KeyError if role not found.
        """
        if not hasattr(self, role):
            raise KeyError(f"No model assignment for role: {role}")
        return getattr(self, role)

    @classmethod
    def from_profile(cls, profile: ModelProfile | str) -> LLMModelMapping:
        """Create a model mapping from a named profile.

        Profiles:
          eco  — Balanced Anthropic-first (Opus/Sonnet/Haiku mix)
          max  — Maximum performance (Opus + Sonnet everywhere)
          test — Cheapest possible (Haiku-only, no fallbacks)
        """
        profile = ModelProfile(profile)

        if profile == ModelProfile.ECO:
            return cls()

        if profile == ModelProfile.MAX:
            return cls(
                decepticon=ModelAssignment(
                    primary=OPUS,
                    fallback=GPT_5,
                    temperature=0.4,
                ),
                soundwave=ModelAssignment(
                    primary=SONNET,
                    fallback=HAIKU,
                    temperature=0.4,
                ),
                exploit=ModelAssignment(
                    primary=OPUS,
                    fallback=SONNET,
                    temperature=0.3,
                ),
                analyst=ModelAssignment(
                    primary=OPUS,
                    fallback=SONNET,
                    temperature=0.2,
                ),
                recon=ModelAssignment(
                    primary=SONNET,
                    fallback=OPUS,
                    temperature=0.3,
                ),
                postexploit=ModelAssignment(
                    primary=OPUS,
                    fallback=SONNET,
                    temperature=0.3,
                ),
                defender=ModelAssignment(
                    primary=OPUS,
                    fallback=SONNET,
                    temperature=0.2,
                ),
            )

        if profile == ModelProfile.TEST:
            return cls(
                decepticon=ModelAssignment(primary=HAIKU, temperature=0.4),
                soundwave=ModelAssignment(primary=HAIKU, temperature=0.4),
                exploit=ModelAssignment(primary=HAIKU, temperature=0.3),
                analyst=ModelAssignment(primary=HAIKU, temperature=0.2),
                reverser=ModelAssignment(primary=HAIKU, temperature=0.2),
                contract_auditor=ModelAssignment(primary=HAIKU, temperature=0.2),
                cloud_hunter=ModelAssignment(primary=HAIKU, temperature=0.2),
                ad_operator=ModelAssignment(primary=HAIKU, temperature=0.2),
                recon=ModelAssignment(primary=HAIKU, temperature=0.3),
                postexploit=ModelAssignment(primary=HAIKU, temperature=0.3),
                defender=ModelAssignment(primary=HAIKU, temperature=0.2),
                vulnresearch=ModelAssignment(primary=HAIKU, temperature=0.4),
                scanner=ModelAssignment(primary=HAIKU, temperature=0.2),
                detector=ModelAssignment(primary=HAIKU, temperature=0.2),
                verifier=ModelAssignment(primary=HAIKU, temperature=0.2),
                patcher=ModelAssignment(primary=HAIKU, temperature=0.2),
                exploiter=ModelAssignment(primary=HAIKU, temperature=0.2),
            )

        raise ValueError(f"Unknown profile: {profile}")  # type: ignore[unreachable]

    @classmethod
    def from_env_overrides(cls, base_profile: ModelProfile | str = ModelProfile.ECO) -> LLMModelMapping:
        """Create a model mapping from a base profile with environment variable overrides.

        Environment variables allow per-agent-role model customization:
        
        Primary model overrides:
          DECEPTICON_MODEL_DECEPTICON=openrouter/anthropic/claude-opus-4-6
          DECEPTICON_MODEL_RECON=openrouter/meta-llama/llama-3.1-70b-instruct
          DECEPTICON_MODEL_EXPLOIT=openrouter/anthropic/claude-sonnet-4-6
        
        Fallback model overrides (optional):
          DECEPTICON_MODEL_DECEPTICON_FALLBACK=openrouter/openai/gpt-5.4
          DECEPTICON_MODEL_RECON_FALLBACK=openrouter/google/gemini-flash-1.5
        
        Supported agent roles:
          decepticon, soundwave, recon, exploit, postexploit
          analyst, reverser, contract_auditor, cloud_hunter, ad_operator
          vulnresearch, scanner, detector, verifier, patcher, exploiter, defender
        
        Args:
            base_profile: Base profile to start from (eco/max/test)
        
        Returns:
            LLMModelMapping with environment variable overrides applied
        
        Example:
            # Start with eco profile, override recon to use Llama 70B
            DECEPTICON_MODEL_RECON=openrouter/meta-llama/llama-3.1-70b-instruct
            mapping = LLMModelMapping.from_env_overrides("eco")
        """
        # Start with base profile
        mapping = cls.from_profile(base_profile)
        
        # Get all agent role fields
        role_fields = cls.model_fields.keys()
        
        # Check for environment variable overrides
        overrides = {}
        for role in role_fields:
            env_var_primary = f"DECEPTICON_MODEL_{role.upper()}"
            env_var_fallback = f"DECEPTICON_MODEL_{role.upper()}_FALLBACK"
            
            primary_override = os.getenv(env_var_primary)
            fallback_override = os.getenv(env_var_fallback)
            
            # If either override exists, create new assignment
            if primary_override or fallback_override:
                current_assignment = getattr(mapping, role)
                
                # Use override if provided, otherwise keep current value
                new_primary = primary_override if primary_override else current_assignment.primary
                new_fallback = fallback_override if fallback_override else current_assignment.fallback
                
                # Validate model names exist in catalog (optional, log warning if not found)
                if primary_override:
                    log.info(
                        "Environment override for role '%s': primary model '%s' → '%s'",
                        role,
                        current_assignment.primary,
                        new_primary,
                    )
                
                if fallback_override:
                    log.info(
                        "Environment override for role '%s': fallback model '%s' → '%s'",
                        role,
                        current_assignment.fallback or "(none)",
                        new_fallback,
                    )
                
                overrides[role] = ModelAssignment(
                    primary=new_primary,
                    fallback=new_fallback,
                    temperature=current_assignment.temperature,
                    max_tokens=current_assignment.max_tokens,
                )
        
        # Apply overrides if any exist
        if overrides:
            mapping = mapping.model_copy(update=overrides)
        
        return mapping

    def with_provider(self, provider: ModelProvider | str) -> "LLMModelMapping":
        """Return a new mapping with primary models remapped for the given provider.

        Provider remapping strategies:

        ModelProvider.API
            No-op, returns self unchanged. Models use their original provider
            prefixes (anthropic/, openai/, gemini/, etc.) and route through
            LiteLLM proxy with direct API keys.

        ModelProvider.AUTH
            Remap ``anthropic/*`` primaries to ``auth/*`` so they route through
            the Claude Code OAuth handler. Fallbacks stay on API provider as a
            paid safety net when subscription hits limits. Non-Anthropic models
            (GPT, Gemini, etc.) are left unchanged.

        ModelProvider.OPENROUTER
            Remap ALL primaries to ``openrouter/<provider>/<model>`` format.
            Routes all requests through OpenRouter unified gateway using single
            OPENROUTER_API_KEY. Fallbacks also remapped to OpenRouter.
            
            Examples:
              anthropic/claude-opus-4-6 → openrouter/anthropic/claude-opus-4-6
              openai/gpt-5.4 → openrouter/openai/gpt-5.4
              gemini/gemini-2.5-flash → openrouter/google/gemini-flash-1.5

        ModelProvider.HYBRID
            Mixed strategy for cost optimization:
            - Keep Anthropic models on direct API (better rate limits)
            - Route non-Anthropic models through OpenRouter (cost savings)
            - Fallbacks use OpenRouter when primary is direct, vice versa
            
            This gives you:
            - Best rate limits on Anthropic (direct API)
            - Access to open-source models (Llama, Mistral via OpenRouter)
            - Cost optimization (use cheaper models where appropriate)

        Model name remapping rules:
        - anthropic/claude-* → openrouter/anthropic/claude-*
        - openai/gpt-* → openrouter/openai/gpt-*
        - gemini/gemini-* → openrouter/google/gemini-* (provider name differs)
        - Other providers passed through as-is with openrouter/ prefix

        Only primary models are remapped; fallbacks are preserved as safety nets
        unless provider is OPENROUTER (then fallbacks also remapped).
        """
        provider = ModelProvider(provider)
        if provider == ModelProvider.API:
            return self

        def _remap_to_auth(assignment: ModelAssignment) -> ModelAssignment:
            """Remap Anthropic models to auth/* for OAuth subscription."""
            primary = assignment.primary
            if primary.startswith("anthropic/"):
                model_id = primary.split("/", 1)[1]
                primary = f"auth/{model_id}"
            return ModelAssignment(
                primary=primary,
                fallback=assignment.fallback,
                temperature=assignment.temperature,
                max_tokens=assignment.max_tokens,
            )

        def _remap_to_openrouter(model_name: str) -> str:
            """Remap model name to OpenRouter format.
            
            Handles provider name differences (e.g., gemini → google).
            """
            if model_name.startswith("openrouter/"):
                return model_name  # Already in OpenRouter format
            
            if model_name.startswith("anthropic/"):
                # anthropic/claude-opus-4-6 → openrouter/anthropic/claude-opus-4-6
                model_id = model_name.split("/", 1)[1]
                return f"openrouter/anthropic/{model_id}"
            
            if model_name.startswith("openai/"):
                # openai/gpt-5.4 → openrouter/openai/gpt-5.4
                model_id = model_name.split("/", 1)[1]
                return f"openrouter/openai/{model_id}"
            
            if model_name.startswith("gemini/"):
                # gemini/gemini-2.5-flash → openrouter/google/gemini-flash-1.5
                # Note: OpenRouter uses "google" as provider, not "gemini"
                model_id = model_name.split("/", 1)[1]
                # Map to OpenRouter's Google model names
                if "flash" in model_id:
                    return "openrouter/google/gemini-flash-1.5"
                elif "pro" in model_id:
                    return "openrouter/google/gemini-pro-1.5"
                else:
                    # Fallback: use model_id as-is
                    return f"openrouter/google/{model_id}"
            
            # For other providers (minimax, ollama, etc.), pass through with openrouter/ prefix
            # This may not work for all providers, but provides a reasonable default
            return f"openrouter/{model_name}"

        def _remap_openrouter_full(assignment: ModelAssignment) -> ModelAssignment:
            """Remap both primary and fallback to OpenRouter."""
            primary = _remap_to_openrouter(assignment.primary)
            fallback = _remap_to_openrouter(assignment.fallback) if assignment.fallback else None
            return ModelAssignment(
                primary=primary,
                fallback=fallback,
                temperature=assignment.temperature,
                max_tokens=assignment.max_tokens,
            )

        def _remap_hybrid(assignment: ModelAssignment) -> ModelAssignment:
            """Hybrid strategy: direct Anthropic, OpenRouter for others."""
            primary = assignment.primary
            fallback = assignment.fallback
            
            # Keep Anthropic on direct API for better rate limits
            if not primary.startswith("anthropic/"):
                primary = _remap_to_openrouter(primary)
            
            # Route fallbacks through OpenRouter for cost savings
            if fallback and not fallback.startswith("anthropic/"):
                fallback = _remap_to_openrouter(fallback)
            
            return ModelAssignment(
                primary=primary,
                fallback=fallback,
                temperature=assignment.temperature,
                max_tokens=assignment.max_tokens,
            )

        # Select remapping function based on provider
        if provider == ModelProvider.AUTH:
            remap_fn = _remap_to_auth
        elif provider == ModelProvider.OPENROUTER:
            remap_fn = _remap_openrouter_full
        elif provider == ModelProvider.HYBRID:
            remap_fn = _remap_hybrid
        else:
            raise ValueError(f"Unknown provider: {provider}")

        return self.model_copy(
            update={field: remap_fn(getattr(self, field)) for field in self.__class__.model_fields}
        )
