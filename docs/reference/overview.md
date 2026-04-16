# CLI Reference

The Specify CLI (`specify`) manages the full lifecycle of Spec-Driven Development — from project initialization to workflow automation.

## Core Commands

The foundational commands for creating and managing Spec Kit projects.

- **`specify init`** — scaffold a new project with templates, scripts, and an AI coding agent integration
- **`specify check`** — verify that required tools (Git, AI coding agents) are installed
- **`specify version`** — display version and system information

[Core Commands reference →](core.md)

## Integrations

Integrations connect Spec Kit to your AI coding agent. Each integration sets up the appropriate command files, context rules, and directory structures for a specific agent. Only one integration is active per project.

- **`specify integration list`** — see available integrations
- **`specify integration install`** / **`uninstall`** / **`switch`** / **`upgrade`** — manage the active integration

[Integrations reference →](integrations.md)

## Extensions

Extensions add new capabilities — domain-specific commands, external tool integrations, quality gates, and more. Multiple extensions can be installed side by side.

- **`specify extension search`** / **`add`** / **`remove`** — discover and manage extensions
- **`specify extension catalog`** — manage catalog sources for discovery and installation

[Extensions reference →](extensions.md)

## Presets

Presets customize how Spec Kit works — overriding templates, commands, and terminology without changing any tooling. Multiple presets can be stacked with priority ordering.

- **`specify preset search`** / **`add`** / **`remove`** — discover and manage presets
- **`specify preset resolve`** — trace which file wins in the resolution stack
- **`specify preset catalog`** — manage catalog sources

[Presets reference →](presets.md)

## Workflows

Workflows automate multi-step processes — chaining commands, prompts, shell steps, and human checkpoints into repeatable sequences with conditional logic, loops, and resume support.

- **`specify workflow run`** / **`resume`** / **`status`** — execute and monitor workflows
- **`specify workflow search`** / **`add`** / **`remove`** — discover and manage workflows
- **`specify workflow catalog`** — manage catalog sources

[Workflows reference →](workflows.md)
