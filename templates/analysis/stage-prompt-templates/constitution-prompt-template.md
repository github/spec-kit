# Constitution Stage Prompt (from Legacy Analysis)

**Generated from**: Legacy Code Analysis
**Date**: <<ANALYSIS_DATE>>
**Project**: <<PROJECT_NAME>>

---

## Quick Reference

**Legacy Stack**: <<LEGACY_STACK_SUMMARY>>
**Target Stack**: <<TARGET_STACK_SUMMARY>>
**Analysis**: Analyzed <<N>> files, <<M>> LOC

---

## Extracted Principles from Legacy Codebase

Use these principles (extracted from actual code) as the foundation for your constitution.

### Business Principles (from functional-spec.md §6)

<<FOR_EACH non-negotiable FROM functional-spec.md>>
**<<PRINCIPLE_NAME>>**
Rationale: <<RATIONALE>>
Evidence: <<file:line>>
Example: <<CODE_SNIPPET or CONFIG_VALUE>>
<<END_FOR_EACH>>

### Architectural Principles (from technical-spec.md §1)

<<FOR_EACH legacy principle FROM technical-spec.md>>
**<<PRINCIPLE_NAME>>**
Evidence: <<file:line>>
Recommendation: <<Preserve | Modernize>>
<<END_FOR_EACH>>

### Quality Principles (from functional-spec.md §7)

<<FOR_EACH NFR FROM functional-spec.md>>
**<<PRINCIPLE_NAME>>** (e.g., "80%+ Test Coverage")
Evidence: <<file:line>>
Current: <<CURRENT_VALUE>>
Target: <<TARGET_VALUE>>
<<END_FOR_EACH>>

---

## Critical Constraints (Must Include in Constitution)

These are **non-negotiable** requirements derived from code analysis:

1. **<<CONSTRAINT_1>>** (e.g., "PII Encryption")
   File: <<encryption-middleware.js:45-78>>
   Requirement: All PII encrypted at rest (AES-256)

2. **<<CONSTRAINT_2>>** (e.g., "Audit Logging")
   File: <<audit-logger.js:12-34>>
   Requirement: All transactions logged (GDPR, SOX compliance)

3. **<<CONSTRAINT_3>>**
   <<Continue>>

---

## Suggested Constitution Structure

Use the standard Spec Kit constitution format, but populate with extracted principles:

```markdown
# PROJECT CONSTITUTION

## PRINCIPLES

**Business Principles**:
- <<Principle from legacy analysis>>

**Architectural Principles**:
- Simplicity (prefer simple solutions)
- Evolvability (use LTS versions)
- <<Principle from legacy analysis>>

**Quality Principles**:
- <<Test coverage target from legacy>>
- <<Performance target from legacy>>

## PROJECT METADATA

**Tech Stack**: <<USER_CHOICE_LANGUAGE>>, <<USER_CHOICE_DATABASE>>, etc.
(See technical-spec.md §8 for full stack)

**Deployment**: <<USER_CHOICE_DEPLOYMENT>>

**Observability**: <<USER_CHOICE_OBSERVABILITY>>

**Security**: <<USER_CHOICE_SECURITY>>

## NON-NEGOTIABLES

- <<All items from functional-spec.md §6>>

```

---

## Ready-to-Paste Prompt for /speckit.constitution

```text
PROJECT CONSTITUTION for modernization of <<PROJECT_NAME>>

Use the following principles extracted from legacy codebase analysis:

BUSINESS PRINCIPLES:
- <<Principle 1 with evidence>>
- <<Principle 2 with evidence>>

ARCHITECTURAL PRINCIPLES:
- Simplicity, evolvability, operability
- <<Principle from legacy that should be preserved>>

QUALITY PRINCIPLES:
- Test coverage: Maintain or improve from <<current%>> to <<target%>>
- Performance: p95 < <<target>>ms (current: <<baseline>>ms)

NON-NEGOTIABLES:
- <<All critical constraints from functional-spec.md §6>>

TARGET TECH STACK:
- Language: <<USER_CHOICE_LANGUAGE>>
- Database: <<USER_CHOICE_DATABASE>>
- Deployment: <<USER_CHOICE_DEPLOYMENT>>
- Full stack in technical-spec.md §8

SECURITY:
- Auth: <<USER_CHOICE_SECURITY>>
- Encryption: At rest (AES-256) and in transit (TLS 1.3)

For detailed technical specifications, see analysis/technical-spec.md.
```

---

## END OF CONSTITUTION PROMPT
