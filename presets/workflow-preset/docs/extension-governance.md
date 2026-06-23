# Preset Extension Governance

This document is the repository-level rule set for extending `workflow-preset`.
It exists to keep preset changes aligned with Spec Kit's preset model and this
repository's contract tests.

## Source Of Truth

- `preset.yml` declares every packaged command, template, schema, and script.
- `commands/` contains stage-local LLM instructions.
- `templates/` contains stable artifact shapes.
- `schemas/` contains machine-readable JSON contracts.
- `validators/` contains pure in-memory cross-field contract checks.
- `tests/test_preset_contract.py` is the executable contract for this preset.

## Preset Boundaries

Presets customize existing Spec Kit workflows by overriding or composing
commands, templates, and scripts. Use extensions, not presets, for new tooling,
external integrations, static analyzers, workflow runners, or commands that add
a new capability outside the existing Spec Kit workflow.

Do not reintroduce Python orchestration, workflow shell dispatch, integration
adapter scripts, or worker dispatch from scripts.

Evidence templates: packaged evidence templates are allowed preset artifacts.
Intake contract templates are also allowed when they define input shape,
completeness gates, and blocker lint rules without executing an external system.
Design Requirement Intake and Requirement Merge templates may define
provider-neutral design facts and merge reports. Figma is a provider-specific design source;
Screenshot is provider evidence and visual proof.
Screenshots must not become the primary Design Requirement Intake carrier or a source of product semantics.
Provider evidence artifacts may record screenshot refs, visual proof refs, coverage gaps, and provider evidence blockers as source facts. They must not decide visual planning readiness, proof sufficiency, accepted exception rules, checklist Gate Status, or checklist Blocking Items.
Figma MCP execution, hooks, adapter scripts, and authentication are external integration concerns and remain outside this preset.

## Template And Command Ownership

- templates own stable artifact shapes.
- commands own stage-local generation instructions.
- Commands may name the inputs they consume, the outputs they write, and the
  local update rules for their own phase.
- Do not put downstream prohibitions in upstream commands.
- Do not encode full output structures only inside command text when the output
  is intended to be durable or reused by later phases.

Stage ownership:

- `/speckit.constitution`: constitution governance and project principles only.
- `/speckit.specify`: requirement artifacts only.
- `/speckit.clarify`: requirement clarification only.
- `/speckit.checklist`: checklist artifacts and BDD/NFR/Visual Fidelity readiness gates only.
- `/speckit.plan`: Phase 0 behavior projection, planning artifacts, and formal contracts.
- `/speckit.tasks`: `tasks.md` only.
- `/speckit.analyze`: vertical consistency checks across requirements, behavior drafts, contracts, and tasks only.
- `/speckit.implement`: implementation handoff execution only.

`/speckit.tasks` owns implementation, validation, visual verification, contract validation, data-side-effect validation, integration/e2e validation, and code review task definition in `tasks.md`. `/speckit.implement` may execute those tasks and record receipt evidence, but it must not invent validation strategy, add lifecycle roles, change requirements, update contracts, or widen scope during execution.

When Design Requirement Intake or a Figma Evidence Packet has already been written into `spec.md`, `/speckit.clarify` may clarify those requirement gaps from `spec.md`, but extraction remains outside clarification.
external design extraction is not a clarification responsibility.

Visual Fidelity readiness applies to design-derived and product-side visual requirements such as pixel-perfect, brand-critical, responsive visual, or UI visual acceptance requirements. The Visual Fidelity Evidence Matrix is the single visual readiness record and uses one row per visual requirement or visual proof obligation with Source `spec.md` section, Fidelity Scope, Screenshot Level, Evidence Refs, Visual Proof Required, Blocking Item ID, and Exception Rule. It is the only artifact that decides visual planning readiness, visual proof level sufficiency, screenshot sufficiency, accepted exception rules, checklist Gate Status, and checklist Blocking Items. Provider source readiness remains separate: provider intake may prove raw metadata completeness, metadata index completeness proof, node inventory parity, and blocker lint errors, but that proof is not the Visual Fidelity readiness gate. Responsive visual requirements block PASS only when they are complex, multi-state, or declare L2 or L3 visual proof.

## Structured Artifact Rules

Machine-readable JSON artifacts are contracts, not prose examples. Stable
structured JSON artifacts require schemas in `schemas/` and focused validator
coverage in `validators/` when cross-field rules matter.

Every schema or validator added for a preset artifact must be covered by
`tests/test_preset_contract.py`.

## Behavior-first extension rule

BDD and UIF artifacts need independent templates. A behavior-first extension
must not rely only on command prose to define:

- BDD draft files.
- UIF intent files.
- data fixture intent files.
- behavior scenario draft files.
- formal BDD contracts.
- Expected UIF contracts.
- behavior scenario, fixture, and assertion contracts.

Phase 0 behavior drafts and planning-phase formal contracts must be separate
artifacts with separate owners. If they are JSON, they also need schemas and
validator coverage.

## Planning Artifact Boundaries

Keep `/speckit.plan` and `/speckit.tasks` as core-template wrappers unless the
contract tests are intentionally updated to change that rule.

Planning design artifacts remain optional and contextual:

- `class-diagram.md`
- `contracts/sequences.md`

Validation strategy is derived by `/speckit.tasks` from behavior contracts,
interface contracts, `research.md`, and `quickstart.md`. Do not add a
standalone `test-plan.md` artifact unless the preset contract is deliberately
changed for an audit or manual-review requirement.

Keep product requirements in `spec.md`, including explicit NFR assumptions;
NFR readiness belongs in `spec.md` product requirements rather than downstream
planning guesses. Keep domain model details in `data-model.md`, interface
schemas in `contracts/`, and validation run guidance in `quickstart.md`.

For visual planning, research.md records visual validation decisions only and must not duplicate the Visual Fidelity Evidence Matrix; contracts formalize visual interaction and state constraints by referencing accepted visual items, visual proof refs, and accepted exception refs; contracts/sequences.md records visual state flow only when it affects cross-boundary sequencing, async callbacks, retry, rollback, compensation, or error propagation, and must not define visual style, tokens, layout breakpoints, screenshot matrices, or validation commands.
## Handoff Extension Rules

Handoff extensions must update schema, validator, command, and cross-agent documentation together.
Any new implementation-stage artifact that Worker
Agents may read or write must be reflected in:

- `schemas/speckit.implement.*.schema.json` when the JSON contract changes.
- `validators/speckit_implement_contract.py` when cross-field validation changes.
- `commands/speckit.implement.md` when Core, Vertical Planner, or Worker
  behavior changes.
- `tests/contracts/speckit-cross-agent-subagents.md` when worker prompts, context digest rules,
  shard rules, or path rules change.
- `tests/test_preset_contract.py` for all of the above.

## Release Discipline

Do not bump preset version or release archive URLs until release preparation.
Unreleased behavior belongs under `## Unreleased` in `CHANGELOG.md`.

## Verification

After changing preset commands, templates, schemas, validators, governance docs,
or public documentation, run:

```bash
python3 -m unittest tests/test_preset_contract.py
```

If the system Python lacks development dependencies, use a local virtual
environment and the same unittest command from that environment.
