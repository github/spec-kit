### 2. Initialize a project

```bash
specify init my-project --integration copilot
cd my-project
```

> **Want to see the whole flow on one small project?** Follow the [Quick Start Guide](https://github.github.io/spec-kit/quickstart.html) for the Taskify walkthrough: `/speckit.specify` → `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`.

To check for updates or upgrade the installed CLI, use the self-management commands. See the [Upgrade Guide](./docs/upgrade.md) for detailed scenarios and customization options.

```bash
# Check whether a newer release is available (read-only — does not modify anything)
specify self check

# Preview what would run, without actually upgrading
specify self upgrade --dry-run

# Upgrade in place to the latest stable release (auto-detects uv tool vs pipx install)
specify self upgrade

# Or pin a specific release tag (replace vX.Y.Z[suffix] with your desired release tag)
specify self upgrade --tag vX.Y.Z[suffix]
```

Bare `specify self upgrade` executes immediately, matching the no-prompt behavior of commands like `pip install -U` and `npm update`. For `uv tool` installs, it runs `uv tool install specify-cli --force --from <git ref>` under the hood so pinned release tags work, including dev, alpha/beta/rc, or build metadata suffixes. `uvx` (ephemeral) runs and source checkouts are detected and produce path-specific guidance instead of running an installer. Set `SPECIFY_UPGRADE_TIMEOUT_SECS` to cap how long the installer subprocess may run (default: no timeout — interrupt with `Ctrl+C` if needed).