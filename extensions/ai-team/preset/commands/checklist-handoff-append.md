## AI Team Effective Spec (preset: ai-team-handoff-spec)

When loading feature context for checklist generation:

1. **Preferred**: `EFFECTIVE_SPEC` from `speckit.ai-team.handoff-spec.resolve` hook JSON
2. **Fallback**: `$FEATURE_DIR/spec.override.md` when present
3. **Else**: `$FEATURE_DIR/spec.md`

Never commit `spec.override.md`.
