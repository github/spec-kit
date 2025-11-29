# Spectrena Test Suite

Comprehensive test suite for Spectrena CLI and workflow.

## Test Structure

```
tests/
├── conftest.py          # Pytest fixtures and test helpers
├── test_config.py       # Configuration system tests
├── test_commands.py     # CLI command tests
├── test_workflow.py     # Integration workflow tests
├── test_worktrees.py    # Worktree management tests
└── README.md            # This file
```

## Running Tests

### Run All Tests

```bash
# From project root
pytest

# With verbose output
pytest -v

# With coverage
pytest --cov=src/spectrena --cov-report=term-missing
```

### Run Specific Test Files

```bash
pytest tests/test_config.py
pytest tests/test_commands.py
pytest tests/test_workflow.py
pytest tests/test_worktrees.py
```

### Run Specific Test Classes

```bash
pytest tests/test_config.py::TestSpecIdConfig
pytest tests/test_commands.py::TestNewCommand
pytest tests/test_workflow.py::TestSpecCreationWorkflow
```

### Run Specific Tests

```bash
pytest tests/test_config.py::TestSpecIdConfig::test_simple_template
pytest tests/test_commands.py::TestNewCommand::test_slugify
```

## Test Categories

### Unit Tests

Test individual functions and classes in isolation:

- **test_config.py**: Configuration loading, saving, YAML parsing, spec ID generation
- **test_commands.py**: Individual command functions (new, plan, doctor, context)

### Integration Tests

Test complete workflows:

- **test_workflow.py**: End-to-end spec creation, planning, context update workflows
- **test_worktrees.py**: Git worktree operations and dependency tracking

## Fixtures

### Core Fixtures (conftest.py)

- `temp_dir`: Temporary directory for test isolation
- `git_repo`: Initialized git repository
- `spectrena_project`: Full Spectrena project structure
- `sample_spec`: Pre-created spec for testing
- `sample_plan`: Pre-created plan.md with tech stack
- `cli_runner`: Helper for running CLI commands

## Test Coverage

### Modules Covered

| Module | Coverage | Notes |
|--------|----------|-------|
| config.py | ✅ Full | Config loading, saving, validation |
| new.py | ✅ Full | Spec ID generation, slugify, numbering |
| plan.py | ✅ Full | Spec detection, plan initialization |
| context.py | ✅ Full | Tech stack extraction, CLAUDE.md update |
| doctor.py | ✅ Partial | Command/package checks (env-dependent) |
| worktrees.py | ✅ Full | Branch detection, dependencies, worktrees |

### Workflows Covered

- ✅ Simple spec creation (001-feature-name)
- ✅ Component-based specs (CORE-001-feature)
- ✅ Project-prefixed specs (MYAPP-001-feature)
- ✅ Full format specs (MYAPP-CORE-001-feature)
- ✅ Config migration scenarios
- ✅ Plan initialization
- ✅ Tech stack extraction and context update
- ✅ Worktree creation and management
- ✅ Dependency graph parsing

## Writing New Tests

### Basic Test Template

```python
def test_feature_name(fixture_name):
    """Test description."""
    # Arrange
    expected = "expected value"

    # Act
    result = function_under_test()

    # Assert
    assert result == expected
```

### Using Fixtures

```python
def test_with_project(spectrena_project):
    """Test that needs a project structure."""
    os.chdir(spectrena_project)

    config = Config.load()
    assert config.spec_id.template is not None
```

### Testing File Operations

```python
def test_file_creation(temp_dir):
    """Test file creation in isolated directory."""
    file_path = temp_dir / "test.txt"
    file_path.write_text("content")

    assert file_path.exists()
    assert file_path.read_text() == "content"
```

## Continuous Integration

Tests run automatically on:

- Every push to feature branches
- Pull requests to main branch
- Pre-commit hooks (if configured)

### GitHub Actions Configuration

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -e ".[dev]"
      - run: pytest --cov=src/spectrena --cov-report=xml
      - uses: codecov/codecov-action@v3
```

## Troubleshooting

### Tests Fail with Import Errors

```bash
# Reinstall in development mode
pip install -e .
```

### Git-Related Tests Fail

```bash
# Ensure git is configured
git config --global user.name "Test User"
git config --global user.email "test@example.com"
```

### Temporary Directory Issues

```bash
# Clean pytest cache
pytest --cache-clear
```

## Test-Driven Development

When adding new features:

1. Write test first (TDD approach)
2. Run test to see it fail
3. Implement feature
4. Run test to see it pass
5. Refactor if needed

Example:

```bash
# 1. Create test
cat > tests/test_new_feature.py << 'EOF'
def test_new_feature():
    assert new_feature() == "expected"
EOF

# 2. Run and watch it fail
pytest tests/test_new_feature.py

# 3. Implement feature in src/spectrena/

# 4. Run and watch it pass
pytest tests/test_new_feature.py

# 5. Run all tests
pytest
```

## Performance Testing

For performance-critical operations:

```python
import time

def test_performance(spectrena_project):
    """Test operation completes within time limit."""
    start = time.time()

    # Operation under test
    result = expensive_operation()

    elapsed = time.time() - start
    assert elapsed < 1.0  # Should complete in < 1 second
```

## Future Test Additions

Potential areas for expanded testing:

- [ ] Lineage database operations
- [ ] MCP server functionality
- [ ] Discovery command with AI calls (mocked)
- [ ] Config wizard interactive flow
- [ ] Error handling and edge cases
- [ ] Cross-platform path handling
- [ ] Large-scale dependency graphs
- [ ] Concurrent worktree operations
