---
description: Wrap the core planning workflow with architecture SSOT grounding.
strategy: wrap
---

## Architecture SSOT Injection

Before running the core planning workflow, inspect these project-level architecture files if they exist:

- `.specify/memory/architecture.md`
- `.specify/memory/architecture-scenario-view.md`
- `.specify/memory/architecture-logical-view.md`
- `.specify/memory/architecture-process-view.md`
- `.specify/memory/architecture-development-view.md`
- `.specify/memory/architecture-physical-view.md`

This wrapper is a non-invasive context injection. The core planning workflow remains responsible for setup, feature analysis, technical research, design artifacts, contracts, agent-context updates, and plan reporting.

Do not change the core planning phases, required artifacts, scripts, constitution checks, research process, or output paths. Do not introduce new `ERROR` gates beyond the core planning gates.

If none of these files exist, continue with the core planning workflow without adding an architecture grounding section solely for the missing files.

If one or more files exist:

- Treat them as the architecture grounding for this planning pass: the plan must reason within the SSOT's architecture intent, boundaries, constraints, anti-patterns, and unresolved gaps.
- Extract only architecture-level conclusions: intent, stable boundaries, forbidden crossings, change axes, anti-patterns, invariants, open risks, and review triggers.
- Do not invent architecture facts when files still contain `NEEDS ARCH UPDATE`; carry the unresolved item into the plan.
- If the feature direction conflicts with the architecture SSOT, make the conflict explicit in the plan and identify the resolution path: refresh the architecture SSOT or adjust the feature plan.
- Do not run `/speckit.arch.generate` automatically.

The plan output MUST include an `Architecture Grounding` section when architecture files are present. That section is not an audit report; it records how the plan reasoning is bounded by the architecture SSOT:

- Architecture files read
- Applicable stable boundaries and forbidden crossings
- Architecture constraints or unresolved gaps that bound the plan
- Conflicts, if any, that prevent valid planning inside the current architecture SSOT, plus the required resolution path
- Architecture drift risks to watch during implementation

{CORE_TEMPLATE}

## Architecture Grounding Summary

Before finishing, summarize how architecture SSOT grounded the generated plan:

- If no architecture files were present, state that the core plan continued without architecture SSOT input.
- If architecture files were present, summarize the boundaries, forbidden crossings, unresolved architecture gaps, conflicts, and drift risks that bounded the plan reasoning.
- Do not modify architecture files from this command.
