# /speckit.converge

Verify implementation matches specification (convergence check).

## Usage

```bash
/speckit.converge <feature_name> [--checklist] [--diff]
```

## Options

- `--checklist` — Run convergence checklist interactively
- `--diff` — Show spec vs implementation diff

## Process

1. Read spec.md, plan.md, tasks.md
2. Compare implemented code against requirements
3. Run convergence checklist
4. Report gaps and deviations

## Hermes Desktop Integration

In Hermes Desktop, the TaskBoard convergence column shows live status.
