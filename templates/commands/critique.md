---
description: Perform a dual-lens critical review of the specification and plan from both product strategy and engineering risk perspectives before implementation.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -IncludeTasks
---

## User Input

```text
$ARGUMENTS
```

You **MUST** consider the user input before proceeding (if not empty).

## Pre-Execution Checks

**Check for extension hooks (before critique)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.before_critique` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Pre-Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```
  - **Mandatory hook** (`optional: false`):
    ```
    ## Extension Hooks

    **Automatic Pre-Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}

    Wait for the result of the hook command before proceeding to the Outline.
    ```
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently

## Goal

Challenge the specification and implementation plan through two distinct expert lenses BEFORE committing to implementation. The **Product Lens** evaluates whether the right problem is being solved in the right way for users. The **Engineering Lens** evaluates whether the technical approach is sound, scalable, and free of hidden risks. This dual review prevents costly mid-implementation pivots and catches strategic and technical blind spots early.

## Operating Constraints

**STRICTLY READ-ONLY FOR EXISTING ARTIFACTS**: During this command, do **not** directly modify existing project files such as `spec.md`, `plan.md`, or other source/docs. You **may** create a new critique report under `FEATURE_DIR/critiques/critique-{timestamp}.md`. Propose, but do not apply, edits to `spec.md`/`plan.md`; applying any changes requires explicit user approval in a follow-up step or command after the user reviews the findings.

**CONSTRUCTIVE CHALLENGE**: The goal is to strengthen the spec and plan, not to block progress. Every critique item must include a constructive suggestion for improvement.

**Constitution Authority**: The project constitution (`/memory/constitution.md`) defines non-negotiable principles. Any spec/plan element conflicting with the constitution is automatically a 🎯 Must-Address item.

## Outline

1. Run `{SCRIPT}` from repo root and parse FEATURE_DIR and AVAILABLE_DOCS list. All paths must be absolute. For single quotes in args like "I'm Groot", use escape syntax: e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").

2. **Load Critique Context**:
   - **REQUIRED**: Read `spec.md` for requirements, user stories, and acceptance criteria
   - **REQUIRED**: Read `plan.md` for architecture, tech stack, and implementation phases
   - **IF EXISTS**: Read `/memory/constitution.md` for governing principles
   - **IF EXISTS**: Read `tasks.md` for task breakdown (if already generated)
   - **IF EXISTS**: Read previous critique reports in FEATURE_DIR/critiques/ for context

3. **Product Lens Review** (CEO/Product Lead Perspective):

   Adopt the mindset of an experienced product leader who cares deeply about user value, market fit, and business impact. Evaluate:

   #### 3a. Problem Validation
   - Is the problem statement clear and well-defined?
   - Is this solving a real user pain point, or is it a solution looking for a problem?
   - What evidence supports the need for this feature? (user research, data, customer requests)
   - Is the scope appropriate — not too broad (trying to do everything) or too narrow (missing the core value)?

   #### 3b. User Value Assessment
   - Does every user story deliver tangible user value?
   - Are the acceptance criteria written from the user's perspective (outcomes, not implementation)?
   - Is the user journey complete — or are there gaps where users would get stuck?
   - What's the simplest version that would deliver 80% of the value? (MVP analysis)
   - Are there unnecessary features that add complexity without proportional value?

   #### 3c. Alternative Approaches
   - Could a simpler solution achieve the same outcome?
   - Are there existing tools, libraries, or services that could replace custom implementation?
   - What would a competitor's approach look like?
   - What would happen if this feature were NOT built? What's the cost of inaction?

   #### 3d. Edge Cases & User Experience
   - What happens when things go wrong? (error states, empty states, loading states)
   - How does this feature interact with existing functionality?
   - Are accessibility considerations addressed?
   - Is the feature discoverable and intuitive?
   - What are the onboarding/migration implications for existing users?

   #### 3e. Success Measurement
   - Are the success criteria measurable and time-bound?
   - How will you know if this feature is successful after launch?
   - What metrics should be tracked?
   - What would trigger a rollback decision?

4. **Engineering Lens Review** (Staff Engineer Perspective):

   Adopt the mindset of a senior staff engineer who has seen projects fail due to hidden technical risks. Evaluate:

   #### 4a. Architecture Soundness
   - Does the architecture follow established patterns for this type of system?
   - Are boundaries and interfaces well-defined (separation of concerns)?
   - Is the architecture testable at each layer?
   - Are there circular dependencies or tight coupling risks?
   - Does the architecture support future evolution without major refactoring?

   #### 4b. Failure Mode Analysis
   - What are the most likely failure modes? (network failures, data corruption, resource exhaustion)
   - How does the system degrade gracefully under each failure mode?
   - What happens under peak load? Is there a scaling bottleneck?
   - What are the blast radius implications — can a failure in this feature affect other parts of the system?
   - Are retry, timeout, and circuit-breaker strategies defined?

   #### 4c. Security & Privacy Review
   - What is the threat model? What attack vectors does this feature introduce?
   - Are trust boundaries clearly defined (user input, API responses, third-party data)?
   - Is sensitive data handled appropriately (encryption, access control, retention)?
   - Are there compliance implications (GDPR, SOC2, HIPAA)?
   - Is the principle of least privilege followed?

   #### 4d. Performance & Scalability
   - Are there potential bottlenecks in the data flow?
   - What are the expected data volumes? Will the design handle 10x growth?
   - Are caching strategies appropriate and cache invalidation well-defined?
   - Are database queries optimized (indexing, pagination, query complexity)?
   - Are there resource-intensive operations that should be async or batched?

   #### 4e. Testing Strategy
   - Is the testing plan comprehensive (unit, integration, E2E)?
   - Are the critical paths identified for priority testing?
   - Is the test data strategy realistic?
   - Are there testability concerns (hard-to-mock dependencies, race conditions)?
   - Is the test coverage target appropriate for the risk level?

   #### 4f. Operational Readiness
   - Is observability planned (logging, metrics, tracing)?
   - Are alerting thresholds defined?
   - Is there a rollback strategy?
   - Are database migrations reversible?
   - Is the deployment strategy clear (blue-green, canary, feature flags)?

   #### 4g. Dependencies & Integration Risks
   - Are third-party dependencies well-understood (stability, licensing, maintenance)?
   - Are integration points with existing systems well-defined?
   - What happens if an external service is unavailable?
   - Are API versioning and backward compatibility considered?

5. **Cross-Lens Synthesis**:
   Identify items where both lenses converge (these are highest priority):
   - Product simplification that also reduces engineering risk
   - Engineering constraints that affect user experience
   - Scope adjustments that improve both value delivery and technical feasibility

6. **Severity Classification**:
   Classify each finding:

   - 🎯 **Must-Address**: Blocks proceeding to implementation. Critical product gap, security vulnerability, architecture flaw, or constitution violation. Must be resolved before `/speckit.tasks`.
   - 💡 **Recommendation**: Strongly suggested improvement that would significantly improve quality, value, or risk profile. Should be addressed but won't block progress.
   - 🤔 **Question**: Ambiguity or assumption that needs stakeholder input. Cannot be resolved by the development team alone.

7. **Generate Critique Report**:
   Ensure the directory `FEATURE_DIR/critiques/` exists (create it if necessary), then create the critique report at `FEATURE_DIR/critiques/critique-{timestamp}.md` using `templates/critique-template.md` as the required structure. The report must include:

   - **Executive Summary**: Overall assessment and readiness to proceed
   - **Product Lens Findings**: Organized by subcategory (3a-3e)
   - **Engineering Lens Findings**: Organized by subcategory (4a-4g)
   - **Cross-Lens Insights**: Items where both perspectives converge
   - **Findings Summary Table**: All items with ID, lens, severity, summary, suggestion

   **Findings Table Format**:
   | ID | Lens | Severity | Category | Finding | Suggestion |
   |----|------|----------|----------|---------|------------|
   | P1 | Product | 🎯 | Problem Validation | No evidence of user need | Conduct 5 user interviews or reference support tickets |
   | E1 | Engineering | 💡 | Failure Modes | No retry strategy for API calls | Add exponential backoff with circuit breaker |
   | X1 | Both | 🎯 | Scope × Risk | Feature X adds complexity with unclear value | Defer to v2; reduces both scope and technical risk |

8. **Provide Verdict**:
   Based on findings, provide one of:
   - ✅ **PROCEED**: No must-address items. Spec and plan are solid. Run `/speckit.tasks` to proceed.
   - ⚠️ **PROCEED WITH UPDATES**: Must-address items found but are resolvable. Offer to apply fixes to spec/plan, then proceed.
   - 🛑 **RETHINK**: Fundamental product or architecture concerns. Recommend revisiting the spec with `/speckit.specify` or the plan with `/speckit.plan`.

9. **Offer Remediation**:
   For each must-address item and recommendation:
   - Provide a specific suggested edit to `spec.md` or `plan.md`
   - Ask: "Would you like me to apply these changes? (all / select / none)"
   - If user approves, apply changes to the relevant files
   - After applying changes, recommend re-running `/speckit.critique` to verify

## Post-Critique Actions

Suggest next steps based on verdict:
- If PROCEED: "Run `/speckit.tasks` to break the plan into actionable tasks"
- If PROCEED WITH UPDATES: "Review the suggested changes, then run `/speckit.tasks`"
- If RETHINK: "Consider running `/speckit.specify` to refine the spec or `/speckit.plan` to revise the architecture"

**Check for extension hooks (after critique)**:
- Check if `.specify/extensions.yml` exists in the project root.
- If it exists, read it and look for entries under the `hooks.after_critique` key
- If the YAML cannot be parsed or is invalid, skip hook checking silently and continue normally
- Filter out hooks where `enabled` is explicitly `false`. Treat hooks without an `enabled` field as enabled by default.
- For each remaining hook, do **not** attempt to interpret or evaluate hook `condition` expressions:
  - If the hook has no `condition` field, or it is null/empty, treat the hook as executable
  - If the hook defines a non-empty `condition`, skip the hook and leave condition evaluation to the HookExecutor implementation
- For each executable hook, output the following based on its `optional` flag:
  - **Optional hook** (`optional: true`):
    ```
    ## Extension Hooks

    **Optional Hook**: {extension}
    Command: `/{command}`
    Description: {description}

    Prompt: {prompt}
    To execute: `/{command}`
    ```
  - **Mandatory hook** (`optional: false`):
    ```
    ## Extension Hooks

    **Automatic Hook**: {extension}
    Executing: `/{command}`
    EXECUTE_COMMAND: {command}
    ```
- If no hooks are registered or `.specify/extensions.yml` does not exist, skip silently
