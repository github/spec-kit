## SpecKitPlus Quickstart — From Vibe Coding to Spec-Driven Delivery

You just practiced AI pair programming in `01_dev_env/06_ai_pair_programming/` (vibe coding with coding principles). Now we’ll rebuild the same project using SpecKitPlus (SPP) and Spec‑Driven Development (SDD) so you can transfer those skills into a production‑style workflow.

**What you already learned (recap):**
- Prompting patterns, small iterations, and repository‑aware agents
- Guardrails: review diffs, run locally, validate behavior

**What you’ll do now (SPP Quickstart):**
- Rebuild the same app via SDD artifacts (Specify → Plan → Tasks → Implement)
- Keep everything under version control with tests and ADRs
- Use the same agent you prefer (Claude, Cursor, Gemini CLI, Qwen Code, etc.)

**Why SPP for this stage:**
- Structured planning and implementation
- Fewer bugs and clearer UX through specs and tests
- Git‑first workflow with CI in mind
- Works with any coding agent (Claude Code, Cursor, Windsurf, Codeium, etc.)

### Quickstart TL;DR
1. Constitution → [/sp.constitution](#constitution) (jump to full prompt)
2. Specify → [/sp.specify](#specify) (jump to full prompt)
3. Plan → [/sp.plan](#plan) (jump to full prompt)
4. Tasks → [/sp.tasks](#tasks) (jump to full prompt)
5. Implement → [/sp.implement](#implement) (jump to full prompt)
6. Tests + Merge → (see [Test & Merge](#test-and-merge))
7. ADRs as needed → (see [ADRs](#adrs))

## Core Workflow Components

In SDD you start with a spec. It’s the contract for behavior and the source of truth your agents use to generate, test, and validate code. Less guesswork, fewer surprises, higher quality. Here’s the SPP workflow you’ll follow to rebuild the same app:

### 1. Constitution (One-Time Setup)
Sets project principles, standards, and tech stack preferences at the start of your project.

### 2. Feature Lifecycle
The main workflow for planning and implementing features:

- **Specify** - Define business requirements (non-technical)
- **Clarify** (Optional) - Agent asks follow-up questions
- **Plan** - Create technical implementation plan, data models, and service interfaces
- **ADR** - Create or update architectural decision records.
- **Tasks** - Break plan into individual actionable tasks
- **Analyze** (Optional) - Verify documentation completeness
- **Implement** - Agent builds the features
- **PHR** - THe prompts with slash commands are auto recorded. For others you can use `/sp.phr` to auto record your conversations with your ai coder.
- **Test & Merge** - Validate changes and merge to main branch

## Getting Started

### Installing SpecKit

1. Navigate to your project directory
2. Run the installation command:

```bash
uvx speckitplus init <PROJECt_NAME>
```

3. Select your AI agent (Claude, Cursor, Codeium, etc.)
4. Choose your script type (PowerShell, Bash, etc.)

You can install SpecKit for multiple agents simultaneously by running the command multiple times with different agent selections.

## Project Structure

After installation, SpecKit creates:

```
your-project/
├── .speckit/
│   ├── memory/
│   │   └── constitution.md
│   ├── scripts/
│   └── templates/
├── .gemini/
│   └── commands/
├── .cursor/
│   └── prompts/
└── .claude/
    └── commands/
```

**Key Files:**
- **constitution.md** - Project principles and standards
- **scripts/** - Helper scripts for branch creation and workflow automation
- **templates/** - Templates for specs, plans, and tasks
- **commands/prompts** - Detailed instructions for each workflow step

## Step-by-Step Workflow

### Step 1: Constitution

Set up your project standards (run once at project start):

```bash
/sp.constitution
```

**Example prompt:**
```
Write clean and modular code and use Next.js 15 best practices
```

The agent will generate a comprehensive constitution file including:
- Framework best practices
- Component organization
- Code standards
- Architecture decisions

**Pro Tip:** This is a human-in-the-loop process. Review and modify the generated constitution to match your preferences.

Jump to full prompt: [0001 Constitution](#appendix-prompts)

### Step 2: Specify

Define what you want to build (business requirements only):

```bash
/sp.specify
```

**Example prompt:**
```
I would like to build a basic expense tracking app.
- Add, view, and delete expenses
- Track personal expenses with amount, date, categories, and description
- Simple dashboard showing recent expenses and basic totals
- Do not implement user auth as this is just a personal tracker
```

SpecKit automatically:
- Creates a new feature branch
- Generates a spec file with user scenarios, edge cases, and acceptance criteria

Jump to full prompt: [0002 Specify](#appendix-prompts)

### Step 3: Clarify (Optional)

Let the agent ask clarifying questions:

```bash
/sp.clarify
```

The agent will analyze your spec and ask targeted questions to fill gaps:
- UI behavior preferences
- Edge case handling
- Data validation rules
- Feature scope clarifications

**Example questions:**
- "Should the system allow negative amounts to represent refunds?"
- "What does 'recent expenses' mean? Last 10? Last 30 days?"
- "Are descriptions and categories required or optional?"

### Step 4: Plan

Create a technical implementation plan:

```bash
/sp.plan
```

**Provide technical details:**
```
Use Next.js with app router, route handlers, and server actions.
Add backend/server-side logic to a server folder in the src folder.
Use local storage to persist data.
Do not implement auth.
```

SpecKit generates:
- **quick-start.md** - Feature overview and testing scenarios
- **plan.md** - Complete technical plan with data models, contracts, and architecture
- **research.md** - Technical research and decisions
- Agent files updated with project context

Jump to full prompt: [0003 Plan](#appendix-prompts)

### Step 5: Tasks

Break the plan into actionable implementation steps:

```bash
/sp.tasks
```

The agent creates phases with numbered tasks (T001, T002, etc.):
- Phase 3.1: Setup and foundation
- Phase 3.2: Storage and utilities  
- Phase 3.3: Contract tests (TDD)
- Phase 3.4: Server actions
- Phase 3.5: Components
- And so on...

Jump to full prompt: [0004 Tasks](#appendix-prompts)

### Step 6: Implement

Build the features in manageable chunks:

```bash
/sp.implement
```

**Implementation strategies:**

**Option 1 - Full implementation:**
```bash
/sp.implement
```

**Option 2 - Specific tasks:**
```bash
/sp.implement T001 to T005
```

**Option 3 - By phase:**
```bash
/sp.implement phase 3.1
```

**Best Practice:** Implement in small chunks to maintain context window efficiency. Clear chat between phases to prevent context degradation.

The agent will:
1. Run tests (which fail initially - expected behavior)
2. Implement the functionality
3. Re-run tests (which now pass)
4. Mark completed tasks with an X in the tasks file

Jump to full prompt: [0005 Implement](#appendix-prompts)

### Step 7: Test

Follow the quick-start.md guide to manually test your application:
- Verify all user scenarios
- Test edge cases
- Confirm acceptance criteria

### Step 8: Merge

Create a pull request and merge to main:

1. Commit your changes
2. Publish the feature branch
3. Create a pull request on GitHub
4. Review and merge
5. Delete the feature branch
6. Switch back to main and sync

```bash
git checkout main
git pull origin main
```

Jump to full prompt: [0006 PR Checklist](#appendix-prompts)

## Test-Driven Development (TDD)

SpecKit follows TDD principles:

1. **Write tests first** - Tests are created before implementation
2. **Watch tests fail** - Initial test run shows expected failures
3. **Implement features** - Build functionality to pass tests
4. **Tests pass** - Confirms feature completion
5. **Refactor** - Add polish and optimizations

You'll see a `tests/` folder in your project with comprehensive test suites for each feature.

## Using SpecKit with Different Agents

### Claude Code / Cursor
Use slash commands directly:
```bash
/sp.constitution
/sp.specify
/sp.plan
```

### Codeium (or agents without slash commands)
Drag and drop the prompt files into chat:
1. Navigate to `.codeium/prompts/`
2. Drag the desired prompt file (e.g., `constitution.md`) into the chat
3. Add your requirements

**This approach works with ANY coding agent**, making SpecKit universally compatible.

## Adding New Features

To add additional features after completing your first one:

1. Start fresh - no need to run `/sp.constitution` again
2. Run `/sp.specify` with your new feature requirements
3. SpecKit automatically creates a new feature branch
4. Follow the complete workflow (clarify → plan → tasks → implement)
5. Each feature gets its own isolated spec folder
6. Merge when complete

**Example:**
```bash
/sp.specify

Please add a budget tracking feature to this app.
```

## Conclusion

SpecKit transforms AI coding agents from unpredictable tools into structured development partners. By following professional development practices and maintaining clear documentation, you'll consistently build production-ready applications that match your vision.


---

## Appendix: Prompts (Copy & Paste)

### 0001 Constitution
```
/sp.constitution

Project type: Rebuild the same app from 01_dev_env/06_ai_pair_programming using SDD.
Priorities: Readable, modular code; tests first; ADRs for consequential decisions.
Stack: Python 3.12+/uv; keep agent prompts/versioned artifacts in repo.
Quality bar: CI green required, coverage ≥ 80% for touched modules.
```

### 0002 Specify
```
/sp.specify

Feature: simple math calculator with cli interface for testing and usage.
User journeys: list primary flows; include at least one edge case per flow.
Acceptance criteria: explicit inputs/outputs, status codes, error messages.
Constraints: performance budget, file size/time limits, non-goals.
Success metrics: what we will measure to accept this feature.
```

### 0003 Plan
```
/sp.plan

Produce: architecture sketch, interfaces, data model, error taxonomy, NFRs.
Decisions needing ADR: enumerate candidates with options and tradeoffs.
Testing strategy: unit + integration cases derived from acceptance criteria.
```

### 0004 Tasks
```
/sp.tasks

Break plan into small tasks (T001..), each ≤ 30 minutes, testable, reversible.
Add dependencies between tasks; group into phases; mark deliverables per task.
```

### 0005 Implement
```
/sp.implement T001..T005

Rules: tests first, smallest diff, keep public API stable within a phase.
After each task: run tests, update checklist, note deltas to spec if needed.
```

### 0006 PR Checklist
```
Checklist before merge:
- [ ] Spec and plan updated to match implementation
- [ ] All new/changed code has tests; coverage target met
- [ ] ADR added/updated for consequential decisions
- [ ] CI green; manual smoke verified
- [ ] PR description links spec section(s) and ADR(s)
```