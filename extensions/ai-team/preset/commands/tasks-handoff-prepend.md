## Handoff spec

When loading requirement content, prefer `$FEATURE_DIR/spec.override.md` if it exists; do not use a handoff URL in `spec.md` as the requirement body.

If `spec.md` is a remote handoff pointer and `spec.override.md` is missing, stop and re-run `speckit.plan` or `speckit.ai-team.handoff-spec-sync` before continuing.

When User Input directs a tasks revision from native analyze findings, treat that as the sole revision basis: patch `tasks.md` for the listed issues only; do not regenerate tasks from spec unless a listed revision explicitly requires it.

## AI Team task traceability

For every implementation task, include exact paths plus the applicable user
story or requirement, expected architecture delta (`ARCH-*` or `none`), and
test/evidence ID. Ensure every expected architecture delta and every linked
work-item symptom has at least one task and verification path. Native
`tasks.md` remains the execution authority; do not create a parallel task map.
