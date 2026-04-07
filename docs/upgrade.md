# Upgrade Guide

> You have InfraKit installed and want to upgrade to the latest version. This guide covers upgrading the CLI tool and refreshing your project's command files.

---

## Quick Reference

| What to Upgrade | Command | When |
|----------------|---------|------|
| **CLI only** | `uv tool install infrakit-cli --force --from git+https://github.com/neelneelpurk/infrakit.git` | Get latest CLI features |
| **Project files** | `infrakit init --here --force --ai <agent> --iac <crossplane\|terraform>` | Get updated slash commands and templates |
| **Both** | Run CLI upgrade, then project update | Recommended for major versions |

---

## Part 1: Upgrade the CLI

### Persistent installation

```bash
uv tool install infrakit-cli --force --from git+https://github.com/neelneelpurk/infrakit.git
```

### One-shot `uvx` usage

No action needed — `uvx` always fetches the latest version.

### Verify

```bash
infrakit check
```

---

## Part 2: Refresh Project Files

When InfraKit releases new or updated slash commands, refresh your project:

```bash
infrakit init --here --force --ai <your-agent> --iac crossplane
```

Replace `<your-agent>` with your AI assistant. See [Supported AI Agents](../README.md#supported-ai-agents).

### What gets updated

- ✅ Slash command files (`.claude/commands/`, `.github/prompts/`, etc.)
- ✅ IaC-specific agent persona files (`.infrakit/agent_personas/`)

### What stays safe

These files are **never touched** during an upgrade:

- ✅ `.infrakit/context.md` — your project context
- ✅ `.infrakit/coding-style.md` — your coding standards
- ✅ `.infrakit/tagging.md` — your tagging requirements
- ✅ `.infrakit/tracks/` — all track directories with spec, plan, and tasks
- ✅ `.infrakit/tracks.md` — track registry
- ✅ Your infrastructure YAML source files
- ✅ Your git history

### Understanding `--force`

Without `--force`, the CLI asks for confirmation when the directory is non-empty. With `--force`, it skips the prompt and merges immediately. Your `.infrakit/` configuration files are not overwritten.

---

## Troubleshooting

### Slash commands not showing up after upgrade

1. Restart your IDE or AI agent completely
2. Verify command files exist:

   ```bash
   ls .claude/commands/ | grep infrakit     # Claude Code
   ls .gemini/commands/ | grep infrakit     # Gemini CLI
   ls .github/prompts/ | grep infrakit      # GitHub Copilot
   ```

3. Re-run `infrakit init --here --force --ai <agent> --iac crossplane`

### CLI upgrade not working

```bash
uv tool uninstall infrakit-cli
uv tool install infrakit-cli --from git+https://github.com/neelneelpurk/infrakit.git
```

---

## Do I need to run `infrakit` every time?

No. Run `infrakit init` once per project (or when upgrading). Once the slash commands are installed in your project's agent folder, your AI agent reads them directly — no need to run `infrakit` again for day-to-day use.
