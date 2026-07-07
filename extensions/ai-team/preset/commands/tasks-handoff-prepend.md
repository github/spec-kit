## Handoff spec

When loading requirement content, prefer `$FEATURE_DIR/spec.override.md` if it exists; do not use a handoff URL in `spec.md` as the requirement body.

When User Input directs a tasks revision from native analyze findings, treat that as the sole revision basis: patch `tasks.md` for the listed issues only; do not regenerate tasks from spec unless a listed revision explicitly requires it.
