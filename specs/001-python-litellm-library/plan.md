# Implementation Plan: Python Library with Universal LLM Support

**Branch**: `001-python-litellm-library` | **Date**: 2025-12-19 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-python-litellm-library/spec.md`

## Summary

Transform spec-kit from a Markdown-template-based toolkit into a standalone Python library with programmatic API, supporting 100+ LLM providers via LiteLLM. The library preserves the proven spec-driven workflow (Constitution, Specify, Clarify, Plan, Tasks, Implement) while adding automation capabilities through structured outputs (Pydantic), a modern CLI (Typer/Rich), and MCP server integration for AI assistants.

## Technical Context

**Language/Version**: Python 3.11+ (required for modern type hints, match statements, and performance improvements)
**Primary Dependencies**: LiteLLM (multi-provider LLM), Pydantic/pydantic-settings (schemas/config), Instructor (structured outputs), Typer (CLI), Rich (formatting), Jinja2 (templates), PyYAML (config), MCP (optional - AI assistant integration)
**Storage**: File-based (Markdown for artifacts, YAML for config) - no database required
**Testing**: pytest with pytest-asyncio for async operations, pytest-cov for coverage
**Target Platform**: Cross-platform (Linux, macOS, Windows) - Python-based CLI and library
**Project Type**: Single project - Python library with CLI entry point
**Performance Goals**: <5s for typical LLM-powered operations (excluding LLM response time), <100ms for file I/O operations, streaming support for long operations
**Constraints**: Offline-capable with local LLMs (Ollama), no API keys in artifacts, backward compatibility with existing spec-kit Markdown formats
**Scale/Scope**: Single-developer workflow focus, support 10+ LLM providers, 6 workflow phases, 8 user stories

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Since the project constitution template is not yet configured for this project, the following standard software engineering principles apply:

| Principle | Status | Evidence |
|-----------|--------|----------|
| **Library-First** | PASS | Core functionality exposed as importable Python library before CLI wrapping |
| **CLI Interface** | PASS | Typer CLI exposes all library functions with JSON + human-readable output |
| **Test-First** | PASS | pytest test suite required for all core modules; tests organized by type |
| **Integration Testing** | PASS | Contract tests for LLM provider interface, integration tests for workflow phases |
| **Observability** | PASS | Structured logging via Rich, clear error messages with actionable guidance |
| **Simplicity** | PASS | Single project structure, no microservices, file-based storage only |

**Gate Result**: PASS - No violations requiring justification.

## Project Structure

### Documentation (this feature)

```text
specs/001-python-litellm-library/
├── spec.md              # Feature specification (complete)
├── plan.md              # This file
├── research.md          # Phase 0 output - technology research
├── data-model.md        # Phase 1 output - entity schemas
├── quickstart.md        # Phase 1 output - developer onboarding
├── contracts/           # Phase 1 output - API contracts
│   └── api.md           # Public Python API documentation
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
└── speckit/
    ├── __init__.py              # Package exports
    ├── speckit.py               # Main SpecKit class (orchestrator)
    ├── config.py                # Configuration management (Pydantic Settings)
    ├── llm.py                   # LiteLLMProvider wrapper
    ├── schemas.py               # Pydantic models for all artifacts
    ├── cli.py                   # Typer CLI application
    │
    ├── core/                    # Workflow phase implementations
    │   ├── __init__.py
    │   ├── constitution.py      # ConstitutionManager
    │   ├── specification.py     # SpecificationBuilder
    │   ├── clarifier.py         # ClarificationEngine
    │   ├── planner.py           # TechnicalPlanner
    │   ├── tasker.py            # TaskGenerator
    │   ├── implementer.py       # ImplementationTracker
    │   └── analyzer.py          # ConsistencyAnalyzer
    │
    ├── storage/                 # Artifact persistence
    │   ├── __init__.py
    │   ├── base.py              # Abstract storage interface
    │   └── file_storage.py      # Markdown file storage implementation
    │
    ├── templates/               # Jinja2 prompt templates
    │   ├── __init__.py
    │   ├── constitution.jinja2
    │   ├── specification.jinja2
    │   ├── clarify.jinja2
    │   ├── plan.jinja2
    │   ├── tasks.jinja2
    │   └── analyze.jinja2
    │
    └── mcp/                     # MCP server (optional dependency)
        ├── __init__.py
        ├── __main__.py          # python -m speckit.mcp
        └── server.py            # MCP tool definitions

tests/
├── __init__.py
├── conftest.py                  # Shared fixtures
├── unit/                        # Unit tests (mocked dependencies)
│   ├── __init__.py
│   ├── test_config.py
│   ├── test_llm.py
│   ├── test_schemas.py
│   └── test_storage.py
├── integration/                 # Integration tests (real components)
│   ├── __init__.py
│   ├── test_workflow.py         # End-to-end workflow
│   └── test_cli.py              # CLI invocation tests
└── contract/                    # Contract tests (LLM provider interface)
    ├── __init__.py
    └── test_llm_providers.py

examples/
├── basic_usage.py               # Minimal example
├── multi_provider.py            # LLM provider switching
├── custom_templates.py          # Template customization
└── automation_pipeline.py       # CI/CD integration example
```

**Structure Decision**: Single project structure selected. The library (`src/speckit/`) is self-contained with clear module boundaries. The existing `src/specify_cli/` remains separate as the project initialization tool; the new `src/speckit/` implements the spec-driven workflow as an importable library.

## Complexity Tracking

> No violations requiring justification - design follows simplicity principles.

| Aspect | Decision | Rationale |
|--------|----------|-----------|
| Single package | `src/speckit/` | Simpler than monorepo; all workflow phases in one installable package |
| File storage only | No SQLite option in v1 | YAGNI - Markdown files sufficient, integrates with Git workflows |
| Sync-first API | Async as secondary | Most CLI usage is synchronous; async provided for advanced integrations |
| Template-based prompts | Jinja2 files | Customizable, maintainable, separates prompts from code logic |
