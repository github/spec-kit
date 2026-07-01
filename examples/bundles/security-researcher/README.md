# Security Researcher bundle

A role bundle for security researchers practicing Spec-Driven Development:
threat modeling, security review, and compliance.

## What it installs

- **Extension** `agent-context` — keeps the agent context file in sync.
- **Preset** `security-compliance` (priority 5, append) — security and
  compliance command set; presets apply in ascending priority order, so this
  low number (5) places it ahead of higher-numbered presets in the stack.
- **Steps** `threat-model`, `security-review`.
- **Workflow** `secure-sdd` — a security-first SDD workflow.

This bundle is **integration-agnostic**: it inherits the project's active
integration.

## Usage

```bash
specify bundle validate --path examples/bundles/security-researcher
specify bundle build --path examples/bundles/security-researcher --output dist/
```
