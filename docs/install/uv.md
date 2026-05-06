# Installing uv

[uv](https://docs.astral.sh/uv/) is a fast Python package manager by [Astral](https://astral.sh/). Spec Kit uses `uv` (via `uvx` or `uv tool install`) to run the `specify` CLI without polluting your global Python environment.

> [!NOTE]
> **Already have uv?** Run `uv --version` to confirm it is installed, then head back to the [Installation Guide](../installation.md).

## Installation

### macOS and Linux — Standalone Installer

The quickest way to install uv on macOS or Linux is the official shell script:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

After the script finishes, open a new terminal (or run `source $HOME/.local/bin/env`) so the `uv` binary is on your `PATH`.

### Windows — Standalone Installer

On Windows, run the following in PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

After the script finishes, open a new terminal so the `uv` binary is on your `PATH`.

### macOS — Homebrew

```bash
brew install uv
```

### Windows — WinGet

```powershell
winget install --id=astral-sh.uv -e
```

### Windows — Scoop

```powershell
scoop install uv
```

## Verification

Confirm that uv is installed and on your `PATH`:

```bash
uv --version
```

You should see output similar to `uv 0.x.y (...)`.

## Further Reading

For advanced options (self-update, proxy settings, uninstall, etc.) see the official [uv installation docs](https://docs.astral.sh/uv/getting-started/installation/).
