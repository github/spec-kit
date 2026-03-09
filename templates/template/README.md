# My Template Pack

A custom template pack for Spec Kit.

## Overview

This template pack provides customized artifact templates for your development workflow.

## Templates Included

| Template | Type | Description |
|----------|------|-------------|
| `spec-template` | artifact | Custom feature specification template |

## Installation

```bash
# Install from local directory (during development)
specify template add --dev /path/to/this/directory

# Install from catalog (after publishing)
specify template add my-template-pack
```

## Usage

Once installed, templates are automatically resolved by the Spec Kit scripts.
When you run `specify specify` or create a new feature, your custom templates
will be used instead of the core defaults.

## Template Types

- **artifact** — Document scaffolds (spec.md, plan.md, tasks.md, etc.)
- **command** — AI agent prompts (the files in `.claude/commands/`, etc.)
- **script** — Custom scripts that replace core scripts

## Development

1. Edit templates in the `templates/` directory
2. Test with: `specify template add --dev .`
3. Verify with: `specify template resolve spec-template`

## Publishing

See the [Template Publishing Guide](../../docs/TEMPLATE-PUBLISHING-GUIDE.md) for details.

## License

MIT
