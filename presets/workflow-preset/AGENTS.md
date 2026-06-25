# Codex Project Instructions

This repository is a Spec Kit community preset named `workflow-preset`.

## Project Shape

- `preset.yml` is the preset manifest and should stay aligned with the files it declares.
- `commands/` contains Spec Kit command templates.
- `templates/` contains wrapped Spec Kit templates.
- `schemas/` contains decoupled JSON schema contracts.
- `validators/` contains pure in-memory contract validators for tests.
- `tests/test_preset_contract.py` is the main contract test suite.

## Development Rules

- Preserve the preset contract tested by `tests/test_preset_contract.py`.
- Follow the Extension Governance in `docs/extension-governance.md` before adding or changing preset commands, templates, schemas, validators, handoff contracts, or behavior-first artifacts.
- Keep `/speckit.plan` and `/speckit.tasks` as core-template wrappers.
- Keep `/speckit.implement` as a replacement command with Core Agent, Vertical Planner Agent, and Worker Agent modes.
- Do not reintroduce Python orchestration, workflow shell dispatch, integration adapter scripts, or worker dispatch from scripts.
- Planning design artifacts are optional and contextual:
  - `class-diagram.md`
  - `contracts/sequences.md`
- Validation strategy is derived by `/speckit.tasks` from behavior contracts, interface contracts, `research.md`, and `quickstart.md`; do not add standalone `test-plan.md` without intentionally updating the preset contract.
- Do not move product requirements out of `spec.md`, domain model details out of `data-model.md`, interface schemas out of `contracts/`, or validation run guidance out of `quickstart.md`.

## Integration Boundary

- This repository owns the `workflow-preset` source, tests, release artifact,
  and source documentation.
- Do not open pull requests from this repository directly to `github/spec-kit`.
- Do not push branches to `github/spec-kit` or add workflow automation that
  targets `github/spec-kit` for pull requests, repository dispatches, or direct
  writes.
- If a Spec Kit catalog or bundled snapshot update is needed, target the
  `bigsmartben/spec-kit` integration fork first. The integration fork owns any
  downstream pull request to `github/spec-kit`.
- Source releases must provide source-backed metadata for the integration fork:
  repository URL, release version, source commit SHA, download URL, and
  validation evidence.

## Handoff Boundaries

When working from a generated handoff JSON:

- Treat the handoff JSON and its `context_digest_path` as primary context.
- Verify `contract_type` is `speckit.implement.handoff.v2`.
- Verify the handoff declares `agent_topology`, `lifecycle_stage`, `vertical_capability`, `capability_boundary`, `planner_outputs`, and `draft_source`.
- Verify `agent_topology.vertical_planner_agent.may_execute_implementation` is false.
- Stop before editing if `context_gaps` is not empty.
- Execute only the listed `task_ids`.
- Write only paths listed in `allowed_write_paths`.
- Do not edit `tasks.md`; write only the declared receipt and scoped task paths.
- Do not read full `spec.md`, `plan.md`, `research.md`, `contracts/`, `class-diagram.md`, or `quickstart.md` unless the handoff explicitly allows it.

## Validation

Run the focused contract tests after changes:

```bash
python3 -m unittest tests/test_preset_contract.py
```

For local preset installation checks, the `specify` CLI must be available on `PATH`.
