# LiteLLM Quick Reference Guide

**Created**: 2025-12-19
**Purpose**: Quick reference for common LiteLLM patterns

## Quick Start

```python
# Install dependencies
pip install litellm instructor pydantic pydantic-settings

# Basic usage
from litellm import completion

response = completion(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)
```

## 1. Fallback Chains - Quick Patterns

### Simple Fallbacks
```python
from litellm import completion

response = completion(
    model="gpt-4",
    messages=messages,
    fallbacks=["claude-3-5-sonnet-20241022", "gpt-3.5-turbo"]
)
```

### Router with Priorities
```python
from litellm import Router

router = Router(
    model_list=[
        {
            "model_name": "primary",
            "litellm_params": {"model": "gpt-4", "api_key": "sk-..."},
            "model_info": {"priority": 1}
        },
        {
            "model_name": "backup",
            "litellm_params": {"model": "claude-3-5-sonnet-20241022", "api_key": "sk-ant-..."},
            "model_info": {"priority": 2}
        }
    ],
    routing_strategy="priority"
)

response = await router.acompletion(model="primary", messages=messages)
```

## 2. Retry Logic - Quick Patterns

### Built-in Retries
```python
import litellm

# Global config
litellm.num_retries = 3
litellm.retry_after = 10

# Per-request
response = completion(
    model="gpt-4",
    messages=messages,
    num_retries=3
)
```

### Error Handling
```python
try:
    response = completion(model="gpt-4", messages=messages)
except litellm.exceptions.RateLimitError:
    # Handle rate limit
    pass
except litellm.exceptions.ContextWindowExceededError:
    # Switch to larger context model
    response = completion(model="claude-3-5-sonnet-20241022", messages=messages)
except litellm.exceptions.APIConnectionError:
    # Handle network errors
    pass
```

## 3. Instructor Integration - Quick Patterns

### Basic Structured Output
```python
import instructor
from litellm import completion
from pydantic import BaseModel

client = instructor.from_litellm(completion)

class User(BaseModel):
    name: str
    age: int

user = client(
    model="gpt-4",
    messages=[{"role": "user", "content": "Extract: John Doe, 30"}],
    response_model=User
)
```

### Streaming Structured Output
```python
class Task(BaseModel):
    title: str
    description: str

for partial in client(
    model="gpt-4",
    messages=messages,
    response_model=instructor.Partial[Task],
    stream=True
):
    print(partial.title if partial.title else "...")
```

## 4. Authentication - Quick Patterns

### Environment Variables
```python
import os

# LiteLLM auto-detects these
os.environ["OPENAI_API_KEY"] = "sk-..."
os.environ["ANTHROPIC_API_KEY"] = "sk-ant-..."
os.environ["GEMINI_API_KEY"] = "..."

# Just use the model
response = completion(model="gpt-4", messages=messages)
```

### Programmatic Auth
```python
response = completion(
    model="gpt-4",
    api_key="sk-...",
    messages=messages
)
```

### Custom Base URL (Ollama, etc.)
```python
response = completion(
    model="ollama/llama3.1:8b",
    api_base="http://localhost:11434",
    messages=messages
)
```

### Pydantic Settings
```python
from pydantic_settings import BaseSettings
from pydantic import SecretStr

class Settings(BaseSettings):
    openai_api_key: SecretStr
    anthropic_api_key: SecretStr

    class Config:
        env_file = ".env"

settings = Settings()
```

## 5. Streaming - Quick Patterns

### Basic Streaming
```python
response = completion(
    model="gpt-4",
    messages=messages,
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

### Async Streaming
```python
from litellm import acompletion

async def stream():
    response = await acompletion(
        model="gpt-4",
        messages=messages,
        stream=True
    )

    async for chunk in response:
        if chunk.choices[0].delta.content:
            print(chunk.choices[0].delta.content, end="", flush=True)
```

### With Rich Progress
```python
from rich.live import Live
from rich.markdown import Markdown

text = ""
with Live(console=console) as live:
    for chunk in completion(model="gpt-4", messages=messages, stream=True):
        if chunk.choices[0].delta.content:
            text += chunk.choices[0].delta.content
            live.update(Markdown(text))
```

## Common Configurations

### Provider Model Names

```python
# OpenAI
"gpt-4-turbo-preview"
"gpt-4"
"gpt-3.5-turbo"

# Anthropic
"claude-3-5-sonnet-20241022"
"claude-3-opus-20240229"

# Google
"gemini/gemini-pro"
"vertex_ai/gemini-pro"

# Ollama (local)
"ollama/llama3.1:8b"
"ollama/mistral:7b"

# Azure OpenAI
"azure/gpt-4"

# Groq
"groq/llama-3.1-70b-versatile"

# Cohere
"command-r-plus"
```

### Timeout Configuration

```python
response = completion(
    model="gpt-4",
    messages=messages,
    timeout=600,  # 10 minutes
)
```

### Max Tokens

```python
response = completion(
    model="gpt-4",
    messages=messages,
    max_tokens=2000,
)
```

### Temperature

```python
# Deterministic (structured outputs)
response = completion(model="gpt-4", messages=messages, temperature=0.0)

# Creative
response = completion(model="gpt-4", messages=messages, temperature=0.9)

# Balanced
response = completion(model="gpt-4", messages=messages, temperature=0.7)
```

## Error Types

```python
litellm.exceptions.RateLimitError          # 429 - rate limited
litellm.exceptions.ContextWindowExceededError  # Input too long
litellm.exceptions.ContentPolicyViolationError # Content filtered
litellm.exceptions.APIConnectionError       # Network error
litellm.exceptions.Timeout                 # Request timeout
litellm.exceptions.APIError                # General API error
```

## Complete Production Example

```python
import instructor
import litellm
from litellm import Router
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List, Dict, Optional
import asyncio

# Configuration
class LLMConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    openai_api_key: str
    anthropic_api_key: str
    default_model: str = "gpt-4"

# Initialize
config = LLMConfig()

router = Router(
    model_list=[
        {
            "model_name": "primary",
            "litellm_params": {
                "model": "gpt-4",
                "api_key": config.openai_api_key,
                "timeout": 600
            },
            "model_info": {"priority": 1}
        },
        {
            "model_name": "backup",
            "litellm_params": {
                "model": "claude-3-5-sonnet-20241022",
                "api_key": config.anthropic_api_key,
                "timeout": 600
            },
            "model_info": {"priority": 2}
        }
    ],
    routing_strategy="priority",
    num_retries=2,
    fallbacks=[{"primary": ["backup"]}]
)

client = instructor.from_litellm(router.completion)
async_client = instructor.from_litellm(router.acompletion)

# Schema
class Response(BaseModel):
    answer: str = Field(..., min_length=10)
    confidence: float = Field(..., ge=0, le=1)

# Usage
async def generate():
    try:
        result = await async_client(
            model="primary",
            messages=[{"role": "user", "content": "What is AI?"}],
            response_model=Response,
            max_retries=3
        )
        return result
    except litellm.exceptions.RateLimitError:
        print("Rate limited, all retries exhausted")
    except Exception as e:
        print(f"Error: {e}")

# Run
response = asyncio.run(generate())
print(f"Answer: {response.answer}")
print(f"Confidence: {response.confidence}")
```

## Tips and Tricks

1. **Always use async in production** - Better performance with `acompletion()`
2. **Set timeouts** - Prevent hanging requests
3. **Use Router for complex apps** - Better than direct `completion()` calls
4. **Validate with Instructor** - Always use Pydantic for structured data
5. **Include local fallback** - Ollama as final fallback for reliability
6. **Log everything** - Set `litellm.set_verbose = True` during development
7. **Test with mocks** - Use `litellm.mock_response` for testing
8. **Monitor token usage** - Track costs with callbacks
9. **Cache when possible** - Cache common responses
10. **Handle rate limits gracefully** - Use exponential backoff

## Testing

```python
# Mock for testing
import litellm

litellm.mock_response = "Mocked response"

response = completion(
    model="gpt-4",
    messages=[{"role": "user", "content": "test"}]
)
# Returns mocked response
```

## Debugging

```python
# Enable verbose logging
import litellm

litellm.set_verbose = True

# See all API calls and responses
response = completion(model="gpt-4", messages=messages)
```

## Common Gotchas

1. **Model names are case-sensitive** - Use exact names from docs
2. **Stream chunks may be None** - Always check before accessing
3. **Context limits vary** - Check each model's token limits
4. **Some providers need custom params** - Azure requires `api_base`, `api_version`
5. **Rate limits differ by provider** - Implement appropriate backoff
6. **Token counting is approximate** - Use tiktoken for accurate counts
7. **Streaming doesn't return usage** - Track tokens separately
8. **Async requires event loop** - Use `asyncio.run()` or existing loop
9. **Environment variables are case-sensitive** - Use exact names
10. **Router needs model_name** - Use aliases in model_list

## Resources

- LiteLLM Docs: https://docs.litellm.ai
- Instructor Docs: https://python.useinstructor.com
- Pydantic Docs: https://docs.pydantic.dev
- Provider List: https://docs.litellm.ai/docs/providers
