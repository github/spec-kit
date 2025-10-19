# Custom Guard Types Architecture

## Overview

Guard types come in two flavors:
- **Official types** (`.specify/guards/types/`) - Provided by spec-kit, updated on `specify init`
- **Custom types** (`.specify/guards/types-custom/`) - User-defined, preserved across updates

## Directory Structure

```
.specify/guards/
├── types/              # Official (replaceable on update)
│   ├── api/
│   ├── database/
│   ├── docker-playwright/
│   ├── lint-ruff/
│   └── unit-pytest/
├── types-custom/       # Custom (preserved)
│   ├── my-type/
│   │   ├── guard-type.yaml
│   │   ├── scaffolder.py
│   │   └── templates/
│   └── README.md
├── list/               # Guard instances (G001.json, etc.)
├── history/            # Execution logs
└── index.json          # ID counter
```

## Creating Custom Guard Types

### Quick Start

```bash
specify guard create-type --name my-validation --category validation --description "My custom validation"
```

This creates:
- `types-custom/my-validation/guard-type.yaml` - Type manifest
- `types-custom/my-validation/scaffolder.py` - Scaffolding logic
- `types-custom/my-validation/templates/test.py.j2` - Template example

### Manifest Format (guard-type.yaml)

```yaml
name: my-validation
version: 1.0.0
category: validation
description: |
  Custom validation for my specific needs

ai_hints:
  when_to_use: "Use when AI agents need to validate X"
  boilerplate_explanation: "Generates Y test files with Z setup"

dependencies:
  tools: []
  python_packages: []

scaffolder_class: MyValidationScaffolder
```

### Scaffolder Implementation

```python
from pathlib import Path
from specify_cli.guards.scaffolder import BaseScaffolder

class MyValidationScaffolder(BaseScaffolder):
    def scaffold(self):
        # Use self.render_template() to generate files
        test_file = self.project_root / "tests" / f"{self.guard_id}_{self.name}.py"
        test_file.parent.mkdir(parents=True, exist_ok=True)
        
        content = self.render_template(
            "test.py.j2",
            guard_id=self.guard_id,
            name=self.name
        )
        
        test_file.write_text(content)
        
        return {
            "files_created": [str(test_file)],
            "command": f"python {test_file}",
            "next_steps": f"Created {self.guard_type} guard {self.guard_id}"
        }
```

## Using Custom Types

Custom types work identically to official types:

```bash
# List all types (official + custom)
specify guard types

# Create guard using custom type
specify guard create --type my-validation --name test-guard

# Run guard
specify guard run G001
```

## Update Behavior

When running `specify init`:
- **types/** is deleted and replaced with latest official types
- **types-custom/** is never touched - all custom types preserved
- **list/**, **history/**, **index.json** are preserved

## Implementation Details

### GuardType.list_types()
Scans both `types/` and `types-custom/` directories, returning combined list.

### GuardType.load_type()
Checks `types/` first, then `types-custom/`, returning first match.

### GuardType.get_all_types_with_descriptions()
Returns all types with `source` field indicating "official" or "custom".

### Build Script
`.github/workflows/scripts/create-release-packages.sh`:
- Copies `guards/types/*` → `.specify/guards/types/`
- Creates `.specify/guards/types-custom/` with README
- Never modifies existing `types-custom/` content

## AI Agent Integration

Command templates automatically load both official and custom types:

```python
# In /plan, /tasks, /implement commands
guards_base = Path('.specify/guards')
types = GuardType.get_all_types_with_descriptions(guards_base)
for t in types:
    print(f"{t['name']} ({t['category']}) [{t['source']}]: {t['when_to_use']}")
```

Agents see:
- Type name, category, version
- **Source** (official/custom) to distinguish marketplace vs user-defined
- AI hints for when to use
- Dependencies required

## Testing

Tests verify both official and custom type scanning:
- `test_list_types_with_custom()` - Checks both directories
- `test_load_custom_type()` - Loads from types-custom/
- `test_load_type()` - Checks official types first

All 21 tests pass ✅
