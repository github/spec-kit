# Nano Banana Prompts to Generate Diagrams

Here’s a copy-paste pack of **Nano Banana** prompts to generate every diagram we’ve used (and a few extras teams usually want). each prompt is self-contained and tells the model what to draw, the style, constraints, and what to label. just paste one prompt at a time into Nano Banana and export as SVG/PNG.

Download:

* NANO-BANANA-PROMPTS.md

---

## 1) System Context (high-level architecture)

**Prompt (copy-paste):**

```
You are a diagramming assistant. Create a clean SYSTEM CONTEXT diagram titled
"GPS Engineering — AI Chat Service (System Context)". Style: minimal, readable, light grid, no clip art.

Include these nodes and relationships:
- Client (Web UI/CLI)
- FastAPI Service (/healthz, /chat)
- OpenAI Agents SDK (Agents, Runner/stream, Sessions) — inside the service boundary
- Tools cluster (calculator, now, future: RAG/Knowledge)
- Guardrails (Pydantic output, max length 1200)
- Config/Secrets (.env via dotenv)
- Tracing/Logs (optional)
- CI (ruff, pytest, promptfoo EDD smoke)
- Registry (container images)
- Runtime (Uvicorn container behind reverse proxy)
- Editor Environments (Cursor; VS Code + GPT-5 Codex) — outside runtime

Edges:
- Client -> FastAPI: POST /chat (JSON or SSE)
- FastAPI -> Agents SDK: run(session, tools, guardrails)
- Agents SDK -> Tools: function_tool invocations
- FastAPI -> Tracing/Logs: spans + events (optional)
- CI -> Registry -> Runtime: build/push/deploy
- FastAPI -> Config/Secrets: env on startup
- Editors -> Git: commits/PRs (PHR/ADR links)

Constraints:
- Group Agents SDK + Tools + Guardrails as "Agent Runtime" cluster.
- Show protocols on edges where relevant: HTTP, SSE.
- Keep labels short; use straight lines, right angles.

Output: vector (SVG), transparent background if possible.
```

---

## 2) Runtime Sequence — /chat (non-streaming)

**Prompt:**

```
Draw a SEQUENCE DIAGRAM titled "POST /chat (non-streaming) — GPS Engineering".

Lifelines:
- User
- FastAPI (/chat)
- Session Store (in-memory)
- CustomerAgent (via Agents SDK Runner)
- Tools (calculator, now)

Steps:
1) User -> FastAPI: POST /chat {session_id, user_message}
2) FastAPI -> Session Store: get_or_create(session_id)
3) FastAPI -> CustomerAgent: run(message, session, tools, guardrails)
4) alt tool-needed
   CustomerAgent -> Tools: calculator/now
   Tools -> CustomerAgent: result
   end
5) CustomerAgent -> FastAPI: ChatReply {text, used_tool?, handoff=false}
6) FastAPI -> User: 200 JSON

Notes:
- Enforce Pydantic shape; length <= 1200 chars.
- On missing user_message: return 400 {error_code:"MISSING_USER_MESSAGE"} (top-level).
Style: compact lifelines, balanced spacing. Output SVG.
```

---

## 3) Runtime Sequence — /chat with SSE streaming

**Prompt:**

```
Create a SEQUENCE DIAGRAM titled "POST /chat (SSE streaming) — GPS Engineering".

Actors:
- User
- FastAPI (/chat)
- CustomerAgent (runner.stream)
- Tools (optional)

Flow:
- User -> FastAPI: POST /chat with header Accept: text/event-stream
- FastAPI -> CustomerAgent: stream(user_message, session)
- loop token streaming
    CustomerAgent -> FastAPI: token
    FastAPI -> User: SSE line "data:<token>\n\n"
- end loop
- FastAPI -> User: SSE terminator "data:[DONE]\n\n"

Notes:
- Response header: Content-Type: text/event-stream
- Optional tool call in an 'opt tools' section
- JSON fallback if Accept header not present

Style: readable chunks, thin arrows. Output SVG.
```

---

## 4) Agent Handoff — intent router

**Prompt:**

```
Design a STATE/ACTIVITY diagram titled "Agent Handoff Policy (Customer ↔ Research)".

States/Nodes:
- Parse Intent
- Confidence Check
- Route: CustomerAgent
- Route: ResearchAgent
- Handoff Reason (log/metadata)
- Respond

Transitions (with guards):
- Parse Intent -> Confidence Check
- [intent=RESEARCH ∧ confidence≥0.7] -> ResearchAgent
- [else] -> CustomerAgent
- Both routes -> Handoff Reason -> Respond

Style: businesslike, minimal icons. Output SVG.
```

---

## 5) Contract/Class Model — ChatReply + ErrorBody

**Prompt:**

```
Draw a CLASS DIAGRAM titled "Contracts: ChatReply & Errors".

Classes:
- ChatReply
  - text: str
  - used_tool: Optional[str]
  - handoff: bool
- ErrorBody
  - error_code: str

Notes:
- Show types; mark Optional with ?
- /chat returns ChatReply on 200; ErrorBody on 400 for missing user_message (top-level field).
- Keep small and printable. Output SVG.
```

---

## 6) Deployment (Dev → CI → Runtime)

**Prompt:**

```
Create a DEPLOYMENT diagram titled "Pipeline: Dev → CI → Runtime (uv + Docker)".

Nodes:
- Dev Workstation (Cursor; VS Code + GPT-5 Codex)
- GitHub (PRs with Spec-Compliance checkbox)
- CI (ruff, pytest, promptfoo EDD smoke, docker build)
- Registry (container image)
- Runtime (Uvicorn container, non-root user, healthcheck)
- Observability (logs/traces)

Edges:
- Dev -> GitHub: push PR (links PHRs and ADRs)
- GitHub -> CI: workflow run
- CI -> Registry: push versioned image
- Registry -> Runtime: pull & deploy
- Runtime -> Observability: traces + logs

Style: rectangular nodes, cluster “Platform” for GitHub/CI/Registry. Output SVG.
```

---

## 7) Data Flow — sessions, tools, guardrails

**Prompt:**

```
Produce a DATA FLOW diagram titled "Chat Execution Data Flow (Tools + Guardrails)".

Elements:
- Request: {session_id, user_message}
- Session Store (in-memory)
- Agent (instructions + tools)
- Tools (calculator, now; future: RAG)
- Guardrails (validate ChatReply; MAX_LEN=1200; structured)
- Response: ChatReply

Arrows:
Request -> Agent
Agent <-> Session Store
Agent -> Tools (optional)
Tools -> Agent (result)
Agent -> Guardrails -> Response

Annotations:
- No secrets in payload; secrets from .env on startup.
Style: left-to-right, labeled edges. SVG output.
```

---

## 8) Error Taxonomy — quick map

**Prompt:**

```
Draw a MIND MAP titled "Error Taxonomy (Chat Service)".

Center: Errors
Branches:
- 400 Bad Request
  - MISSING_USER_MESSAGE (top-level error_code)
  - Invalid payload shape
- 415 Unsupported Media Type
  - Non-JSON POST
- 500 Internal Error
  - Tool failure
  - Runner exception
- Streaming
  - SSE headers missing
  - Proxy buffering issues

Style: compact, monochrome. Output SVG.
```

---

## 9) CI Pipeline — gates & artifacts (with EDD)

**Prompt:**

```
Create a PIPELINE diagram titled "CI Gates (TDD + EDD)".

Stages:
- Lint (ruff)
- Unit/Contract Tests (pytest, offline)
- EDD Smoke (promptfoo; scope discipline, tool-first policy)
- Build (Docker with uv)
- Publish (registry)
- Optional: Deploy (manual approval)

Artifacts:
- Test reports (unit/contract)
- EDD report
- Docker image

Rules:
- Gate "No green, no merge" between Tests/EDD and Build
- PR requires Spec link + PHR/ADR references

Style: horizontal flow, check icons on gates. Output SVG.
```

---

## 10) Repository Map — folders & purpose

**Prompt:**

```
Render a REPOSITORY STRUCTURE diagram titled "Repo Map (GPS Starter)".

Folders:
- app/
  - agents/ (core, tools, customer, research)
  - guards/ (schemas, rules)
  - streaming.py (SSE utilities)
  - http_errors.py (spec-compliant 400)
  - main.py (FastAPI)
- tests/ (contract + streaming)
- docs/
  - specs/ (SDD: spec-chat, spec-sse)
  - prompts/ (PHRs + Cursor prompts)
  - adr/ (ADR-0002: SSE vs WS)
  - rules/ (Cursor & Codex rules bundles)
  - diagrams/ (exports)
- evals/ (promptfoo config + behavior suites)
- .github/workflows/ (ci, ci-edd)
- Dockerfile, pyproject.toml, Makefile, .env.sample

Annotate each folder with a 3–6 word purpose.
Style: tree layout, monospace labels. Output SVG.
```

---

## 11) Prompt-Driven Development — loop (“…with a suit on”)

**Prompt:**

```
Make a CYCLE diagram titled "PDD × TDD Loop — …with a suit on".

Nodes (in order):
- Plan (Architect Prompt; micro-spec)
- Red (Tests only; contract/unit)
- Green (Smallest diff; implement to spec)
- Refactor (keep tests green)
- Explain (Explainer prompt; ≤8 bullets)
- Record (PHR + ADR)
- Share (PR with CI gates; Spec-Compliance)

Arrows connect in a loop. Add one-line notes under each node.
Style: circular arrows, professional palette. Output SVG.
```

---

## 12) PR Lifecycle — with governance

**Prompt:**

```
Build a FLOWCHART titled "PR Lifecycle — GPS Governance".

Steps:
- Open PR (links Spec + PHRs + ADRs)
- CI runs (ruff, pytest, EDD smoke)
- Review (small diffs preferred; traceability checks)
- Gate: "No green, no merge"
- Merge to main
- Tag & Release notes (optional)

Side notes:
- Security: No secrets in code/prompts (.env only)
- Observability: enable tracing on release

Style: two swimlanes (Developer vs CI/Review). Output SVG.
```

---

## 13) Traceability — Prompts ↔ Specs ↔ ADRs ↔ PRs ↔ CI

**Prompt:**

```
Design a RELATIONSHIP diagram titled "Traceability: Spec ↔ PHR ↔ ADR ↔ PR ↔ CI".

Entities:
- Spec (docs/specs/*.md)
- PHR (Prompt History Record) (docs/prompts/*.prompt.md)
- ADR (docs/adr/*.md)
- PR (links to Spec, PHRs, ADRs; Spec-Compliance checkbox)
- CI (lint/tests/EDD)

Links:
- Spec -> PHR (prompts reference exact spec file)
- PHR -> PR (PR aggregates 1..n PHRs)
- ADR <-> Spec (decisions impacting specs/protocols)
- PR -> CI (gates)
- CI -> Status (required for merge)

Use crow's-foot or simple 1..n cardinalities. Output SVG.
```

---

## 14) Streaming Headers — tiny reference card (bonus)

**Prompt:**

```
Create a SMALL REFERENCE CARD titled "SSE Headers & Events (Quick Ref)".

Show:
- Request header: Accept: text/event-stream
- Response header: Content-Type: text/event-stream
- Event lines:
  - data:<token>\\n\\n
  - data:[DONE]\\n\\n
Note: Use JSON ChatReply when Accept header is not present (fallback).

Style: index-card layout, code font for header lines. Output SVG.
```

---

## 15) Security & Secrets — flow (bonus)

**Prompt:**

```
Draw a SIMPLE FLOW diagram titled "Secrets & Config Flow (.env)".

Nodes:
- .env / .env.sample (OPENAI_API_KEY, MODEL)
- Settings loader (dotenv)
- FastAPI app
- OpenAI Agents SDK (Agent/Runner)

Arrows:
.env -> Settings -> FastAPI -> Agents SDK

Rule: "Never hardcode secrets. Use environment variables and .env.sample."
Style: minimalist. Output SVG.
```

---

### Tips for Nano Banana

* If the tool supports **“revise”**, try: “tighten spacing,” “reduce label size,” “transparent background,” “export SVG.”
* Keep node counts modest; split large concepts (like CI) into dedicated diagrams.
* Use consistent titles so your exported diagrams double as document section headings.


