## AI Team Handoff Spec (preset: ai-team-handoff-spec)

The mandatory `before_plan` hook (`speckit.ai-team.handoff-spec-sync`) runs before native planning when
`handoff_requirement_url=<https-url>` or deprecated `published_requirement_url=<https-url>` is in scope.

Hook responsibilities (do not duplicate fetch in this command):

- Accept only remote `https://` URLs for authoritative handoff input
- Bootstrap `spec.md` as a URL pointer when missing
- Fetch and merge into gitignored `spec.override.md` while preserving an existing public `spec.md`
- Append `**/spec.override.md` to `.gitignore` when needed
- Stop when authentication prevents fetch; do not invent missing requirement content

When loading requirement **content** after the hook:

1. **Preferred**: `EFFECTIVE_SPEC` from hook JSON
2. **Fallback**: `$FEATURE_DIR/spec.override.md` when present
3. **Else**: `$FEATURE_DIR/spec.md` / `FEATURE_SPEC`

Never commit `spec.override.md`.
