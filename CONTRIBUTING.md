# Contributing to Spectrena

## Quick Setup

```bash
# Clone
git clone https://github.com/rghsoftware/spectrena
cd spectrena

# Install editable with dev deps
uv pip install -e ".[dev,lineage-surreal]"

# Run tests
pytest

# Install as tool (for CLI testing)
uv tool install -e ".[lineage-surreal]"
```

## Project Structure

```
spectrena/
├── src/spectrena/
│   ├── __init__.py      # Typer CLI app
│   ├── config.py        # Configuration system
│   ├── new.py           # spectrena new
│   ├── plan.py          # spectrena plan-init
│   ├── doctor.py        # spectrena doctor
│   ├── context.py       # spectrena update-context
│   ├── discover.py      # spectrena discover
│   ├── worktrees.py     # sw command
│   └── lineage/
│       ├── db.py        # LineageDB + MCP server
│       ├── server.py    # Entry point
│       └── schema.surql # Database schema
├── tests/
├── templates/           # Default templates (copied to projects)
└── pyproject.toml
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature
```

### 2. Make Changes

- Follow existing code style
- Add type hints
- Update tests
- Update docs if needed

### 3. Test

```bash
# Unit tests
pytest

# With coverage
pytest --cov=spectrena --cov-report=html

# Type checking
pyright src/

# Linting
ruff check src/
ruff format src/
```

### 4. Manual Testing

```bash
# Test CLI
spectrena --help
spectrena new -c TEST "Test feature"

# Test worktrees
sw list
sw dep show

# Test MCP server
spectrena-mcp &
# Then test in Claude Code
```

### 5. Submit PR

```bash
git push -u origin feature/your-feature
gh pr create
```

## Code Style

### Python

- Python 3.11+
- Type hints required
- Docstrings for public functions
- `ruff` for formatting/linting

```python
def create_spec(
    description: str,
    component: Optional[str] = None,
    *,
    no_branch: bool = False,
) -> Path:
    """
    Create a new spec directory with template.
    
    Args:
        description: Brief spec description
        component: Component prefix (e.g., CORE, API)
        no_branch: Skip git branch creation
    
    Returns:
        Path to created spec directory
    """
    ...
```

### CLI Commands

- Use Typer for all CLI
- Rich for output formatting
- Consistent option naming: `--flag`, `-f`
- Always include `--help`

```python
@app.command()
def my_command(
    name: str = typer.Argument(..., help="The name"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
):
    """Short description of what this does."""
    ...
```

### MCP Tools

- Async functions
- Return dicts (JSON-serializable)
- Clear docstrings (shown to Claude)

```python
@mcp.tool()
async def my_tool(param: str) -> dict:
    """
    One-line description for Claude.
    
    Args:
        param: What this parameter does
    
    Returns:
        Dict with result fields
    """
    return {"status": "ok", "data": ...}
```

## Testing

### Unit Tests

```python
# tests/test_config.py
def test_config_load_default():
    config = Config.load()
    assert config.spec_id.padding == 3

def test_config_generate_spec_id():
    config = Config()
    config.spec_id.template = "{component}-{NNN}-{slug}"
    
    result = config.spec_id.generate("user-auth", 1, "CORE")
    assert result == "CORE-001-user-auth"
```

### Integration Tests

```python
# tests/test_cli.py
from typer.testing import CliRunner
from spectrena import app

runner = CliRunner()

def test_new_spec(tmp_path):
    with runner.isolated_filesystem(temp_dir=tmp_path):
        # Setup
        (tmp_path / "specs").mkdir()
        
        result = runner.invoke(app, ["new", "-c", "CORE", "Test"])
        
        assert result.exit_code == 0
        assert (tmp_path / "specs" / "CORE-001-test").exists()
```

## Documentation

- README.md: Overview and quick reference
- QUICKSTART.md: Getting started guide
- CONFIGURATION.md: Full config reference
- Docstrings: API documentation

When updating features:
1. Update relevant docs
2. Update command help text
3. Add examples where helpful

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create PR, get review
4. Merge to main
5. Tag release: `git tag v0.2.0`
6. Build and publish:

```bash
python -m build
twine upload dist/*
```

## Questions?

- Open an issue for bugs/features
- Discussions for questions
- PRs welcome!
