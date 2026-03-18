# Spec Kit Utilities Extension

Session management and validation tools for Spec Kit projects.

## Commands

### Resume (`/speckit.speckit-utils.resume`)

Scan your project for active features and get a prompt to continue where you left off.

```
/speckit.speckit-utils.resume
/speckit.speckit-utils.resume 001-auth
```

Detects which SDD phase each feature is in (specify, plan, tasks, implement, complete) and suggests the next command.

### Doctor (`/speckit.speckit-utils.doctor`)

Validate project health across five categories:

- Templates: all required templates present
- Agent config: AI agent directory and commands registered
- Scripts: bash/powershell scripts exist and are executable
- Constitution: project constitution exists with content
- Features: spec/plan/tasks artifacts present for each feature

```
/speckit.speckit-utils.doctor
```

### Validate (`/speckit.speckit-utils.validate`)

Verify that completed tasks produced expected files and that spec requirements trace to tasks.

```
/speckit.speckit-utils.validate
/speckit.speckit-utils.validate 001-auth
/speckit.speckit-utils.validate --strict
```

## Installation

```bash
specify extension add speckit-utils
```

## Hooks

The extension optionally hooks into:

- `after_specify`: prompts to run doctor (project health check)
- `after_plan`: prompts to run validate (requirement traceability)

## License

MIT
