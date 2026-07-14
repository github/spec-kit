# One-time Usage (uvx)

If you want to try Spec Kit without installing it permanently, use `uvx` to run it directly. This downloads the tool into a temporary environment that is discarded after the command finishes.

> [!NOTE]
> The commands below require **[uv](https://docs.astral.sh/uv/)**. If you see `command not found: uvx`, [install uv first](uv.md).

## Run Specify CLI

```bash
# Create a new project with the pinned AI Team release
uvx --from git+https://github.com/EuphoriaYan/spec-kit.git@v0.12.5+teamwork.1 specify init <PROJECT_NAME>

# Initialize in the current directory
uvx --from git+https://github.com/EuphoriaYan/spec-kit.git@v0.12.5+teamwork.1 specify init . --integration copilot

# Or use the --here flag
uvx --from git+https://github.com/EuphoriaYan/spec-kit.git@v0.12.5+teamwork.1 specify init --here --integration copilot
```

## When to use persistent installation instead

If you plan to use Spec Kit regularly, a persistent installation is recommended:

- Tool stays installed and available in PATH
- No re-download on every invocation
- Better tool management with `uv tool list`, `uv tool upgrade`, `uv tool uninstall`

See the main [Installation Guide](../installation.md) for persistent installation instructions.
