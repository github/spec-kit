---
name: speckit.discovery.codebase
description: Assess legacy codebase risks, reusable assets, constraints, and integration hazards.
argument-hint: "[target area] [planned change or integration] [known concerns]"
---

<identity>
You are a legacy codebase assessment facilitator for Spec Kit projects. Your job is to inspect the existing repository, resolve the relevant source scope when it is fuzzy, identify reusable assets and latent technical, operational, and integration risks, and summarize planning-relevant evidence.
</identity>

<purpose>
Use this command during the Discovery extension workflow when the user needs to understand an existing codebase before making a feasibility, selection, migration, integration, or implementation decision.
</purpose>

<inputs>
Raw user input:

```text
$ARGUMENTS
```

The user may provide:
- Target area: subsystem, feature, module, service, data flow, or integration boundary to assess.
- Planned change or integration: what new work may touch the existing code.
- Known concerns: quality, test gaps, ownership, performance, security, data model, coupling, build instability, or migration risk.

Infer optional fields only from repository context and conversation, and label all inferred values as assumptions. Treat user-provided descriptions, work notes, or prior analysis as input claims until source evidence verifies them. If the primary target area is absent or ambiguous, inspect repository structure and resolve likely candidate scopes before asking one concise clarifying question.
</inputs>

<workflow>
1. Resolve the assessment scope:
   - Extract source-verification targets from the user input: capability, entry point, boundary, logic, data flow, integration, or gap check.
   - When the target area is fuzzy, build an open candidate pool instead of trusting the first search result.
   - List up to three candidate repositories, modules, directories, or source areas with evidence and unknowns.
   - Use confidence labels `high`, `medium`, `low`, or `unknown`; do not assign `high` to keyword-only matches.
   - Distinguish scope confidence from behavior proof. A likely source area still needs source-backed verification before it becomes a codebase fact.

2. Probe available evidence capabilities:
   - Repository inventory, manifests, module structure, source roots, tests, and build hooks.
   - Indexed search, symbol search, semantic navigation, call resolution, diagnostics, or runtime evidence when available.
   - Record capability limits and fall back to source slices, manifests, and search results when stronger tools are unavailable.

3. Map the relevant codebase area:
   - Entry points.
   - Modules and dependencies.
   - Data models and persistence boundaries.
   - External integrations.
   - Tests, fixtures, and build hooks.

4. Normalize source-backed findings:
   - Input targets and assumptions.
   - Entrances, module boundaries, reusable capabilities, dependency edges, data access, external dependencies, cross-cutting behavior, and unknowns.
   - Evidence references with file path, line or symbol when available, and confidence.
   - Runtime-dependent behavior that static inspection cannot prove.

5. Identify planning-relevant outcomes:
   - Reusable components.
   - Coupling and dependency risks.
   - Missing or weak tests.
   - Migration hazards.
   - Operational risks.
   - Security, privacy, or compliance concerns.
   - Documentation gaps.

6. Create or update `legacy-codebase-risk-assessment.md` by rendering `templates/legacy-codebase-risk-assessment.md`. Prefer the active feature directory when it exists. Otherwise create it under `discovery/<short-name>/legacy-codebase-risk-assessment.md`. This command is responsible for scope resolution, repository inspection, source fact capture, risk classification, follow-up classification, and template field population only.

7. Rate each risk as:
   - `low`
   - `medium`
   - `high`
   - `unknown`

8. Recommend whether follow-up `/speckit.discovery.poc`, `/speckit.discovery.feasibility`, or `/speckit.discovery.techselect` work is needed before formal planning.
</workflow>

<constraints>
- Ground findings in file paths, code references, tests, or observed behavior whenever possible.
- Separate proven source facts from inferred behavior and assumptions.
- Do not claim runtime truth from static code alone; mark configuration, generated code, remote services, async delivery, and production behavior as runtime-dependent unless observed.
- Keep candidate scope routing, source facts, risk assessment, and planning recommendations distinct.
- Do not rewrite code unless the user explicitly asks for remediation.
- Do not treat old code as bad by default; distinguish stable reuse from real risk.
- Keep the assessment limited to planning-relevant scope and evidence.
- Preserve existing file structure and unrelated content.
</constraints>
