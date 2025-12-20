---
description: Configure Claude Code skills and hooks for the current project to automate tests, linters, setup tasks, and generate architecture/best practices skills from framework documentation.
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
- **Architecture Skills**: Best practices and patterns from detected frameworks
- **Coding Guidelines**: Framework-specific coding standards fetched from official docs

1. Run `{SCRIPT}` from repo root and parse the JSON output containing:
   - `PROJECT_TYPE`: Detected project type (node, node-typescript, python, rust, go, java-maven, java-gradle, scala-sbt, scala-mill, dotnet, ruby, php, generic)
   - `DETECTED_TOOLS`: List of detected tools (package managers, test runners, linters)
   - `DETECTED_FRAMEWORKS`: List of detected frameworks with their documentation URLs:
     ```json
     [
       {"name": "react", "docs_url": "https://react.dev", "github_url": "https://github.com/facebook/react"},
       {"name": "next", "docs_url": "https://nextjs.org/docs", "github_url": "https://github.com/vercel/next.js"}
     ]
     ```
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
   - Present the detected project type, tools, and frameworks to user
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

   Detected Frameworks:
   ├── react (https://react.dev)
   ├── next (https://nextjs.org/docs)
   └── tailwind (https://tailwindcss.com/docs)

   Proposed Hooks:
   ├── SessionStart: npm install
   ├── PostToolUse[Edit|Write]: prettier --write
   └── Stop: npm test

   Proposed Skills:
   ├── testing-skill: Run and write tests with jest
   ├── react-architecture: React patterns and best practices
   ├── nextjs-patterns: Next.js App Router conventions
   └── tailwind-guidelines: Tailwind CSS utility patterns

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

   **For Scala projects (sbt/Mill)**:
   - `hooks/session-setup.sh`: `sbt compile` or `mill compile`
   - `hooks/auto-format.sh`: `scalafmt` on edited files
   - `hooks/pre-commit-checks.sh`: `sbt test` or `mill test`

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

7. **Generate Skills** (based on detected tools and frameworks):

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

8. **Generate Framework Architecture Skills** (CRITICAL - for each detected framework):

   For EACH framework in `DETECTED_FRAMEWORKS`, create a skill by fetching documentation:

   **Step 8.1: Fetch Framework Documentation**

   For each framework, use WebFetch to retrieve best practices:

   - **Primary source**: Fetch the `docs_url` from the framework entry
   - **Fallback**: If docs_url fails, fetch the README from `github_url`
   - **Key pages to fetch** (append to docs_url):
     - `/getting-started` or `/introduction`
     - `/best-practices` or `/patterns`
     - `/architecture` or `/project-structure`
     - `/api-reference` (for key APIs)

   **Step 8.2: Extract Key Information**

   From the fetched documentation, extract:
   - **Architecture patterns**: Recommended project structure, component organization
   - **Best practices**: Do's and don'ts, common pitfalls
   - **Coding conventions**: Naming conventions, file organization
   - **Performance tips**: Optimization strategies
   - **Security guidelines**: Common vulnerabilities to avoid

   **Step 8.3: Create Framework Skill**

   Create `.claude/skills/{framework}-architecture/SKILL.md`:

   ```yaml
   ---
   name: {framework}-architecture
   description: Architecture patterns, best practices, and coding guidelines for {Framework Name}. Activate when building features, reviewing code, or making architectural decisions with {Framework Name}.
   ---

   # {Framework Name} Architecture & Best Practices

   > Generated from official documentation: {docs_url}
   > Last updated: {current_date}

   ## Project Structure

   [Recommended directory structure from docs]

   ## Core Patterns

   [Key architectural patterns: components, hooks, state management, etc.]

   ## Best Practices

   ### Do's
   [List of recommended practices]

   ### Don'ts
   [Common anti-patterns to avoid]

   ## Coding Conventions

   [Naming conventions, file organization, import patterns]

   ## Performance Guidelines

   [Optimization tips, lazy loading, memoization patterns]

   ## Security Considerations

   [XSS prevention, input validation, authentication patterns]

   ## Common Patterns

   ### [Pattern 1 Name]
   ```{language}
   // Example code
   ```

   ### [Pattern 2 Name]
   ```{language}
   // Example code
   ```

   ## References

   - [Official Documentation]({docs_url})
   - [GitHub Repository]({github_url})
   ```

   **Example Skills to Generate**:

   | Framework | Skill Name | Key Content |
   |-----------|------------|-------------|
   | React | react-architecture | Component patterns, hooks rules, state management |
   | Next.js | nextjs-patterns | App Router, Server Components, data fetching |
   | Vue | vue-architecture | Composition API, reactivity, component design |
   | Django | django-patterns | MTV pattern, ORM best practices, security |
   | FastAPI | fastapi-architecture | Dependency injection, async patterns, Pydantic |
   | Spring | spring-patterns | IoC, annotations, layered architecture |
   | Scala/ZIO | zio-patterns | Effect system, error handling, resource management |
   | Rust/Axum | axum-patterns | Handler patterns, extractors, error handling |

9. **Generate Language-Specific Best Practices Skill**:

   Based on `PROJECT_TYPE`, create a general coding standards skill:

   **For TypeScript projects** (`.claude/skills/typescript-standards/SKILL.md`):
   ```yaml
   ---
   name: typescript-standards
   description: TypeScript coding standards and type safety best practices. Activate when writing or reviewing TypeScript code.
   ---

   # TypeScript Coding Standards

   ## Type Safety

   - Prefer `unknown` over `any`
   - Use strict mode (`"strict": true` in tsconfig)
   - Define explicit return types for public APIs
   - Use discriminated unions for complex types

   ## Naming Conventions

   - PascalCase for types, interfaces, classes, enums
   - camelCase for variables, functions, methods
   - SCREAMING_SNAKE_CASE for constants
   - Prefix interfaces with `I` only if project convention

   ## Code Organization

   - One component/class per file
   - Group imports: external, internal, relative
   - Export types separately from implementations

   ## Error Handling

   - Use Result/Either patterns for expected errors
   - Throw only for unexpected errors
   - Always type catch blocks: `catch (error: unknown)`
   ```

   **For Python projects** (`.claude/skills/python-standards/SKILL.md`):
   - PEP 8 style guide
   - Type hints best practices
   - Async/await patterns
   - Error handling with context managers

   **For Scala projects** (`.claude/skills/scala-standards/SKILL.md`):
   - Functional programming patterns
   - Effect systems (ZIO, Cats Effect)
   - Implicits and type classes
   - Error handling with Either/Option

10. **Make Hook Scripts Executable**:
    - Run `chmod +x` on all generated hook scripts
    - Verify scripts are valid bash

11. **Validation and Testing**:
    - Dry-run the SessionStart hook to verify it works
    - Check that the settings.json is valid JSON
    - Verify skill files have valid YAML frontmatter

12. **Report Completion**:
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
      ├── .claude/skills/testing-skill/SKILL.md
      ├── .claude/skills/linting-skill/SKILL.md
      ├── .claude/skills/react-architecture/SKILL.md      (if React detected)
      ├── .claude/skills/nextjs-patterns/SKILL.md         (if Next.js detected)
      └── .claude/skills/typescript-standards/SKILL.md    (if TypeScript detected)

      Framework Skills Generated:
      ├── react-architecture: React patterns and best practices
      ├── nextjs-patterns: Next.js App Router conventions
      └── typescript-standards: TypeScript coding standards

      To test your setup:
      1. Start a new Claude Code session in this project
      2. The SessionStart hook will run automatically
      3. Edit a file to trigger the PostToolUse hook
      4. Use /clear to reset and re-trigger SessionStart
      5. Skills will auto-activate based on your task context

      Next steps:
      - Customize hooks in .claude/hooks/ as needed
      - Review generated architecture skills for accuracy
      - Add project-specific patterns to skills
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
