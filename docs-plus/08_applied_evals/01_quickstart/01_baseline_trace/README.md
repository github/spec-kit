# Step 01 — Baseline Trace (Trace Grading Basics)

Purpose
- Run a single OpenAI Agents SDK request using Gemini via OpenAI-compatible API.
- Optionally export traces to Langfuse if credentials are present.

How this maps to “Evaluations in 2025 (OpenAI)”
- Trace grading: capture an end-to-end trace to inspect later when triaging failures.

Run
```bash
uv run python 01_baseline_trace/main.py
```

Env
- `.env` in repo root or this folder with `GEMINI_API_KEY`.
- Optional: `LANGFUSE_PUBLIC_KEY`, `LANGFUSE_SECRET_KEY`, `LANGFUSE_HOST`.


