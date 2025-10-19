# Official Guard Types

This directory contains the official guard types distributed with Spec Kit.

## What are Guard Types?

Guard types are templates that define how validation checkpoints (guards) are scaffolded. Each guard type provides:

- **Scaffolding logic**: Automated file generation
- **Templates**: Boilerplate code for tests/validations
- **Metadata**: Description, dependencies, AI hints

## Available Types (MVP)

### unit-pytest
**Category**: Testing  
**Purpose**: Python unit test validation using pytest

Creates pytest-based unit tests with proper structure and boilerplate.

**Usage**:
```bash
specify guard create --type unit-pytest --name my-feature-tests
```

### api
**Category**: Testing  
**Purpose**: API endpoint validation

Creates API integration tests with schema validation and endpoint testing boilerplate.

**Usage**:
```bash
specify guard create --type api --name user-endpoints
```

## Custom Guard Types

Users can create custom guard types in `.specify/guards/types-custom/`. Custom types are preserved during Spec Kit updates, while official types in this directory may be replaced.

See `.specify/guards/types-custom/README.md` for information about creating custom guard types.

## Directory Structure

```
guards/types/
├── unit-pytest/
│   ├── guard-type.yaml       # Metadata
│   ├── scaffolder.py          # Python scaffolding logic
│   └── templates/
│       └── test.py.j2         # Jinja2 template
└── api/
    ├── guard-type.yaml
    ├── scaffolder.py
    └── templates/
        ├── schema.json.j2
        └── test.py.j2
```

## Version

These guard types are part of Spec Kit **v0.0.25** (MVP release).

Future releases will add more guard types:
- `database`: Database migration/schema validation
- `lint-ruff`: Python linting with Ruff
- `docker-playwright`: Browser testing with Playwright

---

For more information, see the [Spec Kit documentation](https://github.github.io/spec-kit/).
