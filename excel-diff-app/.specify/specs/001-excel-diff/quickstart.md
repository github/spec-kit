# Quickstart - Excel Diff App

This quickstart shows how to run the Excel Diff utility once implemented.

## Install (once)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e .
```

## Example usage
```powershell
# Compare two files using ID as key and write outputs
excel-diff --base data/fileA.xlsx --compare data/fileB.xlsx --key ID --out-diff diff.csv --out-chart diff.png
```

## Development
- Run unit tests:
```powershell
pytest -q
```

## Notes
- By default, the first sheet is used. Use `--sheet` to choose another sheet.
- Use `--key` with one or more column names for composite keys.
