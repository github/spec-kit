# Module 04c – Prompt History Records (PHR)

> **Built into Spec Kit: Turn every AI exchange into a first-class artifact that compounds your learning and accelerates your team.**

## The Problem: Lost Knowledge

Every day, developers have hundreds of AI conversations that produce valuable code, insights, and decisions. But this knowledge disappears into chat history, leaving you to:

- **Reinvent solutions** you already figured out
- **Debug without context** of why code was written that way
- **Miss patterns** in what prompts actually work
- **Lose traceability** for compliance and code reviews

## The Solution: Prompt History Records

**PHRs capture every meaningful AI exchange as a structured artifact** that lives alongside your code, creating a searchable, reviewable history of your AI-assisted development.

### Core Learning Science Principles

| Principle              | How PHRs Apply                                         | Daily Benefit                               |
| ---------------------- | ------------------------------------------------------ | ------------------------------------------- |
| **Spaced Repetition**  | Revisit PHRs weekly to reinforce successful strategies | Build muscle memory for effective prompting |
| **Metacognition**      | Reflect on what worked/didn't work in each exchange    | Develop better prompting intuition          |
| **Retrieval Practice** | Search PHRs when facing similar problems               | Access proven solutions instantly           |
| **Interleaving**       | Mix different types of prompts (architect/red/green)   | Strengthen transfer across contexts         |

---

## Spec Kit Native: Built-In PHR System

PHRs are **built into Spec Kit** when you initialize a project with `specify init`. No manual setup required!

### Automatic Setup with Specify CLI

When you run `specify init`:

```bash
specify init --ai gemini  # Or claude, cursor, copilot, etc.
```

You automatically get:

- ✅ **PHR command** (e.g., `/phr` slash command)
- ✅ **PHR template** (`.specify/templates/phr-template.prompt.md`)
- ✅ **PHR creation script** (`.specify/scripts/bash/create-phr.sh` or PowerShell)
- ✅ **Deterministic location logic** (pre-feature vs feature-specific)

---

## Deterministic PHR Location Strategy

PHRs use a **simple, deterministic rule** for where they're stored:

### Before Feature Exists (Pre-Feature Work)

**Location:** `docs/prompts/`  
**Stages:** `constitution`, `spec`, `general`  
**Naming:** `0001-title.constitution.prompt.md`

**Use cases:**

- Creating constitution.md
- Writing initial specs
- General project setup

**Example:**

```
docs/
└── prompts/
    ├── 0001-define-quality-standards.constitution.prompt.md
    ├── 0002-create-auth-spec.spec.prompt.md
    └── 0003-setup-ci-cd.general.prompt.md
```

### After Feature Exists (Feature Work)

**Location:** `specs/<feature>/prompts/`  
**Stages:** `architect`, `red`, `green`, `refactor`, `explainer`, `misc`  
**Naming:** `0001-title.architect.prompt.md`

**Use cases:**

- Feature planning and design
- Implementation work
- Debugging and fixes
- Code refactoring

**Example:**

```
specs/
├── 001-authentication/
│   ├── spec.md
│   ├── plan.md
│   └── prompts/
│       ├── 0001-design-jwt-system.architect.prompt.md
│       ├── 0002-implement-jwt.green.prompt.md
│       └── 0003-fix-token-bug.red.prompt.md
└── 002-database/
    └── prompts/
        ├── 0001-design-schema.architect.prompt.md
        └── 0002-optimize-queries.refactor.prompt.md
```

### Key Features

- **Local sequence numbering**: Each directory starts at 0001
- **Stage-based extensions**: Files show their type (`.architect.prompt.md`, `.red.prompt.md`)
- **Auto-detection**: Script finds the right feature from branch name or latest numbered feature
- **No ambiguity**: Clear rules, no complex fallback logic

---

## PHR Stages

### Pre-Feature Stages

| Stage          | Extension                 | When to Use                                    | Example                   |
| -------------- | ------------------------- | ---------------------------------------------- | ------------------------- |
| `constitution` | `.constitution.prompt.md` | Defining quality standards, project principles | Creating constitution.md  |
| `spec`         | `.spec.prompt.md`         | Creating business requirements, feature specs  | Writing spec.md           |
| `general`      | `.general.prompt.md`      | Setup, docs, unclassified early work           | Configuring tools, README |

### Feature-Specific Stages (TDD Cycle)

| Stage       | Extension              | TDD Phase      | When to Use                                 | Example                     |
| ----------- | ---------------------- | -------------- | ------------------------------------------- | --------------------------- |
| `architect` | `.architect.prompt.md` | **Plan**       | Design, planning, API contracts             | Designing JWT auth system   |
| `red`       | `.red.prompt.md`       | **Red**        | Debugging, fixing errors, test failures     | Fixing token expiration bug |
| `green`     | `.green.prompt.md`     | **Green**      | Implementation, new features, passing tests | Implementing login endpoint |
| `refactor`  | `.refactor.prompt.md`  | **Refactor**   | Code cleanup, optimization                  | Extracting auth middleware  |
| `explainer` | `.explainer.prompt.md` | **Understand** | Code explanations, documentation            | Understanding JWT flow      |
| `misc`      | `.misc.prompt.md`      | **Other**      | Uncategorized feature work                  | General feature questions   |

---

## Using PHRs in Your Workflow

### The `/phr` Command

Use `/phr` for **any AI interaction** you want to capture:

```bash
# Pre-feature work (constitution, specs)
/phr Define our API versioning standards

# Feature planning
/phr Design the authentication system architecture

# Implementation
/phr Implement JWT token generation with 15-minute expiration

# Debugging
/phr Fix the database connection timeout error

# Refactoring
/phr Extract authentication middleware into separate module
```

### What Happens When You Use `/phr`

1. **Execute Your Request** - The AI does the actual work you asked for
2. **Classify the Stage** - Determines if it's architect/red/green/etc.
3. **Extract Metadata** - Captures files, tests, labels from the exchange
4. **Create PHR File** - Automatically generates the PHR with proper naming
5. **Confirm Creation** - Shows you where the PHR was saved

### Integrated SDD Workflow

```
Constitution → /specify → /plan → /adr → /tasks → /implement → /phr
                                                                  ↑
                                                    Record every exchange
```

**PHRs run throughout:**

- Use `/phr` during constitution creation
- Use `/phr` during spec writing
- Use `/phr` during feature implementation
- Use `/phr` for any debugging or refactoring

---

## Daily Workflow with PHRs

### Morning: Context Loading (2 minutes)

```bash
# Read yesterday's PHRs to rehydrate context
ls specs/*/prompts/*.prompt.md | tail -5 | xargs cat

# Or for pre-feature work
ls docs/prompts/*.prompt.md | tail -5 | xargs cat
```

### During Work: Capture Everything (automatic)

The `/phr` command handles everything:

```bash
/phr Add password hashing to user registration
```

The agent will:

1. Implement password hashing
2. Automatically create the PHR
3. Show you: `✅ PHR recorded → specs/001-auth/prompts/0004-add-password-hashing.green.prompt.md`

### Evening: Reflect & Learn (3 minutes)

```bash
# Review today's PHRs
grep -r "Reflection:" specs/*/prompts/ | tail -3

# Find patterns in successful prompts
grep -r "✅ Impact:" specs/*/prompts/ | grep -v "recorded for traceability"
```

---

## What Each PHR Contains

```yaml
---
id: 0001
title: Design JWT authentication system
stage: architect
date: 2025-10-01
surface: agent
model: gpt-4
feature: 001-authentication
branch: feat/001-authentication
user: Jane Developer
command: phr
labels: ["auth", "security", "jwt"]
links:
  spec: specs/001-authentication/spec.md
  ticket: null
  adr: docs/adr/0003-jwt-choice.md
  pr: null
files:
  - src/auth/jwt.py
  - src/auth/middleware.py
  - tests/test_jwt.py
tests:
  - tests/test_jwt.py::test_token_generation
---

## Prompt

Design a JWT authentication system with token generation, validation, and refresh capabilities.

## Response snapshot

Created JWT auth system with:
- Token generation with 15-minute expiration
- Refresh token with 7-day expiration
- Middleware for route protection
- Comprehensive test coverage

## Outcome

- ✅ Impact: Complete JWT auth system designed and implemented
- 🧪 Tests: tests/test_jwt.py::test_token_generation (passing)
- 📁 Files: src/auth/jwt.py, src/auth/middleware.py, tests/test_jwt.py
- 🔁 Next prompts: Implement refresh token rotation, add rate limiting
- 🧠 Reflection: JWT implementation was straightforward; consider adding refresh token rotation for better security
```

---

## Searching Your PHR Knowledge Base

### Find by Topic

```bash
# Find all authentication-related prompts
grep -r "auth" specs/*/prompts/

# Find all prompts about databases
grep -r "database\|sql\|postgres" specs/*/prompts/
```

### Find by Stage

```bash
# Find all debugging sessions (red stage)
find specs -name "*.red.prompt.md"

# Find all architecture planning (architect stage)
find specs -name "*.architect.prompt.md"

# Find all implementations (green stage)
find specs -name "*.green.prompt.md"
```

### Find by File

```bash
# Find prompts that touched specific files
grep -r "auth.py" specs/*/prompts/

# Find prompts that ran specific tests
grep -r "test_login" specs/*/prompts/
```

### Find by Feature

```bash
# List all PHRs for a specific feature
ls -la specs/001-authentication/prompts/

# Count PHRs per feature
for dir in specs/*/prompts; do echo "$dir: $(ls "$dir" | wc -l)"; done
```

---

## Advanced Usage

### Team Knowledge Sharing

```bash
# Commit PHRs with your code
git add specs/*/prompts/ && git commit -m "Add PHR: JWT authentication implementation"

# Review team's PHRs
git log --all --grep="PHR:" --oneline

# Create team prompt library
mkdir .docs/team-prompts
cp specs/*/prompts/*.architect.prompt.md .docs/team-prompts/
```

### Compliance & Auditing

```bash
# Generate audit trail for security work
find specs -name "*.prompt.md" -exec grep -l "security\|auth\|payment" {} \;

# Track when decisions were made
grep -r "date:" specs/*/prompts/ | grep "2025-10"

# Find who worked on what
grep -r "user:" specs/*/prompts/ | sort | uniq
```

### Performance Optimization

```bash
# Find your most effective prompts
grep -r "✅ Impact:" specs/*/prompts/ | grep -v "recorded for traceability"

# Identify patterns in failed attempts
grep -r "❌" specs/*/prompts/

# Track time-to-solution
grep -r "Next prompts:" specs/*/prompts/ | grep -v "none"
```

---

## Integration with SDD Components

### PHRs Link to Everything

```yaml
links:
  spec: specs/001-auth/spec.md # Feature spec
  adr: docs/adr/0003-jwt-choice.md # Architectural decision
  ticket: JIRA-123 # Issue tracker
  pr: https://github.com/org/repo/pull/45 # Pull request
```

### Workflow Integration

```
1. /constitution   → docs/prompts/0001-quality-standards.constitution.prompt.md
2. /specify        → docs/prompts/0002-auth-requirements.spec.prompt.md
3. /plan           → specs/001-auth/prompts/0001-design-system.architect.prompt.md
4. /adr            → (ADR references the PHR for context)
5. /tasks          → specs/001-auth/prompts/0002-break-down-tasks.architect.prompt.md
6. /implement      → specs/001-auth/prompts/0003-implement-jwt.green.prompt.md
7. Debug & fix     → specs/001-auth/prompts/0004-fix-token-bug.red.prompt.md
8. Refactor        → specs/001-auth/prompts/0005-extract-middleware.refactor.prompt.md
```

---

## Why This Works (Learning Science)

### Spaced Repetition

- **Weekly PHR reviews** reinforce successful prompting patterns
- **Searching past PHRs** when facing similar problems builds retrieval strength
- **Pattern recognition** emerges from reviewing your own prompt history

### Metacognition

- **Reflection prompts** in each PHR force you to think about what worked
- **"Next prompts"** section helps you plan follow-up actions
- **Outcome tracking** shows the connection between prompts and results

### Interleaving

- **Stage tagging** (architect/red/green) mixes different types of thinking
- **Context switching** between planning, coding, and debugging strengthens transfer
- **Cross-domain learning** happens when you apply patterns from one area to another

### Retrieval Practice

- **Searching PHRs** forces active recall of past solutions
- **Weekly reviews** strengthen memory consolidation
- **Reapplying patterns** to new problems deepens understanding

---

## Success Metrics

After 1 week of using PHRs, you should have:

- [ ] 20+ PHRs capturing your AI interactions
- [ ] 3+ successful prompt patterns you can reuse
- [ ] 1+ debugging session where PHRs saved you time
- [ ] Clear understanding of what prompts work for your domain

After 1 month:

- [ ] 100+ PHRs organized by feature
- [ ] Searchable knowledge base of effective prompts
- [ ] Measurable reduction in time spent solving similar problems
- [ ] Team members using each other's PHRs as templates

**The goal:** Turn AI assistance from ad-hoc to systematic, building a compounding knowledge base that makes you more effective every day.

---

## Troubleshooting

### Common Issues

**"Invalid stage 'architect' for pre-feature context"**

- **Cause**: Using feature stage before specs/ directory exists
- **Solution**: Use pre-feature stages (`constitution`, `spec`, `general`) or create a feature first

**"No feature specified and no numbered features found"**

- **Cause**: Working in feature context but no features exist
- **Solution**: Run `/specify` to create your first feature, or specify `--feature` manually

**"Feature directory not found"**

- **Cause**: Specified feature doesn't exist in `specs/`
- **Solution**: Check available features with `ls specs/` or create the feature with `/specify`

**PHRs not being created automatically**

- **Cause**: `/phr` command not properly configured
- **Solution**: Run `specify init` again to regenerate agent commands

### Manual PHR Creation

If needed, you can create PHRs manually:

```bash
# Pre-feature PHR
.specify/scripts/bash/create-phr.sh \
  --title "Define API standards" \
  --stage constitution \
  --prompt "Create API versioning standards" \
  --json

# Feature-specific PHR
.specify/scripts/bash/create-phr.sh \
  --title "Implement login" \
  --stage green \
  --prompt "Add JWT login endpoint" \
  --feature "001-auth" \
  --files "src/auth.py,tests/test_auth.py" \
  --labels "auth,security" \
  --json
```

---

## Comparison: PHR vs Traditional Methods

| Aspect            | Traditional (Chat History) | PHR System                            |
| ----------------- | -------------------------- | ------------------------------------- |
| **Persistence**   | Lost when chat closes      | Permanent, version-controlled         |
| **Searchability** | Limited to current session | `grep`, `find`, full-text search      |
| **Organization**  | Chronological only         | By feature, stage, file, label        |
| **Team Sharing**  | Screenshots, copy-paste    | Git commits, pull requests            |
| **Traceability**  | None                       | Links to specs, ADRs, PRs             |
| **Learning**      | No reinforcement           | Spaced repetition, retrieval practice |
| **Compliance**    | No audit trail             | Complete history with metadata        |

---

## Summary

PHRs are **built into Spec Kit** and provide:

✅ **Deterministic location strategy**: `docs/prompts/` (pre-feature) vs `specs/<feature>/prompts/` (feature work)  
✅ **Stage-based organization**: Clear extensions show the type of work  
✅ **Local sequence numbering**: Each directory maintains its own series  
✅ **Automatic integration**: Works with `/phr` slash command  
✅ **Learning-focused**: Based on spaced repetition and retrieval practice  
✅ **Team-friendly**: Version-controlled, searchable, shareable  
✅ **Compliance-ready**: Complete audit trail with metadata

**Start using PHRs today** by running `specify init` and using `/phr` for every AI interaction. Your future self (and your team) will thank you! 🚀
