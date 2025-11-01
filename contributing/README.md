# Contributing to Spec Kit

Thank you for your interest in contributing! This section contains documentation for contributors and maintainers.

## Quick Links

- **[Development Setup](./development-setup.md)** - Set up your local environment
- **[Testing](./testing.md)** - Running and writing tests
- **[Architecture](./architecture/)** - Implementation details and design decisions

## Getting Started

1. **Fork and Clone**
   ```bash
   git clone https://github.com/YOUR_USERNAME/spec-kit.git
   cd spec-kit
   ```

2. **Set Up Development Environment**

   See [Development Setup](./development-setup.md) for detailed instructions.

3. **Make Your Changes**

   Create a feature branch and make your changes.

4. **Test Your Changes**

   Run tests and verify your changes work as expected.

5. **Submit a Pull Request**

   Push your changes and create a pull request.

## Development Workflows

### Quick Development Iteration

```bash
# Run CLI directly without installing
python -m src.specify_cli init test-project --ai claude --ignore-agent-tools

# Test changes immediately
```

### Editable Installation

```bash
# Create virtual environment
uv venv
source .venv/bin/activate  # or .venv\Scripts\Activate.ps1 on Windows

# Install in editable mode
uv pip install -e .

# Now 'specify' command uses your local changes
specify --help
```

### Testing from Git Branch

```bash
# Push your branch
git push origin your-feature-branch

# Test it like a user would
uvx --from git+https://github.com/YOUR_USERNAME/spec-kit.git@your-feature-branch specify init test --ai claude
```

## Project Structure

```
spec-kit/
├── src/specify_cli/        # Python CLI implementation
│   ├── __init__.py        # Main CLI logic
│   └── scripts/           # Embedded bash/PowerShell scripts
├── scripts/               # Template bash/PowerShell scripts
├── templates/             # Spec and plan templates
├── docs/                  # User-facing documentation
├── contributing/          # Contributor documentation (you are here)
├── tests/                 # Test suite
└── pyproject.toml        # Python package configuration
```

## Documentation

### User Documentation (`docs/`)
- Getting Started tutorials
- How-to guides
- Concept explanations
- Reference documentation

### Contributor Documentation (`contributing/`)
- Development setup
- Architecture decisions
- Implementation details
- Testing strategies

## Key Guidelines

1. **Code Quality**
   - Follow existing code style
   - Add tests for new features
   - Document public APIs

2. **Documentation**
   - Update docs when changing features
   - Keep examples current
   - Write clear commit messages

3. **Testing**
   - Test your changes locally
   - Ensure existing tests pass
   - Add new tests for new features

4. **Pull Requests**
   - Keep PRs focused and atomic
   - Reference related issues
   - Provide clear description of changes

## Architecture Documentation

- [Multi-Repo Implementation](./architecture/multi-repo-implementation.md)
- [Multi-Repo Modes Comparison](./architecture/multi-repo-modes-comparison.md)
- [Multi-Repo Testing](./architecture/multi-repo-testing.md)

## Need Help?

- Open an issue for questions
- Check existing issues for similar problems
- Read the [Development Setup](./development-setup.md) guide

## Related Resources

- [Main README](../README.md) - Project overview
- [Code of Conduct](../CODE_OF_CONDUCT.md) - Community guidelines
- [License](../LICENSE) - Project license
