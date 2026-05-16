# Installation Guide

## Prerequisites

- **Linux/macOS** (or Windows; PowerShell scripts now supported without WSL)
- AI coding agent: [Claude Code](https://www.anthropic.com/claude-code), [GitHub Copilot](https://code.visualstudio.com/), [Codebuddy CLI](https://www.codebuddy.ai/cli), [Gemini CLI](https://github.com/google-gemini/gemini-cli), or [Pi Coding Agent](https://pi.dev)
- [uv](https://docs.astral.sh/uv/) for package management (recommended) or [pipx](https://pypa.github.io/pipx/) for persistent installation
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

## Installation

> **Important:** The only official, maintained packages for Spec Kit come from the [github/spec-kit](https://github.com/github/spec-kit) GitHub repository. Any packages with the same name available on PyPI (e.g. `specify-cli` on pypi.org) are **not** affiliated with this project and are not maintained by the Spec Kit maintainers. For normal installs, use the GitHub-based commands shown below. For offline or air-gapped environments, locally built wheels created from this repository are also valid.

### Initialize a New Project

The easiest way to get started is to initialize a new project. Pin a specific release tag for stability (check [Releases](https://github.com/github/spec-kit/releases) for the latest):

```bash
# Install from a specific stable release (recommended — replace vX.Y.Z with the latest tag)
uvx --from git+https://github.com/github/spec-kit.git@vX.Y.Z specify init <PROJECT_NAME>

# Or install latest from main (may include unreleased changes)
uvx --from git+https://github.com/github/spec-kit.git specify init <PROJECT_NAME>
```

> [!NOTE]
> For a persistent installation, `pipx` works equally well:
> ```bash
> pipx install git+https://github.com/github/spec-kit.git@vX.Y.Z
> ```
> The project uses a standard `hatchling` build backend and has no uv-specific dependencies.

Or initialize in the current directory:

```bash
uvx --from git+https://github.com/github/spec-kit.git@vX.Y.Z specify init .
# or use the --here flag
uvx --from git+https://github.com/github/spec-kit.git@vX.Y.Z specify init --here
```

### Specify Integration

You can proactively specify your coding agent integration during initialization:

```bash
uvx --from git+https://github.com/github/spec-kit.git@vX.Y.Z specify init <project_name> --integration claude
uvx --from git+https://github.com/github/spec-kit.git@vX.Y.Z specify init <project_name> --integration gemini
uvx --from git+https://github.com/github/spec-kit.git@vX.Y.Z specify init <project_name> --integration copilot
uvx --from git+https://github.com/github/spec-kit.git@vX.Y.Z specify init <project_name> --integration codebuddy
uvx --from git+https://github.com/github/spec-kit.git@vX.Y.Z specify init <project_name> --integration pi
```

### Specify Script Type (Shell vs PowerShell)

All automation scripts now have both Bash (`.sh`) and PowerShell (`.ps1`) variants.

Auto behavior:

- Windows default: `ps`
- Other OS default: `sh`
- Interactive mode: you'll be prompted unless you pass `--script`

Force a specific script type:

```bash
uvx --from git+https://github.com/github/spec-kit.git@vX.Y.Z specify init <project_name> --script sh
uvx --from git+https://github.com/github/spec-kit.git@vX.Y.Z specify init <project_name> --script ps
```

### Ignore Agent Tools Check

If you prefer to get the templates without checking for the right tools:

```bash
uvx --from git+https://github.com/github/spec-kit.git@vX.Y.Z specify init <project_name> --integration claude --ignore-agent-tools
```

## Verification

After installation, run the following command to confirm the correct version is installed:

```bash
specify version
```

This helps verify you are running the official Spec Kit build from GitHub, not an unrelated package with the same name.

After initialization, you should see the following commands available in your coding agent:

- `/speckit.specify` - Create specifications
- `/speckit.plan` - Generate implementation plans  
- `/speckit.tasks` - Break down into actionable tasks

The `.specify/scripts` directory will contain both `.sh` and `.ps1` scripts.

### Update Notifications

`specify` can check once per 24 hours whether a newer release is available on GitHub and print an upgrade hint. This is **opt-in**: the check is off by default because air-gapped and network-constrained environments cannot reach GitHub.

To enable it, set:

```bash
export SPECIFY_ENABLE_UPDATE_CHECK=1   # or true / yes / on
```

Even when enabled, the check stays silent when:

- stdout is not a TTY (piped output, redirected to a file, etc.)
- the `CI` environment variable is set

Network failures and rate-limit responses are swallowed — the check never fails the command you ran, though a cache miss may add a small startup delay (bounded by a 2-second fetch timeout) while contacting GitHub. Failures are also cached for the same 24h window, so a transient outage or block won't cause the CLI to retry on every invocation.

## Troubleshooting

### Enterprise / Air-Gapped Installation

If your environment blocks access to PyPI (you see 403 errors when running `uv tool install` or `pip install`), you can create a portable wheel bundle on a connected machine and transfer it to the air-gapped target.

**Step 1: Build the wheel on a connected machine (same OS and Python version as the target)**

```bash
# Clone the repository
git clone https://github.com/github/spec-kit.git
cd spec-kit

# Build the wheel
pip install build
python -m build --wheel --outdir dist/

# Download the wheel and all its runtime dependencies
pip download -d dist/ dist/specify_cli-*.whl
```

> **Important:** `pip download` resolves platform-specific wheels (e.g., PyYAML includes native extensions). You must run this step on a machine with the **same OS and Python version** as the air-gapped target. If you need to support multiple platforms, repeat this step on each target OS (Linux, macOS, Windows) and Python version.

**Step 2: Transfer the `dist/` directory to the air-gapped machine**

Copy the entire `dist/` directory (which contains the `specify-cli` wheel and all dependency wheels) to the target machine via USB, network share, or other approved transfer method.

**Step 3: Install on the air-gapped machine**

```bash
pip install --no-index --find-links=./dist specify-cli
```

**Step 4: Initialize a project (no network required)**

```bash
# Initialize a project — no GitHub access needed
specify init my-project --integration claude
```

Bundled assets are used by default — no network access is required.

> **Note:** Python 3.11+ is required.

> **Windows note:** Offline scaffolding requires PowerShell 7+ (`pwsh`), not Windows PowerShell 5.x (`powershell.exe`). Install from https://aka.ms/powershell.

### Git Credential Manager on Linux

If you're having issues with Git authentication on Linux, you can install Git Credential Manager:

```bash
#!/usr/bin/env bash
set -e
echo "Downloading Git Credential Manager v2.6.1..."
wget https://github.com/git-ecosystem/git-credential-manager/releases/download/v2.6.1/gcm-linux_amd64.2.6.1.deb
echo "Installing Git Credential Manager..."
sudo dpkg -i gcm-linux_amd64.2.6.1.deb
echo "Configuring Git to use GCM..."
git config --global credential.helper manager
echo "Cleaning up..."
rm gcm-linux_amd64.2.6.1.deb
```
