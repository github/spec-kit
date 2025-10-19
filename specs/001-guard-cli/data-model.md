# Data Model: Guard CLI Implementation

**Feature**: 001-guard-cli  
**Date**: 2025-10-19

## Entity Relationship Diagram

```
┌─────────────────┐       1:N        ┌──────────────────┐
│  GuardRegistry  │◄─────────────────│      Guard       │
│                 │                  │                  │
│ - feature       │                  │ - id (G001)      │
│ - guards[]      │                  │ - type           │
│ - next_id       │                  │ - name           │
└─────────────────┘                  │ - command        │
                                     │ - created        │
                                     │ - status         │
                                     │ - files[]        │
                                     └──────────────────┘
                                              │
                                              │ references
                                              ▼
┌─────────────────┐       1:N        ┌──────────────────┐
│   GuardType     │◄─────────────────│      Guard       │
│                 │                  └──────────────────┘
│ - name          │
│ - version       │
│ - category      │
│ - manifest      │───────► GuardTypeManifest
│ - scaffolder    │───────► GuardScaffolder
│ - templates[]   │───────► Template[]
│ - validator     │───────► GuardValidator
└─────────────────┘
```

## Entities

### 1. GuardRegistry

Represents the central registry file (`.guards/registry.json`) that tracks all guards for a feature.

**Attributes**:
- `feature` (string): Feature identifier (e.g., "001-guard-cli")
- `guards` (array): List of Guard objects
- `next_id` (integer): Counter for sequential ID generation

**Relationships**:
- Has many Guards (1:N)

**Validation Rules**:
- `feature` must match current git branch or SPECIFY_FEATURE env variable
- `next_id` must always be greater than maximum existing guard ID
- `guards` array must not contain duplicate IDs

**File Location**: `.guards/registry.json`

**State Transitions**:
- Created: When first guard is created in a feature
- Updated: When guard added, removed, or status changed
- Deleted: When feature branch is deleted (cleanup)

**Example**:
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

### 2. Guard

Represents a specific validation checkpoint instance.

**Attributes**:
- `id` (string): Sequential identifier (G001, G002, etc.)
- `type` (string): Guard type name (e.g., "unit-pytest", "api", "docker-playwright")
- `name` (string): Human-readable name (e.g., "user-endpoints", "checkout-flow")
- `command` (string): Makefile target to execute (e.g., "make test-guard-G001")
- `created` (string): ISO 8601 timestamp of creation
- `status` (enum): "active", "disabled", "deprecated"
- `files` (array): List of file paths generated for this guard
- `metadata_file` (string): Path to detailed metadata JSON

**Relationships**:
- Belongs to GuardRegistry (N:1)
- References GuardType (N:1)

**Validation Rules**:
- `id` must match pattern `G\d{3}` (G001, G002, ... G999)
- `type` must reference existing GuardType
- `name` must be kebab-case lowercase alphanumeric with hyphens
- `command` must be executable via subprocess
- `created` must be valid ISO 8601 timestamp
- `status` must be one of: "active", "disabled", "deprecated"
- `files` must all exist on filesystem

**State Transitions**:
- Created → Active: When guard successfully created
- Active → Disabled: When guard temporarily turned off
- Active → Deprecated: When guard type upgraded or replaced
- Disabled → Active: When guard re-enabled

**Metadata File Example** (`.guards/G001-metadata.json`):
```json
{
  "id": "G001",
  "type": "unit-pytest",
  "type_version": "1.0.0",
  "name": "guard-commands",
  "command": "make test-guard-G001",
  "created": "2025-10-19T14:30:00Z",
  "created_by": "opencode",
  "status": "active",
  "files": [
    "tests/unit/guards/G001_guard_commands.py"
  ],
  "last_executed": "2025-10-19T15:00:00Z",
  "last_result": "pass",
  "execution_count": 5,
  "average_duration_ms": 1250
}
```

---

### 3. GuardType

Represents a reusable guard template package.

**Attributes**:
- `name` (string): Guard type identifier (e.g., "unit-pytest", "api")
- `version` (string): Semantic version (e.g., "1.0.0")
- `category` (enum): "unit", "integration", "e2e", "performance", "security", "lint", "schema", "database"
- `manifest` (GuardTypeManifest): Metadata from guard-type.yaml
- `scaffolder` (GuardScaffolder): Code generation logic
- `templates` (array): Jinja2 template files
- `validator` (GuardValidator): Execution and result parsing logic

**Relationships**:
- Has many Guards (1:N)
- Composed of GuardTypeManifest, GuardScaffolder, Templates, GuardValidator

**Validation Rules**:
- `name` must be unique within guard type registry
- `version` must follow semantic versioning (MAJOR.MINOR.PATCH)
- `category` must be one of defined enums
- `manifest` must be valid YAML with required fields
- `scaffolder` must implement GuardScaffolder interface
- `templates` directory must contain at least one .j2 file
- `validator` must be executable

**File Structure**:
```
.specify/guards/types/{name}/
├── guard-type.yaml        # Manifest
├── scaffolder.py          # Code generator
├── templates/             # Jinja2 templates
│   ├── test.py.j2
│   └── config.yaml.j2
├── validator.py           # Execution logic
├── README.md              # AI-optimized documentation
└── example/               # Reference implementation
    └── sample_test.py
```

---

### 4. GuardTypeManifest

Represents metadata from guard-type.yaml file.

**Attributes**:
- `name` (string): Guard type name
- `version` (string): Semantic version
- `description` (string): Multi-line description
- `category` (string): Guard category
- `author` (string): Author/organization
- `license` (string): License identifier (e.g., "MIT")
- `dependencies` (object): Runtime and package dependencies
- `compatibility` (object): Language and framework compatibility
- `scaffolding` (object): Files created/updated specification
- `execution` (object): Command, timeout, exit codes
- `ai_hints` (object): AI-specific guidance

**Validation Rules**:
- `name` must match directory name
- `version` must be valid semver
- `dependencies.runtime` must specify version constraints
- `dependencies.packages` must be installable
- `compatibility.languages` must be supported language identifiers
- `execution.command` must be valid shell command
- `execution.timeout` must be positive integer
- `ai_hints` must contain `when_to_use` and `boilerplate_explanation`

**Example** (from unit-pytest guard type):
```yaml
name: unit-pytest
version: 1.0.0
description: |
  Opinionated unit test scaffolds using pytest.
category: unit
author: Spec Kit Core Team
license: MIT

dependencies:
  runtime:
    - python: ">=3.11"
  packages:
    - pytest: ">=7.0"
    - pytest-mock: ">=3.10"

compatibility:
  languages: [python]
  frameworks: [fastapi, flask, django, cli]

scaffolding:
  creates:
    - tests/unit/guards/{guard_id}_{name}.py
  updates:
    - Makefile

execution:
  command: "pytest tests/unit/guards/{guard_id}_{name}.py -v"
  timeout: 60
  exit_codes:
    success: 0
    failure: 1

ai_hints:
  when_to_use: |
    Use for validating individual functions or classes.
  boilerplate_explanation: |
    Generates pytest test file with fixtures and mocks.
```

---

### 5. GuardScaffolder

Abstract base class for guard type code generators.

**Interface**:
```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List

class GuardScaffolder(ABC):
    def __init__(self, guard_id: str, name: str, guard_type: str, feature_dir: Path):
        self.guard_id = guard_id
        self.name = name
        self.guard_type = guard_type
        self.feature_dir = feature_dir
    
    @abstractmethod
    def scaffold(self) -> Dict[str, any]:
        """
        Generate boilerplate code for this guard.
        
        Returns:
            {
                'guard_id': str,
                'files_created': List[Path],
                'command': str,
                'next_steps': str
            }
        """
        pass
    
    def render_template(self, template_name: str, context: Dict) -> str:
        """Render Jinja2 template with context"""
        pass
    
    def create_file(self, path: Path, content: str) -> None:
        """Create file with content, creating parent directories"""
        pass
    
    def update_makefile(self, target_name: str, target_command: str) -> None:
        """Add target to Makefile idempotently"""
        pass
```

**Implementations**:
- UnitPytestScaffolder (unit-pytest guard type)
- APIScaffolder (api guard type)
- DatabaseScaffolder (database guard type)
- DockerPlaywrightScaffolder (docker-playwright guard type)
- LintRuffScaffolder (lint-ruff guard type)

---

### 6. GuardValidator

Executable that runs guard tests and parses results.

**Interface**:
```python
from abc import ABC, abstractmethod
from typing import Dict

class GuardValidator(ABC):
    def __init__(self, guard_id: str, command: str, timeout: int = 300):
        self.guard_id = guard_id
        self.command = command
        self.timeout = timeout
    
    @abstractmethod
    def execute(self) -> Dict[str, any]:
        """
        Execute guard validation.
        
        Returns:
            {
                'exit_code': int,
                'passed': bool,
                'stdout': str,
                'stderr': str,
                'duration_ms': int,
                'tests_run': int,
                'tests_passed': int,
                'tests_failed': int,
                'timed_out': bool
            }
        """
        pass
    
    def parse_output(self, stdout: str, stderr: str) -> Dict:
        """Parse test framework output into structured results"""
        pass
```

---

## Data Flow

### Guard Creation Flow

```
User: specify guard create --type api --name user-endpoints
  ↓
CLI: Parse arguments
  ↓
Registry: Load .guards/registry.json (with file lock)
  ↓
Registry: Generate next guard ID (G001)
  ↓
GuardType: Load guard type (api)
  ↓
Scaffolder: Instantiate APIScaffolder(G001, user-endpoints)
  ↓
Scaffolder: Render templates (test.py.j2, schema.json.j2)
  ↓
Scaffolder: Create files (tests/api/guards/G001_user_endpoints.py)
  ↓
Scaffolder: Update Makefile (add test-guard-G001 target)
  ↓
Registry: Add guard entry
  ↓
Registry: Increment next_id
  ↓
Registry: Save registry.json (unlock file)
  ↓
CLI: Output success message with next steps
```

### Guard Execution Flow

```
User: specify guard run G001
  ↓
CLI: Parse guard ID
  ↓
Registry: Load .guards/registry.json
  ↓
Registry: Find guard by ID
  ↓
Validator: Instantiate validator for guard type
  ↓
Validator: Execute command (make test-guard-G001)
  ↓
Validator: Capture stdout/stderr
  ↓
Validator: Parse output (test counts, failures)
  ↓
Validator: Return structured result
  ↓
Registry: Update last_executed, last_result
  ↓
CLI: Format output (PASS/FAIL, test details)
  ↓
CLI: Exit with appropriate code (0 = pass, 1 = fail, 2 = error)
```

---

## Storage Locations

| Entity | Storage | Format | Scope |
|--------|---------|--------|-------|
| GuardRegistry | `.guards/registry.json` | JSON | Per feature |
| Guard Metadata | `.guards/{id}-metadata.json` | JSON | Per guard |
| GuardType | `.specify/guards/types/{name}/` | Directory | Global (project) |
| GuardTypeManifest | `.specify/guards/types/{name}/guard-type.yaml` | YAML | Per guard type |
| GuardScaffolder | `.specify/guards/types/{name}/scaffolder.py` | Python | Per guard type |
| Templates | `.specify/guards/types/{name}/templates/*.j2` | Jinja2 | Per guard type |
| GuardValidator | `.specify/guards/types/{name}/validator.py` | Python | Per guard type |

---

## Constraints & Invariants

1. **Guard ID Uniqueness**: No two guards in the same feature can have the same ID
2. **Sequential IDs**: Guard IDs must be sequential (no gaps unless guard deleted)
3. **Type Existence**: Guard type must exist before guard can be created
4. **File Consistency**: All files in `Guard.files[]` must exist
5. **Makefile Sync**: Every active guard must have corresponding Makefile target
6. **Registry Atomicity**: Registry updates must be atomic (file locking)
7. **Version Compatibility**: Guard type version must be compatible with current Python/package versions
8. **Status Validity**: Guard status must be valid enum value
9. **Command Executability**: Guard command must be executable via subprocess
10. **Timeout Bounds**: Guard timeout must be between 1 and 3600 seconds
