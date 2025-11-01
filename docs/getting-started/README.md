# Getting Started

Welcome to Spec-Driven Development with Spec Kit! This section will get you up and running with your first project.

## Quick Navigation

- **[Installation Guide](./installation.md)** - Install the `specify` CLI tool
- **[Quick Start](./quickstart.md)** - Create your first spec in 4 steps
- **[Your First Spec](./first-spec.md)** - Step-by-step walkthrough of creating a real project

## 5-Minute Quick Path

```bash
# 1. Install the CLI
uvx --from git+https://github.com/hcnimi/spec-kit.git specify init my-project --ai claude

# 2. Create your first spec
cd my-project
/specify Build a simple photo album organizer

# 3. Create the implementation plan
/plan Use vanilla JavaScript and SQLite

# 4. Start implementing
/tasks
```

## Recommended Learning Path

1. **Start here**: [Installation Guide](./installation.md) - 5 minutes
2. **Then**: [Quick Start](./quickstart.md) - 10 minutes
3. **Deep dive**: [Your First Spec](./first-spec.md) - 30 minutes walkthrough
4. **Ready for more?** Check out [Guides](/guides/) for common tasks

## Core Concepts You'll Encounter

- **Specification** - Detailed description of what you want to build (the "what" and "why")
- **Implementation Plan** - Technical approach and architecture decisions (the "how")
- **Tasks** - Actionable breakdown of work items
- **Capabilities** - Atomic units of work for large features (400-1000 LOC each)

## Need Help?

- 📖 See [Concepts](/concepts/) to understand the methodology
- 🔍 Check [Reference](/reference/) for command and template documentation
- 🤝 Join our community or open an issue on [GitHub](https://github.com/hcnimi/spec-kit/issues)
