# Clarify Stage Prompt (from Legacy Analysis)

**Project**: <<PROJECT_NAME>>
**Critical Instruction**: **Consult legacy code as source of truth**

---

## Source of Truth Guidance

⚠️ **IMPORTANT**: When clarifying ambiguous requirements, specifications that are
underspecified, or situations requiring further clarification:

### CONSULT THE LEGACY APPLICATION CODE AS THE SOURCE OF TRUTH

Do not guess or assume. Check the actual implementation first.

---

## Legacy Code References (for Clarification)

### Authentication & Authorization

- File: <<src/auth/login.js:34-89>>
- Behavior: <<session-based, 30min timeout, cookie storage>>
- Use this as reference for auth questions

### Business Logic (Critical Features)

<<FOR_EACH critical feature>>

- <<FEATURE_NAME>>
  File: <<path/to/file:line-range>>
  Key behavior: <<description>>

<<END_FOR>>

### Configuration & Constants

- File: <<config/app.js>>
- Important settings: <<list key configs>>

### Data Validation Rules

- File: <<validators/input.js>>
- Schemas: <<list validation rules>>

---

## Clarification Process

**Step 1**: User asks clarifying question
**Step 2**: Check if answer exists in legacy code references above
**Step 3a**: If found → Use legacy implementation as answer
**Step 3b**: If NOT found or still unclear → ASK USER (don't assume)

**Example**:

❓ Question: "How should we handle session timeout?"

✅ Answer from legacy code:

- Check: `src/auth/session.js:56`
- Finding: Hardcoded 30 minutes
- Decision: Preserve 30min timeout (or ask user if should make configurable)

❌ DON'T: Assume 15min or 60min without checking code

---

## Ready-to-Paste Prompt

```text
CLARIFY stage for modernization of <<PROJECT_NAME>>.

CLARIFICATION GUIDANCE:
- For ANY ambiguous requirements, check legacy code first
- Legacy code is SOURCE OF TRUTH for current behavior
- If still unclear after checking code, ASK USER (don't assume)

LEGACY CODE REFERENCES:
- Auth: <<file:line>> (<<key behavior>>)
- <<Feature 1>>: <<file:line>> (<<key behavior>>)
- <<Feature 2>>: <<file:line>> (<<key behavior>>)
- Config: <<file:line>> (<<important settings>>)

CRITICAL BEHAVIORS (preserve exactly):
<<FROM functional-spec.md §6>>
- <<Behavior 1>>: Evidence <<file:line>>
- <<Behavior 2>>: Evidence <<file:line>>

If specification is underspecified or ambiguous:
1. Check legacy code at references above
2. If still unclear, ASK ME
3. NEVER guess or assume behavior

Full legacy analysis: analysis/functional-spec.md
```
