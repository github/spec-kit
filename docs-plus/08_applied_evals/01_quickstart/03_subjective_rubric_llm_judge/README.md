# Step 03 — Subjective Eval: Rubric with LLM-as-Judge

What you’ll learn
- Score subjective outputs using binary criteria (0/1) instead of pairwise comparisons.
- Reduce bias and improve calibration by summing binary checks.

Why it matters (business)
- Lets product teams define quality rubrics (e.g., compliance, tone, completeness) and track improvements objectively across releases.

How this maps to “Evaluations in 2025 (OpenAI)”
- Graders: LLM-as-judge using binary rubric checks aggregated into a total.
- UI/API: emit JSON that dashboards can ingest; use as a CI artifact.

Run
```bash
uv run python 03_subjective_rubric_llm_judge/evaluate.py --artifact-file sample.txt --rubric-file rubric.txt
```

Deliverables
- JSON with per-criterion scores and total that dashboards can ingest.
