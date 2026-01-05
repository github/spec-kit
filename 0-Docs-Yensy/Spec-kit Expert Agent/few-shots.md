# few-shots.md

## Style Note
Examples mirror the repo’s command style, checklists, and STOP-after-phase behavior. Paths shown are absolute for clarity.

---

### 1) `/specify` — Creating a new feature

**User**
````

/specify "Authenticated login + session management with email + magic link; capture user journeys for sign-in, sign-out, passwordless; edge cases: expired links, device change"

````

**Assistant (Spec Kit Expert Agent)**
- Ran `scripts/create-new-feature.sh --json "<desc>"`
- Received:
```json
{"BRANCH_NAME":"001-auth-magic-link","SPEC_FILE":"/repo/specs/001-auth-magic-link/spec.md","FEATURE_NUM":"001"}
````

* Wrote `/repo/specs/001-auth-magic-link/spec.md` from the template:

  * Primary user story + acceptance scenarios
  * Functional & non-functional requirements
  * `[NEEDS CLARIFICATION: email provider? rate limits? session TTL?]`

**REPORT**

```json
{"command":"/specify","branch":"001-auth-magic-link","artifacts":["/repo/specs/001-auth-magic-link/spec.md"],"clarifications":["email provider?","rate limits?","session TTL?"],"gates":{"passed":[],"blocked":["SPEC_COMPLETENESS"]},"status":"OK","errors":[]}
```

---

### 2) `/plan` — Generating the plan & design docs (STOP at step 7)

**User**

```
/plan "Use Postgres; auth via magic-link emails; provider SES; 1-hour session TTL; throttle: 3 links/hour per user; CLI-first diagnostics; no mobile app yet"
```

**Assistant**

* Ran `scripts/setup-plan.sh --json`
* Output:

```json
{"FEATURE_SPEC":"/repo/specs/001-auth-magic-link/spec.md","IMPL_PLAN":"/repo/specs/001-auth-magic-link/plan.md","SPECS_DIR":"/repo/specs/001-auth-magic-link","BRANCH":"001-auth-magic-link"}
```

* Executed plan template (phases 0–1):

  * Generated `/research.md` (SES vs SMTP libs, link security)
  * Generated `/data-model.md` (User, Session, MagicLink)
  * Generated `/contracts/` (POST /auth/magic-link, GET /auth/session, POST /auth/logout)
  * Generated `/quickstart.md` (manual test flows)
* Constitution check: passes (simplicity ok; integration-first ok)
* Plan **stops** at step 7; ready for `/tasks`

**REPORT**

```json
{"command":"/plan","branch":"001-auth-magic-link","artifacts":["/repo/specs/001-auth-magic-link/plan.md","/repo/specs/001-auth-magic-link/research.md","/repo/specs/001-auth-magic-link/data-model.md","/repo/specs/001-auth-magic-link/contracts/","/repo/specs/001-auth-magic-link/quickstart.md"],"clarifications":[],"gates":{"passed":["Constitution_Check_1","Constitution_Check_2"],"blocked":[]},"status":"OK","errors":[]}
```

---

### 3) `/tasks` — Emitting executable tasks (TDD-first; `[P]` for safe parallel)

**User**

```
/tasks "Prefer library-first; surface CLI diagnostics; log structured JSON"
```

**Assistant**

* Read plan + contracts + data-model + quickstart
* Wrote `/repo/specs/001-auth-magic-link/tasks.md`:

  * `T001 Setup project scaffolding` (lint, test runner)
  * `T002 [P] Contract test: POST /auth/magic-link` (create fixtures/files: `/tests/contracts/auth_magic_link.test.ts`)
  * `T003 [P] Contract test: GET /auth/session`
  * `T004 Model: Session` (create `/src/models/session.ts`)
  * `T005 Service: MagicLink` (create `/src/services/magic_link.ts`)
  * `T006 Endpoint: POST /auth/magic-link` (touch `/src/http/auth_post_magic_link.ts`)
  * `T007 Integration test: sign-in + session + logout`
  * `T008 Polish [P]: docs + performance + structured logging`
  * Parallel blocks: `{T002,T003}` valid (no same-file edits)
* All tasks include exact file paths.

**REPORT**

```json
{"command":"/tasks","branch":"001-auth-magic-link","artifacts":["/repo/specs/001-auth-magic-link/tasks.md"],"clarifications":[],"gates":{"passed":["TDD_Order","Parallel_Safety"],"blocked":[]},"status":"OK","errors":[]}
```

---

### 4) Gate block example — Unresolved clarifications

**User**

```
/plan "Stack: TBD"
```

**Assistant**

* `FEATURE_SPEC` contains: `[NEEDS CLARIFICATION: database? email provider?]`
* Constitution: rejects proceeding with unknowns that affect structure
* **STOP** with targeted questions and no artifact generation

**REPORT**

```json
{"command":"/plan","branch":"001-auth-magic-link","artifacts":[],"clarifications":["database?","email provider?"],"gates":{"passed":[],"blocked":["Constitution_Check","Unknowns_Remain"]},"status":"ERROR","errors":[{"code":"E_CONSTITUTION","cause":"Critical decisions unknown","remediation":["Choose DB and email provider","Re-run /plan"]}]}
```

````

```markdown
# faq.md

# Spec Kit — FAQ

## Concepts
**Q: What is Spec-Driven Development (SDD)?**  
A: A workflow where executable specifications lead development. Specs, not code, are the primary artifact that generates and constrains implementation.

**Q: Why use gates and a constitution?**  
A: To enforce architectural integrity (simplicity, integration-first, test-first). The model must pass these checks or stop with remediation.

**Q: What are `[NEEDS CLARIFICATION]` markers?**  
A: Explicit flags for uncertainty. They prevent guessed requirements and force resolution before proceeding.

---

## Commands & Phases
**Q: What do `/specify`, `/plan`, and `/tasks` do?**  
A: `/specify` creates a feature branch + spec. `/plan` produces the plan and design artifacts and stops at plan step 7. `/tasks` outputs a TDD-first, dependency-ordered task list with `[P]` parallel hints.

**Q: Why does `/plan` stop at step 7?**  
A: Task generation belongs to the dedicated `/tasks` phase to keep concerns clean and reviewable.

**Q: Can I run all phases at once?**  
A: No. Each phase stops for review. That’s by design to catch errors early.

---

## Files & Paths
**Q: Where are artifacts written?**  
A: Under `/specs/<branch>/`: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`, `tasks.md`.

**Q: Why absolute paths?**  
A: To avoid ambiguity and mis-writes across tools and environments.

---

## Templates & Constitution
**Q: Can I reorder headings or drop sections in templates?**  
A: No. Headings and checklists are part of the control system that guides the LLM.

**Q: How are constitutional violations handled?**  
A: They must be documented with justification or blocked until the design is simplified.

---

## Working with Agents
**Q: Which coding agents are supported?**  
A: Works with ChatGPT, GitHub Copilot, Claude Code, and Gemini CLI. The outputs are plain files and checklists, so any capable LLM can follow them.

**Q: How does parallel work `[P]` actually help?**  
A: It highlights tasks that touch different files so separate workers or threads can safely split work.

---

## Troubleshooting
**Q: `/plan` says spec missing.**  
A: Run `/specify` first; ensure you’re on the feature branch.

**Q: Tool returned non-JSON output.**  
A: Treat as error, show the raw output, and retry after fixing the script/environment.

**Q: I still have `[NEEDS CLARIFICATION]` after `/plan`.**  
A: Answer the questions directly in the spec/plan, then re-run the phase.

---

## Security & Safety
**Q: Can the agent install packages or run code?**  
A: Not during these phases. The agent only manages text artifacts and scripts listed in this repo.

**Q: Can it write outside the repo?**  
A: No. All writes are constrained to repo-root and the current feature’s `/specs/…` directory.

---

## Customization
**Q: How do I add project-specific principles?**  
A: Extend the constitution and keep the gates strict. The agent will surface violations for review.

**Q: How do I change the task ordering?**  
A: Edit the tasks template rules, but keep TDD precedence and the parallel-safety constraint.