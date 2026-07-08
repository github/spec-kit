## Handoff spec

When loading requirement content, prefer `$FEATURE_DIR/spec.override.md` if it exists; do not use a handoff URL in `spec.md` as the requirement body.

If `spec.md` is a remote handoff pointer and `spec.override.md` is missing, stop and re-run `speckit.plan` or `speckit.ai-team.handoff-spec-sync` before continuing.

When User Input directs a tasks revision from native analyze findings, treat that as the sole revision basis: patch `tasks.md` for the listed issues only; do not regenerate tasks from spec unless a listed revision explicitly requires it.
