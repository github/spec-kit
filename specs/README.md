# Specifications Directory

This directory contains all feature specifications, implementation plans, and task breakdowns.

## Structure

Each feature should have its own directory with the following structure:

```
specs/
├── 001-feature-name/
│   ├── spec.md          # Feature specification
│   ├── plan.md          # Implementation plan
│   ├── tasks.md         # Task breakdown
│   ├── research.md      # Research notes (optional)
│   ├── data-model.md    # Data model (if applicable)
│   ├── quickstart.md    # Quick start guide (optional)
│   └── contracts/       # API contracts and schemas
│       ├── api.yaml
│       └── schema.json
└── README.md            # This file
```

## Creating New Specifications

Use the AI agent commands:

1. `/specify <feature-description>` - Create a new specification
2. `/plan <feature-name>` - Generate implementation plan
3. `/tasks <feature-name>` - Break down into tasks

## Naming Convention

Use the format: `NNN-feature-name` where:
- `NNN` is a zero-padded sequence number (001, 002, etc.)
- `feature-name` is a kebab-case description
