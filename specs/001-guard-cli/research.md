# Research: Guard CLI Implementation

**Feature**: 001-guard-cli  
**Date**: 2025-10-19  
**Status**: Complete

## Research Questions Resolved

### 1. CLI Framework Integration with Typer

**Question**: How to integrate guard commands as a command group in existing Typer CLI?

**Decision**: Use Typer's command groups with `@app.command()` decorators within a `guard_app = typer.Typer()` instance, then register with main app using `app.add_typer(guard_app, name="guard")`.

**Rationale**: 
- Typer already in use in specify-cli
- Command groups provide clean namespace separation (`specify guard types`, `specify guard create`)
- Consistent with existing CLI patterns in the project
- Type hints and auto-generated help work seamlessly

**Alternatives Considered**:
- Click framework: More boilerplate, less type-safe
- argparse: Too low-level for rich CLI experience
- Custom CLI parser: Reinventing the wheel

**References**:
- Typer documentation: https://typer.tiangolo.com/tutorial/subcommands/add-typer/
- Existing specify CLI code in src/specify_cli/__init__.py

---

### 2. Template Engine for Boilerplate Generation

**Question**: Which templating engine should generate the 200+ lines of opinionated boilerplate code?

**Decision**: Jinja2 template engine

**Rationale**:
- Industry standard for Python code generation
- Powerful template syntax (loops, conditionals, filters, macros)
- Can generate any text format (Python, JavaScript, YAML, JSON, Markdown)
- Excellent error messages for template debugging
- Widely known by developers (reduces onboarding friction)
- Supports template inheritance for guard type reusability

**Alternatives Considered**:
- String formatting/f-strings: Too limited for 200+ line templates
- Mako: Less popular, similar capabilities
- Mustache: Too logic-less for complex boilerplate
- Custom DSL: Unnecessary complexity

**Implementation Notes**:
- Templates stored in `.specify/guards/types/{guard-type}/templates/`
- Context variables: `guard_id`, `guard_name`, `feature_name`, `tech_stack`, `timestamp`
- Template naming: `{artifact}.{extension}.j2` (e.g., `test.py.j2`, `config.yaml.j2`)

---

### 3. Guard Registry Storage Format

**Question**: How to persist guard metadata (ID, type, name, command, timestamp, status)?

**Decision**: JSON file at `.guards/registry.json` per feature

**Rationale**:
- Simple, human-readable format
- Easy to parse/write with Python's `json` module
- Git-friendly (easy to diff, review changes)
- No external database dependency
- Feature-scoped (each feature has its own registry)
- Extensible schema for future metadata

**Alternatives Considered**:
- SQLite database: Overkill for simple key-value storage
- YAML: Less standard for data storage, parsing overhead
- TOML: Less common for runtime data
- Individual JSON files per guard: More I/O overhead

**Schema Design**:
```json
{
  "feature": "001-guard-cli",
  "guards": [
    {
      "id": "G001",
      "type": "unit-pytest",
      "name": "guard-commands",
      "command": "make test-guard-G001",
      "created": "2025-10-19T14:30:00Z",
      "status": "active",
      "files": ["tests/unit/guards/G001_guard_commands.py"],
      "metadata_file": ".guards/G001-metadata.json"
    }
  ],
  "next_id": 2
}
```

---

### 4. Guard ID Generation Strategy

**Question**: How to generate sequential guard IDs (G001, G002, G003) safely avoiding collisions?

**Decision**: Atomic increment of `next_id` counter in registry.json with file locking

**Rationale**:
- Sequential IDs are human-friendly and sortable
- Registry file provides single source of truth
- File locking prevents race conditions in concurrent guard creation
- Simple rollback on failure (ID not incremented if creation fails)

**Alternatives Considered**:
- UUIDs: Not human-friendly, hard to reference in tasks
- Timestamp-based IDs: Collision risk, not sortable
- Database sequences: Requires external dependency
- Git commit count: Fragile, depends on git state

**Implementation**:
```python
import fcntl  # Unix file locking
import msvcrt  # Windows file locking

def generate_guard_id(registry_path):
    with open(registry_path, 'r+') as f:
        # Lock file (cross-platform)
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Unix
        # msvcrt.locking(f.fileno(), msvcrt.LK_LOCK, 1)  # Windows
        
        registry = json.load(f)
        guard_id = f"G{registry['next_id']:03d}"
        registry['next_id'] += 1
        
        f.seek(0)
        json.dump(registry, f, indent=2)
        f.truncate()
        
        return guard_id
```

---

### 5. Makefile Update Strategy (Idempotent & Atomic)

**Question**: How to add guard targets to Makefile without corrupting existing content?

**Decision**: Marker-based insertion with backup and atomic write

**Rationale**:
- Markers (e.g., `# BEGIN GUARDS`, `# END GUARDS`) provide safe insertion points
- Atomic write (write to temp file, then rename) prevents corruption on failure
- Backup file created before modification for rollback
- Idempotent: Re-running guard create with same ID doesn't duplicate targets

**Alternatives Considered**:
- Append-only: Risk of duplicates, no structure
- Full Makefile generation: Loses manual customizations
- Separate Makefile.guards: Requires manual include
- Make include directive: Fragile across Make versions

**Implementation Pattern**:
```makefile
# Existing Makefile content...

# BEGIN GUARDS - Do not modify this marker
test-guard-G001:
\tpytest tests/unit/guards/G001_guard_commands.py

test-guard-G002:
\tpytest tests/api/guards/G002_user_endpoints.py
# END GUARDS - Do not modify this marker

# Rest of Makefile...
```

**Update Algorithm**:
1. Read Makefile into memory
2. Find BEGIN/END markers
3. Check if guard target already exists (idempotency)
4. If not exists, insert new target alphabetically
5. Write to `Makefile.tmp`
6. Rename `Makefile` to `Makefile.bak`
7. Rename `Makefile.tmp` to `Makefile`
8. On success, delete `Makefile.bak`

---

### 6. Guard Type Manifest Schema

**Question**: What metadata should guard-type.yaml contain?

**Decision**: YAML manifest with structured sections for metadata, dependencies, scaffolding, execution, and AI hints

**Schema**:
```yaml
name: unit-pytest
version: 1.0.0
description: |
  Opinionated unit test scaffolds using pytest with fixtures, mocks, and coverage.
  Optimized for AI agent consumption.
category: unit
author: Spec Kit Core Team
license: MIT

dependencies:
  runtime:
    - python: ">=3.11"
    - make: ">=4.0"
  packages:
    - pytest: ">=7.0"
    - pytest-mock: ">=3.10"
    - pytest-cov: ">=4.0"

compatibility:
  languages: [python]
  frameworks: [fastapi, flask, django, cli]

scaffolding:
  creates:
    - tests/unit/guards/{guard_id}_{name}.py
    - tests/unit/conftest.py
  updates:
    - Makefile

execution:
  command: "pytest tests/unit/guards/{guard_id}_{name}.py -v --cov"
  timeout: 60
  exit_codes:
    success: 0
    failure: 1

ai_hints:
  when_to_use: |
    Use unit-pytest guard for validating individual functions, classes, or modules.
    Best for: Pure functions, business logic, data transformations, CLI commands.
    Not suitable for: Database interactions (use database guard), API endpoints (use api guard).
  
  boilerplate_explanation: |
    Generates opinionated pytest test file with:
    - Test class structure
    - Fixtures for common objects
    - Mock/patch examples for dependencies
    - Parametrized test examples
    - Coverage assertions
    Assumes: Standard Python project structure, pytest installed.
```

**Rationale**:
- YAML is human-readable and supports multi-line strings
- Clear section separation (dependencies, scaffolding, execution, AI hints)
- AI hints help agents choose appropriate guard types
- Version field enables guard type evolution
- Compatibility field prevents misuse (e.g., Python guard for JavaScript project)

---

### 7. Guard Execution Timeout Handling

**Question**: How to enforce 300-second timeout on guard execution?

**Decision**: Use `subprocess.run(timeout=300)` with graceful error handling

**Rationale**:
- Python's subprocess module provides built-in timeout support
- Timeout raises `TimeoutExpired` exception for clean handling
- Configurable per-guard via manifest
- Prevents runaway tests from blocking CI/CD

**Implementation**:
```python
import subprocess

def execute_guard(guard_id, timeout=300):
    try:
        result = subprocess.run(
            ["make", f"test-guard-{guard_id}"],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False  # Don't raise on non-zero exit
        )
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "timed_out": False
        }
    except subprocess.TimeoutExpired as e:
        return {
            "exit_code": 2,  # Timeout error code
            "stdout": e.stdout.decode() if e.stdout else "",
            "stderr": e.stderr.decode() if e.stderr else "",
            "timed_out": True
        }
```

---

### 8. Cross-Platform Compatibility (Linux, macOS, Windows)

**Question**: How to ensure guard CLI works across all platforms?

**Decision**: Use pathlib for paths, subprocess for commands, conditional file locking

**Platform-Specific Concerns**:

**Path Handling**:
```python
from pathlib import Path

# Always use pathlib.Path for cross-platform paths
guard_registry = Path(".guards") / "registry.json"
```

**File Locking**:
```python
import platform

if platform.system() == "Windows":
    import msvcrt
    # Windows locking
else:
    import fcntl
    # Unix locking
```

**Makefile**:
- Make available on all platforms (GNU Make on Windows via WSL, chocolatey, or scoop)
- Use `.PHONY` targets to avoid file conflicts
- Avoid platform-specific shell commands in targets

**Line Endings**:
- Use `newline=None` in file operations to respect platform conventions
- Git configured with `core.autocrlf=input` for consistent repository line endings

---

## Technology Stack Summary

| Component | Technology | Version | Rationale |
|-----------|-----------|---------|-----------|
| CLI Framework | Typer | Latest | Already in use, type-safe |
| Terminal UI | Rich | Latest | Already in use, beautiful output |
| Templating | Jinja2 | >=3.0 | Industry standard, powerful |
| Manifest Format | YAML | PyYAML >=6.0 | Human-readable, multi-line support |
| Registry Format | JSON | stdlib json | Simple, git-friendly |
| Guard Execution | subprocess | stdlib | Built-in timeout, cross-platform |
| File Locking | fcntl/msvcrt | stdlib | Atomic ID generation |
| Testing | pytest | >=7.0 | Already in use |

---

## Implementation Priorities

### MVP (User Stories P1):
1. **Guard Create (US1)**: Core value - generate boilerplate
2. **Guard Run (US3)**: Critical - execute validation
3. **Guard Types (US2)**: Discovery - know what exists

### Post-MVP (User Stories P3-P4):
4. **Guard List (US4)**: Tracking - useful but not critical
5. **Guard Install (US5)**: Extensibility - future enhancement

---

## Risks & Mitigations

### Risk: Makefile Corruption
**Mitigation**: Atomic writes with backup, marker-based insertion, validation before write

### Risk: Concurrent Guard Creation (Race Conditions)
**Mitigation**: File locking on registry.json during ID generation

### Risk: Guard Type Scaffolder Crashes
**Mitigation**: Try/catch with rollback, clear error messages, validation before execution

### Risk: Cross-Platform Compatibility Issues
**Mitigation**: pathlib for paths, conditional file locking, avoid platform-specific commands

### Risk: Template Rendering Failures
**Mitigation**: Template validation on guard type installation, clear error messages with variable context

---

## Open Questions (None)

All technical decisions resolved. Ready for Phase 1 (Design & Contracts).
