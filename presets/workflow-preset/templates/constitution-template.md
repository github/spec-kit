{CORE_TEMPLATE}

## Change Scope Granularity

Spec Kit planning and execution MUST use R/M/U/O scope granularity:

- R: Repository / Workspace. Environment only; too broad for scoped changes.
- M: Module / Capability. Hard outer boundary.
- U: Unit / Design Object. Primary planning boundary.
- O: Operation / Detail. Execution detail.

Planning locks M + U.
Execution maps U -> concrete paths -> O-level changes.
If U -> concrete paths cannot be determined, report a context gap. Do not widen scope to R or broad M.

This principle applies from planning onward. Requirement specification, clarification, and checklist readiness MUST NOT infer M/U/O boundaries.
