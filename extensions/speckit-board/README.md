# speckit-board — Spec Kit canvas extension

A Copilot CLI canvas extension that turns any Spec Kit project into a live
Spec-Driven Development (SDD) dashboard in the side panel.

## What you get

Two canvases registered by one extension:

- **`speckit-board`** — portfolio view of every feature in `specs/`, each
  rendered as a row with its pipeline status
  (`Specify → Clarify → Plan → Tasks → Analyze → Implement`) and a one-click
  next-step action. Constitution sits at the top in a collapsible strip.
- **`speckit-feature`** — focused drill-in for a single feature: pipeline
  state, an artifact grid (`spec.md`, `plan.md`, `tasks.md`, checklists,
  research, data model, analyze report), and stage-specific action buttons
  that send `/speckit.*` slash commands to the chat.

Both canvases are **always openable** — empty states gently guide the user
through `specify init` or kicking off their first spec.

## Install

From a checkout of the `github/spec-kit` repo:

```bash
# Copy into ~/.copilot/extensions/speckit-board (production install)
specify canvas install

# Or symlink for active development on the extension itself
specify canvas install --dev

# List what's installed
specify canvas list

# Remove
specify canvas uninstall
```

After installing, restart Copilot CLI (or ask the agent to reload extensions)
and tell the chat: **"open the speckit-board canvas"**.

## Native theming

The iframes use the canvas-provided CSS custom properties
(`--background-color-default`, `--text-color-default`, `--text-color-muted`,
`--border-color-default`, `--color-focus-outline`, `--font-sans`,
`--font-mono`, `--text-body-medium`, `--leading-body-medium`,
`--font-weight-semibold`, and the GitHub Primer ramps `--b-11-10`, `--g-11-10`,
`--n-1-10`, etc.) so the UI follows the host theme — light, dark, and
high-contrast — with no hardcoded colors.

## How actions work

The canvases drive the session through `session.send()`:

1. User clicks a stage button in the iframe (e.g. **/speckit.plan**).
2. The iframe POSTs `/api/send` to its loopback HTTP server.
3. The extension calls `SESSION.send({ prompt: "/speckit.plan ..." })`.
4. The agent runs the command; the canvas re-scans on focus + after a short
   delay so newly created artifacts appear automatically.

Two arg-taking commands (`/speckit.specify`, `/speckit.plan`) expose an inline
text input next to the button so users can type the description without
leaving the canvas.

## Layout

```
extensions/speckit-board/
├── extension.mjs     # joinSession + per-canvas wiring + loopback servers
├── renderer.mjs      # HTML/CSS for both canvases (native theming)
└── scanner.mjs       # pure filesystem scan → state JSON
```

No `package.json`, no `node_modules` — `@github/copilot-sdk/extension` is
auto-resolved by the Copilot CLI host. Logs go through `session.log()` only
(stdout is reserved for JSON-RPC).

## Agent-callable actions

Both canvases expose actions the agent can invoke directly:

| Canvas              | Action          | Purpose                                                |
| ------------------- | --------------- | ------------------------------------------------------ |
| `speckit-board`     | `refresh`       | Re-scan the project.                                   |
| `speckit-board`     | `open_feature`  | Validate a slug and hand off to `speckit-feature`.     |
| `speckit-feature`   | `refresh`       | Re-scan the feature.                                   |
| `speckit-feature`   | `run_command`   | Send any `/speckit.*` slash command (validates input). |

## Scope (v1)

- **In**: read-only dashboard, slash-command launching, "Open in editor"
  handoff to the built-in `editor` canvas, focus-based + manual refresh,
  inline text inputs for arg-taking commands.
- **Out**: editing markdown, toggling task checkboxes, multi-workspace,
  filesystem watching (refresh is on focus / on-demand only).

## Mock UX scenarios

Both canvases include a **Mock** picker in the top-right toolbar that
swaps the live project scan for a synthetic project. Useful for design
review and previewing every pipeline state without seeding a real repo.

- `speckit-board` scenarios: `not-initialized`, `initialized-empty`,
  `early`, `mixed`, `mature`.
- `speckit-feature` scenarios: `not-found`, `spec-only`, `with-clarify`,
  `planned`, `tasks-started`, `tasks-done`, `analyzed`, `implemented`.

Selecting a scenario adds `?scenario=<name>` to the iframe URL; pick
**Live (real project)** to return to the actual scan. Mock scenarios
never read or write files and never send prompts to the session.
