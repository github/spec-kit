# /speckit.constitution

Run the Constitution Wizard to create or update the project constitution.

## Usage

```bash
/speckit.constitution [--init] [--review] [--amend]
```

## Options

- `--init` — Start new constitution wizard (5-step guided flow)
- `--review` — Review current constitution against active specs
- `--amend` — Propose amendment to existing constitution

## Wizard Steps

1. **Purpose** — Select from 9 purposes or define custom
2. **Principles** — Choose 3-5 core principles
3. **Architecture** — Select from 25 architecture options
4. **Governance** — Define review/amendment process
5. **Ratify** — Review and confirm

## Output

Writes to `.specify/memory/constitution.md`

## Hermes Desktop Integration

In Hermes Desktop, this command launches the ConstitutionWizard pane.
