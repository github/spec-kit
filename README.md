<div align="center">
    <img src="./media/logo_large.webp" alt="InfraKit Logo" width="200" height="200"/>
    <h1>🌱 InfraKit</h1>
    <h3><em>Build production-ready infrastructure faster.</em></h3>
</div>

<p align="center">
    <strong>An open source infrastructure-first toolkit that brings constraint-driven development to IaC — specify what you need, let agents generate it.</strong>
</p>

<p align="center">
    <a href="https://github.com/github/infrakit/actions/workflows/release.yml"><img src="https://github.com/github/infrakit/actions/workflows/release.yml/badge.svg" alt="Release"/></a>
    <a href="https://github.com/github/infrakit/stargazers"><img src="https://img.shields.io/github/stars/github/infrakit?style=social" alt="GitHub stars"/></a>
    <a href="https://github.com/github/infrakit/blob/main/LICENSE"><img src="https://img.shields.io/github/license/github/infrakit" alt="License"/></a>
    <a href="https://github.github.io/infrakit/"><img src="https://img.shields.io/badge/docs-GitHub_Pages-blue" alt="Documentation"/></a>
</p>

---

## Table of Contents

- [🤔 What is InfraKit?](#-what-is-infrakit)
- [⚡ Get Started](#-get-started)
- [🤖 Supported AI Agents](#-supported-ai-agents)
- [🔧 InfraKit CLI Reference](#-infrakit-cli-reference)
- [📚 Core Philosophy](#-core-philosophy)
- [🔧 Prerequisites](#-prerequisites)
- [📖 Learn More](#-learn-more)
- [🔍 Troubleshooting](#-troubleshooting)
- [💬 Support](#-support)
- [🙏 Acknowledgements](#-acknowledgements)
- [📄 License](#-license)

## 🤔 What is InfraKit?

InfraKit is an infrastructure-first toolkit that applies **Constraint-Driven Development** to Infrastructure as Code. Instead of writing YAML or HCL by hand, you describe what infrastructure you need — InfraKit's AI agent workflow produces production-ready manifests through a structured spec → plan → implement → review → validate pipeline.

At launch InfraKit supports **Crossplane** (Kubernetes-native IaC). Support for Terraform, Pulumi, CloudFormation, and OpenTofu is on the roadmap.

## ⚡ Get Started

### 1. Install InfraKit CLI

#### Option 1: Persistent Installation (Recommended)

```bash
uv tool install infrakit-cli --from git+https://github.com/github/infrakit.git
```

Then use the tool directly:

```bash
# Create a new Crossplane project
infrakit init my-infra --ai claude --iac crossplane

# Or initialize in an existing project
infrakit init . --ai claude --iac crossplane
# or
infrakit init --here --ai claude --iac crossplane

# Check installed tools
infrakit check
```

To upgrade InfraKit, see the [Upgrade Guide](./docs/upgrade.md). Quick upgrade:

```bash
uv tool install infrakit-cli --force --from git+https://github.com/github/infrakit.git
```

#### Option 2: One-time Usage

```bash
uvx --from git+https://github.com/github/infrakit.git infrakit init my-infra --iac crossplane
```

### 2. Establish infrastructure principles

Launch your AI assistant in the project directory. Use **`/infrakit:constitution`** to define your project's governing infrastructure principles — security standards, tagging requirements, environment policies, and compliance rules that guide all subsequent resources.

```bash
/infrakit:constitution Create principles for a production AWS environment with mandatory encryption, private networking, multi-AZ for production, and required cost-center tagging.
```

### 3. Specify a resource

Use **`/infrakit:specify_composition`** to describe the infrastructure resource you need.

```bash
/infrakit:specify_composition I need a managed PostgreSQL database that developers can claim with a simple Kubernetes manifest. It should support dev and prod environments with different sizing, enforce encryption at rest, and expose connection details as a secret.
```

### 4. Create an implementation plan

Use **`/infrakit:plan_composition`** for architecture review and implementation planning.

```bash
/infrakit:plan_composition
```

### 5. Generate Crossplane YAML

Use **`/infrakit:implement_composition`** to generate the XRD, Composition, and example Claim.

```bash
/infrakit:implement_composition
```

### 6. Review and validate

```bash
/infrakit:review_composition    # Best-practices + coding-style review
/infrakit:validate_composition  # Run crossplane render validation
```

For a detailed step-by-step walkthrough, see our [complete guide](./constraint-driven.md).

## 🤖 Supported AI Agents

| Agent                                                                                | Support | Notes                                                                                                                                     |
| ------------------------------------------------------------------------------------ | ------- | ----------------------------------------------------------------------------------------------------------------------------------------- |
| [Qoder CLI](https://qoder.com/cli)                                                   | ✅      |                                                                                                                                           |
| [Amazon Q Developer CLI](https://aws.amazon.com/developer/learning/q-developer-cli/) | ⚠️      | Amazon Q Developer CLI [does not support](https://github.com/aws/amazon-q-developer-cli/issues/3064) custom arguments for slash commands. |
| [Amp](https://ampcode.com/)                                                          | ✅      |                                                                                                                                           |
| [Auggie CLI](https://docs.augmentcode.com/cli/overview)                              | ✅      |                                                                                                                                           |
| [Claude Code](https://www.anthropic.com/claude-code)                                 | ✅      |                                                                                                                                           |
| [CodeBuddy CLI](https://www.codebuddy.ai/cli)                                        | ✅      |                                                                                                                                           |
| [Codex CLI](https://github.com/openai/codex)                                         | ✅      |                                                                                                                                           |
| [Cursor](https://cursor.sh/)                                                         | ✅      |                                                                                                                                           |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli)                            | ✅      |                                                                                                                                           |
| [GitHub Copilot](https://code.visualstudio.com/)                                     | ✅      |                                                                                                                                           |
| [IBM Bob](https://www.ibm.com/products/bob)                                          | ✅      | IDE-based agent with slash command support                                                                                                |
| [Jules](https://jules.google.com/)                                                   | ✅      |                                                                                                                                           |
| [Kilo Code](https://github.com/Kilo-Org/kilocode)                                    | ✅      |                                                                                                                                           |
| [opencode](https://opencode.ai/)                                                     | ✅      |                                                                                                                                           |
| [Qwen Code](https://github.com/QwenLM/qwen-code)                                     | ✅      |                                                                                                                                           |
| [Roo Code](https://roocode.com/)                                                     | ✅      |                                                                                                                                           |
| [SHAI (OVHcloud)](https://github.com/ovh/shai)                                       | ✅      |                                                                                                                                           |
| [Windsurf](https://windsurf.com/)                                                    | ✅      |                                                                                                                                           |
| [Antigravity (agy)](https://agy.ai/)                                                 | ✅      |                                                                                                                                           |
| Generic                                                                              | ✅      | Bring your own agent — use `--ai generic --ai-commands-dir <path>` for unsupported agents                                                 |

## 🔧 InfraKit CLI Reference

The `infrakit` command supports the following options:

### Commands

| Command | Description                                                                                                                                             |
| ------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `init`  | Initialize a new InfraKit project from the latest template                                                                                              |
| `check` | Check for installed tools (`git`, `claude`, `gemini`, `code`/`code-insiders`, `cursor-agent`, `windsurf`, `qwen`, `opencode`, `codex`, `shai`, `qodercli`) |

### `infrakit init` Arguments & Options

| Argument/Option        | Type     | Description                                                                                                                                                                                  |
| ---------------------- | -------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `<project-name>`       | Argument | Name for your new project directory (optional if using `--here`, or use `.` for current directory)                                                                                           |
| `--ai`                 | Option   | AI assistant to use: `claude`, `gemini`, `copilot`, `cursor-agent`, `qwen`, `opencode`, `codex`, `windsurf`, `kilocode`, `auggie`, `roo`, `codebuddy`, `amp`, `shai`, `q`, `agy`, `bob`, `qodercli`, or `generic` (requires `--ai-commands-dir`) |
| `--ai-commands-dir`    | Option   | Directory for agent command files (required with `--ai generic`, e.g. `.myagent/commands/`)                                                                                                  |
| `--iac`                | Option   | IaC tool to use: `crossplane`                                                                                                                                                                |
| `--script`             | Option   | Script variant to use: `sh` (bash/zsh) or `ps` (PowerShell)                                                                                                                                  |
| `--ignore-agent-tools` | Flag     | Skip checks for AI agent tools like Claude Code                                                                                                                                              |
| `--no-git`             | Flag     | Skip git repository initialization                                                                                                                                                           |
| `--here`               | Flag     | Initialize project in the current directory instead of creating a new one                                                                                                                    |
| `--force`              | Flag     | Force merge/overwrite when initializing in current directory (skip confirmation)                                                                                                             |
| `--skip-tls`           | Flag     | Skip SSL/TLS verification (not recommended)                                                                                                                                                  |
| `--debug`              | Flag     | Enable detailed debug output for troubleshooting                                                                                                                                             |
| `--github-token`       | Option   | GitHub token for API requests (or set GH_TOKEN/GITHUB_TOKEN env variable)                                                                                                                    |
| `--ai-skills`          | Flag     | Install Prompt.MD templates as agent skills in agent-specific `skills/` directory (requires `--ai`)                                                                                          |

### Examples

```bash
# Basic project initialization with Crossplane
infrakit init my-infra --ai claude --iac crossplane

# Initialize with specific AI assistant
infrakit init my-infra --ai gemini --iac crossplane

# Initialize with Cursor support
infrakit init my-infra --ai cursor-agent --iac crossplane

# Initialize with PowerShell scripts (Windows/cross-platform)
infrakit init my-infra --ai copilot --iac crossplane --script ps

# Initialize in current directory
infrakit init . --ai claude --iac crossplane
# or use the --here flag
infrakit init --here --ai claude --iac crossplane

# Force merge into current (non-empty) directory without confirmation
infrakit init . --force --ai claude --iac crossplane

# Skip git initialization
infrakit init my-infra --ai gemini --iac crossplane --no-git

# Enable debug output for troubleshooting
infrakit init my-infra --ai claude --iac crossplane --debug

# Use GitHub token for API requests (helpful for corporate environments)
infrakit init my-infra --ai claude --iac crossplane --github-token ghp_your_token_here

# Install agent skills with the project
infrakit init my-infra --ai claude --iac crossplane --ai-skills

# Initialize with an unsupported agent (generic / bring your own agent)
infrakit init my-infra --ai generic --ai-commands-dir .myagent/commands/ --iac crossplane

# Check system requirements
infrakit check
```

### Available Slash Commands

After running `infrakit init`, your AI coding agent will have access to these slash commands:

#### IaC-Native Commands (Crossplane)

| Command                          | Agent Role              | Description                                               |
| -------------------------------- | ----------------------- | --------------------------------------------------------- |
| `/infrakit:setup`                | —                       | Initialize `.infrakit/` project config                    |
| `/infrakit:specify_composition`  | Cloud Solutions Engineer | Create infrastructure resource specification              |
| `/infrakit:plan_composition`     | Cloud Architect         | Architecture review + implementation plan                 |
| `/infrakit:implement_composition`| Crossplane Engineer     | Generate XRD, Composition, and Claim YAML                 |
| `/infrakit:review_composition`   | Cloud Architect         | Review against Crossplane best practices + coding style   |
| `/infrakit:validate_composition` | —                       | Run `crossplane render` validation                        |
| `/infrakit:new_composition`      | Cloud Solutions Engineer | Full multi-agent flow for a new resource                  |
| `/infrakit:update_composition`   | Cloud Solutions Engineer | Update an existing composition                            |
| `/infrakit:status`               | —                       | Track progress dashboard                                  |

#### Generic Commands

| Command                   | Description                                                       |
| ------------------------- | ----------------------------------------------------------------- |
| `/infrakit:constitution`  | Define infrastructure principles and standards                    |
| `/infrakit:clarify`       | Resolve ambiguities before planning                               |
| `/infrakit:tasks`         | Generate actionable task breakdown                                |
| `/infrakit:analyze`       | Cross-artifact consistency check                                  |
| `/infrakit:checklist`     | Quality validation checklist                                      |

### Environment Variables

| Variable            | Description                                                                                                                                                                                            |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `INFRAKIT_RESOURCE` | Override resource detection for non-Git repositories. Set to the resource track directory name (e.g., `postgres-db-init-20260401-120000`) to work on a specific resource when not using Git branches. |

## 📚 Core Philosophy

Constraint-Driven Development for infrastructure means:

- **Spec before YAML** — define *what* the resource must do before generating any code
- **Multi-agent review** — Cloud Solutions Engineer gathers requirements, Cloud Architect reviews for security/cost/reliability, IaC Engineer generates verified manifests
- **Never guess schemas** — always verify apiVersions, field names, and patch paths against provider documentation before writing YAML
- **Coding standards enforced** — mandatory tagging, Pipeline mode compositions, providerConfigRef patterns baked into every resource

## 🌟 Development Phases

| Phase                                    | Focus                         | Key Activities                                                                                          |
| ---------------------------------------- | ----------------------------- | ------------------------------------------------------------------------------------------------------- |
| **0-to-1** ("Greenfield")                | New infrastructure resources  | Specify resource requirements, generate XRD + Composition + Claim from scratch                         |
| **Iterative Enhancement** ("Brownfield") | Update existing compositions  | Modify specs, regenerate YAML, validate changes don't break existing claims                             |

## 🔧 Prerequisites

- **Linux/macOS/Windows**
- [Supported](#-supported-ai-agents) AI coding agent
- [uv](https://docs.astral.sh/uv/) for package management
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)
- `kubectl` (for Crossplane projects)

If you encounter issues with an agent, please open an issue so we can refine the integration.

## 📖 Learn More

- **[Complete Constraint-Driven Development Methodology](./constraint-driven.md)** — Deep dive into the full process
- **[Upgrade Guide](./docs/upgrade.md)** — How to upgrade InfraKit

---

## 🔍 Troubleshooting

### Git Credential Manager on Linux

If you're having issues with Git authentication on Linux, you can install Git Credential Manager:

```bash
#!/usr/bin/env bash
set -e
echo "Downloading Git Credential Manager v2.6.1..."
wget https://github.com/git-ecosystem/git-credential-manager/releases/download/v2.6.1/gcm-linux_amd64.2.6.1.deb
echo "Installing Git Credential Manager..."
sudo dpkg -i gcm-linux_amd64.2.6.1.deb
echo "Configuring Git to use GCM..."
git config --global credential.helper manager
echo "Cleaning up..."
rm gcm-linux_amd64.2.6.1.deb
```

## 💬 Support

For support, please open a [GitHub issue](https://github.com/github/infrakit/issues/new). We welcome bug reports, feature requests, and questions about using InfraKit.

## 🙏 Acknowledgements

This project is heavily influenced by and based on the work and research of [John Lam](https://github.com/jflam).

## 📄 License

This project is licensed under the terms of the MIT open source license. Please refer to the [LICENSE](./LICENSE) file for the full terms.
