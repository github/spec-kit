# AI Agent Guidelines

**Version:** 2.2
**Last Updated:** 2025-11-02

---

## 1. Quick Reference

**Core Principle:** Specifications are the **single source of truth**. Never guess, always clarify.

**Document Priority:** Constitution > Spec > Plan > Supporting Docs

**Task States:** `[ ]` pending, `[x]` complete, `[F]` failed, `[B]` blocked, `[W]` waiting for approval

**Critical Rules:**

| DO | DON'T |
|----|-------|
| Stop & emit `CLARIFICATION NEEDED` when unclear | Commit secrets/API keys/credentials |
| Follow Constitution at all times | Modify `.specify/` during implementation |
| Run formatters → linters → tests before commit | Add requirements not in specs |
| Update spec first if issues found | Proceed when spec is unclear |
| Mark tasks immediately after completion | Override human feedback without updated spec |

**RFC 2119 Keywords:** MUST/MUST NOT (mandatory), SHOULD/SHOULD NOT (recommended), MAY (optional)

**When Stuck - Decision Tree:**

```text
Problem → Action
├─ Spec unclear? → CLARIFICATION NEEDED (5.1), mark tasks [B], WAIT
├─ Test failed?
│  ├─ Syntax/typo? → Auto-fix max 2× (7.3)
│  ├─ Logic error? → Mark [F], REPORT, WAIT (7.3)
│  └─ Flaky? → Document, ESCALATE (7.3)
├─ Constitution conflict? → STOP, FLAG, WAIT (7.2)
├─ Missing dependency/file? → research.md, [B], ESCALATE (7.4)
├─ Version conflict? → CLARIFICATION NEEDED (5.4)
├─ License conflict? → research.md, suggest alternatives (9.2)
├─ Workflow command fails? → Check, retry 1×, escalate (3)
├─ Gate fails? → STOP, check plan.md justification (6.6)
└─ Git conflict? → abort, REPORT, WAIT (8.1)
```

---

## 2. Purpose

AI agent behavioral/operational standards for Spec-Driven Development using Spec Kit framework. Agents MUST follow to ensure deterministic, auditable, production-ready contributions aligned with specs and Constitution.

---

## 3. Document Structure & Priority

**Project Structure:**

```text
project-root/
├── .specify/memory/constitution.md    # Immutable principles
├── .specify/templates/                 # Templates
├── .specify/scripts/                   # Scripts
└── specs/[###-feature-name]/
    ├── spec.md                         # WHAT/WHY
    ├── plan.md                         # HOW
    ├── data-model.md, contracts/, research.md, quickstart.md, tasks.md
```

**Priority (Highest→Lowest):**

1. **Constitution** - Immutable. Ex: "no ORMs" overrides spec suggestion
2. **Spec** - Requirements. Ex: "CSV export" overrides plan "JSON only"
3. **Plan** - Architecture. Ex: Plan's library choice overrides agent preference
4. **Supporting Docs** - Sub-priority: data-model > contracts > research > quickstart > tasks

**Conflict Resolution:** STOP → emit `CLARIFICATION NEEDED` (conflicting sections) → DO NOT guess → WAIT for human + spec update

**Workflow Commands:**

| Command | Output | Description |
|---------|--------|-------------|
| `/speckit.specify` | spec.md | Create spec from description |
| `/speckit.clarify` | Updated spec.md | Resolve ambiguities |
| `/speckit.plan` | plan.md + design docs | Generate architecture |
| `/speckit.tasks` | tasks.md | Generate task list |
| `/speckit.implement` | Code + tests | Execute tasks |
| `/speckit.resume` | Restored context | Resume from state/tasks |

**Command Failure:** REPORT error → CHECK prerequisites → RETRY 1× (transient) → ESCALATE (persistent)

---

## 4. Core Responsibilities

Agents MUST interpret specs as **single source of truth** and produce deterministic, production-ready results.

### 4.1 Specification Interpretation

- **MUST** read in priority order (3) before implementation
- **MUST** derive all logic from specs only
- **MUST NOT** add requirements/dependencies/opinions not in specs
- **SHOULD** cross-reference spec/plan/supporting docs

**Context Window:** If docs exceed capacity: (1) read Constitution+Spec+Plan fully, (2) load supporting docs on-demand, (3) emit warning, (4) reserve 30%/40%/30% for docs/code/history. **If mandatory docs don't fit:** STOP, emit `CONTEXT OVERFLOW`, suggest splitting, WAIT.

**Binary Files:** If spec references images/PDFs: emit warning, REQUEST text description in spec/plan, DO NOT proceed with assumptions.

### 4.2 Code Generation

**MUST** generate code that is:

- **Functionally Deterministic:** Same logic/behavior (timestamps/UUIDs in metadata may vary)
- **Idempotent:** Re-execution doesn't duplicate/corrupt
- **Production-ready:** Compiles, passes tests, follows conventions

**Randomness Seeds (priority):** (1) Explicit in spec/plan, (2) Hash of feature dir name, (3) Fixed constant (e.g., 0)

**Output:** All artifacts from plan, tests for every acceptance scenario

---

## 5. Behavioral Principles

### 5.1 Ambiguity Protocol

**When unclear:** emit `CLARIFICATION NEEDED` with: Document+line, Question, Options, Recommendation (if Constitution-aligned), Blocked tasks

**Multiple Ambiguities:** BATCH if found upfront. EMIT immediately + CONTINUE non-blocked if found during implementation.

**Scope Decision:**

| Ambiguity Type | Action |
|----------------|--------|
| Fundamental (affects all) | STOP ALL WORK |
| Isolated (affects some) | STOP blocked, CONTINUE others |
| Detail (affects function) | CONTINUE, emit clarification |

### 5.2 Minimal Changes

**Small:** 1 scenario/story per commit, 1-5 files, <300 lines

**Exceptions (>300 lines OK):** Generated code, migrations, test fixtures, scaffolding (1st commit), lockfiles

**Partial Implementation:** MAY ship incremental user stories. MUST NOT ship half-implemented (broken code). CAN ship `[B]` blocked with research.md docs. CANNOT ship `[F]` failed.

### 5.3 Rationale

**MUST** link to spec sections in commits/code:

- **Commit:** "Implement [###-name]: Story 2, Scenario 1\n- Adds X per spec.md L67-72\nRefs: specs/[###-name]/spec.md"
- **Code:** `# Implements spec.md Story 2, Scenario 1: CSV export (plan.md 3.4)`

### 5.4 Read-Only Defaults

**Allowed:** src/, tests/, dev configs (`/config/{dev,test,local,development,staging}.*`), build files (Makefile, package.json, Cargo.toml, pyproject.toml, go.mod, etc.)

**Build Files:** IF plan mentions → follow. IF spec requires dependency → MAY add + document in research.md. IF neither → CLARIFICATION NEEDED.

**Dependency Conflicts:** CHECK existing → DETECT conflicts (version/compatibility) → emit `CLARIFICATION NEEDED` (current vs required, options) → PREFER existing if compatible.

**Prohibited:** `.specify/*`, `specs/[###-name]/*.md`, production configs (`/config/*.{production,prod}.*`), dependencies (`node_modules`, `.venv`, `target`, `build`), `.git`, system files

### 5.5 Guardrails

See 5.4 Prohibited. **Exception:** Changes with plan justification.

### 5.6 Traceability

**PR Template:** Feature, Spec/Plan paths, Status (✅/⏳ user stories), Constitution Compliance (gates + coverage ≥80% line, 100% scenario), Acceptance Testing, How to Test (→quickstart.md)

### 5.7 Compliance

**MUST** follow Constitution. **If conflict:** STOP → FLAG → DO NOT proceed without human decision.

---

## 6. Quality & Verification

### 6.1 Pre-Commit

**MUST run:** Formatters, linters, type checkers, build verification

**WHERE/WHEN/HOW:** Local / before commit / via hooks or CI scripts

**No hooks?** Check configs (.pre-commit-config.yaml, package.json, Makefile) → run manually → document missing automation in research.md.

### 6.2 Acceptance Testing

**For each Given-When-Then:** test code that (1) sets up Given, (2) executes When, (3) asserts Then

**Failure Policy:** Fix all scenarios for story before complete. MAY proceed to next story if current passes. MUST NOT ship PR with failing scenarios. **Priority:** P1 before P2/P3.

**Time-Dependent:** MUST use mocking (freezegun, Sinon, timecop, Clock, clockwork). Document in plan.md. **Example:** `@freeze_time("2025-01-01 12:00")` + jump time vs real sleep.

### 6.3 Contract Compliance

**IF contracts/ exists:** (1) Compare endpoints to definitions, (2) Validate schemas exactly, (3) Test error responses, (4) Verify auth

**Tools (SHOULD use if available):** OpenAPI (Spectral, Redocly), GraphQL (graphql-inspector), REST (Pact, Spring Cloud Contract)

### 6.4 Data Model Alignment

**IF data-model.md exists:** Verify migrations/models/validation/relationships match schemas

### 6.5 Quickstart Verification

**IF quickstart.md exists:** Follow steps exactly, verify outputs, test edge cases

### 6.6 Constitution Gates

**Common:** Library-First, CLI Interface, Test-First, Simplicity (max 3 projects), Anti-Abstraction, Integration-First

**Gate fail = BLOCKER.** MUST NOT proceed without plan.md "Complexity Tracking" justification.

**Custom Gates (non-Constitution):** Verify same as Constitution gates. Treat as blocker unless marked "SHOULD"/"aspirational". Report in PR.

### 6.7 Fail Fast

**Abort:** STOP → REPORT (test/build failed, error, blocked scenario, affected tasks) → UPDATE tasks.md `[F]` → EMIT issue (7.3) → WAIT

**Report to:** Console (interactive), CI log (automated), tasks.md comments (async)

---

## 7. Violation Handling & Recovery

**Pattern:** Trigger → Response (actions) → Recovery (resolution)

### 7.1 Specification Violations

**Trigger:** Spec ambiguous/contradictory/incomplete

**Response:** DETERMINE scope (see 5.1 table) → STOP (as appropriate) → EMIT `CLARIFICATION NEEDED` → DO NOT guess → WAIT

**Recovery:** Human updates spec → agent detects (interactive: "CLARIFICATION PROVIDED" msg; git: `git log -1 spec.md` every 5min; file: timestamp every 5min; CI: timeout plan.md or 30min) → re-read spec → validate resolved → resume

### 7.2 Constitutional Violations

**Trigger:** Spec/implementation conflicts Constitution

**Response:** STOP all → FLAG (article, spec requirement, conflict reason) → REQUEST human decision → WAIT

**Resolution:** (A) Human updates spec to align, OR (B) Human adds justification to plan.md Complexity Tracking

### 7.3 Quality Failures

**Trigger:** Tests fail or quality checks fail

**Response:** SUSPEND → REPORT (6.7) → DETERMINE: (1) Obvious (syntax, typos, imports) → auto-fix max 2×, (2) Ambiguous (logic, assertions) → mark `[F]`, WAIT, (3) Spec issue → `CLARIFICATION NEEDED`

**Flaky Tests (non-deterministic pass/fail):** IDENTIFY (different errors, timeouts, races, network deps) → DOCUMENT in research.md (test, evidence, root cause, recommendations) → EMIT warning → mark `[F]` → ESCALATE. **DO NOT:** retry >2×, mark passed, ignore.

**Recovery:** Obvious → fix + retest + resume (if ≤2 attempts). Ambiguous → human diagnosis + fix + retest. Spec issue → human updates spec + regenerate.

### 7.4 Technical Blockers

**Types:** Missing dependencies/credentials, missing/renamed files, platform incompatibility

**Response:** DOCUMENT in research.md (blocker, blocked tasks, description, impact, alternatives, recommendation, status) → UPDATE tasks.md `[B]` with comment → SUGGEST alternatives → ESCALATE

**Missing Files:** SEARCH similar (fuzzy) → IF found: `CLARIFICATION NEEDED` (similar files found, question) → IF not found: `CLARIFICATION NEEDED` (no similar files, should create or path wrong?) → DO NOT create without confirmation.

**Recovery:** Human provides dependency/API/credentials → validate available → resume

### 7.5 Constitution Ambiguity

**Trigger:** Constitution article vague (e.g., "Keep it simple" - how many files?)

**Common ambiguous:** Simplicity (how many?), Libraries (even if 10× larger?), Test-first (which types?), Optimization (what's premature?)

**Response:** STOP → DOCUMENT ambiguity → EMIT `CONSTITUTION AMBIGUITY` (article, question, current situation, interpretations, blocked) → DO NOT proceed → WAIT

**Recovery:** Human clarifies (constitution.md note or message) → re-read → validate understanding → proceed

---

## 8. Collaboration Protocol

### 8.1 Version Control

- **MUST** commit after validation passes (6.1)
- **MUST** atomic commits (1 story/scenario)
- **MUST** reference feature + spec sections
- **MUST** work on feature branch `[###-feature-name]`
- **SHOULD** group related tasks into scenario/story commits

**Timing:** Complete → mark `[x]` → validate → IF pass: commit, IF fail: fix + repeat

**Parallelization:** SHOULD 1 task at time. MAY parallel IF no shared deps/files/models AND agent capable. MUST NOT parallel if shared files/models or dependencies.

**Merge Conflicts:** git abort → REPORT (files, local/remote changes) → DO NOT resolve → WAIT

**Rollback:** DO NOT delete branch → IF merged: revert → IF not merged: reset --hard (only if human requests) → PREFER fix commits → WAIT for direction before force-push/delete

### 8.2 Change Communication

**MUST** update design docs when trade-offs occur. **MUST** document decisions in research.md: Chosen, Rationale, Alternatives (rejected + why), Trade-offs, References. **MUST** use PR template (5.6).

### 8.3 Feedback Loop

**MUST** update spec first if issues found. **MUST NOT** override human feedback without updated spec. **MUST** regenerate when specs updated.

**Regeneration Strategy:**

| Spec Change | Strategy | Action |
|-------------|----------|--------|
| Requirements added | Incremental | Add new code, keep existing |
| Requirements modified | Selective | Regen affected functions/classes |
| Architecture changed | Full | Regen entire modules from scratch |
| Data model changed | Full | Regen models, migrations, deps |
| Acceptance criteria changed | Test-first | Regen tests → update impl to pass |

**Workflow:** Identify scope → backup (git commit) → regen tests → regen impl → validate → IF fail: fix or repeat. **When in doubt:** prefer incremental/selective, ALWAYS tests before impl, NEVER delete working code without backup.

---

## 9. Ethics & Safety

### 9.1 Prohibited Actions

**MUST NOT:** Commit secrets/keys/tokens/passwords, share PII in logs, make undisclosed network calls, exfiltrate data

**Detection MUST:** Run scanners (git-secrets, truffleHog, gitleaks, detect-secrets), validate no hardcoded credentials (patterns: password=, api_key=, token=, secret=), check data leaks (PII, emails, IPs). **SHOULD:** Use .gitignore for sensitive files (`.env`, `credentials.json`, `*.pem`, `*.key`)

### 9.2 Licensing

**MUST** respect licenses. **SHOULD** prefer permissive (MIT, Apache, BSD). **MUST NOT** include closed-source without approval. **MUST** ensure privacy/compliance alignment.

**Conflicts:** STOP → DOCUMENT in research.md (library+license, Constitution requirement, why needed) → SUGGEST compatible alternatives → ESCALATE → WAIT

### 9.3 Standards & Portability

**SHOULD** prefer open standards (JSON > binary), portable code. **MUST** document platform deps in plan.md if unavoidable.

**Platform Deps:** Document WHERE (plan.md "Platform Requirements"), WHAT (OS/version/arch/libs), WHY (why platform-specific needed), ALTERNATIVES (rejected cross-platform + why)

---

## 10. Meta-Guidelines

### 10.1 Document Errors

**IF** error in AGENTS.md: EMIT `DOCUMENT ERROR` (location, issue, impact, severity) → CONTINUE implementation → LOG for human. **DO NOT:** stop for minor errors, attempt fix, ignore severe contradictions.

### 10.2 Version Management

**MUST** use version at **start of feature** implementation. **DO NOT** switch mid-feature. **IF** new version released during: complete current with original → adopt new for **next** feature.

**Upgrade triggers:** New feature starts, human requests, critical bug fix (human notifies)

**Detection:** Check line 3-4. Document in PR: "Implemented per AGENTS.md v2.2"

---

## 11. Glossary

**Acceptance Criteria** - Measurable conditions for user story completion (spec.md)

**Acceptance Scenario** - Given-When-Then test case defining success criteria

**Atomic Commit** - Single logical change implementing 1 story/scenario

**Constitution** - Immutable project principles (`.specify/memory/constitution.md`)

**Constitution Gate** - Yes/no compliance check (plan.md). Gate failure = blocker without justification.

**Complexity Tracking** - Table in plan.md: `| Violation | Why Needed | Simpler Alternative Rejected |`

**Deterministic** - Same spec → functionally equivalent code (behavior identical, metadata may vary)

**Feature Branch** - Git branch `[###-feature-name]` for specific feature

**Feature Directory** - `specs/[###-feature-name]/` with all feature docs

**Feature Directory Name** - Format `[###-feature-name]` (e.g., `001-user-auth`)

**Given-When-Then** - Scenario format: "Given [context] When [action] Then [outcome]"

**Idempotent** - Re-execution produces same result without side effects

**Implementation Plan** - `plan.md` defining HOW (technical architecture)

**Feature Specification** - `spec.md` defining WHAT/WHY (requirements)

**P1/P2/P3** - Priority levels (P1=must-have, P2=should-have, P3=nice-to-have)

**Pre-Commit Validation** - Formatters → linters → type checkers → build before commit

**Single Source of Truth** - Authoritative specification documents

**Supporting Documents** - Optional artifacts: data-model, contracts, research, quickstart, tasks

**Task States** - `[ ]` pending, `[x]` complete, `[F]` failed, `[B]` blocked (external), `[W]` waiting (approval)

**User Story** - High-level requirement: "As [user], I want [goal] so that [benefit]". Contains acceptance scenarios.

---

*AI agents MUST internalize and honor these guidelines for quality, consistency, and specification alignment in Spec-Driven Development projects using Spec Kit.*
