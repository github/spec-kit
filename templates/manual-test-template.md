---
description: "Manual test guide template for feature verification"
---

# Manual Test Guide: [FEATURE NAME]

**Feature**: `[feature-branch]` | **Spec**: [spec.md](spec.md) | **Plan**: [plan.md](plan.md)

> **Who this is for**: Anyone manually verifying this feature with `curl` or Postman — no test framework needed.
> All calls target a running service. Read **Prerequisites** fully before starting.

<!--
  ============================================================================
  IMPORTANT: The content below is a SAMPLE STRUCTURE for illustration only.

  The /speckit.manual-test command MUST replace these with actual test cases
  based on:
  - User stories and acceptance scenarios from spec.md
  - Endpoints and request/response shapes from contracts/
  - Field constraints and state machines from data-model.md
  - Integration scenarios from quickstart.md
  - Auth roles and entitlements from plan.md

  Tests MUST be numbered TEST-01, TEST-02, ... sequentially.
  Every test MUST have a good case AND at least one bad case.
  DO NOT keep these sample items in the generated test.md file.
  ============================================================================
-->

---

## Prerequisites

| Requirement | Detail |
|---|---|
| Service running | `https://localhost:{PORT}` or your target env URL |
| DDL applied | `[migration script name]` executed against target DB |
| ADMIN token | Tenant admin with `[entitlement]` (e.g. Scott) |
| USER token | Regular user with required enrollment (e.g. Jessica) |

Set these shell variables once before running any command:

```bash
BASE="https://localhost:{PORT}"
ADMIN_TOKEN="<paste admin bearer token here>"
USER_TOKEN="<paste user bearer token here>"
ENTITY_ID="<paste UUID here>"
```

---

## Section 1 — [Resource Group Name]

> [One-line description of what this section covers]

### TEST-01 — [Test name: action + subject]

**What it tests**: [Which acceptance scenario, FR-###, or edge case — one sentence]

```bash
curl -k -s -X [METHOD] \
  "$BASE/[path]" \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '[body]' | python3 -m json.tool
```

**✅ Expected — Good case**
- HTTP `[code]`
- [Body/header assertion 1]
- [Body/header assertion 2]

**❌ Bad case — [label, e.g. "no token"]**
```bash
curl -k -s -o /dev/null -w "%{http_code}" -X [METHOD] \
  "$BASE/[path]"
```
→ Expected: `[code]` ([reason])

---

### TEST-02 — [Test name]

**What it tests**: [One sentence]

```bash
curl -k -s -o /dev/null -w "%{http_code}" -X [METHOD] \
  "$BASE/[path]" \
  -H "Authorization: Bearer $USER_TOKEN" \
  -H "Content-Type: application/json" \
  -d '[body]'
```

**✅ Expected**: `[code]`

**❌ Bad case — wrong role**
```bash
curl -k -s -o /dev/null -w "%{http_code}" -X [METHOD] \
  "$BASE/[path]" \
  -H "Authorization: Bearer $USER_TOKEN"
```
→ Expected: `403`

---

## Section 2 — Edge Cases & Security Tests

### TEST-NN — PII / sensitive values must not appear in logs

```bash
docker logs [service-name] 2>&1 | grep -i "[sensitive-term]"
```

**✅ Expected**: No plaintext sensitive values in any log line.

---

## Section 3 — Full End-to-End Smoke Test

Run this sequence in order to confirm everything works together:

```bash
# Step 1: [description] — expect HTTP 2xx
echo "=== Step 1: [description] ==="
[curl command]

# Step 2: [description] — expect HTTP 2xx
echo "=== Step 2: [description] ==="
[curl command]

# Step N: [description]
echo "=== Step N: [description] ==="
[curl command]

echo "=== Done ==="
```

**✅ Expected outcome**: [List HTTP code per step, e.g. 200, 204, 201, 204]

---

## Quick Reference — All APIs at a Glance

| # | Method | Path | Auth | Good | Bad |
|---|---|---|---|---|---|
| TEST-01 | `[METHOD]` | `[path]` | Admin | [code] | [codes] |
| TEST-02 | `[METHOD]` | `[path]` | User | [code] | [codes] |
| TEST-NN | `[METHOD]` | `[path]` | [role] | [code] | [codes] |
