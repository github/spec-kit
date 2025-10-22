# Testing Guide for Bicep Generator

This document provides comprehensive information about testing the Bicep Generator feature of the Specify CLI.

## Table of Contents

1. [Test Organization](#test-organization)
2. [Running Tests](#running-tests)
3. [Test Categories](#test-categories)
4. [Writing Tests](#writing-tests)
5. [CI/CD Integration](#cicd-integration)
6. [Troubleshooting](#troubleshooting)

## Test Organization

### Directory Structure

```
tests/bicep/
├── conftest.py                  # Shared test fixtures and configuration
├── test_analyzer.py             # Unit tests for ProjectAnalyzer
├── test_generator.py            # Unit tests for BicepGenerator
├── test_integration.py          # Integration and E2E tests
├── test_utils.py                # Test utility functions
└── test_data/                   # Test data and fixtures
    ├── templates/               # Sample Bicep templates
    ├── parameters/              # Sample parameter files
    └── projects/                # Sample project structures
```

### Test Markers

Tests are organized using pytest markers:

- **`unit`**: Unit tests that test individual components in isolation
- **`integration`**: Integration tests that test multiple components together
- **`e2e`**: End-to-end tests that test complete workflows
- **`slow`**: Tests that take a long time to run (> 5 seconds)
- **`azure`**: Tests that require Azure credentials and interact with real Azure services
- **`requires_cli`**: Tests that require Azure CLI or Bicep CLI to be installed

## Running Tests

### Prerequisites

1. Install test dependencies:
   ```bash
   pip install -e ".[dev,test]"
   ```

2. Install Azure CLI and Bicep CLI (for CLI-dependent tests):
   ```bash
   # Azure CLI
   # Windows: https://learn.microsoft.com/en-us/cli/azure/install-azure-cli-windows
   # macOS: brew install azure-cli
   # Linux: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   
   # Bicep CLI
   az bicep install
   ```

### Quick Start

Run all tests except Azure integration tests:
```bash
pytest tests/bicep -m "not azure"
```

Run with coverage:
```bash
pytest tests/bicep -m "not azure" --cov=src/specify_cli/bicep --cov-report=html
```

### Using Test Runner Scripts

#### Bash (Linux/macOS)

```bash
# Run all tests with coverage
./scripts/bash/run-tests.sh

# Run only unit tests
./scripts/bash/run-tests.sh -t unit

# Run integration tests with verbose output
./scripts/bash/run-tests.sh -t integration -v

# Quick run (unit tests only, no coverage)
./scripts/bash/run-tests.sh -q

# Run E2E tests including slow ones
./scripts/bash/run-tests.sh -t e2e -s

# Run all tests including Azure integration
./scripts/bash/run-tests.sh -a
```

#### PowerShell (Windows)

```powershell
# Run all tests with coverage
.\scripts\powershell\run-tests.ps1

# Run only unit tests
.\scripts\powershell\run-tests.ps1 -Type unit

# Run integration tests with verbose output
.\scripts\powershell\run-tests.ps1 -Type integration -Verbose

# Quick run (unit tests only, no coverage)
.\scripts\powershell\run-tests.ps1 -Quick

# Run E2E tests including slow ones
.\scripts\powershell\run-tests.ps1 -Type e2e -Slow

# Run all tests including Azure integration
.\scripts\powershell\run-tests.ps1 -Azure
```

### Running Specific Test Categories

#### Unit Tests Only

```bash
pytest tests/bicep -m unit
```

Unit tests are fast and don't require external dependencies. They test individual components in isolation using mocks.

#### Integration Tests

```bash
pytest tests/bicep -m integration
```

Integration tests verify that multiple components work together correctly. They may use file I/O but don't require Azure credentials.

#### End-to-End Tests

```bash
pytest tests/bicep -m e2e
```

E2E tests run complete workflows from analysis to template generation. They test the system as a whole.

#### Azure Integration Tests

```bash
pytest tests/bicep -m azure
```

**⚠️ WARNING**: These tests interact with real Azure resources and require:
- Azure credentials configured (via `az login`)
- An active Azure subscription
- Appropriate permissions to create/modify resources

Set environment variables:
```bash
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
export AZURE_RESOURCE_GROUP="your-test-resource-group"
```

### Excluding Slow Tests

```bash
pytest tests/bicep -m "not slow"
```

### Running Failed Tests Only

```bash
pytest tests/bicep --lf  # Last failed
pytest tests/bicep --ff  # Failed first, then others
```

### Parallel Execution

For faster test runs, use pytest-xdist:

```bash
pip install pytest-xdist
pytest tests/bicep -n auto  # Auto-detect CPU count
pytest tests/bicep -n 4     # Use 4 workers
```

## Test Categories

### Unit Tests (`test_analyzer.py`, `test_generator.py`)

#### Test Classes

1. **TestProjectAnalyzer**
   - Tests project structure analysis
   - Tests dependency detection from configuration files
   - Tests dependency detection from package files
   - Tests secret detection in code
   - Tests confidence scoring
   - Tests directory exclusion patterns

2. **TestResourceDetection**
   - Tests detection of specific Azure services
   - Covers: Storage, Web Apps, Key Vault, SQL, Cosmos DB, Container Registry, Function Apps

3. **TestBicepGenerator**
   - Tests basic template generation
   - Tests dependency resolution
   - Tests MCP schema integration
   - Tests parameter file generation
   - Tests naming conventions
   - Tests best practices application

4. **TestTemplateGeneration**
   - Tests generation of individual resource templates
   - Tests output declarations
   - Tests dependency relationships

5. **TestModularGeneration**
   - Tests main orchestrator generation
   - Tests module file organization
   - Tests parameter passing between modules

### Integration Tests (`test_integration.py`)

#### Test Classes

1. **TestEndToEndWorkflow**
   - Complete analyze → generate → validate → review workflow
   - Multi-environment deployments
   - Template updates and change detection
   - MCP Server integration

2. **TestTemplateValidation**
   - Bicep syntax validation
   - Schema compliance
   - Best practices validation
   - Security requirements
   - Azure ARM validation

3. **TestTemplateDeployment**
   - Deployment package preparation
   - Deployment script generation
   - Dry-run deployments
   - Actual deployments (Azure tests only)

4. **TestDependencyResolution**
   - Simple dependency graphs
   - Complex dependency chains
   - Circular dependency detection

5. **TestCostEstimation**
   - Basic resource cost estimation
   - Scaling considerations
   - Cost optimization recommendations

6. **TestSecurityAnalysis**
   - Security issue scanning
   - Compliance framework checks
   - Security report generation

## Writing Tests

### Test Structure

Follow the Arrange-Act-Assert pattern:

```python
def test_example(sample_project):
    # Arrange: Set up test data
    analyzer = ProjectAnalyzer(sample_project)
    
    # Act: Perform the operation
    result = analyzer.analyze()
    
    # Assert: Verify the outcome
    assert result is not None
    assert len(result.resources) > 0
```

### Using Fixtures

Fixtures are defined in `conftest.py` and can be used in any test:

```python
def test_with_fixtures(temp_project_dir, mock_mcp_client, sample_project_analysis):
    # temp_project_dir: Temporary directory for test projects
    # mock_mcp_client: Mock Azure MCP Server client
    # sample_project_analysis: Pre-built analysis result
    pass
```

### Async Tests

For async code, use pytest-asyncio:

```python
import pytest

@pytest.mark.asyncio
async def test_async_operation(mock_mcp_client):
    schema = await mock_mcp_client.get_bicep_schema("Microsoft.Storage/storageAccounts")
    assert schema is not None
```

### Parametrized Tests

Test multiple scenarios with one test function:

```python
@pytest.mark.parametrize("resource_type,expected_name", [
    ("Microsoft.Storage/storageAccounts", "storage"),
    ("Microsoft.Web/sites", "webapp"),
    ("Microsoft.KeyVault/vaults", "keyvault"),
])
def test_resource_naming(resource_type, expected_name):
    name = extract_name(resource_type)
    assert name == expected_name
```

### Mock Objects

Use unittest.mock for mocking:

```python
from unittest.mock import Mock, AsyncMock, patch

def test_with_mock():
    mock_client = Mock()
    mock_client.get_schema.return_value = {"type": "object"}
    
    result = process_schema(mock_client)
    
    assert mock_client.get_schema.called
    assert result is not None
```

### Test Utilities

Use helper functions from `test_utils.py`:

```python
from tests.bicep.test_utils import (
    create_mock_analysis,
    create_mock_bicep_template,
    validate_bicep_syntax,
    assert_resource_exists,
)

def test_template_generation():
    template = create_mock_bicep_template("Microsoft.Storage/storageAccounts")
    errors = validate_bicep_syntax(template)
    assert len(errors) == 0
    assert_resource_exists(template, "Microsoft.Storage/storageAccounts")
```

### Adding New Tests

1. **Identify the test category**: Unit, integration, or E2E?
2. **Choose the appropriate file**: `test_analyzer.py`, `test_generator.py`, or `test_integration.py`
3. **Add the test function** with descriptive name: `test_<feature>_<scenario>()`
4. **Add appropriate markers**: `@pytest.mark.unit`, `@pytest.mark.slow`, etc.
5. **Use fixtures** where appropriate
6. **Follow AAA pattern**: Arrange, Act, Assert
7. **Add docstring** explaining what the test validates

Example:

```python
@pytest.mark.unit
def test_detect_storage_dependencies(sample_web_project):
    """Test that storage account dependencies are correctly detected from config files."""
    # Arrange
    analyzer = ProjectAnalyzer(sample_web_project)
    
    # Act
    result = analyzer.analyze()
    
    # Assert
    storage_deps = [d for d in result.dependencies if d.service_type == "storage"]
    assert len(storage_deps) > 0
    assert storage_deps[0].confidence > 0.8
```

## CI/CD Integration

### GitHub Actions Workflow

The project includes a GitHub Actions workflow (`.github/workflows/test-bicep-generator.yml`) that:

1. **Runs on multiple platforms**: Ubuntu, Windows, macOS
2. **Tests multiple Python versions**: 3.11, 3.12
3. **Runs test stages**:
   - Unit tests (all platforms)
   - Integration tests (all platforms)
   - E2E tests (Ubuntu only)
   - Azure integration tests (main branch only, requires secrets)

4. **Generates coverage reports**:
   - Uploads to Codecov
   - Comments on pull requests
   - Fails if coverage < 80%

5. **Caches dependencies** for faster runs

### Required GitHub Secrets

For Azure integration tests:

- `AZURE_CREDENTIALS`: Azure service principal credentials
- `AZURE_SUBSCRIPTION_ID`: Target subscription ID
- `AZURE_RESOURCE_GROUP`: Test resource group name
- `CODECOV_TOKEN`: Codecov upload token

### Local CI Simulation

Run the same checks as CI locally:

```bash
# Install dependencies
pip install -e ".[dev,test]"

# Run all test stages
pytest tests/bicep -m unit --cov=src/specify_cli/bicep
pytest tests/bicep -m integration --cov=src/specify_cli/bicep --cov-append
pytest tests/bicep -m e2e --cov=src/specify_cli/bicep --cov-append

# Check coverage threshold
pytest tests/bicep -m "not azure" --cov=src/specify_cli/bicep --cov-fail-under=80
```

## Troubleshooting

### Common Issues

#### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'specify_cli'`

**Solution**:
```bash
pip install -e .
```

#### Async Test Errors

**Problem**: `RuntimeError: Event loop is closed`

**Solution**: Ensure pytest-asyncio is installed and configured:
```bash
pip install pytest-asyncio
```

Check `pytest.ini` has:
```ini
[pytest]
asyncio_mode = auto
```

#### Mock Not Found

**Problem**: Tests fail because mock objects aren't available

**Solution**: Ensure fixtures are imported from `conftest.py`:
```python
# conftest.py fixtures are automatically available
def test_example(mock_mcp_client):  # This fixture is auto-discovered
    pass
```

#### Azure CLI Not Found

**Problem**: `FileNotFoundError: [Errno 2] No such file or directory: 'az'`

**Solution**: Install Azure CLI or skip CLI-dependent tests:
```bash
pytest tests/bicep -m "not requires_cli"
```

#### Coverage Too Low

**Problem**: `FAILED tests/bicep/test_analyzer.py::test_example - AssertionError: coverage < 80%`

**Solution**: Add more tests to cover untested code paths. Check coverage report:
```bash
pytest tests/bicep --cov=src/specify_cli/bicep --cov-report=html
open htmlcov/index.html  # View detailed coverage
```

### Debugging Tests

#### Verbose Output

```bash
pytest tests/bicep -vv  # Very verbose
```

#### Print Debugging

```bash
pytest tests/bicep -s  # Don't capture stdout
```

#### Drop into Debugger on Failure

```bash
pytest tests/bicep --pdb  # Python debugger
```

#### Run Specific Test

```bash
pytest tests/bicep/test_analyzer.py::TestProjectAnalyzer::test_analyze_web_project
```

### Performance Issues

#### Slow Tests

Identify slow tests:
```bash
pytest tests/bicep --durations=10  # Show 10 slowest tests
```

Mark slow tests:
```python
@pytest.mark.slow
def test_expensive_operation():
    pass
```

Skip slow tests:
```bash
pytest tests/bicep -m "not slow"
```

#### Parallel Execution

Speed up test runs with parallel execution:
```bash
pip install pytest-xdist
pytest tests/bicep -n auto
```

## Best Practices

1. **Keep tests isolated**: Each test should be independent
2. **Use descriptive names**: `test_<feature>_<scenario>()`
3. **One assertion per logical concept**: Don't over-assert
4. **Use fixtures**: Reuse common setup code
5. **Mock external dependencies**: Azure MCP Server, Azure CLI, file I/O
6. **Test edge cases**: Empty inputs, invalid data, error conditions
7. **Keep tests fast**: Unit tests should be < 1 second
8. **Maintain high coverage**: Aim for 80%+ code coverage
9. **Document complex tests**: Add docstrings explaining what's being validated
10. **Update tests with code**: When changing code, update related tests

## Coverage Goals

- **Overall**: 80% minimum
- **Core modules**: 90%+ (analyzer.py, generator.py)
- **Integration modules**: 80%+ (mcp_client.py, validator.py)
- **Utility modules**: 70%+ (helpers, config)

## Additional Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Pytest-asyncio Documentation](https://pytest-asyncio.readthedocs.io/)
- [unittest.mock Documentation](https://docs.python.org/3/library/unittest.mock.html)
- [Codecov Documentation](https://docs.codecov.com/)

---

*For questions or issues with testing, please open a GitHub issue or contact the development team.*
