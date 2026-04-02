# Local Development Guide

This guide shows how to iterate on the `infrakit` CLI locally without publishing a release or committing to `main` first.

> Scripts now have both Bash (`.sh`) and PowerShell (`.ps1`) variants. The CLI auto-selects based on OS unless you pass `--script sh|ps`.

## 1. Clone and Switch Branches

```bash
git clone https://github.com/github/infrakit.git
cd infrakit
# Work on a feature branch
git checkout -b your-feature-branch
```

## 2. Run the CLI Directly (Fastest Feedback)

You can execute the CLI via the module entrypoint without installing anything:

```bash
# From repo root
python -m src.infrakit_cli --help
python -m src.infrakit_cli init demo-project --ai claude --iac crossplane --ignore-agent-tools --script sh
```

If you prefer invoking the script file style (uses shebang):

```bash
python src/infrakit_cli/__init__.py init demo-project --iac crossplane --script ps
```

## 3. Use Editable Install (Isolated Environment)

Create an isolated environment using `uv` so dependencies resolve exactly like end users get them:

```bash
# Create & activate virtual env (uv auto-manages .venv)
uv venv
source .venv/bin/activate  # or on Windows PowerShell: .venv\Scripts\Activate.ps1

# Install project in editable mode
uv pip install -e .

# Now 'infrakit' entrypoint is available
infrakit --help
```

Re-running after code edits requires no reinstall because of editable mode.

## 4. Invoke with uvx Directly From Git (Current Branch)

`uvx` can run from a local path (or a Git ref) to simulate user flows:

```bash
uvx --from . infrakit init demo-uvx --ai copilot --iac crossplane --ignore-agent-tools --script sh
```

You can also point uvx at a specific branch without merging:

```bash
# Push your working branch first
git push origin your-feature-branch
uvx --from git+https://github.com/github/infrakit.git@your-feature-branch infrakit init demo-branch-test --iac crossplane --script ps
```

### 4a. Absolute Path uvx (Run From Anywhere)

If you're in another directory, use an absolute path instead of `.`:

```bash
uvx --from /mnt/c/GitHub/infrakit infrakit --help
uvx --from /mnt/c/GitHub/infrakit infrakit init demo-anywhere --ai copilot --iac crossplane --ignore-agent-tools --script sh
```

Set an environment variable for convenience:

```bash
export INFRAKIT_SRC=/mnt/c/GitHub/infrakit
uvx --from "$INFRAKIT_SRC" infrakit init demo-env --ai copilot --iac crossplane --ignore-agent-tools --script ps
```

(Optional) Define a shell function:

```bash
infrakit-dev() { uvx --from /mnt/c/GitHub/infrakit infrakit "$@"; }
# Then
infrakit-dev --help
```

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
python -c "import infrakit_cli; print('Import OK')"
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
mkdir /tmp/infrakit-test && cd /tmp/infrakit-test
python -m src.infrakit_cli init --here --ai claude --iac crossplane --ignore-agent-tools --script sh  # if repo copied here
```

Or copy only the modified CLI portion if you want a lighter sandbox.

## 9. Debug Network / TLS Skips

If you need to bypass TLS validation while experimenting:

```bash
infrakit check --skip-tls
infrakit init demo --iac crossplane --skip-tls --ai gemini --ignore-agent-tools --script ps
```

(Use only for local experimentation.)

## 10. Rapid Edit Loop Summary

| Action | Command |
|--------|---------|
| Run CLI directly | `python -m src.infrakit_cli --help` |
| Editable install | `uv pip install -e .` then `infrakit ...` |
| Local uvx run (repo root) | `uvx --from . infrakit ...` |
| Local uvx run (abs path) | `uvx --from /mnt/c/GitHub/infrakit infrakit ...` |
| Git branch uvx | `uvx --from git+URL@branch infrakit ...` |
| Build wheel | `uv build` |

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
