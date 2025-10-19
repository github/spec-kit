# Step 04 — Error Analysis (Trace-driven)

What you’ll learn
- Aggregate where failures occur across components (search, fetch, rank, write).
- Tally counts to decide where to invest next.

Why it matters (business)
- Ensures engineering time targets the bottleneck that most impacts outcomes. Avoids spending weeks on the wrong component.

How this maps to “Evaluations in 2025 (OpenAI)”
- Trace grading + taxonomy: tag failures by component and feed new cases back into datasets.

Run
```bash
uv run python 04_error_analysis/analyze_errors.py --input-csv errors.csv
```

Input CSV schema
- example_id, component, error (yes/no)
