# Applied Evals | Build an Agentic AI System with SpecifyPlus Evals Extension

> The single biggest predictor of whether someone can build effectively is whether they know how to drive a disciplined process for evals and error analysis. Teams that don’t know how to do this can spend months tweaking agents with little progress to show for it. Instead of guessing what to work on, you'll let evals data guide you. ([The Batch](https://www.deeplearning.ai/the-batch/issue-322/))

### What this step covers
- **Goal**: Make evals a first‑class part of your agent development—treat them like tests and gates.
- **Outcome**: A small, living evaluation suite with clear pass/fail criteria, wired into CI.

### Evaluations in 2025 (OpenAI)
- **Datasets**: Curate/version example sets; grow them from production samples and edge cases.
- **Graders**: Combine rubric‑based LLM graders with deterministic checks (exact/regex/JSON/function).
- **Trace grading**: Inspect end‑to‑end agent traces to locate failing steps, tool calls, or prompts.
- **Baselines and deltas**: Compare PR runs to a baseline; fail CI on quality or safety regressions.
- **UI + API**: Use the Evaluate UI for triage and the API/SDKs to automate runs in CI.

See: OpenAI “Evaluate” docs → [Getting started](https://platform.openai.com/docs/guides/evaluation-getting-started?api-mode=responses).

### Evals and error analysis
- **Evals quantify** whether you’re meeting explicit quality and safety goals (scores, pass/fail, deltas vs. baseline).
- **Error analysis diagnoses** why failures happen. Use traces to pinpoint which step/tool/prompt broke.
- Maintain a simple taxonomy (e.g., retrieval miss, tool misuse, formatting error, guardrail trip) and tag failures.
- Convert tagged failures into new dataset cases; prioritize recurring categories to raise impact fastest.

### Minimal workflow (checklist)
- [ ] **Define the task**: What does “good” look like? Write crisp acceptance criteria.
- [ ] **Seed a dataset**: 10–20 real examples; include tricky/negative cases you actually see.
- [ ] **Add graders**: One rubric LLM grader + at least one deterministic metric.
- [ ] **Set thresholds**: E.g., accuracy ≥ X%, zero critical safety violations.
- [ ] **Baseline**: Run once and mark as baseline for future comparisons.
- [ ] **Wire CI**: Run on PR; compare to baseline; block on regressions.
- [ ] **Triage with traces**: Drill into failing steps; fix prompts/tools/code; re‑run.
- [ ] **Grow the dataset**: Add newly discovered failures and corner cases.


### Notes
- Keep evals small but representative. Grow them weekly; prioritize bugs from real usage.
- Treat evals as quality contracts—change them deliberately and review deltas.
- Store datasets with your code; version them; avoid leaking any secrets.

### Further learning
- Discipline for evals and error analysis: [The Batch](https://www.deeplearning.ai/the-batch/issue-322/)
- Course: [Agentic AI](https://www.deeplearning.ai/courses/agentic-ai/)
- OpenAI: [Evaluate — Getting started](https://platform.openai.com/docs/guides/evaluation-getting-started?api-mode=responses)