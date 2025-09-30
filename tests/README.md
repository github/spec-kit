# Test Suite

This directory contains all tests for the Spec-Kit project. Tests are organized by language and testing framework.

## 📁 Directory Structure

```
tests/
├── python/              # Python tests (pytest)
│   ├── unit/           # Unit tests for CLI and utilities
│   ├── integration/    # Integration tests
│   └── conftest.py     # Pytest configuration and fixtures
├── fish/               # Fish shell tests (Fishtape)
│   ├── *.test.fish    # Test files
│   ├── helpers.fish   # Test helper functions
│   └── fixtures/      # Test fixtures
└── README.md          # This file
```

## 🧪 Running Tests

### Quick Start

```bash
# Run all tests
make test

# Run specific test suite
make test-python
make test-fish

# Run with linting
make test-all
```

### Individual Test Suites

#### Python Tests (pytest)

Tests for the Specify CLI Python code:

```bash
# All Python tests
uv run pytest tests/python/

# Specific test file
uv run pytest tests/python/unit/test_cli_init.py

# With coverage report
uv run pytest tests/python/ --cov=src/specify_cli --cov-report=html

# Specific test function
uv run pytest tests/python/unit/test_cli_init.py::test_init_basic
```

**Framework**: pytest + pytest-cov + pytest-mock  
**Coverage Target**: 45%+  
**Location**: `tests/python/`

#### Fish Shell Tests (Fishtape)

Tests for Fish shell automation scripts:

```bash
# All Fish tests
fish -c "fishtape tests/fish/*.test.fish"

# Specific test file
fish -c "fishtape tests/fish/common.test.fish"

# View summary only
fish -c "fishtape tests/fish/*.test.fish" | tail -5
```

**Framework**: Fishtape 3.0.1  
**Test Count**: 48 tests (100% passing)  
**Location**: `tests/fish/`  
**Details**: See `tests/fish/README.md`

## 📊 Test Coverage

### Python Tests
- **CLI commands**: `init`, `check`
- **Utilities**: Repository detection, git operations, downloads
- **Error handling**: Invalid arguments, missing dependencies
- **Cross-platform**: Linux, macOS, Windows

**Current Coverage**: See `htmlcov/index.html` after running tests

### Fish Tests
- **Core functions**: All 8 functions in `common.fish` (100%)
- **Argument parsing**: Help flags, usage messages for all scripts
- **Error validation**: Edge cases, invalid inputs
- **Pure functions**: Repository root detection, branch resolution

**Coverage**: 100% of testable functions (see `tests/fish/README.md`)

## 🛠️ Development

### Adding Python Tests

1. Create test file in `tests/python/unit/` or `tests/python/integration/`
2. Follow naming: `test_*.py`
3. Use fixtures from `conftest.py`
4. Run `make test-python` to verify

Example:
```python
# tests/python/unit/test_new_feature.py
def test_my_feature():
    assert some_function() == expected_result
```

### Adding Fish Tests

1. Create test file in `tests/fish/`: `new-feature.test.fish`
2. Use Fishtape syntax: `@test "description" (command) operator expected`
3. Source helpers if needed: `source (dirname (status filename))/helpers.fish`
4. Run `make test-fish` to verify

Example:
```fish
# tests/fish/new-feature.test.fish
@test "feature works" (my_function "arg") = "expected"
```

## 🚀 Continuous Integration

Tests run automatically on:
- **Push** to `main`, `feature-*`, `fix-*` branches
- **Pull requests** to `main`
- **Matrix**: Python 3.11, 3.12, 3.13 × Ubuntu, macOS, Windows

See `.github/workflows/test.yml` for CI configuration.

## 🔍 Troubleshooting

### Python Tests Failing

```bash
# Check Python version
uv run python --version

# Reinstall dependencies
uv sync --extra dev

# Run with verbose output
uv run pytest -vv tests/python/

# Run specific test with debug output
uv run pytest -vv -s tests/python/unit/test_cli_init.py::test_name
```

### Fish Tests Failing

```bash
# Check Fish installation
fish --version

# Check Fishtape installation
fish -c "type -q fishtape && echo 'Installed' || echo 'Missing'"

# Install Fishtape
fish -c "curl -sL https://raw.githubusercontent.com/jorgebucaran/fisher/main/functions/fisher.fish | source && fisher install jorgebucaran/fishtape"

# Run with verbose output
fish -c "fishtape tests/fish/common.test.fish"
```

### Coverage Too Low

The Python test suite requires 45%+ coverage. If failing:

1. Check which files lack coverage: `uv run pytest --cov-report=term-missing`
2. Add tests for uncovered lines
3. Review `htmlcov/index.html` for detailed report

## 📚 Resources

- [pytest documentation](https://docs.pytest.org/)
- [Fishtape documentation](https://github.com/jorgebucaran/fishtape)
- [Fish shell documentation](https://fishshell.com/docs/current/)
- [Makefile targets](#running-tests): Run `make help`

## 🎯 Testing Philosophy

### What We Test
- ✅ Core functionality and happy paths
- ✅ Error handling and edge cases
- ✅ Public APIs and CLI interfaces
- ✅ Cross-platform compatibility (Python)
- ✅ Pure functions and utilities (Fish)

### What We Don't Test
- ❌ External dependencies (GitHub API, network calls - mocked)
- ❌ Platform-specific implementations (tested implicitly)
- ❌ Complex integration workflows (tested manually)
- ❌ Third-party library internals

**Principle**: Better to have reliable tests than high coverage with flaky tests.

---

**Last Updated**: 2025-09-30  
**Maintainers**: See `CONTRIBUTING.md`
