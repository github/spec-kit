# Scripts Directory

This directory contains utility scripts for Specify CLI development and project management.

## Development Scripts

### Local Development Installation

Install Specify CLI locally for development and testing:

#### PowerShell (Windows)

```powershell
# Install from default location (C:\git\spec-kit-4applens)
.\scripts\powershell\install-local-dev.ps1

# Install from custom location
.\scripts\powershell\install-local-dev.ps1 -SpecKitPath "D:\repos\spec-kit-4applens"

# Skip copying GitHub Copilot prompt file
.\scripts\powershell\install-local-dev.ps1 -SkipPromptFile

# Force reinstallation
.\scripts\powershell\install-local-dev.ps1 -Force

# Show help
.\scripts\powershell\install-local-dev.ps1 -?
```

#### Bash (Linux/macOS)

```bash
# Install from default location ($HOME/git/spec-kit-4applens)
./scripts/bash/install-local-dev.sh

# Install from custom location
./scripts/bash/install-local-dev.sh --spec-kit-path "/opt/repos/spec-kit-4applens"

# Skip copying GitHub Copilot prompt file
./scripts/bash/install-local-dev.sh --skip-prompt-file

# Force reinstallation
./scripts/bash/install-local-dev.sh --force

# Show help
./scripts/bash/install-local-dev.sh --help
```

**What these scripts do:**

1. ✅ Validate the Specify CLI source code location
2. ✅ Check Python and pip installation
3. ✅ Uninstall previous version (if exists)
4. ✅ Install CLI in editable mode with Bicep support: `pip install -e ".[bicep]"`
5. ✅ Copy `.github/prompts/speckit.bicep.prompt.md` to your test project
6. ✅ Verify installation and show next steps

**Benefits of editable mode (`-e` flag):**

- Changes to source code are immediately reflected
- No need to reinstall after each change
- Perfect for development and testing
- Easy to uninstall: `pip uninstall specify-cli`

## Project Management Scripts

### Bash Scripts (`scripts/bash/`)

- `check-prerequisites.sh` - Verify project prerequisites and requirements
- `common.sh` - Shared utility functions for bash scripts
- `create-new-feature.sh` - Scaffold new feature specifications
- `setup-plan.sh` - Initialize planning documents
- `update-agent-context.sh` - Update AI agent context files

### PowerShell Scripts (`scripts/powershell/`)

- `check-prerequisites.ps1` - Verify project prerequisites and requirements
- `common.ps1` - Shared utility functions for PowerShell scripts
- `create-new-feature.ps1` - Scaffold new feature specifications
- `setup-plan.ps1` - Initialize planning documents
- `update-agent-context.ps1` - Update AI agent context files

## Usage in Projects

When you run `specify init`, these scripts are copied to your project's `.specify/scripts/` directory and can be used for project management tasks.

### Example: Check Prerequisites

```bash
# Bash
.specify/scripts/bash/check-prerequisites.sh --json

# PowerShell
.specify/scripts/powershell/check-prerequisites.ps1 -Json
```

### Example: Create New Feature

```bash
# Bash
.specify/scripts/bash/create-new-feature.sh --feature-name "user-authentication"

# PowerShell
.specify/scripts/powershell/create-new-feature.ps1 -FeatureName "user-authentication"
```

## Script Conventions

- **Bash scripts**: Use `.sh` extension, start with `#!/usr/bin/env bash`
- **PowerShell scripts**: Use `.ps1` extension, include help documentation
- **Common functions**: Shared code in `common.sh` and `common.ps1`
- **Error handling**: Scripts use `set -euo pipefail` (bash) and `$ErrorActionPreference = "Stop"` (PowerShell)
- **Output formatting**: Consistent use of colors and symbols (✅ ❌ ⚠️ ℹ️)

## Contributing

When adding new scripts:

1. Create both bash and PowerShell versions for cross-platform support
2. Include help documentation (`--help` for bash, `-?` for PowerShell)
3. Use consistent output formatting (colors, symbols)
4. Add error handling and validation
5. Update this README with script description and usage examples

---

For more information, see the [main project README](../README.md).
