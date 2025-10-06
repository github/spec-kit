# What is [Spec-Driven Development](https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/)?

Instead of coding first and writing docs later, in spec-driven development, you start with a (you guessed it) spec. This is a contract for how your code should behave and becomes the source of truth your tools and AI agents use to generate, test, and validate code. The result is less guesswork, fewer surprises, and higher-quality code.

In 2025, this matters because:

- AI IDEs and agent SDKs can turn ambiguous prompts into a lot of code quickly. Without a spec, you just get **elegant garbage faster**.
- Agent platforms (e.g., **OpenAI Agents SDK**) make multi-tool, multi-agent orchestration cheap—but the **cost of weak specifications is amplified** at scale.
- The broader ecosystem (e.g., GitHub’s recent “spec-driven” tooling push) is converging on **spec-first workflows** for AI software.

### Why it beats “vibe coding”

- Captures decisions in a **reviewable artifact** instead of buried chat threads.
- **Speeds onboarding** and cross-team collaboration.
- Reduces **rework and drift** because tests/examples anchor behavior.

### Tools & patterns mentioned/adjacent in the ecosystem

- **Spec-Kit Plus** (Panaversity open-source toolkit)
- **Spec-Kit** (GitHub’s open-source toolkit) — templates and helpers for running an SDD loop with your AI tool of choice.
- Broader coverage in recent articles summarizing SDD’s rise and best practices.

## How Spec-Kit Plus Works: Automatic Documentation + Explicit Decision Points

Spec-Kit Plus extends GitHub's Spec Kit with two key innovations:

### 1. **Automatic Prompt History Records (PHR)**

Every significant AI interaction is automatically captured as a structured artifact—no extra commands needed. You work normally, and get complete documentation of your AI-assisted development journey.

**What gets captured automatically:**

- `/constitution` commands → PHR created
- `/specify` commands → PHR created
- `/plan` commands → PHR created + ADR suggestion
- `/tasks` commands → PHR created
- `/implement` commands → PHR created
- Debugging, refactoring, explanations → PHRs created

**You see:** Brief confirmation like `📝 PHR-0003 recorded`

### 2. **Explicit Architecture Decision Records (ADR)**

After planning completes, you get a suggestion to review for architectural decisions. You explicitly run `/adr` when ready to capture significant technical choices.

**Flow:**

```
/plan completes
    ↓
📋 "Review for architectural decisions? Run /adr"
    ↓
(You run /adr when ready)
    ↓
ADRs created in docs/adr/ (if decisions are significant)
```

**Why explicit?** Architectural decisions require careful judgment, team discussion, and review of existing patterns. You control when this happens.

---

## The Complete SDD Workflow

### Core Modules (Required for Every Feature)

0. **[Module 00 – Setup Environment](00_setup_speckit_plus/readme.md)**

   - Install Spec-Kit Plus: `pip install specifyplus`
   - Initialize project: `sp init my-app --ai gemini`
   - Get automatic PHR + explicit ADR capabilities

1. **[Module 01 – QuickStart HandsOn Project](01_quickstart/readme.md)**

2. **[Module 02 – Define Constitution](02_constitution/readme.md)**

   - Set project principles and quality standards
   - Creates: `memory/constitution.md`
   - **PHR automatically created** 📝

3. **[Module 03 – Write Specification](03_spec/readme.md)**

   - Capture business requirements and acceptance criteria
   - Creates: `docs/prompts/NNNN-feature-name.spec.prompt.md`
   - **PHR automatically created** 📝

4. **[Module 04 – Create Plan](04_plan/readme.md)**

   - Design technical architecture and implementation approach
   - Creates: `specs/NNN-feature/plan.md`
   - **PHR automatically created** 📝
   - **ADR suggestion appears** 📋

5. **[Module 05 – Review Architectural Decisions](05_adr/readme.md)**

   - **(You explicitly run `/adr` when ready)**
   - Captures significant technical choices with context
   - Creates: `docs/adr/NNNN-decision-title.md`

6. **[Module 06 – Generate Task List](06_tasks/readme.md)**

   - Break down implementation into verifiable tasks
   - Creates: `specs/NNN-feature/tasks.md`
   - **PHR automatically created** 📝

7. **[Module 07 – Implement](07_implementation/readme.md)**
   - Execute tasks with TDD cycle (Red → Green → Refactor)
   - Creates: Code, tests, documentation
   - **PHR automatically created for each work session** 📝

### Knowledge Management Modules

10. **[Module 10 – Prompt History Records (Overview)](10_phr/readme.md)**

    - Understand how automatic PHR capture works
    - Learn PHR location rules (pre-feature vs feature-specific)
    - Search and leverage your accumulated AI knowledge

11. **[Module 11 – Analyze & Clarify](11_analyze_and_clarify/readme.md)**
    - Advanced spec analysis and clarification techniques
    - When/how to refine specifications
    - Troubleshooting ambiguous requirements

### Practice Projects

- **[Module 08 – Capstone Chatbot Project](08_chatbot_project/readme.md)**

  - End-to-end SDD practice: spec → plan → ADR → tasks → implement
  - Build a complete chatbot following full workflow

- **[Module 09 – Operationalize Nine Articles](09_operationalize_nine_articles/readme.md)**
  - Advanced: Apply SDD to operationalize complex concepts
  - Practice with real-world documentation challenges

[From Spec to Deploy: Building an Expense Tracker with SpecKit](https://dev.to/manjushsh/from-spec-to-deploy-building-an-expense-tracker-with-speckit-1hg9)

[Watch: Spec-Driven Development in the Real World](https://www.youtube.com/watch?v=3le-v1Pme44)

---

## Key Workflow Patterns

### Pattern 1: Pre-Feature Work (Constitution + Specs)

```bash
sp init my-project --ai qwen  # Setup once
/constitution Define quality standards
  → 📝 PHR-0001 created in docs/prompts/

/specify Create authentication feature
  → 📝 PHR-0002 created in docs/prompts/
  → Branch created: feat/001-authentication
  → Spec created: docs/prompts/0002-auth-feature.spec.prompt.md
```

### Pattern 2: Feature Development (Plan → ADR → Tasks → Implement)

```bash
/plan Design JWT authentication system
  → 📝 PHR-0001 created in specs/001-auth/prompts/
  → Plan created: specs/001-auth/plan.md
  → 📋 "Review for architectural decisions? Run /adr"

/adr  # When ready to review
  → Creates: docs/adr/0001-jwt-authentication.md
  → Creates: docs/adr/0002-token-refresh-strategy.md

/tasks Break down implementation
  → 📝 PHR-0002 created in specs/001-auth/prompts/
  → Tasks created: specs/001-auth/tasks.md

/implement Write token generation function
  → 📝 PHR-0003 created in specs/001-auth/prompts/
  → Code + tests created
```

### Pattern 3: Debugging & Refactoring

```bash
# Just ask for help or make changes:
Fix token expiration bug
  → 📝 PHR-0004 created (stage: red)

Extract authentication middleware
  → 📝 PHR-0005 created (stage: refactor)

# No extra commands needed!
```

---

## What You Get

### Automatic Documentation (No Extra Work)

- **PHRs** in `docs/prompts/` and `specs/*/prompts/`
- Complete record of every AI interaction
- Searchable with `grep`, `find`, full-text search
- Version-controlled with your code

### Explicit Decision Records (When Needed)

- **ADRs** in `docs/adr/`
- Captures WHY behind technical choices
- Links to specs, plans, alternatives, consequences
- Sequential numbering (0001, 0002, 0003, etc.)

### Structured Artifacts

- **Constitution** - Project principles
- **Specs** - Business requirements
- **Plans** - Technical architecture
- **Tasks** - Implementation breakdown
- **Code + Tests** - Working software

---

## Quick Reference: Commands & Automation

| Command         | What It Does                   | PHR Created? | ADR Created?       |
| --------------- | ------------------------------ | ------------ | ------------------ |
| `/constitution` | Define project principles      | ✅ Automatic | ❌ No              |
| `/specify`      | Write feature spec             | ✅ Automatic | ❌ No              |
| `/plan`         | Design architecture            | ✅ Automatic | 📋 Suggestion only |
| `/adr`          | Review architectural decisions | ❌ No\*      | ✅ Explicit        |
| `/tasks`        | Break down implementation      | ✅ Automatic | ❌ No              |
| `/implement`    | Execute TDD cycle              | ✅ Automatic | ❌ No              |
| Debugging       | Fix errors                     | ✅ Automatic | ❌ No              |
| Refactoring     | Clean up code                  | ✅ Automatic | ❌ No              |
| `/phr` (manual) | Override automatic PHR         | ✅ Explicit  | ❌ No              |

\* The `/adr` command itself doesn't create a PHR, but the planning session before it does

---

Each module guide includes:

- **Inputs** - What you need before starting
- **Actions** - Step-by-step workflow
- **Outputs** - Artifacts created
- **Quality gates** - What "done" looks like
- **Common pitfalls** - What to avoid
- **Examples** - Real-world scenarios

Ready to build muscle memory for spec-driven development? Start with Module 01! 🚀

> **Note**: Use `specifyplus` or `sp` commands.

### Quick start

```bash
# Install from PyPI (recommended)
pip install specifyplus
# or with uv
uv tool install specifyplus

# Use the CLI
specifyplus init my-app
# or alias
sp init my-app

# One-time usage
uvx specifyplus --help
uvx specifyplus init my-app
```

### Take-home checklist

- Start every feature with a **one-page intent brief** and **acceptance criteria**.
- Store **spec.md**, **plan.md**, and **examples/tests** in the repo; review them like code.
- Make every PR link to the spec section it implements; **fail CI** if required examples/tests are missing.
- Periodically **refactor the spec** (not just the code) as understanding evolves.

---

## Official Spec Kit Plus resources

- [Spec Kit Plus GitHub repository](https://github.com/panaversity/spec-kit-plus) — enhanced templates, scripts, and CLI
- [PyPI package](https://pypi.org/project/specifyplus/) — install with `pip install specifyplus`
- [Original Spec Kit repository](https://github.com/github/spec-kit) — base implementation
- [Spec Kit video overview](https://www.youtube.com/watch?v=a9eR1xsfvHg) — walkthrough of the end-to-end workflow
