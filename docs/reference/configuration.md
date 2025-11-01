# Configuration Reference

Project structure and configuration files.

## Directory Structure

```
project-root/
├── .specify/                    # Spec Kit configuration
│   ├── config.yml              # Project-level configuration
│   ├── templates/              # Custom templates (optional)
│   │   ├── spec-template.md
│   │   └── plan-template.md
│   ├── memory/                 # Project context
│   │   ├── constitution.md     # Project principles
│   │   └── .gitignore
│   ├── scripts/                # Automation scripts
│   │   ├── *.sh               # Bash scripts
│   │   └── *.ps1              # PowerShell scripts
│   └── docs/                   # Internal documentation
│
├── specs/                       # Feature specifications
│   ├── proj-1.feature-name/
│   │   ├── spec.md
│   │   ├── plan.md
│   │   └── cap-001-capability/  # For large features
│   │       └── plan.md
│   └── proj-2.another-feature/
│
├── docs/                        # Project documentation
│   ├── product-vision.md       # (optional) Product vision
│   ├── system-architecture.md  # System architecture
│   └── ...
│
├── .claude/commands/           # Claude Code commands
├── .gemini/commands/           # Gemini CLI commands
├── .copilot/commands/          # GitHub Copilot commands
│
├── .gitignore
├── README.md
└── [project files...]
```

## Configuration Files

### `config.yml`
Project-level Spec Kit configuration.

**Example**:
```yaml
project:
  name: My Project
  ai_assistant: claude
  script_type: sh

specs:
  location: specs/
  naming_pattern: proj-{id}.{name}

templates:
  location: .specify/templates/
```

## File Naming Conventions

### Specification IDs
```
proj-NNN.feature-name/
```

Example: `proj-123.user-authentication/`

### Capability IDs
```
cap-NNN-capability-name/
```

Example: `cap-001-email-verification/`

## Ignoring Files

The `.specify/` directory should be committed to git (it contains templates and config).

The `specs/` directory should be committed (it's documentation).

Generated files are typically in `.gitignore`:
- `.specify/scripts/` - Generated from templates
- `[project]/.claude/` - AI agent-specific
- `[project]/.gemini/` - AI agent-specific
- etc.

## Customization

### Custom Templates
Place custom templates in `.specify/templates/` matching the template name:
```
.specify/templates/spec-template.md         # Custom spec template
.specify/templates/plan-template.md         # Custom plan template
```

### Configuration Updates
Update `.specify/config.yml` to customize project settings.

### Scripts
Add custom scripts to `.specify/scripts/` for project-specific automation.

## Multi-Repo Workspaces

For multi-repo projects, see [Workspace Configuration](./workspace-config.md).

## Related

- [Getting Started](../getting-started/) - Initial setup
- [Workspace Config](./workspace-config.md) - Multi-repo configuration
- [Templates](./templates.md) - Template documentation
