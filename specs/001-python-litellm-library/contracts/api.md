# API Contract: speckit Python Library

**Feature**: 001-python-litellm-library
**Generated**: 2025-12-19
**Version**: 0.1.0

## Overview

This document defines the public API contract for the `speckit` Python library. All public interfaces are guaranteed stable within major versions following semantic versioning.

## Installation

```bash
# Core library
pip install speckit-ai

# With MCP server support
pip install speckit-ai[mcp]

# Development dependencies
pip install speckit-ai[dev]
```

## Quick Start

```python
from speckit import SpecKit
from speckit.config import LLMConfig

# Initialize with default configuration (uses env vars)
kit = SpecKit(project_path="./my-project")

# Or with explicit configuration
kit = SpecKit(
    project_path="./my-project",
    llm_config=LLMConfig(model="ollama/llama3.1")
)

# Generate a specification
spec = kit.specify("Add user authentication with OAuth2 support")
print(spec.to_markdown())
```

---

## Module: `speckit`

### Class: `SpecKit`

Main orchestrator class providing access to all workflow phases.

#### Constructor

```python
def __init__(
    self,
    project_path: str | Path,
    config: Optional[SpecKitConfig] = None,
    llm_config: Optional[LLMConfig] = None
) -> None
```

**Parameters**:
- `project_path`: Root directory of the project
- `config`: Full configuration object (optional)
- `llm_config`: LLM-specific configuration (optional, overrides config.llm)

**Behavior**:
- Loads configuration from `.speckit/config.yaml` if exists
- Falls back to environment variables
- Creates `.speckit/` directory if not exists

#### Methods

##### `constitution()`

```python
def constitution(
    self,
    project_name: str,
    principles: Optional[list[str]] = None,
    interactive: bool = True
) -> Constitution
```

Create or update project constitution.

**Parameters**:
- `project_name`: Name for the constitution
- `principles`: Optional seed principles (LLM generates if not provided)
- `interactive`: If True, prompts for principle refinement

**Returns**: `Constitution` model

**Example**:
```python
constitution = kit.constitution(
    project_name="My Project",
    principles=["Test-first development", "Simple over complex"]
)
```

##### `specify()`

```python
def specify(
    self,
    feature_description: str,
    feature_id: Optional[str] = None
) -> Specification
```

Generate a feature specification from natural language description.

**Parameters**:
- `feature_description`: Natural language description of the feature
- `feature_id`: Optional custom ID (auto-generated if not provided)

**Returns**: `Specification` model

**Example**:
```python
spec = kit.specify(
    "Allow users to export reports as PDF with custom headers"
)
```

##### `clarify()`

```python
def clarify(
    self,
    specification: Specification,
    max_questions: int = 5
) -> tuple[Specification, list[ClarificationQuestion]]
```

Identify ambiguities and generate clarification questions.

**Parameters**:
- `specification`: Specification to analyze
- `max_questions`: Maximum questions to generate

**Returns**: Tuple of (updated spec, questions needing answers)

**Example**:
```python
updated_spec, questions = kit.clarify(spec)
for q in questions:
    print(f"Q: {q.question}")
    # Get user input and apply answer
    updated_spec = kit.apply_clarification(updated_spec, q.id, answer)
```

##### `plan()`

```python
def plan(
    self,
    specification: Specification,
    tech_stack: Optional[TechStack] = None
) -> TechnicalPlan
```

Generate technical implementation plan.

**Parameters**:
- `specification`: Specification to plan for
- `tech_stack`: Optional constraints on technology choices

**Returns**: `TechnicalPlan` model

**Example**:
```python
plan = kit.plan(spec, tech_stack=TechStack(language="Python 3.11"))
```

##### `tasks()`

```python
def tasks(
    self,
    plan: TechnicalPlan,
    parallel_friendly: bool = True
) -> TaskBreakdown
```

Generate implementation tasks from plan.

**Parameters**:
- `plan`: Technical plan to break down
- `parallel_friendly`: If True, maximizes parallel task opportunities

**Returns**: `TaskBreakdown` model

**Example**:
```python
breakdown = kit.tasks(plan)
for task in breakdown.get_next_tasks():
    print(f"Ready: {task.title}")
```

##### `analyze()`

```python
def analyze(
    self,
    specification: Specification,
    plan: TechnicalPlan,
    tasks: TaskBreakdown
) -> AnalysisReport
```

Check consistency across all artifacts.

**Parameters**:
- `specification`: Source specification
- `plan`: Implementation plan
- `tasks`: Task breakdown

**Returns**: `AnalysisReport` with issues and recommendations

**Example**:
```python
report = kit.analyze(spec, plan, breakdown)
if report.has_issues:
    print(report.to_markdown())
```

#### Async Variants

All methods have async variants with `_async` suffix:

```python
spec = await kit.specify_async("Feature description")
plan = await kit.plan_async(spec)
tasks = await kit.tasks_async(plan)
```

---

## Module: `speckit.config`

### Class: `LLMConfig`

```python
class LLMConfig(BaseSettings):
    model: str = "gpt-4o-mini"
    api_key: Optional[str] = None
    api_base: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 4096
    timeout: int = 120
    max_retries: int = 3
    fallback_models: list[str] = ["gpt-4o-mini", "claude-3-haiku-20240307"]
```

**Environment Variables**:
- `SPECKIT_MODEL`
- `SPECKIT_API_KEY` (or provider-specific: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`)
- `SPECKIT_API_BASE`
- `SPECKIT_TEMPERATURE`
- `SPECKIT_MAX_TOKENS`

### Class: `SpecKitConfig`

```python
class SpecKitConfig(BaseSettings):
    llm: LLMConfig
    storage: StorageConfig
    project_path: Path
    language: str = "en"
    verbose: bool = False
    debug: bool = False
```

**Factory Methods**:

```python
# Load from project directory
config = SpecKitConfig.from_project("./my-project")

# Save to project
config.save()
```

---

## Module: `speckit.llm`

### Class: `LiteLLMProvider`

Low-level LLM access for custom integrations.

```python
from speckit.llm import LiteLLMProvider
from speckit.config import LLMConfig

provider = LiteLLMProvider(LLMConfig(model="ollama/llama3.1"))

# Simple completion
response = provider.complete(
    prompt="Summarize this feature",
    system="You are a technical writer"
)
print(response.content)

# Structured output
from speckit.schemas import UserStory

story = provider.complete_structured(
    prompt="Generate a user story for login",
    response_model=UserStory
)
print(story.as_a, story.i_want)

# Streaming
for chunk in provider.stream("Generate a long description"):
    print(chunk, end="")
```

#### Methods

```python
def complete(
    self,
    prompt: str,
    system: Optional[str] = None,
    **kwargs
) -> LLMResponse

async def complete_async(
    self,
    prompt: str,
    system: Optional[str] = None,
    **kwargs
) -> LLMResponse

def complete_structured(
    self,
    prompt: str,
    response_model: Type[T],
    system: Optional[str] = None,
    **kwargs
) -> T

async def complete_structured_async(
    self,
    prompt: str,
    response_model: Type[T],
    system: Optional[str] = None,
    **kwargs
) -> T

def stream(
    self,
    prompt: str,
    system: Optional[str] = None,
    **kwargs
) -> Iterator[str]

async def stream_async(
    self,
    prompt: str,
    system: Optional[str] = None,
    **kwargs
) -> AsyncIterator[str]

@staticmethod
def list_models() -> list[str]
```

---

## Module: `speckit.schemas`

All Pydantic models are exported from this module.

```python
from speckit.schemas import (
    # Enums
    Priority,
    TaskStatus,
    PhaseType,
    FeatureStatus,

    # Config models
    LLMConfig,
    StorageConfig,
    SpecKitConfig,

    # Workflow artifacts
    Constitution,
    UserStory,
    FunctionalRequirement,
    Entity,
    Specification,
    TechStack,
    ArchitectureComponent,
    TechnicalPlan,
    Task,
    TaskBreakdown,

    # Response models
    LLMResponse,
    GeneratedArtifact,
    AnalysisReport,
    ClarificationQuestion,
)
```

All models support:

```python
# JSON serialization
json_str = model.model_dump_json()
model = ModelClass.model_validate_json(json_str)

# Markdown export
markdown = model.to_markdown()

# Schema export (for documentation)
schema = ModelClass.model_json_schema()
```

---

## Module: `speckit.storage`

### Class: `FileStorage`

```python
from speckit.storage import FileStorage

storage = FileStorage(project_path="./my-project")

# Save artifact
storage.save_specification(spec, feature_id="001-my-feature")
storage.save_plan(plan, feature_id="001-my-feature")
storage.save_tasks(tasks, feature_id="001-my-feature")

# Load artifact
spec = storage.load_specification(feature_id="001-my-feature")
plan = storage.load_plan(feature_id="001-my-feature")

# List features
features = storage.list_features()  # ["001-feature", "002-other"]
```

---

## CLI Interface

All library functions are accessible via CLI:

```bash
# Initialize project
speckit init

# Create constitution
speckit constitution "My Project" --principles "Test-first"

# Generate specification
speckit specify "Add user authentication" --feature-id 001-auth

# Clarify specification
speckit clarify --feature 001-auth

# Generate plan
speckit plan --feature 001-auth

# Generate tasks
speckit tasks --feature 001-auth

# Analyze artifacts
speckit analyze --feature 001-auth

# Configuration
speckit config set model ollama/llama3.1
speckit config show
```

**Output Modes**:

```bash
# Human-readable (default)
speckit specify "Feature" --format rich

# JSON output
speckit specify "Feature" --format json

# Quiet (errors only)
speckit specify "Feature" --quiet
```

---

## Error Handling

### Exception Hierarchy

```python
from speckit.exceptions import (
    SpecKitError,           # Base exception
    ConfigurationError,     # Invalid configuration
    LLMError,              # LLM provider errors
    LLMRateLimitError,     # Rate limit hit (retryable)
    LLMTimeoutError,       # Request timeout (retryable)
    ValidationError,       # Schema validation failed
    StorageError,          # File I/O errors
    WorkflowError,         # Invalid workflow state
)
```

### Error Recovery

```python
from speckit.exceptions import LLMRateLimitError

try:
    spec = kit.specify("Feature")
except LLMRateLimitError as e:
    print(f"Rate limited, retry after {e.retry_after}s")
    # Library automatically retries with fallback models
```

---

## MCP Server

When installed with `[mcp]` extra:

```bash
# Start MCP server
python -m speckit.mcp

# Or via CLI
speckit mcp serve
```

**Exposed Tools**:

| Tool | Description |
|------|-------------|
| `speckit_specify` | Generate specification from description |
| `speckit_clarify` | Identify clarification questions |
| `speckit_plan` | Generate technical plan |
| `speckit_tasks` | Generate task breakdown |
| `speckit_analyze` | Check artifact consistency |
| `speckit_list_features` | List project features |
| `speckit_get_artifact` | Retrieve specific artifact |

**Claude Desktop Configuration** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "speckit": {
      "command": "python",
      "args": ["-m", "speckit.mcp"],
      "cwd": "/path/to/project"
    }
  }
}
```

---

## Versioning

This library follows semantic versioning:

- **Major**: Breaking API changes
- **Minor**: New features, backward compatible
- **Patch**: Bug fixes, backward compatible

Deprecated features are marked with `@deprecated` decorator and removed in next major version.
