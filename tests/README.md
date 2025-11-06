# Spec Kit Test Suite

Comprehensive test suite for the Spec Kit project, covering critical paths, flows, and integration scenarios.

## Test Structure

```
tests/
├── conftest.py           # Shared fixtures and test configuration
├── unit/                 # Unit tests for individual components
│   ├── test_cli_init.py              # CLI init command tests
│   ├── test_template_download.py     # Template download/extraction tests
│   ├── test_agent_detection.py       # AI agent detection tests
│   └── test_guidelines_system.py     # Guidelines system tests
├── integration/          # Integration tests for complete workflows
│   └── test_full_init_flow.py        # Full init workflow tests
└── bash/                 # Tests for bash scripts
    └── test_bash_scripts.py          # Bash script validation tests
```

## Running Tests

### Install Test Dependencies

```bash
# Install with development dependencies
uv pip install -e ".[dev]"

# Or using pip
pip install -e ".[dev]"
```

### Run All Tests

```bash
# Run all tests with coverage
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=src/specify_cli --cov-report=html
```

### Run Specific Test Categories

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run tests excluding slow tests
pytest -m "not slow"

# Run specific test file
pytest tests/unit/test_cli_init.py

# Run specific test class
pytest tests/unit/test_cli_init.py::TestCheckTool

# Run specific test function
pytest tests/unit/test_cli_init.py::TestCheckTool::test_check_tool_found
```

### Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=src/specify_cli --cov-report=html

# View in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows

# Generate XML coverage report (for CI)
pytest --cov=src/specify_cli --cov-report=xml

# Terminal coverage report with missing lines
pytest --cov=src/specify_cli --cov-report=term-missing
```

## Test Categories

### Unit Tests (`-m unit`)

Test individual functions and components in isolation:
- CLI command validation
- Template download and extraction logic
- Agent detection and configuration
- JSON parsing and merging
- Git operations
- Guidelines system

**Coverage Goal**: 70%+ of critical paths

### Integration Tests (`-m integration`)

Test complete workflows end-to-end:
- Full project initialization flow
- Template download and extraction
- Git repository initialization
- Error recovery and cleanup
- Multi-agent support

**Coverage Goal**: All critical user flows

### Slow Tests (`-m slow`)

Long-running tests that may take several seconds:
- Multiple agent initialization
- Multiple script type testing
- Real file system operations

**Run separately**: `pytest -m slow`

## CI/CD Integration

Tests run automatically on:
- Every push to main branch
- Every pull request
- Manual workflow dispatch

### GitHub Actions Workflow

`.github/workflows/test.yml` runs:
1. Unit tests on multiple Python versions (3.11, 3.12)
2. Integration tests
3. Coverage report generation
4. Coverage upload to Codecov (optional)

### Local CI Simulation

```bash
# Run tests like CI does
pytest --cov=src/specify_cli --cov-report=xml --cov-report=term-missing -v
```

## Writing New Tests

### Test Naming Convention

- Test files: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`

### Using Fixtures

Common fixtures are defined in `conftest.py`:

```python
def test_example(temp_dir, mock_release_data):
    """Test using shared fixtures."""
    project_path = temp_dir / "myproject"
    assert mock_release_data["tag_name"] == "v1.0.0"
```

### Available Fixtures

- `temp_dir`: Temporary directory for test operations
- `mock_project_dir`: Mock project directory structure
- `mock_release_data`: Mock GitHub release data
- `mock_template_zip`: Mock template zip file
- `mock_agent_config`: Mock agent configuration
- `mock_guidelines_structure`: Mock guidelines directory
- `mock_httpx_client`: Mock HTTP client
- `mock_git_commands`: Mock git subprocess commands

### Test Markers

Mark tests with appropriate markers:

```python
@pytest.mark.unit
def test_something():
    """Unit test."""
    pass

@pytest.mark.integration
def test_workflow():
    """Integration test."""
    pass

@pytest.mark.slow
def test_long_running():
    """Slow test."""
    pass
```

## Debugging Tests

### Run with Debug Output

```bash
# Show print statements
pytest -s

# Show local variables on failure
pytest -l

# Enter debugger on failure
pytest --pdb

# Show test execution time
pytest --durations=10
```

### Run Specific Failing Test

```bash
# Run only the last failed test
pytest --lf

# Run failed tests first, then others
pytest --ff
```

## Test Coverage Goals

| Component | Coverage Target | Current |
|-----------|----------------|---------|
| CLI Init Command | 80%+ | TBD |
| Template System | 75%+ | TBD |
| Agent Detection | 90%+ | TBD |
| Guidelines System | 70%+ | TBD |
| Integration Flows | 100% | TBD |

## Continuous Improvement

- Add tests for new features
- Maintain test coverage above 70%
- Keep tests fast (< 5 seconds for unit tests)
- Use mocks to avoid external dependencies
- Document complex test scenarios

## Troubleshooting

### Import Errors

If you see import errors:

```bash
# Ensure package is installed in development mode
uv pip install -e .

# Or
pip install -e .
```

### Missing Dependencies

```bash
# Install test dependencies
uv pip install -e ".[dev]"
```

### Tests Hanging

Some tests may hang if they wait for user input. Use:

```bash
# Run with timeout
pytest --timeout=30
```

### Permission Errors (Bash Scripts)

On Unix systems, ensure bash scripts are executable:

```bash
chmod +x scripts/bash/*.sh
```

## Contributing

When contributing:

1. Write tests for new features
2. Ensure existing tests pass: `pytest`
3. Maintain or improve coverage: `pytest --cov`
4. Follow test naming conventions
5. Add docstrings to test functions
6. Use appropriate markers (`@pytest.mark.unit`, etc.)

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-cov documentation](https://pytest-cov.readthedocs.io/)
- [pytest-mock documentation](https://pytest-mock.readthedocs.io/)
