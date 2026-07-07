## AI Team Effective Spec (preset: ai-team-handoff-spec)

When loading requirement **content** for task generation:

1. **Preferred**: `EFFECTIVE_SPEC` from `speckit.ai-team.handoff-spec.resolve` hook JSON
2. **Fallback**: `$FEATURE_DIR/spec.override.md` when present
3. **Else**: `$FEATURE_DIR/spec.md`

Extract user stories and priorities from the **effective** spec, not from the URL pointer in `spec.md` alone.

Never commit `spec.override.md`.
