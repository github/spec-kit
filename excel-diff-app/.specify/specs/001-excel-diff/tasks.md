# Tasks - Excel Diff App

## 001 Project skeleton
- [ ] Create package `excel_diff/` with `__init__.py` and `cli.py` entrypoint
- [ ] Add `pyproject.toml` (or reuse root) and requirements for the project

## 002 Reader
- [ ] Implement `excel_diff/reader.py`:
  - [ ] read sheet into DataFrame
  - [ ] optional column type hints
  - [ ] tests for different sheet names and missing columns

## 003 Compare
- [ ] Implement `excel_diff/compare.py`:
  - [ ] index by key(s)
  - [ ] detect added/removed rows
  - [ ] detect changed cells with old/new/delta
  - [ ] tests for number, string, and NA changes

## 004 Report
- [ ] Implement `excel_diff/report.py`:
  - [ ] write diff CSV
  - [ ] write optional Excel workbook
  - [ ] generate PNG chart for numeric deltas
  - [ ] tests for chart generation (mock data)

## 005 CLI
- [ ] Implement `excel_diff/cli.py` wiring to above modules
- [ ] Add console messages and exit codes

## 006 Tests & CI
- [ ] Add `tests/` with pytest
- [ ] Add GitHub Actions workflow to run tests

## 007 Docs & Examples
- [ ] quickstart README
- [ ] sample Excel files in `examples/` (small synthetic data)

## 008 Polish
- [ ] Add logging and error handling
- [ ] Consider replacing argparse with `typer` for richer CLI
- [ ] Add threshold parameter to fail CI when diffs exceed a limit
