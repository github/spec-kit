---
description: Complete project setup - configures hooks, skills, agents, and constitution in one command
scripts:
  sh: scripts/bash/setup-hooks.sh --json
  ps: scripts/powershell/setup-hooks.ps1 -Json
---

# SpecKit Project Setup

You are the **Setup Orchestrator**. Complete the full initial setup for this SpecKit project in **3 phases**.

## User Input

```text
$ARGUMENTS
```

**Analyze user preferences** (if provided):
- `--minimal`: Only SessionStart hook (dependency install)
- `--full`: All hooks (SessionStart, PostToolUse, Stop)
- `--no-format`: Skip auto-formatting hooks
- `--no-tests`: Skip test-running hooks
- `--skip-skills`: Don't create skill files
- Custom requests (e.g., "add ESLint pre-commit check")

---

# PHASE 1: Detect Project & Configure Hooks/Skills

## Step 1.1: Run Detection Script

Run `{SCRIPT}` from repo root and parse the JSON output:

```json
{
  "PROJECT_TYPE": "node-typescript | python | rust | go | java-maven | java-gradle | scala-sbt | scala-mill | dotnet | ruby | php | generic",
  "DETECTED_TOOLS": ["npm", "typescript", "jest", ...],
  "DETECTED_FRAMEWORKS": [
    {"name": "react", "docs_url": "https://react.dev", "github_url": "https://github.com/facebook/react"},
    {"name": "next", "docs_url": "https://nextjs.org/docs", "github_url": "https://github.com/vercel/next.js"},
    {"name": "spring", "docs_url": "https://spring.io/guides", "github_url": "https://github.com/spring-projects/spring-boot"}
  ],
  "CLAUDE_DIR": "/path/to/.claude",
  "SETTINGS_FILE": "/path/to/.claude/settings.json",
  "SKILLS_DIR": "/path/to/.claude/skills",
  "HOOKS_DIR": "/path/to/.claude/hooks"
}
```

## Step 1.2: Present Detected Configuration

Show the user what was detected and what will be configured:

```
Detected Project Configuration:
├── Project Type: {PROJECT_TYPE}
├── Package Manager: {PACKAGE_MANAGER}
├── Test Runner: {TEST_RUNNER}
├── Linter: {LINTER}
└── Formatter: {FORMATTER}

Detected Frameworks:
├── {framework1} ({docs_url1})
├── {framework2} ({docs_url2})
└── ...

Proposed Hooks:
├── SessionStart: {install_command}
├── PostToolUse[Edit|Write]: {format_command}
└── Stop: {test_command}

Proposed Skills:
├── testing-skill: Run and write tests
├── linting-skill: Run linting and formatting
├── {framework}-architecture: Patterns and best practices
└── {language}-standards: Coding conventions

Proceed with setup? (yes/no/customize)
```

## Step 1.3: Create Directory Structure

```bash
mkdir -p .claude/hooks
mkdir -p .claude/skills
mkdir -p .claude/agents/speckit
```

## Step 1.4: Generate Hook Scripts

Create hook scripts in `.claude/hooks/` based on PROJECT_TYPE:

### session-setup.sh

```bash
#!/bin/bash
set -e

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
elif [ -f "pyproject.toml" ]; then
  echo "Installing Python dependencies..."
  pip install -e . -q
elif [ -f "Cargo.toml" ]; then
  echo "Building Rust project..."
  cargo build --quiet
elif [ -f "go.mod" ]; then
  echo "Downloading Go modules..."
  go mod download
elif [ -f "pom.xml" ]; then
  echo "Installing Maven dependencies..."
  mvn dependency:resolve -q
elif [ -f "build.gradle" ] || [ -f "build.gradle.kts" ]; then
  echo "Installing Gradle dependencies..."
  ./gradlew build -x test --quiet 2>/dev/null || gradle build -x test --quiet
elif [ -f "build.sbt" ]; then
  echo "Compiling Scala project..."
  sbt compile
fi

# Show project status
echo ""
echo "=== Current Status ==="
echo "Git branch: $(git branch --show-current 2>/dev/null || echo 'not a git repo')"
echo "Changed files: $(git status --short 2>/dev/null | wc -l | tr -d ' ') files"

exit 0
```

### auto-format.sh

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
  java|kt|kts)
    if command -v google-java-format &> /dev/null; then
      google-java-format -i "$filepath" 2>/dev/null || true
    fi
    ;;
  scala|sc)
    if command -v scalafmt &> /dev/null; then
      scalafmt "$filepath" 2>/dev/null || true
    fi
    ;;
esac

exit 0
```

### pre-commit-checks.sh

```bash
#!/bin/bash

# Pre-commit checks hook - runs when Claude finishes responding

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
elif [ -f "pom.xml" ]; then
  echo "Running Maven tests..."
  mvn test -q || echo "Tests failed (non-blocking)"
elif [ -f "build.gradle" ] || [ -f "build.gradle.kts" ]; then
  echo "Running Gradle tests..."
  ./gradlew test --quiet 2>/dev/null || gradle test --quiet || echo "Tests failed (non-blocking)"
elif [ -f "build.sbt" ]; then
  echo "Running sbt tests..."
  sbt test || echo "Tests failed (non-blocking)"
fi

echo "Checks complete"
exit 0
```

## Step 1.5: Generate Settings File

Create `.claude/settings.json`:

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

## Step 1.6: Generate Testing Skill

Create `.claude/skills/testing-skill/SKILL.md`:

```yaml
---
name: testing-skill
description: Run and write tests for this project. Activate when implementing features, fixing bugs, or ensuring test coverage.
---

# Testing Skill

## Test Commands

[Generate based on detected test runner: jest, pytest, cargo test, go test, mvn test, gradle test, sbt test]

## Writing Tests

[Generate based on project structure and test framework conventions]
```

## Step 1.7: Generate Linting Skill

Create `.claude/skills/linting-skill/SKILL.md`:

```yaml
---
name: linting-skill
description: Run linting and code formatting tools. Use when code quality needs improvement or before committing.
---

# Linting Skill

## Linting Commands

[Generate based on detected linter/formatter: eslint, prettier, ruff, black, clippy, golint, checkstyle, scalafmt]
```

## Step 1.8: Generate Framework Architecture Skills

For EACH framework in `DETECTED_FRAMEWORKS`, create a skill:

### Skill Directory Structure

```
.claude/skills/{framework}-architecture/
├── SKILL.md              (required - lean instructions)
└── references/
    ├── patterns.md       (detailed architectural patterns)
    ├── best-practices.md (do's, don'ts, anti-patterns)
    └── examples.md       (code examples and snippets)
```

### Step 1.8.1: Fetch Framework Documentation

Use WebFetch on `docs_url` to retrieve:
- Getting started / introduction
- Best practices / patterns
- Architecture / project structure
- API reference

### Step 1.8.2: Create SKILL.md

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

- [Anti-pattern 1]
- [Anti-pattern 2]
- [Anti-pattern 3]

## When to Load References

- For detailed patterns: `Read references/patterns.md`
- For best practices: `Read references/best-practices.md`
- For code examples: `Read references/examples.md`

## External Resources

- [Official Docs]({docs_url})
- [GitHub]({github_url})
```

### Step 1.8.3: Create references/patterns.md

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

### Step 1.8.4: Create references/best-practices.md

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

### Step 1.8.5: Create references/examples.md

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

## Step 1.9: Generate Language-Specific Standards Skill

Based on `PROJECT_TYPE`, create a language coding standards skill:

### For TypeScript projects (.claude/skills/typescript-standards/)

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

### For Python projects (.claude/skills/python-standards/)

```yaml
---
name: python-standards
description: |
  Python coding standards following PEP 8 and modern best practices.
  Use when: writing Python code, reviewing PRs, or when user asks about
  "PEP 8", "type hints", "Python conventions".
---

# Python Standards

## Core Rules

- Follow PEP 8 style guide
- Use type hints (PEP 484, 585) for all public APIs
- Prefer `pathlib.Path` over `os.path`
- Use context managers for resource handling

## Quick Reference

| Element | Convention |
|---------|------------|
| Classes | PascalCase |
| Functions/Variables | snake_case |
| Constants | SCREAMING_SNAKE_CASE |
| Private | _leading_underscore |

## Critical Don'ts

- Never use mutable default arguments
- Never catch bare exceptions (use specific types)
- Never use `from module import *`
```

### For Java projects (.claude/skills/java-standards/)

```yaml
---
name: java-standards
description: |
  Java coding standards and enterprise best practices.
  Use when: writing Java code, reviewing PRs, or when user asks about
  "Java conventions", "enterprise patterns", "Spring best practices".
---

# Java Standards

## Core Rules

- Follow Google Java Style Guide
- Use final for immutable variables
- Prefer composition over inheritance
- Use Optional for nullable return types

## Quick Reference

| Element | Convention |
|---------|------------|
| Classes/Interfaces | PascalCase |
| Methods/Variables | camelCase |
| Constants | SCREAMING_SNAKE_CASE |
| Packages | lowercase.dot.separated |

## Critical Don'ts

- Never return null from collections (return empty)
- Never catch Exception/Throwable in general code
- Never use raw types (always parameterize generics)
- Never expose mutable internal state

## References

- For Spring patterns: Read references/spring-patterns.md
- For enterprise patterns: Read references/enterprise-patterns.md
```

### For Scala projects (.claude/skills/scala-standards/)

```yaml
---
name: scala-standards
description: |
  Scala functional programming standards and best practices.
  Use when: writing Scala code, using ZIO/Cats Effect, or when user asks about
  "FP patterns", "effect systems", "Scala conventions".
---

# Scala Standards

## Core Rules

- Prefer immutability - use val over var
- Use for-comprehensions for effect composition
- Prefer Option/Either/Try over nulls and exceptions
- Use type classes for polymorphism

## Quick Reference

| Element | Convention |
|---------|------------|
| Classes/Traits | PascalCase |
| Methods/Values | camelCase |
| Type Parameters | Single uppercase (A, B, F) |
| Packages | lowercase |

## Critical Don'ts

- Never use null - use Option
- Never throw exceptions in pure code - use Either/ZIO
- Never use mutable state in shared code
- Never block on Futures/Effects
```

### For Rust projects (.claude/skills/rust-standards/)

```yaml
---
name: rust-standards
description: |
  Rust coding standards and ownership best practices.
  Use when: writing Rust code, reviewing PRs, or when user asks about
  "ownership", "borrowing", "Rust conventions", "memory safety".
---

# Rust Standards

## Core Rules

- Follow ownership and borrowing rules
- Prefer Result/Option over panics
- Use trait-based polymorphism
- Leverage the type system for safety

## Quick Reference

| Element | Convention |
|---------|------------|
| Types/Traits | PascalCase |
| Functions/Variables | snake_case |
| Constants | SCREAMING_SNAKE_CASE |
| Lifetimes | lowercase single letter ('a) |

## Critical Don'ts

- Never use unwrap() in library code
- Never leak memory (use RAII)
- Never use unsafe without justification
```

### For Go projects (.claude/skills/go-standards/)

```yaml
---
name: go-standards
description: |
  Go coding standards following Effective Go.
  Use when: writing Go code, reviewing PRs, or when user asks about
  "Go conventions", "error handling", "goroutines".
---

# Go Standards

## Core Rules

- Follow Effective Go guidelines
- Handle errors explicitly - don't ignore
- Keep interfaces small
- Use goroutines and channels appropriately

## Quick Reference

| Element | Convention |
|---------|------------|
| Exported | PascalCase |
| Unexported | camelCase |
| Acronyms | All caps (HTTP, URL) |
| Packages | lowercase, single word |

## Critical Don'ts

- Never ignore errors (use _ only with intention)
- Never use init() for complex initialization
- Never use naked returns in long functions
```

## Step 1.10: Create Universal Skills (Always Created)

### Code Review Skill (.claude/skills/code-review/)

Copy from `.specify/templates/skills/code-review/` if available, otherwise create:

```
.claude/skills/code-review/
├── SKILL.md
└── references/
    ├── review-checklist.md
    └── security-review.md
```

Content includes:
- Comprehensive review checklist (architecture, code quality, security, performance, testing, documentation, operational)
- OWASP Top 10 security review guide with code examples
- Language-specific security checks

### Tech Debt Skill (.claude/skills/tech-debt/)

Copy from `.specify/templates/skills/tech-debt/` if available, otherwise create:

```
.claude/skills/tech-debt/
├── SKILL.md
└── references/
    ├── debt-patterns.md
    └── refactoring-strategies.md
```

Content includes:
- 14 common debt patterns (God Object, Spaghetti Architecture, Copy-Paste, etc.)
- Safe refactoring principles
- Refactoring techniques (Extract Method, Extract Class, Strangler Fig, etc.)
- Prioritization framework

### Architecture Patterns Skill (.claude/skills/architecture-patterns/)

Copy from `.specify/templates/skills/architecture-patterns/` if available, otherwise create:

```
.claude/skills/architecture-patterns/
├── SKILL.md
└── references/
    ├── implementations.md
    └── ddd-patterns.md
```

Content includes:
- Clean Architecture, Hexagonal Architecture, DDD patterns
- Layer separation and dependency rules
- Production-ready code examples
- Aggregate design, value objects, domain events

### Microservices Patterns Skill (.claude/skills/microservices-patterns/)

Copy from `.specify/templates/skills/microservices-patterns/` if available, otherwise create:

```
.claude/skills/microservices-patterns/
├── SKILL.md
└── references/
    ├── resilience-patterns.md
    └── data-patterns.md
```

Content includes:
- Service decomposition strategies
- Communication patterns (sync/async)
- Resilience patterns (Circuit Breaker, Bulkhead, Retry)
- Data patterns (Saga, Event Sourcing, CQRS, Outbox)

### Architecture Decision Records Skill (.claude/skills/architecture-decision-records/)

Copy from `.specify/templates/skills/architecture-decision-records/` if available, otherwise create:

```
.claude/skills/architecture-decision-records/
├── SKILL.md
└── references/
    ├── templates.md
    └── examples.md
```

Content includes:
- ADR templates (MADR, lightweight, Y-statement, RFC)
- Real-world examples
- Decision process and review checklist

## Step 1.11: Make Hook Scripts Executable

```bash
chmod +x .claude/hooks/session-setup.sh
chmod +x .claude/hooks/auto-format.sh
chmod +x .claude/hooks/pre-commit-checks.sh
```

## Step 1.12: Validate Configuration

- Verify settings.json is valid JSON
- Dry-run the SessionStart hook
- Verify skill files have valid YAML frontmatter

---

# PHASE 2: Create Project Agents

## Step 2.1: Create Agents Directory

```bash
mkdir -p .claude/agents/speckit
```

## Step 2.2: Key Principle - Agents Use Skills

Agents reference skills via the `skills:` frontmatter field. **Skills provide domain expertise; Agents handle workflow orchestration.**

```yaml
---
name: backend-coder
tools: Read, Glob, Grep, Bash, Edit, Write
model: sonnet
skills: java-standards, spring-architecture  # Auto-loaded from .claude/skills/
---
```

## Step 2.3: Create SpecKit Workflow Agents (Primary)

These agents form the **Spec-Driven Development (SDD) pipeline**:

```
Spec → spec-analyzer → designer ──→ implementer → tester → Done
                           ↓              ↑
                    frontend-designer ────┘ (for UI features)
```

### spec-analyzer.md

```markdown
---
name: spec-analyzer
description: |
  Analyzes specification documents to extract requirements, entities, and dependencies.
  Use when: parsing specs, extracting requirements, understanding what to build.
  Invoke for: /breakdown, /design (first step), requirement analysis.
tools: Read, Glob, Grep
model: haiku
---

# Spec Analyzer

You analyze specification documents and extract structured requirements.

## Core Responsibilities

1. **Parse Specifications**: Read spec files, extract functional requirements
2. **Identify Entities**: Find domain objects, their properties, relationships
3. **Map Dependencies**: Determine order of implementation, blockers
4. **Validate Completeness**: Flag missing information, ambiguities

## Workflow Integration

- **Input**: Spec file path(s) from `.speckit/specs/`
- **Output**: Structured analysis (entities, requirements, dependencies)
- **Handoff to**: `designer` agent for technical design

## Output Format

Return structured JSON:
```json
{
  "entities": [{"name": "", "properties": [], "relationships": []}],
  "requirements": [{"id": "", "description": "", "priority": "", "entities": []}],
  "dependencies": [{"from": "", "to": "", "type": ""}],
  "ambiguities": ["..."]
}
```

## Guidelines

- Focus on WHAT, not HOW (that's designer's job)
- Flag unclear requirements rather than assuming
- Use domain language from the spec
```

### designer.md

```markdown
---
name: designer
description: |
  Creates technical designs and architecture from analyzed specifications.
  Use when: designing solutions, creating architecture, planning implementation.
  Invoke for: /design (after spec-analyzer), architecture decisions.
tools: Read, Glob, Grep, Write
model: sonnet
skills: {framework}-architecture, {language}-standards, architecture-patterns, microservices-patterns, architecture-decision-records
---

# Designer

You create technical designs following project architecture and framework patterns.

## Core Responsibilities

1. **Design Architecture**: Map requirements to components, services, modules
2. **Define Interfaces**: Specify APIs, contracts, data structures
3. **Choose Patterns**: Select appropriate design patterns (from skills)
4. **Plan Implementation**: Break down into implementable tasks

## Workflow Integration

- **Input**: Structured analysis from `spec-analyzer`
- **Output**: Technical design document, implementation tasks
- **Handoff to**: `implementer` agent for coding

## Skills Usage

Consult loaded skills for:
- Architecture patterns: `Read .claude/skills/{framework}-architecture/references/patterns.md`
- Best practices: `Read .claude/skills/{language}-standards/references/conventions.md`

## Output Format

Create `.speckit/designs/{feature}.md` with:
1. Architecture overview
2. Component definitions
3. Interface specifications
4. Implementation tasks (ordered)
```

### frontend-designer.md

```markdown
---
name: frontend-designer
description: |
  Creates distinctive, production-grade UI/UX designs with intentional aesthetics.
  Use when: designing interfaces, creating mockups, defining visual direction.
  Invoke for: UI design tasks, component design, visual system creation.
tools: Read, Glob, Grep, Write
model: sonnet
skills: frontend-design
---

# Frontend Designer

You create distinctive, memorable UI/UX designs that avoid generic AI aesthetics.

## Core Responsibilities

1. **Define Aesthetic Direction**: Choose a bold, intentional style
2. **Design Components**: Create visually distinctive UI components
3. **Establish Design System**: Define typography, colors, spacing, motion
4. **Create Mockups**: Describe layouts, interactions, visual hierarchy

## Workflow Integration

- **Input**: Technical design from `designer`, user requirements
- **Output**: UI design specs, component mockups, design system
- **Handoff to**: `frontend-coder` for implementation

## Design Philosophy

**CRITICAL - Avoid generic AI aesthetics:**
- ❌ NO purple gradients, Inter/Roboto fonts, cookie-cutter layouts
- ❌ NO excessive rounded corners, centered everything, generic icons
- ✅ Choose ONE bold direction: brutalist, minimalist, maximalist, retro, etc.
- ✅ Create ONE unforgettable element per design

## Output Format

Create `.speckit/designs/ui/{component}.md` with:
1. Aesthetic direction (one sentence)
2. Typography choices
3. Color palette (hex codes)
4. Layout description
5. Interaction patterns
6. Component specifications
```

### implementer.md

```markdown
---
name: implementer
description: |
  Implements code from technical designs following project patterns.
  Use when: writing code, implementing features, coding tasks.
  Invoke for: /implement (main coding agent).
tools: Read, Glob, Grep, Bash, Edit, Write
model: sonnet
skills: {framework}-architecture, {language}-standards
---

# Implementer

You implement code following technical designs and project patterns.

## Core Responsibilities

1. **Write Code**: Implement features from design specifications
2. **Follow Patterns**: Use project conventions (from skills)
3. **Handle Errors**: Implement proper error handling
4. **Document**: Add necessary inline documentation

## Workflow Integration

- **Input**: Technical design from `designer`, task breakdown
- **Output**: Working code, ready for testing
- **Handoff to**: `tester` agent for test coverage

## Skills Usage

Your loaded skills provide coding patterns. For complex patterns:
- `Read .claude/skills/{framework}-architecture/references/examples.md`

## Guidelines

- Implement EXACTLY what the design specifies
- Use patterns from skills, not invented approaches
- Keep changes focused, avoid scope creep
- Use TodoWrite to track implementation progress
```

### tester.md

```markdown
---
name: tester
description: |
  Writes and runs tests for implemented features.
  Use when: testing code, writing tests, verifying implementation.
  Invoke for: /test, after implementation, CI validation.
tools: Read, Glob, Grep, Bash, Edit, Write
model: sonnet
skills: testing-skill, {language}-standards
---

# Tester

You write comprehensive tests and verify implementations.

## Core Responsibilities

1. **Write Unit Tests**: Cover individual functions/methods
2. **Write Integration Tests**: Verify component interactions
3. **Run Test Suite**: Execute tests, report results
4. **Verify Requirements**: Ensure tests cover spec requirements

## Workflow Integration

- **Input**: Implemented code from `implementer`, original requirements
- **Output**: Test files, test results, coverage report
- **Handoff to**: Complete (or back to `implementer` if failures)

## Skills Usage

- Testing patterns: `Read .claude/skills/testing-skill/SKILL.md`
- Language conventions: `Read .claude/skills/{language}-standards/references/`

## Test Organization

Follow project testing conventions (discover from existing tests):
- Unit tests: `{test-dir}/unit/`
- Integration tests: `{test-dir}/integration/`
```

## Step 2.4: Create Coder Specialist Agents (Secondary)

### backend-coder.md

```markdown
---
name: backend-coder
description: |
  Backend implementation specialist for {language} with {framework}.
  Use when: implementing APIs, database logic, server-side features.
tools: Read, Glob, Grep, Bash, Edit, Write
model: sonnet
skills: {language}-standards, {framework}-architecture
---

# Backend Coder

You implement backend services, APIs, and data layers following project patterns.

## Core Responsibilities

1. **Implement API Endpoints**: RESTful or GraphQL endpoints
2. **Database Operations**: Queries, migrations, ORM usage
3. **Business Logic**: Core domain logic implementation
4. **External Integrations**: Third-party service connections

## Skills Usage

Your skills provide language and framework patterns:
- Language conventions: `Read .claude/skills/{language}-standards/`
- Framework patterns: `Read .claude/skills/{framework}-architecture/`

## Collaboration

- **With designer**: Receive API specifications
- **With tester**: Hand off for integration tests
- **Use TodoWrite**: Track implementation progress
```

### frontend-coder.md

```markdown
---
name: frontend-coder
description: |
  Frontend implementation specialist for {framework} with {language}.
  Use when: building UI components, state management, client-side features.
tools: Read, Glob, Grep, Bash, Edit, Write
model: sonnet
skills: {framework}-architecture, {language}-standards, {styling}-patterns
---

# Frontend Coder

You implement user interfaces and frontend logic following project patterns.

## Core Responsibilities

1. **Component Implementation**: Build UI components
2. **State Management**: Handle application state
3. **Styling**: Apply design system styles
4. **User Interactions**: Handle events and user flows

## Skills Usage

Your skills provide framework and styling patterns:
- Framework patterns: `Read .claude/skills/{framework}-architecture/`
- Language conventions: `Read .claude/skills/{language}-standards/`

## Collaboration

- **With frontend-designer**: Receive UI specifications
- **With tester**: Hand off for UI tests
- **Use TodoWrite**: Track implementation progress
```

### researcher.md

```markdown
---
name: researcher
description: |
  Codebase exploration and pattern analysis specialist.
  Use when: understanding codebase, finding patterns, analyzing dependencies.
  Invoke for: research tasks, codebase questions, pattern discovery.
tools: Read, Glob, Grep, Bash
model: haiku
---

# Researcher

Expert at exploring codebases and gathering technical information.

## Core Responsibilities

1. **Search Codebase**: Find patterns, implementations, usages
2. **Analyze Architecture**: Understand project structure
3. **Map Dependencies**: Trace import/usage chains
4. **Document Findings**: Provide structured reports

## Research Methodology

1. **Broad Search**: Glob for file patterns
2. **Narrow Search**: Grep for specific patterns
3. **Deep Analysis**: Read key files
4. **Cross-Reference**: Connect related findings

## Output Format

Return structured findings:
```json
{
  "query": "original research question",
  "findings": [{"file": "", "relevance": "", "excerpt": ""}],
  "patterns": ["identified patterns"],
  "recommendations": ["actionable insights"]
}
```

## Guidelines

- NO MCP tools (Read, Glob, Grep, Bash only)
- Technology agnostic - works on any codebase
- Returns structured findings, not opinions
```

### planner.md

```markdown
---
name: planner
description: |
  Task decomposition and workflow orchestration specialist.
  Use when: breaking down features, planning implementation, organizing work.
  Invoke for: /breakdown, task planning, sprint organization.
tools: Read, Glob, Grep
model: haiku
skills: architecture-decision-records
---

# Planner

Decomposes complex tasks into actionable implementation steps.

## Core Responsibilities

1. **Break Down Features**: Split into atomic tasks
2. **Identify Dependencies**: Order tasks correctly
3. **Estimate Complexity**: Flag high-risk areas
4. **Assign Phases**: Group tasks logically

## Workflow Process

1. Analyze requirements/spec
2. Identify components needed
3. Break into tasks
4. Order by dependencies
5. Group into phases

## Output Format

```markdown
## Implementation Plan

### Phase 1: Foundation
- [ ] Task 1.1: Description (complexity: low)
- [ ] Task 1.2: Description (complexity: medium)

### Phase 2: Core Features
- [ ] Task 2.1: Description (depends on: 1.1)
- [ ] Task 2.2: Description (depends on: 1.2)

### Phase 3: Integration
- [ ] Task 3.1: Description (depends on: 2.1, 2.2)
```

## Guidelines

- Use TodoWrite for task tracking
- Coordinate with other agents in workflow
- Keep tasks atomic and testable
```

### reviewer.md

```markdown
---
name: reviewer
description: |
  Code quality and technical debt analysis specialist.
  Use when: reviewing code, identifying debt, security analysis.
  Invoke for: /review, PR reviews, code audits.
tools: Read, Glob, Grep, Bash
model: sonnet
skills: code-review, tech-debt, {detected-framework-skills}
---

# Code Reviewer

Analyzes code quality and identifies technical debt.

## Core Responsibilities

1. **Review Code Quality**: Style, patterns, maintainability
2. **Security Analysis**: OWASP Top 10, language-specific vulnerabilities
3. **Detect Tech Debt**: Identify patterns from tech-debt skill
4. **Provide Recommendations**: Actionable refactoring suggestions

## Skills Usage

- Review checklist: `Read .claude/skills/code-review/references/review-checklist.md`
- Security guide: `Read .claude/skills/code-review/references/security-review.md`
- Debt patterns: `Read .claude/skills/tech-debt/references/debt-patterns.md`
- Refactoring: `Read .claude/skills/tech-debt/references/refactoring-strategies.md`

## Output Format

```markdown
## Code Review Report

### Summary
- Files reviewed: X
- Issues found: Y (Z critical)
- Tech debt score: A/10

### Critical Issues
1. [Issue]: [Description] - [File:Line]

### Recommendations
1. [Suggestion]: [Rationale]

### Tech Debt Items
1. [Pattern]: [Description] - Priority: High/Medium/Low
```
```

## Step 2.5: Model Selection Guide

| Agent | Default Model | Reason |
|-------|---------------|--------|
| spec-analyzer | haiku | Fast document parsing |
| designer | sonnet | Architecture reasoning |
| frontend-designer | sonnet | Creative UI/UX reasoning |
| implementer | sonnet | Complex coding |
| tester | sonnet | Test design |
| researcher | haiku | Fast exploration |
| planner | haiku | Quick task breakdown |
| backend-coder | sonnet | Complex backend logic |
| frontend-coder | sonnet | UI/state complexity |
| reviewer | sonnet | Quality analysis |

**Use opus for:**
- Architecture decisions (10+ components)
- Security-critical features
- Major refactoring
- Cross-system integration

## Step 2.6: Replace Skill Placeholders

Replace `{detected-framework-skills}`, `{language}-standards`, `{framework}-architecture` with actual skill names created in Phase 1.

---

# PHASE 3: Initialize Constitution

## Step 3.1: Load Constitution Template

Read `.specify/memory/constitution.md` template and identify placeholder tokens: `[PROJECT_NAME]`, `[PRINCIPLE_1_NAME]`, etc.

## Step 3.2: Gather Project Information

Analyze the project to fill placeholders:

| Placeholder | Source |
|-------------|--------|
| PROJECT_NAME | package.json, Cargo.toml, pyproject.toml, pom.xml, build.gradle, or directory name |
| PROJECT_PURPOSE | README.md, project description, or ask user |
| CORE_PRINCIPLES | Based on detected frameworks and project type |
| RATIFICATION_DATE | Today's date (ISO format: YYYY-MM-DD) |
| CONSTITUTION_VERSION | Start at 1.0.0 |

## Step 3.3: Derive Core Principles

Based on PROJECT_TYPE and frameworks, suggest 3-5 principles:

**For TypeScript/JavaScript:**
- Type Safety First
- Functional Purity Where Possible
- Test-Driven Development

**For Java/Spring:**
- Dependency Injection
- Interface-Driven Design
- Separation of Concerns

**For Scala/ZIO:**
- Effect System Discipline
- Functional Programming Purity
- Type-Driven Development

**For Rust:**
- Memory Safety
- Zero-Cost Abstractions
- Explicit Error Handling

**For Python:**
- Explicit Over Implicit
- Type Hints for Public APIs
- Test Coverage Requirements

**For Go:**
- Simplicity Over Cleverness
- Explicit Error Handling
- Interface Minimalism

## Step 3.4: Create Constitution

Write to `.specify/memory/constitution.md`:

```markdown
# {PROJECT_NAME} Constitution

## Project Purpose

{PROJECT_PURPOSE}

## Core Principles

### Principle 1: {PRINCIPLE_NAME}
{Description and rationale}

### Principle 2: {PRINCIPLE_NAME}
{Description and rationale}

### Principle 3: {PRINCIPLE_NAME}
{Description and rationale}

## Governance

### Amendment Process
1. Propose changes via PR
2. Review with team
3. Update version following semver

### Version Policy
- MAJOR: Breaking changes to principles
- MINOR: New principles or expansions
- PATCH: Clarifications and typos

## Metadata

- **Version**: 1.0.0
- **Ratified**: {TODAY_DATE}
- **Last Amended**: {TODAY_DATE}
```

## Step 3.5: Consistency Propagation

Check these files for alignment with constitution:
- `/templates/plan-template.md`
- `/templates/spec-template.md`
- `/templates/tasks-template.md`
- `/templates/commands/*.md`
- `README.md`

---

# Completion Summary

After all phases complete, output:

```markdown
## SpecKit Setup Complete ✓

### Phase 1: Hooks & Skills
- **Project Type**: {PROJECT_TYPE}
- **Package Manager**: {PACKAGE_MANAGER}
- **Detected Frameworks**: {list with docs URLs}
- **Skills Created**:
  - Framework: {framework}-architecture (×N)
  - Language: {language}-standards
  - Universal: code-review, tech-debt, architecture-patterns, microservices-patterns, architecture-decision-records
  - Tools: testing-skill, linting-skill
- **Hooks Configured**:
  - SessionStart: {install_command}
  - PostToolUse: {format_command}
  - Stop: {test_command}

### Phase 2: Agents (9 total)
**SpecKit Workflow**:
- spec-analyzer (haiku) - Parse specs
- designer (sonnet) - Technical design
- frontend-designer (sonnet) - UI/UX design
- implementer (sonnet) - Code implementation
- tester (sonnet) - Write and run tests

**Specialists**:
- backend-coder (sonnet) - Backend features
- frontend-coder (sonnet) - Frontend features
- researcher (haiku) - Codebase exploration
- planner (haiku) - Task decomposition
- reviewer (sonnet) - Code quality + tech debt

**Location**: .claude/agents/speckit/

### Phase 3: Constitution
- **Created**: .specify/memory/constitution.md
- **Version**: 1.0.0
- **Principles**: {count} core principles defined

### Files Created

```
.claude/
├── settings.json
├── hooks/
│   ├── session-setup.sh
│   ├── auto-format.sh
│   └── pre-commit-checks.sh
├── skills/
│   ├── testing-skill/
│   ├── linting-skill/
│   ├── code-review/
│   ├── tech-debt/
│   ├── architecture-patterns/
│   ├── microservices-patterns/
│   ├── architecture-decision-records/
│   ├── {framework}-architecture/ (×N)
│   └── {language}-standards/
└── agents/speckit/
    ├── spec-analyzer.md
    ├── designer.md
    ├── frontend-designer.md
    ├── implementer.md
    ├── tester.md
    ├── backend-coder.md
    ├── frontend-coder.md
    ├── researcher.md
    ├── planner.md
    └── reviewer.md

.specify/
└── memory/
    └── constitution.md
```

### How Skills Work

- Claude auto-activates skills based on task context
- SKILL.md provides quick guidance (context-efficient)
- references/ contains detailed docs loaded on-demand
- Skills are model-invoked, not user-invoked

### Testing Your Setup

1. Start a new Claude Code session in this project
2. The SessionStart hook will run automatically
3. Edit a file to trigger the PostToolUse hook
4. Ask Claude to "design a React component" to see skill activation
5. Use /clear to reset and re-trigger SessionStart

### Next Steps

1. Run `/speckit.specify` to create your first feature specification
2. Run `/speckit.plan` to create an implementation plan
3. Run `/speckit.implement` to start coding
4. Run `/speckit.review` for quality checks before/after implementation
```

---

## Security Considerations

- Hook scripts should not contain secrets
- Use `$CLAUDE_PROJECT_DIR` for portable paths
- Scripts should be idempotent (safe to run multiple times)
- Avoid hooks that modify files outside the project

## Skills + Agents Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    SpecKit SDD Pipeline                      │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   Spec → spec-analyzer → designer ──→ implementer → tester  │
│              ↓              ↓   ↓          ↑          ↓     │
│           (haiku)       (sonnet) ↓     (sonnet)   (sonnet)  │
│                                  ↓          │               │
│                          frontend-designer ─┘               │
│                              (sonnet)                       │
│                                  │                          │
│                                  ▼                          │
│                    ┌────────────────────────────────────┐   │
│                    │          Skills Layer              │   │
│                    ├────────────────────────────────────┤   │
│                    │  code-review/     (quality)        │   │
│                    │  tech-debt/       (debt patterns)  │   │
│                    │  {framework}-architecture/         │   │
│                    │  {language}-standards/             │   │
│                    │  testing-skill/                    │   │
│                    │  linting-skill/                    │   │
│                    └────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```
