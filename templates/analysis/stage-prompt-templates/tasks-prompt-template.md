# Tasks Stage Prompt (from Legacy Analysis)

**Project**: <<PROJECT_NAME>>
**Input**: Requirements from specify stage

---

## Task Breakdown Guidance (with Legacy Complexity)

Use legacy code analysis to estimate task complexity accurately.

---

## Complexity Hints from Legacy Analysis

### High Complexity Areas (from code analysis)

<<FOR_EACH complex area>>

**<<AREA_NAME>>** (e.g., "Payment Processing")

- Files: <<list of files>>
- LOC: <<N>> lines
- Dependencies: <<list external deps>>
- Complexity: <<cyclomatic complexity, nested levels>>
- Estimated effort: <<HIGH>> (requires careful migration)

<<END_FOR>>

### Medium Complexity Areas

<<Similar structure>>

### Low Complexity Areas

<<Similar structure>>

---

## Migration-Specific Tasks

These tasks are specific to modernization (not greenfield):

1. **Data Migration Tasks**
   - Schema conversion (<<legacy DB>> → <<target DB>>)
   - Data backfill (historical data)
   - Reconciliation verification
   - Effort: <<estimate based on table count, row count>>

2. **Dual-Write Implementation**
   - Write to both legacy and new system
   - Consistency checks
   - Effort: <<estimate based on write endpoints>>

3. **Cutover Tasks**
   - Traffic routing (canary, blue-green)
   - Rollback procedures
   - Monitoring dashboards

---

## Ready-to-Paste Prompt

```text
TASKS breakdown for modernization of <<PROJECT_NAME>>.

COMPLEXITY GUIDANCE (from legacy code analysis):
- High complexity: <<list areas with LOC, dependencies>>
- Medium complexity: <<list areas>>
- Low complexity: <<list areas>>

MODERNIZATION-SPECIFIC TASKS:
1. Setup infrastructure (<<USER_CHOICE_DEPLOYMENT>>)
2. Data migration planning
   - Schema: <<N>> tables to migrate
   - Data: <<M>> GB historical data
3. Service migration (by phase):
   - P1: <<critical services>>
   - P2: <<standard services>>
4. Integration migration
   - External: <<list integrations>>
5. Cutover & rollback procedures

TESTING REQUIREMENTS (<<USER_CHOICE_TESTING>>):
- Unit tests: <<target coverage%>>
- Integration tests: <<key scenarios>>
- E2E tests: <<critical workflows>>

Refer to technical-spec.md §12 for detailed migration plan.
Break down each phase into 2-week sprints.
```text
