# The SDD & Spec Kit Crash Course

*From philosophy to a shipped product — how a senior engineer uses Spec-Driven
Development as load-bearing infrastructure, not ceremony.*

> **Who this is for.** Engineers who already ship software and want SDD to be a
> real part of their lifecycle — not a demo. The running example is built by a
> fictional senior AI engineer shipping an **agentic product with a real
> frontend**, because that is where SDD earns its keep: non-determinism, evals,
> human-in-the-loop review, and a UI that has to feel good.
>
> **How to read it.** Parts I–II are the *why* and the *mental model*. Part III
> is the *reference* (every command, when to reach for it). Part IV is the
> *t0 → shipped* walkthrough with real prompts. Part V is how to operate it like
> a senior — including when **not** to use SDD.
>
> **A note on the code samples.** Prompts are shown in full because they are the
> thing you actually type. Generated artifacts (`spec.md`, `plan.md`, etc.) are
> shown as **captions and structure only** — Spec Kit writes the prose; your job
> is to learn the *shape* so you can review it.

---

## Table of Contents

- [Part I — The Philosophy](#part-i--the-philosophy)
- [Part II — The Software Design Approach](#part-ii--the-software-design-approach)
- [Part III — Spec Kit Features & How-Tos](#part-iii--spec-kit-features--how-tos)
- [Part IV — End-to-End: t0 to a Shipped Product](#part-iv--end-to-end-t0-to-a-shipped-product)
- [Part V — Operating SDD Like a Senior](#part-v--operating-sdd-like-a-senior)
- [Appendix — Cheat Sheets](#appendix--cheat-sheets)

---

## Part I — The Philosophy

### 1.1 The power inversion

For decades, **code was the source of truth** and the spec was scaffolding —
written once, approved, then quietly abandoned the moment "real work" began.
The artifact you trusted was the one the machine ran.

Spec-Driven Development **inverts that relationship**: the **specification
becomes the durable, executable artifact**, and code becomes its *expression* —
regenerable, replaceable, downstream. You no longer hand-translate intent into
syntax and lose fidelity at every step. You maintain intent precisely enough
that an AI agent can produce a faithful implementation from it, again and again.

The practical consequence: when requirements change, you **change the spec and
regenerate**, instead of archaeology-ing through code to reconstruct what was
meant. The spec stops being documentation *about* the system and becomes the
*lever that moves* the system.

### 1.2 Why this is viable *now* (and wasn't before)

This idea is old; what changed is that LLMs got good enough to do the
"specification → working code" step with real fidelity. Three forces converge:

- **Capability** — models can now interpret rich natural-language intent and
  produce coherent, multi-file implementations.
- **Cost of change collapsed** — re-deriving an implementation from an updated
  spec is now minutes, not a sprint, so treating code as disposable is rational.
- **Complexity demands it** — modern products carry constraints (compliance,
  multi-stack, AI non-determinism) that *need* a structured intent layer to stay
  coherent.

The bottleneck moved. It is no longer "how fast can you type code." It is **"how
precisely can you express what you actually want, and how well can you keep that
expression honest."** SDD is the discipline for that.

### 1.3 Core principles

SDD rests on a handful of commitments:

- **Intent before mechanism** — define the *what* and *why* completely before
  the *how*. The stack is a downstream decision, not the starting point.
- **Multi-step refinement over one-shot generation** — you do not "prompt once
  and pray." You build a spec, interrogate it, plan against it, decompose it,
  and only then implement. Each step is a checkpoint.
- **Explicit uncertainty** — unknowns are *marked*, not silently guessed.
  Ambiguity surfaces as `[NEEDS CLARIFICATION]`, not as a confident hallucination
  three files deep.
- **Guardrails over vibes** — organizational principles (the *constitution*) and
  structured templates constrain the model toward good outcomes instead of
  hoping the prompt was perfect.
- **The spec is the contract** — reviews, debates, and decisions happen at the
  spec/plan layer where they are cheap, not in a code review where they are
  expensive and late.

### 1.4 What SDD is **not**

A senior recognizes SDD by what it refuses to be:

- **Not "write a giant doc, then code by hand."** The artifacts are
  *operational* — they drive generation. A spec nobody regenerates from is just
  waterfall with extra steps.
- **Not vibe coding.** Vibe coding optimizes for "something that runs." SDD
  optimizes for "the thing we agreed to build, traceable to why."
- **Not a replacement for engineering judgment.** The model drafts; **you** own
  the constitution, the clarifications, the gate decisions, and the review. SDD
  *concentrates* your judgment at the highest-leverage points.
- **Not all-or-nothing.** You can run the full pipeline on a load-bearing feature
  and skip straight to `/speckit.implement` on a throwaway. Match ceremony to
  stakes (see §5.4).

---

## Part II — The Software Design Approach

SDD is not just a workflow; it is an opinion about *how software should be
designed*. Five ideas carry the weight.

### 2.1 The constitution as architectural law

Before any feature exists, you write a **constitution** — a small set of binding
principles that govern *every* subsequent decision. It lives at
`.specify/memory/constitution.md` and is referenced during specify, plan, and
implement.

Think of it as the project's **non-negotiable invariants**: code-quality rules,
a testing mandate, UX consistency requirements, performance budgets, dependency
discipline. Crucially, principles are **enforced as gates**, not posted as
inspirational wallpaper. A plan that violates "Test-First" or "Minimal
Dependencies" is supposed to *fail the gate* and force either a fix or an
explicit, justified exception.

> The original SDD essay frames these as numbered "Articles" (Library-First,
> CLI Interface, Test-First, Simplicity, Anti-Abstraction, Integration-First,
> etc.). The exact articles matter less than the move: **promote your hardest-won
> engineering values into machine-checkable gates that the agent must pass
> through.**

### 2.2 Intent layer vs. mechanism layer

SDD draws a hard line through your artifacts:

| Layer | Artifact | Answers | Owner of truth |
| --- | --- | --- | --- |
| **Intent** | `spec.md` | *What* / *why* — user stories, requirements, acceptance criteria | Product + Eng, no stack |
| **Mechanism** | `plan.md`, `research.md`, `data-model.md`, `contracts/` | *How* — stack, schemas, APIs, trade-offs | Eng |
| **Execution** | `tasks.md` → code | *Do it* — ordered, testable units | Agent, reviewed by Eng |

The discipline: **keep the stack out of the spec.** "Users can drag-and-drop
albums" belongs in the spec. "We use React DnD Kit with optimistic updates"
belongs in the plan. This separation is what lets the same intent be
re-implemented in a different stack, and what keeps spec reviews about *product*
rather than *frameworks*.

### 2.3 Template-driven quality: how structure constrains the model

Spec Kit's templates are not formatting — they are **guardrails that make LLMs
produce better output**. Concretely, the templates:

- **Prevent premature implementation detail** — the spec template structurally
  pushes "how" content into later phases.
- **Force explicit uncertainty** — `[NEEDS CLARIFICATION]` markers are *required*
  where the input is silent, converting silent assumptions into visible
  questions.
- **Encode checklists and gates** — the model must walk a structured sequence
  (requirement completeness, constitution check, simplicity/anti-abstraction
  gates) rather than free-associate.
- **Order file creation** — research before data-model before contracts before
  tasks, so each artifact stands on a settled foundation.

The insight worth internalizing: **a good template is a prompt that runs every
time, on every feature, without you remembering to type it.** That is where
consistency at scale comes from.

### 2.4 The pre-implementation gates ("Phase −1")

Before code is generated, the plan passes through gates derived from your
constitution. Canonical examples:

- **Simplicity gate** — are you adding more moving parts than the problem
  requires? Default to fewer projects, fewer layers.
- **Anti-abstraction gate** — are you wrapping frameworks in needless
  indirection? Use the platform directly until you have a concrete reason not to.
- **Integration-first gate** — are contracts defined and is testing wired against
  real integrations before unit minutiae?

A gate failure is a **feature, not a blocker**: it catches over-engineering and
ambiguity while the cost of changing course is a paragraph edit, not a rewrite.

### 2.5 Spec persistence: greenfield, brownfield, and evolution

SDD does **not** prescribe a single way to keep `spec.md`/`plan.md`/`tasks.md`
alive after requirements shift. You choose a persistence model:

- **0→1 (greenfield)** — generate everything from high-level intent; the spec is
  born with the code.
- **Iterative enhancement (brownfield)** — add features to an existing system;
  specs describe deltas and integrate with reality on disk.
- **Spec evolution** — when requirements change, update the spec and re-derive,
  using `/speckit.converge` to fold reality and intent back together.

The senior move is to **decide your persistence model deliberately** at project
start, and to treat the spec as a living asset under version control alongside
the code — not a one-time generation prompt.

---

## Part III — Spec Kit Features & How-Tos

Spec Kit is the toolkit that operationalizes SDD: a CLI (`specify`) that
bootstraps your repo, and a set of agent slash-commands (`/speckit.*`) that drive
the pipeline.

### 3.1 Install and initialize

```bash
# Install the CLI (requires uv). Pin to the latest release tag.
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@vX.Y.Z

# Scaffold a project wired for your agent. --integration picks the agent.
specify init redaktor --integration copilot      # or: claude, gemini, codex, ...

# Initialize inside an existing repo (brownfield):
specify init . --here --integration copilot

# Keep the CLI current:
specify self check          # read-only: is a newer release available?
specify self upgrade        # upgrade in place
```

> **Agent-agnostic, with one syntax note.** Most agents expose commands as
> `/speckit.specify`, `/speckit.plan`, etc. **Codex CLI in skills mode** uses
> `$speckit-*`; **GitHub Copilot CLI** uses `/agents` to select the agent. This
> guide uses the `/speckit.*` form, and the examples are written against
> **Claude Code**.

What `init` gives you: the `.specify/` directory (constitution, templates,
scripts), the `/speckit.*` commands registered with your agent, and the repo
prepared for the `specs/NNN-feature/` layout.

### 3.2 The core pipeline at a glance

The spine of every feature is five commands. The supporting cast (clarify,
analyze, checklist, converge, taskstoissues) wraps around them.

```text
/speckit.constitution   →  .specify/memory/constitution.md      (project law, once-ish)
        │
/speckit.specify        →  specs/NNN-feature/spec.md            (WHAT/WHY; new branch)
        │   ⟂ /speckit.clarify   (de-risk ambiguity before planning)
/speckit.plan           →  plan.md + research.md + data-model.md + contracts/ + quickstart.md
        │   ⟂ /speckit.checklist (quality-test the requirements)
/speckit.tasks          →  tasks.md                             (ordered, [P]-parallelizable)
        │   ⟂ /speckit.analyze   (cross-artifact consistency audit, read-only)
        │   ⟂ /speckit.taskstoissues (optional: fan out to GitHub issues)
/speckit.implement      →  working code, task-by-task, marking [X] as it goes
        │
/speckit.converge       →  reconcile code-on-disk with spec; append missing work
```

Commands **hand off** to each other — after `specify`, the agent offers to jump
to `plan` or `clarify`; after `plan`, to `tasks` or `checklist`; and so on. You
can follow the rail or jump around as judgment dictates.

### 3.3 Command-by-command how-to

Each entry: **what it does · when to reach for it · example prompt · what it
emits · senior tips.**

#### `/speckit.constitution`

- **What** — creates/updates the project constitution and keeps dependent
  templates in sync.
- **When** — once at project birth; revisit when a principle genuinely changes
  (rare; version it).
- **Prompt**

  ```text
  # Establish binding principles. Name the values you will NOT compromise,
  # and say how they should arbitrate technical decisions.
  /speckit.constitution Create principles focused on: (1) every behavior change
  ships with a test, (2) AI components are evaluated, not just "tried" — every
  prompt/agent has an eval set and a regression threshold, (3) the human is in
  the loop for any irreversible action, (4) minimal dependencies and idempotent
  file ops, (5) p95 latency budgets per endpoint. Include governance for how
  these gate planning and implementation.
  ```

- **Emits** — `.specify/memory/constitution.md` (with a versioned "Sync Impact"
  header).
- **Tips** — keep it short and *enforceable*. A principle you can't imagine
  failing a plan against is just decoration. Treat edits as semver: principle
  changes are MAJOR.

#### `/speckit.specify`

- **What** — turns a natural-language feature description into a structured
  spec; creates the feature branch and `specs/NNN-*/` directory.
- **When** — the start of every feature.
- **Prompt** — describe **what** and **why**; resist naming the stack.

  ```text
  # Note what's present: actors, flows, rules, edge cases. Note what's absent:
  # frameworks, libraries, schemas. That's deliberate.
  /speckit.specify Build a service that detects and masks personal data (PII)
  in Turkish-language documents before they're shared. A user pastes or uploads
  text; the system highlights detected PII (names, national IDs, IBANs, phones,
  addresses) with a confidence level; a human reviewer can accept, reject, or
  edit each detection; on confirmation the system returns a masked copy plus an
  audit record. Reviewers must never be able to export a document with unresolved
  high-confidence detections.
  ```

- **Emits** — `spec.md` with **user stories**, **functional requirements**,
  **acceptance criteria**, and `[NEEDS CLARIFICATION]` markers where you were
  silent. *(Caption only — learn the shape: numbered stories, testable
  requirements, explicit edge cases.)*
- **Tips** — over-specify the *rules and edge cases*; under-specify the
  *mechanism*. If you catch yourself writing a library name, move it to the plan.

#### `/speckit.clarify`

- **What** — interrogates the spec and asks up to **5 targeted questions** about
  underspecified areas, then encodes your answers back into `spec.md`.
- **When** — immediately after `specify`, *before* `plan`, on anything
  load-bearing. This is the cheapest bug-prevention in the whole pipeline.
- **Prompt**

  ```text
  # Let it drive. Answer crisply; vague answers produce vague specs.
  /speckit.clarify
  ```

- **Emits** — an updated `spec.md` with ambiguities resolved and clarifications
  recorded.
- **Tips** — if it asks something you "obviously" know, that's the point: the
  spec didn't say it, so the implementation would have guessed. Answer it.

#### `/speckit.plan`

- **What** — produces the technical design from the spec and your stack input.
- **When** — once the spec is clarified and you're ready to commit to *how*.
- **Prompt** — *now* you bring the stack and constraints.

  ```text
  # This is where architecture lives. Be specific about stack, boundaries,
  # and the things you've already decided.
  /speckit.plan Build with: FastAPI + Python 3.12 backend, a hybrid PII pipeline
  (deterministic regex/checksum validators for IDs/IBANs + an LLM extractor for
  names/addresses), an LLM-as-judge verification pass, Postgres for audit records,
  and a React + TypeScript review UI with optimistic accept/reject. Stream
  detections to the UI via SSE. Keep the detection engine importable and testable
  independently of the web layer. No PII leaves the boundary unmasked in logs.
  ```

- **Emits** — `plan.md`, plus (as warranted) `research.md` (trade-off studies),
  `data-model.md` (schemas/entities), `contracts/` (API/event contracts), and
  `quickstart.md` (key validation scenarios). *(Caption only.)*
- **Tips** — read `research.md` and `contracts/` like a design doc, because that
  is what they are. This is your cheapest chance to kill a bad abstraction.

#### `/speckit.checklist`

- **What** — generates a **"unit test for your requirements."** It validates the
  *quality* of the spec (completeness, clarity, consistency, coverage) — **not**
  the implementation.
- **When** — after plan, before tasks, on domains where requirement quality is
  the risk (UX, security, compliance, anything fuzzy).
- **Prompt**

  ```text
  # Ask for a domain-scoped checklist. Think "are the requirements well-written?"
  # not "does the button work?"
  /speckit.checklist Generate a requirements-quality checklist for the human
  review UX and the PII-handling rules: are confidence thresholds quantified?
  is every detection category's masking behavior specified? are export-blocking
  conditions unambiguous? are accessibility requirements for the reviewer
  defined?
  ```

- **Emits** — a checklist of questions that probe whether your *spec* is
  airtight. Items like *"Is 'high confidence' quantified?"* — not *"Test that
  masking works."*
- **Tips** — failing checklist items send you back to `specify`/`clarify`, not to
  code. That's the loop working.

#### `/speckit.tasks`

- **What** — decomposes plan + design artifacts into an **ordered, dependency-
  aware `tasks.md`**, marking parallelizable tasks `[P]`.
- **When** — once the plan is settled.
- **Prompt**

  ```text
  /speckit.tasks Break the plan into tasks
  ```

- **Emits** — `tasks.md`: setup → foundational → per-story → polish, each task
  small and testable, with `[P]` on independent ones. *(Caption only — note the
  phasing; you'll scope `implement` against it.)*
- **Tips** — skim for tasks that are too big to verify; a task you can't write a
  test for is a task that's underspecified upstream.

#### `/speckit.analyze`

- **What** — a **non-destructive, read-only** cross-artifact audit. Checks
  `spec.md`, `plan.md`, and `tasks.md` for inconsistencies, gaps, and drift.
- **When** — after tasks, before implement; and any time you suspect artifacts
  have diverged.
- **Prompt**

  ```text
  /speckit.analyze Run a project analysis for consistency
  ```

- **Emits** — a report of mismatches (e.g., a requirement with no task, a task
  with no requirement, a contract the plan never mentions). It **changes
  nothing**; you decide the fixes.
- **Tips** — treat a clean `analyze` as your "ready to implement" gate.

#### `/speckit.taskstoissues` *(optional)*

- **What** — converts `tasks.md` into dependency-ordered **GitHub issues**.
- **When** — when work is shared across a team or you want the backlog tracked in
  GitHub rather than a file.
- **Prompt**

  ```text
  /speckit.taskstoissues Create GitHub issues from the tasks, preserving order
  and dependencies, labeled by phase.
  ```

- **Emits** — GitHub issues (via the GitHub MCP server) mirroring your task DAG.
- **Tips** — great for human/AI hand-offs: a teammate or another agent can pick up
  an issue with full spec context linked.

#### `/speckit.implement`

- **What** — executes `tasks.md`, building the code task-by-task and marking each
  `[X]` as it completes.
- **When** — after a clean analyze. This is the generation step.
- **Prompt** — and critically, **how to scope it** (see §3.5).

  ```text
  # Full run for small features:
  /speckit.implement Start the implementation in phases

  # Scoped run for large ones (recommended — keeps context healthy):
  /speckit.implement only execute the Setup and Foundational phases, then stop
  and report progress
  ```

- **Emits** — working code, committed task-by-task; `tasks.md` updated with `[X]`.
- **Tips** — review *per phase*, not at the end. The completed-task markers mean
  you can stop, review, and resume without losing your place.

#### `/speckit.converge`

- **What** — assesses **code-on-disk against spec/plan/tasks**, then **appends
  the remaining unbuilt work** as new tasks so `implement` can finish it.
- **When** — brownfield reality checks; after manual edits; when a long
  implementation drifted; whenever "what's actually built?" ≠ "what we said."
- **Prompt**

  ```text
  /speckit.converge Assess the codebase against the spec and append any missing
  work as tasks.
  ```

- **Emits** — newly appended tasks in `tasks.md` capturing the delta between
  intent and reality. Then you re-run `implement`.
- **Tips** — this is the *spec-evolution* workhorse. Change the spec, run
  `converge`, run `implement` — that's how a living spec stays load-bearing.

### 3.4 Extensions, presets, and bundles

Spec Kit is customizable so it can match *your* lifecycle, not just the default.

- **Extensions** — opt-in command packs that hook into the pipeline. Built-ins
  include:
  - **`git`** — commit/validate/feature/remote helpers so SDD phases map cleanly
    to branches and commits.
  - **`bug`** — `assess` → `test` → `fix`: a spec-driven *bug* workflow (reproduce
    with a failing test first, then fix).
  - **`agent-context`** — keeps the agent's working context updated as the project
    grows.
  - Extensions hook at defined points (`before_specify`, `before_plan`, …) via
    `.specify/extensions.yml`.
- **Presets** — alternative command/template sets. **`lean`** trims the pipeline
  for speed; **`scaffold`** is a starting point for authoring your own; the
  templates are yours to fork.
- **Bundles** — role-based setups: **developer**, **product-manager**,
  **business-analyst**, **security-researcher**. A bundle pre-wires the commands
  and emphasis a given role needs.

> Senior framing: extensions/presets/bundles are how you **encode your team's
> SDLC into the tool**. The default pipeline is a strong opinion; these let you
> make it *your* opinion.

### 3.5 Handling complex features (the context problem)

Big features sail through specify/plan/tasks and then **degrade mid-
`implement`** — the agent loses the plan, skips tasks, or hallucinates as the
context window fills and compaction kicks in. The root cause is context
exhaustion, and there are four fixes:

```text
# 1) Scope each run — the simplest fix, works on any agent:
/speckit.implement only execute tasks T001-T010, then stop and report progress

# 2) Delegate to sub-agents (if your agent supports them):
/speckit.implement delegate each parallel [P] task to a sub-agent

# 3) Combine scoping + delegation for very large features:
/speckit.implement execute only the Core phase, delegate [P] tasks to sub-agents

# 4) Decompose into smaller specs ("spec of specs") — when even one phase is
#    too big, split the feature into sub-features, each with its own
#    spec/plan/tasks cycle. Highest overhead; reserve for genuinely huge work.
```

Because completed tasks are marked `[X]`, scoped runs resume cleanly. **Default
to option 1**; reach for sub-agents when you want parallelism; decompose only
when a single phase still overflows.

---

## Part IV — End-to-End: t0 to a Shipped Product

> **The cast.** Deniz, a senior AI engineer, is shipping **Redaktör** — an
> agentic Turkish-document **PII detection & masking** service with a
> **human-in-the-loop review UI**. It's representative of real agentic-product
> work: non-deterministic model components, an eval discipline, a human approval
> step, and a frontend that has to feel trustworthy.
>
> Watch for the **load-bearing moves** (⚖️) — the moments where SDD does real
> work a senior refuses to skip. The point isn't the product; it's the *operating
> discipline*.

### t0 — Frame the problem before touching the tool

Deniz doesn't open the agent first. He writes three sentences in a notebook:
*who hurts today, what "done" means, what must never happen.* For Redaktör:
"Compliance teams manually redact Turkish docs; done = reviewer-approved masked
copy + audit trail; **never** export a doc with unresolved high-confidence PII."

⚖️ **Load-bearing move:** the spec is only as good as the intent behind it. Five
minutes of human framing prevents an hour of regenerating a confidently-wrong
spec.

### Phase 1 — Bootstrap & constitution

```bash
specify init redaktor --integration claude
cd redaktor
```

Then, before any feature, he encodes the **values that arbitrate every later
decision** — and for an AI product, that explicitly includes *evals* and
*human-in-the-loop*:

```text
# The constitution is where an AI product's hardest invariants become gates.
/speckit.constitution Create binding principles: (1) every behavior change ships
with a test; (2) NON-NEGOTIABLE — every AI component (extractor, judge) has a
versioned eval set with a regression threshold; promotion requires passing it;
(3) the human reviewer is the final authority — no irreversible export without
explicit approval; (4) PII never appears in logs, traces, or error messages;
(5) the detection engine is a library, importable and testable without the web
layer; (6) p95 detection latency budget: 2s for a 2-page document. Add governance:
plans that violate these must fail the gate or carry a written, justified
exception.
```

⚖️ **Load-bearing move:** principle (2) turns "we tried the prompt and it seemed
fine" into a *gate*. Principle (4) will later cause `analyze` and review to flag
any logging task that touches raw text. The constitution is doing architecture.

### Phase 2 — Specify the *what*, ruthlessly stack-free

```text
# Actors, flows, rules, edge cases. Zero frameworks. Zero model names.
/speckit.specify Build a service that detects and masks personal data in
Turkish-language documents before sharing. A reviewer pastes or uploads text;
the system streams back detected PII (full names, T.C. national IDs, IBANs,
phone numbers, postal addresses) each with a category and a confidence level;
the reviewer accepts, rejects, or edits each detection inline; on confirmation
the system returns a masked copy and writes an immutable audit record (who,
when, what changed). Hard rule: the system must block export while any
high-confidence detection is unresolved. Documents may be up to 20 pages.
```

The agent creates branch `001-pii-masking` and `specs/001-pii-masking/spec.md`
with user stories, functional requirements, acceptance criteria — and a few
`[NEEDS CLARIFICATION]` markers where Deniz was silent.

> *(Caption of `spec.md`, not its contents:)* §User Stories (reviewer-centric),
> §Functional Requirements (FR-1 detect, FR-2 stream w/ confidence, FR-3 inline
> resolve, FR-4 export-block rule, FR-5 audit), §Edge Cases (empty doc, all-PII
> doc, mixed-language doc), §`[NEEDS CLARIFICATION]` on retention + masking
> format.

⚖️ **Load-bearing move:** Deniz *notices* he never said how masking should look
(`[ALİ YILMAZ]` → `[AD-SOYAD]`? black box? partial?) — but he doesn't fix it by
editing prose. He lets `clarify` extract it, so the resolution is recorded
systematically.

### Phase 3 — Clarify: spend questions now, not bugs later

```text
/speckit.clarify
```

The agent asks five sharp questions. Deniz answers crisply:

```text
# (paraphrased Q→A — answers get encoded back into spec.md)
Q: Confidence threshold for "high"?        → ≥ 0.85 blocks export; 0.6–0.85 warns.
Q: Masking representation?                 → category tokens, e.g. [TCKN], [IBAN].
Q: Retention of original text?             → originals purged after audit write;
                                             audit stores only masked + diff.
Q: Multi-language docs?                    → detect TR PII only; flag non-TR spans.
Q: Who can override an export block?       → nobody in v1; it's a hard stop.
```

⚖️ **Load-bearing move:** "nobody can override the export block" is now a
*requirement with a test target*, not a tribal assumption. This single
clarification will shape a contract, a task, and a regression test downstream.

### Phase 4 — Plan: now, and only now, the architecture

```text
# Stack, boundaries, and the decisions already made enter here.
/speckit.plan Build with: FastAPI + Python 3.12; a HYBRID detection pipeline —
deterministic validators (regex + checksum) for T.C. IDs/IBANs/phones, and an
LLM extractor for names/addresses; an LLM-as-judge pass that scores each
candidate and assigns confidence; Postgres for immutable audit records; React +
TypeScript review UI with optimistic accept/reject and SSE streaming of
detections. Keep `redaktor.engine` importable and web-independent. Structured
logging with a redaction filter so raw text can never be logged. Provide an eval
harness (golden Turkish docs with labeled PII) for both extractor and judge.
```

> *(Caption of emitted design artifacts:)*
>
> - `research.md` — trade study: regex-only vs. LLM-only vs. **hybrid** (chosen:
>   hybrid for precision on structured IDs + recall on names); SSE vs.
>   WebSocket (chosen: SSE, one-way stream).
> - `data-model.md` — entities: `Document`, `Detection{category, span,
>   confidence, status}`, `AuditRecord`.
> - `contracts/` — `POST /documents`, `GET /documents/{id}/detections` (SSE),
>   `POST /detections/{id}/resolve`, `POST /documents/{id}/export` (enforces the
>   block rule).
> - `quickstart.md` — the golden-path validation scenario.

⚖️ **Load-bearing move:** Deniz reads `research.md` and pushes back: the judge
adds latency. He keeps it but adds a plan note — *deterministic validators
short-circuit the judge for checksum-valid IDs* — protecting the 2s p95 budget
from principle (6). This is a design debate happening in `plan.md`, where it's
free.

### Phase 5 — Checklist the requirements, then task it out

Because the **review UX** and **PII rules** are the real risk, he quality-tests
the *requirements* first:

```text
/speckit.checklist Generate a requirements-quality checklist for the review UX
and PII rules: is every detection category's masking token specified? is the
export-block condition unambiguous and testable? are reviewer keyboard/a11y
requirements defined? is the SSE reconnect behavior on dropped connection
specified?
```

Two items fail — SSE reconnect behavior and a11y were never specified. He loops
back through `clarify` to fix the *spec*, not the code. Then:

```text
/speckit.tasks Break the plan into tasks
```

> *(Caption of `tasks.md`:)* Setup (repo, CI, db) → Foundational (engine library,
> validators, eval harness) → Story A (detect+stream) → Story B (resolve UI) →
> Story C (export-block + audit) → Polish (a11y, latency, observability). `[P]`
> on the independent validator and UI-component tasks.

### Phase 6 — Analyze: the "ready to build" gate

```text
/speckit.analyze Run a project analysis for consistency
```

The read-only audit flags one real gap: **no task covers the "non-TR span"
flagging** from the clarify step. Deniz adds it (re-runs `tasks`), re-analyzes,
gets a clean report.

⚖️ **Load-bearing move:** a clean `analyze` is his hard gate to implementation. A
requirement with no task is a feature that silently won't exist — caught here for
the price of a re-read.

### Phase 7 — Implement, scoped by phase

He never one-shots a feature this size. He scopes by phase to keep context
healthy (§3.5):

```text
# 1) Foundation first — the engine + evals must exist before stories.
/speckit.implement only execute the Setup and Foundational phases, then stop and
report progress

# (Deniz reviews: runs the eval harness, confirms validators pass on golden IDs.)

# 2) Then story by story, reviewing each:
/speckit.implement execute Story A (detect + stream), then stop

# 3) Large parallelizable polish — delegate if the agent supports sub-agents:
/speckit.implement execute the Polish phase, delegate [P] tasks to sub-agents
```

Each task lands as `[X]`. Between phases, Deniz **runs the app and the evals**,
not just the unit tests — because for an AI component, "tests pass" ≠ "it
detects well." The eval set from principle (2) is the real acceptance gate.

⚖️ **Load-bearing move:** reviewing per phase means a bad masking decision is
caught after Story A, not after the whole product is wired. The `[X]` markers let
him stop and resume without losing the thread.

### Phase 8 — Converge: reconcile reality with intent

Mid-build, product asks for one change: *warn-level detections (0.6–0.85) should
also be reviewable, not just high-confidence ones.* Deniz does the
**spec-evolution loop**, not a hand-patch:

```text
# 1) Update the spec/clarify with the new rule, then:
/speckit.converge Assess the codebase against the updated spec and append any
missing work as tasks.

# 2) converge appends the delta tasks (UI filter for warn-level, export rule
#    stays high-confidence-only). Then finish them:
/speckit.implement execute the newly appended tasks
```

⚖️ **Load-bearing move:** the requirement change entered through the *spec* and
propagated *down* — not as a stray commit. The spec stays the source of truth, so
the next engineer (or agent) reads intent that matches reality.

### Phase 9 — Ship: CI, audit, and the human gate

Before release, Deniz wires the lifecycle closure (often via the `git` extension
and his CI):

- **CI gates** run the test suite *and* the eval suite; a regression below the
  eval threshold **fails the build** (principle 2, now load-bearing in CI).
- **A redaction-filter test** asserts no raw PII reaches logs (principle 4).
- **An export-block test** asserts the hard stop from the clarify step.
- He has the agent fan remaining work to issues for a teammate:

  ```text
  /speckit.taskstoissues Create GitHub issues for the remaining polish tasks,
  preserving dependency order, labeled by phase.
  ```

Redaktör ships: a reviewer pastes a document, watches detections stream in with
confidence, resolves each inline, and exports a masked copy with an audit trail —
and **cannot** export while a high-confidence detection is unresolved, because
that rule has been load-bearing since Phase 3.

### What made this "senior," in one breath

The model wrote most of the code. **Deniz owned the leverage points**: framing
intent (t0), promoting invariants to gates (constitution), spending clarify
questions early, debating architecture in `plan.md`, gating on a clean `analyze`,
reviewing *per phase* against **evals** not vibes, and routing every change
through the spec via `converge`. SDD didn't replace his judgment — it
*concentrated* it where it mattered.

---

## Part V — Operating SDD Like a Senior

### 5.1 Habits that separate load-bearing SDD from theater

- **Always `clarify` before `plan`** on anything that matters. It's the highest
  ROI command in the kit.
- **Read `research.md` and `contracts/`.** If you're not reviewing the design
  artifacts, you're vibe coding with extra files.
- **Gate on a clean `analyze`.** Make "no orphan requirements, no orphan tasks"
  your definition of implementation-ready.
- **Scope `implement` by phase, review between phases.** Don't discover problems
  at the end.
- **Route changes through the spec → `converge` → `implement`.** Hand-patches rot
  the spec; once it's stale, it stops being load-bearing and you're back to
  code-as-truth.

### 5.2 Anti-patterns to refuse

- **Stack in the spec.** Frameworks in `spec.md` poison the intent layer and
  block re-implementation.
- **Skipping clarify to "save time."** You don't save it; you move it to
  debugging, at 10× the cost.
- **One-shot `implement` on a big feature.** Context exhaustion will corrupt the
  back half of the run.
- **A constitution of platitudes.** If a principle can't fail a plan, delete it.
- **Treating generated artifacts as write-once.** A spec you never regenerate
  from is documentation, not SDD.

### 5.3 Fitting SDD to a team

- Use **`taskstoissues`** to turn a task DAG into a shared backlog; each issue
  carries spec context, so humans and agents can both pick up work.
- Use **bundles** (developer / PM / BA / security) so each role gets the
  pipeline emphasis they need.
- Use **extensions** (`git`, `bug`, `agent-context`) to bind SDD phases to your
  real branch/commit/triage flow.
- Keep `spec.md`/`plan.md`/`tasks.md` **in version control** next to the code and
  review them in PRs — the spec diff *is* the design review.

### 5.4 When **not** to reach for the full pipeline

SDD ceremony should match stakes:

| Situation | Reach for |
| --- | --- |
| Load-bearing feature, multiple stories, real risk | Full pipeline + clarify + checklist + analyze |
| Small, well-understood change | specify → plan → tasks → implement (skip the wrappers) |
| Throwaway spike / proof of concept | Straight to `/speckit.implement` with a tight prompt |
| Bug fix | The `bug` extension (assess → failing test → fix) |
| Requirements changed on a live feature | `clarify`/edit spec → `converge` → `implement` |

The senior skill is calibration: enough structure to stay honest, not so much
that it's theater.

### 5.5 The one-sentence summary

**Make intent the durable artifact, promote your invariants to gates, spend your
judgment at the spec/plan/analyze checkpoints, and let the agent regenerate the
code — so that when the world changes, you change the spec and the system
follows.**

---

## Appendix — Cheat Sheets

### A. Command map

| Command | Phase | Emits | Reach for it when |
| --- | --- | --- | --- |
| `/speckit.constitution` | Govern | `constitution.md` | Project birth; principle change |
| `/speckit.specify` | Intent | `spec.md` (+ branch) | Every new feature |
| `/speckit.clarify` | Intent | updated `spec.md` | Before planning anything load-bearing |
| `/speckit.plan` | Design | `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md` | Spec is clarified |
| `/speckit.checklist` | Design | requirements-quality checklist | Fuzzy/high-risk domains (UX, security) |
| `/speckit.tasks` | Decompose | `tasks.md` | Plan is settled |
| `/speckit.analyze` | Gate | read-only consistency report | Before implement; on suspected drift |
| `/speckit.taskstoissues` | Decompose | GitHub issues | Team/shared backlog |
| `/speckit.implement` | Build | code + `[X]` tasks | After a clean analyze |
| `/speckit.converge` | Evolve | appended delta tasks | Spec changed; brownfield reconcile |

### B. Artifact graph

```text
constitution.md ──governs──▶ spec.md ──derives──▶ plan.md ─┬─▶ research.md
                                  ▲                          ├─▶ data-model.md
                            clarify│ checklist               ├─▶ contracts/
                                  │                          └─▶ quickstart.md
                                  │                                  │
                                  └────────── analyze (audits all) ──┤
                                                                     ▼
                                                                 tasks.md ──▶ code
                                                                     ▲          │
                                                                     └ converge ┘
```

### C. Glossary

- **Constitution** — binding project principles, enforced as plan-time gates.
- **Gate (Phase −1)** — a pre-implementation check (simplicity, anti-abstraction,
  integration-first) a plan must pass or explicitly waive.
- **`[NEEDS CLARIFICATION]`** — an explicit uncertainty marker; a question, not a
  guess.
- **Persistence model** — your chosen strategy for keeping specs alive
  (greenfield / brownfield / evolution).
- **`[P]` task** — a task with no blocking dependency; parallelizable.
- **Converge** — reconcile code-on-disk with intent by appending the missing
  work as tasks.
- **Bundle / Preset / Extension** — role setups / alternative pipelines / opt-in
  command packs that tailor Spec Kit to your SDLC.

---

*Further reading in this repo: [`spec-driven.md`](../../spec-driven.md) (the
full SDD essay and the constitutional articles),
[`docs/concepts/sdd.md`](../concepts/sdd.md),
[`docs/concepts/complex-features.md`](../concepts/complex-features.md), and
[`docs/guides/evolving-specs.md`](./evolving-specs.md).*
