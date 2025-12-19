# LiteLLM Best Practices for Multi-Provider Python Libraries

**Created**: 2025-12-19
**Purpose**: Research findings on LiteLLM best practices for building production-grade Python libraries supporting 100+ LLM providers

## Table of Contents
1. [Fallback Chain Configuration](#1-fallback-chain-configuration)
2. [Retry Logic and Error Handling](#2-retry-logic-and-error-handling)
3. [Instructor Integration for Structured Outputs](#3-instructor-integration-for-structured-outputs)
4. [Provider Authentication Methods](#4-provider-authentication-methods)
5. [Streaming Support Patterns](#5-streaming-support-patterns)

---

## 1. Fallback Chain Configuration

### Overview
LiteLLM provides built-in fallback mechanisms that automatically switch between models/providers when requests fail. This is critical for production resilience.

### Basic Fallback Pattern

```python
import litellm
from litellm import completion

# Simple fallback list - LiteLLM tries each in order
def completion_with_fallbacks(messages, **kwargs):
    """
    LiteLLM automatically handles fallbacks when using fallbacks parameter
    """
    response = completion(
        model="gpt-4",
        messages=messages,
        fallbacks=["claude-3-5-sonnet-20241022", "gpt-3.5-turbo"],
        **kwargs
    )
    return response
```

### Advanced Fallback Configuration

```python
import litellm
from litellm import Router
from typing import List, Dict, Any

class LLMProviderManager:
    """
    Production-grade provider manager with sophisticated fallback chains
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize router with model groups and fallback strategy

        Args:
            config: Configuration dict with model_list and routing settings
        """
        # Define model list with priorities and capabilities
        model_list = [
            {
                "model_name": "primary-gpt4",  # Alias for routing
                "litellm_params": {
                    "model": "gpt-4-turbo-preview",
                    "api_key": config.get("openai_api_key"),
                    "timeout": 600,
                    "max_retries": 2,
                },
                "model_info": {
                    "priority": 1,  # Higher priority = tried first
                    "max_tokens": 128000,
                    "supports_vision": True,
                }
            },
            {
                "model_name": "primary-claude",
                "litellm_params": {
                    "model": "claude-3-5-sonnet-20241022",
                    "api_key": config.get("anthropic_api_key"),
                    "timeout": 600,
                    "max_retries": 2,
                },
                "model_info": {
                    "priority": 1,
                    "max_tokens": 200000,
                    "supports_vision": True,
                }
            },
            {
                "model_name": "fallback-local",
                "litellm_params": {
                    "model": "ollama/llama3.1:8b",
                    "api_base": config.get("ollama_base_url", "http://localhost:11434"),
                    "timeout": 300,
                },
                "model_info": {
                    "priority": 2,  # Lower priority = fallback
                    "max_tokens": 8192,
                    "supports_vision": False,
                }
            },
            {
                "model_name": "cost-effective",
                "litellm_params": {
                    "model": "gpt-3.5-turbo",
                    "api_key": config.get("openai_api_key"),
                    "timeout": 300,
                },
                "model_info": {
                    "priority": 3,
                    "max_tokens": 16385,
                }
            }
        ]

        # Initialize Router with fallback configuration
        self.router = Router(
            model_list=model_list,
            # Routing strategy: "simple-shuffle" tries all models at same priority
            routing_strategy="priority",  # Respects priority field
            retry_after=10,  # Wait 10s before retrying failed provider
            num_retries=2,  # Retry count per model
            timeout=600,  # Global timeout
            fallbacks=[
                # Define explicit fallback chains by model group
                {
                    "primary-gpt4": ["primary-claude", "fallback-local", "cost-effective"]
                },
                {
                    "primary-claude": ["primary-gpt4", "fallback-local", "cost-effective"]
                }
            ],
            # Set context window fallback behavior
            context_window_fallbacks=[
                # If input exceeds model's context, try these
                {"primary-gpt4": ["primary-claude"]},  # Claude has larger context
            ],
            # Enable automatic fallback on specific errors
            allowed_fails=2,  # Number of failures before circuit breaker activates
        )

    async def complete(
        self,
        messages: List[Dict[str, str]],
        model: str = "primary-gpt4",
        **kwargs
    ):
        """
        Execute completion with automatic fallbacks

        The router handles:
        - Rate limit errors (429) → automatic retry after delay
        - Context window errors → fallback to models with larger context
        - Provider unavailability (500, 503) → try next model in chain
        - Timeout errors → try faster/local models
        """
        try:
            response = await self.router.acompletion(
                model=model,
                messages=messages,
                **kwargs
            )
            return response
        except Exception as e:
            # Router exhausted all fallbacks
            raise LLMProviderError(f"All providers failed: {e}")

# Usage example
config = {
    "openai_api_key": "sk-...",
    "anthropic_api_key": "sk-ant-...",
    "ollama_base_url": "http://localhost:11434"
}

provider = LLMProviderManager(config)
response = await provider.complete(
    messages=[{"role": "user", "content": "Hello"}],
    model="primary-gpt4"
)
```

### Best Practices for Fallback Chains

1. **Prioritize by Capability**: Order models by quality/features, not just cost
2. **Include Local Fallback**: Always have an offline option (Ollama) as final fallback
3. **Group Similar Models**: Create aliases for model groups (e.g., "high-quality", "fast", "cost-effective")
4. **Context-Aware Fallbacks**: Use `context_window_fallbacks` for handling large inputs
5. **Circuit Breaker Pattern**: Use `allowed_fails` to prevent cascade failures
6. **Monitor Fallback Usage**: Log when fallbacks are triggered to identify pattern issues

### Configuration Schema

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict

class ModelConfig(BaseModel):
    """Configuration for a single model in fallback chain"""
    model_name: str = Field(..., description="Alias for routing")
    provider: str = Field(..., description="Provider name (openai, anthropic, etc)")
    model: str = Field(..., description="Actual model identifier")
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    priority: int = Field(default=5, ge=1, le=10)
    max_tokens: int = Field(default=4096)
    timeout: int = Field(default=600)
    max_retries: int = Field(default=2)
    supports_streaming: bool = Field(default=True)
    supports_vision: bool = Field(default=False)
    supports_function_calling: bool = Field(default=True)

class FallbackConfig(BaseModel):
    """Fallback chain configuration"""
    primary_model: str
    fallback_models: List[str]
    enabled: bool = True
    retry_delay: int = Field(default=10, description="Seconds between retries")

class LLMConfig(BaseModel):
    """Complete LLM configuration with fallbacks"""
    models: List[ModelConfig]
    fallback_chains: List[FallbackConfig]
    routing_strategy: str = Field(default="priority", pattern="^(priority|simple-shuffle|usage-based)$")
    global_timeout: int = Field(default=600)
    allowed_fails: int = Field(default=2)
```

---

## 2. Retry Logic and Error Handling

### Built-in Retry Mechanisms

LiteLLM provides automatic retries with exponential backoff for transient failures.

```python
import litellm
from litellm import completion
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
import logging

# Configure LiteLLM logging
litellm.set_verbose = True  # Enable detailed logging
litellm.suppress_debug_info = False

class LLMErrorHandler:
    """
    Comprehensive error handling for LiteLLM operations
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        # Configure LiteLLM's built-in retry behavior
        litellm.num_retries = 3  # Global retry count
        litellm.retry_after = 10  # Seconds to wait between retries

    def completion_with_retries(self, messages, model="gpt-4", **kwargs):
        """
        Use LiteLLM's built-in retry mechanism

        LiteLLM automatically retries on:
        - Rate limit errors (429)
        - Server errors (500, 502, 503, 504)
        - Timeout errors
        - Connection errors
        """
        try:
            response = completion(
                model=model,
                messages=messages,
                num_retries=3,  # Per-request override
                **kwargs
            )
            return response

        except litellm.exceptions.RateLimitError as e:
            # Provider rate limit exceeded - all retries exhausted
            self.logger.error(f"Rate limit exceeded: {e}")
            raise

        except litellm.exceptions.ContextWindowExceededError as e:
            # Input exceeds model's context window
            self.logger.error(f"Context window exceeded: {e}")
            # Try with a model that has larger context
            return self.completion_with_retries(
                messages,
                model="claude-3-5-sonnet-20241022",  # Has 200k context
                **kwargs
            )

        except litellm.exceptions.ContentPolicyViolationError as e:
            # Content filtered by provider
            self.logger.error(f"Content policy violation: {e}")
            raise  # Don't retry - fix content instead

        except litellm.exceptions.APIConnectionError as e:
            # Network/connection issue
            self.logger.error(f"API connection error: {e}")
            raise

        except litellm.exceptions.APIError as e:
            # General API error
            self.logger.error(f"API error: {e}")
            raise

        except litellm.exceptions.Timeout as e:
            # Request timeout
            self.logger.error(f"Request timeout: {e}")
            raise

        except Exception as e:
            # Unexpected error
            self.logger.error(f"Unexpected error: {e}", exc_info=True)
            raise

### Advanced Retry with Tenacity

# For more control, combine LiteLLM with Tenacity
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

class AdvancedLLMClient:
    """
    Production-grade LLM client with sophisticated retry logic
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @retry(
        # Retry up to 5 times
        stop=stop_after_attempt(5),
        # Exponential backoff: 2^n seconds (2, 4, 8, 16, 32)
        wait=wait_exponential(multiplier=2, min=2, max=60),
        # Only retry on specific exceptions
        retry=retry_if_exception_type((
            litellm.exceptions.RateLimitError,
            litellm.exceptions.APIConnectionError,
            litellm.exceptions.Timeout,
        )),
        # Log before sleeping
        before_sleep=before_sleep_log(logging.getLogger(__name__), logging.WARNING),
        reraise=True
    )
    async def completion_with_advanced_retry(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4",
        **kwargs
    ):
        """
        Completion with Tenacity retry logic

        Tenacity provides:
        - Exponential backoff
        - Configurable retry conditions
        - Retry statistics
        - Before/after retry callbacks
        """
        try:
            response = await litellm.acompletion(
                model=model,
                messages=messages,
                **kwargs
            )
            return response
        except Exception as e:
            self.logger.error(f"Completion failed: {e}")
            raise

### Error Classification and Recovery

class ErrorRecoveryStrategy:
    """
    Intelligent error recovery based on error type
    """

    def __init__(self, router: Router):
        self.router = router
        self.logger = logging.getLogger(__name__)

    async def execute_with_recovery(
        self,
        messages: List[Dict[str, str]],
        model: str,
        **kwargs
    ):
        """
        Execute with error-specific recovery strategies
        """
        max_attempts = 3
        attempt = 0
        last_error = None

        while attempt < max_attempts:
            try:
                response = await self.router.acompletion(
                    model=model,
                    messages=messages,
                    **kwargs
                )
                return response

            except litellm.exceptions.ContextWindowExceededError as e:
                # Strategy: Truncate input or switch to larger context model
                self.logger.warning(f"Context exceeded, trying recovery strategy {attempt + 1}")

                if attempt == 0:
                    # First attempt: Try to truncate messages
                    messages = self._truncate_messages(messages, target_tokens=100000)
                elif attempt == 1:
                    # Second attempt: Switch to model with larger context
                    model = self._get_larger_context_model(model)
                else:
                    raise

                attempt += 1
                last_error = e

            except litellm.exceptions.RateLimitError as e:
                # Strategy: Exponential backoff + switch provider
                self.logger.warning(f"Rate limited, attempt {attempt + 1}/{max_attempts}")

                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)

                if attempt >= 1:
                    # Switch to different provider after first retry
                    model = self._get_alternative_provider(model)

                attempt += 1
                last_error = e

            except litellm.exceptions.ContentPolicyViolationError as e:
                # No retry - this requires content modification
                self.logger.error("Content policy violation - cannot auto-recover")
                raise

            except (
                litellm.exceptions.APIConnectionError,
                litellm.exceptions.Timeout
            ) as e:
                # Strategy: Retry with exponential backoff
                self.logger.warning(f"Connection/timeout error, attempt {attempt + 1}/{max_attempts}")

                wait_time = 2 ** attempt
                await asyncio.sleep(wait_time)

                attempt += 1
                last_error = e

            except Exception as e:
                # Unknown error - log and raise
                self.logger.error(f"Unexpected error: {e}", exc_info=True)
                raise

        # All retries exhausted
        raise LLMProviderError(f"All retry attempts failed: {last_error}")

    def _truncate_messages(
        self,
        messages: List[Dict[str, str]],
        target_tokens: int
    ) -> List[Dict[str, str]]:
        """Intelligently truncate message history"""
        # Keep system message and recent messages
        system_msgs = [m for m in messages if m["role"] == "system"]
        other_msgs = [m for m in messages if m["role"] != "system"]

        # Estimate tokens (rough: 4 chars = 1 token)
        total_chars = sum(len(m["content"]) for m in other_msgs)
        target_chars = target_tokens * 4

        if total_chars <= target_chars:
            return messages

        # Keep recent messages up to target
        truncated = []
        char_count = 0
        for msg in reversed(other_msgs):
            msg_chars = len(msg["content"])
            if char_count + msg_chars > target_chars:
                break
            truncated.insert(0, msg)
            char_count += msg_chars

        return system_msgs + truncated

    def _get_larger_context_model(self, current_model: str) -> str:
        """Get model with larger context window"""
        # Map to models with larger contexts
        context_upgrades = {
            "gpt-4": "claude-3-5-sonnet-20241022",  # 8k → 200k
            "gpt-3.5-turbo": "gpt-4-turbo-preview",  # 16k → 128k
            "ollama/llama3.1:8b": "claude-3-5-sonnet-20241022",  # 8k → 200k
        }
        return context_upgrades.get(current_model, "claude-3-5-sonnet-20241022")

    def _get_alternative_provider(self, current_model: str) -> str:
        """Get alternative provider for same capability"""
        alternatives = {
            "gpt-4": "claude-3-5-sonnet-20241022",
            "claude-3-5-sonnet-20241022": "gpt-4-turbo-preview",
            "gpt-3.5-turbo": "ollama/llama3.1:8b",
        }
        return alternatives.get(current_model, current_model)

### Best Practices for Error Handling

1. **Use LiteLLM's Built-in Retries**: Set `num_retries` and `retry_after` for automatic handling
2. **Layer Retry Strategies**: Combine LiteLLM retries + Tenacity for complex scenarios
3. **Classify Errors**: Handle different error types with appropriate strategies
4. **Log Everything**: Use structured logging to track retry patterns
5. **Set Sensible Timeouts**: Balance responsiveness with completion probability
6. **Circuit Breaker**: Implement circuit breaker to avoid cascade failures
7. **Monitor Retry Rates**: Track retry metrics to identify provider issues
8. **Graceful Degradation**: Have local/fallback options when cloud providers fail

### Error Handling Configuration

```python
from pydantic import BaseModel, Field

class RetryConfig(BaseModel):
    """Retry configuration"""
    max_retries: int = Field(default=3, ge=0, le=10)
    initial_delay: float = Field(default=2.0, gt=0)
    max_delay: float = Field(default=60.0, gt=0)
    exponential_base: float = Field(default=2.0, gt=1)
    retry_on_timeout: bool = True
    retry_on_rate_limit: bool = True
    retry_on_server_error: bool = True
    retry_on_connection_error: bool = True

class TimeoutConfig(BaseModel):
    """Timeout configuration"""
    connect_timeout: float = Field(default=10.0, gt=0)
    read_timeout: float = Field(default=600.0, gt=0)
    total_timeout: float = Field(default=660.0, gt=0)
```

---

## 3. Instructor Integration for Structured Outputs

### Overview
Instructor is a library that adds structured output validation to LLM calls using Pydantic models. It integrates seamlessly with LiteLLM.

### Basic Instructor + LiteLLM Setup

```python
import instructor
from litellm import completion
from pydantic import BaseModel, Field
from typing import List, Optional

# Patch LiteLLM with Instructor
client = instructor.from_litellm(completion)

# Define structured output schema
class UserInfo(BaseModel):
    """Structured user information"""
    name: str = Field(..., description="Full name of the user")
    age: int = Field(..., ge=0, le=150, description="Age in years")
    email: Optional[str] = Field(None, description="Email address")
    interests: List[str] = Field(default_factory=list, description="List of interests")

# Get structured output
def extract_user_info(text: str) -> UserInfo:
    """Extract structured user information from text"""
    response = client(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Extract user information from the text."},
            {"role": "user", "content": text}
        ],
        response_model=UserInfo,  # Instructor adds this parameter
    )
    return response  # Returns validated UserInfo instance

# Usage
user_text = "My name is John Doe, I'm 32 years old, love coding and hiking."
user_info = extract_user_info(user_text)
print(user_info.name)  # "John Doe"
print(user_info.age)   # 32
```

### Advanced Instructor Patterns

```python
import instructor
from litellm import Router
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal, Union
from enum import Enum
import asyncio

class Priority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class Task(BaseModel):
    """Individual task with validation"""
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=10)
    priority: Priority = Field(default=Priority.MEDIUM)
    estimated_hours: float = Field(..., ge=0.5, le=200)
    dependencies: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)

    @field_validator('title')
    @classmethod
    def validate_title(cls, v):
        """Ensure title doesn't contain special chars"""
        if any(char in v for char in ['<', '>', '{', '}']):
            raise ValueError("Title cannot contain special characters")
        return v

class TaskList(BaseModel):
    """Collection of tasks with metadata"""
    tasks: List[Task] = Field(..., min_items=1, max_items=50)
    total_estimated_hours: float = Field(..., ge=0)
    summary: str = Field(..., min_length=20)

    @field_validator('total_estimated_hours')
    @classmethod
    def validate_total(cls, v, info):
        """Ensure total matches sum of task estimates"""
        if 'tasks' in info.data:
            calculated = sum(t.estimated_hours for t in info.data['tasks'])
            if abs(v - calculated) > 0.1:  # Allow small floating point errors
                raise ValueError(f"Total hours {v} doesn't match sum {calculated}")
        return v

class StructuredOutputManager:
    """
    Manager for structured outputs with LiteLLM + Instructor
    """

    def __init__(self, router: Router):
        self.router = router
        # Patch router for instructor support
        self.client = instructor.from_litellm(router.completion)
        self.async_client = instructor.from_litellm(router.acompletion)

    def get_structured_output(
        self,
        messages: List[Dict[str, str]],
        response_model: type[BaseModel],
        model: str = "gpt-4",
        max_retries: int = 3,
        **kwargs
    ) -> BaseModel:
        """
        Get structured output with automatic validation and retries

        Instructor handles:
        - Schema injection into prompt
        - Response parsing and validation
        - Automatic retry on validation failures
        - Partial response handling
        """
        try:
            response = self.client(
                model=model,
                messages=messages,
                response_model=response_model,
                max_retries=max_retries,  # Instructor's retry for validation
                **kwargs
            )
            return response

        except instructor.exceptions.IncompleteOutputException as e:
            # Model didn't generate complete output
            # Instructor can try to salvage partial results
            if e.last_completion:
                return response_model.parse_obj(e.last_completion)
            raise

        except Exception as e:
            raise StructuredOutputError(f"Failed to get structured output: {e}")

    async def get_structured_output_async(
        self,
        messages: List[Dict[str, str]],
        response_model: type[BaseModel],
        model: str = "gpt-4",
        **kwargs
    ) -> BaseModel:
        """Async version of get_structured_output"""
        response = await self.async_client(
            model=model,
            messages=messages,
            response_model=response_model,
            **kwargs
        )
        return response

# Usage example
async def generate_task_plan(description: str) -> TaskList:
    """Generate structured task plan from description"""
    manager = StructuredOutputManager(router)

    messages = [
        {
            "role": "system",
            "content": "You are a project planner. Generate a detailed task list."
        },
        {
            "role": "user",
            "content": f"Create a task plan for: {description}"
        }
    ]

    task_list = await manager.get_structured_output_async(
        messages=messages,
        response_model=TaskList,
        model="gpt-4",
        temperature=0.7,
    )

    return task_list

# Run it
plan = asyncio.run(generate_task_plan("Build a REST API with authentication"))
print(f"Generated {len(plan.tasks)} tasks, total: {plan.total_estimated_hours}h")
```

### Streaming Structured Outputs

```python
import instructor
from litellm import completion
from pydantic import BaseModel, Field
from typing import List, Iterable

class PartialTask(BaseModel):
    """Task that can be built incrementally"""
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[Priority] = None
    estimated_hours: Optional[float] = None

class StructuredStreamManager:
    """
    Handle streaming structured outputs
    """

    def __init__(self):
        self.client = instructor.from_litellm(completion)

    def stream_structured_output(
        self,
        messages: List[Dict[str, str]],
        response_model: type[BaseModel],
        model: str = "gpt-4",
    ) -> Iterable[BaseModel]:
        """
        Stream partial structured outputs as they're generated

        Yields partial models that progressively have more fields populated
        """
        response = self.client(
            model=model,
            messages=messages,
            response_model=instructor.Partial[response_model],  # Partial wrapper
            stream=True,
        )

        for partial in response:
            yield partial

# Usage
def process_streaming_tasks(description: str):
    """Process tasks as they stream in"""
    manager = StructuredStreamManager()

    messages = [
        {"role": "system", "content": "Generate tasks one by one."},
        {"role": "user", "content": description}
    ]

    print("Streaming tasks:")
    for partial_task in manager.stream_structured_output(
        messages=messages,
        response_model=Task,
        model="gpt-4"
    ):
        # partial_task progressively has more fields populated
        if partial_task.title:
            print(f"  - {partial_task.title}", end="")
        if partial_task.estimated_hours:
            print(f" ({partial_task.estimated_hours}h)", end="")
        print()
```

### Complex Nested Structures

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union
from datetime import datetime

class FileChange(BaseModel):
    """Represents a file change in implementation"""
    path: str = Field(..., description="File path")
    change_type: Literal["create", "modify", "delete"]
    description: str = Field(..., min_length=10)
    code_snippet: Optional[str] = None

class ImplementationPhase(BaseModel):
    """Phase in implementation plan"""
    phase_name: str
    order: int = Field(..., ge=1)
    file_changes: List[FileChange] = Field(..., min_items=1)
    estimated_minutes: int = Field(..., ge=5)
    validation_steps: List[str] = Field(..., min_items=1)

class TechnicalPlan(BaseModel):
    """Complete technical implementation plan"""
    summary: str = Field(..., min_length=50, max_length=500)
    architecture_decisions: List[str] = Field(..., min_items=1)
    phases: List[ImplementationPhase] = Field(..., min_items=1)
    total_estimated_hours: float
    technologies: List[str] = Field(..., min_items=1)
    risks: List[str] = Field(default_factory=list)

    @field_validator('phases')
    @classmethod
    def validate_phase_order(cls, phases):
        """Ensure phases are in correct order"""
        orders = [p.order for p in phases]
        if orders != sorted(orders):
            raise ValueError("Phases must be in sequential order")
        return phases

# Generate complex nested structure
def generate_technical_plan(specification: str) -> TechnicalPlan:
    """Generate comprehensive technical plan with validation"""
    client = instructor.from_litellm(completion)

    messages = [
        {
            "role": "system",
            "content": """You are a technical architect. Generate a detailed
            implementation plan with phases, file changes, and validation steps."""
        },
        {
            "role": "user",
            "content": f"Create technical plan for:\n\n{specification}"
        }
    ]

    plan = client(
        model="gpt-4-turbo-preview",  # Use larger context for complex outputs
        messages=messages,
        response_model=TechnicalPlan,
        temperature=0.5,
        max_retries=5,  # More retries for complex validation
    )

    return plan
```

### Best Practices for Instructor + LiteLLM

1. **Use Type Hints Everywhere**: Pydantic relies on type hints for validation
2. **Add Field Descriptions**: Help LLM understand what each field should contain
3. **Use Validators**: Add custom validators for business logic constraints
4. **Set Reasonable Limits**: Use `min_items`, `max_items`, `min_length` to prevent abuse
5. **Handle Partial Outputs**: Use `instructor.Partial` for streaming or incomplete responses
6. **Retry on Validation Failures**: Set `max_retries` to handle invalid outputs
7. **Use Enums for Categories**: Constrain categorical fields with Enum
8. **Nested Models for Complex Data**: Break complex schemas into nested Pydantic models
9. **Document Your Schemas**: Add docstrings to models and fields
10. **Test Schema Evolution**: Ensure schemas can evolve without breaking existing data

### Configuration for Structured Outputs

```python
from pydantic import BaseModel, Field
from typing import Type, Dict, Any

class StructuredOutputConfig(BaseModel):
    """Configuration for structured output generation"""
    max_retries: int = Field(default=3, description="Retries for validation failures")
    temperature: float = Field(default=0.5, ge=0, le=2, description="Lower for structured output")
    enable_streaming: bool = Field(default=False)
    validate_on_partial: bool = Field(default=True)
    strict_validation: bool = Field(default=True)
    fallback_to_json: bool = Field(default=False, description="Fallback to raw JSON if schema fails")

class SchemaRegistry:
    """Registry for Pydantic schemas"""

    def __init__(self):
        self._schemas: Dict[str, Type[BaseModel]] = {}

    def register(self, name: str, schema: Type[BaseModel]):
        """Register a schema for reuse"""
        self._schemas[name] = schema

    def get(self, name: str) -> Type[BaseModel]:
        """Get registered schema"""
        return self._schemas[name]

    def list_schemas(self) -> List[str]:
        """List all registered schema names"""
        return list(self._schemas.keys())
```

---

## 4. Provider Authentication Methods

### Overview
LiteLLM supports multiple authentication methods across 100+ providers. Each provider may use different auth mechanisms.

### Environment Variable Authentication

```python
import os
from litellm import completion

# LiteLLM automatically reads provider API keys from environment variables
# Following standard naming conventions:

# OpenAI
os.environ["OPENAI_API_KEY"] = "sk-..."

# Anthropic
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-..."

# Google (Gemini/PaLM)
os.environ["GEMINI_API_KEY"] = "..."
os.environ["VERTEXAI_PROJECT"] = "your-project-id"
os.environ["VERTEXAI_LOCATION"] = "us-central1"

# Azure OpenAI
os.environ["AZURE_API_KEY"] = "..."
os.environ["AZURE_API_BASE"] = "https://your-resource.openai.azure.com"
os.environ["AZURE_API_VERSION"] = "2024-02-15-preview"

# Cohere
os.environ["COHERE_API_KEY"] = "..."

# Hugging Face
os.environ["HUGGINGFACE_API_KEY"] = "hf_..."

# Groq
os.environ["GROQ_API_KEY"] = "gsk_..."

# DeepSeek
os.environ["DEEPSEEK_API_KEY"] = "..."

# Together AI
os.environ["TOGETHER_API_KEY"] = "..."

# Replicate
os.environ["REPLICATE_API_KEY"] = "r8_..."

# Bedrock (AWS)
os.environ["AWS_ACCESS_KEY_ID"] = "..."
os.environ["AWS_SECRET_ACCESS_KEY"] = "..."
os.environ["AWS_REGION_NAME"] = "us-west-2"

# Now use completion without passing keys explicitly
response = completion(
    model="gpt-4",  # LiteLLM reads OPENAI_API_KEY
    messages=[{"role": "user", "content": "Hello"}]
)

response = completion(
    model="claude-3-5-sonnet-20241022",  # Reads ANTHROPIC_API_KEY
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Programmatic Authentication

```python
from litellm import completion
from typing import Dict, Optional

class AuthenticationManager:
    """
    Centralized authentication management for all providers
    """

    def __init__(self, credentials: Dict[str, Dict[str, str]]):
        """
        Initialize with credentials dict

        Args:
            credentials: Dict mapping provider names to their auth details
                {
                    "openai": {"api_key": "sk-..."},
                    "anthropic": {"api_key": "sk-ant-..."},
                    "azure": {
                        "api_key": "...",
                        "api_base": "https://...",
                        "api_version": "..."
                    }
                }
        """
        self.credentials = credentials

    def get_auth_params(self, model: str) -> Dict[str, str]:
        """
        Get authentication parameters for a specific model

        Args:
            model: Model identifier (e.g., "gpt-4", "claude-3-5-sonnet")

        Returns:
            Dict of auth parameters to pass to completion()
        """
        # Determine provider from model name
        provider = self._get_provider(model)

        if provider not in self.credentials:
            raise AuthenticationError(f"No credentials for provider: {provider}")

        creds = self.credentials[provider]

        # Build auth params based on provider
        if provider == "openai":
            return {"api_key": creds["api_key"]}

        elif provider == "anthropic":
            return {"api_key": creds["api_key"]}

        elif provider == "azure":
            return {
                "api_key": creds["api_key"],
                "api_base": creds["api_base"],
                "api_version": creds.get("api_version", "2024-02-15-preview"),
            }

        elif provider == "vertex":
            return {
                "vertex_project": creds["project_id"],
                "vertex_location": creds.get("location", "us-central1"),
            }

        elif provider == "bedrock":
            return {
                "aws_access_key_id": creds["access_key_id"],
                "aws_secret_access_key": creds["secret_access_key"],
                "aws_region_name": creds.get("region", "us-west-2"),
            }

        else:
            # Generic provider (Cohere, Hugging Face, etc.)
            return {"api_key": creds.get("api_key")}

    def _get_provider(self, model: str) -> str:
        """Map model name to provider"""
        model_lower = model.lower()

        if model_lower.startswith("gpt-") or model_lower.startswith("text-davinci"):
            return "openai"
        elif model_lower.startswith("claude-"):
            return "anthropic"
        elif "azure/" in model_lower:
            return "azure"
        elif "vertex_ai/" in model_lower or "gemini" in model_lower:
            return "vertex"
        elif "bedrock/" in model_lower:
            return "bedrock"
        elif "command" in model_lower:
            return "cohere"
        elif "groq/" in model_lower:
            return "groq"
        elif "together_ai/" in model_lower:
            return "together"
        elif "ollama/" in model_lower:
            return "ollama"
        else:
            raise ValueError(f"Unknown provider for model: {model}")

    def completion_with_auth(
        self,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs
    ):
        """
        Make completion call with automatic auth injection
        """
        auth_params = self.get_auth_params(model)

        return completion(
            model=model,
            messages=messages,
            **auth_params,
            **kwargs
        )

# Usage
credentials = {
    "openai": {"api_key": "sk-..."},
    "anthropic": {"api_key": "sk-ant-..."},
    "azure": {
        "api_key": "...",
        "api_base": "https://your-resource.openai.azure.com",
        "api_version": "2024-02-15-preview"
    }
}

auth_manager = AuthenticationManager(credentials)

# Automatically uses correct auth for each model
response = auth_manager.completion_with_auth(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)

response = auth_manager.completion_with_auth(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Custom Base URLs (Self-hosted/Proxy)

```python
from litellm import completion

# Ollama (local model server)
response = completion(
    model="ollama/llama3.1:8b",
    api_base="http://localhost:11434",
    messages=[{"role": "user", "content": "Hello"}]
)

# Custom OpenAI-compatible endpoint
response = completion(
    model="openai/custom-model",
    api_base="https://your-proxy.com/v1",
    api_key="your-proxy-key",
    messages=[{"role": "user", "content": "Hello"}]
)

# vLLM server (OpenAI-compatible)
response = completion(
    model="openai/mistral-7b",
    api_base="http://localhost:8000/v1",
    messages=[{"role": "user", "content": "Hello"}]
)

# Text Generation Inference (HuggingFace)
response = completion(
    model="huggingface/codellama-7b",
    api_base="http://localhost:8080",
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Multi-tenant Authentication

```python
from litellm import Router
from typing import Dict, Optional
import jwt

class MultiTenantAuthManager:
    """
    Manage authentication for multiple tenants/users
    Each tenant can have different provider credentials
    """

    def __init__(self):
        self.tenant_credentials: Dict[str, Dict[str, Dict]] = {}
        self.routers: Dict[str, Router] = {}

    def register_tenant(
        self,
        tenant_id: str,
        credentials: Dict[str, Dict[str, str]]
    ):
        """
        Register credentials for a tenant

        Args:
            tenant_id: Unique tenant identifier
            credentials: Provider credentials for this tenant
        """
        self.tenant_credentials[tenant_id] = credentials

        # Create dedicated router for this tenant
        model_list = self._build_model_list(credentials)
        self.routers[tenant_id] = Router(model_list=model_list)

    def _build_model_list(self, credentials: Dict[str, Dict[str, str]]) -> List[Dict]:
        """Build model list from credentials"""
        model_list = []

        if "openai" in credentials:
            model_list.append({
                "model_name": "gpt-4",
                "litellm_params": {
                    "model": "gpt-4",
                    "api_key": credentials["openai"]["api_key"],
                }
            })

        if "anthropic" in credentials:
            model_list.append({
                "model_name": "claude-3-5-sonnet",
                "litellm_params": {
                    "model": "claude-3-5-sonnet-20241022",
                    "api_key": credentials["anthropic"]["api_key"],
                }
            })

        if "ollama" in credentials:
            model_list.append({
                "model_name": "llama-local",
                "litellm_params": {
                    "model": "ollama/llama3.1:8b",
                    "api_base": credentials["ollama"].get(
                        "api_base",
                        "http://localhost:11434"
                    ),
                }
            })

        return model_list

    def get_router(self, tenant_id: str) -> Router:
        """Get router for specific tenant"""
        if tenant_id not in self.routers:
            raise AuthenticationError(f"Tenant not registered: {tenant_id}")
        return self.routers[tenant_id]

    async def completion_for_tenant(
        self,
        tenant_id: str,
        model: str,
        messages: List[Dict[str, str]],
        **kwargs
    ):
        """Make completion call for specific tenant"""
        router = self.get_router(tenant_id)
        response = await router.acompletion(
            model=model,
            messages=messages,
            **kwargs
        )
        return response

# Usage
auth_manager = MultiTenantAuthManager()

# Register tenant A with OpenAI access
auth_manager.register_tenant(
    tenant_id="tenant_a",
    credentials={
        "openai": {"api_key": "sk-tenant-a-key"},
        "ollama": {"api_base": "http://localhost:11434"}
    }
)

# Register tenant B with Anthropic access
auth_manager.register_tenant(
    tenant_id="tenant_b",
    credentials={
        "anthropic": {"api_key": "sk-ant-tenant-b-key"},
    }
)

# Use tenant-specific credentials
response = await auth_manager.completion_for_tenant(
    tenant_id="tenant_a",
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Configuration-based Authentication

```python
from pydantic import BaseModel, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Dict, Optional
import yaml

class ProviderCredentials(BaseModel):
    """Credentials for a single provider"""
    api_key: Optional[SecretStr] = None
    api_base: Optional[str] = None
    api_version: Optional[str] = None
    project_id: Optional[str] = None
    region: Optional[str] = None
    access_key_id: Optional[SecretStr] = None
    secret_access_key: Optional[SecretStr] = None

class LLMSettings(BaseSettings):
    """
    LLM configuration with automatic environment variable loading

    Loads from:
    1. Environment variables (OPENAI_API_KEY, etc.)
    2. .env file
    3. Config file (YAML/JSON)
    4. Programmatic settings
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore"
    )

    # Provider credentials (loaded from env vars)
    openai_api_key: Optional[SecretStr] = Field(None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[SecretStr] = Field(None, alias="ANTHROPIC_API_KEY")
    gemini_api_key: Optional[SecretStr] = Field(None, alias="GEMINI_API_KEY")
    cohere_api_key: Optional[SecretStr] = Field(None, alias="COHERE_API_KEY")
    groq_api_key: Optional[SecretStr] = Field(None, alias="GROQ_API_KEY")

    # Azure specific
    azure_api_key: Optional[SecretStr] = Field(None, alias="AZURE_API_KEY")
    azure_api_base: Optional[str] = Field(None, alias="AZURE_API_BASE")
    azure_api_version: Optional[str] = Field("2024-02-15-preview", alias="AZURE_API_VERSION")

    # AWS Bedrock
    aws_access_key_id: Optional[SecretStr] = Field(None, alias="AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[SecretStr] = Field(None, alias="AWS_SECRET_ACCESS_KEY")
    aws_region_name: Optional[str] = Field("us-west-2", alias="AWS_REGION_NAME")

    # Google Vertex AI
    vertex_project: Optional[str] = Field(None, alias="VERTEXAI_PROJECT")
    vertex_location: Optional[str] = Field("us-central1", alias="VERTEXAI_LOCATION")

    # Local/custom endpoints
    ollama_base_url: Optional[str] = Field("http://localhost:11434", alias="OLLAMA_BASE_URL")

    # Default model
    default_model: str = Field("gpt-4", alias="DEFAULT_MODEL")

    @classmethod
    def from_yaml(cls, path: str) -> "LLMSettings":
        """Load settings from YAML file"""
        with open(path) as f:
            config = yaml.safe_load(f)
        return cls(**config)

    def get_credentials(self, provider: str) -> Dict[str, str]:
        """Get credentials for a specific provider"""
        if provider == "openai":
            return {"api_key": self.openai_api_key.get_secret_value()}
        elif provider == "anthropic":
            return {"api_key": self.anthropic_api_key.get_secret_value()}
        elif provider == "azure":
            return {
                "api_key": self.azure_api_key.get_secret_value(),
                "api_base": self.azure_api_base,
                "api_version": self.azure_api_version,
            }
        elif provider == "bedrock":
            return {
                "aws_access_key_id": self.aws_access_key_id.get_secret_value(),
                "aws_secret_access_key": self.aws_secret_access_key.get_secret_value(),
                "aws_region_name": self.aws_region_name,
            }
        # Add more providers as needed
        raise ValueError(f"Unknown provider: {provider}")

# Usage with environment variables
settings = LLMSettings()  # Automatically loads from .env

# Usage with YAML config
# config.yaml:
# openai_api_key: sk-...
# anthropic_api_key: sk-ant-...
# default_model: claude-3-5-sonnet-20241022
settings = LLMSettings.from_yaml("config.yaml")

# Use in application
response = completion(
    model=settings.default_model,
    api_key=settings.get_credentials("openai")["api_key"],
    messages=[{"role": "user", "content": "Hello"}]
)
```

### Best Practices for Authentication

1. **Environment Variables First**: Use env vars for local development, CI/CD
2. **Never Commit Secrets**: Use `.env` files (gitignored) or secret managers
3. **Pydantic Settings**: Use pydantic-settings for type-safe configuration
4. **SecretStr for Keys**: Use `SecretStr` to prevent accidental logging
5. **Provider Auto-detection**: Let LiteLLM auto-detect providers from model names
6. **Multi-tenant Isolation**: Separate credentials by tenant/user in SaaS apps
7. **Custom Base URLs**: Support self-hosted models for privacy/cost
8. **Credential Rotation**: Design for easy credential updates without code changes
9. **Fallback to Local**: Have local Ollama as fallback when cloud credentials missing
10. **Validate on Startup**: Test credentials at application startup, fail fast

---

## 5. Streaming Support Patterns

### Basic Streaming

```python
from litellm import completion
from typing import Iterator

def stream_completion(messages: List[Dict[str, str]], model: str = "gpt-4") -> Iterator[str]:
    """
    Basic streaming completion

    Yields text chunks as they arrive from the LLM
    """
    response = completion(
        model=model,
        messages=messages,
        stream=True,  # Enable streaming
    )

    for chunk in response:
        # Extract text from chunk
        if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
            delta = chunk.choices[0].delta
            if hasattr(delta, 'content') and delta.content:
                yield delta.content

# Usage
messages = [{"role": "user", "content": "Write a long story"}]
print("Streaming response:")
for text_chunk in stream_completion(messages):
    print(text_chunk, end="", flush=True)
print()  # Newline at end
```

### Async Streaming

```python
from litellm import acompletion
from typing import AsyncIterator
import asyncio

async def stream_completion_async(
    messages: List[Dict[str, str]],
    model: str = "gpt-4"
) -> AsyncIterator[str]:
    """
    Async streaming completion for better concurrency
    """
    response = await acompletion(
        model=model,
        messages=messages,
        stream=True,
    )

    async for chunk in response:
        if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
            delta = chunk.choices[0].delta
            if hasattr(delta, 'content') and delta.content:
                yield delta.content

# Usage
async def main():
    messages = [{"role": "user", "content": "Explain quantum computing"}]

    print("Async streaming:")
    async for text_chunk in stream_completion_async(messages):
        print(text_chunk, end="", flush=True)
    print()

asyncio.run(main())
```

### Rich Console Streaming

```python
from litellm import completion
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from typing import Iterator

class StreamingPresenter:
    """
    Present streaming LLM responses with rich formatting
    """

    def __init__(self):
        self.console = Console()

    def stream_with_formatting(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4"
    ) -> str:
        """
        Stream response with live-updating rich formatting

        Returns:
            Complete response text
        """
        response = completion(
            model=model,
            messages=messages,
            stream=True,
        )

        accumulated_text = ""

        # Use Live context for updating display
        with Live(console=self.console, refresh_per_second=10) as live:
            for chunk in response:
                if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        accumulated_text += delta.content

                        # Render as markdown (live updates)
                        live.update(Markdown(accumulated_text))

        return accumulated_text

# Usage
presenter = StreamingPresenter()
messages = [
    {
        "role": "user",
        "content": "Write a markdown document about Python best practices"
    }
]
full_response = presenter.stream_with_formatting(messages)
```

### Streaming with Token Counting

```python
from litellm import completion
import tiktoken
from typing import Iterator, Tuple

class StreamingTokenCounter:
    """
    Stream response while counting tokens in real-time
    """

    def __init__(self, model: str = "gpt-4"):
        self.model = model
        # Get appropriate tokenizer for model
        try:
            self.encoder = tiktoken.encoding_for_model(model)
        except KeyError:
            # Fallback to cl100k_base for unknown models
            self.encoder = tiktoken.get_encoding("cl100k_base")

    def stream_with_token_count(
        self,
        messages: List[Dict[str, str]]
    ) -> Iterator[Tuple[str, int, int]]:
        """
        Stream chunks with running token count

        Yields:
            Tuple of (text_chunk, chunk_tokens, total_tokens)
        """
        response = completion(
            model=self.model,
            messages=messages,
            stream=True,
        )

        total_tokens = 0

        for chunk in response:
            if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if hasattr(delta, 'content') and delta.content:
                    text = delta.content
                    chunk_tokens = len(self.encoder.encode(text))
                    total_tokens += chunk_tokens

                    yield (text, chunk_tokens, total_tokens)

# Usage
counter = StreamingTokenCounter(model="gpt-4")
messages = [{"role": "user", "content": "Write a detailed essay"}]

print("Streaming with token count:")
for text, chunk_tokens, total_tokens in counter.stream_with_token_count(messages):
    print(f"[{total_tokens} tokens] {text}", end="", flush=True)
print()
```

### Streaming with Callbacks

```python
from litellm import completion
from typing import Callable, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class StreamEvent:
    """Event emitted during streaming"""
    timestamp: datetime
    event_type: str  # "start", "chunk", "end", "error"
    content: Optional[str] = None
    metadata: Optional[dict] = None
    error: Optional[Exception] = None

class StreamingCallbackManager:
    """
    Manage callbacks during streaming operations
    """

    def __init__(
        self,
        on_start: Optional[Callable[[StreamEvent], None]] = None,
        on_chunk: Optional[Callable[[StreamEvent], None]] = None,
        on_end: Optional[Callable[[StreamEvent], None]] = None,
        on_error: Optional[Callable[[StreamEvent], None]] = None,
    ):
        self.on_start = on_start
        self.on_chunk = on_chunk
        self.on_end = on_end
        self.on_error = on_error

    def stream_with_callbacks(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4",
        **kwargs
    ) -> str:
        """
        Stream with callback notifications

        Returns:
            Complete response text
        """
        # Emit start event
        if self.on_start:
            self.on_start(StreamEvent(
                timestamp=datetime.now(),
                event_type="start",
                metadata={"model": model, "message_count": len(messages)}
            ))

        accumulated_text = ""
        chunk_count = 0

        try:
            response = completion(
                model=model,
                messages=messages,
                stream=True,
                **kwargs
            )

            for chunk in response:
                if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if hasattr(delta, 'content') and delta.content:
                        text = delta.content
                        accumulated_text += text
                        chunk_count += 1

                        # Emit chunk event
                        if self.on_chunk:
                            self.on_chunk(StreamEvent(
                                timestamp=datetime.now(),
                                event_type="chunk",
                                content=text,
                                metadata={
                                    "chunk_number": chunk_count,
                                    "accumulated_length": len(accumulated_text)
                                }
                            ))

            # Emit end event
            if self.on_end:
                self.on_end(StreamEvent(
                    timestamp=datetime.now(),
                    event_type="end",
                    content=accumulated_text,
                    metadata={
                        "total_chunks": chunk_count,
                        "total_length": len(accumulated_text)
                    }
                ))

            return accumulated_text

        except Exception as e:
            # Emit error event
            if self.on_error:
                self.on_error(StreamEvent(
                    timestamp=datetime.now(),
                    event_type="error",
                    error=e,
                    metadata={"chunk_count": chunk_count}
                ))
            raise

# Usage with custom callbacks
def handle_start(event: StreamEvent):
    print(f"[{event.timestamp}] Starting stream with {event.metadata['model']}")

def handle_chunk(event: StreamEvent):
    print(event.content, end="", flush=True)

def handle_end(event: StreamEvent):
    print(f"\n[{event.timestamp}] Completed: {event.metadata['total_chunks']} chunks, "
          f"{event.metadata['total_length']} chars")

def handle_error(event: StreamEvent):
    print(f"\n[ERROR] {event.error}")

manager = StreamingCallbackManager(
    on_start=handle_start,
    on_chunk=handle_chunk,
    on_end=handle_end,
    on_error=handle_error
)

messages = [{"role": "user", "content": "Tell me a story"}]
response = manager.stream_with_callbacks(messages, model="gpt-4")
```

### Streaming to Multiple Outputs

```python
from litellm import completion
from typing import List, TextIO
import sys

class MultiStreamWriter:
    """
    Stream to multiple outputs simultaneously
    """

    def __init__(self, outputs: List[TextIO]):
        """
        Args:
            outputs: List of file-like objects to write to
        """
        self.outputs = outputs

    def stream_to_multiple(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4"
    ) -> str:
        """
        Stream to all registered outputs

        Returns:
            Complete response text
        """
        response = completion(
            model=model,
            messages=messages,
            stream=True,
        )

        accumulated_text = ""

        for chunk in response:
            if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if hasattr(delta, 'content') and delta.content:
                    text = delta.content
                    accumulated_text += text

                    # Write to all outputs
                    for output in self.outputs:
                        output.write(text)
                        output.flush()

        return accumulated_text

# Usage - write to console and file simultaneously
with open("response.txt", "w") as f:
    writer = MultiStreamWriter([sys.stdout, f])

    messages = [{"role": "user", "content": "Explain machine learning"}]
    response = writer.stream_to_multiple(messages)

# response.txt now contains the full response
```

### Streaming with Instructor (Partial Structured Outputs)

```python
import instructor
from litellm import completion
from pydantic import BaseModel, Field
from typing import List, Optional

class Article(BaseModel):
    """Article structure that builds incrementally"""
    title: Optional[str] = None
    summary: Optional[str] = None
    sections: List[str] = Field(default_factory=list)
    conclusion: Optional[str] = None

class StructuredStreamManager:
    """
    Stream structured outputs as they're generated
    """

    def __init__(self):
        self.client = instructor.from_litellm(completion)

    def stream_structured(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4"
    ):
        """
        Stream partial structured outputs

        Yields progressively more complete Article objects
        """
        response = self.client(
            model=model,
            messages=messages,
            response_model=instructor.Partial[Article],  # Partial wrapper
            stream=True,
        )

        for partial_article in response:
            yield partial_article

# Usage
manager = StructuredStreamManager()

messages = [
    {
        "role": "user",
        "content": "Write an article about renewable energy with title, summary, 3 sections, and conclusion"
    }
]

print("Streaming structured output:")
for partial in manager.stream_structured(messages):
    if partial.title:
        print(f"\nTitle: {partial.title}")
    if partial.summary:
        print(f"Summary: {partial.summary}")
    if partial.sections:
        print(f"Sections: {len(partial.sections)}")
    if partial.conclusion:
        print(f"Conclusion available")
```

### Streaming with Progress Tracking

```python
from litellm import completion
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.console import Console
from typing import Optional

class ProgressStreamingManager:
    """
    Stream with rich progress indicators
    """

    def __init__(self):
        self.console = Console()

    def stream_with_progress(
        self,
        messages: List[Dict[str, str]],
        model: str = "gpt-4",
        expected_tokens: Optional[int] = None
    ) -> str:
        """
        Stream with progress bar (if expected_tokens provided)
        or spinner (if not)
        """
        response = completion(
            model=model,
            messages=messages,
            stream=True,
        )

        accumulated_text = ""
        token_count = 0

        if expected_tokens:
            # Use progress bar when we know expected length
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("{task.completed}/{task.total} tokens"),
                console=self.console
            ) as progress:
                task = progress.add_task(
                    "Generating...",
                    total=expected_tokens
                )

                for chunk in response:
                    if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        if hasattr(delta, 'content') and delta.content:
                            text = delta.content
                            accumulated_text += text
                            # Rough token count (4 chars ≈ 1 token)
                            tokens = len(text) // 4
                            token_count += tokens
                            progress.update(task, advance=tokens)
        else:
            # Use spinner when length unknown
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=self.console
            ) as progress:
                task = progress.add_task("Generating response...", total=None)

                for chunk in response:
                    if hasattr(chunk, 'choices') and len(chunk.choices) > 0:
                        delta = chunk.choices[0].delta
                        if hasattr(delta, 'content') and delta.content:
                            accumulated_text += delta.content

        return accumulated_text

# Usage
manager = ProgressStreamingManager()

messages = [{"role": "user", "content": "Write a 500-word essay"}]
response = manager.stream_with_progress(
    messages,
    expected_tokens=700  # Rough estimate for 500 words
)
```

### Best Practices for Streaming

1. **Always Use Async for Production**: Better concurrency and resource usage
2. **Handle Incomplete Chunks**: Check for None/empty content in deltas
3. **Flush Output Buffers**: Call `flush()` after writing chunks for real-time display
4. **Track Token Usage**: Monitor streaming to prevent runaway costs
5. **Implement Timeouts**: Set reasonable timeouts for streaming operations
6. **Graceful Cancellation**: Allow users to cancel long-running streams
7. **Error Recovery**: Handle network issues mid-stream gracefully
8. **Progress Feedback**: Show progress indicators for better UX
9. **Buffer Management**: Balance between real-time display and efficient I/O
10. **Structured Streaming**: Use Instructor's Partial for streaming structured data

### Streaming Configuration

```python
from pydantic import BaseModel, Field

class StreamingConfig(BaseModel):
    """Configuration for streaming operations"""
    enabled: bool = Field(default=True)
    chunk_size: Optional[int] = Field(None, description="Target chunk size in tokens")
    buffer_size: int = Field(default=1, description="Number of chunks to buffer")
    flush_interval: float = Field(default=0.1, description="Seconds between flushes")
    show_progress: bool = Field(default=True)
    enable_callbacks: bool = Field(default=False)
    timeout: float = Field(default=300.0, description="Streaming timeout in seconds")
    retry_on_disconnect: bool = Field(default=True)
    max_retries: int = Field(default=3)
```

---

## Summary and Key Recommendations

### Overall Architecture Recommendations

1. **Use Router for Production**: Prefer `Router` over direct `completion()` calls for better control
2. **Layer Your Abstractions**:
   - Low-level: LiteLLM Router
   - Mid-level: Provider manager with auth/retry
   - High-level: Domain-specific clients (SpecBuilder, Planner, etc.)
3. **Configuration-Driven**: Use Pydantic Settings for all configuration
4. **Async by Default**: Use async/await for better scalability
5. **Structured Outputs Everywhere**: Use Instructor + Pydantic for reliable parsing

### Production Checklist

- [ ] Implement fallback chains with local models as final fallback
- [ ] Configure retry logic with exponential backoff
- [ ] Use Instructor for all LLM-generated data structures
- [ ] Support env vars + config files + programmatic configuration
- [ ] Implement async streaming with progress indicators
- [ ] Add comprehensive error handling for all provider types
- [ ] Include circuit breakers to prevent cascade failures
- [ ] Log all provider interactions for debugging
- [ ] Validate credentials on startup
- [ ] Document supported providers and authentication methods
- [ ] Add integration tests for top 5 providers
- [ ] Implement token counting and budget controls
- [ ] Support multi-tenant credential isolation
- [ ] Enable streaming for long-running operations
- [ ] Add callbacks for observability

### Code Organization

```
src/speckit/
├── llm/
│   ├── __init__.py
│   ├── router.py           # Router configuration
│   ├── auth.py             # Authentication management
│   ├── retry.py            # Retry and error handling
│   ├── streaming.py        # Streaming utilities
│   └── structured.py       # Instructor integration
├── config/
│   ├── __init__.py
│   ├── settings.py         # Pydantic Settings
│   └── providers.py        # Provider configurations
└── core/
    # Your application logic
```

### Reference Implementation Snippet

```python
# Complete example combining all best practices
import instructor
from litellm import Router
from pydantic import BaseModel
from typing import List, Dict

class ProductionLLMClient:
    """
    Production-ready LLM client with:
    - Fallback chains
    - Retry logic
    - Structured outputs
    - Multi-provider auth
    - Streaming support
    """

    def __init__(self, config: LLMSettings):
        # Initialize router with fallback chains
        model_list = self._build_model_list(config)
        self.router = Router(
            model_list=model_list,
            routing_strategy="priority",
            retry_after=10,
            num_retries=2,
            fallbacks=[
                {"primary": ["secondary", "local"]}
            ],
            allowed_fails=2,
        )

        # Patch for Instructor support
        self.client = instructor.from_litellm(self.router.completion)
        self.async_client = instructor.from_litellm(self.router.acompletion)

    async def generate_structured(
        self,
        messages: List[Dict[str, str]],
        response_model: type[BaseModel],
        model: str = "primary",
        stream: bool = False,
    ) -> BaseModel:
        """Generate structured output with all safeguards"""
        return await self.async_client(
            model=model,
            messages=messages,
            response_model=response_model,
            stream=stream,
            max_retries=3,
        )
```

This research document provides comprehensive guidance for building a production-grade Python library with LiteLLM supporting 100+ providers. All patterns are based on LiteLLM's actual capabilities and established best practices.
