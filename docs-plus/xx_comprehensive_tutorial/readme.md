# The AI-First Engineering Playbook (2025)

**A single, comprehensive tutorial to design, build, and maintain agentic software—prompt-first, test-guarded, and production-ready.**

> Goal: you will create and sustain real AI agents and services using **Prompt-Driven Development (PDD)** + **TDD** + **ADRs** + **PRs**, powered by **Cursor** (AI-first IDE), optionally **VS Code + GPT-5 Codex**, **uv** (Python deps), the **OpenAI Agents SDK**, and a **Prompt History** discipline. The entire method favors prompts over hand-coding, with small, verifiable steps.

---

## 0) Glossary (read this once)

* **PDD (Prompt-Driven Development):** A method where you build in **tiny, sequenced prompts**. The AI writes the code; you write the intent (acceptance criteria, constraints, and out-of-scope).
* **Vibe coding:** Unstructured exploratory prompting. Great for spikes; bad for long-lived systems.
* **TDD (Test-Driven Development):** **Red → Green → Refactor**. Write failing tests first; make the smallest change to pass; then clean up.
* **ADR (Architecture Decision Record):** A short doc that records a significant decision: context → options → decision → consequences.
* **PR (Pull Request):** The social + technical gate for merging: small scope, tests, ADR links, CI green → merge.
* **PHR (Prompt History Record):** A numbered **prompt file** that captures the exact prompt used, its scope/constraints, and the outcome. They sit beside ADRs for traceability.
* **Agents SDK (OpenAI):** Minimal building blocks for agentic apps—**agents**, **tools**, **sessions**, **handoffs**, **guardrails**, **tracing**.
* **Cursor:** AI-first IDE (VS Code-like) with repo-aware chat, multi-file “Composer,” and inline completions.
* **GPT-5 Codex (optional companion):** OpenAI’s cloud/CLI/IDE agent for repo-wide edits, PRs, and parallel tasks.
* **uv:** Fast Python package manager & environment tool (lockfile + reproducibility).
* **SSE:** Server-Sent Events—simple HTTP streaming for token-by-token responses.

---

## 1) System Overview (what you’re building)

A production-grade **chatbot/agent service** with:

* A **FastAPI** backend (healthcheck, `/chat` non-streaming + **SSE** streaming).
* A **CustomerAgent** (default) with **tools** (e.g., `calculator`, `now`), **guardrails** (Pydantic output), and **sessions**.
* A **ResearchAgent** and **handoff** logic for specialized queries.
* **Tests** (unit + contract), **ADR/PHR** history, **CI**, **Docker** (uv-based), **tracing**, and a clear **PR** policy.

Everything is produced by **prompts**. You’ll read and explain generated code—but you won’t hand-write it.

---

## 2) Architecture at a Glance (suggested diagrams)

Include these diagrams (in `docs/diagrams/`):

1. **Context Diagram** — Clients → API (FastAPI) → Agents SDK → Tools.
2. **Runtime Sequence** — `/chat` request → session lookup → CustomerAgent → (optional) handoff → streaming → guardrail check → response.
3. **Agent Collaboration** — Handoff policy (when/how) and trace spans.
4. **Deployment** — Dev (Cursor), CI (lint/test/build), Registry, Runtime (Docker), Observability.
5. **Data Contracts** — JSON schemas for requests/responses; `ChatReply` structure.
6. **Decision Map** — ADR links to components (streaming choice, handoff strategy, guardrails, Docker strategy).

---

## 3) Dual Environment Setup (fast, repeatable)

Use **both** environments for best results:

### A) Cursor (AI-first IDE)

1. Install and sign in.
2. Settings → **Models**: choose your top coding model (GPT-5 class).
3. Add **Workspace Rules** (see §4).
4. Import standard extensions (Python, Docker, Git).
5. Create a repo folder and open it.

### B) VS Code + GPT-5 Codex (optional but powerful)

* Install VS Code + Codex extension; sign in to GPT-5.
* Use Codex for **repo-wide** tasks (big refactors, multi-branch PRs), while Cursor handles **short, iterative edits** with inline completions.
* Keep the repo git-synced to bounce between tools.

---

## 4) Project “House Rules” (copy into `docs/rules.md` **and** Cursor Rules)

* **Language/Deps:** Python 3.12+, **uv** for envs/locks.
* **Framework/SDK:** FastAPI, Pydantic; **OpenAI Agents SDK** for agent logic.
* **Quality:** pytest; **mock external calls**; ruff; coverage ≥ 80%; deterministic CI.
* **Security:** no secrets in code; `.env.sample`; sanitize logs.
* **Prompts:** PDD baby steps; **PHR files for every step**; “smallest diff”; no unrelated refactors.
* **Docs:** README must include `uv` run commands; ADR for significant choices; explain generated code succinctly.
* **PR Gate:** small scope, tests passing, ADR links when interfaces/deps change; **no green, no merge**.

---

## 5) Repository Skeleton (one-and-done prompt to Cursor/Composer)

**Prompt (Composer):**

```
Scaffold a Python service using uv and the OpenAI Agents SDK:

- pyproject.toml + uv.lock
- app/main.py (FastAPI + GET /healthz stub)
- app/agents/core.py (CustomerAgent factory, get_runner(), Sessions enabled)
- app/agents/tools.py (function_tool: calculator(expression), now(tz?))
- app/agents/customer.py (instructions; defer to tools)
- app/agents/research.py (ResearchAgent; stubs for handoff)
- app/guards/schemas.py (Pydantic ChatReply {text, used_tool?, handoff})
- app/guards/rules.py (length limit; simple validation)
- app/config.py (.env loading w/ defaults)
- tests/ (healthz, chat contract skeletons)
- docs/adr/0000-template.md, docs/prompts/0000-template.prompt.md
- .env.sample, .gitignore, .dockerignore
- Makefile (setup/test/run/lint/coverage)
- .github/workflows/ci.yml (ruff, pytest, coverage, docker build)
- README with uv commands, curl examples
```

> After Cursor generates files, **create your first PHR** (`docs/prompts/0001-setup-architect.prompt.md`) with the exact prompt and outcome.

---

## 6) Prompt-Driven Development (PDD) × TDD: the 7-step loop

**Always** work in **baby steps**, each recorded as PHRs:

1. **Plan (Architect Prompt)**
2. **Red (tests-only)**
3. **Green (minimal diff)**
4. **Refactor (keep tests green)**
5. **Explain (8-bullet diff summary)**
6. **Record (ADR if decision)**
7. **Share (PR; CI must pass)**

### 6.1 Example: Healthcheck (tiny slice)

**PHR-A (Architect):**

```
Goal: GET /healthz returns {"status":"ok"}; add tests and README curl.
Constraints: minimal diff; no new deps.
Out of scope: auth, DB.
```

**PHR-B (Red):**

```
Add tests/test_healthz.py::test_healthz_ok expecting {"status":"ok"}.
No production code changes.
```

**PHR-C (Green):**

```
Implement GET /healthz to pass tests; update README with a curl example.
Output: diff-only; no refactors.
```

**Commit, PR:** title “/healthz endpoint + tests”; link PHR-A..C.

---

## 7) Build the Chat API with Streaming and Handoffs

### 7.1 `/chat` Non-Streaming (contracts first)

**PHR-D (Architect):**

```
POST /chat {session_id, user_message} → returns JSON ChatReply {text, used_tool?, handoff:boolean}
Errors: 400 if missing user_message. Tool use shown in response.
Constraints: minimal diff; keep offline tests.
```

**PHR-E (Red):** failing tests (200 happy path; 400 missing field).
**PHR-F (Green):** minimal implementation using Agents SDK Runner; **Sessions** keyed by `session_id`.
**PHR-G (Explainer):** ask Cursor for an 8-bullet summary.
**ADR:** none yet (no broad decision).

### 7.2 Add **SSE** Streaming (with an ADR)

**PHR-H (Architect):**

```
Add streaming to /chat using SSE when Accept: text/event-stream; fallback JSON otherwise.
Tests: SSE headers and event format; JSON fallback still passes.
Constraints: minimal diff; no new deps.
```

**PHR-I (Red):** failing SSE tests.
**PHR-J (Green):** add streaming pipeline; keep non-streaming stable.
**ADR-0002:** *“Streaming Protocol Choice (SSE vs WS vs Polling)”*—context, options, decision, consequences.
**PR:** link PHR-H..J and ADR-0002.

### 7.3 Tools and Guardrails

**PHR-K (Architect):**

```
Add function tools:
- calculator(expression:str) -> str (safe eval or simple parser)
- now(tz?:str) -> str (ISO timestamp; default UTC)
Expose tool usage in ChatReply.used_tool.
Add guardrail: ChatReply schema; length <=1200 chars; single retry on validation fail.
```

**PHR-L (Red):** tests for tool visibility and guardrail fail/retry.
**PHR-M (Green):** implement tools; enforce `output_type=ChatReply`; add retry; keep tests offline.
**ADR-0004:** “Output Shape & Limits” (why these constraints).

### 7.4 Handoffs (CustomerAgent → ResearchAgent)

**PHR-N (Architect):**

```
Introduce ResearchAgent; handoff when intent=RESEARCH (confidence >=0.7).
Log handoff_reason; surface handoff flag in response.
```

**PHR-O (Red):** failing tests for classifier threshold and `handoff_reason` presence.
**PHR-P (Green):** minimal classification + handoff; maintain sessions.
**ADR-0003:** “Handoff Strategy & Thresholds.”

---

## 8) Observability & Tracing

**PHR-Q (Architect):**

```
Instrument tracing: spans for tool calls and handoffs; add docs/observability.md (enable, view, filter).
Keep tests offline—mock tracing backends.
```

**PHR-R (Red/Green):** add mocks, then minimal hooks.
**Explainer:** bullet summary of spans and sampling choices.

---

## 9) Docker & CI

**PHR-S (Architect):**

```
Create a uv-based multi-stage Dockerfile:
- build: uv sync; run tests
- final: copy app + env; uv run uvicorn app.main:app
Add make docker-build/run; document image size and security basics.
```

**PHR-T (Green):** implement file + .dockerignore; CI builds image.
**ADR-0005:** “Docker Strategy (uv / multi-stage).”
**PR policy doc:** “no green, no merge,” coverage gate, ADR links for interface/dep changes.

---

## 10) Prompt History Program (PHR) — treat prompts as artifacts

* Create `docs/prompts/NNNN-<slug>-<stage>.prompt.md` for every step: **architect, red, green, refactor, explainer, adr-draft, pr-draft**.
* Each file includes **front-matter** (id, date, model, scope\_files, acceptance, constraints, out\_of\_scope) and the **exact prompt text**.
* Append an **Outcome** section (files changed, tests added, next prompts).
* Link PHR IDs in commits/PRs and ADRs.
* (Optional) Use the **Prompt History Kit** (templates, Makefile, git hooks) to automate IDs and indexing.

---

## 11) Using Cursor (practical workflow)

* **Inline** for micro-edits (comments as intent → Tab to accept).
* **Chat** for explanations and quick investigations (“Explain data flow from X to Y, two bullets per file”).
* **Composer** for slices that touch multiple files—**write prompts like GitHub Issues**: paths, acceptance tests, constraints, out-of-scope, and expected diff.

**Best practices (from OpenAI teams):**

* **Ask Mode → Code Mode:** plan first, then implement from the plan.
* **Harden the environment:** scripts for setup/tests; explicit env vars; mocks; fix root causes.
* **Small queued tasks:** use a backlog (Composer tasks) instead of mega-prompts.

---

## 12) Using GPT-5 Codex (optional companion)

* Prefer **Cloud** for big, parallel repo tasks (wide refactors, multi-PR changes).
* Prefer **CLI/IDE** for local edits with fast feedback.
* Keep prompts shaped like **Issues/PRs**; enforce PDD×TDD; open PRs with ADR links.

---

## 13) Governance: PRs, ADRs, and Policy

* **PR template** includes: problem/solution, screenshots or curl, test plan, risks/rollback, linked ADRs/PHRs.
* **ADR discipline**: write one when public APIs change, deps shift, performance/security matters, or you choose among architectural options.
* **Policy defaults:** “smallest diff,” coverage gate, deterministic tests, **no green, no merge**.

---

## 14) Quality Signals & Metrics

* **Lead time** (hours per small PR)
* **Change failure rate** (rollback/hotfix %)
* **MTTR** (time to recover)
* **Coverage + contract tests** (spec clarity)
* **ADR density** (documented decisions / significant changes)
* **AI utilization** (prompts per merged PR; % diffs generated by AI)

Track these in CI dashboards; review monthly.

---

## 15) Security, Privacy, and Compliance

* Never paste secrets into prompts; use `.env` references.
* Sanitize logs and traces; use synthetic data in tests.
* License respect: cite the origin of any copied snippet in PR/PHR; prefer first-party generation.

---

## 16) Troubleshooting & Anti-Patterns

* **Scope creep:** split into smaller PHRs; one vertical slice per PR.
* **Over-refactor:** enforce “diff-only to pass tests”; reserve refactor for its own step.
* **Flaky CI:** mock network/time; stabilize fixtures; pin seeds.
* **Prompt drift:** restate acceptance criteria and **out-of-scope** explicitly; link prior PHRs for context.
* **Opaque decisions:** if you argued about it, **write an ADR**.

---

## 17) “All the Prompts You Need” (copy/paste catalog)

### Architect (micro-spec)

```
Design <feature> as a minimal slice.
- Files to touch (paths)
- API shape & payloads
- Given/When/Then acceptance tests
- Risks & rollback
Output: plan + diff outline; no code yet.
```

### Red (tests only)

```
Add failing tests for <behavior> including edge/negative cases.
No production code changes. Minimal diff. Offline with mocks.
```

### Green (minimal change)

```
Make the smallest change necessary to pass tests/<path>::<test>.
No unrelated refactors. No new deps. Output diff-only.
```

### Refactor (safe)

```
Refactor internals for clarity/performance; preserve public APIs/behavior.
All tests remain green. Summarize changes in 5 bullets.
```

### Explainer

```
Explain the diff in 8 bullets, flag risks, and list follow-ups (if any).
```

### ADR (why this way)

```
Create ADR <id-title> with Context, Options (pros/cons), Decision, Consequences, References.
Link related PR and PHR IDs.
```

### PR (review gate)

```
Draft a PR:
- Title + summary (problem/solution)
- Test plan (commands, fixtures)
- Screenshots/curl
- Risks & rollback
- Links: ADR(s), PHR(s), issue(s)
Scope small; CI must pass.
```

---

## 18) Putting It All Together (suggested first milestone)

**Milestone: “MVP Chat” (2–4 hours, all prompts)**

1. Healthcheck (architect, red, green) → PR #1.
2. `/chat` non-streaming (architect, red, green, explainer) → PR #2.
3. SSE streaming (architect, red, green) + **ADR-0002** → PR #3.
4. Tools + guardrails (architect, red, green) + **ADR-0004** → PR #4.
5. Handoffs (architect, red, green) + **ADR-0003** → PR #5.
6. Tracing hooks + docs → PR #6.
7. Docker + CI + PR policy + **ADR-0005** → PR #7.

Every step has PHR files, a tiny diff, tests, and a passing CI.

---

## 19) Maintenance & Evolution

* Add **RAG/Knowledge** tools later (vector store + retrieval tool).
* Introduce **WebSocket** streaming if bi-directionality is needed—document in an ADR and migrate with contract tests.
* Expand the **Prompt Cookbook** from your PHRs—promote great prompts to reusable templates.

---

### Final Word

2025 is the year AI development went **mainstream and professional**. The edge isn’t “using AI”; it’s **operationalizing** AI: **PDD** to steer, **TDD** to verify, **ADRs** to explain, and **PRs** to gate. Pair that with a dual setup (Cursor for flow, Codex for scale), a repeatable repo pattern (uv + FastAPI + Agents SDK), and a **Prompt History** discipline. You’ll ship faster—and you’ll actually want to maintain what you shipped.

If you want, I can also drop a **starter repo** (folders, templates, Makefile, hooks) or add a **diagram stubs pack** to your canvas so you can print and annotate with your team.

## Starter Repo Version 1

Here’s your **starter repo** with folders, templates, Makefile, and Git hooks bundled up:

* Download: ai-agent-playbook-starter1.zip

### What’s inside

* `app/` — minimal FastAPI app (`/healthz`) to validate the loop
* `tests/` — starter test for `/healthz`
* `docs/adr/0000-template.md` — ADR template
* `docs/prompts/0000-template.prompt.md` — Prompt History Record (PHR) template
* `docs/diagrams/` — Mermaid stubs (context, sequence, contracts, deployment)
* `scripts/` — `prompt_new.py`, `prompt_index.py`, `prompt_guard.py`
* `.githooks/` — `pre-commit` + `commit-msg` to nudge PHR discipline
* `.github/workflows/ci.yml` — lint + test CI stub
* `Makefile` — `prompt-new`, `prompt-index`, `prompt-guard` + dev targets
* `README.md` — quick start & structure

### Quick start

```bash
unzip ai-agent-playbook-starter.zip && cd ai-agent-playbook-starter
git init
git config core.hooksPath .githooks
chmod +x .githooks/* scripts/*.py

# (Use uv or pip — your call)
python -m venv .venv && source .venv/bin/activate
pip install --upgrade pip && pip install fastapi "uvicorn[standard]" pydantic python-dotenv httpx pytest ruff

# Try the first PHR flow
make prompt-new SLUG=setup STAGE=architect
make prompt-index
pytest -q
```

## Starter Repo Version 2 Update

Now I also want to also add a uv multi-stage Dockerfile and a PR template prewired with ADR/PHR sections to this repo.

Your starter repo now includes a **uv-based multi-stage Dockerfile** and a **PR template** wired for PHR/ADR discipline.

* Download updated ai-agent-playbook-starter2.zip

### What I added

* `Dockerfile` — multi-stage build using **uv** in the builder image, slim runtime, non-root user, healthcheck, and `uvicorn` entrypoint.
* `.github/PULL_REQUEST_TEMPLATE.md` — prompts you to link **PHR** files and **ADR**s, include a **test plan**, and capture **risks/rollback**.
* `README.md` — appended a quick **Docker** build/run snippet.

## Starter Repo Version 3 Update

Now I want to also drop placeholder red tests for /chat and SSE so your first two PDD iterations start with failing tests out of the box.

Added the **red tests** and updated the package. You’re ready to kick off the PDD loop immediately.

* Download updated repo ai-agent-playbook-starter3.zip

### What’s new

* `tests/test_chat_contract.py` — two failing tests:

  * `test_chat_missing_user_message_returns_400`
  * `test_chat_happy_path_returns_chatreply_shape`
* `tests/test_chat_streaming.py` — failing SSE streaming test:

  * `test_chat_streaming_sse_headers_and_events`
* `README.md` — “First Iterations (Red → Green)” section with next steps.

### How to proceed (now)

1. Run tests to see the reds:

   ```bash
   pytest -q
   ```
2. In Cursor, paste the **PHR-0005 architect** prompt for `/chat` (from the canvas doc or `docs/TUTORIAL-ITERATIONS.md`).
3. Then **PHR-0007 green**: “smallest diff to pass `tests/test_chat_contract.py`…”.
4. Repeat for SSE (PHR-0009 → 0011), then add the streaming ADR.

## Starter Repo Version 4 Update

Now we want to add stub files for app/agents/core.py, app/guards/schemas.py, etc., so Cursor has placeholders to fill during the green steps.

I added the stub modules so Cursor has clear targets to fill during your “green” steps, and I repackaged the repo.

* Download the updated repo ai-agent-playbook-starter4.zip

### Newly added stubs

* `app/agents/core.py` — session store + placeholders for `get_customer_agent()` and `get_runner()`
* `app/agents/tools.py` — `calculator()` and `now()` stubs
* `app/agents/customer.py` — instruction string
* `app/agents/research.py` — instruction string + `should_handoff()` policy stub
* `app/guards/schemas.py` — `ChatReply` Pydantic model
* `app/guards/rules.py` — `validate_reply()` guardrail stub
* `app/config.py` — minimal settings
* `app/streaming.py` — `to_sse()` SSE helper
* `__init__.py` for `app/`, `app/agents/`, `app/guards/`

### Next steps in Cursor

1. Run tests to see reds:

   ```bash
   pytest -q
   ```
2. Paste **PHR-0005 (architect)** for `/chat`, then **PHR-0007 (green)** to make the smallest diff that passes:

   * `tests/test_chat_contract.py::test_chat_missing_user_message_returns_400`
   * `tests/test_chat_contract.py::test_chat_happy_path_returns_chatreply_shape`
3. Move to streaming: **PHR-0009 → 0011** (architect → red → green for SSE).
4. Record **ADR-0002** for the streaming protocol choice; open a **PR** with PHR/ADR links.


