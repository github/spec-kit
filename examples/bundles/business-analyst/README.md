# Business Analyst bundle

A role bundle for business analysts working in a Spec-Driven Development flow:
requirements elicitation, traceability, and acceptance criteria.

## What it installs

- **Extension** `agent-context` — keeps the agent context file in sync.
- **Preset** `requirements-elicitation` (priority 10, append) — elicitation and
  analysis command set.
- **Steps** `capture-requirements`, `trace-acceptance-criteria`.
- **Workflow** `requirements-to-spec` — turns captured requirements into a spec.

This bundle is **integration-agnostic**: it inherits the project's active
integration.

## Usage

```bash
specify bundle validate --path examples/bundles/business-analyst
specify bundle build --path examples/bundles/business-analyst --output dist/
```
