# Extension-contributed always-on instructions — prototype + evidence

Prototype for [github/spec-kit#4200](https://github.com/github/spec-kit/issues/4200):
let an extension contribute an always-on instruction block that reaches the agent
without any command/hook invocation. Ownership follows the maintainer's decision:
**core validates the metadata only; the opt-in `agent-context` extension composes and
owns the agent-file writes.** With `agent-context` not installed, installing an
extension does not touch agent files.

**Triggers / lifecycle.** The agent needs no command invocation to *receive* the rules —
they live in the always-on context file. Composition and refresh are performed by
`agent-context` itself: its `speckit.agent-context.update` command and its `after_specify`
/ `after_plan` hooks, so the block is written during normal setup, before the agent runs,
and a disabled or removed extension's block is dropped on the next refresh. A fully
automatic trigger on `extension add`/`remove` would need an extension-lifecycle hook point
in core (none exists today — the event system covers agent-runtime events only), so that is
deliberately left as a follow-up owned by `agent-context`.

## What changed

- **Core (`src/specify_cli/extensions/__init__.py`)** — accepts and validates a new
  `provides: instructions:` capability (list of `{ file, description? }`), path-safe via
  the existing `relative_extension_path_violation` guard, exposed as `.instructions`.
  Core performs **no** agent-file writes. An instructions-only extension is valid.
- **`agent-context` (`scripts/python/update_agent_context.py`)** — on update, discovers
  installed **and enabled** extensions (reads `.specify/extensions/.registry` +
  each `extension.yml` directly, no CLI dependency), reads each `provides.instructions`
  file, and merges it into the routed agent context file inside a per-extension
  namespaced block:

  ```
  <!-- SPECKIT EXT:<id> START -->
  …rule block…
  <!-- SPECKIT EXT:<id> END -->
  ```

- **bash / PowerShell twins** — delegate to the Python twin's new
  `--emit-extension-blocks` mode, so all three produce **byte-identical** output from a
  single implementation.

## Efficacy

The lift is about **delivery/reachability**, not content or instruction weighting: the
delivered payload is the same rule block whether it arrives always-on or via a command, so
when it is present the measured conformance gain carries over by construction. Two
measurements, same conformance metric, 2 models × 4 languages × 3 complexity (n=24):

- **This mechanism's exact output.** Bare vs the block this install path actually writes to
  `.github/copilot-instructions.md`, captured byte-for-byte: **+0.123 mean best-practice
  conformance, 22 wins / 0 ties / 2 losses** (both losses tiny, on a near-ceiling model).
  This is the verified, install-path-accurate figure.
- **Earlier distilled-block pilot** (a shorter, hand-distilled rule block — a *distinct*
  experiment with a *distinct* payload): **+0.142 mean** over bare, vs +0.10 for the same
  content delivered as on-demand commands. Kept for context, not the headline number.

## Verification (automated)

`tests/extensions/test_extension_instructions.py` (13 tests, all passing):

- **Core validation** — `provides: instructions:` accepted; instructions-only extension is
  valid; non-list rejected; entry missing `file` rejected; path traversal (`/abs`, `..`,
  `sub/../../..`) rejected.
- **Composition** — enabled extension's block is written into the routed context file with
  namespaced markers and byte-exact payload; disabling an extension removes its block on
  the next update while leaving the base managed section intact; multiple extensions
  coexist in deterministic id order; a path-unsafe manifest entry is skipped; **no agent
  file is written when `agent-context` is not configured**; `--emit-extension-blocks`
  emits the shared block text.

Full suite (rebased on current `main`): `pytest` → **6916 passed, 415 skipped**
(the skips are the bash/pwsh cross-execution parity tests, which run on POSIX CI).

Manual end-to-end (copilot integration) also confirmed: `specify extension add` a
`provides: instructions:` extension + `agent-context` → the rules appear in
`.github/copilot-instructions.md`; `disable`/`enable` remove/restore the block; a project
without `agent-context` gets no agent-file writes.
