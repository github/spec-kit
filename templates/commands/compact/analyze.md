---
description: Non-destructive cross-artifact consistency and quality analysis across spec.md, plan.md, and tasks.md.
scripts:
  sh: scripts/bash/check-prerequisites.sh --json --require-tasks --include-tasks
  ps: scripts/powershell/check-prerequisites.ps1 -Json -RequireTasks -IncludeTasks
---

## Input

```text
$ARGUMENTS
```

Consider user input before proceeding (if not empty).

## Constraints

**READ-ONLY**: Never modify files. Output structured analysis report only.
**Constitution** (`/memory/constitution.md`) is non-negotiable - conflicts are always CRITICAL.

## Workflow

1. Run `{SCRIPT}`, parse FEATURE_DIR. Derive SPEC, PLAN, TASKS paths. Abort if any missing.

2. **Load** minimal context from each artifact:
   - spec.md: requirements, success criteria, user stories, edge cases
   - plan.md: architecture, data model, phases, constraints
   - tasks.md: IDs, descriptions, phases, [P] markers, file paths
   - constitution: principles, MUST/SHOULD statements

3. **Build models**: Requirements inventory (FR-###, SC-###), user story/action inventory, task coverage mapping, constitution rule set.

4. **Detection passes** (max 50 findings):
   - A. **Duplication**: near-duplicate requirements
   - B. **Ambiguity**: vague terms without metrics, unresolved placeholders
   - C. **Underspecification**: missing outcomes, unaligned stories, undefined references
   - D. **Constitution alignment**: MUST principle violations, missing mandated sections
   - E. **Coverage gaps**: requirements with zero tasks, orphan tasks, unbuildable success criteria
   - F. **Inconsistency**: terminology drift, entity mismatches, ordering contradictions

5. **Severity**: CRITICAL (constitution violation, zero-coverage blocking req) > HIGH (conflicts, ambiguous security/perf) > MEDIUM (terminology drift, missing NFR tasks) > LOW (style, minor redundancy)

6. **Report** (markdown, no file writes):

   | ID | Category | Severity | Location(s) | Summary | Recommendation |
   |----|----------|----------|-------------|---------|----------------|

   + Coverage summary table + Constitution issues + Unmapped tasks + Metrics (total reqs, tasks, coverage%, ambiguity/duplication/critical counts)

7. **Next actions**: If CRITICAL → resolve before `/speckit.implement`. If LOW/MEDIUM → may proceed with suggestions.

8. **Offer remediation**: Ask user if they want concrete edit suggestions for top N issues (don't apply automatically).

Context: {ARGS}
