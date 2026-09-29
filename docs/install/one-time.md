# One-time Usage (uvx)

If you want to try Spec Kit without installing it permanently, use `uvx` to run it directly. This downloads the tool into a temporary environment that is discarded after the command finishes.

> [!NOTE]
> The commands below require **[uv](https://docs.astral.sh/uv/)**. If you see `command not found: uvx`, [install uv first](uv.md).

## Run Specify CLI

```bash
# Create a new project (latest from main)
uvx --from git+https://github.com/github/spec-kit.git specify init <PROJECT_NAME>

# Or target a specific release (replace vX.Y.Z with a tag from Releases;
# keep the leading v, e.g. v0.12.11 not 0.12.11)
uvx --from git+https://github.com/github/spec-kit.git@vX.Y.Z specify init <PROJECT_NAME>

# Initialize in the current directory
uvx --from git+https://github.com/github/spec-kit.git specify init . --integration copilot

# Or use the --here flag
uvx --from git+https://github.com/github/spec-kit.git specify init --here --integration copilot
```

## When to use persistent installation instead

If you plan to use Spec Kit regularly, a persistent installation is recommended:

- Tool stays installed and available in PATH
- No re-download on every invocation
- Better tool management with `uv tool list`, `uv tool upgrade`, `uv tool uninstall`
- Required for [presets](../community/presets.md) that provide a **script** template: the generated
  script resolves its composition by invoking `specify` at run time, so it needs the CLI (or an
  importable `specify_cli`) to still be present after `init` finishes. The `uvx` flow above discards
  its environment as soon as the command exits, so a script-providing preset installed this way will
  fail the first time its script runs. Use a persistent installation if you plan to use such a preset.

See the main [Installation Guide](../installation.md) for persistent installation instructions.
