# Research Notes: Python Library with Universal LLM Support

**Feature**: 001-python-litellm-library
**Generated**: 2025-12-19
**Purpose**: Phase 0 research findings to inform technical decisions

## Research Summary

This document consolidates research findings for building a Python library with universal LLM support via LiteLLM, MCP server integration, and modern CLI using Typer/Rich.

---

## 1. LiteLLM Multi-Provider Integration

### Decision: Use LiteLLM with Instructor for Structured Outputs

**Rationale**: LiteLLM provides a unified interface to 100+ LLM providers with consistent API, automatic retry logic, and fallback support. Instructor adds reliable structured output parsing using Pydantic models.

**Alternatives Considered**:
- Direct provider SDKs: Rejected (each requires separate integration, no unified interface)
- LangChain: Rejected (heavier dependency, more abstraction than needed)
- OpenAI SDK only: Rejected (no multi-provider support without significant work)

### Implementation Patterns

#### Provider Configuration
```python
import litellm
from instructor import from_litellm

# LiteLLM uses provider prefixes for routing
# OpenAI: "gpt-4o", "gpt-4o-mini"
# Anthropic: "claude-sonnet-4-20250514", "claude-3-haiku-20240307"
# Google: "gemini/gemini-1.5-pro"
# Local: "ollama/llama3.1", "ollama/mistral"
# Groq: "groq/llama-3.1-70b-versatile"
# DeepSeek: "deepseek/deepseek-chat"

# Authentication via environment variables (provider-specific)
# OPENAI_API_KEY, ANTHROPIC_API_KEY, GEMINI_API_KEY, etc.
# Or set globally: litellm.api_key = "sk-..."
```

#### Fallback Chains
```python
response = litellm.completion(
    model="gpt-4o",
    messages=[{"role": "user", "content": prompt}],
    fallbacks=["gpt-4o-mini", "claude-3-haiku-20240307"],
    num_retries=3,
    timeout=120
)
```

#### Structured Outputs with Instructor
```python
from instructor import from_litellm
from pydantic import BaseModel

class UserStory(BaseModel):
    id: str
    as_a: str
    i_want: str
    so_that: str

client = from_litellm(litellm.completion)

story = client(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Generate a user story for login"}],
    response_model=UserStory,
    max_retries=3  # Instructor retries on validation failures
)
```

#### Streaming Support
```python
# Sync streaming
response = litellm.completion(
    model="gpt-4o",
    messages=messages,
    stream=True
)
for chunk in response:
    if chunk.choices[0].delta.content:
        yield chunk.choices[0].delta.content

# Async streaming
async for chunk in await litellm.acompletion(..., stream=True):
    if chunk.choices[0].delta.content:
        yield chunk.choices[0].delta.content
```

#### Error Handling
```python
from litellm.exceptions import (
    RateLimitError,
    APIConnectionError,
    Timeout,
    ServiceUnavailableError
)

try:
    response = litellm.completion(...)
except RateLimitError as e:
    # Automatic retry with exponential backoff
    # Or trigger fallback model
    pass
except Timeout:
    # Increase timeout or use faster model
    pass
```

### Supported Providers (Minimum 10)

| Provider | Model Format | Auth Env Var |
|----------|--------------|--------------|
| OpenAI | `gpt-4o`, `gpt-4o-mini` | `OPENAI_API_KEY` |
| Anthropic | `claude-sonnet-4-20250514` | `ANTHROPIC_API_KEY` |
| Google | `gemini/gemini-1.5-pro` | `GEMINI_API_KEY` |
| Ollama | `ollama/llama3.1` | None (local) |
| Groq | `groq/llama-3.1-70b` | `GROQ_API_KEY` |
| DeepSeek | `deepseek/deepseek-chat` | `DEEPSEEK_API_KEY` |
| OpenRouter | `openrouter/anthropic/claude-3.5-sonnet` | `OPENROUTER_API_KEY` |
| Together AI | `together_ai/meta-llama/Llama-3-70b` | `TOGETHER_API_KEY` |
| Mistral | `mistral/mistral-large` | `MISTRAL_API_KEY` |
| Azure OpenAI | `azure/deployment-name` | `AZURE_API_KEY` |

---

## 2. MCP Server Implementation

### Decision: Use FastMCP Pattern for Tool Exposure

**Rationale**: FastMCP provides a decorator-based approach that auto-generates tool schemas from Python type hints, reducing boilerplate and ensuring schema accuracy.

**Alternatives Considered**:
- Raw MCP SDK: Rejected (more boilerplate, manual schema definition)
- Custom protocol: Rejected (no ecosystem compatibility)

### Implementation Patterns

#### Basic Server Setup
```python
from mcp import FastMCP

mcp = FastMCP("speckit")

@mcp.tool()
def speckit_specify(
    feature_description: str,
    feature_id: str | None = None
) -> str:
    """Generate a feature specification from natural language description.

    Args:
        feature_description: Natural language description of the feature
        feature_id: Optional custom ID (auto-generated if not provided)

    Returns:
        Generated specification in Markdown format
    """
    kit = SpecKit(project_path=os.getcwd())
    spec = kit.specify(feature_description, feature_id)
    return spec.to_markdown()

@mcp.tool()
def speckit_plan(feature_id: str) -> str:
    """Generate technical implementation plan for a feature.

    Args:
        feature_id: Feature ID to generate plan for

    Returns:
        Technical plan in Markdown format
    """
    kit = SpecKit(project_path=os.getcwd())
    spec = kit.storage.load_specification(feature_id)
    plan = kit.plan(spec)
    return plan.to_markdown()
```

#### Async Tool Support
```python
@mcp.tool()
async def speckit_specify_async(feature_description: str) -> str:
    """Async version for long-running operations."""
    kit = SpecKit(project_path=os.getcwd())
    spec = await kit.specify_async(feature_description)
    return spec.to_markdown()
```

#### Error Handling in Tools
```python
from mcp.types import McpError

@mcp.tool()
def speckit_get_artifact(feature_id: str, artifact_type: str) -> str:
    """Retrieve a specific artifact."""
    try:
        kit = SpecKit(project_path=os.getcwd())
        if artifact_type == "spec":
            return kit.storage.load_specification(feature_id).to_markdown()
        elif artifact_type == "plan":
            return kit.storage.load_plan(feature_id).to_markdown()
        else:
            raise McpError(f"Unknown artifact type: {artifact_type}")
    except FileNotFoundError:
        raise McpError(f"Feature not found: {feature_id}")
```

#### Claude Desktop Configuration
```json
{
  "mcpServers": {
    "speckit": {
      "command": "python",
      "args": ["-m", "speckit.mcp"],
      "cwd": "/path/to/project",
      "env": {
        "OPENAI_API_KEY": "sk-..."
      }
    }
  }
}
```

### Exposed Tools

| Tool | Purpose | Parameters |
|------|---------|------------|
| `speckit_specify` | Generate specification | `feature_description`, `feature_id?` |
| `speckit_clarify` | Identify ambiguities | `feature_id`, `max_questions?` |
| `speckit_plan` | Generate tech plan | `feature_id`, `tech_stack?` |
| `speckit_tasks` | Generate tasks | `feature_id`, `parallel_friendly?` |
| `speckit_analyze` | Check consistency | `feature_id` |
| `speckit_list_features` | List all features | None |
| `speckit_get_artifact` | Get specific artifact | `feature_id`, `artifact_type` |

---

## 3. Typer CLI with Rich Console

### Decision: Follow Existing specify_cli Patterns

**Rationale**: The existing codebase demonstrates proven patterns for progress tracking, error handling, and interactive selection that should be replicated.

**Alternatives Considered**:
- Click: Rejected (Typer is Click-based but adds type hints and autocomplete)
- argparse: Rejected (no rich output support, more boilerplate)

### Implementation Patterns

#### Command Organization
```python
import typer
from typer.core import TyperGroup

class SpecKitGroup(TyperGroup):
    """Custom group with banner display."""
    def format_help(self, ctx, formatter):
        show_banner()
        super().format_help(ctx, formatter)

app = typer.Typer(
    name="speckit",
    help="Spec-driven development toolkit with AI assistance",
    add_completion=False,
    invoke_without_command=True,
    cls=SpecKitGroup,
)

# Subcommand groups
config_app = typer.Typer(help="Configuration management")
app.add_typer(config_app, name="config")
```

#### Progress Tracking with Rich
```python
from rich.console import Console
from rich.live import Live
from rich.tree import Tree

console = Console()

class StepTracker:
    """Track hierarchical progress steps."""
    def __init__(self, title: str):
        self.title = title
        self.steps = []
        self._refresh_cb = None

    def add(self, key: str, label: str):
        self.steps.append({"key": key, "label": label, "status": "pending"})

    def start(self, key: str, detail: str = ""):
        self._update(key, status="running", detail=detail)

    def complete(self, key: str, detail: str = ""):
        self._update(key, status="done", detail=detail)

    def render(self) -> Tree:
        tree = Tree(f"[cyan]{self.title}[/cyan]")
        for step in self.steps:
            symbol = {"done": "[green]●[/green]", "running": "[cyan]○[/cyan]", "pending": "[dim]○[/dim]"}
            tree.add(f"{symbol[step['status']]} {step['label']}")
        return tree

# Usage with Live display
tracker = StepTracker("Generating Specification")
tracker.add("analyze", "Analyzing feature description")
tracker.add("generate", "Generating user stories")
tracker.add("save", "Saving to file")

with Live(tracker.render(), console=console, refresh_per_second=4, transient=True) as live:
    tracker.attach_refresh(lambda: live.update(tracker.render()))

    tracker.start("analyze")
    spec = kit.specify(description)
    tracker.complete("analyze")
    # ... continue
```

#### JSON vs Human Output
```python
import json

@app.callback()
def main_callback(
    ctx: typer.Context,
    json_output: bool = typer.Option(False, "--json", help="Output JSON"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output")
):
    ctx.ensure_object(dict)
    ctx.obj["json_mode"] = json_output
    ctx.obj["verbose"] = verbose

@app.command()
def specify(
    ctx: typer.Context,
    description: str = typer.Argument(..., help="Feature description"),
    feature_id: str = typer.Option(None, "--id", help="Feature ID")
):
    """Generate a feature specification."""
    json_mode = ctx.obj.get("json_mode", False)

    kit = SpecKit(project_path=".")
    spec = kit.specify(description, feature_id)

    if json_mode:
        print(json.dumps(spec.model_dump(), indent=2))
    else:
        console.print(Panel(spec.to_markdown(), title="Specification"))
```

#### Error Handling
```python
from rich.panel import Panel

# Exit codes
EXIT_SUCCESS = 0
EXIT_ERROR = 1
EXIT_VALIDATION = 2
EXIT_NOT_FOUND = 3

def handle_error(message: str, details: str = None, exit_code: int = EXIT_ERROR):
    """Display error and exit."""
    content = message if not details else f"{message}\n\n{details}"
    console.print(Panel(content, title="[red]Error[/red]", border_style="red"))
    raise typer.Exit(exit_code)

@app.command()
def plan(feature_id: str):
    try:
        kit = SpecKit(project_path=".")
        spec = kit.storage.load_specification(feature_id)
        plan = kit.plan(spec)
        console.print(plan.to_markdown())
    except FileNotFoundError:
        handle_error(
            f"Feature '{feature_id}' not found",
            "Run 'speckit list' to see available features",
            exit_code=EXIT_NOT_FOUND
        )
    except LLMError as e:
        handle_error(f"LLM error: {e.message}", str(e))
```

### CLI Command Structure

```text
speckit
├── init                    # Initialize project
├── constitution [name]     # Create/update constitution
├── specify <description>   # Generate specification
├── clarify --feature ID    # Clarify specification
├── plan --feature ID       # Generate plan
├── tasks --feature ID      # Generate tasks
├── analyze --feature ID    # Check consistency
├── list                    # List features
├── show --feature ID       # Show feature artifacts
├── config
│   ├── set <key> <value>   # Set config value
│   ├── get <key>           # Get config value
│   └── show                # Show all config
└── mcp
    └── serve               # Start MCP server
```

---

## 4. Configuration Management

### Decision: Pydantic Settings with Environment/File/Code Precedence

**Rationale**: Pydantic Settings provides type-safe configuration with automatic environment variable loading and validation.

**Alternatives Considered**:
- python-dotenv only: Rejected (no type validation)
- ConfigParser: Rejected (no nested configs, no validation)
- Dynaconf: Rejected (heavier dependency than needed)

### Implementation Patterns

#### Pydantic Settings Setup
```python
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class LLMConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="SPECKIT_",
        env_file=".env",
        extra="ignore"
    )

    model: str = Field(default="gpt-4o-mini")
    api_key: str | None = Field(default=None)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4096, ge=1)
    fallback_models: list[str] = Field(
        default_factory=lambda: ["gpt-4o-mini", "claude-3-haiku-20240307"]
    )
```

#### YAML Config File
```python
import yaml
from pathlib import Path

class SpecKitConfig(BaseSettings):
    @classmethod
    def from_project(cls, project_path: Path) -> "SpecKitConfig":
        config_file = project_path / ".speckit" / "config.yaml"
        if config_file.exists():
            with open(config_file) as f:
                data = yaml.safe_load(f)
            return cls(**data, project_path=project_path)
        return cls(project_path=project_path)

    def save(self):
        config_dir = self.project_path / ".speckit"
        config_dir.mkdir(parents=True, exist_ok=True)
        with open(config_dir / "config.yaml", "w") as f:
            yaml.dump(self.model_dump(exclude={"project_path"}), f)
```

### Configuration Precedence

1. **Programmatic** (code): Highest priority
2. **CLI arguments**: Override config file
3. **Environment variables**: `SPECKIT_*` prefixed
4. **Config file**: `.speckit/config.yaml`
5. **Defaults**: Built into Pydantic models

---

## 5. Template System

### Decision: Jinja2 for Prompt Templates

**Rationale**: Jinja2 is widely used, well-documented, and supports template inheritance for prompt variants.

**Alternatives Considered**:
- String formatting: Rejected (no conditionals, loops)
- Mako: Rejected (less common, steeper learning curve)
- Handlebars: Rejected (requires JS runtime)

### Implementation Pattern

```python
from jinja2 import Environment, PackageLoader, select_autoescape

class TemplateManager:
    def __init__(self):
        self.env = Environment(
            loader=PackageLoader("speckit", "templates"),
            autoescape=select_autoescape(),
            trim_blocks=True,
            lstrip_blocks=True
        )

    def render(self, template_name: str, **context) -> str:
        template = self.env.get_template(f"{template_name}.jinja2")
        return template.render(**context)

# Example template: specification.jinja2
"""
You are a technical specification writer. Generate a specification for:

Feature: {{ feature_description }}

{% if constitution %}
Project Principles:
{% for principle in constitution.core_principles %}
- {{ principle }}
{% endfor %}
{% endif %}

Include:
- User stories with acceptance criteria
- Functional requirements
- Success criteria
"""
```

---

## 6. Testing Strategy

### Decision: pytest with Async Support and Mocking

**Rationale**: pytest is the Python standard, pytest-asyncio handles async tests, and mocking LLM calls enables fast, deterministic tests.

### Test Organization

```text
tests/
├── conftest.py              # Shared fixtures
├── unit/                    # Mocked dependencies
│   ├── test_config.py       # Configuration validation
│   ├── test_schemas.py      # Pydantic model tests
│   └── test_storage.py      # File I/O tests
├── integration/             # Real components
│   ├── test_workflow.py     # End-to-end workflow
│   └── test_cli.py          # CLI invocation
└── contract/                # LLM interface tests
    └── test_llm_providers.py
```

### Key Fixtures

```python
# conftest.py
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_llm_response():
    """Mock LLM completion response."""
    return {
        "choices": [{"message": {"content": "Generated content"}}],
        "model": "gpt-4o-mini",
        "usage": {"prompt_tokens": 100, "completion_tokens": 50}
    }

@pytest.fixture
def mock_litellm(mock_llm_response, monkeypatch):
    """Patch litellm.completion for deterministic tests."""
    mock = AsyncMock(return_value=mock_llm_response)
    monkeypatch.setattr("litellm.completion", mock)
    monkeypatch.setattr("litellm.acompletion", mock)
    return mock

@pytest.fixture
def temp_project(tmp_path):
    """Create temporary project structure."""
    (tmp_path / ".speckit").mkdir()
    (tmp_path / "specs").mkdir()
    return tmp_path
```

---

## Summary: Key Technical Decisions

| Area | Decision | Key Library |
|------|----------|-------------|
| LLM Provider | LiteLLM unified interface | `litellm>=1.40.0` |
| Structured Outputs | Instructor for Pydantic | `instructor>=1.0.0` |
| Configuration | Pydantic Settings | `pydantic-settings>=2.0` |
| CLI Framework | Typer with Rich | `typer>=0.12.0`, `rich>=13.0` |
| Templates | Jinja2 | `jinja2>=3.1` |
| MCP Server | FastMCP pattern | `mcp>=1.0.0` (optional) |
| Testing | pytest + mocking | `pytest>=8.0`, `pytest-asyncio` |
| Config Format | YAML | `pyyaml>=6.0` |

All decisions prioritize:
1. **Simplicity**: Minimal dependencies, clear patterns
2. **Flexibility**: Multi-provider support, customizable templates
3. **Reliability**: Type safety, validation, error handling
4. **Developer Experience**: Rich CLI, async support, clear docs
