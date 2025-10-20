# 001 - Excel Diff App

## Summary
Build a command-line utility and library that compares two Excel (XLSX) files and produces:
- A diff report (CSV and optional Excel) listing added rows, removed rows, and changed cells with old/new values and numeric deltas where applicable.
- A chart image (PNG) summarizing numeric differences (for example: sum of deltas per numeric column).

The tool will be usable as a CLI and as a Python library for embedding in other workflows.

## Goals
- Provide a reliable row-level diff based on a configurable key (single or composite).
- Produce clear, reviewable output suitable for reviewers (diff CSV/Excel) and stakeholders (PNG chart).
- Be testable and suitable for automation (CI-friendly CLI with exit codes and machine-readable output).

## Non-goals
- Large-scale distributed delta processing or database synchronization (out-of-scope for v1).
- Full Excel formatting fidelity in output (v1 focuses on data correctness; formatting can be added later).

## User Stories
1. As a data analyst, I want to compare two exported Excel reports and see which rows were added or removed.
2. As a product manager, I want a chart showing which numeric columns changed the most between exports.
3. As an engineer, I want a CLI that can run in CI to validate changes and return non-zero exit codes when diffs exceed thresholds.

## Acceptance Criteria
- CLI: `excel-diff --base fileA.xlsx --compare fileB.xlsx --key ID --out-diff diff.csv --out-chart diff.png` completes and writes expected outputs.
- Diff report contains: row key, column, base value, new value, delta (if numeric), and a change type where appropriate (`added`, `removed`, `changed`).
- Chart PNG is generated for numeric deltas (or an explicit message if none).
- Unit tests cover matching logic, numeric delta calculation, and missing-column handling.

## Constraints & Assumptions
- Input files will typically be small-to-medium (<= 100k rows). For larger files, the tool should fail gracefully with a suggested approach (sampling, database-backed processing).
- Default sheet: first sheet. Configurable via `--sheet`.
- Use Python ecosystem (pandas, openpyxl, matplotlib/seaborn) for rapid development.

## Security & Privacy
- Respect local file system; do not transmit file contents externally.
- Consider adding guidance for handling PII in the docs (redaction options later).
