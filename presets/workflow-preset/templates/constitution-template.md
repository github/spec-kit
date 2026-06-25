{CORE_TEMPLATE}

## Change Scope Granularity

Spec Kit planning and execution MUST use R/M/U/O scope granularity:

- R: Repository / Workspace. Environment only; too broad for scoped changes.
- M: Module / Capability. Hard outer boundary.
- U: Unit / Design Object. Primary planning boundary.
- O: Operation / Detail. Execution detail.

The R/M/U/O letter mapping is fixed. Do not paraphrase, expand, rename, translate, or substitute these letters with other nouns.

Planning locks M + U.
Execution maps U -> concrete paths -> O-level changes.
If U -> concrete paths cannot be determined, report a context gap. Do not widen scope to R or broad M.

This principle applies from planning onward. Requirement specification, clarification, and checklist readiness MUST NOT infer M/U/O boundaries.

## Architecture SSOT Boundary

Ratified constitution principles are durable governance rules, not architecture fact storage.
Architecture decisions, domain facts, object design, flows, and interface contracts belong in their architecture SSOT artifacts:

- `specs/<feature>/data-model.md`: domain model and domain facts.
- `specs/<feature>/class-diagram.md`: object, module, adapter, and internal design structure.
- `specs/<feature>/contracts/sequences.md`: cross-boundary flow, sequencing, async, retry, rollback, and failure paths.
- `specs/<feature>/contracts/`: interface and message contracts.
- `specs/<feature>/research.md`: architecture decisions and tradeoffs that need evidence.

Constitution principles may reference these SSOT artifact types, but must not copy concrete implementation facts, temporary repository observations, or module responsibility inventories into ratified governance text.

## Architecture SSOT Compliance

Ratified constitution principles define the compliance rule only. Concrete architecture decisions, domain facts, object design, flows, and interface contracts MUST remain in their Architecture SSOT artifacts.

Planning outputs MUST comply with existing Architecture SSOT artifacts.
Planning MUST NOT contradict, relocate, weaken, or silently replace architecture SSOT content.
If planning cannot produce outputs that comply with existing Architecture SSOT artifacts, report a planning blocker instead of generating inconsistent artifacts.
