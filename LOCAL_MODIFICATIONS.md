# Local Modifications to Spec-Kit

This document tracks modifications made to our local fork of spec-kit that differ from the upstream repository.

---

## Modification 1: Applied PR #1368 (Antigravity IDE Support)

**Date Applied:** 2026-01-04  
**Applied By:** Antigravity AI Agent  
**Upstream Status:** PR Open (pending merge)  
**Base Commit:** Not yet merged to upstream main

### Summary

Applied upstream Pull Request #1368 which adds support for Google's Antigravity IDE as an AI assistant option in the Specify CLI.

### Upstream PR Details

- **PR URL:** https://github.com/github/spec-kit/pull/1368
- **PR Author:** serhiishtokal
- **PR Date:** December 21, 2025
- **Commits:**
  - `f3ba03e` - feat: antigravity agent
  - `a8c6570` - fix: rename Antigravity to Antigravity IDE and mark as IDE-based

### Files Modified

1. `.github/workflows/scripts/create-github-release.sh` (+2 lines)
2. `.github/workflows/scripts/create-release-packages.ps1` (+8, -2 lines)
3. `.github/workflows/scripts/create-release-packages.sh` (+5, -1 lines)
4. `AGENTS.md` (+7, -1 lines)
5. `CHANGELOG.md` (+6 lines)
6. `README.md` (+5, -2 lines)
7. `pyproject.toml` (+1, -1 lines) - Version 0.0.22 → 0.0.23
8. `scripts/bash/update-agent-context.sh` (+17, -4 lines)
9. `scripts/powershell/update-agent-context.ps1` (+11, -4 lines)
10. `src/specify_cli/__init__.py` (+8, -1 lines)

### Local Modifications vs Upstream PR

**None** - PR applied as-is without modifications.

### Rationale

- Enables Antigravity IDE support in our local environment
- PR is well-implemented and follows established patterns
- No critical issues identified during evaluation
- Applied before upstream merge to gain early access to feature

### Sync Strategy

**When PR #1368 merges to upstream:**

- **Scenario 1 (PR merges as-is):** No action needed - our copy already has it
- **Scenario 2 (PR merges with changes):** Review delta, apply additional changes if needed
- **Scenario 3 (PR rejected/closed):** Maintain local implementation or revert

### Related Documentation

- Evaluation Report: `/docs/docs-local/2026-01-04/spec-kit-pr-1368-evaluation-report.md`
- OpenSpec Proposal: `/openspec/changes/evaluate-spec-kit-pr-1368/proposal.md`
- OpenSpec Design: `/openspec/changes/evaluate-spec-kit-pr-1368/design.md`
- OpenSpec Tasks: `/openspec/changes/evaluate-spec-kit-pr-1368/tasks.md`

---

## Future Modifications

_This section will be updated as additional local modifications are made._

---

**Document Version:** 1.0  
**Last Updated:** 2026-01-04  
**Maintained By:** LeonAI Development Team
