---
description: Configure Claude Code skills and hooks for the current project to automate tests, linters, and setup tasks.
scripts:
  sh: scripts/bash/setup-hooks.sh --json
  ps: scripts/powershell/setup-hooks.ps1 -Json
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

This command sets up Claude Code skills and hooks for your project, enabling automated workflows for:

- **SessionStart**: Automatic dependency installation when Claude starts
- **PostToolUse**: Auto-formatting and linting after file edits
- **Stop**: Run tests and checks before session ends

1. Run `{SCRIPT}` from repo root and parse the JSON output containing:
   - `PROJECT_TYPE`: Detected project type (node, python, rust, go, java, dotnet, ruby, php, generic)
   - `DETECTED_TOOLS`: List of detected tools (package managers, test runners, linters)
   - `CLAUDE_DIR`: Path to `.claude/` directory
   - `SETTINGS_FILE`: Path to `.claude/settings.json`
   - `SKILLS_DIR`: Path to `.claude/skills/` directory
   - `HOOKS_DIR`: Path to `.claude/hooks/` directory

2. **Analyze User Input** (if provided):
   - Parse user preferences from `$ARGUMENTS`
   - Supported options:
     - `--minimal`: Only SessionStart hook (dependency install)
     - `--full`: All hooks (SessionStart, PostToolUse, Stop)
     - `--no-format`: Skip auto-formatting hooks
     - `--no-tests`: Skip test-running hooks
     - Custom hook requests (e.g., "add a hook to run eslint")

3. **Review Detected Configuration**:
   - Present the detected project type and tools to user
   - Show what hooks and skills will be created
   - Ask for confirmation before proceeding

   Example output:
   ```
   Detected Project Configuration:
   ├── Project Type: node (TypeScript)
   ├── Package Manager: npm
   ├── Test Runner: jest
   ├── Linter: eslint
   └── Formatter: prettier

   Proposed Hooks:
   ├── SessionStart: npm install
   ├── PostToolUse[Edit|Write]: prettier --write
   └── Stop: npm test

   Proposed Skills:
   └── testing-skill: Run and write tests with jest

   Proceed with setup? (yes/no/customize)
   ```

4. **Create Directory Structure**:
   - Ensure `.claude/` directory exists
   - Create `.claude/hooks/` for hook scripts
   - Create `.claude/skills/` for skill definitions

5. **Generate Hook Scripts** based on project type:

   **For Node.js/TypeScript projects**:
   - `hooks/session-setup.sh`: `npm install` or `yarn install` or `pnpm install`
   - `hooks/auto-format.sh`: Run prettier/eslint on edited files
   - `hooks/pre-commit-checks.sh`: Run tests and type-check

   **For Python projects**:
   - `hooks/session-setup.sh`: `pip install -r requirements.txt` or `poetry install`
   - `hooks/auto-format.sh`: Run black/ruff on edited files
   - `hooks/pre-commit-checks.sh`: Run pytest and mypy

   **For Rust projects**:
   - `hooks/session-setup.sh`: `cargo build` (compile dependencies)
   - `hooks/auto-format.sh`: `cargo fmt` on edited files
   - `hooks/pre-commit-checks.sh`: `cargo test` and `cargo clippy`

   **For Go projects**:
   - `hooks/session-setup.sh`: `go mod download`
   - `hooks/auto-format.sh`: `gofmt -w` on edited files
   - `hooks/pre-commit-checks.sh`: `go test ./...` and `go vet`

   **For generic projects**:
   - `hooks/session-setup.sh`: Display project status (git status, recent changes)
   - Skip auto-format if no formatter detected
   - Skip tests if no test runner detected

6. **Generate Settings File** (`.claude/settings.json`):

   Create or update the settings file with hook configuration:

   ```json
   {
     "$schema": "https://json.schemastore.org/claude-code-settings.json",
     "permissions": {
       "allow": ["Skill"]
     },
     "hooks": {
       "SessionStart": [
         {
           "hooks": [
             {
               "type": "command",
               "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/session-setup.sh"
             }
           ]
         }
       ],
       "PostToolUse": [
         {
           "matcher": "Edit|Write",
           "hooks": [
             {
               "type": "command",
               "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/auto-format.sh"
             }
           ]
         }
       ],
       "Stop": [
         {
           "hooks": [
             {
               "type": "command",
               "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/pre-commit-checks.sh"
             }
           ]
         }
       ]
     }
   }
   ```

7. **Generate Skills** (optional, based on project):

   **Testing Skill** (`.claude/skills/testing-skill/SKILL.md`):
   ```yaml
   ---
   name: testing-skill
   description: Run and write tests for this project. Activate when implementing features, fixing bugs, or ensuring test coverage.
   ---

   # Testing Skill

   ## Test Commands

   [Generated based on detected test runner]

   ## Writing Tests

   [Generated based on project structure]
   ```

   **Linting Skill** (`.claude/skills/linting-skill/SKILL.md`):
   ```yaml
   ---
   name: linting-skill
   description: Run linting and code formatting tools. Use when code quality needs improvement or before committing.
   ---

   # Linting Skill

   ## Linting Commands

   [Generated based on detected linter/formatter]
   ```

8. **Make Hook Scripts Executable**:
   - Run `chmod +x` on all generated hook scripts
   - Verify scripts are valid bash

9. **Validation and Testing**:
   - Dry-run the SessionStart hook to verify it works
   - Check that the settings.json is valid JSON
   - Verify skill files have valid YAML frontmatter

10. **Report Completion**:
    - List all created files
    - Show a summary of configured hooks and skills
    - Provide instructions for testing:
      ```
      Setup Complete!

      Created files:
      ├── .claude/settings.json
      ├── .claude/hooks/session-setup.sh
      ├── .claude/hooks/auto-format.sh
      ├── .claude/hooks/pre-commit-checks.sh
      └── .claude/skills/testing-skill/SKILL.md

      To test your setup:
      1. Start a new Claude Code session in this project
      2. The SessionStart hook will run automatically
      3. Edit a file to trigger the PostToolUse hook
      4. Use /clear to reset and re-trigger SessionStart

      Next steps:
      - Customize hooks in .claude/hooks/ as needed
      - Add more skills in .claude/skills/
      - Review .claude/settings.json for advanced options
      ```

## Hook Script Templates

### Session Setup Hook (session-setup.sh)

```bash
#!/bin/bash
set -e

# Session setup hook - runs when Claude Code starts
# This script's stdout is injected into Claude's context

echo "=== Project Setup ==="

# Detect and run package manager
if [ -f "package-lock.json" ]; then
  echo "Installing npm dependencies..."
  npm install --silent
elif [ -f "yarn.lock" ]; then
  echo "Installing yarn dependencies..."
  yarn install --silent
elif [ -f "pnpm-lock.yaml" ]; then
  echo "Installing pnpm dependencies..."
  pnpm install --silent
elif [ -f "requirements.txt" ]; then
  echo "Installing Python dependencies..."
  pip install -r requirements.txt -q
elif [ -f "Cargo.toml" ]; then
  echo "Building Rust project..."
  cargo build --quiet
elif [ -f "go.mod" ]; then
  echo "Downloading Go modules..."
  go mod download
fi

# Show project status
echo ""
echo "=== Current Status ==="
echo "Git branch: $(git branch --show-current 2>/dev/null || echo 'not a git repo')"
echo "Changed files: $(git status --short 2>/dev/null | wc -l | tr -d ' ') files"

exit 0
```

### Auto-Format Hook (auto-format.sh)

```bash
#!/bin/bash

# Auto-format hook - runs after Edit/Write operations
# Receives tool input as JSON via stdin

input=$(cat)
filepath=$(echo "$input" | jq -r '.tool_input.file_path // empty')

if [ -z "$filepath" ]; then
  exit 0
fi

# Get file extension
ext="${filepath##*.}"

case "$ext" in
  ts|tsx|js|jsx|json)
    if command -v prettier &> /dev/null; then
      prettier --write "$filepath" 2>/dev/null || true
    fi
    ;;
  py)
    if command -v black &> /dev/null; then
      black "$filepath" 2>/dev/null || true
    elif command -v ruff &> /dev/null; then
      ruff format "$filepath" 2>/dev/null || true
    fi
    ;;
  rs)
    if command -v rustfmt &> /dev/null; then
      rustfmt "$filepath" 2>/dev/null || true
    fi
    ;;
  go)
    if command -v gofmt &> /dev/null; then
      gofmt -w "$filepath" 2>/dev/null || true
    fi
    ;;
esac

exit 0
```

### Pre-Commit Checks Hook (pre-commit-checks.sh)

```bash
#!/bin/bash

# Pre-commit checks hook - runs when Claude finishes responding
# Use exit code 0 to show info, exit code 2 to block with feedback

echo "=== Running Pre-Commit Checks ==="

# Detect and run tests
if [ -f "package.json" ]; then
  if grep -q '"test"' package.json; then
    echo "Running npm tests..."
    npm test --silent || echo "Tests failed (non-blocking)"
  fi
elif [ -f "pytest.ini" ] || [ -f "pyproject.toml" ]; then
  echo "Running pytest..."
  python -m pytest --tb=short -q || echo "Tests failed (non-blocking)"
elif [ -f "Cargo.toml" ]; then
  echo "Running cargo tests..."
  cargo test --quiet || echo "Tests failed (non-blocking)"
elif [ -f "go.mod" ]; then
  echo "Running go tests..."
  go test ./... -v || echo "Tests failed (non-blocking)"
fi

echo "Checks complete"
exit 0
```

## Guidelines

### When to Use This Command

- After initializing a new project with `/speckit.specify`
- When setting up an existing project for Claude Code
- When you want to automate repetitive development tasks

### Customization Options

Users can customize the setup by providing arguments:
- `--minimal`: Only install dependencies on session start
- `--full`: Enable all hooks (format, lint, test)
- `--skip-skills`: Don't create skill files
- Custom requests like "add ESLint pre-commit check"

### Security Considerations

- Hook scripts should not contain secrets
- Use `$CLAUDE_PROJECT_DIR` for portable paths
- Scripts should be idempotent (safe to run multiple times)
- Avoid hooks that modify files outside the project
