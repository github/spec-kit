# OpenSpec Change: Evaluate Spec-Kit PR #1368

**Change ID:** `evaluate-spec-kit-pr-1368`  
**Status:** Proposal Phase ✅  
**Date:** 2026-01-04  
**Branch:** `feat/evaluate-spec-kit-pr-1368`

---

## Quick Summary

This OpenSpec change proposes a comprehensive evaluation of GitHub Pull Request #1368 for the spec-kit framework. The PR adds support for **Google's Antigravity IDE** as an AI assistant option in Specify CLI.

### Key Findings

✅ **Overall Assessment:** PR is well-structured and follows spec-kit patterns  
⚠️ **Initial Concern:** Copilot flagged directory path "inconsistency" - re-analyzed as **not a bug**  
✅ **Recommendation:** Safe to implement with comprehensive testing

### Critical Decision

After deep analysis, we determined the "directory path inconsistency" flagged by GitHub Copilot review is actually a **feature pattern**, not a bug:

- `.agent/workflows/` → User-invocable workflow commands
- `.agent/rules/` → Agent context/instruction files

This dual-directory structure matches existing IDE agents (Windsurf, Cursor, IBM Bob).

---

## Documents

### Core Documents

| Document                         | Purpose                                        | Status      |
| -------------------------------- | ---------------------------------------------- | ----------- |
| **[proposal.md](./proposal.md)** | Comprehensive evaluation proposal              | ✅ Complete |
| **[tasks.md](./tasks.md)**       | 35 detailed implementation tasks               | ✅ Complete |
| **[design.md](./design.md)**     | Architectural decisions and technical approach | ✅ Complete |

### Supporting Documents (To Be Created During Implementation)

| Document                                                            | Purpose                    | Phase   |
| ------------------------------------------------------------------- | -------------------------- | ------- |
| `/docs/docs-local/2026-01-04/spec-kit-pr-1368-test-results.md`      | Comprehensive test results | Phase 7 |
| `/docs/docs-local/2026-01-04/spec-kit-pr-1368-upstream-feedback.md` | Feedback for PR author     | Phase 7 |
| `/docs/docs-local/2026-01-04/spec-kit-pr-1368-evaluation-report.md` | Final evaluation report    | Phase 7 |
| `/frameworks/spec-kit/LOCAL_MODIFICATIONS.md`                       | Our changes vs upstream    | Phase 3 |

---

## PR #1368 Details

### What It Does

Adds support for Google's **Antigravity IDE** as the 17th AI assistant supported by spec-kit.

### Changes

- **10 files modified** across Python, Bash, PowerShell, and Markdown
- **Version bump:** 0.0.22 → 0.0.23
- **2 commits:**
  - `f3ba03e` - Initial Antigravity agent implementation
  - `a8c6570` - Naming fix (Antigravity → Antigravity IDE, mark as IDE-based)

### Key Implementation

```python
# src/specify_cli/__init__.py
"antigravity": {
    "name": "Antigravity IDE",
    "folder": ".agent/",
    "install_url": None,
    "requires_cli": False,  # IDE-based, not CLI-based
}
```

**Directory Structure:**

- Commands: `.agent/workflows/` (5 speckit workflow .md files)
- Rules: `.agent/rules/specify-rules.md` (agent context)
- Format: Markdown
- Pattern: Matches Windsurf/Cursor IDE agents

---

## Implementation Plan

### Phase Summary

| Phase                     | Tasks        | Est. Time       | Status          |
| ------------------------- | ------------ | --------------- | --------------- |
| **1. Preparation**        | 3 tasks      | ~30 min         | Pending         |
| **2. Static Analysis**    | 5 tasks      | ~2 hours        | Pending         |
| **3. Patch Application**  | 3 tasks      | ~1 hour         | Pending         |
| **4. Linux Testing**      | 4 tasks      | ~1.5 hours      | Pending         |
| **5. Regression Testing** | 3 tasks      | ~1 hour         | Pending         |
| **6. Windows Testing**    | 3 tasks      | ~30 min OR skip | Pending         |
| **7. Documentation**      | 5 tasks      | ~2 hours        | Pending         |
| **TOTAL**                 | **35 tasks** | **~7.5 hours**  | **0% Complete** |

### Next Steps

1. **Get User Approval** for this proposal
2. **Run:** Follow `/opt-openspec-global-apply` workflow
3. **Execute** tasks.md sequentially (respect dependencies)
4. **Test** comprehensively at each checkpoint
5. **Document** results and create final report

---

## Risks & Mitigations

| Risk                          | Level    | Mitigation                                  |
| ----------------------------- | -------- | ------------------------------------------- |
| Patch application conflicts   | LOW      | Backup + dry-run before apply               |
| ~~Directory path bug~~        | ~~HIGH~~ | ~~Re-analyzed: Not a bug~~                  |
| Regression in existing agents | LOW      | Comprehensive regression testing            |
| Windows test unavailability   | MEDIUM   | Document ENV limitation, skip gracefully    |
| Upstream PR changes           | MEDIUM   | Monitor PR, maintain LOCAL_MODIFICATIONS.md |

---

## Success Criteria

### Must-Have (Blocking)

- ✅ All static analysis passes
- ✅ Fresh installation succeeds (Linux)
- ✅ Context update scripts work
- ✅ No regressions in existing agents
- ✅ Documentation complete

### Should-Have (Important)

- Cross-platform testing (Windows PowerShell)
- Release package generation validated
- Pattern consistency confirmed

### Nice-to-Have (Optional)

- Performance benchmarks
- Contributor guide updated

---

## References

- **Original PR:** https://github.com/github/spec-kit/pull/1368
- **PR Author:** @serhiishtokal
- **Related Issues:** #1213, #1217, #1220
- **Spec-Kit Repo:** https://github.com/github/spec-kit
- **Local Framework:** `/frameworks/spec-kit`

---

## Quick Links

### Review Documents

```bash
# Read the proposal
cat openspec/changes/evaluate-spec-kit-pr-1368/proposal.md

# Review tasks
cat openspec/changes/evaluate-spec-kit-pr-1368/tasks.md

# Study design decisions
cat openspec/changes/evaluate-spec-kit-pr-1368/design.md
```

### Start Implementation

```bash
# Follow the apply workflow
# (After user approval)
# Execute tasks.md Phase 1 tasks...
```

---

**README Version:** 1.0  
**Last Updated:** 2026-01-04T20:45:59-04:00  
**Status:** ✅ Proposal Complete - Awaiting Approval
