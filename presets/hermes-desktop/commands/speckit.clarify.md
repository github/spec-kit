# /speckit.clarify

Resolve [NEEDS CLARIFICATION] markers in a specification.

## Usage

```bash
/speckit.clarify <feature_name> [--all] [--marker=<id>]
```

## Options

- `--all` — Resolve all clarification markers interactively
- `--marker` — Resolve specific marker by ID

## Process

1. List all [NEEDS CLARIFICATION] markers in spec
2. For each marker, prompt for resolution
3. Update spec.md with resolved content
4. Re-validate constitution gates

## Constraints

- Maximum 3 clarification markers per spec
- Each resolution must be specific and testable
