# GEPA Template Optimizer

This tool optimizes the prompt templates under `templates/` using DSPy’s GEPA optimizer. It generates high-quality, instruction‑first markdown templates with structural completeness and org guardrails.

## What It Does

- Scans `templates/` for `.md` files (excluding `templates/generated/`).
- Derives required sections from headings and anchors.
- Pulls guardrails from `memory/constitution.md` when present.
- Builds an instruction spec per template and uses GEPA to evolve a program that outputs improved template text.
- Writes to `templates/generated/` by default, or overwrites in place with `--in-place`.

## Usage

- Offline dev (fast, safe, no network):
  - `python3 tools/gepa/generate_templates.py --use-mock --limit 2`

- Real optimization (OpenAI example):
  - `export OPENAI_API_KEY=...`
  - `python3 tools/gepa/generate_templates.py --lm-provider openai --lm-model gpt-4o-mini --max-metric-calls 10`
  - Add `--in-place` to overwrite `templates/` once satisfied.

### .env support

You can store your secrets (e.g., `OPENAI_API_KEY=...`) in a `.env` file at the repo root. The tool will load `<repo-root>/.env` automatically if present, or you can pass a custom path via `--env-file`.

Examples:

- Create `.env` in repo root:
  ```
  OPENAI_API_KEY=sk-…
  ```
  Then run:
  ```
  python3 tools/gepa/generate_templates.py --lm-provider openai --lm-model gpt-4o-mini --max-metric-calls 10
  ```

- Use a custom env file:
  ```
  python3 tools/gepa/generate_templates.py --env-file ./local.env --lm-provider openai --lm-model gpt-4o-mini
  ```

### Flags

- `--use-mock`: run with DSPy mock LM; skips heavy GEPA and stages generated files in `templates/generated/` with a marker.
- `--lm-provider`, `--lm-model`: configure a real LLM (e.g., `openai` and `gpt-4o-mini`).
- `--max-metric-calls`: cap GEPA budget to bound runtime; pick a small value for quick validation.
- `--in-place`: overwrite originals in `templates/`.
- `--limit`: process only N files (useful for quick tests).

## How It Scores Templates

The metric encourages:
- Required sections present (based on headings and common anchors like “Success Criteria”, “Checklist”).
- Minimal placeholders such as `<...>`, `TODO`, `TBD`.
- Guard phrases from `memory/constitution.md` when available (e.g., “Don’t guess”).

The metric returns a single numeric score for GEPA aggregation.

## Troubleshooting

- “Inputs have not been set for this example”
  - Fixed by explicitly marking inputs via `.with_inputs('requirements')`. This repo already does so.

- “unsupported operand type(s) for +: 'int' and 'tuple'” during GEPA
  - Metric must return a float only; this repo’s metric does so.

- litellm complaints in mock mode
  - Don’t force GEPA with mock LM; use `--use-mock` without `--force-gepa`.
  - For real optimization, provide a valid provider and API key.

## CI Drift Check

The repo includes a GitHub Actions workflow that runs this tool in mock mode to ensure it executes cleanly. Optionally, you can enable an in‑place drift check (see the workflow file) to fail if re‑running the tool would change tracked templates.
