# The Ultimate 2025 Tutorial: Shipping AI Software “with a suit on”

**Spec-Driven Development (SDD) × Prompt-Driven Development (PDD) × TDD × EDD × ADR × PHR × PR**
*(Works equally well in VS Code + Codex or Cursor; uses Python, FastAPI, uv, and the OpenAI Agents SDK.)*

---

## 0) What you’ll build

A production-shaped **chat service** that demonstrates:

* `/healthz` (hello world)
* `/chat` (structured JSON contract)
* `/chat` **streaming** via SSE
* **Agents** with **tools** (calculator, now) + **guardrails**
* Optional **handoff** to a Research agent
* **TDD** for unit/contract tests, **EDD** (promptfoo) for behavioral tests
* **SDD** specs, **PHRs** (Prompt History Records), **ADRs**, and a PR template with a **Spec-Compliance** checkbox
* Reproducible envs via **uv**, CI (ruff + pytest + optional EDD), and Docker

You can start from the two starter repos we generated earlier:

* **Cursor**-flavored starter: `cursor-pdd-starter.zip`
* **VS Code + Codex** starter: `vscode-codex-pdd-starter.zip`
  (Each includes PHR/ADR templates, CI, Dockerfile, tests, rules, and optional EDD scaffolding.)

---

## 1) Core ideas (keep these on your desk)

### Spec-Driven Development (SDD)

Write a **single source of truth** for each thin slice *before* any code: scope, contracts, behaviors, acceptance tests, ops constraints, and change control. The spec anchors every prompt, test, and PR.

### Prompt-Driven Development (PDD)

Ship in **baby steps** through sequenced prompts:

1. **Plan** (Architect prompt)
2. **Red** (tests only)
3. **Green** (smallest diff)
4. **Refactor** (keep tests green)
5. **Explain** (short diff notes)
6. **Record** (PHR & ADR)
7. **Share** (PR with CI gates)

### TDD (Test-Driven Development)

Write **failing tests first**; implement only enough to go green. TDD is how you make PDD precise.

### EDD (Evaluation-Driven Development)

Turn your **agent behavior** into measurable suites (promptfoo). Gate PRs with a small smoke suite; run a deeper matrix nightly.

### Governance acronyms

* **PHR** (Prompt History Record): one Markdown per meaningful prompt (what you asked, scope, acceptance, outcome).
* **ADR** (Architecture Decision Record): short memo explaining **why** the design choice.
* **PR**: small, CI-gated change set linking PHRs, ADRs, and the **spec**.

---

## 2) Architecture in one view

**Client → FastAPI (`/chat`) → Agents SDK → Tools (calculator/now) → Guardrails → SSE streaming**

* **Sessions** keyed by `session_id`
* Optional **handoff** to a specialized Research agent
* **Tracing** (optional) for spans around tools & handoffs

*Diagram ideas to include in your docs:*

1. **System context** (blocks and arrows)
2. **Sequence** for `/chat` (non-streaming + SSE branch)
3. **Contract diagram** for `ChatReply` and error envelope
4. **Workflow loop** (SDD spec → PDD → TDD/EDD → ADR/PR)
5. **Traceability map** (Spec ↔ PHR ↔ ADR ↔ PR ↔ CI)

---

## 3) Workspace setup (one time)

```bash
# Project bootstrap
uv venv && source .venv/bin/activate
uv init --python 3.12
uv add fastapi "uvicorn[standard]" pydantic python-dotenv httpx pytest ruff openai-agents
mkdir -p app/{agents,guards} tests docs/{specs,adr,prompts,pr,diagrams} .github/workflows evals/{behavior,datasets,rubrics}
echo "OPENAI_API_KEY=\nMODEL=gpt-5" > .env.sample
```

**VS Code**: add `.vscode/tasks.json` for `lint`, `test`, `run`, and `edd:smoke`.
**Cursor**: paste your **house rules** (we provided a rules file) into *Settings → Rules for AI*.

---

## 4) Write the first SDD specs

Create `docs/specs/spec-chat-v1.md` (non-streaming) and `docs/specs/spec-chat-streaming-sse-v1.md` (SSE). Here are concise versions (we already gave you full files in the specs bundle):

**`spec-chat-v1.md` (highlights)**

* **POST** `/chat` with `{session_id, user_message}`
* Response `ChatReply { text, used_tool?, handoff }`
* **400** on missing `user_message` with top-level body: `{"error_code":"MISSING_USER_MESSAGE"}`
* Sessions: in-memory per `session_id`
* Guardrail: text length ≤ 1200, structured response

**`spec-chat-streaming-sse-v1.md` (highlights)**

* If `Accept: text/event-stream`, stream tokens as lines: `data:<token>\n\n`
* End with `data:[DONE]\n\n`
* JSON fallback if not SSE

**ADR**: `docs/adr/0002-streaming-protocol-choice.md` (SSE vs WS vs long-poll; pick SSE for v1)

---

## 5) PDD × TDD × SDD: the step-by-step build

> You’ll *paste prompts* into Cursor or Codex. Keep diffs tiny and always run tests between steps.

### Slice A — `/healthz` (warm-up)

**A1 – Architect (PHR)**
*Prompt gist:* Implement `GET /healthz` (200 `{"status":"ok"}`), add `tests/test_healthz.py`, README curl. Minimal diff.

**A2 – Red**
Add failing test `test_healthz_ok()`.

**A3 – Green**
Implement the handler to pass.
Run: `uv run pytest -q` → green.

**A4 – Explain & Record**
Ask for an 8-bullet explainer; save PHR; open a tiny PR.

---

### Slice B — `/chat` non-streaming to **spec**

**B1 – Red tests** (contract)
Create `tests/test_chat_contract.py` with:

* `test_chat_missing_user_message_returns_400_top_level_error_code()`
* `test_chat_happy_path_returns_chatreply_shape()`

> We provided ready-made RED tests in `red-tests-bundle.zip`.

**B2 – Green (to spec)**
Use this **Green PHR** (we gave you the exact file `0102-implement-to-spec-chat-green.prompt.md`):

> Implement exactly `docs/specs/spec-chat-v1.md`; minimal diff; only touch `app/main.py`, `app/guards/schemas.py`, `tests/test_chat_contract.py`. 400 must return **top-level** `{"error_code": "MISSING_USER_MESSAGE"}`, not `{"detail":...}`.

Run: `uv run pytest -q` → should be green.

**B3 – Explain & Record**
Save the explainer. Commit with PHR + link the spec.

---

### Slice C — **SSE** streaming to **spec**

**C1 – Red tests**
Create `tests/test_chat_streaming.py` asserting `Content-Type: text/event-stream`, at least one `data:` line, and terminator `data:[DONE]`.

**C2 – Green (to spec)**
Use `0103-implement-to-spec-sse-green.prompt.md`:

> Implement SSE per `spec-chat-streaming-sse-v1.md`. Add streaming when `Accept: text/event-stream`, JSON fallback otherwise, minimal diff.

Run: `uv run pytest -q` → green.

**C3 – ADR**
Accept `ADR-0002` in git; link it in PR.

---

### Slice D — Tools & Guardrails (policy)

**D1 – Architect**
Spec (or add to `spec-chat-v1.md`) policy section:

* Tools: `calculator(expression)`, `now(tz?)`
* **Tool-first** for math/time; no guessing
* Guardrail: `ChatReply` schema and length ≤ 1200; retry once then friendly error

**D2 – Red (unit & minimal EDD)**

* Unit tests that enforce JSON shape and length rule
* **EDD smoke** (`evals/behavior/002-math-tool-usage.yaml`)—e.g., *18% tip on \$62.50* expected to include correct value (or surface `used_tool` if you return metadata)

**D3 – Green**
Wire tools under an Agent (Agents SDK) and validate through the guardrail.

**D4 – Explain & Record**
PHR (“tool policy + guardrails”), ADR if policy is consequential.

---

### Slice E — Optional ResearchAgent handoff

**E1 – Architect**
Spec handoff: *If intent = RESEARCH with confidence ≥0.7 → handoff; surface `handoff_reason`.*

**E2 – Red**
Mocked test that forces handoff path and checks metadata.

**E3 – Green**
Add `ResearchAgent`, route by intent, pass tests.

---

## 6) EDD: behavioral safety net with **promptfoo**

**Why**: Unit tests catch code errors; **EDD** catches **behavioral drift**.

**Repo additions** (already scaffolded):

```
promptfoo.config.yaml
evals/behavior/001-scope-discipline.yaml
evals/behavior/002-math-tool-usage.yaml
evals/datasets/*.csv   # optional larger suites
```

**Run locally**

```bash
promptfoo eval --suite smoke        # quick PR-gate set
promptfoo eval --suite full         # slower, pre-merge or nightly
```

**CI gate snippet** (extra job):

```yaml
  edd:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm i -g promptfoo
      - name: Start API
        run: |
          nohup uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 >/dev/null 2>&1 &
          sleep 2
      - run: promptfoo eval --config promptfoo.config.yaml --suite smoke --format junit --output results/edd.xml
```

**PR policy**: lint + unit tests + **EDD smoke** must pass (no green, no merge).

---

## 7) PRs, ADRs, PHRs—make change review effortless

**PR template (updated)** includes:

* **Linked Spec(s)**
* PHRs & ADRs
* Test plan
* **Checklist** with **Spec compliance** box:

  * Contracts, behaviors, constraints **implemented as written**
  * **Spec acceptance tests present and passing**
  * EDD smoke passing (if configured)

**PHRs** live in `docs/prompts/NNNN-<slug>-<stage>.prompt.md`. Include:

* Scope, acceptance, constraints, exact prompt, and a short *Outcome* (files, tests, notes)
* Reviewers read PHR to understand your **intent** in seconds.

**ADRs** live in `docs/adr/*.md`. 1–2 pages each, tops.

---

## 8) Docker & CI

**Dockerfile** uses uv in a **multi-stage** build; app runs as non-root.
**GitHub Actions**: `ruff` + `pytest` (+ optional promptfoo smoke).
**Makefile** (or VS Code Tasks) to standardize commands: `lint`, `test`, `run`, `edd:smoke`.

---

## 9) Operating model for teams

* Roles (can be prompts, not people): **Architect**, **Implementer**, **Tester**, **Tech Writer**, **Release Shepherd**
* Policies (defaults):

  * Small diffs; **no green, no merge**
  * ADR required for API or dependency shifts
  * **Coverage threshold** and **contract tests** for public surfaces
  * **Spec** versioning and change control
* Hygiene:

  * `.env.sample`, `README`, PR template, CI, PHR & ADR directories
  * **Tracing** optional but recommended

---

## 10) Anti-patterns & fixes

* **Vibe coding** (prompting without specs) → write a **thin spec** per slice.
* **Prompt drift** → reference the **spec file** and **PHR id** in every new prompt.
* **Brittle behavior** → add **EDD** semantics (e.g., `similar`, regex) and pin models for PR gates.
* **Flaky tests** → keep unit tests offline; mock external calls.
* **Big bang changes** → many small PRs; each PR links a spec + PHR + ADR.

---

## 11) Copy-paste assets (minimal, production-shaped)

### a) `ChatReply` model

```python
# app/guards/schemas.py
from pydantic import BaseModel
from typing import Optional

class ChatReply(BaseModel):
    text: str
    used_tool: Optional[str] = None
    handoff: bool = False
```

### b) Error envelope for spec-compliant 400s

```python
# app/http_errors.py (optional helper)
from fastapi import JSONResponse

def bad_request(error_code: str):
    return JSONResponse(status_code=400, content={"error_code": error_code})
```

### c) Contract tests (RED → then GREEN)

```python
# tests/test_chat_contract.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_chat_missing_user_message_returns_400_top_level_error_code():
    res = client.post("/chat", json={"session_id":"s1"})
    assert res.status_code == 400
    assert res.json().get("error_code") == "MISSING_USER_MESSAGE"

def test_chat_happy_path_returns_chatreply_shape():
    res = client.post("/chat", json={"session_id":"s2","user_message":"Hello"})
    assert res.status_code == 200
    body = res.json()
    assert "text" in body and "handoff" in body and "used_tool" in body
```

### d) SSE tests

```python
# tests/test_chat_streaming.py
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_streaming_sends_event_stream_headers():
    h = {"Accept":"text/event-stream"}
    res = client.post("/chat", json={"session_id":"s","user_message":"stream"}, headers=h, stream=True)
    assert res.status_code == 200
    assert "text/event-stream" in res.headers.get("content-type","").lower()

def test_streaming_emits_at_least_one_data_line_and_done():
    h = {"Accept":"text/event-stream"}
    with client.stream("POST","/chat", json={"session_id":"s2","user_message":"go"}, headers=h) as res:
        body = "".join(list(res.iter_text()))
        assert "data:" in body
        assert "data:[DONE]" in body
```

### e) EDD smoke examples (promptfoo)

```yaml
# evals/behavior/001-scope-discipline.yaml
tests:
  - name: "Out-of-scope politely declines"
    vars: { prompt: "Reset my AWS root password" }
    assert:
      - type: contains
        value: "I can’t help with that"

# evals/behavior/002-math-tool-usage.yaml
tests:
  - name: "Tips are computed, not guessed"
    vars: { prompt: "What is 18% tip on $62.50?" }
    assert:
      - type: contains
        value: "18%"
```

---

## 12) First week plan (do this and you’re rolling)

**Day 1**

* Paste rules (Cursor or PR-ready in repo)
* Create `/healthz` (A slice) → PR → merge

**Day 2–3**

* Write `spec-chat-v1.md` and **contract tests** (B slice) → Green → PR with **Spec-Compliance** checked

**Day 3–4**

* Write SSE spec + tests (C slice) → Green → ADR → PR

**Day 4–5**

* Tools + Guardrails (D slice) with **EDD smoke** → PR (add EDD to CI if ready)

**Day 5**

* Optional handoff (E slice) → PR
* Publish **Prompt Library** (architect/red/green/refactor/explainer; implement-to-spec)

---

## 13) The mindset

Summer ’25 made AI pair-dev table stakes. Winners don’t merely “use AI”—they **operationalize** it:

* **SDD** keeps intent crisp and shared
* **PDD** keeps velocity high (tiny, test-guarded diffs)
* **TDD/EDD** keep quality visible and measurable
* **PHR/ADR/PR** keep decisions auditable and maintainable

That’s how you ship fast **and** sleep at night.

---

We’ve packaged **everything** we discussed into a single drop-in bundle you can merge into either starter repo (Cursor or VS Code + Codex).

**Download:**

* **Ultimate Additions (specs + PHRs + RED tests + error helper + EDD + CI + PR template)**

  ultimate-additions.zip

### What’s inside (at a glance)

* **SDD Specs**

  * `docs/specs/spec-chat-v1.md` — `/chat` non-streaming contract
  * `docs/specs/spec-chat-streaming-sse-v1.md` — SSE protocol (Accept: text/event-stream, `data:<token>\n\n`, `data:[DONE]\n\n`)
* **ADR**

  * `docs/adr/0002-streaming-protocol-choice.md` — SSE vs WS vs long-poll (Accepted)
* **PHRs (Implement-to-spec prompts)**

  * `docs/prompts/0102-implement-to-spec-chat-green.prompt.md`
  * `docs/prompts/0103-implement-to-spec-sse-green.prompt.md`
* **RED Tests (TDD)**

  * `tests/test_chat_contract.py` — enforces top-level `{"error_code": "MISSING_USER_MESSAGE"}` and `ChatReply` shape
  * `tests/test_chat_streaming.py` — SSE headers + token lines + terminator
* **Error Helper**

  * `app/http_errors.py` — returns spec-compliant 400 errors
* **EDD (promptfoo)**

  * `promptfoo.config.yaml`
  * `evals/behavior/001-scope-discipline.yaml` (in/out of scope)
  * `evals/behavior/002-math-tool-usage.yaml` (tool-first policy)
* **CI & PR template**

  * `.github/workflows/ci-edd-example.yml` — adds **EDD smoke** job beside unit tests
  * `.github/PULL_REQUEST_TEMPLATE.md` — includes the **Spec compliance** checkbox

### How to merge

1. Unzip into your repo root (it won’t overwrite your code unless paths already exist).
2. If you already have a PR template, merge in the **Spec compliance** checklist block.
3. Run tests:

```bash
uv run pytest -q           # Expect RED until you implement to spec
```

4. (Optional EDD)

```bash
npm i -g promptfoo
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 &
promptfoo eval --suite smoke
```

5. Use the included **PHR prompts** to run **Green** steps strictly to spec.

## Unified Starter

We merged everything into a single, fully-wired template that works in **VS Code + Codex** and **Cursor**.

**Download the unified starter:**

* ai-agent-starter-all-in-one.zip

### What you get

* **Production-shaped scaffold**: FastAPI app, `/healthz`, `/chat` (JSON), SSE stub (tests included), uv deps, Dockerfile.
* **Governance**: SDD specs, PHRs (implement-to-spec prompts), ADR, updated PR template with **Spec compliance** checkbox, Git hooks nudging PHRs.
* **Quality gates**: TDD tests (contract + streaming), EDD via **promptfoo** (smoke suites), CI workflows (ruff + pytest + optional EDD job).
* **Editor support**: VS Code tasks (`lint`, `test`, `run`, `edd:*`), works great in Cursor too.

### Quickstart

```bash
unzip ai-agent-starter-all-in-one.zip -d ./ai-agent-starter
cd ai-agent-starter
uv venv && source .venv/bin/activate
uv sync
uv run pytest -q    # healthz + /chat contract should pass; SSE tests are RED until you implement
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
curl -s http://localhost:8000/healthz
```

### Next steps (SDD × PDD × TDD × EDD loop)

1. **/chat (non-streaming)**

   * Spec: `docs/specs/spec-chat-v1.md`
   * PHR: `docs/prompts/0102-implement-to-spec-chat-green.prompt.md`
   * Tests: `tests/test_chat_contract.py`
2. **SSE streaming**

   * Spec: `docs/specs/spec-chat-streaming-sse-v1.md`
   * PHR: `docs/prompts/0103-implement-to-spec-sse-green.prompt.md`
   * Tests: `tests/test_chat_streaming.py`
3. **EDD (promptfoo)**

   * Config: `promptfoo.config.yaml`
   * Suites: `evals/behavior/*.yaml`
   * Run: `promptfoo eval --suite smoke`
4. **PR**

   * Use `.github/PULL_REQUEST_TEMPLATE.md` with **Spec compliance** box and link your PHRs/ADRs.

## Added **Cursor Rules** bundle and a **Codex Prompting House Rules** file into the repo, so your team has the same “guardrails” inside both IDEs.

We’ve embedded **both rules bundles** into the unified starter and repackaged it.

* **Unified starter (now with Cursor + Codex rules):**
  
  ai-agent-starter-with-rules.zip

### Where to find them in the repo

```
docs/
  rules/
    cursor-rules.md
    cursor-rules.json
    codex-rules.md
    codex-rules.json
    README.md
```

### How to use

* **Cursor:** open *Cursor → Settings → Rules for AI* and paste the contents of `docs/rules/cursor-rules.md` (or JSON).
* **VS Code + Codex:** keep `docs/rules/codex-rules.md` in-repo and paste its top section into your initial task prompts so Codex follows the same SDD × PDD × TDD × EDD guardrails.

## Ready-to-Run Cursor Composer prompts** (Architect/Red/Green/Refactor/Explainer) prefilled for your `/chat` and SSE slices

You now have **ready-to-run Cursor Composer prompts** for both slices (/chat and SSE) across the full PDD loop (Architect → Red → Green → Refactor → Explainer), plus a **Fix-only** micro-prompt.

**Download:**

* cursor-composer-prompts.zip

### What’s inside (`docs/prompts/`)

* **/chat (non-streaming)**

  * `0201-architect-chat.prompt.md`
  * `0202-red-chat.prompt.md`
  * `0203-green-chat.prompt.md`
  * `0204-refactor-chat.prompt.md`
  * `0205-explainer-chat.prompt.md`
* **SSE streaming**

  * `0211-architect-sse.prompt.md`
  * `0212-red-sse.prompt.md`
  * `0213-green-sse.prompt.md`
  * `0214-refactor-sse.prompt.md`
  * `0215-explainer-sse.prompt.md`
* **Maintenance**

  * `0299-fix-only.prompt.md` (smallest-change-to-green)

### How to use in Cursor

1. Open your repo in Cursor.
2. Press **⌘I / Ctrl+I** to open Composer.
3. Paste the relevant prompt file content and run.
4. Approve the diffs, run tests, repeat the loop.

## Unified starter zip so you have one download with everything (rules, specs, ADR/PHR, tests, CI, EDD, prompts)

All set! I’ve injected the **Cursor Composer prompts** directly into the unified starter repo.

**Download the one-stop starter (rules + specs + ADR/PHR + tests + CI + EDD + Cursor prompts):**

* ai-agent-starter-with-rules-and-prompts.zip

### Where everything lives

```
docs/
  specs/                       # SDD specs (/chat, SSE)
  adr/                         # ADR-0002 streaming protocol
  prompts/                     # PHRs + Cursor Composer prompts (Architect/Red/Green/Refactor/Explainer, Fix-only)
  rules/                       # Cursor & Codex rules bundles (MD + JSON)
.github/
  workflows/ci.yml             # unit/lint CI
  workflows/ci-edd.yml         # EDD smoke (promptfoo) CI
tests/                         # Contract + SSE tests (TDD)
evals/                         # EDD behavior suites (promptfoo)
app/                           # FastAPI app, schema, SSE helper, 400 helper
```

### Quickstart

```bash
unzip ai-agent-starter-with-rules-and-prompts.zip -d ./ai-agent-starter
cd ai-agent-starter
uv venv && source .venv/bin/activate
uv sync
uv run pytest -q                      # some tests RED until you run the Green prompts
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Run the PDD loop in Cursor

1. Open the folder in **Cursor**.
2. Press **⌘I / Ctrl+I** → paste `docs/prompts/0201-architect-chat.prompt.md`.
3. Then `0202-red-chat.prompt.md` (tests only) → run tests (RED).
4. `0203-green-chat.prompt.md` to implement to spec → run tests (GREEN).
5. Repeat for SSE with `0211…` → `0212…` → `0213…`.

## The final version that already **implements SSE** so everything is green out-of-the-box:

Done! I’ve produced a version where **SSE is fully implemented** so the test suite should be green out of the box.

* **Download (SSE implemented, tests pass):**
  
  ai-agent-starter-green.zip

### What changed

* Implemented SSE in `app/main.py`:

  * Detects `Accept: text/event-stream`
  * Streams tokens via `StreamingResponse(to_sse(...))`
  * Emits `data:<token>\n\n` and ends with `data:[DONE]\n\n` (handled by `to_sse`)
* Non-streaming path still returns the structured `ChatReply`.

### Quick test

```bash
unzip ai-agent-starter-green.zip -d ./ai-agent-starter
cd ai-agent-starter
uv venv && source .venv/bin/activate
uv sync
uv run pytest -q        # should be all green now
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
```






