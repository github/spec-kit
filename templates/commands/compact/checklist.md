---
description: Generate a custom checklist for the current feature - "unit tests for requirements writing".
scripts:
  sh: scripts/bash/check-prerequisites.sh --json
  ps: scripts/powershell/check-prerequisites.ps1 -Json
---

## Input

```text
$ARGUMENTS
```

Consider user input before proceeding (if not empty).

## Core Concept

Checklists are **unit tests for requirements** - they validate quality, clarity, and completeness of requirements, NOT implementation behavior.

- YES: "Are visual hierarchy requirements defined?" / "Is 'fast' quantified with metrics?"
- NO: "Verify button clicks" / "Test error handling works"

## Workflow

1. **Setup**: Run `{SCRIPT}`, parse FEATURE_DIR and AVAILABLE_DOCS.

2. **Clarify intent**: Generate up to 3 contextual questions from user phrasing + spec signals (scope, depth, audience, risk). Skip if already clear from $ARGUMENTS. May ask 2 follow-ups if gaps remain (max 5 total).

3. **Load context**: Read spec.md, plan.md (if exists), tasks.md (if exists) - only relevant portions.

4. **Generate checklist**:
   - Create `FEATURE_DIR/checklists/[domain].md`
   - If exists: append continuing from last CHK ID. Never delete existing content.
   - Group by: Completeness, Clarity, Consistency, Measurability, Coverage, Edge Cases, NFRs, Dependencies, Ambiguities
   - Each item: question format about requirement quality with [dimension] tag
   - Include traceability refs: `[Spec §X.Y]`, `[Gap]`, `[Ambiguity]`, `[Conflict]`
   - Soft cap: 40 items, merge near-duplicates, consolidate low-impact edge cases

5. **Report**: Path, item count, focus areas, whether created or appended.

## Item Format

```
- [ ] CHK### Are [requirement type] defined/specified for [scenario]? [Dimension, Spec §X.Y]
```

Patterns: "Are X defined?" / "Is X quantified?" / "Are X consistent between A and B?" / "Can X be measured?" / "Does spec define X?"

Prohibited: "Verify", "Test", "Confirm" + implementation behavior / "Displays correctly" / "Click", "navigate", "render"
