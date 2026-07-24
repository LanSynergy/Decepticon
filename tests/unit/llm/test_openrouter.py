"""Unit tests for OpenRouter integration functionality.

Tests cover:
- ModelProvider enum includes OPENROUTER and HYBRID
- OpenRouter model constants are defined correctly
- with_provider() remapping logic for all provider types
- HYBRID mode keeps Anthropic direct, routes others to OpenRouter
- Backward compatibility (API and AUTH providers unchanged)
"""

import pytest

from decepticon.llm.models import (
    GEMINI_FLASH,
    GPT_4,
    GPT_5,
    HAIKU,
    OPENROUTER_COMMAND_R,
    OPENROUTER_COMMAND_R_PLUS,
    OPENROUTER_GEMINI_FLASH,
    OPENROUTER_GEMINI_PRO,
    OPENROUTER_GPT_4,
    OPENROUTER_GPT_4O,
    OPENROUTER_GPT_5,
    OPENROUTER_HAIKU,
    OPENROUTER_LLAMA_405B,
    OPENROUTER_LLAMA_70B,
    OPENROUTER_LLAMA_8B,
    OPENROUTER_MISTRAL_LARGE,
    OPENROUTER_MISTRAL_MEDIUM,
    OPENROUTER_MIXTRAL_8X7B,
    OPENROUTER_OPUS,
    OPENROUTER_SONNET,
    OPUS,
    SONNET,
    LLMModelMapping,
    ModelAssignment,
    ModelProvider,
)


class TestModelProviderEnum:
    """Tests for ModelProvider enum with OpenRouter support."""

    def test_provider_enum_has_openrouter(self):
        """Test that ModelProvider enum includes OPENROUTER."""
        assert hasattr(ModelProvider, "OPENROUTER")
        assert ModelProvider.OPENROUTER == "openrouter"

    def test_provider_enum_has_hybrid(self):
        """Test that ModelProvider enum includes HYBRID."""
        assert hasattr(ModelProvider, "HYBRID")
        assert ModelProvider.HYBRID == "hybrid"

    def test_provider_enum_all_values(self):
        """Test that all expected provider values exist."""
        expected_providers = {"api", "auth", "openrouter", "hybrid"}
        actual_providers = {p.value for p in ModelProvider}
        assert expected_providers == actual_providers

    def test_provider_enum_from_string(self):
        """Test that provider can be created from string."""
        assert ModelProvider("openrouter") == ModelProvider.OPENROUTER
        assert ModelProvider("hybrid") == ModelProvider.HYBRID
        assert ModelProvider("api") == ModelProvider.API
        assert ModelProvider("auth") == ModelProvider.AUTH


class TestOpenRouterModelConstants:
    """Tests for OpenRouter model constant definitions."""

    def test_openrouter_anthropic_models(self):
        """Test that OpenRouter Anthropic models are defined correctly."""
        assert OPENROUTER_OPUS == "openrouter/anthropic/claude-opus-4-6"
        assert OPENROUTER_SONNET == "openrouter/anthropic/claude-sonnet-4-6"
        assert OPENROUTER_HAIKU == "openrouter/anthropic/claude-haiku-4-5"

    def test_openrouter_openai_models(self):
        """Test that OpenRouter OpenAI models are defined correctly."""
        assert OPENROUTER_GPT_5 == "openrouter/openai/gpt-5.4"
        assert OPENROUTER_GPT_4 == "openrouter/openai/gpt-4.1"
        assert OPENROUTER_GPT_4O == "openrouter/openai/gpt-4o"

    def test_openrouter_google_models(self):
        """Test that OpenRouter Google models are defined correctly."""
        assert OPENROUTER_GEMINI_PRO == "openrouter/google/gemini-pro-1.5"
        assert OPENROUTER_GEMINI_FLASH == "openrouter/google/gemini-flash-1.5"

    def test_openrouter_llama_models(self):
        """Test that OpenRouter Llama models are defined correctly."""
        assert OPENROUTER_LLAMA_405B == "openrouter/meta-llama/llama-3.1-405b-instruct"
        assert OPENROUTER_LLAMA_70B == "openrouter/meta-llama/llama-3.1-70b-instruct"
        assert OPENROUTER_LLAMA_8B == "openrouter/meta-llama/llama-3.1-8b-instruct"

    def test_openrouter_mistral_models(self):
        """Test that OpenRouter Mistral models are defined correctly."""
        assert OPENROUTER_MISTRAL_LARGE == "openrouter/mistralai/mistral-large"
        assert OPENROUTER_MISTRAL_MEDIUM == "openrouter/mistralai/mistral-medium"
        assert OPENROUTER_MIXTRAL_8X7B == "openrouter/mistralai/mixtral-8x7b-instruct"

    def test_openrouter_cohere_models(self):
        """Test that OpenRouter Cohere models are defined correctly."""
        assert OPENROUTER_COMMAND_R_PLUS == "openrouter/cohere/command-r-plus"
        assert OPENROUTER_COMMAND_R == "openrouter/cohere/command-r"

    def test_all_openrouter_models_have_prefix(self):
        """Test that all OpenRouter constants start with 'openrouter/'."""
        openrouter_constants = [
            OPENROUTER_OPUS,
            OPENROUTER_SONNET,
            OPENROUTER_HAIKU,
            OPENROUTER_GPT_5,
            OPENROUTER_GPT_4,
            OPENROUTER_GPT_4O,
            OPENROUTER_GEMINI_PRO,
            OPENROUTER_GEMINI_FLASH,
            OPENROUTER_LLAMA_405B,
            OPENROUTER_LLAMA_70B,
            OPENROUTER_LLAMA_8B,
            OPENROUTER_MISTRAL_LARGE,
            OPENROUTER_MISTRAL_MEDIUM,
            OPENROUTER_MIXTRAL_8X7B,
            OPENROUTER_COMMAND_R_PLUS,
            OPENROUTER_COMMAND_R,
        ]
        for model in openrouter_constants:
            assert model.startswith("openrouter/")


class TestWithProviderAPI:
    """Tests for with_provider(ModelProvider.API) - no-op behavior."""

    def test_api_provider_returns_unchanged(self):
        """Test that API provider returns mapping unchanged."""
        mapping = LLMModelMapping()
        remapped = mapping.with_provider(ModelProvider.API)
        
        # Should be the same object (no-op)
        assert remapped is mapping

    def test_api_provider_preserves_all_assignments(self):
        """Test that API provider preserves all role assignments."""
        mapping = LLMModelMapping()
        remapped = mapping.with_provider("api")
        
        # Check a few representative roles
        assert remapped.decepticon.primary == OPUS
        assert remapped.recon.primary == HAIKU
        assert remapped.exploit.primary == SONNET


class TestWithProviderAUTH:
    """Tests for with_provider(ModelProvider.AUTH) - OAuth remapping."""

    def test_auth_remaps_anthropic_primaries(self):
        """Test that AUTH provider remaps Anthropic primaries to auth/*."""
        mapping = LLMModelMapping()
        remapped = mapping.with_provider(ModelProvider.AUTH)
        
        # Anthropic models should be remapped
        assert remapped.decepticon.primary == "auth/claude-opus-4-6"
        assert remapped.exploit.primary == "auth/claude-sonnet-4-6"
        assert remapped.recon.primary == "auth/claude-haiku-4-5"

    def test_auth_preserves_fallbacks(self):
        """Test that AUTH provider preserves fallback models."""
        mapping = LLMModelMapping()
        remapped = mapping.with_provider(ModelProvider.AUTH)
        
        # Fallbacks should stay on API provider
        assert remapped.decepticon.fallback == GPT_5
        assert remapped.exploit.fallback == GPT_4
        assert remapped.recon.fallback == GEMINI_FLASH

    def test_auth_preserves_non_anthropic_models(self):
        """Test that AUTH provider doesn't change non-Anthropic models."""
        mapping = LLMModelMapping()
        remapped = mapping.with_provider(ModelProvider.AUTH)
        
        # Non-Anthropic primaries should be unchanged
        assert remapped.decepticon.fallback == GPT_5
        assert remapped.recon.fallback == GEMINI_FLASH

    def test_auth_preserves_temperature(self):
        """Test that AUTH provider preserves temperature settings."""
        mapping = LLMModelMapping()
        remapped = mapping.with_provider(ModelProvider.AUTH)
        
        assert remapped.decepticon.temperature == 0.4
        assert remapped.exploit.temperature == 0.3
        assert remapped.recon.temperature == 0.3


class TestWithProviderOPENROUTER:
    """Tests for with_provider(ModelProvider.OPENROUTER) - full remapping."""

    def test_openrouter_remaps_anthropic_models(self):
        """Test that OPENROUTER remaps Anthropic models correctly."""
        mapping = LLMModelMapping()
        remapped = mapping.with_provider(ModelProvider.OPENROUTER)
        
        assert remapped.decepticon.primary == OPENROUTER_OPUS
        assert remapped.exploit.primary == OPENROUTER_SONNET
        assert remapped.recon.primary == OPENROUTER_HAIKU

    def test_openrouter_remaps_openai_models(self):
        """Test that OPENROUTER remaps OpenAI models correctly."""
        mapping = LLMModelMapping()
        remapped = mapping.with_provider(ModelProvider.OPENROUTER)
        
        # Check fallbacks that use OpenAI
        assert remapped.decepticon.fallback == OPENROUTER_GPT_5
        assert remapped.exploit.fallback == OPENROUTER_GPT_4

    def test_openrouter_remaps_gemini_models(self):
        """Test that OPENROUTER remaps Gemini models correctly."""
        mapping = LLMModelMapping()
        remapped = mapping.with_provider(ModelProvider.OPENROUTER)
        
        # Gemini Flash should map to OpenRouter's Google Flash
        assert remapped.recon.fallback == OPENROUTER_GEMINI_FLASH

    def test_openrouter_remaps_both_primary_and_fallback(self):
        """Test that OPENROUTER remaps both primary and fallback models."""
        mapping = LLMModelMapping()
        remapped = mapping.with_provider(ModelProvider.OPENROUTER)
        
        # Check that both are remapped
        assert remapped.decepticon.primary.startswith("openrouter/")
        assert remapped.decepticon.fallback is not None
        assert remapped.decepticon.fallback.startswith("openrouter/")
        assert remapped.exploit.primary.startswith("openrouter/")
        assert remapped.exploit.fallback is not None
        assert remapped.exploit.fallback.startswith("openrouter/")

    def test_openrouter_preserves_temperature(self):
        """Test that OPENROUTER preserves temperature settings."""
        mapping = LLMModelMapping()
        remapped = mapping.with_provider(ModelProvider.OPENROUTER)
        
        assert remapped.decepticon.temperature == 0.4
        assert remapped.exploit.temperature == 0.3
        assert remapped.recon.temperature == 0.3

    def test_openrouter_handles_already_remapped_models(self):
        """Test that OPENROUTER handles models already in OpenRouter format."""
        # Create a mapping with OpenRouter models
        mapping = LLMModelMapping(
            decepticon=ModelAssignment(
                primary=OPENROUTER_OPUS,
                fallback=OPENROUTER_GPT_5,
            )
        )
        remapped = mapping.with_provider(ModelProvider.OPENROUTER)
        
        # Should remain unchanged
        assert remapped.decepticon.primary == OPENROUTER_OPUS
        assert remapped.decepticon.fallback == OPENROUTER_GPT_5


class TestWithProviderHYBRID:
    """Tests for with_provider(ModelProvider.HYBRID) - mixed strategy."""

    def test_hybrid_keeps_anthropic_direct(self):
        """Test that HYBRID keeps Anthropic models on direct API."""
        mapping = LLMModelMapping()
        remapped = mapping.with_provider(ModelProvider.HYBRID)
        
        # Anthropic primaries should stay direct
        assert remapped.decepticon.primary == OPUS
        assert remapped.exploit.primary == SONNET
        assert remapped.recon.primary == HAIKU
        
        # Should NOT have openrouter/ prefix
        assert not remapped.decepticon.primary.startswith("openrouter/")
        assert not remapped.exploit.primary.startswith("openrouter/")
        assert not remapped.recon.primary.startswith("openrouter/")

    def test_hybrid_routes_non_anthropic_to_openrouter(self):
        """Test that HYBRID routes non-Anthropic models to OpenRouter."""
        mapping = LLMModelMapping()
        remapped = mapping.with_provider(ModelProvider.HYBRID)
        
        # Non-Anthropic fallbacks should be remapped
        assert remapped.decepticon.fallback == OPENROUTER_GPT_5
        assert remapped.exploit.fallback == OPENROUTER_GPT_4
        assert remapped.recon.fallback == OPENROUTER_GEMINI_FLASH

    def test_hybrid_preserves_anthropic_fallbacks(self):
        """Test that HYBRID preserves Anthropic fallbacks as direct."""
        mapping = LLMModelMapping()
        remapped = mapping.with_provider(ModelProvider.HYBRID)
        
        # Analyst has Anthropic fallback (Opus)
        assert remapped.analyst.primary == SONNET
        assert remapped.analyst.fallback == OPUS
        # Both should stay direct
        assert not remapped.analyst.primary.startswith("openrouter/")
        assert not remapped.analyst.fallback.startswith("openrouter/")

    def test_hybrid_mixed_strategy_example(self):
        """Test HYBRID strategy with a complete example."""
        mapping = LLMModelMapping()
        remapped = mapping.with_provider(ModelProvider.HYBRID)
        
        # Decepticon: Anthropic primary (direct) + OpenAI fallback (OpenRouter)
        assert remapped.decepticon.primary == OPUS
        assert remapped.decepticon.fallback == OPENROUTER_GPT_5
        
        # Exploit: Anthropic primary (direct) + OpenAI fallback (OpenRouter)
        assert remapped.exploit.primary == SONNET
        assert remapped.exploit.fallback == OPENROUTER_GPT_4
        
        # Recon: Anthropic primary (direct) + Gemini fallback (OpenRouter)
        assert remapped.recon.primary == HAIKU
        assert remapped.recon.fallback == OPENROUTER_GEMINI_FLASH

    def test_hybrid_preserves_temperature(self):
        """Test that HYBRID preserves temperature settings."""
        mapping = LLMModelMapping()
        remapped = mapping.with_provider(ModelProvider.HYBRID)
        
        assert remapped.decepticon.temperature == 0.4
        assert remapped.exploit.temperature == 0.3
        assert remapped.recon.temperature == 0.3


class TestProviderRemappingEdgeCases:
    """Tests for edge cases in provider remapping."""

    def test_invalid_provider_raises_error(self):
        """Test that invalid provider raises ValueError."""
        mapping = LLMModelMapping()
        with pytest.raises(ValueError, match="is not a valid ModelProvider"):
            mapping.with_provider("invalid_provider")

    def test_provider_from_string(self):
        """Test that provider can be specified as string."""
        mapping = LLMModelMapping()
        
        # Should work with string values
        remapped_api = mapping.with_provider("api")
        remapped_auth = mapping.with_provider("auth")
        remapped_openrouter = mapping.with_provider("openrouter")
        remapped_hybrid = mapping.with_provider("hybrid")
        
        assert remapped_api is mapping  # API is no-op
        assert remapped_auth.decepticon.primary.startswith("auth/")
        assert remapped_openrouter.decepticon.primary.startswith("openrouter/")
        assert remapped_hybrid.decepticon.primary == OPUS

    def test_chaining_providers_not_recommended(self):
        """Test that chaining providers works but may produce unexpected results."""
        mapping = LLMModelMapping()
        
        # Chain: API → AUTH → OPENROUTER
        remapped = mapping.with_provider("api").with_provider("auth").with_provider("openrouter")
        
        # Final result should be OpenRouter format
        assert remapped.decepticon.primary.startswith("openrouter/")

    def test_max_profile_with_openrouter(self):
        """Test that max profile works with OpenRouter provider."""
        mapping = LLMModelMapping.from_profile("max")
        remapped = mapping.with_provider(ModelProvider.OPENROUTER)
        
        # All should be remapped to OpenRouter
        assert remapped.decepticon.primary == OPENROUTER_OPUS
        assert remapped.exploit.primary == OPENROUTER_OPUS
        assert remapped.recon.primary == OPENROUTER_SONNET

    def test_test_profile_with_openrouter(self):
        """Test that test profile works with OpenRouter provider."""
        mapping = LLMModelMapping.from_profile("test")
        remapped = mapping.with_provider(ModelProvider.OPENROUTER)
        
        # All should be Haiku via OpenRouter
        assert remapped.decepticon.primary == OPENROUTER_HAIKU
        assert remapped.exploit.primary == OPENROUTER_HAIKU
        assert remapped.recon.primary == OPENROUTER_HAIKU
        
        # No fallbacks in test profile
        assert remapped.decepticon.fallback is None


class TestBackwardCompatibility:
    """Tests to ensure backward compatibility with existing code."""

    def test_default_mapping_unchanged(self):
        """Test that default mapping behavior is unchanged."""
        mapping = LLMModelMapping()
        
        # Default should still use direct API models
        assert mapping.decepticon.primary == OPUS
        assert mapping.exploit.primary == SONNET
        assert mapping.recon.primary == HAIKU

    def test_from_profile_unchanged(self):
        """Test that from_profile() behavior is unchanged."""
        eco = LLMModelMapping.from_profile("eco")
        max_profile = LLMModelMapping.from_profile("max")
        test = LLMModelMapping.from_profile("test")
        
        # Should still return direct API models by default
        assert eco.decepticon.primary == OPUS
        assert max_profile.decepticon.primary == OPUS
        assert test.decepticon.primary == HAIKU

    def test_api_provider_is_default(self):
        """Test that API provider is the default (no-op)."""
        mapping = LLMModelMapping()
        
        # with_provider("api") should be a no-op
        assert mapping.with_provider("api") is mapping

    def test_auth_provider_still_works(self):
        """Test that existing AUTH provider functionality is unchanged."""
        mapping = LLMModelMapping()
        remapped = mapping.with_provider("auth")
        
        # Should still remap Anthropic to auth/*
        assert remapped.decepticon.primary == "auth/claude-opus-4-6"
        assert remapped.decepticon.fallback == GPT_5  # Fallback unchanged


# Made with Bob