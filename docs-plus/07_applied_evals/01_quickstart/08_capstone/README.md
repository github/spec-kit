# Step 08 — Capstone: Business-Connected Agent with Evals

Goal
- Build a small agentic workflow using the OpenAI Agents SDK (Gemini via OpenAI-compatible API) that solves a business task and includes evals wired to KPIs.

Example briefs (choose one)
- Research assistant: fetch sources, draft summary, include component-level source quality eval (preferred domains), rubric-based quality, and latency/cost snapshot.
- Invoice assistant: extract due date, include objective eval over a labeled set; add error analysis to pinpoint failure modes.
- Marketing captioner: enforce <=10-word rule; track compliance rate; add rubric for tone/brand criteria.

Requirements
- KPIs: accuracy (or rubric score), user satisfaction proxy, latency, cost sketch.
- A/B: compare two prompt configs and recommend a winner with data.
- README: how to run, decisions, and next steps.

Starter commands
```bash
uv sync
# reuse earlier steps as modules or copy minimal code
```
