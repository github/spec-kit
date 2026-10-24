# /speckit.plan

Generate implementation plan from ratified specification.

## Usage

```bash
/speckit.plan <feature_name> [--interactive] [--template=<name>]
```

## Options

- `--interactive` — Launch PlanCanvas in Hermes Desktop (v2)
- `--template` — Use specific template (default: plan-template.md)

## Process

1. Read ratified spec.md
2. Apply architecture decisions from constitution
3. Generate technical approach and file structure
4. Create implementation steps with testing strategy
5. Write to `.specify/specs/<feature_name>/plan.md`

## Constitution Validation

Plan must pass all constitution gates before task generation.
