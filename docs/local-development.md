# Local Development Guide

This guide shows how to iterate on the `specify` CLI locally without publishing a release or committing to `main` first.

> Scripts now have Bash (`.sh`), PowerShell (`.ps1`), and Fish shell (`.fish`) variants. The CLI auto-selects based on OS unless you pass `--script sh|ps|fish`.

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

## 5. Local Template Testing

When modifying templates, command files, or adding new features (like fish shell support), you can test without creating GitHub releases by using local template packages.

### Environment Variable: SPECIFY_LOCAL_TEMPLATES

Set `SPECIFY_LOCAL_TEMPLATES=1` to make the CLI use locally built packages instead of downloading from GitHub:

```bash
# Build local packages
bash .github/workflows/scripts/create-release-packages.sh v0.0.0-dev

# Test with local packages
SPECIFY_LOCAL_TEMPLATES=1 uv run specify init ../test-project --ai cursor --script fish --no-git
```

### How It Works

When `SPECIFY_LOCAL_TEMPLATES=1` or `SPECIFY_DEV_MODE=1` is set:

1. **Skips GitHub API calls** - No network requests
2. **Searches `.genreleases/` directory** - Looks for locally built packages
3. **Pattern matching** - Finds `spec-kit-template-{agent}-{script}-{version}.zip`
4. **Uses latest** - If multiple versions, selects newest by filename
5. **Shows notification** - Displays: `LOCAL DEV MODE: Using {filename}`

**Implementation**: See `src/specify_cli/__init__.py` lines 463-496 in `download_template_from_github()`

### Building Local Packages

Use the release package script with environment variables to control what gets built:

```bash
# Build all packages (all agents x all scripts)
bash .github/workflows/scripts/create-release-packages.sh v0.0.0-dev

# Build only fish scripts (all agents)
SCRIPTS=fish bash .github/workflows/scripts/create-release-packages.sh v0.0.0-dev

# Build only cursor packages (all scripts)
AGENTS=cursor bash .github/workflows/scripts/create-release-packages.sh v0.0.0-dev

# Build specific combination
AGENTS=claude SCRIPTS=fish bash .github/workflows/scripts/create-release-packages.sh v0.0.0-dev
```

Packages are created in `.genreleases/` directory.

### Common Testing Workflows

**Test new agent support**:
```bash
# 1. Build packages for new agent
AGENTS=windsurf bash .github/workflows/scripts/create-release-packages.sh v0.0.0-dev

# 2. Test locally
SPECIFY_LOCAL_TEMPLATES=1 uv run specify init ../test-windsurf --ai windsurf --no-git

# 3. Verify agent files created
ls ../test-windsurf/.windsurf/workflows/
```

**Test new script type (e.g., fish)**:
```bash
# 1. Build fish packages for all agents
SCRIPTS=fish bash .github/workflows/scripts/create-release-packages.sh v0.0.0-dev

# 2. Test multiple agents
SPECIFY_LOCAL_TEMPLATES=1 uv run specify init ../test-cursor-fish --ai cursor --script fish --no-git
SPECIFY_LOCAL_TEMPLATES=1 uv run specify init ../test-claude-fish --ai claude --script fish --no-git

# 3. Verify fish scripts work
fish ../test-cursor-fish/.specify/scripts/fish/check-prerequisites.fish --help
```

**Iterate on template changes**:
```bash
# 1. Edit templates/commands/plan.md
vim templates/commands/plan.md

# 2. Rebuild specific package
AGENTS=claude SCRIPTS=sh bash .github/workflows/scripts/create-release-packages.sh v0.0.0-dev

# 3. Test change immediately
SPECIFY_LOCAL_TEMPLATES=1 uv run specify init ../test-template --ai claude --script sh --no-git

# 4. Verify change
cat ../test-template/.claude/commands/plan.md
```

### Benefits

- ✅ **Fast iteration** - No GitHub release needed
- ✅ **Offline development** - No network dependency
- ✅ **Safe testing** - Doesn't pollute releases
- ✅ **Realistic** - Uses production package format
- ✅ **Flexible** - Test any agent/script combination

### Cleanup

Remove test artifacts when done:

```bash
# Remove test projects
rm -rf ../test-*

# Remove local packages (optional)
rm -rf .genreleases/
```

## 6. Testing Script Permission Logic

After running an `init`, check that shell scripts are executable on POSIX systems:

```bash
ls -l scripts | grep .sh
# Expect owner execute bit (e.g. -rwxr-xr-x)
```
On Windows you will instead use the `.ps1` scripts (no chmod needed).

## 7. Run Lint / Basic Checks (Add Your Own)

Currently no enforced lint config is bundled, but you can quickly sanity check importability:
```bash
python -c "import specify_cli; print('Import OK')"
```

## 8. Build a Wheel Locally (Optional)

Validate packaging before publishing:

```bash
uv build
ls dist/
```
Install the built artifact into a fresh throwaway environment if needed.

## 9. Using a Temporary Workspace

When testing `init --here` in a dirty directory, create a temp workspace:

```bash
mkdir /tmp/spec-test && cd /tmp/spec-test
python -m src.specify_cli init --here --ai claude --ignore-agent-tools --script sh  # if repo copied here
```
Or copy only the modified CLI portion if you want a lighter sandbox.

## 10. Debug Network / TLS Skips

If you need to bypass TLS validation while experimenting:

```bash
specify check --skip-tls
specify init demo --skip-tls --ai gemini --ignore-agent-tools --script ps
```
(Use only for local experimentation.)

## 11. Rapid Edit Loop Summary

| Action | Command |
|--------|---------|
| Run CLI directly | `python -m src.specify_cli --help` |
| Editable install | `uv pip install -e .` then `specify ...` |
| Local uvx run (repo root) | `uvx --from . specify ...` |
| Local uvx run (abs path) | `uvx --from /mnt/c/GitHub/spec-kit specify ...` |
| Git branch uvx | `uvx --from git+URL@branch specify ...` |
| Build local packages | `bash .github/workflows/scripts/create-release-packages.sh` |
| Test with local packages | `SPECIFY_LOCAL_TEMPLATES=1 uv run specify init ...` |
| Build wheel | `uv build` |

## 12. Cleaning Up

Remove build artifacts / virtual env quickly:
```bash
rm -rf .venv dist build *.egg-info .genreleases/
```

## 13. Common Issues

| Symptom | Fix |
|---------|-----|
| `ModuleNotFoundError: typer` | Run `uv pip install -e .` |
| Scripts not executable (Linux) | Re-run init or `chmod +x scripts/*.sh` |
| Git step skipped | You passed `--no-git` or Git not installed |
| Wrong script type downloaded | Pass `--script sh` or `--script ps` explicitly |
| TLS errors on corporate network | Try `--skip-tls` (not for production) |
| "No matching package found" in local mode | Build packages first with `create-release-packages.sh` |
| Local mode not working | Check `.genreleases/` directory exists and has matching `*.zip` files |

## 14. Next Steps

- Update docs and run through Quick Start using your modified CLI
- Open a PR when satisfied
- (Optional) Tag a release once changes land in `main`

