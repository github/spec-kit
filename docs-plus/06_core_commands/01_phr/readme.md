# Module 10 – Prompt History Records (PHR): Automatic Knowledge Capture

> **Built into Spec Kit: Every AI exchange is automatically captured as a structured artifact—no extra commands needed.**

## The Problem: Lost Knowledge

Every day, developers have hundreds of AI conversations that produce valuable code, insights, and decisions. But this knowledge disappears into chat history, leaving you to:

- **Reinvent solutions** you already figured out
- **Debug without context** of why code was written that way
- **Miss patterns** in what prompts actually work
- **Lose traceability** for compliance and code reviews

## The Solution: Automatic Prompt History Records

**PHRs are created automatically after every significant AI interaction** in Spec Kit. No extra commands, no manual effort—just work normally and get complete documentation of your AI-assisted development journey.

### Core Learning Science Principles

| Principle              | How PHRs Apply                                         | Daily Benefit                               |
| ---------------------- | ------------------------------------------------------ | ------------------------------------------- |
| **Spaced Repetition**  | Revisit PHRs weekly to reinforce successful strategies | Build muscle memory for effective prompting |
| **Metacognition**      | Reflect on what worked/didn't work in each exchange    | Develop better prompting intuition          |
| **Retrieval Practice** | Search PHRs when facing similar problems               | Access proven solutions instantly           |
| **Interleaving**       | Mix different types of prompts (architect/red/green)   | Strengthen transfer across contexts         |

---

## How It Works: Completely Automatic

### Setup (One Time)

When you run `specify init`:

```bash
specify init --ai gemini  # Or claude, cursor, copilot, etc.
```

You automatically get:

- ✅ **Implicit PHR creation** built into every command
- ✅ **PHR templates** and scripts
- ✅ **Deterministic location logic** (pre-feature vs feature-specific)
- ✅ **Manual `/phr` command** for custom cases (optional)

### Daily Usage: Just Work Normally

PHRs are created **automatically** after:

```bash
/sp.constitution Define quality standards     → PHR created in history/prompts/constitution/
/sp.specify Create authentication feature     → PHR created in history/prompts/general/
/sp.plan Design JWT system                    → PHR created in history/prompts/auth/
/sp.tasks Break down implementation           → PHR created in history/prompts/auth/
/sp.implement Write JWT token generation      → PHR created in history/prompts/auth/
```

Also after general work:

- Technical questions producing code → PHR created
- Debugging or fixing errors → PHR created
- Code explanations → PHR created
- Refactoring → PHR created

**You see:** Brief confirmation like `📝 PHR-0003 recorded`

**That's it!** Keep working, and your knowledge compounds automatically.

---

## Deterministic PHR Location Strategy

All PHRs are consolidated under `history/prompts/` with logical subdirectories. This provides a single, clear location for all prompt history while keeping them organized by purpose and context.

**Main Rule:** `history/prompts/` → `constitution/` | `<feature-name>/` | `general/`

### Constitution (Project Principles)

**Location:** `history/prompts/constitution/`
**Stages:** `constitution`
**Naming:** `0001-title.constitution.prompt.md`

**Use cases:**
- Defining project quality standards
- Setting up governance rules

**Example:**

```
history/
└── prompts/
    └── constitution/
        ├── 0001-define-quality-standards.constitution.prompt.md
        └── 0002-establish-testing-policy.constitution.prompt.md
```

### Feature-Specific (Feature Implementation Work)

**Location:** `history/prompts/<feature-name>/`
**Stages:** `spec`, `plan`, `tasks`, `red`, `green`, `refactor`, `explainer`, `misc`
**Naming:** `0001-title.spec.prompt.md`

**Use cases:**
- Feature planning and design (spec, plan)
- Implementation work (tasks, green)
- Debugging and fixes (red)
- Code refactoring (refactor)
- Code explanations (explainer)
- Other feature-specific work (misc)

**Feature name extraction:** Automatically extracted from numbered feature directories
Example: `001-authentication` → `history/prompts/authentication/`

**Example:**

```
history/
└── prompts/
    ├── constitution/
    │   └── 0001-quality-standards.constitution.prompt.md
    ├── authentication/
    │   ├── 0001-design-jwt-system.spec.prompt.md
    │   ├── 0002-design-jwt-system.architect.prompt.md
    │   ├── 0003-implement-jwt.green.prompt.md
    │   ├── 0004-fix-token-bug.red.prompt.md
    │   └── 0005-extract-middleware.refactor.prompt.md
    └── database/
        ├── 0001-design-schema.spec.prompt.md
        ├── 0002-design-schema.architect.prompt.md
        └── 0003-optimize-queries.refactor.prompt.md
```

### General/Catch-All (Non-Feature Work)

**Location:** `history/prompts/general/`
**Stages:** `general`
**Naming:** `0001-title.general.prompt.md`

**Use cases:**
- General work not tied to a specific feature
- Setup and configuration
- Documentation
- Infrastructure work

**Example:**

```
history/
└── prompts/
    └── general/
        ├── 0001-setup-ci-pipeline.general.prompt.md
        ├── 0002-configure-docker.general.prompt.md
        └── 0003-setup-monitoring.general.prompt.md
```

### Key Features

- **Local sequence numbering**: Each directory starts at 0001
- **Stage-based extensions**: Files show their type (`.spec.prompt.md`, `.red.prompt.md`, `.refactor.prompt.md`)
- **Auto-detection**: Script automatically extracts feature name from numbered feature directories (`001-auth` → `auth`)
- **Clear location rules**:
  - `constitution` → always `history/prompts/constitution/`
  - Feature stages → `history/prompts/<feature-name>/` (requires feature context)
  - `general` → always `history/prompts/general/`

---

## PHR Stages

All stages are now organized under `history/prompts/` with clear routing:

### Constitution Stage (Project Governance)

| Stage          | Location                     | Extension                 | When to Use                                  |
| -------------- | ---------------------------- | ------------------------- | -------------------------------------------- |
| `constitution` | `history/prompts/constitution/` | `.constitution.prompt.md` | Defining quality standards, project principles |

**Example:** `history/prompts/constitution/0001-define-quality-standards.constitution.prompt.md`

### Feature Stages (TDD Cycle)

| Stage       | Location                    | Extension              | TDD Phase      | When to Use                                 |
| ----------- | --------------------------- | ---------------------- | -------------- | ------------------------------------------- |
| `spec`      | `history/prompts/<feature>/` | `.spec.prompt.md`      | **Specify**    | Writing feature specifications               |
| `plan`      | `history/prompts/<feature>/` | `.plan.prompt.md`      | **Plan**       | Design, planning, API contracts             |
| `red`       | `history/prompts/<feature>/` | `.red.prompt.md`       | **Red**        | Debugging, fixing errors, test failures     |
| `green`     | `history/prompts/<feature>/` | `.green.prompt.md`     | **Green**      | Implementation, new features, passing tests |
| `refactor`  | `history/prompts/<feature>/` | `.refactor.prompt.md`  | **Refactor**   | Code cleanup, optimization                  |
| `explainer` | `history/prompts/<feature>/` | `.explainer.prompt.md` | **Understand** | Code explanations, documentation            |
| `misc`      | `history/prompts/<feature>/` | `.misc.prompt.md`      | **Other**      | Uncategorized feature-specific work         |

**Examples:**
- `history/prompts/authentication/0001-design-jwt-system.plan.prompt.md`
- `history/prompts/authentication/0003-implement-jwt.green.prompt.md`
- `history/prompts/authentication/0004-fix-token-bug.red.prompt.md`

### General Stage (Non-Feature Work)

| Stage     | Location                | Extension            | When to Use                                           |
| --------- | ----------------------- | -------------------- | ----------------------------------------------------- |
| `general` | `history/prompts/general/` | `.general.prompt.md` | General work not tied to a specific feature (setup, configuration, infrastructure) |

**Example:** `history/prompts/general/0001-setup-ci-pipeline.general.prompt.md`

---

## What Happens Behind the Scenes

### Automatic PHR Creation Flow

When you run any significant command:

1. **You execute work** - `/constitution`, `/specify`, `/plan`, debugging, etc.
2. **AI completes the task** - Creates files, writes code, fixes bugs
3. **Stage auto-detected** - System determines: architect, green, red, refactor, etc.
4. **PHR auto-created** - File generated with proper naming and location
5. **Brief confirmation** - You see: `📝 PHR-0003 recorded`

**All metadata captured automatically:**

- Full user prompt (complete multiline text)
- Response summary
- Files modified
- Tests run
- Stage and feature context
- Timestamps and user info

### Integrated SDD Workflow

```
/constitution → PHR created (history/prompts/constitution/)
     ↓
/specify → PHR created (history/prompts/general/)
     ↓
/plan → PHR created (history/prompts/<feature>/) + ADR suggestion
     ↓
/tasks → PHR created (history/prompts/<feature>/)
     ↓
/implement → PHR created (history/prompts/<feature>/)
     ↓
Debug/fix → PHR created (history/prompts/<feature>/)
     ↓
Refactor → PHR created (history/prompts/<feature>/)
```

**PHRs compound throughout the entire workflow—automatically, all under `history/prompts/`.**

### Manual Override (Optional)

You can still use `/phr` explicitly for:

- Custom metadata and labels
- Specific stage override
- Detailed context and links
- Work that wasn't automatically captured

```bash
/phr Define API versioning standards  # Explicit creation with full control
```

But 95% of the time, you won't need to—PHRs just happen!

---

## Daily Workflow with Automatic PHRs

### Morning: Context Loading (2 minutes)

```bash
# Read yesterday's PHRs to rehydrate context - all in one place!
ls history/prompts/*/*.prompt.md | tail -5 | xargs cat

# Or filter by feature
ls history/prompts/authentication/*.prompt.md | tail -5 | xargs cat
```

### During Work: Just Work (PHRs Happen Automatically)

```bash
# You work normally:
/plan Design JWT authentication system
# → AI creates plan.md
# → PHR automatically created: history/prompts/authentication/0001-design-jwt-system.plan.prompt.md
# → You see: 📝 PHR-0001 recorded

/implement Create token generation function
# → AI implements the code
# → PHR automatically created: history/prompts/authentication/0002-implement-token-gen.green.prompt.md
# → You see: 📝 PHR-0002 recorded

# Debug something:
Fix token expiration bug
# → AI fixes the bug
# → PHR automatically created: history/prompts/authentication/0003-fix-expiration-bug.red.prompt.md
# → You see: 📝 PHR-0003 recorded
```

**No `/phr` commands needed!** Every significant interaction is captured automatically.

### Evening: Reflect & Learn (3 minutes)

```bash
# Review today's PHRs - all in history/prompts/
grep -r "Reflection:" history/prompts/ | tail -3

# Find patterns in successful prompts
grep -r "✅ Impact:" history/prompts/ | grep -v "recorded for traceability"

# Count today's PHRs by feature
for dir in history/prompts/*/; do echo "$(basename "$dir"): $(ls "$dir"/*.prompt.md 2>/dev/null | wc -l)"; done
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
  adr: history/adr/0003-jwt-choice.md
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

All PHRs are now in one place: `history/prompts/`

### Find by Topic

```bash
# Find all authentication-related prompts
grep -r "auth" history/prompts/

# Find all prompts about databases
grep -r "database\|sql\|postgres" history/prompts/
```

### Find by Stage

```bash
# Find all debugging sessions (red stage)
find history/prompts -name "*.red.prompt.md"

# Find all planning work (plan stage)
find history/prompts -name "*.plan.prompt.md"

# Find all implementations (green stage)
find history/prompts -name "*.green.prompt.md"
```

### Find by File

```bash
# Find prompts that touched specific files
grep -r "auth.py" history/prompts/

# Find prompts that ran specific tests
grep -r "test_login" history/prompts/
```

### Find by Feature

```bash
# List all PHRs for a specific feature
ls -la history/prompts/authentication/

# Count PHRs per feature
for dir in history/prompts/*/; do echo "$(basename "$dir"): $(ls "$dir"/*.prompt.md 2>/dev/null | wc -l)"; done
```

---

## Advanced Usage

### Team Knowledge Sharing

```bash
# Commit PHRs with your code (all in one place now!)
git add history/prompts/ && git commit -m "Add PHR: JWT authentication implementation"

# Review team's PHRs
git log --all --grep="PHR:" --oneline

# Create team prompt library
mkdir .docs/team-prompts
cp history/prompts/*/*.plan.prompt.md .docs/team-prompts/
```

### Compliance & Auditing

```bash
# Generate audit trail for security work
find history/prompts -name "*.prompt.md" -exec grep -l "security\|auth\|payment" {} \;

# Track when decisions were made
grep -r "date:" history/prompts/ | grep "2025-10"

# Find who worked on what
grep -r "user:" history/prompts/ | sort | uniq
```

### Performance Optimization

```bash
# Find your most effective prompts
grep -r "✅ Impact:" history/prompts/ | grep -v "recorded for traceability"

# Identify patterns in failed attempts
grep -r "❌" history/prompts/

# Track time-to-solution
grep -r "Next prompts:" history/prompts/ | grep -v "none"
```

---

## Integration with SDD Components

### PHRs Link to Everything

```yaml
links:
  spec: specs/001-auth/spec.md # Feature spec
  adr: history/adr/0003-jwt-choice.md # Architectural decision
  ticket: JIRA-123 # Issue tracker
  pr: https://github.com/org/repo/pull/45 # Pull request
```

### Workflow Integration

```
1. /constitution   → history/prompts/constitution/0001-quality-standards.constitution.prompt.md
2. /specify        → history/prompts/general/0001-auth-requirements.spec.prompt.md
3. /plan           → history/prompts/authentication/0001-design-system.plan.prompt.md
4. /adr            → (ADR references the PHR for context)
5. /tasks          → history/prompts/authentication/0002-break-down-tasks.plan.prompt.md
6. /implement      → history/prompts/authentication/0003-implement-jwt.green.prompt.md
7. Debug & fix     → history/prompts/authentication/0004-fix-token-bug.red.prompt.md
8. Refactor        → history/prompts/authentication/0005-extract-middleware.refactor.prompt.md
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

**"Feature stage 'architect' requires specs/ directory and feature context"**

- **Cause**: Using feature stage (`architect`, `red`, `green`, etc.) before specs/ directory exists
- **Solution**: Use pre-feature stages (`constitution`, `spec`) or create a feature first with `/specify`

**"No feature specified and no numbered features found"**

- **Cause**: Working in feature context but no features exist
- **Solution**: Run `/specify` to create your first feature, or specify `--feature` manually

**"Feature directory not found"**

- **Cause**: Specified feature doesn't exist in `specs/`
- **Solution**: Check available features with `ls specs/` or create the feature with `/specify`

**"Warning: No specs/ directory found. Using history/prompts/ for general stage."**

- **Cause**: Using `general` stage when no specs/ directory exists
- **Not an error**: PHR will be created in `history/prompts/` as fallback
- **Suggestion**: Consider using `constitution` or `spec` stages for pre-feature work, or create a feature first

### Manual PHR Creation

If needed, you can create PHRs manually:

```bash
# Constitution PHR
scripts/bash/create-phr.sh \
  --title "Define API standards" \
  --stage constitution \
  --json

# Feature-specific PHR (requires feature context or specs/ directory)
scripts/bash/create-phr.sh \
  --title "Implement login" \
  --stage green \
  --feature "001-auth" \
  --json

# General stage (non-feature work)
scripts/bash/create-phr.sh \
  --title "Setup CI pipeline" \
  --stage general \
  --json
```

**Note:** The script only creates the file with placeholders. The AI agent must fill all `{{PLACEHOLDERS}}` after creation.

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

## Summary: PHRs are Automatic

PHRs are **built into Spec Kit** with automatic creation:

✅ **Completely automatic**: Created after every significant command—no extra work
✅ **Deterministic location** (all under `history/prompts/`):

- Constitution (`constitution`) → `history/prompts/constitution/`
- Feature work (`spec`, `plan`, `tasks`, `red`, `green`, `refactor`, `explainer`, `misc`) → `history/prompts/<feature-name>/`
- General work (`general`) → `history/prompts/general/`
- Clear file naming with stage extensions

✅ **Single location**: All prompts organized in one place (`history/prompts/`) for easy discovery
✅ **Full metadata capture**: Prompts, responses, files, tests, timestamps
✅ **Stage-based organization**: spec, plan, red, green, refactor, explainer, misc, general, constitution
✅ **Learning-focused**: Based on spaced repetition and retrieval practice
✅ **Team-friendly**: Version-controlled, searchable, shareable
✅ **Compliance-ready**: Complete audit trail with no manual effort

**Start using PHRs today** by running `specify init` and working normally. Every AI interaction is automatically captured, documented, and searchable. Your future self (and your team) will thank you! 🚀

### Key Takeaway

> **You don't need to think about PHRs—they just happen.**  
> Work normally with Spec Kit commands, and get automatic documentation of your entire AI-assisted development journey.
