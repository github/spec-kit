# Contract: `bundle` CLI Command Surface

**Feature**: Spec Kit Bundler | **Date**: 2026-06-19

This is the behavioral contract for the `specify bundle` subcommand group (a `bundle` Typer sub-app inside the `specify` CLI, not a standalone tool). Command names/verbs mirror the sibling `specify extension|preset|workflow|catalog` surface so the group feels native. Each command lists its inputs, success behavior, and required error behavior. Exit code `0` = success; non-zero = failure with a clear, actionable message on stderr.

> Note: precise flag spellings are an implementation detail finalized in `tasks.md`/implementation. The **behaviors and error guarantees** below are the contract.

## Consume

### `specify bundle search [<query>]`
- **Input**: optional text query; reads the active catalog stack.
- **Success**: lists matching bundles with id, name, role, version, description, **source catalog**, and **install policy**. Includes `discovery-only` entries (marked as such).
- **Errors**: a misconfigured/unreachable catalog source fails naming the offending source (not a silent empty list).

### `specify bundle info <bundle-id>`
- **Input**: bundle id; resolved from the active catalog stack.
- **Success**: shows full metadata **and the fully expanded component set** (integration, extensions, presets w/ priority+strategy, steps, workflows) with versions, plus the entry's source catalog and install policy. Inspection output MUST equal what `install` would add (transparency, FR-009/SC-002).
- **Errors**: unknown id → clear "not found in active catalogs" error.

### `specify bundle list`
- **Input**: target project (cwd by default).
- **Success**: lists bundles currently installed in the project with versions.
- **Errors**: not a Spec Kit project → clear guidance to run `specify bundle init`/`specify init`.

### `specify bundle init [<bundle>]`
- **Input**: optional bundle (for integration/script defaults); `--integration`, `--script` overrides.
- **Success**: initializes a Spec Kit project (idempotent). Integration/script precedence: explicit flag > bundle's declared value > default (`copilot` + OS-appropriate script). Agnostic bundle inherits the active integration.
- **Errors**: conflicting explicit integration vs. an already-active different integration → clear error asking the user to choose.

### `specify bundle install <bundle-id>`
- **Input**: bundle id (resolved from catalog stack) or pinned source; `--integration`, `--script` overrides.
- **Success**: ensures the project is initialized (idempotent `specify init`), then installs every declared component through its own primitive machinery — single operation, no required follow-up installs. Result matches what `info` showed.
- **Errors (required)**:
  - Bundle resolves only from a `discovery-only` source → refuse with "source is discovery-only" (entry still visible in search/info).
  - Bundle expects a different integration than the project's active one → **fail** asking the user to choose; never silently switch/skip.
  - `requires.speckit_version` exceeds installed version → refuse, explaining the unmet requirement.
  - Partial failure (a component cannot be fetched/installed) → stop with a clear report of what did/didn't install; no silent half-configured state.
- **Pre-install warnings**: foreseeable overlaps (e.g. two presets overriding the same template) are surfaced before installing.

### `specify bundle update [<bundle-id>|--all]`
- **Input**: a bundle id or all installed bundles.
- **Success**: re-resolves the declared component set and refreshes each component via its primitive's normal update path. No bundle-level merge logic. Primitive-level user overrides (e.g. a set priority) are preserved.
- **Errors**: same compatibility/availability guarantees as install.

### `specify bundle remove <bundle-id>`
- **Input**: an installed bundle id.
- **Success**: uninstalls only the components this bundle contributed that are not still required by another installed bundle or installed independently (zero collateral removals, SC-004). Returns the project toward its prior state.
- **Errors**: not installed → clear message.

## Catalog management

### `specify bundle catalog list`
- **Success**: prints the active priority-ordered catalog stack — each source's id, url, priority, install policy, and scope (project/user/built-in) — and indicates when the built-in default stack is in use.

### `specify bundle catalog add <url> [--policy install-allowed|discovery-only] [--priority N]`
- **Success**: registers a source in the project-scoped catalog config; persists it; re-list reflects it.
- **Errors**: invalid/unreachable url → clear error; duplicate source → clear message.

### `specify bundle catalog remove <id|url>`
- **Success**: removes the source from the config; built-in defaults cannot be deleted (only overridden).

## Author

### `specify bundle validate`
- **Input**: a `bundle.yml` in the working directory (or `--path`).
- **Success**: reports the manifest as well-formed and all references resolved.
- **Errors (required)**: missing required identity/metadata field → name it; unresolved component reference → name the specific offending reference; invalid `requires.speckit_version` constraint → clear error. (No authoring scaffold exists — `validate`/`build` only.)

### `specify bundle build`
- **Input**: a validated `bundle.yml`.
- **Success**: produces a single versioned distributable artifact (e.g. `.zip`) containing the manifest, README, and any local assets.
- **Errors**: build on an invalid manifest → refuse, pointing the author to `validate`.
- **Note**: no first-class publish — distribution is hosting the artifact + adding a catalog entry out-of-band.

## Cross-cutting guarantees
- **Transparency**: `info`/`search`/dry behavior reflect exactly what install will do.
- **Reversibility**: `remove` is safe and non-collateral.
- **No resolution layer**: all component conflicts resolve at the primitive level; the only hard cross-bundle failure is the integration clash.
- **Offline**: all consume/author commands work from pinned URLs or local paths without network access.
