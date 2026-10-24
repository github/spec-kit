# /speckit.analyze

Analyze codebase impact for planned tasks.

## Usage

```bash
/speckit.analyze <feature_name> [--tasks=<ids>] [--deep]
```

## Options

- `--tasks` — Analyze specific task IDs
- `--deep` — Full dependency graph analysis

## Output

- Affected files and modules
- Risk assessment
- Recommended implementation order
- Test coverage gaps
