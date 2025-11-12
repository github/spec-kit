---
description: Initialize Kent Beck TDD workflow by creating CLAUDE.md from template
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Outline

This command sets up **Kent Beck's Test-Driven Development workflow** in your project by creating a customized `CLAUDE.md` file based on your project's constitution, plan, and tech stack.

1. **Check Prerequisites**: Verify constitution.md and plan.md exist
2. **Load Template**: Read kent-beck-claude-template.md
3. **Customize**: Auto-populate project-specific sections
4. **Create CLAUDE.md**: Write to project root
5. **Report**: Confirm setup complete

## Execution Flow

### Phase 1: Prerequisites Check

1. **Verify Required Files**:
   ```bash
   # Must exist:
   memory/constitution.md           # Project principles
   specs/[feature]/plan.md          # Implementation plan

   # Nice to have:
   specs/[feature]/spec.md          # Feature requirements
   specs/[feature]/tasks.md         # Task checklist
   ```

2. **Check Git Status**:
   - Repository must be initialized (`git init` already run)
   - Working directory should be clean (warn if not)

3. **Detect Current Feature** (in priority order):
   1. From git branch name (e.g., `001-user-auth`) - **checked first**
   2. From environment variable `SPECIFY_FEATURE` - **fallback**
   3. ERROR if cannot detect feature context from either method

### Phase 2: Load Context

1. **Read Constitution**:
   ```markdown
   From memory/constitution.md:
   - Extract project name
   - Extract core principles (§I, §II, etc.)
   - Extract non-functional requirements (latency, uptime, etc.)
   ```

2. **Read Plan**:
   ```markdown
   From specs/[feature]/plan.md:
   - Extract tech stack (languages, frameworks)
   - Extract architecture patterns
   - Extract testing frameworks
   - Extract code conventions
   ```

3. **Read Spec** (if exists):
   ```markdown
   From specs/[feature]/spec.md:
   - Extract feature name
   - Extract user stories for context
   ```

### Phase 3: Customize Template

1. **Load Base Template**:
   ```bash
   Read: templates/kent-beck-claude-template.md
   ```

2. **Replace Placeholders**:

   **[PROJECT NAME]** → From constitution or git repo name
   ```markdown
   # MyProject - Development Guidelines (Kent Beck TDD)
   ```

   **[AUTO-GENERATED DATE]** → Current date
   ```markdown
   **Last Updated**: 2025-11-12
   ```

   **[AUTO-DETECTED FROM BRANCH]** → Current feature
   ```markdown
   **Current Feature**: 001-user-auth (User Authentication System)
   ```

   **[AUTO-POPULATED FROM plan.md]** → Tech stack section
   ```markdown
   ### Tech Stack

   **Languages**: Python 3.11+, TypeScript 5.0+
   **Frameworks**: FastAPI, React
   **Databases**: PostgreSQL 15, Redis 7
   **Testing**: pytest, pytest-asyncio, Jest
   ```

   **[AUTO-POPULATED FROM plan.md]** → Architecture patterns
   ```markdown
   ### Architecture Patterns

   **Design Patterns**: Repository pattern, Dependency Injection
   **API Style**: REST with OpenAPI 3.0
   **Data Format**: JSON (API), GeoJSON (spatial data)
   ```

   **[AUTO-POPULATED FROM constitution.md]** → Performance requirements
   ```markdown
   ### Performance Requirements

   **Latency**: p95 < 500ms (from §I. Real-Time Performance)
   **Throughput**: 1000 req/sec (from §I. Real-Time Performance)
   **Availability**: 99.9% uptime (from §II. Reliability)
   ```

   **[e.g., Black for Python, Prettier for TypeScript]** → Code conventions
   ```markdown
   ### Code Conventions

   **Python**:
   - Formatting: Black (line length 100)
   - Linting: Pylint, mypy strict mode
   - Type hints: Required for all functions

   **TypeScript**:
   - Formatting: Prettier
   - Linting: ESLint with Airbnb config
   - Strict mode: Enabled
   ```

3. **Preserve Manual Additions Section**:
   ```markdown
   <!-- MANUAL ADDITIONS START -->
   <!-- User can add custom notes here -->
   <!-- MANUAL ADDITIONS END -->
   ```

### Phase 4: Create CLAUDE.md

1. **Write to Project Root**:
   ```bash
   # Create file
   ./CLAUDE.md

   # File structure:
   # - Header (project name, date, feature)
   # - Kent Beck TDD principles
   # - Project-specific config (auto-populated)
   # - AI warning signs
   # - Integration with Speckit
   ```

2. **Set File Permissions**:
   ```bash
   chmod 644 CLAUDE.md
   # Read/write for owner, read for others
   ```

3. **Verify Creation**:
   ```bash
   # Check file exists
   test -f CLAUDE.md

   # Check file size (should be >10KB)
   # Check all placeholders replaced
   ```

### Phase 5: Optional Git Commit

1. **Ask User**:
   ```
   ✅ CLAUDE.md created successfully!

   Commit this file to git? (y/n)
   ```

2. **If Yes**:
   ```bash
   git add CLAUDE.md
   git commit -m "docs: initialize Kent Beck TDD workflow

   Added CLAUDE.md with project-specific TDD guidelines.
   Auto-populated from constitution.md and plan.md.

   🤖 Generated with Claude Code"
   ```

### Phase 6: Report Success

```markdown
✅ Kent Beck TDD Workflow Initialized

📁 Created: CLAUDE.md (12.5 KB)

📋 Configuration:
- Project: MyProject
- Current Feature: 001-user-auth
- Tech Stack: Python 3.11+, FastAPI, PostgreSQL
- Test Framework: pytest

🎯 Next Steps:

1. Review CLAUDE.md and customize if needed
2. Generate tasks: /speckit.tasks
3. Start TDD cycle: /speckit.go

📖 Quick Start:

```bash
# Implement next task with TDD
/speckit.go

# AI will:
# 1. Find next unmarked task
# 2. Write failing test (RED)
# 3. Implement minimum code (GREEN)
# 4. Refactor if needed
# 5. Commit following Tidy First
# 6. Mark task complete
```

---

**Kent Beck TDD Principles Active** ✅
- Test-Driven Development (Red-Green-Refactor)
- Tidy First (Structural ≠ Behavioral commits)
- AI Warning Signs Detection
- Constitution Compliance
```

---

## Customization Options

### Option 1: Minimal Setup (Quick Start)

```bash
/speckit.init-tdd
# Uses defaults from constitution.md and plan.md
# Takes 5 seconds
```

### Option 2: Interactive Setup

```bash
/speckit.init-tdd --interactive
# Asks questions:
# - Test framework? (pytest/Jest/RSpec)
# - Code formatter? (Black/Prettier/Rustfmt)
# - Linter? (Pylint/ESLint/Clippy)
# - Git hooks? (yes/no)
# Takes 2-3 minutes
```

### Option 3: From Existing CLAUDE.md

```bash
/speckit.init-tdd --from-existing
# If CLAUDE.md already exists
# Merge Speckit conventions into existing file
# Preserve user customizations
```

---

## Error Handling

### ERROR 1: Missing Prerequisites

```
❌ Cannot initialize TDD workflow

Missing required files:
- memory/constitution.md (run /speckit.constitution first)
- specs/[feature]/plan.md (run /speckit.plan first)

Action: Complete Speckit workflow before enabling TDD.
```

### ERROR 2: CLAUDE.md Already Exists

```
⚠️ CLAUDE.md already exists (5.2 KB)

Options:
1. Backup and replace with Speckit version
2. Merge Speckit conventions into existing file
3. Cancel initialization

Your choice (1/2/3):
```

If user chooses "2" (merge):
```bash
# Backup existing
mv CLAUDE.md CLAUDE.md.backup

# Create merged version
# - Keep user's custom sections
# - Add Speckit TDD sections
# - Add AI warning signs
# - Add integration workflow

✅ Merged: CLAUDE.md (15.3 KB)
📁 Backup: CLAUDE.md.backup
```

### ERROR 3: Cannot Detect Feature

```
❌ Cannot detect current feature context

Tried:
- Git branch name (on 'main', not a feature branch)
- SPECIFY_FEATURE env var (not set)

Action: Checkout a feature branch first:
git checkout -b 001-my-feature

Or set environment variable:
export SPECIFY_FEATURE=001-my-feature
```

---

## Integration with Speckit Workflow

### Full Workflow Sequence

```
1. /speckit.constitution     → Define project principles
2. /speckit.specify          → Create feature spec
3. /speckit.plan             → Create implementation plan
4. /speckit.tasks            → Generate task breakdown
5. /speckit.init-tdd         → Enable Kent Beck TDD ← YOU ARE HERE
6. /speckit.go               → Implement task 1 (TDD)
7. /speckit.go               → Implement task 2 (TDD)
8. /speckit.go               → Implement task N (TDD)
9. All tasks complete!
```

### When to Use

**Use `/speckit.init-tdd` when**:
- ✅ Starting a new project with TDD
- ✅ Want strict test-driven development
- ✅ Need AI warning sign detection
- ✅ Team wants Kent Beck's methodology

**Skip `/speckit.init-tdd` when**:
- ❌ Already have existing test culture
- ❌ Not using TDD (just implementation)
- ❌ Project is throw-away prototype

---

## Advanced: Custom Template

If you want to customize the Kent Beck template:

1. **Copy template**:
   ```bash
   cp templates/kent-beck-claude-template.md my-template.md
   ```

2. **Edit sections**:
   ```markdown
   # Add your team's specific rules
   # Modify AI warning thresholds
   # Add custom refactoring patterns
   ```

3. **Use custom template**:
   ```bash
   /speckit.init-tdd --template=my-template.md
   ```

---

## Git Hooks Integration (Optional)

During initialization, you can enable git hooks for TDD enforcement:

```bash
/speckit.init-tdd --with-hooks
```

This creates:

**.git/hooks/pre-commit**:
```bash
#!/bin/bash
# Kent Beck TDD Pre-Commit Hook

# 1. All tests must pass
pytest
if [ $? -ne 0 ]; then
    echo "❌ Tests failed - commit blocked"
    exit 1
fi

# 2. Check commit message format
# Must be: "feat:", "refactor:", "test:", "fix:", etc.
COMMIT_MSG=$(cat $1)
if ! echo "$COMMIT_MSG" | grep -qE "^(feat|refactor|test|fix|docs):"; then
    echo "❌ Invalid commit message format"
    echo "Required: feat:|refactor:|test:|fix:|docs:"
    exit 1
fi

# 3. Detect structural vs behavioral
if echo "$COMMIT_MSG" | grep -q "^refactor:"; then
    # Must have "Tidy First" or "No behavior changed"
    if ! echo "$COMMIT_MSG" | grep -qE "(Tidy First|No behavior changed)"; then
        echo "⚠️ Refactor commit should mention 'Tidy First'"
    fi
fi

echo "✅ Pre-commit checks passed"
```

---

## Validation Checklist

After running `/speckit.init-tdd`, verify:

- [ ] `CLAUDE.md` exists in project root
- [ ] File size >10KB (fully populated)
- [ ] Project name is correct (not "[PROJECT NAME]")
- [ ] Tech stack matches plan.md
- [ ] Performance requirements from constitution.md
- [ ] Manual additions section preserved
- [ ] `/speckit.go` command works (try it)

---

## Notes

- This command is idempotent (safe to run multiple times)
- Updates existing CLAUDE.md with new project context
- Preserves user customizations in manual sections
- Auto-detects changes in plan.md and re-populates
- Compatible with all Speckit commands
- Follows spec-kit conventions and philosophy
