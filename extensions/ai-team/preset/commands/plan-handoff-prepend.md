## Handoff spec

The before_plan hook already syncs remote requirements into `spec.override.md` when configured. Do not re-fetch here.

When loading requirement content, prefer `$FEATURE_DIR/spec.override.md` if it exists; do not use a handoff URL in `spec.md` as the requirement body.

When User Input directs a plan revision from `plan_check` and `context-pack.md`, treat that as the sole revision basis: patch `plan.md` for the listed issues only; do not re-derive the plan from spec unless a listed revision explicitly requires it.
