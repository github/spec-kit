# Support

## How to Get Help

### Documentation

- [README.md](./README.md) - Quick start and command reference
- [QUICKSTART.md](./QUICKSTART.md) - Step-by-step getting started guide
- [CONFIGURATION.md](./CONFIGURATION.md) - Full configuration reference
- [AGENTS.md](./AGENTS.md) - Multi-agent support documentation
- [CONTRIBUTING.md](./CONTRIBUTING.md) - Development setup and guidelines

### Issues and Discussions

- **Bug reports**: [Open a GitHub issue](https://github.com/rghsoftware/spectrena/issues/new?template=bug_report.md)
- **Feature requests**: [Open a GitHub issue](https://github.com/rghsoftware/spectrena/issues/new?template=feature_request.md)
- **Questions**: [Start a GitHub discussion](https://github.com/rghsoftware/spectrena/discussions)

Please search existing issues and discussions before creating new ones to avoid duplicates.

## Common Issues

### Installation

**Problem**: `spectrena` command not found after install

```bash
# Check if installed
uv tool list | grep spectrena

# Reinstall
uv tool install spectrena[lineage-surreal]

# Verify PATH includes ~/.local/bin
echo $PATH | grep -q ".local/bin" || echo "Add ~/.local/bin to PATH"
```

**Problem**: MCP server won't start

```bash
# Check if lineage dependencies installed
spectrena-mcp --help

# If missing, reinstall with lineage support
uv tool install spectrena[lineage-surreal]
```

### Configuration

**Problem**: Spec IDs not generating correctly

```bash
# Check current config
spectrena config --show

# Verify template format
# Valid: "{component}-{NNN}-{slug}"
# Invalid: "{COMPONENT}-{nnn}-{slug}"  (wrong case)
```

**Problem**: Components not validating

```yaml
# In .spectrena/config.yml
spec_id:
  components: [CORE, API, UI]  # Must be uppercase

workflow:
  validate_components: true    # Set to false to disable validation
```

### Worktrees

**Problem**: `sw` commands not finding specs

```bash
# Check you're in a git repository
git status

# Check spec branches exist
git branch | grep spec/

# Check deps.mermaid exists
cat deps.mermaid
```

### Lineage

**Problem**: Lineage database errors

```bash
# Check lineage is enabled
spectrena config --show | grep enabled

# Check database path
ls -la .spectrena/lineage/

# Reset database (loses history)
rm -rf .spectrena/lineage/
# Database recreated on next operation
```

## Project Status

Spectrena is under active development. We aim to respond to:

- **Security issues**: Within 48 hours
- **Bug reports**: Within 1 week
- **Feature requests**: As capacity allows

## Related Projects

- [spec-kit](https://github.com/github/spec-kit) - The original toolkit Spectrena is based on
- [Serena](https://github.com/oraios/serena) - Semantic code editing (forked for lineage integration)
- [SurrealDB](https://surrealdb.com/) - Database used for lineage tracking

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md) for development setup and guidelines.
