# UVMGR Retrofit Summary

## Overview

Spec-kit has been retrofitted with best practices and architecture patterns from uvmgr, a mature DevX tool. This retrofit improves code organization, maintainability, and sets the foundation for future enhancements.

## What Was Integrated

### 1. **Shell Utilities Module** (`src/specify_cli/core/shell.py`)

Adapted from uvmgr's `core/shell.py`, providing consistent terminal output:

- `colour()` - Print colored text
- `colour_stderr()` - Print to stderr
- `dump_json()` - Pretty-print JSON with syntax highlighting
- `markdown()` - Render markdown
- `timed()` - Function timing decorator
- `rich_table()` - Quick table rendering
- `progress_bar()` - Context-manager progress bars
- `install_rich()` - Enable Rich tracebacks

**Benefits:**
- Consistent output formatting across the application
- Reduced code duplication in CLI commands
- Better error messages and visual feedback

### 2. **Process Utilities Module** (`src/specify_cli/core/process.py`)

New module for subprocess execution with logging:

- `run_command()` - Execute commands with optional output capture
- `run_logged()` - Execute with labeled logging

**Benefits:**
- Centralized subprocess management
- Consistent error handling
- Better logging integration

### 3. **Operations Layer** (`src/specify_cli/ops/`)

Extracted business logic from the CLI layer:

#### `process_mining.py`
Pure business logic functions for process mining operations:

- `load_event_log()` - Load XES/CSV event logs
- `save_model()` - Save Petri nets, BPMN, or process trees
- `discover_process_model()` - Discover models (5 algorithms)
- `conform_trace()` - Conformance checking
- `get_log_statistics()` - Event log analysis
- `convert_model()` - Format conversions
- `visualize_model()` - Generate visualizations
- `filter_log()` - Log filtering
- `sample_log()` - Log sampling

**Benefits:**
- Separation of concerns (CLI vs. business logic)
- Easier unit testing
- Reusable functions for programmatic use
- Better error handling at the operations level

### 4. **Core Package Structure**

```
src/specify_cli/
├── __init__.py              # Main CLI (current monolithic file)
├── core/
│   ├── __init__.py
│   ├── shell.py             # Rich output utilities (from uvmgr)
│   └── process.py           # Process execution helpers (NEW)
└── ops/
    ├── __init__.py
    └── process_mining.py    # Business logic for PM (NEW)
```

## Architecture Principles Adopted from UVMGR

### 1. **Three-Layer Architecture**

The foundation for scalability:

```
┌─────────────────────────┐
│  CLI Layer              │  ← Commands and user interaction
├─────────────────────────┤
│  Operations Layer       │  ← Business logic (newly extracted)
├─────────────────────────┤
│  Core Utilities Layer   │  ← Shared utilities (newly created)
└─────────────────────────┘
```

While the CLI is still monolithic in `__init__.py`, the ops and core layers are now modular and can be tested independently.

### 2. **Separation of Concerns**

- **CLI Layer** (`__init__.py`): User interaction, argument parsing, output formatting
- **Ops Layer** (`ops/`): Business logic, no dependencies on typer or CLI framework
- **Core Layer** (`core/`): Utilities used by all layers (shell output, process execution)

### 3. **Consistency Patterns**

- Unified output formatting via `colour()` and related functions
- Centralized process execution via `run_command()` and `run_logged()`
- Standardized error messages

## Next Steps for Further Improvements

### Phase 1: CLI Refactoring (Recommended)
Extract command handlers from `__init__.py` into separate modules:
- `commands/pm.py` - Process mining commands
- `commands/init.py` - Project initialization
- `commands/check.py` - Project checks

### Phase 2: Error Handling Framework (Recommended)
Adapt uvmgr's error handling patterns:
- Create `core/exceptions.py` with custom exception hierarchy
- Map subprocess errors to user-friendly messages
- Add telemetry-compatible exception tracking

### Phase 3: OpenTelemetry Integration (Optional)
Add observability following uvmgr's pattern:
- Install `opentelemetry-sdk` and exporters
- Create `core/instrumentation.py` and `core/telemetry.py`
- Decorate operations with `@instrument_command()` decorators
- Track metrics for performance monitoring

### Phase 4: Caching System (Optional)
Add operation result caching:
- Cache ggen generation results
- Cache GitHub API responses
- Use SHA1-based command result caching

## Usage Examples

### Using Shell Utilities

```python
from specify_cli.core import colour, dump_json, markdown

# Colored output
colour("Operation successful!", "green")
colour("This is an error", "red")

# JSON formatting
data = {"spec": "example", "status": "ready"}
dump_json(data)

# Markdown rendering
markdown("# Specification\nYour spec details here")
```

### Using Operations Layer

```python
from specify_cli.ops.process_mining import (
    load_event_log,
    discover_process_model,
    get_log_statistics,
    save_model,
)

# Load event log
log = load_event_log("events.xes")

# Get statistics
stats = get_log_statistics(log)
print(f"Traces: {stats['num_cases']}, Events: {stats['num_events']}")

# Discover model
model, model_type = discover_process_model(log, algorithm="inductive")

# Save result
save_model(model, "output.pnml", model_type=model_type)
```

### Using Process Utilities

```python
from specify_cli.core import run_logged

# Execute with logging
result = run_logged(
    ["ggen", "generate", "spec.rdf"],
    label="Generating spec",
    capture=True
)
print(result)
```

## Files Modified/Created

### Created
- `src/specify_cli/core/__init__.py` - Core utilities package
- `src/specify_cli/core/shell.py` - Shell utilities (from uvmgr)
- `src/specify_cli/core/process.py` - Process execution helpers
- `src/specify_cli/ops/__init__.py` - Operations layer package
- `src/specify_cli/ops/process_mining.py` - PM business logic
- `RETROFIT_SUMMARY.md` - This file

### Unchanged
- `src/specify_cli/__init__.py` - Main CLI (backward compatible)
- `pyproject.toml` - Dependencies (no changes needed)
- All tests and other files remain functional

## Compatibility

✅ **Backward Compatible**: All changes are additive. Existing code continues to work.

✅ **Gradual Migration**: You can use new utilities and ops layer without refactoring the entire CLI.

✅ **Optional Enhancements**: OTEL, error handling, and caching can be added incrementally.

## Benefits Summary

| Area | Before | After |
|------|--------|-------|
| **Code Organization** | Monolithic (2226 lines) | Modular (core + ops) |
| **Testability** | CLI-tied logic | Pure functions in ops layer |
| **Reusability** | CLI-specific | Programmatic API via ops |
| **Output Consistency** | Ad-hoc Rich usage | Unified utilities |
| **Maintainability** | Single large file | Organized by concern |
| **Extensibility** | Monolithic changes | Add new modules |

## References

- **UVMGR Repository**: `./vendors/uvmgr`
- **UVMGR Architecture**: 3-layer pattern (CLI → Ops → Runtime)
- **UVMGR Shell Utilities**: `vendors/uvmgr/src/uvmgr/core/shell.py`
- **UVMGR Operations Pattern**: `vendors/uvmgr/src/uvmgr/ops/`

---

**Status**: ✅ Complete - Ready for further enhancements

**Last Updated**: 2025-12-21
