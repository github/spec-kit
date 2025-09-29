# Hello PDD + ADR Guide: Get Started with Prompt-Driven Development

Hey, jumping into Prompt-Driven Development (PDD) with Architecture Decision Records (ADRs) can seem a bit much at first.You're not alone—it's normal to feel confused, but once you try this simple example, it'll click. 

This guide walks you through building a tiny "Hello World" FastAPI app, step by step. It's designed for beginners, with tips for agentic AI projects like documenting agent choices.

PDD uses AI prompts (e.g., in Cursor, ChatGPT, or CLI Coding Agent) to code in small, testable steps—like Test-Driven Development (TDD) but powered by AI. ADRs capture the "why" behind big decisions. Prompt History Records (PHRs) save your prompts as files for easy replay and team sharing. Together, they make code traceable, reduce bugs, and scale well for agentic AI where things change fast.

We'll use **uv** for project management (fast and simple—assume it's installed). FastAPI for the app (modern, async-ready for AI workflows).

## Quick Setup: Bootstrap Your Project
1. Unzip the skeleton: If you have ai-prompt-history-starter.zip, unzip it: `unzip ai-prompt-history-starter.zip`.
2. Enter folder: `cd ai-prompt-history-starter`.
3. Open in IDE: Use VS Code, PyCharm, or your favorite—open the folder for easy editing.
4. Init with uv: `uv init` (creates virtual env and pyproject.toml).
5. Add deps: `uv add fastapi uvicorn pytest` (for API, server, tests).
6. Init Git: `git init`.
7. Set hooks: `git config core.hooksPath .githooks`.
8. Make executable: `chmod +x .githooks/* scripts/*.py`.
9. Folders: `mkdir -p app tests`.
10. `make prompt-index`

Test: `uv run make prompt-new SLUG=test STAGE=architect` (creates a PHR file). Run commands with `uv run` to use the env. Delete the created file.

## Step 1: Create an ADR for Major Decisions
Start with ADRs for choices like frameworks or agent patterns—prevents random changes later.

- Why? Builds a record for teams or audits; crucial in agentic AI where decisions (e.g., "Use OpenAI SDK for agents") impact everything.
- How:
  - Create docs/adr/0001-web-framework.md (use template).
  - Fill it out (keep short):

```
# ADR-0001: Choose Web Framework for Hello App

- **Status:** Proposed
- **Date:** 2025-09-20

## Context
Need a simple API for /hello endpoint. Async support for future agentic features like real-time responses.

## Options
- A) Flask: Basic and quick. Pros: Minimal. Cons: Limited async.
- B) FastAPI: Modern with auto-docs. Pros: Type-safe, async-ready for AI. Cons: Small setup.
- C) No framework: Custom HTTP. Pros: Ultra-light. Cons: Reinvents basics.

## Decision
Choose FastAPI—suits Python agentic AI with validation and speed.

## Consequences
- Positive: Easy to extend for agents; built-in testing.
- Negative: Adds deps (managed by uv).
- References: uv docs for setup.
```

- Update status to Accepted.
- Commit: `uv run git add docs/adr/0001-*; uv run git commit -m "docs: add ADR-0001 for web framework"`.

This ADR guides your prompts—stick to it!

## Step 2: Build with PHRs in PDD Stages
Now code the app using AI prompts, one stage per PHR file. Break it down to avoid overwhelming AI outputs.

- Why stages? Keeps things focused and testable; great for agentic AI where you might prompt for "plan agent flow" then "test agent logic."
- Run one at a time: Create PHR → Edit prompt → Run in AI tool → Apply to code → Test → Add outcome → Commit.

You can use these system instructions with prompts
"You an AI Engineer. Following the ADR and prompt implement the assigned part carefully."

### 2.1 Architect Stage (Plan It)
- Goal: Outline files, acceptance, and risks.
- Run: `uv run make prompt-new SLUG=hello-world STAGE=architect`.
- File: docs/prompts/0001-hello-world-architect.prompt.md.
- Edit YAML: title "Plan Hello World Endpoint", scope_files ["app/main.py", "tests/test_hello.py"], links {adr: docs/adr/0001-web-framework.md}, acceptance ["GET /hello returns 200 JSON {'message': 'Hello World!'}"], constraints ["minimal diff, no new deps", "offline tests (mocks)"].
- Body: 
  ```
  You are the architect. Plan a FastAPI app with /hello endpoint. Per ADR-0001, use FastAPI. Files: app/main.py. Acceptance: GET /hello -> 200 JSON {"message": "Hello World!"}. Constraints: Minimal diff, no extra deps beyond FastAPI.
  ```
- Run in AI (e.g., Cursor): Get plan (e.g., "Add @app.get('/hello') returning dict. Test with TestClient.").
- Append Outcome:
  ```
  ### Outcome
  - Files changed: app/main.py (planned), tests/test_hello.py (planned)
  - Tests added: None yet
  - Next prompts: 0002 (red)
  - Notes: AI suggested JSON for agent compatibility.
  ```
- Commit: `uv run git commit -m "docs: add PHR-0001 for hello architect"`.

### 2.2 Red Stage (Failing Tests)
- Goal: Tests first—define success, ensure they fail without code.
- Run: `uv run make prompt-new SLUG=hello-world STAGE=red`.
- Edit: links {previous_prompt: 0001}, same acceptance.
- Body: 
  ```
  Add failing tests for /hello. No production code! Use pytest and FastAPI TestClient. Test: GET /hello returns 200 JSON {"message": "Hello World!"}. Offline mocks. Per PHR-0001.
  ```
- Run AI: Get test code.
- Add to tests/test_hello.py.
- Test: `uv run pytest`—should fail.
- Outcome: "Test fails as expected."
- Commit: `uv run git commit -m "test: add failing hello test refs: PHR-0002"`.

### 2.3 Green Stage (Make It Work)
- Goal: Add just enough code to pass tests.
- Run: `uv run make prompt-new SLUG=hello-world STAGE=green`.
- Edit: links {previous_prompt: 0002}.
- Body: 
  ```
  Implement /hello in app/main.py to pass tests. Minimal changes. Use FastAPI per ADR-0001.
  ```
- Run AI: Get code (e.g., from fastapi import FastAPI; app = FastAPI(); @app.get("/hello") def read_hello(): return {"message": "Hello World!"}).
- Add to app/main.py.
- Test: `uv run pytest`—passes!
- Outcome: "Tests pass now."
- Commit: `uv run git commit -m "feat: add hello endpoint refs: PHR-0003, ADR-0001"`.

### 2.4 Refactor Stage (Clean Up, Optional)
- If code needs polish (e.g., for agentic extensions): `uv run make prompt-new SLUG=hello-world STAGE=refactor`.
- Body: "Clean up /hello for agentic use—add async if needed, docs."
- Update, test, outcome, commit.

## Step 3: Link Everything and Merge
- Index: `uv run make prompt-index` (creates table in docs/prompts/index.md for quick search).
- Create PR:
  - Title: "Add Hello World Endpoint"
  - Body:
    ```
    Implements ADR-0001.
    Prompt History:
    - Architect: docs/prompts/0001-hello-world-architect.prompt.md
    - Red: docs/prompts/0002-hello-world-red.prompt.md
    - Green: docs/prompts/0003-hello-world-green.prompt.md
    ```
  - Hooks check refs automatically.
- Merge: Full history preserved.

## Step 4: Run, Learn, and Scale to Agentic AI
- Run: `uv run uvicorn app.main:app --reload` (visit localhost:8000/hello).
- Learn: Rerun a prompt? Copy from PHR body to AI. Quarterly, review index.md for patterns (e.g., "Effective prompts for async endpoints").
- For agentic AI: Use ADRs for "Choose agent framework (e.g., LangGraph vs. CrewAI)". PHRs for stages like "Plan agent workflow" then "Test agent handoffs".

See? Small steps make it manageable. Start here, then apply to your projects.