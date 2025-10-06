# Guide: Using OpenAI **ChatGPT‑5 Codex** (the agentic coding companion)

This guide shows how to get started with **ChatGPT‑5 Codex**, what each surface (Cloud, CLI, IDE) is for, and how to work with it effectively—using **Prompt‑Driven Development (SDD)**, **TDD**, and **ADR/PR** guardrails.

---

## 1) What ChatGPT‑5 Codex is (in one minute)
**Codex** is OpenAI’s coding **agent**. It can read your repo, modify files, run code in a sandbox, and work on multiple tasks **in parallel**. In ChatGPT, you delegate work to Codex; it can also run via a CLI or inside your IDE. Codex uses **GPT‑5** (or GPT‑5‑Codex) as its default model for coding/agentic tasks.

**Key capabilities**
- Reads/edits entire codebases; proposes/opens PRs with tests and docs.
- Runs jobs in the **cloud sandbox** (Codex Cloud) or in your terminal (Codex CLI).
- Pairs neatly with the **OpenAI Agents SDK** patterns (tools, sessions, handoffs).

---

## 2) Prerequisites & access
- ChatGPT plan with **GPT‑5**/Codex access.
- Enable **Codex** (Cloud/CLI/IDE) and authenticate.
- Optional GitHub connection so Codex can open PRs.

---

## 3) Pick your surface: Cloud vs CLI vs IDE
| Surface | Best for | How to use |
|---|---|---|
| **Codex Cloud** | Parallel, long‑running, repo‑wide changes; tests/docs generation | In ChatGPT, assign tasks; Codex returns diffs/logs/PRs |
| **Codex CLI** | Local, repo‑scoped edits; fast feedback | Install CLI, point at a dir, delegate tasks from terminal |
| **IDE Extension** | Interactive editing and previews inside your editor | Install extension, sign in; apply multi‑file diffs and open PRs |

> You can hand work off between ChatGPT (cloud) and your local environment.

---

## 4) First‑time setup (10–15 minutes)
1) Turn on Codex in your ChatGPT plan; enable Cloud/CLI/IDE.
2) Install the **CLI**; authenticate; run `codex --help`.
3) Connect **GitHub** so Codex can push branches and open PRs.
4) Verify **GPT‑5 / GPT‑5‑Codex** is selected for coding tasks.

---

## 5) Core workflows (copy‑paste playbooks)
### A) Read & explain a codebase
**Prompt:** “Scan this repo. Produce a 1‑page map of modules, public interfaces, and runtime flows. List top 5 risks and missing tests. Output markdown.”

### B) Add a feature with **SDD × TDD** (tests first)
1. **Architect:** micro‑spec, constraints, API, G/W/T tests, risks, ADR draft.  
2. **Red:** add failing unit + contract tests.  
3. **Green:** minimal change to pass specific tests.  
4. **Refactor:** internal cleanup; tests stay green.  
5. **PR + ADR:** open PR with summary, link ADR, include curl/screenshots and rollout.

### C) Large‑scale refactor (use **Codex Cloud**)
**Prompt:** “Branch `refactor/config-split`. Move config to `app/config.py` with typed settings, add tests, update docs. Open a PR with risks and rollback.”

### D) Bug hunt with reproduction
**Prompt:** “For issue #142, create a failing test that reproduces the crash, implement the minimal fix, add a regression test, and open a PR with root‑cause notes.”

---

## 6) Model choices & tuning
- **GPT‑5** = default recommendation for Codex tasks.  
- **GPT‑5‑Codex** = further‑optimized for complex, real‑world engineering (if available, prefer this).

---

## 7) Patterns that keep Codex effective (and safe)
- **Small, explicit prompts → small diffs.** Ask for “minimal change to pass test X.”
- **Always pair with tests.** Use TDD: tests first, then minimal implementation.
- **Record decisions.** Have Codex draft an **ADR** for significant changes and link it in the PR.
- **Use Agents SDK concepts** for agentic apps (tools, sessions, handoffs).
- **Deterministic CI.** Mock network calls; enforce “no green, no merge.”

---

## 8) **Best Practices (from OpenAI teams)**
Codex performs best with **structure, context, and room to iterate**. Fold these habits into your SDD × TDD loop:

### 1) Start in **Ask Mode**, then switch to **Code Mode**
For larger tasks, first prompt Codex for an **implementation plan** in Ask Mode, then feed that plan into Code Mode to generate diffs.
- Why: This two‑step flow grounds Codex and reduces errors.
- Good scope: tasks ≈ **~1 hour** of human work or a **few hundred LOC**.
- SDD mapping: Ask = **Plan (Architect)** → Code = **Red/Green/Refactor**.
**Prompt template**
```
ASK: Draft an implementation plan for <feature>. List files, APIs, tests, risks, rollback.
CODE: Using that plan, make the smallest diff to pass the tests. No unrelated refactors.
```

### 2) Iteratively harden **Codex’s execution environment**
Create a predictable workspace to lower error rates:
- Provide setup scripts (install deps, run lint/tests).
- Define required **env vars** and mocks for offline tests.
- When Codex hits build/runtime errors, fix them **in the environment** and retry.
**Prompt template**
```
Create scripts/dev_setup.sh and scripts/test.sh; add .env.sample with required vars; mock external calls so tests run offline. Re‑run the plan in this environment.
```

### 3) Write prompts like a **GitHub Issue / PR**
Codex excels when prompts mirror real tickets:
- Include **file paths**, component names, expected diff shape, doc snippets.
- Anchor to prior art: “Do it like `module_x.py`.”
- Attach acceptance criteria + test plan.
**Prompt template**
```
Title: Add SSE streaming to /chat
Files: app/main.py, app/streaming.py, tests/test_chat_streaming.py
Spec: Return text/event-stream; fallback JSON; keep API stable.
Tests: 200 JSON fallback; SSE headers; event format.
Reference: match style in app/notifications.py
Output: minimal diff + PR description + ADR draft
```

### 4) Use the **task queue** as a lightweight backlog
Capture tangents, partial work, and small fixes as **queued tasks** (one vertical slice per PR). No pressure to finish everything in one go.
**Prompt template**
```
Queue tasks:
1) Extract config to app/config.py with typed settings.
2) Add regression test for issue #142.
3) Update README with curl examples for SSE.
Each task = separate branch + PR.
```

## Quickstart: Hello World via OpenAI Agents SDK
```bash
# 1) Create project
uv init --package hello-codex && cd hello-codex

# 2) Add dependencies
uv add openai-agents python-dotenv

# 3) Minimal main.py
cat > main.py <<'PY'
import os
from dotenv import load_dotenv
from openai_agents import Agent

def main() -> None:
    load_dotenv()
    agent = Agent(model="gpt-5-codex")
    response = agent.run("Say 'Hello, Codex!' and list three SDD steps.")
    print(response)

if __name__ == "__main__":
    main()
PY

# 4) Run
uv run python main.py
```

**Back‑of‑monitor checklist**
- [ ] Plan in **Ask Mode**; implement in **Code Mode**  
- [ ] Stable env scripts + mocks; fix errors at the root  
- [ ] Prompts read like **Issues/PRs** (paths, diffs, tests, docs)  
- [ ] **Small queued tasks**; one slice per PR  
- [ ] **No green, no merge**; link **ADRs** for consequential decisions

---

## 9) When to use Cloud vs CLI vs IDE
- **Cloud:** broad, parallelizable, or long‑running work (scaffold, repo‑wide refactors, tests/docs).
- **CLI:** local, focused changes you’ll review immediately in git.
- **IDE:** interactive flow (discuss file, preview/apply diffs, open PRs).

---

## 10) Common prompts (ready to paste)
- “Explain this diff in 8 bullets and flag risky changes.”
- “Propose 3 refactor options with pros/cons; pick one and implement minimally.”
- “Convert this endpoint to SSE; add tests for headers and streaming; draft ADR ‘streaming‑protocol’.”
- “Create a PR: title, description (problem/solution), test plan, screenshots/curl, risk/rollback.”

---

## 11) Troubleshooting
- **Changed too much:** “Smallest possible diff to pass `tests/...`; no unrelated refactors.”
- **Flaky CI:** Mock externals; stabilize fixtures; add contract tests.
- **Auth/access:** Re‑authenticate Cloud/CLI/IDE; verify plan entitlements.
- **Model mismatch:** Ensure GPT‑5 / GPT‑5‑Codex is selected.

---

## 12) Level up with the OpenAI **Agents SDK**
Building agentic apps? The **Agents SDK** gives you agents, function tools, sessions, and handoffs with minimal boilerplate. Pair it with Codex for repo changes plus runtime behaviors.

---

### Final advice
Treat Codex like a **teammate who types fast**: you set the spec, tests, and limits; it does the labor. Keep changes small, test‑guarded, and documented via ADRs—and use PRs as the gate. That’s how GPT‑5‑powered development stays fast **and** clean.
