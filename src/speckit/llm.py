"""
LLM provider wrapper using LiteLLM for universal model support.

This module provides:
- LiteLLMProvider: Main class for LLM interactions
- LLMResponse: Standard response format
- Support for 100+ LLM providers via LiteLLM
- Automatic fallback chains
- Structured output via Instructor
"""

import time
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Iterator, Optional, Type, TypeVar

import litellm
from pydantic import BaseModel

from speckit.config import LLMConfig

# Enable verbose logging for debugging
litellm.set_verbose = False

T = TypeVar("T", bound=BaseModel)


@dataclass
class LLMResponse:
    """Standard response from LLM operations."""

    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    raw_response: Any = None

    @property
    def prompt_tokens(self) -> int:
        """Get prompt token count."""
        return self.usage.get("prompt_tokens", 0)

    @property
    def completion_tokens(self) -> int:
        """Get completion token count."""
        return self.usage.get("completion_tokens", 0)

    @property
    def total_tokens(self) -> int:
        """Get total token count."""
        return self.usage.get("total_tokens", 0)


class LiteLLMProvider:
    """
    Universal LLM provider using LiteLLM.

    Supports 100+ LLM providers including:
    - OpenAI (gpt-4, gpt-3.5-turbo, etc.)
    - Anthropic (claude-3-opus, claude-3-sonnet, etc.)
    - Google (gemini-pro, gemini-1.5-flash, etc.)
    - Local (ollama/*, llamacpp, etc.)
    - And many more via LiteLLM

    Example:
        >>> from speckit.llm import LiteLLMProvider
        >>> from speckit.config import LLMConfig
        >>>
        >>> provider = LiteLLMProvider(LLMConfig(model="gpt-4o-mini"))
        >>> response = provider.complete("Explain Python decorators")
        >>> print(response.content)
    """

    def __init__(self, config: LLMConfig):
        """
        Initialize the LLM provider.

        Args:
            config: LLM configuration with model, temperature, etc.
        """
        self.config = config
        self._instructor_client = None

    def _get_completion_kwargs(self, **overrides) -> dict[str, Any]:
        """Build kwargs for LiteLLM completion calls."""
        kwargs = {
            "model": self.config.model,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "timeout": self.config.timeout,
        }

        # Add API key if provided
        if self.config.api_key:
            kwargs["api_key"] = self.config.api_key

        # Add custom base URL if provided
        if self.config.api_base:
            kwargs["api_base"] = self.config.api_base

        # Apply overrides
        kwargs.update(overrides)
        return kwargs

    def complete(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        Generate a completion from the LLM.

        Args:
            prompt: The user prompt
            system: Optional system message
            **kwargs: Additional arguments passed to LiteLLM

        Returns:
            LLMResponse with the generated content

        Raises:
            Exception: On LLM errors after retries exhausted
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        completion_kwargs = self._get_completion_kwargs(**kwargs)
        completion_kwargs["messages"] = messages

        return self._complete_with_fallback(completion_kwargs)

    async def complete_async(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        Generate a completion asynchronously.

        Args:
            prompt: The user prompt
            system: Optional system message
            **kwargs: Additional arguments passed to LiteLLM

        Returns:
            LLMResponse with the generated content
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        completion_kwargs = self._get_completion_kwargs(**kwargs)
        completion_kwargs["messages"] = messages

        return await self._complete_with_fallback_async(completion_kwargs)

    def complete_structured(
        self,
        prompt: str,
        response_model: Type[T],
        system: Optional[str] = None,
        **kwargs,
    ) -> T:
        """
        Generate a structured output using Instructor.

        Args:
            prompt: The user prompt
            response_model: Pydantic model class for the response
            system: Optional system message
            **kwargs: Additional arguments passed to Instructor

        Returns:
            Instance of response_model with the generated data

        Example:
            >>> from pydantic import BaseModel
            >>> class UserStory(BaseModel):
            ...     as_a: str
            ...     i_want: str
            ...     so_that: str
            >>>
            >>> story = provider.complete_structured(
            ...     "Generate a user story for login",
            ...     response_model=UserStory
            ... )
            >>> print(story.as_a)
        """
        import instructor

        # Initialize instructor client if needed
        if self._instructor_client is None:
            self._instructor_client = instructor.from_litellm(litellm.completion)

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        completion_kwargs = self._get_completion_kwargs(**kwargs)
        completion_kwargs["messages"] = messages
        completion_kwargs["response_model"] = response_model

        return self._complete_structured_with_fallback(completion_kwargs, response_model)

    async def complete_structured_async(
        self,
        prompt: str,
        response_model: Type[T],
        system: Optional[str] = None,
        **kwargs,
    ) -> T:
        """
        Generate a structured output asynchronously using Instructor.

        Args:
            prompt: The user prompt
            response_model: Pydantic model class for the response
            system: Optional system message
            **kwargs: Additional arguments passed to Instructor

        Returns:
            Instance of response_model with the generated data
        """
        import instructor

        # Use async client
        client = instructor.from_litellm(litellm.acompletion)

        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        completion_kwargs = self._get_completion_kwargs(**kwargs)
        completion_kwargs["messages"] = messages
        completion_kwargs["response_model"] = response_model

        # Try with fallback models
        models_to_try = [self.config.model] + self.config.fallback_models
        last_error = None

        for model in models_to_try:
            try:
                completion_kwargs["model"] = model
                return await client.create(**completion_kwargs)
            except Exception as e:
                last_error = e
                continue

        raise last_error or Exception("All models failed")

    def stream(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs,
    ) -> Iterator[str]:
        """
        Stream a completion from the LLM.

        Args:
            prompt: The user prompt
            system: Optional system message
            **kwargs: Additional arguments passed to LiteLLM

        Yields:
            String chunks as they are generated

        Example:
            >>> for chunk in provider.stream("Write a poem"):
            ...     print(chunk, end="", flush=True)
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        completion_kwargs = self._get_completion_kwargs(**kwargs)
        completion_kwargs["messages"] = messages
        completion_kwargs["stream"] = True

        response = litellm.completion(**completion_kwargs)
        for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def stream_async(
        self,
        prompt: str,
        system: Optional[str] = None,
        **kwargs,
    ) -> AsyncIterator[str]:
        """
        Stream a completion asynchronously.

        Args:
            prompt: The user prompt
            system: Optional system message
            **kwargs: Additional arguments passed to LiteLLM

        Yields:
            String chunks as they are generated
        """
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        completion_kwargs = self._get_completion_kwargs(**kwargs)
        completion_kwargs["messages"] = messages
        completion_kwargs["stream"] = True

        response = await litellm.acompletion(**completion_kwargs)
        async for chunk in response:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    def _complete_with_fallback(self, kwargs: dict) -> LLMResponse:
        """
        Execute completion with automatic fallback to other models.

        Tries the primary model first, then falls back to configured
        fallback models on failure.
        """
        models_to_try = [self.config.model] + self.config.fallback_models
        last_error = None

        for attempt, model in enumerate(models_to_try):
            try:
                kwargs["model"] = model
                response = self._execute_with_retry(kwargs)
                return self._parse_response(response, model)
            except Exception as e:
                last_error = e
                # Continue to next model
                continue

        raise last_error or Exception("All models failed")

    async def _complete_with_fallback_async(self, kwargs: dict) -> LLMResponse:
        """Execute async completion with automatic fallback."""
        models_to_try = [self.config.model] + self.config.fallback_models
        last_error = None

        for model in models_to_try:
            try:
                kwargs["model"] = model
                response = await self._execute_with_retry_async(kwargs)
                return self._parse_response(response, model)
            except Exception as e:
                last_error = e
                continue

        raise last_error or Exception("All models failed")

    def _complete_structured_with_fallback(
        self,
        kwargs: dict,
        response_model: Type[T],
    ) -> T:
        """Execute structured completion with automatic fallback."""
        models_to_try = [self.config.model] + self.config.fallback_models
        last_error = None

        for model in models_to_try:
            try:
                kwargs["model"] = model
                return self._instructor_client.create(**kwargs)
            except Exception as e:
                last_error = e
                continue

        raise last_error or Exception("All models failed")

    def _execute_with_retry(self, kwargs: dict) -> Any:
        """Execute a completion with retry logic."""
        last_error = None

        for attempt in range(self.config.max_retries + 1):
            try:
                return litellm.completion(**kwargs)
            except litellm.RateLimitError as e:
                last_error = e
                if attempt < self.config.max_retries:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                raise
            except litellm.Timeout as e:
                last_error = e
                if attempt < self.config.max_retries:
                    continue
                raise
            except Exception as e:
                # Don't retry other errors
                raise

        raise last_error or Exception("Max retries exceeded")

    async def _execute_with_retry_async(self, kwargs: dict) -> Any:
        """Execute an async completion with retry logic."""
        import asyncio

        last_error = None

        for attempt in range(self.config.max_retries + 1):
            try:
                return await litellm.acompletion(**kwargs)
            except litellm.RateLimitError as e:
                last_error = e
                if attempt < self.config.max_retries:
                    wait_time = 2 ** attempt
                    await asyncio.sleep(wait_time)
                    continue
                raise
            except litellm.Timeout as e:
                last_error = e
                if attempt < self.config.max_retries:
                    continue
                raise
            except Exception as e:
                raise

        raise last_error or Exception("Max retries exceeded")

    def _parse_response(self, response: Any, model: str) -> LLMResponse:
        """Parse LiteLLM response into standard format."""
        content = response.choices[0].message.content or ""
        usage = {}

        if hasattr(response, "usage") and response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return LLMResponse(
            content=content,
            model=model,
            usage=usage,
            raw_response=response,
        )

    @staticmethod
    def list_models() -> list[str]:
        """
        List commonly available models.

        Returns a curated list of popular models. For the full list,
        see https://docs.litellm.ai/docs/providers

        Returns:
            List of model identifiers
        """
        return [
            # OpenAI
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
            # Anthropic
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-3-5-sonnet-20241022",
            # Google
            "gemini/gemini-1.5-pro",
            "gemini/gemini-1.5-flash",
            "gemini/gemini-pro",
            # Local (Ollama)
            "ollama/llama3.1",
            "ollama/llama3.1:70b",
            "ollama/mistral",
            "ollama/codellama",
            # Groq
            "groq/llama-3.1-70b-versatile",
            "groq/mixtral-8x7b-32768",
            # DeepSeek
            "deepseek/deepseek-chat",
            "deepseek/deepseek-coder",
            # Together AI
            "together_ai/meta-llama/Llama-3-70b-chat-hf",
            # Cohere
            "cohere/command-r-plus",
            "cohere/command-r",
        ]
