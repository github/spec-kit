# Shadow Mode Documentation

**Version:** 1.0.0
**Last Updated:** 2025

---

## Table of Contents

- [What is Shadow Mode?](#what-is-shadow-mode)
- [When to Use Shadow Mode](#when-to-use-shadow-mode)
- [Installation](#installation)
- [Configuration](#configuration)
- [Features](#features)
- [Conversion](#conversion)
- [Troubleshooting](#troubleshooting)
- [FAQ](#faq)

---

## What is Shadow Mode?

Shadow Mode is an installation option for Speckit that hides all Speckit-specific branding and files, providing a generic, customizable development toolkit perfect for corporate repositories.

### Key Characteristics

| Aspect | Standard Mode | Shadow Mode |
|--------|---------------|-------------|
| Scripts Location | `scripts/` (visible) | `.devtools/speckit/` (hidden) |
| Templates | Speckit-branded | Generic/unbranded |
| Commands | `/speckit.*` prefix | No prefix (e.g., `/specify`) |
| Configuration | `.speckit.config.json` | `.devtools/.config.json` |
| Visibility | Full Speckit presence | Hidden Speckit engine |
| Branding | Speckit branding | Custom brand name |
| .gitignore | Not added | `.devtools/` hidden by default |

### What Gets Hidden

In Shadow Mode:
- ✅ All scripts moved to `.devtools/speckit/`
- ✅ Speckit branding removed from templates
- ✅ Commands use generic names
- ✅ Configuration uses custom brand name
- ✅ Directory automatically added to `.gitignore`

### What Remains Functional

- ✅ All 32 scripts (16 bash + 16 PowerShell)
- ✅ Complete specification workflow
- ✅ Token management and optimization
- ✅ Quality validation
- ✅ Semantic code search
- ✅ AI agent integration

---

## When to Use Shadow Mode

### Ideal Use Cases

✅ **Corporate Repositories**
- Company requires internal branding
- Don't want external tool names visible
- Need to maintain brand consistency

✅ **Client Projects**
- Working on client codebases
- Client doesn't want Speckit visible
- Need professional, neutral appearance

✅ **Open Source Projects**
- Want generic development workflow
- Don't want tool-specific dependencies
- Prefer framework-agnostic approach

✅ **Team Standardization**
- Established internal methodologies
- Custom workflow names
- Existing documentation standards

### When NOT to Use Shadow Mode

❌ **Small Personal Projects**
- Shadow mode adds unnecessary complexity
- Standard mode is simpler

❌ **Learning/Experimentation**
- Standard mode has better documentation
- Easier to find resources and examples

❌ **Speckit Contribution**
- Need to understand Speckit internals
- Standard mode is more transparent

---

## Installation

### New Project Installation

#### Basic Shadow Mode

```bash
specify init my-project --mode shadow --ai claude
```

#### With Custom Branding

```bash
specify init my-project \
  --mode shadow \
  --brand "Acme DevTools" \
  --ai claude
```

#### Full Custom Setup

```bash
specify init my-project \
  --mode shadow \
  --brand "Your Company" \
  --shadow-path .internal/tools \
  --include-docs \
  --gitignore-shadow \
  --ai claude \
  --script sh
```

### Installation in Existing Directory

```bash
# Initialize in current directory
specify init --here --mode shadow --ai claude --force
```

### Installation Options

| Option | Default | Description |
|--------|---------|-------------|
| `--mode` | `standard` | Installation mode (`standard` or `shadow`) |
| `--brand` | `"Development Tools"` | Custom brand name |
| `--shadow-path` | `.devtools/speckit` | Where to hide scripts |
| `--include-docs` | `true` | Include generic documentation |
| `--gitignore-shadow` | `true` | Add to .gitignore |
| `--ai` | Interactive | AI assistant to use |
| `--script` | Auto-detect | Script type (`sh` or `ps`) |

---

## Configuration

### Configuration File Location

Shadow mode configuration is stored at:
```
.devtools/.config.json
```

### Configuration Structure

```json
{
  "mode": "shadow",
  "brand_name": "Development Tools",
  "speckit_version": "1.0.0",
  "shadow_path": ".devtools/speckit",
  "templates_path": "templates",
  "agent": "claude",
  "script_type": "sh",
  "scripts": {
    "sh": {
      "validate": ".devtools/speckit/scripts/bash/validate-spec.sh",
      "token_budget": ".devtools/speckit/scripts/bash/token-budget.sh",
      ...
    }
  },
  "claude_commands": [
    "specify", "plan", "tasks", "implement", "validate",
    "budget", "prune", "find", ...
  ]
}
```

### Customization

#### Change Brand Name

Edit `.devtools/.config.json`:
```json
{
  "brand_name": "Your Custom Name"
}
```

#### Change Shadow Path

**Not recommended after installation.** If needed:
1. Move `.devtools/speckit/` to new location
2. Update `shadow_path` in config
3. Update all script paths in config
4. Update command files with new paths

#### Add Custom Scripts

Add to `scripts` section:
```json
{
  "scripts": {
    "sh": {
      "custom_script": ".devtools/speckit/scripts/bash/custom.sh"
    }
  }
}
```

---

## Features

### All Scripts Included

Shadow mode includes all 32 Speckit scripts:

**Bash Scripts (16):**
- `validate-spec.sh` - Specification validation
- `token-budget.sh` - Token usage tracking
- `semantic-search.sh` - Natural language code search
- `session-prune.sh` - Context compression
- `error-analysis.sh` - AI-assisted debugging
- `clarify-history.sh` - Decision tracking
- `project-analysis.sh` - Project metrics
- `project-catalog.sh` - Component catalog
- `onboard.sh` - Onboarding materials
- `reverse-engineer.sh` - Code reverse engineering
- `create-new-feature.sh` - Feature scaffolding
- `setup-plan.sh` - Plan initialization
- `setup-ai-doc.sh` - AI documentation
- `update-agent-context.sh` - Context management
- `check-prerequisites.sh` - Tool verification
- `common.sh` - Shared utilities

**PowerShell Scripts (16):**
- Same functionality as bash scripts
- Windows-native implementation
- Full feature parity

### All Commands Available

Shadow mode provides 22 unbranded slash commands:

**Core Workflow:**
- `/specify` - Create specifications
- `/plan` - Generate implementation plans
- `/tasks` - Break down into tasks
- `/implement` - Execute implementation
- `/validate` - Validate specifications

**Quality & Analysis:**
- `/analyze` - Cross-artifact analysis
- `/checklist` - Quality checklists
- `/clarify` - Clarifying questions
- `/clarify-history` - Decision history

**Utilities:**
- `/budget` - Token budget tracking
- `/prune` - Session pruning
- `/find` - Semantic code search
- `/error-context` - Error analysis

**Project Management:**
- `/discover` - Project discovery
- `/document` - Documentation generation
- `/onboard` - Onboarding materials
- `/project-analysis` - Project metrics
- `/project-catalog` - Component catalog
- `/service-catalog` - Service catalog
- `/validate-contracts` - API validation

**Workflow:**
- `/resume` - Resume previous session
- `/constitution` - Project principles

---

## Conversion

### Convert Existing Project

#### Standard → Shadow

```bash
cd your-project
specify convert --to shadow --brand "Your Company"
```

#### Shadow → Standard

```bash
cd your-project
specify convert --to standard
```

### Conversion Process

#### What Happens During Conversion

**Standard → Shadow:**
1. Creates backup in `.devtools/backups/`
2. Moves `scripts/` to `.devtools/speckit/scripts/`
3. Replaces templates with generic versions
4. Replaces commands with unbranded versions
5. Creates `.devtools/.config.json`
6. Adds `.devtools/` to `.gitignore`
7. Removes `.speckit.config.json`

**Shadow → Standard:**
1. Creates backup in `.devtools/backups/`
2. Moves `.devtools/speckit/scripts/` to `scripts/`
3. Replaces templates with Speckit versions
4. Replaces commands with Speckit commands
5. Creates `.speckit.config.json`
6. Removes `.devtools/` directory
7. Updates `.gitignore`

### Conversion Options

```bash
# Convert without backup (not recommended)
specify convert --to shadow --no-backup

# Convert with custom brand
specify convert --to shadow --brand "Acme DevTools"

# Convert with custom shadow path
specify convert --to shadow --shadow-path .internal/tools
```

### Backup and Recovery

Backups are stored at:
```
.devtools/backups/
├── standard-mode-20250107-143022/
│   ├── scripts/
│   ├── templates/
│   └── .speckit.config.json
└── shadow-mode-20250107-150315/
    ├── speckit/
    └── .config.json
```

To restore from backup:
```bash
# Manually restore files from backup directory
cp -r .devtools/backups/standard-mode-*/scripts ./
cp -r .devtools/backups/standard-mode-*/templates ./
```

---

## Troubleshooting

### Common Issues

#### Scripts Not Found

**Problem:** Commands fail with "script not found"

**Solution:**
1. Verify shadow path in `.devtools/.config.json`
2. Check scripts exist: `ls .devtools/speckit/scripts/bash/`
3. Verify script permissions: `chmod +x .devtools/speckit/scripts/bash/*.sh`

#### Commands Not Working

**Problem:** Slash commands not recognized

**Solution:**
1. Verify commands exist: `ls .claude/commands/`
2. Check command syntax in `.claude/commands/*.md`
3. Restart AI agent

#### Wrong Script Type

**Problem:** Bash scripts called on Windows

**Solution:**
Update `.devtools/.config.json`:
```json
{
  "script_type": "ps"
}
```

#### Configuration Not Found

**Problem:** `specify info` shows "unknown mode"

**Solution:**
1. Verify `.devtools/.config.json` exists
2. Check JSON is valid
3. Ensure `mode: "shadow"` is set

### Getting Help

1. **Check configuration:** `specify info`
2. **Verify installation:** Check `.devtools/speckit/` exists
3. **Review logs:** Check command output for errors
4. **Validate setup:** Run `/validate` command

---

## FAQ

### Q: Can I use shadow mode with any AI agent?

**A:** Yes! Shadow mode supports all agents that standard mode supports:
- Claude Code
- GitHub Copilot
- Gemini CLI
- Cursor
- Qwen
- Codex
- And more

### Q: Does shadow mode affect performance?

**A:** No. Shadow mode is functionally identical to standard mode, just with different file locations and names.

### Q: Can I switch between modes?

**A:** Yes! Use `specify convert --to shadow` or `specify convert --to standard` to switch at any time. Backups are created automatically.

### Q: Will shadow mode receive updates?

**A:** Yes. Shadow mode uses the same scripts as standard mode. Updates to Speckit scripts benefit both modes.

### Q: Can I customize the brand name after installation?

**A:** Yes. Edit `.devtools/.config.json` and change `brand_name`. However, this won't retroactively change existing documentation.

### Q: Does shadow mode work offline?

**A:** Yes. All scripts run locally. Only initial installation requires internet (if using `specify init`).

### Q: Can I use shadow mode in a monorepo?

**A:** Yes. Install shadow mode in the monorepo root or in individual packages.

### Q: Does .gitignore always hide .devtools/?

**A:** By default, yes (`--gitignore-shadow` is true). You can disable with `--no-gitignore` if you want to commit shadow files.

### Q: Can I have both standard and shadow modes?

**A:** Not in the same project. However, you can have different modes in different projects or branches.

### Q: How do I update shadow mode scripts?

**A:** Currently, re-run installation or manually update scripts in `.devtools/speckit/scripts/`. Automatic update feature coming in future release.

---

## Additional Resources

- [Conversion Guide](shadow/CONVERSION.md) - Detailed conversion instructions
- [Workflow Guide](shadow/workflow.md) - Generic development workflow
- [Main README](../README.md) - Speckit overview

---

## Support

For issues or questions:
- Check troubleshooting section above
- Review [GitHub Issues](https://github.com/github/spec-kit/issues)
- Consult main documentation

---

**Version:** 1.0.0
**Last Updated:** January 2025
