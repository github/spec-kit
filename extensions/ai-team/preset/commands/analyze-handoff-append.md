## AI Team Effective Spec (preset: ai-team-handoff-spec)

For cross-artifact analysis, set SPEC to the effective spec path:

1. **Preferred**: `EFFECTIVE_SPEC` from hook JSON
2. **Fallback**: `$FEATURE_DIR/spec.override.md` if present
3. **Else**: `$FEATURE_DIR/spec.md`

Analyze requirement content from the effective spec, not the URL pointer alone.

Never commit `spec.override.md`.
