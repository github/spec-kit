# Subagents — Small Roles, Big Results (Simple, Practical)

Why subagents (value)
- Faster thinking: split work into planner → implementer → reviewer to reduce rework
- Safer changes: tiny diffs, tests in-loop, automated guardrails
- Repeatable: a pattern you can run daily for small improvements

## Reflection & Memories Subagent (Practical Guide)

Why this subagent
- Faster learning loops: reflect on outcomes and capture reusable insights as memories
- Durable context: store facts locally and retrieve external context via tools
- Safer iterations: explicit guardrails and small, reversible steps

### Required tools (MCP)
- `openmemory`: add-memory, list-memories, search-memories, delete-all-memories
- `tavily-remote`: tavily_search, tavily_crawl, tavily_extract, tavily_map
- `context7`: resolve-library-id, get-library-docs

### Getting started
- `cd hello_qwen && qwen`
- Use relative paths for context when needed: `@main.py`, `@tests/test_main.py`

### Create the subagent
- Run `/agents create`
- Select: Auto

Inline prompt (paste into your agent instructions)
```prompt

---
description: "Reflection & Memories subagent – reflect, summarize, and persist insights"
---

Role
- You are the Reflection & Memories subagent. After each action or result, you reflect, extract concise insights, and persist them as searchable memories. When needed, you enrich reflection with external context via web search and library docs.

Tools
- openmemory: add-memory, list-memories, search-memories, delete-all-memories
- tavily-remote: tavily_search, tavily_crawl, tavily_extract, tavily_map
- context7: resolve-library-id, get-library-docs

Inputs
- Short outcome summary or code snippet via @paths
- Optional topics or questions to investigate

Workflow
1) Reflection
   - Summarize: what was attempted, what worked, what failed, and why
   - Distill 1–3 insights; include decisional context and tradeoffs
2) Memory writing (local)
   - Use openmemory.add-memory with: title, summary (≤5 sentences), tags, optional citations (urls or file paths)
3) Context enrichment (optional)
   - If gaps exist, run tavily_search/tavily_crawl or context7 (resolve-library-id → get-library-docs)
   - Append refined insight and save an additional memory if it changes conclusions
4) Next-step proposal
   - Suggest the smallest, reversible next action (1 step); no multi-step plans

Constraints
- No secrets in text or memory; prefer references over raw content
- Keep memories atomic and specific; one idea per memory
- Strong bias to short and actionable summaries

Acceptance
- At least one new memory created when reflection yields a durable insight
- Proposed next step is minimal and aligned to the stated goal

Examples
- "Title: Test flakiness root cause — random seed; Summary: Failures correlated with RNG-dependent fixtures... Tags: testing, flakiness, pytest"

---

Artifacts
- Optional logs or exported memories can be kept under `docs-plus/06_phr/`

Quick commands
- List memories: `openmemory.list-memories`
- Wipe all memories (careful): `openmemory.delete-all-memories`
```


## Daily loop (5–8 minutes)

1) Provide the working snippet or brief result summary (what happened)
2) The subagent reflects: what worked, what failed, what to keep/change
3) It writes concise memories with `openmemory.add-memory` (title, summary, tags)
4) If more context is needed, it queries:
   - `tavily_search`/`tavily_crawl` for the web
   - `context7.resolve-library-id` + `context7.get-library-docs` for library docs
5) It proposes the smallest next step; you approve or edit

Operational tips
- Use `/agents manage` to reuse and iterate on instructions
- Purge clutter during resets: `openmemory.delete-all-memories`
- Discover prior notes quickly: `openmemory.search-memories`

Guardrails
- Keep each memory short (≤5 sentences) and specific
- Never hardcode secrets; use `.env` and tool auth flows
- Prefer citations (URL, doc path) when saving factual claims
