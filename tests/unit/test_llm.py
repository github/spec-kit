"""Unit tests for LiteLLMProvider."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from speckit.config import LLMConfig
from speckit.llm import LiteLLMProvider, LLMResponse


@pytest.fixture
def llm_config():
    """Create test LLM configuration."""
    return LLMConfig(
        model="gpt-4o-mini",
        temperature=0.7,
        max_tokens=4096,
        timeout=120,
        max_retries=2,
        fallback_models=["gpt-3.5-turbo"],
    )


@pytest.fixture
def provider(llm_config):
    """Create test provider."""
    return LiteLLMProvider(llm_config)


class TestLLMResponse:
    """Tests for LLMResponse dataclass."""

    def test_create_response(self):
        """Test creating an LLM response."""
        response = LLMResponse(
            content="Hello, world!",
            model="gpt-4o-mini",
            usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
        )
        assert response.content == "Hello, world!"
        assert response.model == "gpt-4o-mini"
        assert response.prompt_tokens == 10
        assert response.completion_tokens == 5
        assert response.total_tokens == 15

    def test_response_with_empty_usage(self):
        """Test response with empty usage dict."""
        response = LLMResponse(content="Test", model="test-model")
        assert response.prompt_tokens == 0
        assert response.completion_tokens == 0
        assert response.total_tokens == 0


class TestLiteLLMProvider:
    """Tests for LiteLLMProvider class."""

    def test_init(self, provider, llm_config):
        """Test provider initialization."""
        assert provider.config == llm_config
        assert provider._instructor_client is None

    def test_get_completion_kwargs(self, provider):
        """Test building completion kwargs."""
        kwargs = provider._get_completion_kwargs()
        assert kwargs["model"] == "gpt-4o-mini"
        assert kwargs["temperature"] == 0.7
        assert kwargs["max_tokens"] == 4096
        assert kwargs["timeout"] == 120

    def test_get_completion_kwargs_with_overrides(self, provider):
        """Test kwargs with overrides."""
        kwargs = provider._get_completion_kwargs(temperature=0.5, model="gpt-4")
        assert kwargs["temperature"] == 0.5
        assert kwargs["model"] == "gpt-4"

    def test_get_completion_kwargs_with_api_key(self):
        """Test kwargs includes API key when provided."""
        config = LLMConfig(model="gpt-4", api_key="test-key")
        provider = LiteLLMProvider(config)
        kwargs = provider._get_completion_kwargs()
        assert kwargs["api_key"] == "test-key"

    def test_get_completion_kwargs_with_api_base(self):
        """Test kwargs includes API base when provided."""
        config = LLMConfig(model="gpt-4", api_base="http://localhost:8000")
        provider = LiteLLMProvider(config)
        kwargs = provider._get_completion_kwargs()
        assert kwargs["api_base"] == "http://localhost:8000"

    @patch("speckit.llm.litellm.completion")
    def test_complete(self, mock_completion, provider):
        """Test basic completion."""
        # Mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        mock_completion.return_value = mock_response

        response = provider.complete("Hello")

        assert response.content == "Test response"
        assert response.model == "gpt-4o-mini"
        mock_completion.assert_called_once()

    @patch("speckit.llm.litellm.completion")
    def test_complete_with_system(self, mock_completion, provider):
        """Test completion with system message."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        mock_completion.return_value = mock_response

        provider.complete("Hello", system="You are helpful")

        call_kwargs = mock_completion.call_args[1]
        messages = call_kwargs["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"

    @patch("speckit.llm.litellm.completion")
    def test_complete_fallback_on_error(self, mock_completion, provider):
        """Test fallback to secondary model on error."""
        # First call fails, second succeeds
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Fallback response"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        mock_completion.side_effect = [
            Exception("Primary model failed"),
            mock_response,
        ]

        response = provider.complete("Hello")

        assert response.content == "Fallback response"
        assert response.model == "gpt-3.5-turbo"  # Fallback model
        assert mock_completion.call_count == 2

    @patch("speckit.llm.litellm.completion")
    def test_complete_all_models_fail(self, mock_completion, provider):
        """Test error when all models fail."""
        mock_completion.side_effect = Exception("All failed")

        with pytest.raises(Exception, match="All failed"):
            provider.complete("Hello")

    @pytest.mark.asyncio
    @patch("speckit.llm.litellm.acompletion")
    async def test_complete_async(self, mock_acompletion, provider):
        """Test async completion."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Async response"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15
        mock_acompletion.return_value = mock_response

        response = await provider.complete_async("Hello")

        assert response.content == "Async response"

    @patch("speckit.llm.litellm.completion")
    def test_stream(self, mock_completion, provider):
        """Test streaming completion."""
        # Create mock chunks
        chunks = []
        for text in ["Hello", " ", "world", "!"]:
            chunk = MagicMock()
            chunk.choices = [MagicMock()]
            chunk.choices[0].delta.content = text
            chunks.append(chunk)

        mock_completion.return_value = iter(chunks)

        result = "".join(provider.stream("Hi"))

        assert result == "Hello world!"

    def test_list_models(self):
        """Test listing available models."""
        models = LiteLLMProvider.list_models()

        assert isinstance(models, list)
        assert len(models) > 10
        assert "gpt-4o" in models
        assert "claude-3-opus-20240229" in models
        assert "ollama/llama3.1" in models

    def test_parse_response(self, provider):
        """Test response parsing."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        response = provider._parse_response(mock_response, "test-model")

        assert response.content == "Test"
        assert response.model == "test-model"
        assert response.usage["prompt_tokens"] == 10

    def test_parse_response_no_content(self, provider):
        """Test parsing response with no content."""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = None
        mock_response.usage = None

        response = provider._parse_response(mock_response, "test-model")

        assert response.content == ""
        assert response.usage == {}
