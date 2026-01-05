# user-guide.md

# Spec Kit — Beginner’s Guide (Step-by-Step)

Welcome! This guide shows non-coders and coders alike how to drive projects with Spec-Driven Development using the Spec Kit Expert Agent.

---

## 1) Install the CLI
Open a terminal and run:
```bash
uvx --from git+https://github.com/github/spec-kit.git specify init <PROJECT_NAME>
````

This sets up the workspace, scripts, and templates.

**Optional (nice to have)**

* Install Git
* Set up an AI coding assistant (GitHub Copilot / Claude Code / Gemini CLI)

---

## 2) Open Your Project

Open the folder in your editor (VS Code works great). You’ll see:

* `scripts/`  → helper scripts
* `templates/` → spec/plan/tasks templates
* `memory/` → constitution and checklist
* `specs/` → feature branches and artifacts appear here as you work

---

## 3) Create Your First Feature (`/specify`)

Describe the feature in plain language—focus on **what** and **why**:

```text
/specify "Authenticated login with magic link; journeys: sign-in/out; edge cases: expired links, device changes"
```

What happens:

* A new feature branch is created (e.g., `001-auth-magic-link`)
* A spec file appears under `specs/001-auth-magic-link/spec.md`
* Any unknowns are flagged as `[NEEDS CLARIFICATION: …]`

**Review the spec** and answer any `[NEEDS CLARIFICATION]` items directly in the file.

---

## 4) Plan the Implementation (`/plan`)

Provide concrete constraints and decisions:

```text
/plan "Postgres; SES for email; 1-hour session TTL; throttle: 3 links/hour per user; CLI diagnostics"
```

What happens:

* The plan is written to `specs/<branch>/plan.md`
* Design artifacts are generated:

  * `research.md`, `data-model.md`, `contracts/`, `quickstart.md`
* Constitution checks run; the plan **stops** for review

**Review the artifacts**. If any issues or questions remain, fix or clarify before moving on.

---

## 5) Break Work Into Tasks (`/tasks`)

Create the task list:

```text
/tasks "Prefer library-first; structured JSON logs"
```

What happens:

* `specs/<branch>/tasks.md` is generated
* Tasks are numbered (`T001…`), dependency-ordered, and mark safe parallel blocks with `[P]`
* Tests come first (TDD), then implementation, then polish

---

## 6) Implement (Outside This Agent)

Now engineers (or toolchains) pick tasks from `tasks.md` and implement them in code, using the contracts and tests. Keep your spec and plan in sync as you learn—update them, then regenerate tasks if needed.

---

## Tips

* Keep features small; shorter loops = faster learning.
* Answer `[NEEDS CLARIFICATION]` quickly to unblock progress.
* Prefer simplicity over cleverness; pass constitution gates first.
* Use absolute paths in discussions to avoid confusion.

---

## Quick Reference

* Start: `/specify "…"`, review `spec.md`
* Design: `/plan "…"`, review `plan.md` + supporting docs
* Tasks: `/tasks "…"`, review `tasks.md` for order and `[P]`
* Always stop after each phase to review before proceeding.