---
name: tech-debt
description: |
  Technical debt identification, tracking, and remediation strategies.
  Activate when: analyzing codebase health, planning refactoring, or when user mentions
  "tech debt", "refactor", "legacy", "cleanup", "code health".
triggers: ["tech debt", "technical debt", "refactor", "legacy code", "code health", "cleanup"]
---

# Technical Debt Management

> Identify, quantify, and strategically address technical debt.

## Debt Categories

| Category | Description | Impact |
|----------|-------------|--------|
| **Design Debt** | Architectural shortcuts | Hard to extend, test |
| **Code Debt** | Implementation shortcuts | Bugs, maintenance cost |
| **Test Debt** | Missing/poor tests | Risk, slow changes |
| **Doc Debt** | Missing documentation | Onboarding, knowledge loss |
| **Dependency Debt** | Outdated packages | Security, compatibility |
| **Infrastructure Debt** | Manual processes | Slow releases, errors |

## Quick Assessment

### Code Smells → Debt Indicators

| Smell | Debt Type | Priority |
|-------|-----------|----------|
| God Class | Design | High |
| Long Method | Code | Medium |
| Copy-Paste | Code | High |
| No Tests | Test | High |
| TODO/FIXME | Code | Low-Medium |
| Magic Numbers | Code | Low |

### Debt Scoring Formula

```
Score = Severity × Spread × Fix Effort

Severity: Critical=4, High=3, Medium=2, Low=1
Spread: Pervasive=3, Common=2, Isolated=1
Effort: Major=3, Moderate=2, Minor=1
```

## Remediation Strategy

### Priority Matrix

|              | Low Effort | High Effort |
|--------------|------------|-------------|
| **High Value** | Do First | Plan Sprint |
| **Low Value** | Quick Wins | Defer/Skip |

### The Boy Scout Rule
> Leave code cleaner than you found it

When touching code:
1. Fix obvious issues
2. Add missing tests
3. Improve naming
4. Remove dead code

## Critical Don'ts

- Don't accumulate debt without tracking
- Don't refactor without tests
- Don't gold-plate (over-engineer solutions)
- Don't ignore security-related debt

## References

- For debt patterns: Read references/debt-patterns.md
- For refactoring strategies: Read references/refactoring-strategies.md
