# Quickstart: Validating Agent-Context Full Opt-In

**Feature**: 001-agent-context-full-optin | **Date**: 2026-06-22

This guide describes how to validate, end-to-end, that the `agent-context` extension is the sole owner of agent context files and that the Specify CLI contains no agent-context logic. It references the contracts in [contracts/cli-behavior.md](./contracts/cli-behavior.md) rather than duplicating assertions.

## Prerequisites

- Repo checked out on branch `001-agent-context-full-optin`
- Python environment for the Specify CLI (per `DEVELOPMENT.md`)
- `pytest` available

## Setup

```bash
# From the repo root
pip install -e .            # or the project's documented dev install
```

## Validation 1 — Full test suite passes (SC-004)

```bash
pytest -q
```

**Expected**: All tests pass. Tests covering removed CLI behavior (context-section upsert/remove, config writers, enabled gating, deprecation warning) have been pruned or relocated to the extension; no test asserts the removed deprecation message (C5, C1).

## Validation 2 — No agent-context logic remains in the CLI (SC-002, SC-003)

```bash
# Should produce NO matches outside extensions/agent-context/ and specs/
grep -rn -E \
  'upsert_context_section|remove_context_section|_agent_context_extension_enabled|_resolve_context_markers|_AGENT_CTX_EXT_CONFIG|_load_agent_context_config|_save_agent_context_config|_update_agent_context_config_file' \
  src/specify_cli/

# Should produce NO matches (deprecation string removed)
grep -rn 'Inline agent-context updates' src/specify_cli/
```

**Expected**: Both commands return nothing for `src/specify_cli/`. (Contract C5.)

## Validation 3 — Init without the extension makes no context changes (SC-001, C1)

```bash
tmp=$(mktemp -d)
# Initialize a project with an integration, WITHOUT opting into agent-context
specify init "$tmp/demo" --integration claude   # adjust to the real non-interactive flags

# The agent context file must have NO managed section written by the CLI
test ! -f "$tmp/demo/CLAUDE.md" || ! grep -q 'SPECKIT START' "$tmp/demo/CLAUDE.md"
# The extension config must NOT be written by the CLI
test ! -f "$tmp/demo/.specify/extensions/agent-context/agent-context-config.yml"
```

**Expected**: No managed section; no extension config written by the CLI; no deprecation output during init. (Contracts C1, C3.)

## Validation 4 — Opt-in path still works end-to-end (SC-005, C2, C7)

```bash
# In a project where the user opted into agent-context, run the extension update
# (slash command in an agent session, or the bundled script directly)
bash extensions/agent-context/scripts/bash/update-agent-context.sh   # adjust args/cwd as documented
```

**Expected**: The extension reads its own `agent-context-config.yml` and creates/refreshes the managed Spec Kit section in the configured context file — proving no loss of functionality and that the extension is self-contained. (Contracts C2, C7.)

## Validation 5 — Backward compatibility (SC-006, C6)

```bash
# Simulate a legacy project: pre-existing managed section + ext config
# Then run init / integration switch / uninstall and confirm success + files untouched
```

**Expected**: Commands complete without error; pre-existing files remain intact and unmodified by the CLI. (Contract C6.)

## Done When

- [ ] `pytest -q` passes (Validation 1)
- [ ] Grep guards return no CLI matches (Validation 2)
- [ ] Init without extension makes no context/config changes (Validation 3)
- [ ] Extension update still manages the section (Validation 4)
- [ ] Legacy projects keep working (Validation 5)
