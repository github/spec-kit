# Local Development Guide

This guide shows how to iterate on the `specify` CLI locally without publishing a release or committing to `main` first.

> Scripts now have both Bash (`.sh`) and PowerShell (`.ps1`) variants. The CLI auto-selects based on OS unless you pass `--script sh|ps`.

## Development Workflow (Checklist)
- Test the `specify` CLI flows (`/specify`, `/plan`, `/tasks`) for your changes
- Verify templates in `templates/` render and behave as expected
- Test scripts in `scripts/` for both `sh` and `ps` variants where applicable
- Update `memory/constitution.md` if you changed core process expectations

## 1. Clone and Switch Branches

```bash
git clone https://github.com/github/spec-kit.git
cd spec-kit
# Work on a feature branch
git checkout -b your-feature-branch
```

## 2. Run the CLI Directly (Fastest Feedback)

You can execute the CLI via the module entrypoint without installing anything:

```bash
# From repo root
python -m src.specify_cli --help
python -m src.specify_cli init demo-project --ai claude --ignore-agent-tools --script sh
```

If you prefer invoking the script file style (uses shebang):

```bash
python src/specify_cli/__init__.py init demo-project --script ps
```

## 3. Use Editable Install (Isolated Environment)

Create an isolated environment using `uv` so dependencies resolve exactly like end users get them:

```bash
# Create & activate virtual env (uv auto-manages .venv)
uv venv
source .venv/bin/activate  # or on Windows PowerShell: .venv\Scripts\Activate.ps1

# Install project in editable mode
uv pip install -e .

# Now 'specify' entrypoint is available
specify --help
```

Re-running after code edits requires no reinstall because of editable mode.

## 4. Invoke with uvx Directly From Git (Current Branch)

`uvx` can run from a local path (or a Git ref) to simulate user flows:

```bash
uvx --from . specify init demo-uvx --ai copilot --ignore-agent-tools --script sh
```

You can also point uvx at a specific branch without merging:

```bash
# Push your working branch first
git push origin your-feature-branch
uvx --from git+https://github.com/github/spec-kit.git@your-feature-branch specify init demo-branch-test --script ps
```

### 4a. Absolute Path uvx (Run From Anywhere)

If you're in another directory, use an absolute path instead of `.`:

```bash
uvx --from /mnt/c/GitHub/spec-kit specify --help
uvx --from /mnt/c/GitHub/spec-kit specify init demo-anywhere --ai copilot --ignore-agent-tools --script sh
```

Set an environment variable for convenience:
```bash
export SPEC_KIT_SRC=/mnt/c/GitHub/spec-kit
uvx --from "$SPEC_KIT_SRC" specify init demo-env --ai copilot --ignore-agent-tools --script ps
```

(Optional) Define a shell function:
```bash
specify-dev() { uvx --from /mnt/c/GitHub/spec-kit specify "$@"; }
# Then
specify-dev --help
```

### 4b. Use Locally Built Templates (No Network)

Build the per-agent, per-script template archives locally and point the CLI at one ZIP via `SPECIFY_TEMPLATE_ZIP`.

- Build on Linux

```bash
chmod +x .github/workflows/scripts/create-release-packages.sh && \
.github/workflows/scripts/create-release-packages.sh v0.0.1; \
chmod -x .github/workflows/scripts/create-release-packages.sh
```

- Build on macOS (use Docker for GNU tools like `cp --parents`)

```bash
docker run --rm -it -v "$PWD":/w -w /w ubuntu:24.04 bash -lc "apt-get update && apt-get install -y zip && chmod +x .github/workflows/scripts/create-release-packages.sh && .github/workflows/scripts/create-release-packages.sh v0.0.1 && chmod -x .github/workflows/scripts/create-release-packages.sh"
```

- (Optional) Build only specific variants

```bash
AGENTS=claude,cursor SCRIPTS=sh .github/workflows/scripts/create-release-packages.sh v0.0.1
```

- Run the CLI against a local ZIP (no network)

```bash
SPECIFY_TEMPLATE_ZIP=/abs/path/spec-kit-template-claude-sh-v0.0.1.zip \
uvx --refresh --no-cache --from /abs/path/to/spec-kit \
  specify init --here --ai claude --script sh --ignore-agent-tools
```

Notes:
- Keep `--ai` and `--script` consistent with the ZIP variant you built.
- On Linux, ensure `zip` is installed. On macOS, prefer the Docker method above.
- Artifacts are git-ignored by default (`spec-kit-template-*-v*.zip`, `sdd-*-package-*`).
- This flow mirrors the release packaging; it’s ideal for verifying template layout and agent-specific directories (Claude, Cursor, Copilot, Qwen, Gemini, opencode, Windsurf).

## 5. Testing Script Permission Logic

After running an `init`, check that shell scripts are executable on POSIX systems:

```bash
ls -l scripts | grep .sh
# Expect owner execute bit (e.g. -rwxr-xr-x)
```
On Windows you will instead use the `.ps1` scripts (no chmod needed).

## 6. Run Lint / Basic Checks (Add Your Own)

Currently no enforced lint config is bundled, but you can quickly sanity check importability:
```bash
python -c "import specify_cli; print('Import OK')"
```

## 7. Build a Wheel Locally (Optional)

Validate packaging before publishing:

```bash
uv build
ls dist/
```
Install the built artifact into a fresh throwaway environment if needed.

## 8. Using a Temporary Workspace

When testing `init --here` in a dirty directory, create a temp workspace:

```bash
mkdir /tmp/spec-test && cd /tmp/spec-test
python -m src.specify_cli init --here --ai claude --ignore-agent-tools --script sh  # if repo copied here
```
Or copy only the modified CLI portion if you want a lighter sandbox.

## 9. Debug Network / TLS Skips

If you need to bypass TLS validation while experimenting:

```bash
specify check --skip-tls
specify init demo --skip-tls --ai gemini --ignore-agent-tools --script ps
```
(Use only for local experimentation.)

## 10. Rapid Edit Loop Summary

| Action | Command |
|--------|---------|
| Run CLI directly | `python -m src.specify_cli --help` |
| Editable install | `uv pip install -e .` then `specify ...` |
| Local uvx run (repo root) | `uvx --from . specify ...` |
| Local uvx run (abs path) | `uvx --from /mnt/c/GitHub/spec-kit specify ...` |
| Git branch uvx | `uvx --from git+URL@branch specify ...` |
| Build wheel | `uv build` |
| Use locally built template | `SPECIFY_TEMPLATE_ZIP=… uvx --from … specify init …` |

## 11. Cleaning Up

Remove build artifacts / virtual env quickly:
```bash
rm -rf .venv dist build *.egg-info
```

## 12. Common Issues

| Symptom | Fix |
|---------|-----|
| `ModuleNotFoundError: typer` | Run `uv pip install -e .` |
| Scripts not executable (Linux) | Re-run init or `chmod +x scripts/*.sh` |
| Git step skipped | You passed `--no-git` or Git not installed |
| Wrong script type downloaded | Pass `--script sh` or `--script ps` explicitly |
| TLS errors on corporate network | Try `--skip-tls` (not for production) |

## 13. Next Steps

- Update docs and run through Quick Start using your modified CLI
- Open a PR when satisfied
- (Optional) Tag a release once changes land in `main`

## 14. Distributing and testing your fork

You can point the CLI at a different GitHub repository (e.g., your fork) for template downloads without changing code. Set these environment variables before running `specify`:

- `SPECIFY_REPO_OWNER` — GitHub user/org that owns the repo
- `SPECIFY_REPO_NAME` — Repository name

The CLI queries `https://api.github.com/repos/<owner>/<repo>/releases/latest` and selects the first asset whose filename contains `spec-kit-template-{ai}-{script}` and ends with `.zip`.

Recommended asset naming (matches release packaging scripts):
`spec-kit-template-<agent>-<script>-vX.Y.Z.zip` (e.g., `spec-kit-template-claude-sh-v0.0.1.zip`).

Steps to distribute/test your fork:
1. Fork this repo and push your changes.
2. Build template archives using the release packaging script (see section 4b for examples).
3. Draft a GitHub Release on your fork and upload the ZIP assets.
4. Export env var overrides and run the CLI against your fork’s release.

Bash/Zsh:
```bash
export SPECIFY_REPO_OWNER=your-gh-username-or-org
export SPECIFY_REPO_NAME=your-spec-kit-repo
# Optional if private/rate-limited
export GH_TOKEN=ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXX

specify init my-forked-test --ai claude --script sh --ignore-agent-tools
```

PowerShell:
```powershell
$env:SPECIFY_REPO_OWNER = 'your-gh-username-or-org'
$env:SPECIFY_REPO_NAME = 'your-spec-kit-repo'
# Optional if private/rate-limited
$env:GH_TOKEN = 'ghp_XXXXXXXXXXXXXXXXXXXXXXXXXXXX'

specify init my-forked-test --ai claude --script ps --ignore-agent-tools
```

Notes:
- If no asset matches, the CLI prints the available asset names—verify your filenames include `spec-kit-template-{ai}-{script}` and end with `.zip`.
- Use `GITHUB_TOKEN` or `GH_TOKEN` for private forks or to avoid GitHub API rate limits.
- Clear the overrides to return to upstream defaults:
  - Bash: `unset SPECIFY_REPO_OWNER SPECIFY_REPO_NAME`
  - PowerShell: `Remove-Item Env:SPECIFY_REPO_OWNER,Env:SPECIFY_REPO_NAME -ErrorAction SilentlyContinue`
