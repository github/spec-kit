## Handoff spec

The before_plan hook already syncs remote requirements into `spec.override.md` when configured. Do not re-fetch here.

When loading requirement content, prefer `$FEATURE_DIR/spec.override.md` if it exists; do not use a handoff URL in `spec.md` as the requirement body.

If `spec.md` is a remote handoff pointer and `spec.override.md` is missing, stop and re-run `speckit.plan` or `speckit.ai-team.handoff-spec-sync` before continuing.

When User Input directs a plan revision from `plan_check` and `context-pack.md`, treat that as the sole revision basis: patch `plan.md` for the listed issues only; do not re-derive the plan from spec unless a listed revision explicitly requires it.

## AI Team plan contract

Keep the native plan template and add these concise sections when absent:

- **Planning Mode**: `standard` or `compact`. Compact is valid only when the
  user selected the compact workflow after impact analysis; never infer it.
- **Change Scope**: affected modules, allowed source/test paths, and explicit
  out-of-scope paths.
- **Architecture Impact**: current Code Graph or source evidence, followed by
  numbered expected deltas (`ARCH-01`, ...). Include class add/delete,
  cross-module dependency, API/SPI, config, wire/data shape, and state ownership
  in this one section. Write `None` with evidence when there is no delta.
- **Compatibility**: default to forward-compatible and behavior-preserving.
  Identify any incompatible contract or default-behavior change and the owner
  decision, migration, and rollback it requires.
- **Verification Strategy**: map expected behavior and architecture deltas to
  planned tests or other evidence.

Do not add a separate change manifest. `plan.md` is the authority for scope,
architecture intent, compatibility, and verification intent.
