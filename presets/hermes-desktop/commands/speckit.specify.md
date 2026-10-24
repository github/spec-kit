# /speckit.specify

Create a new feature specification from requirements.

## Usage

```bash
/speckit.specify <feature_name> [--interactive] [--template=<name>]
```

## Options

- `--interactive` — Launch SpecBuilder pane in Hermes Desktop
- `--template` — Use specific template (default: spec-template.md)

## Process

1. Collect requirements (scenarios, FRs, entities)
2. Identify clarifications (max 3 [NEEDS CLARIFICATION])
3. Validate against constitution gates
4. Write to `.specify/specs/<feature_name>/spec.md`

## Hermes Desktop Integration

In Hermes Desktop, this command opens the SpecBuilder pane.
