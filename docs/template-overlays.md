# Template Overlays & Local Packaging

Spec Kit templates are published as pre-built, agent-specific packages (Claude, Copilot, Gemini, etc.).
This guide covers two ways to customize them locally:

- **Overlays**: layer your own templates on top of the official release packages during `specify init`.
- **Local packaging**: build agent-specific command files directly from `templates/commands/*.md`.

## Overlays

### Base template override

Use your own release packages as the base source (must match Spec Kit’s release asset naming).

```bash
SPECIFY_TEMPLATE_REPO=kcaylor/spec-kit \
uvx --from git+https://github.com/kcaylor/spec-kit.git specify init --here --force --ai claude
```

### Overlay on top of the official release

Keep the official templates as the base and layer your fork on top:

```bash
SPECIFY_TEMPLATE_OVERLAY_REPO=kcaylor/spec-kit \
uvx --from git+https://github.com/kcaylor/spec-kit.git specify init --here --force --ai claude
```

### Overlay from a local directory or ZIP

```bash
SPECIFY_TEMPLATE_OVERLAY_PATH=/absolute/path/to/overlay \
uvx --from git+https://github.com/kcaylor/spec-kit.git specify init --here --force --ai claude
```

The overlay must mirror the structure of a packaged template (for example, `.claude/commands/`).

## Local packaging

If you just want to take `templates/commands/*.md` and generate the agent-specific command files locally:

### Standalone script

```bash
python scripts/package-templates.py --ai claude --script sh --out .
```

### CLI subcommand

```bash
specify package-templates --ai claude --script sh --out .
```

### Common examples

Build all agents (Shell scripts):

```bash
specify package-templates --ai all --script sh --out .
```

Build Copilot commands + prompts:

```bash
specify package-templates --ai copilot --script sh --out . --include-vscode-settings
```

## Notes

- The packaging step uses the same template substitutions as the release script:
  - `{SCRIPT}` is replaced with the selected script variant command.
  - `{ARGS}` becomes `$ARGUMENTS` (Markdown agents) or `{{args}}` (TOML agents).
  - `memory/`, `scripts/`, and `templates/` paths are rewritten to `.specify/` paths.
- For Copilot, the tool generates `.github/prompts/` entries alongside `.github/agents/`.
