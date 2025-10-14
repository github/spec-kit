# Quickstart Evaluations Track

This module contains self-contained, script-first baby steps for practical evaluation workflows aligned with Andrew Ng’s guidance. Each step folder is runnable on its own with `uv` and focuses on one concept.

Prereqs
- Python 3.12+
- `uv` installed
- `.env` with at least `GEMINI_API_KEY` (see `.env.sample`)

Install (from this folder)
```bash
uv sync
```

Run examples
- Step 01 (baseline trace):
```bash
uv run python 01_baseline_trace/main.py
```

- Step 05 (component eval – preferred domains):
```bash
uv run python 05_component_eval_search_quality/eval_search.py --raw "https://arxiv.org/abs/1234 https://example.com/bad"
```

Capstone
- See `08_capstone/` for a business-connected project brief using the OpenAI Agents SDK. Build an agent workflow with evals tied to KPIs (accuracy, satisfaction, latency, cost), and present an A/B-backed recommendation.

Structure
- `shared/` tiny helpers used across steps
- `01_baseline_trace/` minimal Agents SDK call using Gemini (OpenAI-compatible)
- `02_objective_reflection_sql/` skeleton for objective reflection evals
- `03_subjective_rubric_llm_judge/` skeleton for rubric-based subjective evals
- `04_error_analysis/` skeleton for trace-anchored error analysis
- `05_component_eval_search_quality/` preferred-domains ratio evaluation
- `06_cost_latency_benchmark/` skeleton for timing/cost capture
- `07_ab_harness/` skeleton for prompt/model A/B runs

Notes
- Provider: Gemini via OpenAI-compatible API (config in `shared/config.py`).
- Langfuse/OTEL optional. If `LANGFUSE_*` present, traces can be exported.
- CI: Step 05 exits non-zero on failure; mirror this pattern where applicable so CI can gate on regressions.

See also
- Parent page “Minimal workflow (checklist)”: ../readme.md#minimal-workflow-checklist


