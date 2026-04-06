<div align="center">
    <img src="./media/logo.svg" alt="InfraKit Logo" width="200" height="200"/>
    <h1>InfraKit</h1>
    <h3><em>Build production-ready infrastructure faster.</em></h3>
</div>

<p align="center">
    <strong>An open source infrastructure-first toolkit that brings constraint-driven development to IaC — specify what you need, let agents generate it.</strong>
</p>

<p align="center">
    <a href="https://github.com/neelneelpurk/infrakit/actions/workflows/release.yml"><img src="https://github.com/neelneelpurk/infrakit/actions/workflows/release.yml/badge.svg" alt="Release"/></a>
    <a href="https://github.com/neelneelpurk/infrakit/stargazers"><img src="https://img.shields.io/github/stars/neelneelpurk/infrakit?style=social" alt="GitHub stars"/></a>
    <a href="https://github.com/neelneelpurk/infrakit/blob/main/LICENSE"><img src="https://img.shields.io/github/license/neelneelpurk/infrakit" alt="License"/></a>
</p>

---

## Table of Contents

- [What is InfraKit?](#what-is-infrakit)
- [Get Started](#get-started)
- [Supported AI Agents](#supported-ai-agents)
- [InfraKit CLI Reference](#infrakit-cli-reference)
- [Slash Commands](#slash-commands)
- [Core Philosophy](#core-philosophy)
- [Development Phases](#development-phases)
- [Prerequisites](#prerequisites)
- [Learn More](#learn-more)
- [Troubleshooting](#troubleshooting)
- [Credits](#credits)
- [Support](#support)
- [License](#license)

---

## What is InfraKit?

InfraKit is an infrastructure-first toolkit that applies **Constraint-Driven Development** to Infrastructure as Code. Instead of writing YAML by hand, you describe what infrastructure you need — InfraKit's AI agent workflow produces production-ready manifests through a structured **spec → plan → implement → review** pipeline.

Each infrastructure resource gets its own **track**: a directory under `.infrakit/tracks/` that holds the spec, plan, and task list. Multiple tracks can be in progress at once, and every step is transparent and reversible.

InfraKit supports **Crossplane** (Kubernetes-native IaC) and **Terraform** (HashiCorp IaC). Support for Pulumi, CloudFormation, and OpenTofu is on the roadmap.

---

## Get Started

### 1. Install InfraKit CLI

**Persistent installation (recommended):**

```bash
uv tool install infrakit-cli --from git+https://github.com/neelneelpurk/infrakit.git
```

**One-time usage:**

```bash
uvx --from git+https://github.com/neelneelpurk/infrakit.git infrakit init my-infra --ai claude --iac crossplane
```

### 2. Initialize your project

```bash
# New project
infrakit init my-infra --ai claude --iac crossplane

# Existing project
infrakit init --here --ai claude --iac crossplane
```

### 3. Configure project standards

In your AI agent, run `/infrakit:setup` to define your cloud provider, API groups, naming conventions, security requirements, and tagging policies.

```
/infrakit:setup
```

### 4. Create a new resource

Use the IaC-native creation command to kick off the multi-persona solutioning workflow: the Cloud Solutions Engineer gathers requirements and writes a spec, the Cloud Architect reviews it, and the Cloud Security Engineer checks compliance.

**Crossplane:**
```
/infrakit:new_composition PostgreSQL database for application teams
```

**Terraform:**
```
/infrakit:create_terraform_code database ./modules/database
```

### 5. Generate the implementation plan

```
/infrakit:plan <track-name>
```

The IaC Engineer generates a detailed plan: resource schema design, provider API versions (verified against official documentation), argument mappings, and tag requirements.

### 6. Generate tasks and implement

```
/infrakit:tasks <track-name>
/infrakit:implement <track-name>
```

The IaC Engineer works through each task, marking it complete as it goes. All code follows your `coding-style.md` and `tagging.md` exactly.

### 7. Review

```
/infrakit:review <resource-directory>
```

The IaC Engineer reviews the generated code against coding standards, tagging requirements, and argument coverage.

For a detailed walkthrough, see the [Quick Start Guide](./docs/quickstart.md).

---

## Supported AI Agents

| Agent | Support | Notes |
|-------|---------|-------|
| [Claude Code](https://www.anthropic.com/claude-code) | ✅ | |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli) | ✅ | |
| [GitHub Copilot](https://code.visualstudio.com/) | ✅ | |
| [Cursor](https://cursor.sh/) | ✅ | |
| [Windsurf](https://windsurf.com/) | ✅ | |
| [Amp](https://ampcode.com/) | ✅ | |
| [Auggie CLI](https://docs.augmentcode.com/cli/overview) | ✅ | |
| [CodeBuddy CLI](https://www.codebuddy.ai/cli) | ✅ | |
| [Codex CLI](https://github.com/openai/codex) | ✅ | |
| [Kilo Code](https://github.com/Kilo-Org/kilocode) | ✅ | |
| [opencode](https://opencode.ai/) | ✅ | |
| [Qwen Code](https://github.com/QwenLM/qwen-code) | ✅ | |
| [Roo Code](https://roocode.com/) | ✅ | |
| [SHAI (OVHcloud)](https://github.com/ovh/shai) | ✅ | |
| [Qoder CLI](https://qoder.com/cli) | ✅ | |
| [Jules](https://jules.google.com/) | ✅ | |
| [Amazon Q Developer CLI](https://aws.amazon.com/developer/learning/q-developer-cli/) | ⚠️ | Does not support custom arguments for slash commands |
| [Antigravity (agy)](https://agy.ai/) | ✅ | |
| [IBM Bob](https://www.ibm.com/products/bob) | ✅ | |
| Generic | ✅ | Use `--ai generic --ai-commands-dir <path>` for unsupported agents |

---

## InfraKit CLI Reference

### Commands

| Command | Description |
|---------|-------------|
| `init` | Initialize a new InfraKit project from the latest template |
| `check` | Check for installed tools (`git`, `claude`, `gemini`, `kubectl`, etc.) |
| `mcp` | Install a pre-defined MCP server recipe into your agent's MCP config |
| `version` | Display version and system information |

### `infrakit init` Options

| Option | Description |
|--------|-------------|
| `<project-name>` | Name for your new project directory (or use `.` / `--here`) |
| `--ai` | AI assistant: `claude`, `gemini`, `copilot`, `cursor-agent`, `qwen`, `opencode`, `codex`, `windsurf`, `kilocode`, `auggie`, `codebuddy`, `amp`, `shai`, `q`, `agy`, `bob`, `qodercli`, or `generic` |
| `--ai-commands-dir` | Command files directory (required with `--ai generic`) |
| `--iac` | IaC tool: `crossplane` or `terraform` |
| `--script` | Script type to use: `sh` or `ps` |
| `--ignore-agent-tools` | Skip AI agent tool checks |
| `--no-git` | Skip git repository initialization |
| `--here` | Initialize in the current directory |
| `--force` | Skip confirmation when initializing in a non-empty directory |
| `--skip-tls` | Skip SSL/TLS verification |
| `--debug` | Enable verbose diagnostic output |
| `--github-token` | GitHub token for API requests (or set `GH_TOKEN`/`GITHUB_TOKEN`) |
| `--ai-skills` | Install Prompt.MD templates as agent skills |

### Examples

```bash
# New project with Claude and Crossplane
infrakit init my-infra --ai claude --iac crossplane

# New project with Claude and Terraform
infrakit init my-infra --ai claude --iac terraform

# Initialize in the current directory
infrakit init --here --ai claude --iac crossplane

# Force merge into existing directory
infrakit init --here --force --ai claude --iac crossplane

# Skip git initialization
infrakit init my-infra --ai gemini --iac crossplane --no-git

# Use a token for corporate GitHub environments
infrakit init my-infra --ai claude --iac crossplane --github-token ghp_your_token

# Bring your own agent
infrakit init my-infra --ai generic --ai-commands-dir .myagent/commands/ --iac crossplane

# Check system requirements
infrakit check

# Install an MCP server
infrakit mcp
```

---

## Slash Commands

After `infrakit init`, your AI agent will have access to these slash commands.

### Generic Commands

| Command | Description |
|---------|-------------|
| `/infrakit:setup` | Configure project context, coding standards, and tagging requirements |
| `/infrakit:status` | Dashboard showing all tracks and their current status |
| `/infrakit:analyze <track>` | Verify spec/plan consistency and flag gaps |
| `/infrakit:implement <track>` | Execute tasks from tasks.md, marking each complete as it goes |
| `/infrakit:architect-review <track>` | Cloud Architect review of spec and plan |
| `/infrakit:security-review <track>` | Cloud Security Engineer compliance review (SOC2, HIPAA, etc.) |
| `/infrakit:tasks <track>` | Generate ordered task breakdown from spec and plan |
| `/infrakit:checklist <track>` | Generate a verification checklist for the track |

### Crossplane Commands

| Command | Description |
|---------|-------------|
| `/infrakit:new_composition` | Multi-persona workflow: solutioning → architect review → security review → spec |
| `/infrakit:update_composition` | Update an existing composition with the same review workflow |
| `/infrakit:plan <track>` | Crossplane Engineer generates implementation plan from spec |
| `/infrakit:review <directory>` | Crossplane Engineer code review against coding standards and tagging |

### Terraform Commands

| Command | Description |
|---------|-------------|
| `/infrakit:create_terraform_code` | Multi-persona workflow: solutioning → architect review → security review → spec |
| `/infrakit:update_terraform_code` | Update an existing Terraform module with the same review workflow |
| `/infrakit:plan <track>` | Terraform Engineer generates HCL implementation plan from spec |
| `/infrakit:review <directory>` | Terraform Engineer code review against coding standards and tagging |

---

## Core Philosophy

- **Spec before code** — define *what* the resource must do before any code is written
- **Multi-persona review** — Cloud Solutions Engineer gathers requirements, Cloud Architect reviews for architecture/cost/reliability, Cloud Security Engineer checks compliance, IaC Engineer implements
- **Never guess schemas** — all resource argument names and API versions are verified against official provider documentation before any code is written
- **Standards enforced** — mandatory tagging, security defaults, and coding conventions baked into every resource from the start

---

## Development Phases

| Phase | Focus | Key Activities |
|-------|-------|----------------|
| **Greenfield** | New infrastructure resources | Create spec, architect review, security review, generate plan, implement, review |
| **Brownfield** | Update existing compositions | Scan existing code, generate update spec, review changes, implement delta |

---

## Prerequisites

- Linux, macOS, or Windows
- A [supported AI agent](#supported-ai-agents)
- [uv](https://docs.astral.sh/uv/) for package management
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)
- `kubectl` (for Crossplane projects)
- `terraform` (for Terraform projects)

---

## Learn More

- **[Quick Start Guide](./docs/quickstart.md)** — End-to-end Crossplane workflow example
- **[Installation Guide](./docs/installation.md)** — Detailed installation and setup
- **[Upgrade Guide](./docs/upgrade.md)** — How to upgrade InfraKit CLI and project files
- **[Constraint-Driven Development](./constraint-driven.md)** — Deep dive into the methodology

---

## Troubleshooting

### Git Credential Manager on Linux

```bash
#!/usr/bin/env bash
set -e
wget https://github.com/git-ecosystem/git-credential-manager/releases/download/v2.6.1/gcm-linux_amd64.2.6.1.deb
sudo dpkg -i gcm-linux_amd64.2.6.1.deb
git config --global credential.helper manager
rm gcm-linux_amd64.2.6.1.deb
```

---

## Credits

InfraKit is inspired by and built upon the foundational work of the [speckit](https://github.com/github/speckit) project. We credit `speckit` for providing the base for this project's architecture and methodology.

---

## Support

Open a [GitHub issue](https://github.com/neelneelpurk/infrakit/issues/new) for bug reports, feature requests, or questions.

---

## License

This project is licensed under the MIT License. See [LICENSE](./LICENSE) for details.
