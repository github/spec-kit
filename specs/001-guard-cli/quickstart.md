# Quickstart: Guard CLI Implementation

**Feature**: 001-guard-cli  
**Date**: 2025-10-19

## Setup

```bash
# Ensure you're on the feature branch
git checkout 001-guard-cli

# Install dependencies (Jinja2, PyYAML)
uv add jinja2 pyyaml

# Verify existing dependencies
uv pip list | grep -E "(typer|rich|pytest)"
```

## Development Workflow

### 1. Implement Core Guard Command Group

**File**: `src/specify_cli/__init__.py`

Add guard command group to existing Typer app:

```python
import typer
from specify_cli.guards.commands import guard_app

app = typer.Typer()

# Add guard command group
app.add_typer(guard_app, name="guard", help="Manage validation guards")

# Existing commands...
```

### 2. Implement Guard CLI Commands

**File**: `src/specify_cli/guards/commands.py`

```python
import typer
from rich import print
from specify_cli.guards.registry import GuardRegistry
from specify_cli.guards.types import GuardTypeManager
from specify_cli.guards.scaffolder import scaffold_guard
from specify_cli.guards.executor import execute_guard

guard_app = typer.Typer()

@guard_app.command("types")
def list_guard_types(filter: str = typer.Option(None)):
    """List available guard types"""
    manager = GuardTypeManager()
    types = manager.list_types(category_filter=filter)
    # Rich table output...

@guard_app.command("create")
def create_guard(
    type: str = typer.Option(..., help="Guard type"),
    name: str = typer.Option(..., help="Guard name")
):
    """Create a new guard"""
    registry = GuardRegistry()
    guard_id = registry.generate_id()
    result = scaffold_guard(guard_id, type, name)
    print(f"✓ Created Guard {guard_id}")
    # ... more output

@guard_app.command("run")
def run_guard(
    guard_id: str = typer.Argument(None),
    task: str = typer.Option(None)
):
    """Execute a guard"""
    result = execute_guard(guard_id or task)
    if result['passed']:
        print(f"✓ PASS: Guard {guard_id}")
        raise typer.Exit(0)
    else:
        print(f"✗ FAIL: Guard {guard_id}")
        raise typer.Exit(1)

# ... more commands (list, validate, install, validate-type)
```

### 3. Test Guard CLI Locally

```bash
# Test guard types command
specify guard types

# Create a test guard
specify guard create --type unit-pytest --name test-registry

# Verify files created
ls -la tests/unit/guards/
cat Makefile | grep "test-guard-G001"

# Run guard
specify guard run G001

# List guards
specify guard list
```

## Testing Strategy

### Unit Tests

```bash
# Run unit tests for guard CLI
pytest tests/unit/guards/ -v

# Test specific component
pytest tests/unit/guards/test_registry.py::test_generate_guard_id -v

# Coverage report
pytest tests/unit/guards/ --cov=src/specify_cli/guards --cov-report=html
```

### Integration Tests

```bash
# End-to-end guard creation test
pytest tests/integration/guards/test_guard_creation.py -v

# Guard execution test
pytest tests/integration/guards/test_guard_execution.py -v
```

## Common Scenarios

### Scenario 1: Create API Guard for User Endpoints

```bash
# Create guard
specify guard create --type api --name user-endpoints

# Expected output:
# ✓ Installing guard type: api@2.0.1
#   - Creating directory: tests/api/guards/
#   - Generating boilerplate...
# ✓ Created Guard G001: api/user-endpoints
# Files created:
#   tests/api/guards/G001_user_endpoints.py
#   tests/api/guards/G001_schemas.json
#   tests/api/conftest.py
#   Makefile (updated)
# Execute with: make test-guard-G001

# Verify guard
cat tests/api/guards/G001_user_endpoints.py

# Customize test (update selectors, add assertions)
# ... edit file ...

# Run guard
specify guard run G001

# Expected output (pass):
# ✓ PASS: Guard G001 validation successful
#   - Test 1: GET /api/users returns 200 OK
#   - Test 2: Response schema validates
#   - Test 3: Response time < 200ms
```

### Scenario 2: Discover Available Guard Types

```bash
# List all guard types
specify guard types

# Expected output:
# Available guard types in marketplace:
#
# E2E Testing:
#   docker-playwright@1.2.0    Browser automation with Playwright
#
# API Testing:
#   api@2.0.1                  REST API contract validation
#
# Database:
#   database@1.5.0             Schema & migration validation
#
# Unit Testing:
#   unit-pytest@3.0.0          Python unit tests with pytest
#
# Code Quality:
#   lint-ruff@2.0.0            Python linting with Ruff

# Filter by category
specify guard types --filter unit

# Expected output:
# Unit Testing:
#   unit-pytest@3.0.0          Python unit tests with pytest
```

### Scenario 3: Execute Guard and Handle Failure

```bash
# Run guard
specify guard run G001

# Expected output (fail):
# ✗ FAIL: Guard G001 validation failed
#   Test failures:
#   - tests/api/guards/G001_user_endpoints.py::test_get_users_response_schema FAILED
#     AssertionError: Schema validation failed
#     Expected: {"users": [...]}
#     Actual: {"data": [...]}
#
#   Suggestions:
#   - Check API response format matches schema
#   - Verify endpoint returns expected structure
#   - Update schema if API contract changed
#
# Exit code: 1

# Fix code
# ... update implementation ...

# Re-run guard
specify guard run G001

# Expected output (pass):
# ✓ PASS: Guard G001 validation successful
```

### Scenario 4: Install Custom Guard Type

```bash
# Validate custom guard type
specify guard validate-type ./my-custom-guard/

# Expected output:
# ✓ Manifest valid (guard-type.yaml)
# ✓ Scaffolder implements required interface
# ✓ Templates render correctly
# ✓ Validator executable
# ✓ Documentation AI-optimized
# ✓ Example reference implementation works
# Guard type ready for installation!

# Install
specify guard install ./my-custom-guard/

# Expected output:
# ✓ Installed: my-custom-guard@1.0.0
#   Location: .specify/guards/types/my-custom-guard/
#   Available as: specify guard create --type my-custom-guard

# Use custom guard type
specify guard create --type my-custom-guard --name custom-validation
```

## Debugging

### View Guard Registry

```bash
# View registry
cat .guards/registry.json | jq '.'

# View specific guard metadata
cat .guards/G001-metadata.json | jq '.'
```

### Check Guard Type Manifest

```bash
# View guard type manifest
cat .specify/guards/types/api/guard-type.yaml

# Test template rendering
python -c "
from jinja2 import Environment, FileSystemLoader
env = Environment(loader=FileSystemLoader('.specify/guards/types/api/templates'))
template = env.get_template('test.py.j2')
print(template.render(guard_id='G001', name='test'))
"
```

### Verbose Guard Execution

```bash
# Run guard with verbose output
make test-guard-G001 -v

# Check Makefile target
grep -A 5 "test-guard-G001" Makefile
```

## Performance Validation

### Guard Creation Performance

```bash
# Time guard creation
time specify guard create --type api --name perf-test

# Expected: < 5 seconds (SC-001)
```

### Guard Type Listing Performance

```bash
# Time guard type listing
time specify guard types

# Expected: < 1 second (SC-003)
```

### Guard Execution Timeout

```bash
# Create guard with timeout test
# (requires modifying guard to sleep > 300s)
specify guard run G999

# Expected: Timeout after 300 seconds (SC-007)
# Exit code: 2
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Guard Validation

on: [push, pull_request]

jobs:
  guards:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install specify
        run: uv tool install specify-cli --from .
      - name: List guards
        run: specify guard list
      - name: Run all guards
        run: |
          for guard in $(specify guard list --format=ids); do
            specify guard run $guard || exit 1
          done
```

## Troubleshooting

### Issue: Guard Creation Fails with "Guard type not found"

**Solution**: Verify guard type exists
```bash
specify guard types | grep <type-name>
```

### Issue: Guard Execution Fails with "Makefile target not found"

**Solution**: Verify Makefile updated
```bash
grep "test-guard-<id>" Makefile
```

If missing, re-create guard or manually add target.

### Issue: Concurrent Guard Creation Causes Duplicate IDs

**Solution**: File locking should prevent this. If occurs:
```bash
# Fix registry manually
cat .guards/registry.json
# Remove duplicate, fix next_id
```

### Issue: Template Rendering Fails with "Variable not found"

**Solution**: Check guard type templates
```bash
cat .specify/guards/types/<type>/templates/<template>.j2
# Verify all variables used are provided in context
```

## Next Steps

After implementing guard CLI:

1. **Create guards for this feature's tasks** (meta-circular validation)
2. **Update `/speckit.plan` command** to generate guards during planning
3. **Update `/speckit.tasks` command** to register guard IDs in tasks
4. **Update `/speckit.implement` command** to execute guards before marking tasks complete
5. **Document guard system** in README and docs/
