# Specify Stage Prompt (from Legacy Analysis)

**Input Source**: `analysis/functional-spec.md`
**Project**: <<PROJECT_NAME>>

---

## Instructions

This stage maps legacy functionality to modern requirements.
Use `functional-spec.md` as the source of truth for WHAT the system does.

---

## Ready-to-Paste Prompt

```text
SPECIFY requirements for modernization of <<PROJECT_NAME>>.

BASE REQUIREMENTS: Use analysis/functional-spec.md

PHASING (50/30/15/5):
- Phase 1 (50%): <<List FR-CRIT-* features>>
- Phase 2 (30%): <<List FR-STD-* features>>
- Phase 3 (15%): <<List enhanced features>>
- Phase 4 (5%): <<List optional features>>

CRITICAL FEATURES (must preserve exactly):
<<FOR_EACH FR-CRIT-* from functional-spec.md>>
- <<FEATURE_NAME>>
  Evidence: <<file:line>>
  Acceptance Criteria: <<from functional-spec.md>>
<<END_FOR>>

STANDARD FEATURES (can modernize):
<<FOR_EACH FR-STD-* from functional-spec.md>>
- <<FEATURE_NAME>>
  Current: <<implementation>>
  Opportunity: <<modernization approach>>
<<END_FOR>>

LEGACY QUIRKS (decide preserve vs. fix):
<<FOR_EACH FR-QUIRK-* from functional-spec.md>>
- <<QUIRK_NAME>>
  Issue: <<description>>
  Decision: <<preserve | fix>>
<<END_FOR>>

DATA MODELS: See functional-spec.md §8
API CONTRACTS: See functional-spec.md §10

For detailed functional requirements, see analysis/functional-spec.md.
```
