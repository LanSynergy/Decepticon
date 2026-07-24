"""Unit tests for model catalog module."""

import pytest

from decepticon.llm.catalog import (
    ModelInfo,
    compare_models,
    estimate_cost,
    get_model_info,
    list_available_models,
)
from decepticon.llm.models import ModelProvider


class TestModelInfo:
    """Tests for ModelInfo dataclass."""

    def test_model_info_creation(self):
        """Test creating a valid ModelInfo instance."""
        info = ModelInfo(
            id="test/model",
            name="Test Model",
            provider="Test",
            tier="tactical",
            context_length=100_000,
            cost_input=1.0,
            cost_output=5.0,
            description="Test description",
        )
        assert info.id == "test/model"
        assert info.name == "Test Model"
        assert info.provider == "Test"
        assert info.tier == "tactical"
        assert info.context_length == 100_000
        assert info.cost_input == 1.0
        assert info.cost_output == 5.0
        assert info.description == "Test description"

    def test_model_info_validation_negative_context(self):
        """Test that negative context_length raises ValueError."""
        with pytest.raises(ValueError, match="context_length must be positive"):
            ModelInfo(
                id="test/model",
                name="Test Model",
                provider="Test",
                tier="tactical",
                context_length=-1,
                cost_input=1.0,
                cost_output=5.0,
            )

    def test_model_info_validation_negative_cost_input(self):
        """Test that negative cost_input raises ValueError."""
        with pytest.raises(ValueError, match="cost_input must be non-negative"):
            ModelInfo(
                id="test/model",
                name="Test Model",
                provider="Test",
                tier="tactical",
                context_length=100_000,
                cost_input=-1.0,
                cost_output=5.0,
            )

    def test_model_info_validation_negative_cost_output(self):
        """Test that negative cost_output raises ValueError."""
        with pytest.raises(ValueError, match="cost_output must be non-negative"):
            ModelInfo(
                id="test/model",
                name="Test Model",
                provider="Test",
                tier="tactical",
                context_length=100_000,
                cost_input=1.0,
                cost_output=-5.0,
            )

    def test_model_info_zero_cost_allowed(self):
        """Test that zero cost is allowed (for local models)."""
        info = ModelInfo(
            id="ollama/llama3.2",
            name="Local Model",
            provider="Ollama",
            tier="budget",
            context_length=128_000,
            cost_input=0.0,
            cost_output=0.0,
        )
        assert info.cost_input == 0.0
        assert info.cost_output == 0.0


class TestGetModelInfo:
    """Tests for get_model_info function."""

    def test_get_model_info_anthropic_opus(self):
        """Test getting info for Claude Opus."""
        info = get_model_info("anthropic/claude-opus-4-6")
        assert info.id == "anthropic/claude-opus-4-6"
        assert info.name == "Claude Opus 4.6"
        assert info.provider == "Anthropic"
        assert info.tier == "strategic"
        assert info.context_length == 200_000
        assert info.cost_input == 5.0
        assert info.cost_output == 25.0

    def test_get_model_info_openrouter_opus(self):
        """Test getting info for Claude Opus via OpenRouter."""
        info = get_model_info("openrouter/anthropic/claude-opus-4-6")
        assert info.id == "openrouter/anthropic/claude-opus-4-6"
        assert info.name == "Claude Opus 4.6 (OpenRouter)"
        assert info.provider == "Anthropic"
        assert info.tier == "strategic"
        # OpenRouter should be ~10% cheaper
        assert info.cost_input == 4.5
        assert info.cost_output == 22.5

    def test_get_model_info_llama_405b(self):
        """Test getting info for Llama 3.1 405B."""
        info = get_model_info("openrouter/meta-llama/llama-3.1-405b-instruct")
        assert info.provider == "Meta"
        assert info.tier == "strategic"
        assert info.context_length == 128_000
        # Llama should be cheaper than proprietary models
        assert info.cost_input < 5.0

    def test_get_model_info_not_found(self):
        """Test that KeyError is raised for unknown model."""
        with pytest.raises(KeyError, match="Model 'nonexistent/model' not found"):
            get_model_info("nonexistent/model")

    def test_get_model_info_all_required_fields(self):
        """Test that all models have required fields."""
        # Test a few representative models
        models_to_test = [
            "anthropic/claude-opus-4-6",
            "openrouter/anthropic/claude-haiku-4-5",
            "openrouter/meta-llama/llama-3.1-70b-instruct",
            "openrouter/mistralai/mistral-large",
            "gemini/gemini-2.5-flash",
        ]
        for model_id in models_to_test:
            info = get_model_info(model_id)
            assert info.id is not None
            assert info.name is not None
            assert info.provider is not None
            assert info.tier in ["strategic", "precision", "tactical", "budget"]
            assert info.context_length > 0
            assert info.cost_input >= 0
            assert info.cost_output >= 0


class TestListAvailableModels:
    """Tests for list_available_models function."""

    def test_list_all_models(self):
        """Test listing all models without filters."""
        models = list_available_models()
        assert len(models) > 0
        # Should have at least the 15 OpenRouter models + direct API models
        assert len(models) >= 15

    def test_list_models_by_openrouter_provider(self):
        """Test filtering by OpenRouter provider enum."""
        models = list_available_models(provider=ModelProvider.OPENROUTER)
        assert len(models) > 0
        # All should have openrouter/ prefix
        for model in models:
            assert model.id.startswith("openrouter/")

    def test_list_models_by_api_provider(self):
        """Test filtering by API provider enum (direct models)."""
        models = list_available_models(provider=ModelProvider.API)
        assert len(models) > 0
        # None should have openrouter/ prefix
        for model in models:
            assert not model.id.startswith("openrouter/")

    def test_list_models_by_provider_name_anthropic(self):
        """Test filtering by provider name (Anthropic)."""
        models = list_available_models(provider="Anthropic")
        assert len(models) > 0
        # All should be Anthropic models
        for model in models:
            assert model.provider == "Anthropic"
        # Should include both direct and OpenRouter variants
        ids = [m.id for m in models]
        assert "anthropic/claude-opus-4-6" in ids
        assert "openrouter/anthropic/claude-opus-4-6" in ids

    def test_list_models_by_provider_name_meta(self):
        """Test filtering by provider name (Meta)."""
        models = list_available_models(provider="Meta")
        assert len(models) > 0
        # All should be Meta models
        for model in models:
            assert model.provider == "Meta"
        # Should have Llama models
        ids = [m.id for m in models]
        assert "openrouter/meta-llama/llama-3.1-405b-instruct" in ids
        assert "openrouter/meta-llama/llama-3.1-70b-instruct" in ids
        assert "openrouter/meta-llama/llama-3.1-8b-instruct" in ids

    def test_list_models_by_tier_strategic(self):
        """Test filtering by strategic tier."""
        models = list_available_models(tier="strategic")
        assert len(models) > 0
        # All should be strategic tier
        for model in models:
            assert model.tier == "strategic"
        # Should include Opus, GPT-5, Llama 405B
        ids = [m.id for m in models]
        assert "anthropic/claude-opus-4-6" in ids
        assert "openai/gpt-5.4" in ids
        assert "openrouter/meta-llama/llama-3.1-405b-instruct" in ids

    def test_list_models_by_tier_budget(self):
        """Test filtering by budget tier."""
        models = list_available_models(tier="budget")
        assert len(models) > 0
        # All should be budget tier
        for model in models:
            assert model.tier == "budget"
        # Should include smaller Llama models, Mixtral
        ids = [m.id for m in models]
        assert "openrouter/meta-llama/llama-3.1-70b-instruct" in ids
        assert "openrouter/mistralai/mixtral-8x7b-instruct" in ids

    def test_list_models_combined_filters(self):
        """Test combining provider and tier filters."""
        models = list_available_models(
            provider=ModelProvider.OPENROUTER,
            tier="strategic",
        )
        assert len(models) > 0
        # All should be OpenRouter strategic models
        for model in models:
            assert model.id.startswith("openrouter/")
            assert model.tier == "strategic"

    def test_list_models_sorted_by_cost(self):
        """Test that models are sorted by cost (cheapest first)."""
        models = list_available_models()
        # Check that total cost is non-decreasing
        for i in range(len(models) - 1):
            cost1 = models[i].cost_input + models[i].cost_output
            cost2 = models[i + 1].cost_input + models[i + 1].cost_output
            assert cost1 <= cost2


class TestCompareModels:
    """Tests for compare_models function."""

    def test_compare_opus_vs_llama_405b(self):
        """Test comparing Claude Opus with Llama 405B."""
        comparison = compare_models(
            "openrouter/anthropic/claude-opus-4-6",
            "openrouter/meta-llama/llama-3.1-405b-instruct",
        )
        
        # Check structure
        assert "model1" in comparison
        assert "model2" in comparison
        assert "differences" in comparison
        assert "recommendation" in comparison
        
        # Check model1 data
        assert comparison["model1"]["id"] == "openrouter/anthropic/claude-opus-4-6"
        assert comparison["model1"]["name"] == "Claude Opus 4.6 (OpenRouter)"
        assert comparison["model1"]["tier"] == "strategic"
        
        # Check model2 data
        assert comparison["model2"]["id"] == "openrouter/meta-llama/llama-3.1-405b-instruct"
        assert comparison["model2"]["provider"] == "Meta"
        
        # Check differences
        assert "input_cost_diff" in comparison["differences"]
        assert "output_cost_diff" in comparison["differences"]
        assert "total_cost_diff" in comparison["differences"]
        assert "context_length_diff" in comparison["differences"]

    def test_compare_haiku_vs_gemini_flash(self):
        """Test comparing tactical tier models."""
        comparison = compare_models(
            "anthropic/claude-haiku-4-5",
            "gemini/gemini-2.5-flash",
        )
        
        # Both are tactical tier
        assert comparison["model1"]["tier"] == "tactical"
        assert comparison["model2"]["tier"] == "tactical"
        
        # Gemini has much larger context
        assert comparison["differences"]["context_length_diff"] < 0  # Haiku smaller

    def test_compare_models_not_found(self):
        """Test that KeyError is raised for unknown models."""
        with pytest.raises(KeyError):
            compare_models("nonexistent/model1", "anthropic/claude-opus-4-6")
        
        with pytest.raises(KeyError):
            compare_models("anthropic/claude-opus-4-6", "nonexistent/model2")

    def test_compare_models_cost_difference_calculation(self):
        """Test that cost differences are calculated correctly."""
        comparison = compare_models(
            "anthropic/claude-opus-4-6",  # $5 input, $25 output
            "anthropic/claude-haiku-4-5",  # $1 input, $5 output
        )
        
        # Opus should be more expensive
        assert comparison["differences"]["input_cost_diff"] == 4.0  # 5 - 1
        assert comparison["differences"]["output_cost_diff"] == 20.0  # 25 - 5
        assert comparison["differences"]["total_cost_diff"] == 24.0  # 30 - 6

    def test_compare_models_percentage_calculation(self):
        """Test that percentage differences are calculated."""
        comparison = compare_models(
            "anthropic/claude-opus-4-6",
            "anthropic/claude-haiku-4-5",
        )
        
        # Should have percentage differences
        assert "input_cost_pct" in comparison["differences"]
        assert "output_cost_pct" in comparison["differences"]
        # Opus is 400% more expensive on input (5 vs 1)
        assert comparison["differences"]["input_cost_pct"] == pytest.approx(400.0, rel=0.1)

    def test_compare_models_recommendation_exists(self):
        """Test that recommendation is generated."""
        comparison = compare_models(
            "openrouter/anthropic/claude-opus-4-6",
            "openrouter/meta-llama/llama-3.1-70b-instruct",
        )
        
        assert isinstance(comparison["recommendation"], str)
        assert len(comparison["recommendation"]) > 0


class TestEstimateCost:
    """Tests for estimate_cost function."""

    def test_estimate_cost_basic(self):
        """Test basic cost estimation."""
        estimate = estimate_cost(
            "anthropic/claude-opus-4-6",
            input_tokens=10_000,
            output_tokens=5_000,
        )
        
        assert estimate.model_name == "anthropic/claude-opus-4-6"
        assert estimate.input_tokens == 10_000
        assert estimate.output_tokens == 5_000
        # $5 per 1M input tokens = $0.05 for 10K
        assert estimate.input_cost == pytest.approx(0.05, rel=0.01)
        # $25 per 1M output tokens = $0.125 for 5K
        assert estimate.output_cost == pytest.approx(0.125, rel=0.01)
        # Total = $0.175
        assert estimate.total_cost == pytest.approx(0.175, rel=0.01)

    def test_estimate_cost_large_usage(self):
        """Test cost estimation for large token usage."""
        estimate = estimate_cost(
            "openrouter/meta-llama/llama-3.1-70b-instruct",
            input_tokens=1_000_000,  # 1M tokens
            output_tokens=1_000_000,  # 1M tokens
        )
        
        # Llama 70B: $0.59 input, $0.79 output per 1M
        assert estimate.input_cost == pytest.approx(0.59, rel=0.01)
        assert estimate.output_cost == pytest.approx(0.79, rel=0.01)
        assert estimate.total_cost == pytest.approx(1.38, rel=0.01)

    def test_estimate_cost_zero_cost_model(self):
        """Test cost estimation for local model with zero cost."""
        estimate = estimate_cost(
            "ollama/llama3.2",
            input_tokens=100_000,
            output_tokens=50_000,
        )
        
        assert estimate.input_cost == 0.0
        assert estimate.output_cost == 0.0
        assert estimate.total_cost == 0.0

    def test_estimate_cost_model_not_found(self):
        """Test that KeyError is raised for unknown model."""
        with pytest.raises(KeyError):
            estimate_cost("nonexistent/model", 1000, 1000)


class TestCatalogCompleteness:
    """Tests to ensure catalog has all expected models."""

    def test_catalog_has_all_openrouter_models(self):
        """Test that catalog includes all 15 OpenRouter models from Week 1."""
        expected_openrouter_models = [
            "openrouter/anthropic/claude-opus-4-6",
            "openrouter/anthropic/claude-sonnet-4-6",
            "openrouter/anthropic/claude-haiku-4-5",
            "openrouter/openai/gpt-5.4",
            "openrouter/openai/gpt-4.1",
            "openrouter/openai/gpt-4o",
            "openrouter/google/gemini-pro-1.5",
            "openrouter/google/gemini-flash-1.5",
            "openrouter/meta-llama/llama-3.1-405b-instruct",
            "openrouter/meta-llama/llama-3.1-70b-instruct",
            "openrouter/meta-llama/llama-3.1-8b-instruct",
            "openrouter/mistralai/mistral-large",
            "openrouter/mistralai/mistral-medium",
            "openrouter/mistralai/mixtral-8x7b-instruct",
            "openrouter/cohere/command-r-plus",
        ]
        
        for model_id in expected_openrouter_models:
            info = get_model_info(model_id)
            assert info is not None
            assert info.id == model_id

    def test_catalog_has_direct_api_models(self):
        """Test that catalog includes direct API models."""
        expected_direct_models = [
            "anthropic/claude-opus-4-6",
            "anthropic/claude-sonnet-4-6",
            "anthropic/claude-haiku-4-5",
            "openai/gpt-5.4",
            "openai/gpt-4.1",
            "gemini/gemini-2.5-flash",
        ]
        
        for model_id in expected_direct_models:
            info = get_model_info(model_id)
            assert info is not None
            assert not info.id.startswith("openrouter/")

    def test_all_models_have_valid_tiers(self):
        """Test that all models have valid tier assignments."""
        valid_tiers = {"strategic", "precision", "tactical", "budget"}
        models = list_available_models()
        
        for model in models:
            assert model.tier in valid_tiers

    def test_all_models_have_positive_context_length(self):
        """Test that all models have positive context lengths."""
        models = list_available_models()
        
        for model in models:
            assert model.context_length > 0

    def test_openrouter_models_cheaper_than_direct(self):
        """Test that OpenRouter models are cheaper than direct API equivalents."""
        # Compare Anthropic models
        direct_opus = get_model_info("anthropic/claude-opus-4-6")
        openrouter_opus = get_model_info("openrouter/anthropic/claude-opus-4-6")
        
        # OpenRouter should be ~10% cheaper
        assert openrouter_opus.cost_input < direct_opus.cost_input
        assert openrouter_opus.cost_output < direct_opus.cost_output

# Made with Bob
