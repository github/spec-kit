# Quickstart: Spec Kit Bundler

**Feature**: Spec Kit Bundler | **Date**: 2026-06-19 | **Plan**: [plan.md](./plan.md)

A validation/run guide proving the feature works end-to-end. It references [contracts/](./contracts/) and [data-model.md](./data-model.md) rather than duplicating them. Implementation code belongs in `tasks.md` and the implementation phase.

## Prerequisites

- Python ≥ 3.11
- A recent `specify` CLI that includes the `bundle` subcommand group (invoked as `specify bundle ...`)
- The bundler calls the existing `specify` primitive machinery (init, extension/preset/workflow/integration installs) in-process — no separate tool required
- Network access OR a local/pinned bundle artifact + catalog for the offline path

## Scenario A — Consumer: one-command role setup (US1, P1)

Proves the core value: zero → fully role-configured project in one command.

```bash
mkdir my-project && cd my-project
specify bundle search security            # discover bundles for the role
specify bundle info security-researcher   # inspect the EXACT expanded component set first
specify bundle install security-researcher
specify bundle list                       # confirm the bundle is installed
```

**Expected**:
- `info` lists every component (integration, extensions, presets w/ priority+strategy, steps, workflows) with versions, plus source catalog + install policy.
- `install` initializes the project (idempotent `specify init`) and adds **exactly** the components `info` showed — no follow-up installs needed.
- The set present in the project equals the inspected set (transparency, SC-002).

## Scenario B — Integration conflict guard (US4 / FR-019)

Proves the only hard cross-bundle failure stops safely.

```bash
# Project already active on `copilot`; bundle expects `claude`.
specify bundle install some-claude-bundle
```

**Expected**: non-zero exit; clear error stating the bundle expects `claude` while `copilot` is active, asking the user to choose. The active integration is **not** silently changed.

## Scenario C — Discovery-only refusal (FR-025)

```bash
specify bundle search                     # community (discovery-only) entries appear, marked
specify bundle install <community-only-bundle>
```

**Expected**: the bundle is visible in search/info but install is refused with a "source is discovery-only" message.

## Scenario D — Stacking + non-collateral removal (US4 / SC-004)

```bash
specify bundle install developer
specify bundle install security-researcher   # stack a second compatible bundle
specify bundle list                          # both present
specify bundle remove security-researcher
specify bundle list                          # only developer remains
```

**Expected**: removing one bundle uninstalls only the components it contributed that are not still required by the other installed bundle — zero collateral removals.

## Scenario E — Update preserves overrides (US4 / FR-028/029)

```bash
# After installing a bundle, a user manually adjusts a component priority via the primitive.
specify bundle update security-researcher
```

**Expected**: declared components refresh via their primitive update paths; the user's primitive-level override (e.g. set priority) is preserved; no bundle-level merge prompts.

## Scenario F — Author: validate → build (US2, P2)

Proves authoring with no scaffold and out-of-band distribution.

```bash
# Hand-write bundle.yml per contracts/bundle-manifest.schema.md
specify bundle validate                   # lint + verify every reference resolves
specify bundle build                      # produce the versioned artifact (e.g. .zip)
```

**Expected**:
- `validate` fails clearly on a missing field or unresolved reference (naming it), passes on a correct manifest.
- `build` emits a single versioned artifact containing the manifest + README + local assets.
- Distribution: host the artifact and add a catalog entry (`specify bundle catalog add ...`) — there is no first-class publish command.

## Scenario G — Catalog source management (FR-026)

```bash
specify bundle catalog list                                   # show the active stack + policies + scope
specify bundle catalog add https://example.com/catalog.json --policy install-allowed --priority 1
specify bundle catalog list                                   # new source reflected
specify bundle catalog remove https://example.com/catalog.json
```

**Expected**: the project-scoped stack updates accordingly; built-in defaults remain (cannot be deleted, only overridden); precedence is project > user > built-in.

## Offline / air-gapped check

```bash
specify bundle install ./security-researcher.zip   # install from a local pinned artifact, no network
```

**Expected**: installs from the local artifact without network access.

## Done / pass criteria

- Scenarios A–G behave as described.
- Inspection output equals install effect (SC-002).
- Integration clash always halts (SC-003); removals never collateral (SC-004).
- A representative role set (PM, BA, security researcher, developer) is expressible as installable bundles (SC-005).
