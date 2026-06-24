# Product Manager bundle

A role bundle that prepares a Spec Kit project for product managers driving
Spec-Driven Development: discovery, specification, and roadmap planning.

## What it installs

- **Extension** `agent-context` — keeps the agent context file in sync.
- **Preset** `product-discovery` (priority 10, append) — discovery-oriented
  command set.
- **Steps** `draft-spec`, `review-spec` — specification authoring steps.
- **Workflow** `spec-to-roadmap` — turns an approved spec into a roadmap.

This bundle is **integration-agnostic**: it inherits whatever integration the
project already uses (e.g. `copilot`, `claude`).

## Usage

```bash
specify bundle validate --path examples/bundles/product-manager
specify bundle build --path examples/bundles/product-manager --output dist/
```
