# /speckit.constitution.check

Validate specification against project constitution.

## Trigger

Runs before `/speckit.plan` via extension hook.

## Usage

```bash
/speckit.constitution.check <feature_name> [--strict]
```

## Options

- `--strict` — Fail on any violation (default: warn)

## Checks

1. **Purpose Alignment** — Feature serves declared project purpose
2. **Principle Compliance** — No violation of core principles
3. **Architecture Fit** — Consistent with chosen patterns
4. **Governance** — Changes follow review process

## Output

```json
{
  "passed": true,
  "warnings": [],
  "violations": []
}
```

## On Failure

Blocks `/speckit.plan` until resolved.
