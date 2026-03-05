# Contributing to Domain Analysis Tool

We welcome contributions to the Domain Analysis Tool! This guide will help you get started with contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Guidelines](#contributing-guidelines)
- [Testing Requirements](#testing-requirements)
- [Code Style](#code-style)
- [Submitting Changes](#submitting-changes)
- [Issue Reporting](#issue-reporting)

## Code of Conduct

This project adheres to a Code of Conduct to ensure a welcoming environment for all contributors:

- **Be respectful**: Treat all contributors and users with respect and kindness
- **Be inclusive**: Welcome contributors of all backgrounds and experience levels
- **Be constructive**: Provide helpful feedback and focus on improving the project
- **Be collaborative**: Work together to solve problems and share knowledge

## Getting Started

### Prerequisites

Before contributing, ensure you have:

- Python 3.11 or higher
- Git for version control
- bash shell (Linux/macOS) or PowerShell (Windows)
- Basic understanding of domain analysis concepts

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:
   ```bash
   git clone https://github.com/your-username/domain-analysis-tool.git
   cd domain-analysis-tool
   ```

3. Add the upstream repository:
   ```bash
   git remote add upstream https://github.com/original-owner/domain-analysis-tool.git
   ```

## Development Setup

### 1. Install Dependencies

```bash
# Install required Python packages
pip install pyyaml

# For development and testing (when available)
pip install pytest pytest-cov black flake8
```

### 2. Verify Installation

```bash
# Test the domain analysis functionality
python src/specify_cli/domain_analysis.py --help

# Test shell scripts (Linux/macOS)
chmod +x scripts/bash/analyze-domain.sh
./scripts/bash/analyze-domain.sh --help

# Test PowerShell scripts (Windows)
scripts/powershell/analyze-domain.ps1 -Help
```

### 3. Run Tests (when available)

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest tests/ --cov=src/specify_cli/
```

## Contributing Guidelines

### Types of Contributions

We welcome several types of contributions:

1. **Bug Fixes**: Fix issues in the existing codebase
2. **Feature Enhancements**: Improve existing functionality
3. **New Features**: Add new domain analysis capabilities
4. **Documentation**: Improve README, USAGE, or code documentation
5. **Tests**: Add or improve test coverage
6. **Domain Templates**: Add new domain-specific templates

### Contribution Process

1. **Check Existing Issues**: Look for existing issues or discussions
2. **Create an Issue**: For significant changes, create an issue first
3. **Branch Strategy**: Create a feature branch from main
4. **Make Changes**: Implement your changes following our guidelines
5. **Test Thoroughly**: Ensure all tests pass and add new tests
6. **Submit PR**: Open a pull request with clear description

### Branch Naming

Use descriptive branch names:

```bash
# Feature branches
git checkout -b feature/add-healthcare-domain-template
git checkout -b feature/improve-csv-parsing

# Bug fix branches
git checkout -b fix/handle-empty-json-files
git checkout -b fix/windows-path-separator-issue

# Documentation branches
git checkout -b docs/update-installation-guide
git checkout -b docs/add-api-reference
```

## Testing Requirements

### Test Categories

1. **Unit Tests**: Test individual functions and classes
2. **Integration Tests**: Test component interactions
3. **Script Tests**: Test shell script functionality
4. **Data Tests**: Test with sample datasets

### Testing Guidelines

```python
# Example unit test structure
import pytest
from specify_cli.domain_analysis import DomainAnalyzer

def test_entity_extraction():
    """Test entity extraction from JSON data."""
    analyzer = DomainAnalyzer("./test-data")
    entities = analyzer.extract_entities()

    assert len(entities) > 0
    assert entities[0].name is not None
    assert entities[0].confidence >= 0.0

def test_business_rule_inference():
    """Test business rule generation."""
    analyzer = DomainAnalyzer("./test-data")
    rules = analyzer.infer_business_rules()

    for rule in rules:
        assert rule.rule_id is not None
        assert rule.description is not None
        assert 0.0 <= rule.confidence <= 1.0
```

### Test Data

Create test datasets in `tests/data/`:

```
tests/
├── data/
│   ├── financial/
│   │   ├── invoices.json
│   │   ├── payments.json
│   │   └── suppliers.csv
│   ├── ecommerce/
│   │   ├── orders.json
│   │   ├── products.json
│   │   └── customers.csv
│   └── invalid/
│       ├── empty.json
│       ├── malformed.json
│       └── unsupported.txt
└── test_domain_analysis.py
```

## Code Style

### Python Code Style

Follow PEP 8 with these specific guidelines:

```python
# Good: Clear function names and type hints
def extract_business_entities(data_files: List[Path]) -> List[BusinessEntity]:
    """Extract business entities from data files.

    Args:
        data_files: List of JSON/CSV files to analyze

    Returns:
        List of discovered business entities with confidence scores
    """
    entities = []
    # Implementation here
    return entities

# Good: Descriptive variable names
invoice_confidence_threshold = 0.75
payment_matching_rules = []

# Good: Error handling
try:
    with open(file_path, 'r') as f:
        data = json.load(f)
except (FileNotFoundError, json.JSONDecodeError) as e:
    logger.warning(f"Failed to process {file_path}: {e}")
    return None
```

### Shell Script Style

```bash
#!/bin/bash
# Good: Clear variable names and error checking

set -euo pipefail  # Exit on error, undefined vars, pipe failures

readonly DATA_DIR="${1:-./data}"
readonly OUTPUT_FILE="${2:-analysis.json}"

# Function definitions
analyze_directory() {
    local data_dir="$1"
    local output_file="$2"

    if [[ ! -d "$data_dir" ]]; then
        echo "Error: Directory '$data_dir' does not exist" >&2
        return 1
    fi

    # Implementation here
}

# Main execution
main() {
    analyze_directory "$DATA_DIR" "$OUTPUT_FILE"
}

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

### Documentation Style

```python
class DomainAnalyzer:
    """Analyzes business domains from data files.

    This class provides functionality to extract business entities,
    infer business rules, and identify integration points from
    structured data files (JSON/CSV).

    Attributes:
        data_directory: Path to directory containing data files
        confidence_threshold: Minimum confidence for entity acceptance

    Example:
        >>> analyzer = DomainAnalyzer("./financial-data")
        >>> domain_model = analyzer.analyze()
        >>> print(f"Found {len(domain_model.entities)} entities")
    """
```

## Submitting Changes

### Pull Request Process

1. **Update Your Branch**:
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Commit Guidelines**:
   ```bash
   # Good commit messages
   git commit -m "feat: add healthcare domain template with medical entities"
   git commit -m "fix: handle empty CSV files gracefully"
   git commit -m "docs: update installation instructions for Windows"
   git commit -m "test: add unit tests for entity extraction"
   ```

3. **Push Changes**:
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Create Pull Request**:
   - Use the GitHub interface to create a pull request
   - Fill out the pull request template
   - Link to any related issues
   - Request review from maintainers

### Pull Request Template

```markdown
## Description
Brief description of the changes made.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that causes existing functionality to change)
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed
- [ ] New tests added for new functionality

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review of code completed
- [ ] Documentation updated as needed
- [ ] Changes work on both Linux/macOS and Windows
```

## Issue Reporting

### Bug Reports

When reporting bugs, include:

1. **Environment Information**:
   - Operating system (Linux/macOS/Windows)
   - Python version
   - Shell version (bash/PowerShell)

2. **Steps to Reproduce**:
   ```
   1. Run command: ./scripts/bash/analyze-domain.sh --data-dir=./test-data
   2. Observe error message: "FileNotFoundError: No JSON files found"
   3. Expected: Should process CSV files in directory
   ```

3. **Sample Data**: Provide minimal sample data that reproduces the issue

4. **Error Output**: Include complete error messages and stack traces

### Feature Requests

For feature requests, include:

1. **Use Case**: Describe the business problem you're trying to solve
2. **Proposed Solution**: Suggest how the feature might work
3. **Alternatives**: Mention any workarounds you've considered
4. **Domain Context**: Specify which business domains would benefit

### Security Issues

For security-related issues:
- Do NOT create public issues
- Email maintainers directly
- Provide detailed information about the vulnerability
- Allow time for responsible disclosure

## Development Best Practices

### 1. Domain Analysis Principles

- **Data-Driven**: Base entity extraction on actual data patterns
- **Confidence Scoring**: Always provide confidence metrics
- **User Validation**: Support interactive review and customization
- **Cross-Platform**: Ensure functionality works on all supported platforms

### 2. Error Handling

```python
# Good: Comprehensive error handling
def parse_json_file(file_path: Path) -> Optional[Dict]:
    """Parse JSON file with robust error handling."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return None
    except PermissionError:
        logger.error(f"Permission denied reading {file_path}")
        return None
```

### 3. Configuration Management

- Use YAML for configuration files
- Provide sensible defaults
- Validate configuration on load
- Support environment variable overrides

### 4. Cross-Platform Compatibility

```python
# Good: Platform-independent path handling
from pathlib import Path
import os

data_dir = Path(os.environ.get('DATA_DIR', './data'))
config_file = data_dir / 'config.yaml'
```

## Release Process

### Version Numbering

We follow semantic versioning (SemVer):

- **Major** (1.0.0): Breaking changes
- **Minor** (1.1.0): New features, backwards compatible
- **Patch** (1.1.1): Bug fixes, backwards compatible

### Release Checklist

1. Update version numbers
2. Update CHANGELOG.md
3. Run full test suite
4. Update documentation
5. Create release branch
6. Tag release
7. Create GitHub release with notes

## Getting Help

### Communication Channels

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and ideas
- **Pull Request Reviews**: Code-specific feedback

### Maintainer Contact

For urgent issues or questions:
- Create a GitHub issue with `@maintainer` mention
- Email project maintainers (listed in README)

## Recognition

Contributors are recognized in:
- CONTRIBUTORS.md file
- Release notes
- Project documentation

Thank you for contributing to the Domain Analysis Tool!