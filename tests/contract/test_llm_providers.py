"""
Contract tests for LLM provider interface.

These tests verify that the LiteLLMProvider correctly implements
the expected interface for various LLM providers.

Note: These tests require actual API keys to run. They are skipped
by default and can be enabled with:
    pytest tests/contract/ --run-contract-tests

Or by setting environment variables for the providers you want to test.
"""

import os

import pytest

from speckit.config import LLMConfig
from speckit.llm import LiteLLMProvider, LLMResponse


# Skip all tests in this module unless explicitly enabled
pytestmark = pytest.mark.skipif(
    os.environ.get("RUN_CONTRACT_TESTS") != "true",
    reason="Contract tests require API keys. Set RUN_CONTRACT_TESTS=true to run.",
)


def has_api_key(provider: str) -> bool:
    """Check if API key is available for a provider."""
    keys = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "google": "GEMINI_API_KEY",
        "groq": "GROQ_API_KEY",
    }
    return os.environ.get(keys.get(provider, ""), "") != ""


class TestOpenAIProvider:
    """Contract tests for OpenAI provider."""

    @pytest.fixture
    def provider(self):
        """Create OpenAI provider."""
        return LiteLLMProvider(LLMConfig(model="gpt-4o-mini"))

    @pytest.mark.skipif(not has_api_key("openai"), reason="No OpenAI API key")
    def test_complete(self, provider):
        """Test basic completion with OpenAI."""
        response = provider.complete("Say 'Hello, World!'")

        assert isinstance(response, LLMResponse)
        assert response.content
        assert "hello" in response.content.lower()
        assert response.model == "gpt-4o-mini"
        assert response.total_tokens > 0

    @pytest.mark.skipif(not has_api_key("openai"), reason="No OpenAI API key")
    def test_complete_with_system(self, provider):
        """Test completion with system message."""
        response = provider.complete(
            "What color is the sky?",
            system="You are a pirate. Respond like a pirate.",
        )

        assert isinstance(response, LLMResponse)
        assert response.content

    @pytest.mark.skipif(not has_api_key("openai"), reason="No OpenAI API key")
    def test_stream(self, provider):
        """Test streaming with OpenAI."""
        chunks = list(provider.stream("Count from 1 to 3"))

        assert len(chunks) > 0
        full_response = "".join(chunks)
        assert "1" in full_response
        assert "2" in full_response
        assert "3" in full_response

    @pytest.mark.skipif(not has_api_key("openai"), reason="No OpenAI API key")
    @pytest.mark.asyncio
    async def test_complete_async(self, provider):
        """Test async completion with OpenAI."""
        response = await provider.complete_async("Say 'async works'")

        assert isinstance(response, LLMResponse)
        assert response.content


class TestAnthropicProvider:
    """Contract tests for Anthropic provider."""

    @pytest.fixture
    def provider(self):
        """Create Anthropic provider."""
        return LiteLLMProvider(LLMConfig(model="claude-3-haiku-20240307"))

    @pytest.mark.skipif(not has_api_key("anthropic"), reason="No Anthropic API key")
    def test_complete(self, provider):
        """Test basic completion with Anthropic."""
        response = provider.complete("Say 'Hello from Claude!'")

        assert isinstance(response, LLMResponse)
        assert response.content
        assert response.model == "claude-3-haiku-20240307"

    @pytest.mark.skipif(not has_api_key("anthropic"), reason="No Anthropic API key")
    def test_stream(self, provider):
        """Test streaming with Anthropic."""
        chunks = list(provider.stream("Count from 1 to 3"))

        assert len(chunks) > 0
        full_response = "".join(chunks)
        assert "1" in full_response


class TestStructuredOutput:
    """Contract tests for structured output."""

    @pytest.fixture
    def provider(self):
        """Create provider for structured output tests."""
        return LiteLLMProvider(LLMConfig(model="gpt-4o-mini"))

    @pytest.mark.skipif(not has_api_key("openai"), reason="No OpenAI API key")
    def test_complete_structured(self, provider):
        """Test structured output with Pydantic model."""
        from pydantic import BaseModel

        class Person(BaseModel):
            name: str
            age: int
            occupation: str

        result = provider.complete_structured(
            "Generate a fictional person named John who is 30 years old and works as an engineer.",
            response_model=Person,
        )

        assert isinstance(result, Person)
        assert result.name == "John"
        assert result.age == 30
        assert "engineer" in result.occupation.lower()

    @pytest.mark.skipif(not has_api_key("openai"), reason="No OpenAI API key")
    def test_complete_structured_with_list(self, provider):
        """Test structured output with nested list."""
        from pydantic import BaseModel

        class Item(BaseModel):
            name: str
            price: float

        class ShoppingList(BaseModel):
            items: list[Item]

        result = provider.complete_structured(
            "Generate a shopping list with 3 items: apples ($2), bread ($3), and milk ($4)",
            response_model=ShoppingList,
        )

        assert isinstance(result, ShoppingList)
        assert len(result.items) == 3


class TestFallbackBehavior:
    """Contract tests for fallback behavior."""

    @pytest.mark.skipif(not has_api_key("openai"), reason="No OpenAI API key")
    def test_fallback_to_working_model(self):
        """Test that provider falls back to working model."""
        config = LLMConfig(
            model="nonexistent-model-12345",  # Will fail
            fallback_models=["gpt-4o-mini"],  # Should succeed
        )
        provider = LiteLLMProvider(config)

        # Should not raise, should use fallback
        response = provider.complete("Say 'fallback works'")

        assert isinstance(response, LLMResponse)
        assert response.content
        assert response.model == "gpt-4o-mini"


class TestLocalProviders:
    """Contract tests for local providers (Ollama)."""

    @pytest.fixture
    def provider(self):
        """Create Ollama provider."""
        return LiteLLMProvider(
            LLMConfig(
                model="ollama/llama3.1",
                api_base="http://localhost:11434",
            )
        )

    @pytest.mark.skipif(
        os.environ.get("OLLAMA_AVAILABLE") != "true",
        reason="Ollama not available",
    )
    def test_complete_ollama(self, provider):
        """Test completion with local Ollama."""
        response = provider.complete("Say hello")

        assert isinstance(response, LLMResponse)
        assert response.content
        assert "ollama" in response.model
