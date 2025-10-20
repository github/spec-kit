# Unit Pytest Guard Type

## Overview

The `unit-pytest` guard type validates unit tests using the pytest framework with code coverage tracking. It ensures tests pass and meet minimum coverage thresholds for Python projects.

## What This Guard Type Validates

- **Unit Test Execution**: Runs pytest test suites
- **Code Coverage**: Measures test coverage with pytest-cov
- **Coverage Thresholds**: Enforces minimum coverage requirements
- **Test Markers**: Filters tests by markers (e.g., unit, integration, slow)
- **Test Quality**: Identifies failing tests and provides detailed feedback

## When to Use It

### ✅ Use This Guard Type When:

- Validating business logic and algorithms
- Testing individual functions and classes
- Ensuring code coverage meets standards
- Running fast, isolated unit tests
- Testing Python modules and packages
- Verifying refactoring didn't break functionality

### ❌ Don't Use This Guard Type When:

- Testing UI functionality (use `ui-playwright` instead)
- Testing API endpoints end-to-end (use `api-requests` instead)
- Running integration tests (consider separate guard configuration)
- Checking code style (use `static-analysis-python` instead)

## Installation

Ensure pytest and coverage tools are installed:

```bash
uv pip install pytest pytest-cov pytest-json-report
```

## Example Configurations

### Basic Unit Tests

```yaml
id: G003
guard_type: unit-pytest
name: unit-tests
params:
  test_paths:
    - tests/unit/
  coverage_threshold: 80
  markers: []
  verbose: false
  fail_under: true
```

### Guards-Specific Tests

```yaml
id: G003
guard_type: unit-pytest
name: guards-unit-tests
params:
  test_paths:
    - tests/unit/guards/
  coverage_threshold: 85
  markers:
    - unit
  verbose: true
  fail_under: true
```

### Fast Tests Only

```yaml
id: G004
guard_type: unit-pytest
name: fast-tests
params:
  test_paths:
    - tests/unit/
  coverage_threshold: 70
  markers:
    - fast
  verbose: false
  fail_under: true
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `test_paths` | array | `["tests/unit/"]` | Paths to pytest test files/directories |
| `coverage_threshold` | integer | `80` | Minimum coverage percentage (0-100) |
| `markers` | array | `[]` | Pytest markers to filter tests |
| `verbose` | boolean | `false` | Enable verbose pytest output |
| `fail_under` | boolean | `true` | Fail if coverage below threshold |

## Creating a Guard Instance

```bash
# Create a guard for unit tests
specify guard create --type unit-pytest --name unit-tests

# Edit the generated guard.yaml to configure parameters
# Then run the guard
specify guard run G00X
```

## Common Failure Patterns

### 1. Low Coverage

**Symptom**: "Coverage X% below threshold Y%"
**Cause**: Insufficient test coverage
**Fix**:
- Write tests for uncovered code paths
- Review coverage report: `pytest --cov --cov-report=html`
- Lower threshold temporarily if needed (not recommended)
- Exclude irrelevant files from coverage in `.coveragerc`

### 2. Test Failures

**Symptom**: "N of M tests failed"
**Cause**: Broken tests or code changes
**Fix**:
- Review test output in guard history
- Run tests manually: `pytest tests/unit/ -v`
- Fix broken code or update tests
- Check for environmental dependencies

### 3. Missing Test Paths

**Symptom**: "Test path not found: X"
**Cause**: Configured path doesn't exist
**Fix**:
- Create the test directory
- Update `test_paths` in guard.yaml to correct paths
- Ensure relative paths are correct from project root

### 4. Import Errors

**Symptom**: "ModuleNotFoundError" or "ImportError"
**Cause**: Missing dependencies or incorrect PYTHONPATH
**Fix**:
- Install missing dependencies: `uv pip install <package>`
- Check import paths in tests
- Ensure project is installable: `uv pip install -e .`

## Debugging Failures

### View Guard History

```bash
# List recent runs
specify guard history G00X

# View detailed output for specific run
specify guard history G00X --run-id <run-id>
```

### Run Tests Manually

```bash
# Run pytest directly for debugging
uv run pytest tests/unit/ -v --cov --cov-report=term-missing

# Run specific test file
uv run pytest tests/unit/test_example.py -v

# Run with specific marker
uv run pytest tests/unit/ -m unit -v
```

### Generate Coverage Report

```bash
# HTML coverage report
uv run pytest --cov --cov-report=html
# Open htmlcov/index.html in browser

# Terminal report with missing lines
uv run pytest --cov --cov-report=term-missing
```

### Enable Verbose Mode

Temporarily set `verbose: true` in guard.yaml for detailed test output:

```yaml
params:
  verbose: true  # See each test result
```

## Example Test File

Create a basic pytest test in `tests/unit/test_example.py`:

```python
import pytest
from myproject.calculator import Calculator


def test_addition():
    calc = Calculator()
    assert calc.add(2, 3) == 5


def test_subtraction():
    calc = Calculator()
    assert calc.subtract(5, 3) == 2


@pytest.mark.unit
def test_multiplication():
    calc = Calculator()
    assert calc.multiply(3, 4) == 12


@pytest.mark.unit
def test_division():
    calc = Calculator()
    assert calc.divide(10, 2) == 5


@pytest.mark.unit
def test_division_by_zero():
    calc = Calculator()
    with pytest.raises(ValueError):
        calc.divide(10, 0)
```

## Integration with Workflow

### In Plan Phase

Identify unit test validation checkpoints:

```markdown
## Guard Validation Strategy

| Checkpoint | Guard Type | Command |
|------------|------------|---------|
| Business logic | unit-pytest | `specify guard create --type unit-pytest --name core-logic` |
```

### In Tasks Phase

Tag implementation tasks with guard validation:

```markdown
- [ ] T020 Implement payment processor [Guard: G003]
- [ ] T021 Add discount calculation [Guard: G003]
```

### In Implementation Phase

Run guards after implementing functionality:

```bash
# After implementing business logic
specify guard run G003

# If failures occur
specify guard history G003  # Review failures
uv run pytest tests/unit/ -v  # Debug locally
```

## Best Practices

1. **Organize Tests**: Mirror source structure in test directory
2. **Test Isolation**: Each test should be independent
3. **Use Fixtures**: Share setup/teardown with pytest fixtures
4. **Meaningful Names**: Test names should describe what they validate
5. **Markers**: Tag tests by category (unit, integration, slow, fast)
6. **Coverage Goals**: Aim for 80%+ coverage on critical code
7. **Fast Tests**: Keep unit tests fast (<1s each when possible)
8. **Mocking**: Use `unittest.mock` or `pytest-mock` for dependencies

## Pytest Markers

Configure markers in `pytest.ini` or `pyproject.toml`:

```ini
[tool.pytest.ini_options]
markers = [
    "unit: Unit tests (fast, isolated)",
    "integration: Integration tests (slower)",
    "slow: Tests that take >1s",
    "fast: Tests that take <1s",
]
```

Use in guard configuration:

```yaml
params:
  markers:
    - unit
    - fast
```

## Coverage Configuration

Create `.coveragerc` to customize coverage:

```ini
[run]
source = src/
omit =
    */tests/*
    */migrations/*
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
```

## Related Guard Types

- **static-analysis-python**: For code quality and style checks
- **ui-playwright**: For end-to-end UI testing
- **api-requests**: For API contract testing

## Troubleshooting

### pytest not found

```bash
# Install pytest with required plugins
uv pip install pytest pytest-cov pytest-json-report
```

### Coverage report not generated

Ensure pytest-cov is installed:

```bash
uv pip install pytest-cov
```

### Tests pass locally but fail in guard

Check for:
- Environment variables needed by tests
- File paths (relative vs absolute)
- Dependencies installed
- Database/fixture setup

### Slow test execution

- Add `timeout` configuration (default: 300s)
- Use markers to run fast tests separately
- Profile tests: `pytest --durations=10`

---

**Guard Type**: unit-pytest  
**Category**: unit  
**Framework**: pytest  
**Language**: Python
