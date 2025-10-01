# Step 4b: ADR Review Gate (Post-Planning)

Goal: After `/plan`, run a deliberate Architecture Decision Record (ADR) review to reference existing ADRs and create new ones only when architecturally significant decisions were made.

## Why
- Avoids premature ADRs during business/spec stages
- Captures decisions with full context (spec + plan)
- Creates a single checkpoint before tasks/implementation

## When
```
Constitution → /specify → /plan → /adr (this step) → /tasks → /implement → /phr
```

## What to Review
- Existing ADRs relevant to this feature
- New decisions made in `plan.md`, `research.md`, `data-model.md`, `contracts/`
- Conflicts between plan and existing ADRs

## Checklist
- [ ] Is the decision architecturally significant?
- [ ] Context and rationale are clear
- [ ] Alternatives and consequences recorded
- [ ] Traceable to spec/plan requirements
- [ ] Team alignment (ADR can be Accepted)

## How to Use

Use the `/adr` command. It will:
- Analyze planning artifacts
- Reference existing ADRs in `docs/adr/`
- Create new ADRs only when needed (using the package’s deterministic flow)
- Emit a concise review report (the plan remains unchanged)

> Note: ADR creation and numbering are managed by the toolkit so teams get consistent IDs, locations, and metadata without manual steps.

## Outcomes
- Referenced or newly created ADRs in `docs/adr/`
- A review report from `/adr`
- Go/no-go decision for `/tasks`

## Common Pitfalls
- Writing ADRs for implementation details (skip)
- Duplicating existing ADRs (reference instead)
- Editing ADRs after acceptance (write a new ADR that supersedes)
