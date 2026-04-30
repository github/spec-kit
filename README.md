<div align="center">
    <img src="./media/logo.svg" alt="InfraKit Logo" width="200" height="200"/>
    <h1>InfraKit</h1>
    <h3><em>Production-ready infrastructure. Spec it. Plan it. Ship it.</em></h3>
</div>

<p align="center">
    <a href="https://github.com/neelneelpurk/infrakit/actions/workflows/release.yml"><img src="https://github.com/neelneelpurk/infrakit/actions/workflows/release.yml/badge.svg" alt="Release"/></a>
    <a href="https://pypi.org/project/infrakit-cli/"><img src="https://img.shields.io/pypi/v/infrakit-cli" alt="PyPI"/></a>
    <a href="https://github.com/neelneelpurk/infrakit/blob/main/LICENSE"><img src="https://img.shields.io/github/license/neelneelpurk/infrakit" alt="License: MIT"/></a>
    <a href="https://github.com/neelneelpurk/infrakit/stargazers"><img src="https://img.shields.io/github/stars/neelneelpurk/infrakit?style=social" alt="GitHub Stars"/></a>
</p>

<p align="center">
    <strong>An open-source AI-native IaC toolkit that applies Constraint-Driven Development to infrastructure — specify what you need, let agents generate production-ready code.</strong>
</p>

---

## Table of Contents

- [Why InfraKit](#why-infrakit)
- [How It Works](#how-it-works)
- [Supported Tools](#supported-tools)
- [Quick Start](#quick-start)
- [The Track System](#the-track-system)
- [CLI Reference](#cli-reference)
- [Slash Command Reference](#slash-command-reference)
- [Compliance and Security](#compliance-and-security)
- [Configuration Reference](#configuration-reference)
- [Prerequisites](#prerequisites)
- [Learn More](#learn-more)
- [Troubleshooting](#troubleshooting)
- [Credits](#credits)
- [Support](#support)
- [License](#license)

---

## Why InfraKit

Writing IaC by hand is slow, error-prone, and inconsistent. Every engineer applies different naming conventions, forgets tags, and guesses at provider API field names. InfraKit eliminates that with a structured, AI-assisted pipeline that enforces your standards before any code is written.

| Without InfraKit | With InfraKit |
|-----------------|---------------|
| Weeks writing YAML/HCL by hand | Hours from spec to production-ready code |
| Forgotten tags discovered in audit | Tags enforced on every resource, every time |
| Guessed provider API field names | Field names verified against official docs before code is written |
| Ad-hoc requirements buried in tickets | Structured specs linking every decision to a requirement |
| No audit trail for architecture decisions | Changelogs, context files, and contracts committed alongside code |
| One engineer = one style | Coding standards enforced by every agent persona |

---

## How It Works

InfraKit applies **Constraint-Driven Development (CDD)**: constraints (standards, compliance requirements, coding rules) are captured first and used to drive code generation. No code is written before the spec is agreed upon.

### The Four-Persona Pipeline

```
Cloud Solutions Engineer → Cloud Architect → Cloud Security Engineer → IaC Engineer
      (requirements)           (design)          (compliance)          (implementation)
```

1. **Cloud Solutions Engineer** — Iteratively clarifies requirements until all constraints are captured. Writes `spec.md`.
2. **Cloud Architect** — Presents 2–3 named design options with trade-off tables (complexity, cost, flexibility, risk). You choose; the choice is recorded in the spec.
3. **Cloud Security Engineer** — Audits the spec against your compliance frameworks (SOC2, HIPAA, ISO 27001, CIS, NIST). Raises mandatory findings before implementation begins.
4. **IaC Engineer** — Generates the implementation plan, auto-generates a task list, executes each task in order while enforcing your coding standards, and writes post-implementation artifacts.

### The Workflow

```
init → setup → new_composition/create_terraform_code → plan → implement → review
```

`/infrakit:plan` automatically generates a `tasks.md` checkpoint list after you accept the plan. `/infrakit:implement` works through those tasks one by one, marking each complete, then writes the contract, context, and changelog after all tasks are done.

---

## Supported Tools

### IaC Platforms

| Platform | Status | Output Format | Resource Term |
|----------|--------|---------------|---------------|
| [Crossplane](https://crossplane.io/) | ✅ | YAML | Composition |
| [Terraform](https://www.terraform.io/) | ✅ | HCL | Module |
| Pulumi | 🗺️ Roadmap | — | — |
| CloudFormation | 🗺️ Roadmap | — | — |
| OpenTofu | 🗺️ Roadmap | — | — |

### AI Agents

| Agent | Flag | Notes |
|-------|------|-------|
| [Claude Code](https://www.anthropic.com/claude-code) | `--ai claude` | |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli) | `--ai gemini` | |
| [GitHub Copilot](https://code.visualstudio.com/) | `--ai copilot` | |
| [Cursor](https://cursor.sh/) | `--ai cursor-agent` | |
| [Windsurf](https://windsurf.com/) | `--ai windsurf` | |
| [Amp](https://ampcode.com/) | `--ai amp` | |
| [Auggie CLI](https://docs.augmentcode.com/cli/overview) | `--ai auggie` | |
| [CodeBuddy CLI](https://www.codebuddy.ai/cli) | `--ai codebuddy` | |
| [Codex CLI](https://github.com/openai/codex) | `--ai codex` | |
| [Kilo Code](https://github.com/Kilo-Org/kilocode) | `--ai kilocode` | |
| [opencode](https://opencode.ai/) | `--ai opencode` | |
| [Qwen Code](https://github.com/QwenLM/qwen-code) | `--ai qwen` | |
| [Roo Code](https://roocode.com/) | `--ai roo` | |
| [SHAI (OVHcloud)](https://github.com/ovh/shai) | `--ai shai` | |
| [Qoder CLI](https://qoder.com/cli) | `--ai qodercli` | |
| [Amazon Q Developer CLI](https://aws.amazon.com/developer/learning/q-developer-cli/) | `--ai q` | ⚠️ No custom args for slash commands |
| [Antigravity (agy)](https://agy.ai/) | `--ai agy` | |
| [IBM Bob](https://www.ibm.com/products/bob) | `--ai bob` | |
| Generic | `--ai generic` | Use with `--ai-commands-dir <path>` |

---

## Quick Start

### 1. Install InfraKit CLI

```bash
# Persistent installation (recommended)
uv tool install infrakit-cli --from git+https://github.com/neelneelpurk/infrakit.git

# One-time usage
uvx --from git+https://github.com/neelneelpurk/infrakit.git infrakit init my-infra --ai claude --iac crossplane
```

### 2. Initialize Your Project

```bash
# New directory
infrakit init my-infra --ai claude --iac crossplane

# Existing directory
infrakit init --here --ai claude --iac terraform

# With Terraform
infrakit init my-infra --ai claude --iac terraform
```

### 3. Configure Project Standards

Run this once per project in your AI agent. The Cloud Solutions Engineer guides you through cloud provider, naming conventions, security defaults, and tagging requirements.

```
/infrakit:setup
```

Produces:
- `.infrakit/context.md` — cloud provider, API groups, naming conventions
- `.infrakit/coding-style.md` — HCL/YAML coding standards
- `.infrakit/tagging-standard.md` — required resource tags

### 4. Create a Resource Specification

**Crossplane:**
```
/infrakit:new_composition PostgreSQL database for application teams
```

**Terraform:**
```
/infrakit:create_terraform_code database ./modules/database
```

The four-persona pipeline runs: Solutions Engineer → Architect (picks from 2–3 options) → Security Engineer → spec confirmed.

The track is registered in `.infrakit_tracks/tracks.md` with status `📝 spec-generated`.

### 5. Generate the Plan and Task List

```
/infrakit:plan <track-name>
```

The IaC Engineer:
1. Looks up provider API field names against official documentation (never guesses)
2. Designs variable/parameter → resource argument mappings
3. Designs output → attribute mappings
4. Writes `plan.md`

After you accept the plan, `tasks.md` is **automatically generated** with ordered, checkbox tasks for every phase of the implementation.

### 6. Implement

```
/infrakit:implement <track-name>
```

The IaC Engineer works through each task in `tasks.md`, marking `- [ ]` → `- [x]` as it goes. After all tasks complete, it writes:
- `.infrakit_context.md` — resource interface summary
- `.infrakit_changelog.md` — structured change entry
- `infrakit_composition_contract.md` / `.infrakit_terraform_contract.md` — interface contract from the actual code

### 7. Review

```
/infrakit:review <resource-directory>
```

Reviews generated code against your `coding-style.md` and `tagging-standard.md`. Findings are categorized CRITICAL / HIGH / MEDIUM / LOW and the engineer offers to apply fixes.

---

## The Track System

Every resource change gets its own **track** — a versioned directory that holds all artifacts for that change.

```
.infrakit_tracks/
├── tracks.md                          # Registry of all tracks and their status
└── tracks/
    └── postgres-database-20260401-120000/
        ├── spec.md                    # Requirements, parameters, outputs, security requirements
        ├── plan.md                    # Implementation plan: file structure, mappings, tagging strategy
        ├── tasks.md                   # Auto-generated task list (checkbox items for /implement)
        └── migration.md              # (Breaking changes only) migration steps and state impact

.infrakit/
├── config.yaml                       # iac_tool, ai_assistant, resource_term
├── context.md                        # Cloud provider, naming conventions, environment policies
├── coding-style.md                   # Mandatory coding standards
├── tagging-standard.md               # Required resource tags
├── mcp-use.md                        # MCP server usage guidelines
├── memory/                           # Project memory for AI agents
└── agent_personas/                   # Agent persona definitions
    ├── terraform_engineer.md
    └── crossplane_engineer.md
```

Per-resource artifacts written by `/infrakit:implement`:

```
<resource-directory>/
├── .infrakit_context.md               # Resource interface: variables, outputs, resources provisioned
├── .infrakit_changelog.md             # Structured change history (append-only)
└── infrakit_composition_contract.md   # API surface contract (Crossplane)
    OR .infrakit_terraform_contract.md # Module interface contract (Terraform)
```

### Track Status Lifecycle

| Status | Meaning | Next Step |
|--------|---------|-----------|
| 🔵 `initializing` | Track created, spec in progress | Complete requirements with Solutions Engineer |
| 📝 `spec-generated` | Spec confirmed by all personas | `/infrakit:plan <track-name>` |
| 📋 `planned` | Plan and task list generated | `/infrakit:implement <track-name>` |
| ⚙️ `in-progress` | Implementation underway | Continue with `/infrakit:implement` |
| ✅ `done` | Implementation complete | Review, merge, close track |
| ❌ `blocked` | Blocked — needs attention | Resolve blocker, update track status |

---

## CLI Reference

### Commands

| Command | Description |
|---------|-------------|
| `init` | Initialize a new InfraKit project from the latest template |
| `check` | Check for installed tools (`git`, `claude`, `gemini`, `kubectl`, `terraform`, etc.) |
| `mcp` | Install a pre-defined MCP server recipe into your agent's MCP config |
| `version` | Display version and system information |

### `infrakit init` Options

| Option | Type | Description |
|--------|------|-------------|
| `<project-name>` | Positional | Name for your new project directory |
| `--here` | Flag | Initialize in the current directory instead of a new subdirectory |
| `--ai` | Choice | AI assistant (see [Supported AI Agents](#ai-agents)) |
| `--ai-commands-dir` | Path | Command files directory (required with `--ai generic`) |
| `--iac` | Choice | IaC tool: `crossplane` or `terraform` |
| `--script` | Choice | Script type: `sh` (default) or `ps` (PowerShell) |
| `--ignore-agent-tools` | Flag | Skip AI agent tool availability checks |
| `--no-git` | Flag | Skip `git init` |
| `--force` | Flag | Skip confirmation when initializing in a non-empty directory |
| `--skip-tls` | Flag | Skip SSL/TLS verification for corporate proxies |
| `--debug` | Flag | Enable verbose diagnostic output |
| `--github-token` | String | GitHub API token (or set `GH_TOKEN` / `GITHUB_TOKEN`) |
| `--ai-skills` | Flag | Install Prompt.MD templates as agent skills |

### `infrakit init` Examples

```bash
# New project with Claude Code and Crossplane
infrakit init my-infra --ai claude --iac crossplane

# New project with Claude Code and Terraform
infrakit init my-infra --ai claude --iac terraform

# Initialize in the current directory
infrakit init --here --ai claude --iac crossplane

# Force merge into an existing non-empty directory
infrakit init --here --force --ai claude --iac crossplane

# Skip git initialization (useful in CI)
infrakit init my-infra --ai gemini --iac crossplane --no-git

# Corporate GitHub with PAT
infrakit init my-infra --ai claude --iac crossplane --github-token ghp_your_token

# Bring your own agent
infrakit init my-infra --ai generic --ai-commands-dir .myagent/commands/ --iac crossplane

# Check system prerequisites
infrakit check

# Install an MCP server
infrakit mcp
```

---

## Slash Command Reference

After `infrakit init`, your AI agent will have access to these slash commands. All commands are prefixed with `/infrakit:`.

### Generic Commands (all IaC tools)

| Command | Description |
|---------|-------------|
| `/infrakit:setup` | Configure project context, coding standards, and tagging requirements |
| `/infrakit:status` | Dashboard showing all tracks and their current status |
| `/infrakit:analyze <track>` | Cross-artifact consistency check — verifies spec, plan, and code are aligned |
| `/infrakit:architect-review <track>` | Cloud Architect review for architecture correctness, reliability, and cost |
| `/infrakit:security-review <track>` | Cloud Security Engineer compliance review (SOC2, HIPAA, ISO 27001, CIS, NIST) |

### Crossplane Commands

| Command | Description |
|---------|-------------|
| `/infrakit:new_composition` | Full solutioning workflow: Solutions Engineer → Architect → Security → spec |
| `/infrakit:update_composition` | Update an existing composition: brownfield scan → contract review → solutioning → spec |
| `/infrakit:plan <track>` | Crossplane Engineer generates implementation plan + auto-generates `tasks.md` |
| `/infrakit:implement <track>` | Execute tasks from `tasks.md`, mark complete, write context/changelog/contract |
| `/infrakit:review <directory>` | Review generated YAML against coding standards and tagging |
| `/infrakit:setup-coding-style` | Create or update project coding style standards |

### Terraform Commands

| Command | Description |
|---------|-------------|
| `/infrakit:create_terraform_code` | Full solutioning workflow: Solutions Engineer → Architect → Security → spec |
| `/infrakit:update_terraform_code` | Update an existing module: brownfield scan → contract review → solutioning → spec |
| `/infrakit:plan <track>` | Terraform Engineer generates HCL plan + auto-generates `tasks.md` |
| `/infrakit:implement <track>` | Execute tasks from `tasks.md`, mark complete, write context/changelog/contract |
| `/infrakit:review <directory>` | Review generated HCL against coding standards and tagging |
| `/infrakit:setup-coding-style` | Create or update project coding style standards |

### Command Flow

```
Greenfield (new resource):
  setup → new_composition / create_terraform_code
        → plan (tasks.md auto-generated)
        → implement → review

Brownfield (update existing resource):
  update_composition / update_terraform_code
    (scan existing code → regenerate contracts → solutioning → spec)
        → plan (tasks.md auto-generated)
        → implement → review

Optional review steps (before plan):
  architect-review → security-review → analyze
```

---

## Compliance and Security

The Cloud Security Engineer persona in `/infrakit:security-review` audits specs against:

| Framework | Coverage |
|-----------|----------|
| SOC 2 Type II | Encryption at rest, access controls, audit logging |
| HIPAA | PHI handling, data encryption, access management |
| ISO 27001 | Information security controls |
| CIS Benchmarks | Cloud provider hardening standards |
| NIST CSF | Identify, Protect, Detect, Respond, Recover |

Security requirements are embedded into the spec and enforced by the IaC Engineer during implementation. The IaC Engineer will refuse to write code that:

- Hardcodes secrets, passwords, or API keys
- Enables public network access without an explicit variable override with a description
- Skips encryption at rest for storage and database resources
- Uses local state in production Terraform modules

---

## Configuration Reference

### `.infrakit/config.yaml`

Written by `infrakit init`. Read by all slash commands.

```yaml
iac_tool: crossplane          # or terraform
ai_assistant: claude          # or gemini, copilot, etc.
resource_term: composition    # or module (set per iac_tool)
```

### `.infrakit/context.md`

Created by `/infrakit:setup`. Contains:
- Cloud provider (AWS, Azure, GCP)
- API group / namespace conventions
- Naming conventions for resources, parameters, and outputs
- Environment policy (dev, staging, prod)
- Security defaults (encryption, private networking, TLS)
- Required tags

### `.infrakit/coding-style.md`

Created by `/infrakit:setup-coding-style`. Contains mandatory conventions:
- File naming and structure
- Resource naming patterns
- Tagging approach (e.g., AWS `default_tags` in provider block)
- Backend configuration requirements
- Security defaults (no public access, encryption enabled)

### `.infrakit/tagging-standard.md`

Required tags applied to every managed resource. Both mandatory tags (always applied) and conditional tags (environment-specific) are supported.

---

## Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| [uv](https://docs.astral.sh/uv/) | Latest | Package management for `infrakit-cli` |
| [Python](https://www.python.org/downloads/) | 3.11+ | Required by `infrakit-cli` |
| [Git](https://git-scm.com/downloads) | Any | Project version control |
| A [supported AI agent](#ai-agents) | — | Running slash commands |
| [kubectl](https://kubernetes.io/docs/tasks/tools/) | Any | Crossplane projects |
| [crossplane](https://docs.crossplane.io/latest/cli/) | Latest | Optional: `crossplane render` validation |
| [terraform](https://developer.hashicorp.com/terraform/downloads) | 1.x+ | Terraform projects |

**Platform**: Linux, macOS, Windows

---

## Learn More

| Resource | Description |
|----------|-------------|
| [Quick Start Guide](./docs/quickstart.md) | End-to-end Crossplane workflow walkthrough |
| [Installation Guide](./docs/installation.md) | Detailed installation, upgrades, and corporate proxy setup |
| [Upgrade Guide](./docs/upgrade.md) | How to upgrade the CLI and update project template files |
| [Constraint-Driven Development](./constraint-driven.md) | Methodology deep dive: CDD principles and why they work |
| [CHANGELOG](./CHANGELOG.md) | Full version history and breaking changes |
| [CONTRIBUTING](./CONTRIBUTING.md) | How to contribute to InfraKit |

---

## Troubleshooting

### Git Credential Manager on Linux

```bash
wget https://github.com/git-ecosystem/git-credential-manager/releases/download/v2.6.1/gcm-linux_amd64.2.6.1.deb
sudo dpkg -i gcm-linux_amd64.2.6.1.deb
git config --global credential.helper manager
rm gcm-linux_amd64.2.6.1.deb
```

### Corporate Proxy / Self-Signed Certificates

```bash
infrakit init my-infra --ai claude --iac crossplane --skip-tls
```

### Template Download Fails

Use a GitHub personal access token if rate-limited or behind a firewall:

```bash
infrakit init my-infra --ai claude --iac crossplane --github-token ghp_your_token
```

Or set the environment variable:

```bash
export GH_TOKEN=ghp_your_token
infrakit init my-infra --ai claude --iac crossplane
```

### `tasks.md` Not Found When Running `/infrakit:implement`

`tasks.md` is auto-generated by `/infrakit:plan` after you accept the plan. If it is missing, run `/infrakit:plan <track-name>` again to regenerate it.

### Track Directory Not Found

Tracks live under `.infrakit_tracks/tracks/<track-name>/`. If you initialized with an older version of InfraKit (< 0.2.0), your tracks may be under `.infrakit/tracks/`. Move them:

```bash
mkdir -p .infrakit_tracks
mv .infrakit/tracks .infrakit_tracks/tracks
mv .infrakit/tracks.md .infrakit_tracks/tracks.md
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
