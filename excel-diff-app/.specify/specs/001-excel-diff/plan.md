# Plan - Excel Diff App

## Chosen Technology
- Python 3.11+
- Libraries: pandas, openpyxl, matplotlib, seaborn, pytest
- CLI: argparse (initial) — consider `typer` for richer CLI later

## Architecture Overview
- `excel_diff/` package
  - `reader.py` — read Excel sheets into DataFrames (handles schemas and types)
  - `compare.py` — matching logic, row comparison, delta calculation
  - `report.py` — generate CSV/Excel outputs and chart generation
  - `cli.py` — CLI entrypoint delegating to package functions
  - `tests/` — unit tests for core logic

## Tasks (high level)
1. Project skeleton and packaging (`pyproject.toml`, package layout)
2. Implement `reader.py` (load sheet, coerce types optionally)
3. Implement `compare.py` (indexing, matching, change detection)
4. Implement `report.py` (CSV/Excel writer, chart function)
5. Implement `cli.py` and glue
6. Add unit tests for reader and compare
7. Add README quickstart and example files
8. CI: basic test run on push

## Milestones
- M1: skeleton + reader + compare base (smoke test)
- M2: report generation + charting + CLI (end-to-end)
- M3: tests and CI

## Risks
- Memory constraints for very large Excel files. If needed, suggest converting to CSV and using chunked processing or database import.

## Implementation notes
- Use DataFrame.set_index(key_cols) for matching.
- For numeric delta detection, ensure dtype coercion and robust NaN handling.
- Output Excel: use `pandas.ExcelWriter(engine='openpyxl')` for multi-sheet workbook if desired.
