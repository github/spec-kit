# Local Testing Guide for Fish Shell Support

## Overview

This guide explains how to test fish shell support locally before creating a GitHub release.

## IMPORTANT: Temporary Changes to Revert

The following files have been **temporarily modified** for local testing. **REVERT BEFORE COMMIT**:

### 1. `src/specify_cli/__init__.py`
- Lines 446-474: Added local template detection via `SPECIFY_LOCAL_TEMPLATES` env var
- Search for: `# TEMPORARY: LOCAL TESTING - REVERT BEFORE COMMIT`

### 2. `.github/workflows/scripts/create-release-packages.sh`
- Lines 120-132: Fixed macOS compatibility for `cp --parents`
- Lines 209-220: Fixed return code logic in `validate_subset()` function
- Search for: `# TEMPORARY` comments

## Testing Steps

### 1. Build Local Packages

Build test packages (supports filtering by agent/script):

```bash
cd /Volumes/Development/spec-kit

# Build specific agent/script combination
AGENTS=cursor SCRIPTS=fish bash .github/workflows/scripts/create-release-packages.sh v0.0.18

# Build all fish packages (all agents)
SCRIPTS=fish bash .github/workflows/scripts/create-release-packages.sh v0.0.18

# Build all packages
bash .github/workflows/scripts/create-release-packages.sh v0.0.18
```

Packages will be created in `.genreleases/` directory.

### 2. Test with Local Packages

Use the `SPECIFY_LOCAL_TEMPLATES` environment variable to test:

```bash
# Basic test with cursor + fish
SPECIFY_LOCAL_TEMPLATES=1 uv run specify init ../test-fish-project --ai cursor --script fish --no-git

# Test with different agent
SPECIFY_LOCAL_TEMPLATES=1 uv run specify init ../test-claude-fish --ai claude --script fish --no-git

# Interactive mode (will prompt for agent/script)
SPECIFY_LOCAL_TEMPLATES=1 uv run specify init ../test-interactive --no-git
```

### 3. Verify Project Structure

Check that fish scripts were correctly installed:

```bash
ls -la ../test-fish-project/.specify/scripts/fish/
# Should show:
# - check-prerequisites.fish
# - common.fish
# - create-new-feature.fish
# - setup-plan.fish
# - update-agent-context.fish

# Verify commands reference fish scripts
grep -r "scripts/fish" ../test-fish-project/.cursor/commands/
```

### 4. Test Fish Scripts

Test that the fish scripts actually work:

```bash
cd ../test-fish-project

# Test check prerequisites
fish .specify/scripts/fish/check-prerequisites.fish --help

# Test create feature
fish .specify/scripts/fish/create-new-feature.fish "Test Feature"

# Test setup plan
fish .specify/scripts/fish/setup-plan.fish --json
```

## Package Contents

Each package (e.g., `spec-kit-template-cursor-fish-v0.0.18.zip`) contains:

```
.cursor/commands/          # Agent-specific command files
  ├── analyze.md
  ├── clarify.md
  ├── constitution.md
  ├── implement.md
  ├── plan.md
  ├── specify.md
  └── tasks.md
.specify/
  ├── memory/
  │   └── constitution.md
  ├── scripts/
  │   └── fish/            # Fish shell scripts
  │       ├── check-prerequisites.fish
  │       ├── common.fish
  │       ├── create-new-feature.fish
  │       ├── setup-plan.fish
  │       └── update-agent-context.fish
  └── templates/
      ├── agent-file-template.md
      ├── plan-template.md
      ├── spec-template.md
      └── tasks-template.md
```

## Known Issues

### macOS Compatibility Issue (Line 120)

The original script uses `cp --parents` which is GNU coreutils only. The temporary fix uses a while loop with `mkdir -p` instead. This works on macOS but needs to be reverted for Linux CI/CD.

### Validation Logic Bug (Lines 207-220)

The `validate_subset()` function had inverted return codes (0=failure, 1=success). This is temporarily fixed but needs to be reverted or properly fixed in the main codebase.

## Cleanup

After testing, remove test projects and packages:

```bash
# Remove test projects
rm -rf ../test-*-project ../test-*-fish

# Remove generated packages
rm -rf /Volumes/Development/spec-kit/.genreleases
```

## Before Committing

**CRITICAL**: Revert all temporary changes before committing:

1. Revert `src/specify_cli/__init__.py` (lines 446-474)
2. Revert `.github/workflows/scripts/create-release-packages.sh` (lines 120-132, 209-220)
3. Remove this testing guide: `rm LOCAL-TESTING-GUIDE.md`

Search for `# TEMPORARY` or `REVERT BEFORE COMMIT` to find all temporary code.

## Next Steps After Testing

Once local testing is complete and fish support is validated:

1. Revert all temporary changes
2. Fix the bugs properly in the release script (if needed)
3. Commit fish shell changes
4. Create GitHub release (fish packages will be built by CI/CD)
5. Test with production release: `uv run specify init test --ai cursor --script fish`
