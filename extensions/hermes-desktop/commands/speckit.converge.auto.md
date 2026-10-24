# /speckit.converge.auto

Automatically run convergence check after implementation.

## Trigger

Runs after `/speckit.implement` via extension hook.

## Usage

```bash
/speckit.converge.auto <feature_name> [--checklist] [--fail-on-gap]
```

## Options

- `--checklist` — Run full convergence checklist
- `--fail-on-gap` — Exit non-zero if gaps found

## Process

1. Read spec.md, plan.md, tasks.md
2. Compare implementation against requirements
3. Run convergence checklist
4. Report gaps

## Output

```json
{
  "converged": true,
  "gaps": [],
  "checklist": {
    "passed": 6,
    "failed": 0,
    "items": [...]
  }
}
```

