# Data Model: Python Library with Universal LLM Support

**Feature**: 001-python-litellm-library
**Generated**: 2025-12-19
**Source**: [spec.md](spec.md) Key Entities section

## Overview

This document defines the Pydantic models that represent all artifacts in the spec-kit workflow. All models support:
- JSON serialization/deserialization
- Markdown export for human-readable files
- Schema validation for LLM structured outputs

## Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          Project                                 │
│  - path: Path                                                   │
│  - config: SpecKitConfig                                        │
└─────────────────────────────────────────────────────────────────┘
         │                      │
         │ 1:1                  │ 1:N
         ▼                      ▼
┌─────────────────┐    ┌─────────────────────────────────────────┐
│  Constitution   │    │                Feature                   │
│  - principles   │    │  - id: str (e.g., "001-feature-name")   │
│  - standards    │    │  - name: str                            │
│  - constraints  │    │  - status: FeatureStatus                │
└─────────────────┘    └─────────────────────────────────────────┘
                                │
                                │ 1:1 for each
                                ▼
         ┌──────────────────────┼──────────────────────┐
         │                      │                      │
         ▼                      ▼                      ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Specification  │───▶│  TechnicalPlan  │───▶│  TaskBreakdown  │
│  - user_stories │    │  - tech_stack   │    │  - tasks: []    │
│  - requirements │    │  - components   │    │  - dependencies │
│  - criteria     │    │  - data_model   │    │  - progress     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Core Enumerations

### Priority

```python
class Priority(str, Enum):
    """MoSCoW prioritization for requirements and user stories."""
    MUST = "must"       # P1 - Critical for MVP
    SHOULD = "should"   # P2 - Important but not blocking
    COULD = "could"     # P3 - Nice to have
    WONT = "wont"       # Explicitly excluded from scope
```

### TaskStatus

```python
class TaskStatus(str, Enum):
    """Status of implementation tasks."""
    PENDING = "pending"         # Not started
    IN_PROGRESS = "in_progress" # Currently being worked on
    COMPLETED = "completed"     # Done and validated
    BLOCKED = "blocked"         # Waiting on dependency
    SKIPPED = "skipped"         # Intentionally not done
```

### PhaseType

```python
class PhaseType(str, Enum):
    """Implementation phases for task organization."""
    SETUP = "setup"             # Project initialization
    TESTS = "tests"             # Test infrastructure
    CORE = "core"               # Core functionality
    INTEGRATION = "integration" # Component integration
    POLISH = "polish"           # Refinements and docs
```

### FeatureStatus

```python
class FeatureStatus(str, Enum):
    """Status of a feature in the spec-driven workflow."""
    DRAFT = "draft"             # Initial specification
    CLARIFIED = "clarified"     # Ambiguities resolved
    PLANNED = "planned"         # Technical plan complete
    TASKED = "tasked"           # Tasks generated
    IN_PROGRESS = "in_progress" # Implementation started
    COMPLETED = "completed"     # All tasks done
```

## Configuration Models

### LLMConfig

```python
class LLMConfig(BaseSettings):
    """LLM provider configuration via Pydantic Settings."""

    model: str = "gpt-4o-mini"  # LiteLLM model identifier
    api_key: Optional[str] = None  # Override (uses env vars by default)
    api_base: Optional[str] = None  # Custom API endpoint
    temperature: float = 0.7  # 0.0-2.0
    max_tokens: int = 4096
    timeout: int = 120  # seconds
    max_retries: int = 3
    fallback_models: list[str] = ["gpt-4o-mini", "claude-3-haiku-20240307"]
```

**Environment Variables**: `SPECKIT_MODEL`, `SPECKIT_API_KEY`, `SPECKIT_API_BASE`, `SPECKIT_TEMPERATURE`, `SPECKIT_MAX_TOKENS`, `SPECKIT_TIMEOUT`

### StorageConfig

```python
class StorageConfig(BaseSettings):
    """Artifact storage configuration."""

    backend: Literal["file"] = "file"  # Only file storage in v1
    base_dir: str = ".speckit"  # Project-relative directory
    specs_dir: str = "specs"  # Feature specifications directory
```

### SpecKitConfig

```python
class SpecKitConfig(BaseSettings):
    """Main configuration container."""

    llm: LLMConfig
    storage: StorageConfig
    project_path: Path
    language: str = "en"  # Output language preference
    verbose: bool = False
    debug: bool = False
```

**Precedence**: Programmatic > Config File > Environment Variables > Defaults

## Workflow Artifact Models

### Constitution

```python
class Constitution(BaseModel):
    """Project-level principles and standards."""

    project_name: str
    created_at: datetime
    updated_at: datetime
    version: str = "1.0.0"

    # Principle categories
    core_principles: list[str]      # Fundamental values
    quality_standards: list[str]    # Code/test quality rules
    testing_standards: list[str]    # Test coverage/types required
    tech_constraints: list[str]     # Technology restrictions
    ux_guidelines: list[str]        # User experience rules
    governance_rules: list[str]     # Change management rules
```

**Relationships**: One per Project. Referenced by all Specifications for compliance checking.

### UserStory

```python
class UserStory(BaseModel):
    """User story in standard format with acceptance criteria."""

    id: str                         # e.g., "US-001"
    as_a: str                       # User role
    i_want: str                     # Desired action
    so_that: str                    # Business value
    priority: Priority              # P1/P2/P3
    acceptance_criteria: list[str]  # Testable conditions
```

### FunctionalRequirement

```python
class FunctionalRequirement(BaseModel):
    """Functional requirement with rationale."""

    id: str                         # e.g., "FR-001"
    title: str
    description: str
    rationale: str                  # Why this is needed
    priority: Priority
    acceptance_criteria: list[str]
    related_stories: list[str]      # Links to UserStory.id
```

### Entity

```python
class Entity(BaseModel):
    """Domain entity for data modeling."""

    name: str
    description: str
    attributes: list[str]           # Field descriptions
    relationships: list[str]        # Links to other entities
```

### Specification

```python
class Specification(BaseModel):
    """Complete feature specification."""

    feature_name: str
    feature_id: str                 # e.g., "001-python-library"
    created_at: datetime
    version: str = "1.0.0"

    # Content sections
    overview: str
    problem_statement: str
    target_users: list[str]

    # Structured requirements
    user_stories: list[UserStory]
    functional_requirements: list[FunctionalRequirement]
    entities: list[Entity]

    # Constraints and scope
    assumptions: list[str]
    constraints: list[str]
    out_of_scope: list[str]
    success_criteria: list[str]

    # Clarification tracking
    clarifications_needed: list[str]  # Items needing resolution
    clarifications_resolved: list[dict]  # Q&A pairs
```

**Relationships**: Belongs to Feature. Input for TechnicalPlan generation.

### TechStack

```python
class TechStack(BaseModel):
    """Technology stack definition."""

    language: str                   # e.g., "Python 3.11"
    framework: str                  # e.g., "Typer"
    database: Optional[str]         # e.g., "PostgreSQL" or None
    orm: Optional[str]              # e.g., "SQLAlchemy" or None
    testing: str                    # e.g., "pytest"
    additional_tools: list[str]     # e.g., ["Rich", "Jinja2"]
```

### ArchitectureComponent

```python
class ArchitectureComponent(BaseModel):
    """Component in the system architecture."""

    name: str
    component_type: str             # e.g., "module", "service", "cli"
    description: str
    file_path: str                  # e.g., "src/speckit/llm.py"
    dependencies: list[str]         # Other component names
    public_interface: list[str]     # Exported functions/classes
```

### TechnicalPlan

```python
class TechnicalPlan(BaseModel):
    """Technical implementation plan."""

    feature_id: str
    created_at: datetime
    version: str = "1.0.0"

    # Technical decisions
    tech_stack: TechStack
    architecture_overview: str
    components: list[ArchitectureComponent]

    # Design artifacts
    data_model: str                 # Mermaid diagram or description
    file_structure: str             # Directory tree
    api_contracts: str              # API documentation reference

    # Risk management
    technical_risks: list[str]
    mitigation_strategies: list[str]
    research_notes: str             # Findings from Phase 0
```

**Relationships**: Derived from Specification. Input for TaskBreakdown generation.

### Task

```python
class Task(BaseModel):
    """Atomic implementation task."""

    id: str                         # e.g., "T-001"
    title: str
    description: str
    phase: PhaseType
    status: TaskStatus = TaskStatus.PENDING

    # Traceability
    user_story_id: Optional[str]    # Links to UserStory.id
    requirement_ids: list[str]      # Links to FunctionalRequirement.id

    # Execution details
    file_paths: list[str]           # Files to create/modify
    dependencies: list[str]         # Task IDs that must complete first
    is_parallel: bool = False       # Can run with other parallel tasks

    # Validation
    validation_criteria: list[str]  # How to verify completion
    estimated_complexity: str       # "low", "medium", "high"
```

### TaskBreakdown

```python
class TaskBreakdown(BaseModel):
    """Complete task breakdown for a feature."""

    feature_id: str
    created_at: datetime
    tasks: list[Task]

    # Dependency management
    dependency_graph: dict[str, list[str]]  # task_id -> dependent_task_ids

    # Progress tracking
    def get_tasks_by_phase(self, phase: PhaseType) -> list[Task]
    def get_next_tasks(self) -> list[Task]  # Ready to execute
    def mark_complete(self, task_id: str) -> None
    def get_progress(self) -> dict[str, int]  # Status counts
```

**Relationships**: Derived from TechnicalPlan. Contains ordered Tasks.

## LLM Response Models

### LLMResponse

```python
@dataclass
class LLMResponse:
    """Standard response from LLM operations."""

    content: str                    # Generated text
    model: str                      # Model that responded
    usage: dict[str, int]           # Token counts
    raw_response: Any               # Original API response
```

### GeneratedArtifact

```python
class GeneratedArtifact(BaseModel):
    """Result of an LLM-powered generation operation."""

    artifact_type: str              # "specification", "plan", "tasks"
    content: BaseModel              # The generated Pydantic model
    generation_time: float          # Seconds
    model_used: str
    tokens_used: int
    retries: int = 0                # Number of retry attempts
```

## Validation Rules

### Cross-Model Validation

1. **UserStory.id** must be unique within Specification
2. **FunctionalRequirement.related_stories** must reference valid UserStory.id values
3. **Task.dependencies** must reference valid Task.id values within same TaskBreakdown
4. **Task.user_story_id** must reference valid UserStory.id from source Specification
5. **Constitution.version** must follow semantic versioning

### Markdown Export Rules

All models implement `to_markdown() -> str`:
- Use GitHub-flavored Markdown
- Preserve section ordering from templates
- Include metadata header (branch, date, version)
- Support round-trip: `Model.from_markdown(model.to_markdown()) == model`

## Storage Patterns

### File Naming

| Artifact | Path Pattern | Format |
|----------|--------------|--------|
| Constitution | `.speckit/constitution.md` | Markdown |
| Config | `.speckit/config.yaml` | YAML |
| Specification | `specs/{feature_id}/spec.md` | Markdown |
| Plan | `specs/{feature_id}/plan.md` | Markdown |
| Tasks | `specs/{feature_id}/tasks.md` | Markdown |
| Research | `specs/{feature_id}/research.md` | Markdown |

### Versioning

Artifacts include version metadata. On regeneration:
1. Create backup: `{filename}.{timestamp}.bak`
2. Increment version in new file
3. Preserve manual edits where marked with `<!-- MANUAL -->`
