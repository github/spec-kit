---
description: Archive a completed feature specification and update system documentation
scripts:
  sh: scripts/bash/archive-feature.sh --json "{ARGS}"
  ps: scripts/powershell/archive-feature.ps1 -Json "{ARGS}"
---

Archive the completed feature specification:

## What This Does

Moves a completed feature specification to the archive directory:
1. Creates timestamped archive directory
2. Moves all specification artifacts
3. Generates completion report
4. Updates system documentation (if applicable)

## Usage

**From feature branch:**
```bash
/archive
```

**With explicit feature ID:**
```bash
/archive proj-123.feature-name
```

## What Gets Archived

- spec.md (feature specification)
- plan.md (implementation plan)
- tasks.md (task breakdown)
- research.md (research findings)
- data-model.md (data models)
- contracts/ (API specifications)
- All capability subdirectories (if decomposed)

## Archive Location

```
archive/
└── [feature-id]-[timestamp]/
    ├── completion-report.md
    └── [all spec artifacts]
```

## Completion Report

The archive command generates a completion report documenting:
- When the feature was archived
- What artifacts were included
- Original specification location
- Feature completion status

## Use Cases

- Feature development completed and merged
- Cleaning up specs/ directory after PR merge
- Creating historical record of feature evolution
- Preparing for new feature work

## Notes

- Feature must be complete before archiving
- Archive is permanent (requires manual restore)
- Original git history preserved
- Can reference archived specs in future work

**When to archive:**
- After PR merged to main
- After feature deployed to production
- When feature work fully complete

**When NOT to archive:**
- Feature still in development
- PR not yet merged
- Need to reference frequently
