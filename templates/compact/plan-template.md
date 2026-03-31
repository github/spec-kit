# Plan: [FEATURE]

branch: `[###-feature-name]` | date: [DATE] | spec: [link]
input: `/specs/[###-feature-name]/spec.md`

## Summary

[Primary requirement + technical approach]

## Technical Context

- lang: [e.g. Python 3.11]
- deps: [e.g. FastAPI]
- storage: [e.g. PostgreSQL or N/A]
- testing: [e.g. pytest]
- platform: [e.g. Linux server]
- type: [library/cli/web-service/mobile-app]
- perf: [e.g. 1000 req/s or N/A]
- constraints: [e.g. <200ms p95]
- scale: [e.g. 10k users]

## Constitution Check

[Gates from constitution file - must pass before Phase 0]

## Project Structure

### Docs (this feature)

```text
specs/[###-feature]/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md
```

### Source

```text
src/
├── models/
├── services/
├── cli/
└── lib/
tests/
├── contract/
├── integration/
└── unit/
```

Structure decision: [selected structure rationale]

## Complexity Tracking

| Violation | Why Needed | Simpler Alt Rejected |
|-----------|-----------|---------------------|
