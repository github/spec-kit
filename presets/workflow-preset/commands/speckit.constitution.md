---
description: Wrap core constitution updates with change scope granularity and architecture SSOT governance.
strategy: wrap
---

## Change Scope Granularity

Always preserve the Change Scope Granularity principle in `.specify/memory/constitution.md`.

Constitution updates must not remove, weaken, or contradict the principle's R/M/U/O model, boundary timing, or context-gap rule. Keep the principle normative, including `Planning locks M + U`.

The R/M/U/O letter mapping is fixed and MUST remain exact:

- R: Repository / Workspace. Environment only; too broad for scoped changes.
- M: Module / Capability. Hard outer boundary.
- U: Unit / Design Object. Primary planning boundary.
- O: Operation / Detail. Execution detail.

Do not paraphrase, expand, rename, translate, or substitute these letters with other nouns such as Requirement, Model, User/API Interface, or Operations.

If a drafted constitution changes this mapping, discard the draft and report blocker code `CONSTITUTION_RMUO_MAPPING_DRIFT` instead of writing `.specify/memory/constitution.md`.

When producing the Sync Impact Report, report template or command file status only after checking the actual path. If a path cannot be checked, report `CONSTITUTION_TEMPLATE_STATUS_UNCHECKED`; do not report it as missing.
If the root `.specify/templates/constitution-template.md` is still the core placeholder, do not treat that as the workflow-preset template being absent. Resolve or check `.specify/presets/workflow-preset/templates/constitution-template.md` before reporting preset template status.

## Architecture SSOT Boundary

Ratified constitution principles must be durable governance rules, not architecture fact storage.
Architecture decisions, domain facts, object design, flows, and interface contracts belong in their architecture SSOT artifacts:

- `specs/<feature>/data-model.md`: domain model and domain facts.
- `specs/<feature>/class-diagram.md`: object, module, adapter, and internal design structure.
- `specs/<feature>/contracts/sequences.md`: cross-boundary flow, sequencing, async, retry, rollback, and failure paths.
- `specs/<feature>/contracts/`: interface and message contracts.
- `specs/<feature>/research.md`: architecture decisions and tradeoffs that need evidence.

Constitution updates MUST NOT capture, discover, extract, migrate, store, validate, or repair architecture facts.
If user input includes architecture facts, do not embed them in ratified principles.
In the Sync Impact Report, report blocker code `CONSTITUTION_ARCH_SSOT_GAP` and name the responsible workflow-preset SSOT artifact type when it can be classified.
Do not write concrete `specs/<feature>/...` paths, check those paths, create or update those artifacts, or copy concrete implementation facts, temporary repository observations, or module responsibility inventories into ratified constitution principles.

## Architecture SSOT Compliance

Always preserve the Architecture SSOT Compliance principle in `.specify/memory/constitution.md`.

Ratified constitution principles define the compliance rule only. Concrete architecture decisions, domain facts, object design, flows, and interface contracts MUST remain in their Architecture SSOT artifacts.

Planning outputs MUST comply with existing Architecture SSOT artifacts. Planning MUST NOT contradict, relocate, weaken, or silently replace architecture SSOT content. If planning cannot produce outputs that comply with existing Architecture SSOT artifacts, it must report a planning blocker instead of generating inconsistent artifacts.

{CORE_TEMPLATE}

## Change Scope Granularity Reporting

Before finishing, report whether the constitution includes the Change Scope Granularity principle, still states `Planning locks M + U`, preserves the exact R/M/U/O letter mapping, routes architecture decisions, domain facts, object design, flows, and interface contracts to workflow-preset SSOT artifact types instead of embedding concrete implementation content in ratified principles, and requires planning outputs to comply with existing Architecture SSOT artifacts.
