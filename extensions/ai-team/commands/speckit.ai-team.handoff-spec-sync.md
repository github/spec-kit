---
description: "Fetch handoff requirement URL and build gitignored spec.override.md before planning"
scripts:
  sh: scripts/bash/sync-handoff-spec.sh --json
  ps: scripts/powershell/Sync-HandoffSpec.ps1 -Json
---

# Handoff Spec Sync

Run before native planning when a confidential or remote handoff requirement URL
is in scope. Writes or refreshes `spec.override.md` without modifying an existing
public `spec.md` baseline.

## User Input

```text
$ARGUMENTS
```

## Execution

1. If the parent command or task context provides
   `handoff_requirement_url=<https-url>` or deprecated
   `published_requirement_url=<https-url>`, export it before running the script:

   ```bash
   export HANDOFF_REQUIREMENT_URL="https://..."
   ```

2. Run `{SCRIPT}` from the repository root with `$ARGUMENTS` appended when URL
   values appear only in the invocation text.

3. Parse JSON:
   - `SKIPPED: true` — no handoff URL; continue without override changes
   - otherwise record `EFFECTIVE_SPEC`, `FEATURE_SPEC`, `SPEC_BOOTSTRAPPED`

## Script behavior

- Accepts only `https://` URLs
- Creates `spec.md` URL pointer when missing (bootstrap)
- Fetches remote content and merges into `spec.override.md`
- Appends `**/spec.override.md` to `.gitignore` when needed
- Stops with an error when fetch fails (do not invent requirement content)
