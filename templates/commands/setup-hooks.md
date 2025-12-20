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

   For EACH framework in `DETECTED_FRAMEWORKS`, create a skill following the official Anthropic skill structure.

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

   **Step 8.3: Create Framework Skill Directory Structure**

   Create the skill folder with the following structure:
   ```
   .claude/skills/{framework}-architecture/
   ├── SKILL.md              (required - lean instructions)
   ├── references/
   │   ├── patterns.md       (detailed architectural patterns)
   │   ├── best-practices.md (do's, don'ts, anti-patterns)
   │   └── examples.md       (code examples and snippets)
   └── assets/               (optional - templates, configs)
   ```

   **Step 8.4: Create SKILL.md** (keep it lean - context is precious)

   Create `.claude/skills/{framework}-architecture/SKILL.md`:

   ```yaml
   ---
   name: {framework}-architecture
   description: |
     Build and architect {Framework Name} applications following official best practices.
     Use when: building features, reviewing code, making architecture decisions,
     or when user mentions "{framework}", "design", "architecture", or "best practices".
   ---

   # {Framework Name} Architecture

   > Auto-generated from official documentation. See references/ for detailed patterns.

   ## Core Principles

   [3-5 bullet points of essential architectural principles]

   ## Quick Reference

   | Aspect | Recommendation |
   |--------|----------------|
   | Project Structure | [one-liner] |
   | State Management | [one-liner] |
   | Error Handling | [one-liner] |
   | Testing | [one-liner] |

   ## Critical Don'ts

   - [Anti-pattern 1 - brief]
   - [Anti-pattern 2 - brief]
   - [Anti-pattern 3 - brief]

   ## When to Load References

   - For detailed patterns: `Read references/patterns.md`
   - For best practices: `Read references/best-practices.md`
   - For code examples: `Read references/examples.md`

   ## External Resources

   - [Official Docs]({docs_url})
   - [GitHub]({github_url})
   ```

   **Step 8.5: Create references/patterns.md** (detailed architecture)

   ```markdown
   # {Framework Name} Architectural Patterns

   > Generated from: {docs_url}
   > Last updated: {current_date}

   ## Project Structure

   [Recommended directory structure with explanations]

   ## Core Patterns

   ### [Pattern 1: e.g., Component Composition]
   [Detailed explanation with rationale]

   ```{language}
   // Example implementation
   ```

   ### [Pattern 2: e.g., State Management]
   [Detailed explanation]

   ```{language}
   // Example implementation
   ```

   [Continue for all major patterns...]
   ```

   **Step 8.6: Create references/best-practices.md**

   ```markdown
   # {Framework Name} Best Practices

   ## Do's ✓

   ### [Practice 1]
   [Why and how]

   ### [Practice 2]
   [Why and how]

   ## Don'ts ✗

   ### [Anti-pattern 1]
   [Why it's bad and what to do instead]

   ### [Anti-pattern 2]
   [Why it's bad and what to do instead]

   ## Performance Guidelines

   [Optimization strategies specific to this framework]

   ## Security Considerations

   [Security best practices for this framework]
   ```

   **Step 8.7: Create references/examples.md**

   ```markdown
   # {Framework Name} Code Examples

   ## Common Patterns

   ### [Example 1: Basic Setup]
   ```{language}
   // Complete working example
   ```

   ### [Example 2: Advanced Pattern]
   ```{language}
   // Complete working example
   ```

   ## Templates

   [Reusable code templates for common scenarios]
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

   Based on `PROJECT_TYPE`, create a language coding standards skill with the same structure:

   ```
   .claude/skills/{language}-standards/
   ├── SKILL.md
   └── references/
       ├── conventions.md
       ├── patterns.md
       └── anti-patterns.md
   ```

   **For TypeScript projects** (`.claude/skills/typescript-standards/`):

   `SKILL.md`:
   ```yaml
   ---
   name: typescript-standards
   description: |
     TypeScript coding standards and type safety best practices.
     Use when: writing TypeScript code, reviewing PRs, or when user asks about
     "types", "type safety", "TypeScript conventions", or "strict mode".
   ---

   # TypeScript Standards

   ## Core Rules

   - Prefer `unknown` over `any` - narrowing is safer than casting
   - Enable `"strict": true` in tsconfig - no exceptions
   - Define explicit return types for public APIs
   - Use discriminated unions for complex types

   ## Quick Reference

   | Element | Convention |
   |---------|------------|
   | Types/Interfaces | PascalCase |
   | Variables/Functions | camelCase |
   | Constants | SCREAMING_SNAKE_CASE |
   | Files | kebab-case.ts |

   ## Critical Don'ts

   - Never use `any` without explicit justification
   - Never ignore TypeScript errors with @ts-ignore
   - Never use non-null assertion operator without validation

   ## References

   - For detailed conventions: Read references/conventions.md
   - For advanced patterns: Read references/patterns.md
   ```

   **For Python projects** (`.claude/skills/python-standards/`):
   - PEP 8 style guide essentials
   - Type hints best practices (PEP 484, 585)
   - Async/await patterns
   - Context managers for resource handling
   - references/conventions.md with detailed PEP 8

   **For Scala projects** (`.claude/skills/scala-standards/`):
   - Functional programming core principles
   - Effect systems patterns (ZIO, Cats Effect)
   - Implicits and type classes usage
   - Error handling with Either/Option/Try
   - references/fp-patterns.md with detailed examples

   **For Rust projects** (`.claude/skills/rust-standards/`):
   - Ownership and borrowing rules
   - Error handling with Result/Option
   - Trait-based design patterns
   - Memory safety best practices

   **For Go projects** (`.claude/skills/go-standards/`):
   - Effective Go principles
   - Error handling patterns
   - Interface design
   - Concurrency with goroutines/channels

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
      ├── .claude/hooks/
      │   ├── session-setup.sh
      │   ├── auto-format.sh
      │   └── pre-commit-checks.sh
      ├── .claude/skills/testing-skill/
      │   └── SKILL.md
      ├── .claude/skills/linting-skill/
      │   └── SKILL.md
      ├── .claude/skills/react-architecture/    (if React detected)
      │   ├── SKILL.md
      │   └── references/
      │       ├── patterns.md
      │       ├── best-practices.md
      │       └── examples.md
      ├── .claude/skills/nextjs-patterns/       (if Next.js detected)
      │   ├── SKILL.md
      │   └── references/...
      └── .claude/skills/typescript-standards/  (if TypeScript)
          ├── SKILL.md
          └── references/
              ├── conventions.md
              └── patterns.md

      Skills Generated (with references/):
      ├── react-architecture: React patterns and best practices
      ├── nextjs-patterns: Next.js App Router conventions
      └── typescript-standards: TypeScript coding standards

      How Skills Work:
      - Claude auto-activates skills based on your task context
      - SKILL.md provides quick guidance (context-efficient)
      - references/ contains detailed docs loaded on-demand
      - Skills are model-invoked, not user-invoked

      To test your setup:
      1. Start a new Claude Code session in this project
      2. The SessionStart hook will run automatically
      3. Edit a file to trigger the PostToolUse hook
      4. Ask Claude to "design a React component" to see skill activation
      5. Use /clear to reset and re-trigger SessionStart

      Next steps:
      - Customize hooks in .claude/hooks/ as needed
      - Review generated skills for project-specific accuracy
      - Add your own patterns to references/ folders
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
