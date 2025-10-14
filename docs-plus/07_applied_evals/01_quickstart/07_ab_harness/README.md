# Step 07 — A/B Harness (Prompts/Models)

What you’ll learn
- Run multiple configurations over the same prompt and collect outputs.
- Prepare for offline comparison using objective/subjective evaluators.

Why it matters (business)
- Turns prompt/model choices into measurable experiments; supports data-driven product decisions.

How this maps to “Evaluations in 2025 (OpenAI)”
- Baselines/deltas: compare variants vs a baseline; feed outputs to graders for objective/subjective scoring.

Run
```bash
uv run python 07_ab_harness/run_ab.py --matrix-file configs.json --prompt "Why are evals important?"
```

Matrix file (example JSON)
```json
[
  {"name": "Concise", "instructions": "Answer in one sentence.", "model": "gemini-2.5-flash"},
  {"name": "Detailed", "instructions": "Answer in two short sentences.", "model": "gemini-2.5-flash"}
]
```
