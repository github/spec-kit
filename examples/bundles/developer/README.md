# Developer bundle

A role bundle for developers practicing Spec-Driven Development: implementation
planning, task breakdown, and code review.

## What it installs

- **Extension** `agent-context` — keeps the agent context file in sync.
- **Preset** `implementation-planning` (priority 10, append) — implementation
  planning command set.
- **Steps** `plan-implementation`, `break-down-tasks`.
- **Workflow** `spec-to-implementation` — drives a spec through to code.

This bundle is **integration-agnostic**: it inherits the project's active
integration.

## Usage

```bash
specify bundle validate --path examples/bundles/developer
specify bundle build --path examples/bundles/developer --output dist/
```
