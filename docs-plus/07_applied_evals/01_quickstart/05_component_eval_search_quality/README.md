# Step 05 — Component Eval: Preferred Domains Ratio

Objective
- Evaluate whether research/search outputs link to preferred (trusted) domains.

Run (provide raw text containing URLs)
```bash
uv run python 05_component_eval_search_quality/eval_search.py --raw "https://arxiv.org/abs/1234 https://example.com/bad"
```

Config
- Edit `preferred_domains.yml` to change trusted domains.
- Use `--min-ratio` to change threshold.

How this maps to “Evaluations in 2025 (OpenAI)”
- Component-level eval: deterministic check with a CI-friendly non-zero exit on failure.


