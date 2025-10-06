# Spec-Kit Workflow & Troubleshooting Guide

## 🗺️ Command Flow Visual Guide

```
┌─────────────────────────────────────────────────────────────────┐
│                    START NEW FEATURE                             │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │  /constitution (optional)    │◄─── First time only or when
        │  Define project principles   │     updating governance rules
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │     /specify                 │
        │  What do you want to build?  │◄─── Focus on WHAT & WHY
        │  (Requirements & user stories)│     NOT the tech stack yet
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │     /clarify (REQUIRED)      │◄─── MUST run before /plan
        │  Structured Q&A to fill gaps │     unless explicitly skipped
        │  Covers edge cases & details │     for spike/prototype work
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │        /plan                 │◄─── NOW specify tech stack
        │  How will you build it?      │     (frameworks, databases,
        │  (Architecture & tech stack) │      APIs, deployment, etc.)
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │       /tasks                 │
        │  Break down into actionable  │
        │  implementation steps        │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │    /analyze (recommended)    │◄─── Validate before coding
        │  Check consistency & gaps    │     Catches issues early
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │      /implement              │
        │  Execute the implementation  │
        │  TDD approach with testing   │
        └──────────────┬───────────────┘
                       │
                       ▼
        ┌──────────────────────────────┐
        │   Test & Iterate             │
        │   Refine as needed           │
        └──────────────────────────────┘
```

## ❓ When Should I Use Each Command?

### `/constitution`
**When to use:**
- Starting a brand new project for the first time
- Establishing or updating project-wide principles and standards
- Defining governance rules that will guide all development decisions

**Skip if:**
- Constitution already exists and hasn't changed
- Working on a quick spike or experiment

**Example prompt:**
```
/constitution Create principles focused on code quality, testing standards, 
user experience consistency, and performance requirements
```

---

### `/specify`
**When to use:**
- Beginning work on any new feature or capability
- You have a clear idea of WHAT you want to build
- Before you've thought about the HOW (tech stack)

**Scope guidance:**
- ✅ GOOD: Single feature or bounded capability ("user authentication system")
- ✅ GOOD: Specific user workflow ("photo album organization with drag-drop")
- ❌ TOO BIG: Entire application ("build Instagram clone")
- ❌ TOO SMALL: Minor fix ("change button color")

**Common mistakes:**
- Including tech stack details (save for `/plan`)
- Being too vague ("make it better")
- Specifying entire MVPs instead of features

**Example prompt:**
```
/specify Build a photo organization feature that allows users to create albums 
grouped by date, with drag-and-drop reordering. Albums cannot be nested. 
Within each album, photos display in a tile grid interface.
```

---

### `/clarify`
**When to use:**
- **REQUIRED** after `/specify` and before `/plan`
- When specification has ambiguous or underspecified areas
- To ensure all edge cases and requirements are covered

**Skip only if:**
- Explicitly building a spike or throwaway prototype
- You consciously want to defer decisions

**What it does:**
- Asks structured questions about your spec
- Records answers in a Clarifications section
- Ensures comprehensive coverage before technical planning

**Common mistakes:**
- Skipping this step and jumping straight to `/plan` (causes rework)
- Not validating the Review & Acceptance Checklist

**Example interaction:**
```
User: /clarify
Agent: I have several questions about the photo organization spec:
        1. What happens when a user tries to add the same photo to multiple albums?
        2. How should the system handle very large albums (1000+ photos)?
        3. Should there be a maximum number of albums per user?
        ...
```

---

### `/plan`
**When to use:**
- After `/specify` and `/clarify` are complete
- When ready to make technical architecture decisions
- When you know the tech stack you want to use

**What to include:**
- Specific frameworks and versions (e.g., "React 18.3 with Vite")
- Database choices (e.g., "PostgreSQL 16 with Prisma ORM")
- API architecture (REST, GraphQL, etc.)
- Deployment targets (cloud providers, containerization)
- Testing strategies

**Common mistakes:**
- Using at the wrong time (before spec is clarified)
- Being too vague ("use modern stack")
- Over-engineering for the scope

**Example prompt:**
```
/plan Use Vite with vanilla HTML/CSS/JavaScript. Store photo metadata in 
SQLite database. No external image uploads - everything local. Implement 
drag-and-drop with native HTML5 APIs.
```

---

### `/tasks`
**When to use:**
- After `/plan` is validated and complete
- When ready to break down into actionable steps
- Before implementation begins

**What it produces:**
- Ordered list of implementation tasks
- Dependency markers
- Parallel execution opportunities (marked with [P])
- File paths and specific actions

**Common mistakes:**
- Running before plan is complete
- Not reviewing tasks for logical ordering

---

### `/analyze`
**When to use:**
- After `/tasks` is complete
- Before running `/implement`
- When you want to catch issues early

**What it checks:**
- Consistency between spec, plan, and tasks
- Coverage gaps (requirements without tasks)
- Constitution compliance
- Duplications and ambiguities
- Task ordering issues

**Severity levels:**
- 🔴 CRITICAL: Must fix before implementing
- 🟡 HIGH: Should fix before implementing
- 🔵 MEDIUM: Can fix but not blocking
- ⚪ LOW: Optional improvements

---

### `/implement`
**When to use:**
- All previous steps are complete and validated
- Tasks are reviewed and ordered correctly
- You're ready to execute the implementation

**What it does:**
- Parses task breakdown from `tasks.md`
- Executes tasks in correct order
- Respects dependencies and parallel markers
- Follows TDD approach
- Runs local CLI commands (npm, dotnet, etc.)

**Prerequisites:**
- Constitution, spec, plan, and tasks must all exist
- Required tools must be installed locally

---

## 🚨 Common Problems & Solutions

### Problem: "I don't know which command to use first"

**Solution:** Always follow this order:
1. `/constitution` (first time only)
2. `/specify` (what to build)
3. `/clarify` (fill gaps)
4. `/plan` (how to build)
5. `/tasks` (break it down)
6. `/analyze` (validate)
7. `/implement` (execute)

---

### Problem: "My branch name is terrible / doesn't make sense"

**Issue:** The `/specify` command generates branch names automatically, sometimes with poor results.

**Workaround:** 
- Manually rename the branch after creation using `git branch -m new-name`
- Be more specific in your `/specify` prompt about the feature name
- Consider opening an issue or PR for a `/rename` command ([Issue #521](https://github.com/github/spec-kit/issues/521))

---

### Problem: "Should I use /specify for my whole app or just features?"

**Solution:** `/specify` is designed for **individual features**, not entire applications.

**Do this:**
```
/specify User authentication system with email/password login
/specify Dashboard with real-time metrics display  
/specify Export data to CSV functionality
```

**NOT this:**
```
/specify Build a complete task management application ❌
```

**Why:** Spec-kit works best with bounded, feature-sized chunks that fit in a single PR.

---

### Problem: "I already have an existing project - how do I use spec-kit?"

**Solution:** spec-kit is currently optimized for new features, not retrofitting entire codebases.

**Approaches:**
1. Use `specify init . --force` in existing repo root
2. Focus on NEW features you're adding
3. Treat each new feature as its own spec-driven cycle
4. See [Issue #164](https://github.com/github/spec-kit/issues/164) for ongoing discussion

---

### Problem: "The agent is creating files in the wrong place"

**Common causes:**
- Project structure not clearly defined in constitution
- Agent focusing on spec-kit instructions instead of actual code
- Over-engineered solutions

**Solutions:**
- Explicitly define directory structure in `/constitution` or `/plan`
- Review `/analyze` output for structural issues
- Ask agent to "keep it simple" and follow existing patterns
- Reference [Issue #75](https://github.com/github/spec-kit/issues/75)

---

### Problem: "How do I update to the latest spec-kit version?"

**Solution:** 

For persistent installation:
```bash
uv tool upgrade specify-cli --from git+https://github.com/github/spec-kit.git
```

For one-time usage (automatic):
```bash
uvx --from git+https://github.com/github/spec-kit.git specify init project-name
```

See [Issue #324](https://github.com/github/spec-kit/issues/324) for more details.

---

### Problem: "When should I create a new branch?"

**Answer:** The `/specify` command automatically creates a feature branch for you.

**Branch naming convention:**
- Format: `NNN-feature-name` (e.g., `001-user-auth`, `002-photo-albums`)
- Created automatically in `specs/NNN-feature-name/` directory
- One branch per feature specification

**If you need to work across multiple features:**
- Create separate specs and branches
- Use git to manage merging
- Keep features independent when possible

---

## 🎯 Decision Trees

### "Should I run /clarify?"

```
Did you just run /specify? 
    YES → Run /clarify (unless spike/prototype)
    NO → Maybe not needed

Is this a production feature?
    YES → Definitely run /clarify
    NO → Consider skipping for experiments

Are there any ambiguous requirements?
    YES → Run /clarify
    NO → Still recommended to run
```

### "Should I use spec-kit for this task?"

```
Is this a new feature or capability?
    YES → ✅ Good fit for spec-kit
    NO → Continue...

Is this a bug fix or small change?
    YES → ❌ Probably overkill
    NO → Continue...

Will this result in multiple files/changes?
    YES → ✅ Good fit for spec-kit
    NO → ❌ Too small for spec-kit

Do I need to think through architecture?
    YES → ✅ Great fit for spec-kit
    NO → ❌ Just code it directly
```

---

## 📚 Additional Resources

- **[Full Methodology](./spec-driven.md)**: Deep dive into Spec-Driven Development philosophy
- **[Installation Guide](./docs/installation.md)**: Setup instructions for all platforms
- **[Local Development](./docs/local-development.md)**: Contributing to spec-kit itself
- **[GitHub Issues](https://github.com/github/spec-kit/issues)**: Report problems or request features

---

## 💡 Pro Tips

1. **Read the constitution first** - It guides all subsequent decisions
2. **Don't skip /clarify** - It prevents costly rework during implementation
3. **Keep features bounded** - One PR-sized feature per spec cycle
4. **Review /analyze output** - Catches 80% of issues before coding starts
5. **Validate the checklist** - Ask agent to check off items in Review & Acceptance
6. **Iterate on specs** - Don't treat first spec draft as final
7. **Use free-form refinement** - After `/clarify`, you can still ask follow-up questions
8. **Check research.md** - Verify agent chose correct tech stack versions

---

## 🤝 Contributing to This Guide

Found something missing or confusing? Please:
- Open an issue with the `documentation` label
- Submit a PR with improvements
- Share your workflow challenges in discussions

This guide is a living document - your feedback makes it better!