---
description: Check documentation freshness against code and fix stale docs.
---

## User Input

```text
$ARGUMENTS
```

You are performing a **documentation health check** to ensure the knowledge base stays accurate as the codebase evolves. Stale documentation is worse than no documentation—it misleads.

## Philosophy

Documentation should:
- Reflect the current state of the code
- Be trustworthy for both humans and AI
- Stay current without manual effort

This command catches drift between code and docs, then helps fix it.

## What to Validate

### 1. Decision Records (`.minispec/knowledge/decisions/`)

For each decision file:

**Frontmatter validity:**
- Required fields present (type, id, date, status, impacts)
- Status is valid (proposed/accepted/deprecated/superseded)
- If superseded, `superseded_by` points to existing decision

**Content accuracy:**
- Code references still exist
- Referenced file paths are valid
- Impacts list matches actual file locations

**Relevance:**
- Decision hasn't been reversed without documentation
- Status reflects reality (is it still active?)

### 2. Pattern Documentation (`.minispec/knowledge/patterns/`)

For each pattern file:

**Frontmatter validity:**
- Required fields present (type, id, name, category, status)
- Status reflects current usage

**Content accuracy:**
- Code examples match actual patterns in codebase
- "Examples in This Codebase" locations exist
- Referenced files use the pattern as described

**Relevance:**
- Pattern is actually used (not deprecated in practice)
- No newer pattern has replaced it

### 3. Module Documentation (`.minispec/knowledge/modules/`)

For each module file:

**Frontmatter validity:**
- Required fields present (type, id, name, path, status)
- Path points to existing directory

**Content accuracy:**
- Public API matches actual exports
- Listed files exist
- Dependencies are accurate

**Relevance:**
- Module still exists
- Architecture description matches reality

### 4. Architecture Overview (`.minispec/knowledge/architecture.md`)

**Structural accuracy:**
- Described components exist
- Relationships are accurate
- Tech stack is current

### 5. Conventions (`.minispec/knowledge/conventions.md`)

**Accuracy:**
- Conventions are actually followed in code
- No contradicting patterns in recent code

### 6. Glossary (`.minispec/knowledge/glossary.md`)

**Completeness:**
- Key terms from code are defined
- Definitions match usage

## Execution Flow

### Phase 1: Scan Knowledge Base

1. List all files in `.minispec/knowledge/`
2. Parse frontmatter and content
3. Extract all code references (file paths, function names, etc.)

### Phase 2: Cross-Reference with Code

For each reference:
1. Check if the referenced path exists
2. If it references specific code, verify it's still there
3. Track broken references

### Phase 3: Detect Staleness

Look for signals of outdated docs:

**Broken references:**
- File paths that don't exist
- Function names not found
- Module paths invalid

**Timestamp drift:**
- Last updated date vs. file modification times
- Decisions older than code changes in impacted areas

**Contradiction:**
- Doc says X, code does Y
- Pattern doc shows approach A, code uses approach B

### Phase 4: Report Findings

**If everything is fresh:**
> "✅ Documentation check complete. Everything looks current!
>
> **Checked:**
> - [N] decisions - all valid
> - [N] patterns - all accurate
> - [N] modules - all current
>
> No staleness detected."

**If issues found:**
> "Documentation check found [N] items needing attention:
>
> **Stale (code changed, docs didn't):**
> 1. `decisions/003-auth.md`
>    - References `src/auth/jwt.ts` which no longer exists
>    - Last updated: [date], file deleted: [date]
>
> 2. `patterns/api-response.md`
>    - Example shows old response format
>    - Current code uses different structure
>
> **Broken references:**
> 1. `modules/payments.md` → `src/payments/` (directory missing)
>
> **Potentially outdated:**
> 1. `architecture.md` - Not updated in 30+ days, code has changed
>
> Want me to help fix these?"

### Phase 5: Interactive Fixes

For each issue, offer specific resolution:

**For broken references:**
> "The file `src/auth/jwt.ts` no longer exists. It looks like:
> - It was renamed to `src/auth/tokens.ts`, OR
> - The functionality moved to `src/auth/index.ts`, OR
> - The feature was removed entirely
>
> What happened? I'll update the decision record."

**For stale content:**
> "The `api-response` pattern doc shows:
> ```typescript
> { data: T, error: null }
> ```
>
> But current code uses:
> ```typescript
> { success: true, data: T }
> ```
>
> Should I update the pattern doc to match current code?"

**For missing updates:**
> "Several files in `src/payments/` changed recently but `modules/payments.md` wasn't updated.
>
> Changes detected:
> - New file: `refunds.ts`
> - Modified: `checkout.ts`
>
> Want me to update the module documentation?"

**For superseded decisions:**
> "Decision `003-session-auth` describes session-based auth, but I see JWT implementation in the code. Was this decision superseded?
>
> I can:
> a) Mark 003 as superseded and create a new decision for JWT
> b) Update 003 to reflect the change (if it was an evolution)
> c) Leave it (if both approaches coexist)"

### Phase 6: Apply Fixes

When engineer approves fixes:

1. Update the documentation files
2. Maintain frontmatter (update `updated` date)
3. Preserve history (note what changed and why)
4. Commit with clear message

### Phase 7: Summary

After fixes:

> "Documentation updated:
>
> **Fixed:**
> - `decisions/003-auth.md` - Updated file references
> - `patterns/api-response.md` - Synced with current code
> - `modules/payments.md` - Added new components
>
> **Marked as superseded:**
> - `decisions/001-old-approach.md`
>
> Knowledge base is now current with the codebase."

## Automated Detection Heuristics

### Staleness Signals

1. **File reference check**: Does `path/to/file.ts` exist?
2. **Function reference check**: Does `functionName()` exist in the file?
3. **Import check**: Are documented imports still used?
4. **Date check**: Is doc older than recent significant code changes?
5. **Pattern match**: Does code follow the documented pattern?

### Severity Levels

| Level | Meaning | Action |
|-------|---------|--------|
| **Critical** | Broken reference, doc is actively misleading | Must fix |
| **Warning** | Likely stale, needs human verification | Should fix |
| **Info** | Minor drift, still mostly accurate | Optional fix |

## Running Automatically

This command can be run:
- Manually with `/minispec.validate-docs`
- Before `/minispec.walkthrough` (auto-check to warn about stale docs)
- Periodically as maintenance

## Important Guidelines

- **Don't auto-fix without asking**: Staleness might indicate intentional change
- **Preserve decision history**: Don't delete old decisions, supersede them
- **Be specific about what's wrong**: Show the discrepancy clearly
- **Offer concrete fixes**: Don't just report—help resolve
- **Respect the code as truth**: Code is authoritative; docs should match it

## Output Artifacts

This command may update:

1. `.minispec/knowledge/decisions/*.md` - Fixed references, updated status
2. `.minispec/knowledge/patterns/*.md` - Updated examples
3. `.minispec/knowledge/modules/*.md` - Synced with code
4. `.minispec/knowledge/architecture.md` - Updated structure
5. `.minispec/knowledge/conventions.md` - Aligned with practice

All changes require engineer approval.
