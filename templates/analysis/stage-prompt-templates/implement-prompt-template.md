# Implement Stage Prompt (from Legacy Analysis)

**Project**: <<PROJECT_NAME>>
**Critical Instruction**: **Consult legacy code as source of truth**

---

## Source of Truth Guidance

⚠️ **IMPORTANT**: During implementation, when the specification is underspecified,
ambiguous, or requires further clarification:

### CONSULT THE LEGACY APPLICATION CODE AS THE SOURCE OF TRUTH

The legacy code shows the actual behavior that users depend on. Don't guess.

---

## Implementation References (Legacy Code)

### Critical Components (preserve behavior exactly)

<<FOR_EACH critical component>>

**<<COMPONENT_NAME>>** (e.g., "Payment Processing")

- Legacy file: <<src/payments/processor.js:156-234>>
- Key logic:

  ```javascript
  // Retry logic: 3 attempts with exponential backoff
  // Idempotency: Check transaction ID before processing
  // Validation: Amount > 0, currency in [USD, EUR, GBP]
  ```

- **MUST PRESERVE**: <<specific behaviors>>
- Migration target: <<new component path>>

<<END_FOR>>

### Configuration Values

<<FOR_EACH config that affects behavior>>

- <<CONFIG_NAME>>: <<value>>
  File: <<config/app.js:23>>
  Usage: <<where it's used>>
  Migration: <<keep | make configurable | change>>

<<END_FOR>>

### Error Handling Patterns

- Legacy approach: <<describe>>
  File: <<middleware/error-handler.js>>
- Target approach: <<RFC7807 / custom>>
  Preserve error codes: <<list codes to keep>>

### Data Validation Rules

<<FOR_EACH validation rule>>

- Field: <<field_name>>
  Rule: <<validation logic>>
  File: <<validators/input.js:line>>
  Preserve: <<yes/no>>

<<END_FOR>>

---

## Implementation Guidance

### When to Check Legacy Code

✅ **DO check legacy code** for:

- Edge cases not in requirements (null handling, empty arrays, etc.)
- Error messages (users may depend on specific wording)
- Timing/delays (debounce, throttle, retry intervals)
- Default values (what happens if optional field is missing)
- Business rules (validation, calculations, workflows)

❌ **DON'T blindly copy** legacy code:

- Use modern patterns (async/await vs callbacks)
- Fix anti-patterns (global state, tight coupling)
- Improve naming (use descriptive variable names)

**But preserve the BEHAVIOR** even if you modernize the implementation.

---

## Code Migration Map

| Legacy File/Module | Target File/Module | Notes |
|-------------------|-------------------|-------|
| <<src/auth/>> | <<services/auth-service/>> | Modernize session → JWT, keep 30min lifetime |
| <<src/payments/>> | <<services/payment-service/>> | CRITICAL: Preserve exact retry logic |
| <<src/db/>> | <<data/repositories/>> | Replace ORM but keep query logic |

---

## Ready-to-Paste Prompt

```text
IMPLEMENT modernization of <<PROJECT_NAME>>.

IMPLEMENTATION GUIDANCE:
- Consult legacy code when specification is unclear
- Legacy code at <<repo path>> is SOURCE OF TRUTH for behavior
- Preserve critical behaviors even when modernizing implementation

CRITICAL COMPONENTS (preserve behavior exactly):
<<FOR_EACH critical component>>
- <<COMPONENT_NAME>>
  Legacy: <<file:line>>
  Behavior: <<description>>
  Target: <<new location>>
<<END_FOR>>

CONFIGURATION VALUES (from legacy):
<<list key configs with values and migration notes>>

WHEN UNCLEAR:
1. Check legacy code at references above
2. Look for edge cases, error handling, defaults
3. If still unclear, ASK USER
4. NEVER guess behavior

CODE MIGRATION MAP:
<<table of legacy → target mappings>>

TESTING:
- Unit tests: Mirror legacy test cases
- Integration: Test with real data from legacy
- E2E: Replicate critical user workflows

Legacy code reference: <<repo path>>
Full analysis: analysis/functional-spec.md, technical-spec.md
```
