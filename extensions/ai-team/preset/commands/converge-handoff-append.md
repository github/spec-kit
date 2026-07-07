## AI Team Effective Spec (preset: ai-team-handoff-spec)

For converge, read the effective spec as the requirement source:

1. **Preferred**: `EFFECTIVE_SPEC` from hook JSON
2. **Fallback**: `$FEATURE_DIR/spec.override.md` if present
3. **Else**: `$FEATURE_DIR/spec.md`

Do not modify `spec.md`, `spec.override.md`, or `plan.md` during converge.

Never commit `spec.override.md`.
