## AI Team Effective Spec (preset: ai-team-handoff-spec)

Before implementation:

1. **Preferred**: read `EFFECTIVE_SPEC` from `speckit.ai-team.handoff-spec.resolve` hook JSON
2. **Fallback**: read `$FEATURE_DIR/spec.override.md` when present
3. **Else**: read `$FEATURE_DIR/spec.md`

When creating or updating `.gitignore`, ensure `**/spec.override.md` is ignored when handoff overrides are used.

Never commit `spec.override.md`.
