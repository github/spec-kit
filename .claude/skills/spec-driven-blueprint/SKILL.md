---
name: spec-driven-blueprint
description: Guide a user through Spec-Driven Development (SDD) end-to-end and produce a single consolidated Markdown blueprint that drives implementation. Use when the user wants to plan a new feature with the full SDD discipline (constitution → specify → clarify → plan → tasks) and end up with one executable artifact instead of running multiple slash commands. Trigger phrases include "drive development with a spec", "create an SDD blueprint", "walk me through spec-driven development", "guide me through the spec-kit workflow".
---

# Spec-Driven Blueprint Skill

Take a fuzzy product idea and turn it into a single, executable Markdown blueprint that an LLM (or human) can implement straight through. This skill consolidates the spec-kit workflow — constitution, specify, clarify, plan, tasks — into one guided interview and one output file: `BLUEPRINT.md`.

## When to Use

- The user has an idea but no concrete spec, plan, or task list yet.
- The user wants the rigor of spec-kit (`/speckit.specify`, `/speckit.plan`, `/speckit.tasks`) without invoking each command separately.
- The user wants a single Markdown file they can hand to another agent, paste into a PR description, or check into the repo.
- The repo is or is not a spec-kit project — this skill works in either case.

## When NOT to Use

- The user has already run `/speckit.specify` and friends and wants to keep using those commands. Defer to them.
- The task is a one-line bug fix or trivial change — no blueprint needed.
- The user just wants a code change right now and explicitly does not want planning artifacts.

## Core Output: `BLUEPRINT.md`

This skill produces **one file**: `BLUEPRINT.md` (path configurable, default at the repo root or under `specs/<NNN>-<short-name>/BLUEPRINT.md` if the repo is spec-kit-initialized). The file is structured so that each section can be lifted into spec-kit's own templates if desired, but is also self-contained.

The blueprint sections, in order:

1. **Header** — feature name, short-name, date, status, source idea quote.
2. **Constitutional Gates** — the non-negotiable principles this feature respects (Library-First, CLI Interface, Test-First, Simplicity ≤3 projects, Anti-Abstraction, Integration-First). Each gate is a checkbox the implementer can verify.
3. **User Scenarios** — prioritized user stories (P1/P2/P3...) with Given/When/Then acceptance scenarios. P1 must be an independently shippable MVP slice.
4. **Edge Cases** — explicit list of boundary conditions and failure modes.
5. **Functional Requirements** — `FR-001`, `FR-002`, ... each testable. `[NEEDS CLARIFICATION: ...]` markers where unavoidable (max 3).
6. **Key Entities** — domain concepts (no implementation detail).
7. **Success Criteria** — measurable, technology-agnostic outcomes (`SC-001`, `SC-002`, ...).
8. **Assumptions** — defaults the user accepted by not specifying otherwise.
9. **Technical Context** — language, primary deps, storage, testing, target platform, project type, performance goals, constraints, scale.
10. **Project Structure** — concrete directory tree for source and tests.
11. **Tasks** — sequenced, dependency-ordered, organized by user story. Strict format: `- [ ] T### [P?] [USx?] Description with file path`.
12. **Dependencies & Execution Order** — phase dependencies, story dependencies, parallel opportunities.
13. **Implementation Strategy** — MVP-first, incremental delivery, parallel team variants.
14. **Open Questions** — any unresolved `[NEEDS CLARIFICATION]` items, escalated for the user.

## Workflow

Make a TodoWrite list of the phases below and work them in order. Mark each phase complete as you go — never skip ahead even if you think you have enough information.

### Phase 0 — Detect Environment

1. Check whether the repo is spec-kit-initialized: does `.specify/` or `templates/spec-template.md` exist?
2. Check whether `memory/constitution.md` or `.specify/memory/constitution.md` exists. If yes, **read it** and treat its principles as binding for this blueprint.
3. Decide the output path:
   - Spec-kit repo: `specs/<NNN>-<short-name>/BLUEPRINT.md` (compute `NNN` by scanning existing `specs/` dirs, three-digit zero-padded).
   - Otherwise: `./BLUEPRINT.md` at the repo root.
4. Tell the user the detected mode and the planned output path. Ask them to confirm or override.

### Phase 1 — Capture the Idea

Ask the user, in one message, for:

- **One-paragraph problem statement**: What are they trying to build, for whom, and why now?
- **Existing constraints**: Any tech stack mandate, deadline, compliance requirement, or platform target they already know?
- **What's explicitly out of scope** for this slice?

Do not ask follow-ups yet. Capture the answer verbatim into a working buffer; you will quote it in the blueprint header.

### Phase 2 — Generate Short Name and Confirm Output Path

From the problem statement, derive a 2-4 word kebab-case short-name (action-noun: `add-user-auth`, `fix-payment-timeout`, `analytics-dashboard`). Show it to the user with the resolved output path; let them override before continuing.

### Phase 3 — Constitution Gates

If a constitution file was found in Phase 0, list its principles back to the user and ask: "Any gate you want to relax or add for this feature?"

If no constitution exists, propose the spec-kit defaults:

- Library-First (every feature begins as a standalone library)
- CLI Interface (text in/out, JSON support)
- Test-First (NON-NEGOTIABLE — tests written, approved, and failing before implementation)
- Simplicity (≤3 projects, no future-proofing)
- Anti-Abstraction (use frameworks directly, single model representation)
- Integration-First Testing (real environments over mocks, contract tests mandatory)

The user can drop or modify any of these. Record the final list — every gate becomes a checkbox in the blueprint's Constitutional Gates section.

### Phase 4 — User Scenarios (the WHAT)

Draft 2-5 user stories with priorities. Rules:

- **P1 must be an independently shippable MVP** — if you implement only P1, the user gets real value.
- Each story has: brief title, narrative paragraph, "Why this priority", "Independent Test" description, and 1-3 Given/When/Then acceptance scenarios.
- Stay at the user-value level — no implementation detail. If you find yourself writing "use Redis" or "POST /api/foo", stop and rewrite at the user level.

Show the draft to the user. Ask: "Are these the right priorities? Add, remove, or re-rank any."

### Phase 5 — Functional Requirements & Entities

From the user stories, derive:

- **Functional Requirements** (`FR-001`, ...): each must be testable and unambiguous. Use "System MUST...", "Users MUST be able to...".
- **Key Entities** (if data is involved): name + 1-line description + key attributes. **No** schema, no field types, no SQL.
- **Edge Cases**: boundary conditions, failure modes, empty states.

When the user prompt genuinely doesn't specify something, prefer **informed defaults** and record them in the Assumptions section. Only emit `[NEEDS CLARIFICATION: <specific question>]` markers when:

- The choice significantly impacts scope or UX.
- Multiple reasonable interpretations exist with materially different implications.
- No reasonable default exists.

**Hard cap: 3 `[NEEDS CLARIFICATION]` markers across the whole blueprint.** If you generate more, keep only the 3 highest-impact and resolve the rest with informed defaults.

### Phase 6 — Clarify (only if needed)

If any `[NEEDS CLARIFICATION]` markers remain, present them to the user as a numbered set of questions, **all in one message**, formatted as:

```markdown
## Question N: <Topic>

**Context**: <quote from spec>

**What we need to know**: <the question>

**Suggested Answers**:

| Option | Answer | Implications |
|--------|--------|--------------|
| A      | ...    | ...          |
| B      | ...    | ...          |
| C      | ...    | ...          |
| Custom | Provide your own | ...      |

**Your choice**: _waiting for response_
```

Wait for the user's response, then replace each `[NEEDS CLARIFICATION]` with the chosen answer. Do not proceed to Phase 7 with any markers remaining.

### Phase 7 — Success Criteria

Generate 3-6 measurable, technology-agnostic outcomes. Each must be:

- **Measurable**: time, percentage, count, rate.
- **Technology-agnostic**: no framework, language, or database name.
- **User/business-facing**: not "API < 200ms" but "users see results instantly".
- **Verifiable** without knowing the implementation.

Examples:

- ✅ "Users can complete checkout in under 3 minutes."
- ✅ "95% of searches return results in under 1 second."
- ❌ "Redis cache hit rate above 80%." (technology-specific)

### Phase 8 — Technical Context (the HOW, high level)

Now ask the user about implementation. Single message, structured:

- **Language/Version** (e.g., Python 3.12, TypeScript 5.4, Rust 1.75)
- **Primary Dependencies / Frameworks**
- **Storage** (Postgres, SQLite, files, none)
- **Testing framework**
- **Target Platform** (Linux server, browser, iOS, etc.)
- **Project Type** (single library, CLI, web app, mobile + API, ...)
- **Performance Goals**
- **Constraints** (memory, latency, offline, budget)
- **Scale/Scope** (users, data volume, features)

Anything the user leaves blank → mark as `NEEDS CLARIFICATION` in Technical Context **only** (these don't count against the 3-marker cap from Phase 5; they're tech-context unknowns, not spec ambiguity).

### Phase 9 — Constitution Re-check

Walk through each gate from Phase 3. For each:

- **Pass** → leave the checkbox unchecked (implementer will check) and move on.
- **Fail / Justified violation** → add a row to the Complexity Tracking table with `Violation | Why Needed | Simpler Alternative Rejected Because`.

If you cannot justify a gate failure, **do not proceed**. Tell the user the gate is failing and ask them to either accept the simpler alternative or provide justification.

### Phase 10 — Project Structure

Pick the layout that matches Project Type:

- **Single project** (default): `src/{models,services,cli,lib}` + `tests/{contract,integration,unit}`
- **Web app**: `backend/src/{models,services,api}` + `frontend/src/{components,pages,services}` + tests in each
- **Mobile + API**: `api/...` + `ios/` or `android/`

Render the concrete tree. No `Option 1/2/3` labels — just the chosen tree.

### Phase 11 — Tasks

Generate a task list organized by user story. Hard rules:

- **Phase 1 — Setup** (no story label): project init, dependencies, lint config.
- **Phase 2 — Foundational** (no story label): blocking prerequisites for all stories. Database schema, auth framework, base models, error handling, logging. **Nothing user-story-specific.** This phase blocks all subsequent phases.
- **Phase 3+ — One phase per user story** in priority order (P1 → P2 → P3 ...). Each story phase has a checkpoint at the end stating the story is now independently testable.
- **Final phase — Polish & Cross-Cutting**: docs, perf, security hardening, quickstart validation.

Every task strictly follows: `- [ ] T### [P?] [USx?] Description with exact file path`.

- `T###` is sequential across the whole blueprint.
- `[P]` only when the task touches different files than other `[P]` tasks in the same phase and has no dependency on incomplete tasks.
- `[USx]` is required for user-story phase tasks, forbidden for Setup/Foundational/Polish.
- Tests, when included, come **before** implementation tasks they cover.

After the task list, add **Dependencies & Execution Order** (phase deps, story deps, intra-story rules, parallel opportunities) and **Implementation Strategy** (MVP-first, incremental, parallel-team).

### Phase 12 — Write `BLUEPRINT.md`

Write the file to the path confirmed in Phase 2 / Phase 0. Use the structure laid out in **Core Output**. Use absolute paths when calling Write.

### Phase 13 — Validate

Self-review the blueprint against this checklist (this is your unit-test for the document — fix any failures before reporting back):

- [ ] No implementation details leaked into User Scenarios, Functional Requirements, or Success Criteria.
- [ ] At most 3 `[NEEDS CLARIFICATION]` markers in spec sections (Phases 4–7).
- [ ] Every Functional Requirement is testable.
- [ ] Every Success Criterion is measurable and technology-agnostic.
- [ ] P1 user story is independently shippable as an MVP.
- [ ] Every task has an ID, a file path, a checkbox, and (if a story task) a `[USx]` label.
- [ ] No task in Setup or Foundational has a `[USx]` label.
- [ ] No story task in a later phase blocks an earlier P1 task.
- [ ] Constitutional Gates section lists every principle from Phase 3.
- [ ] Complexity Tracking exists if any gate is violated; absent otherwise.
- [ ] Technical Context fields are filled or marked `NEEDS CLARIFICATION`.

Run up to 3 self-review iterations. After 3, if anything still fails, list the failing items in the blueprint's **Open Questions** section and warn the user.

### Phase 14 — Report

Reply to the user with:

- Path to `BLUEPRINT.md`.
- Counts: user stories (by priority), functional requirements, success criteria, tasks (total + per phase).
- List of any `[NEEDS CLARIFICATION]` markers still present.
- Suggested next step: "Hand this blueprint to an implementing agent, or run `/speckit.implement` if this is a spec-kit project pointed at this directory."

Keep the report under 200 words.

## Design Principles for the Skill Itself

- **Ask in batches, not drip-by-drip.** Each phase asks for everything it needs in one message and waits.
- **Default aggressively, ask sparingly.** The 3-marker cap is intentional — guess the rest with industry-standard defaults and document them in Assumptions.
- **WHAT before HOW.** Phases 4-7 stay user-facing. Phase 8+ go technical. Don't let tech bleed into spec.
- **One file out.** Resist the temptation to scatter `spec.md`, `plan.md`, `tasks.md`. The point of this skill is consolidation.
- **Test the document like code.** Phase 13's checklist is the unit test. The blueprint isn't done until it passes.

## Reference Files

- `blueprint-template.md` (next to this SKILL.md): the full template structure with all sections, ready to be filled in.
- `example-blueprint.md`: a worked example for a small feature, for the model to pattern-match against.

When writing the final `BLUEPRINT.md`, start from `blueprint-template.md` and fill in section by section — do not invent a different structure.
