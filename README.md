<div align="center">
    <h1>🧱 InfraKit</h1>
    <h3><em>Spec it. Plan it. Ship it.</em></h3>
</div>

<p align="center">
    <strong>spec-kit for IaC, with a multi-persona pipeline. Open-source; works with Claude Code, Codex, Gemini, Copilot, plus any generic agent; ships Crossplane and Terraform out of the box.</strong>
</p>

<p align="center">
    <a href="https://pypi.org/project/infrakit-cli/"><img src="https://img.shields.io/pypi/v/infrakit-cli?logo=pypi&logoColor=white&label=PyPI" alt="PyPI"/></a>
    <a href="https://pypi.org/project/infrakit-cli/"><img src="https://img.shields.io/pypi/pyversions/infrakit-cli?logo=python&logoColor=white" alt="Python versions"/></a>
    <a href="https://pypi.org/project/infrakit-cli/"><img src="https://img.shields.io/pypi/dm/infrakit-cli?logo=pypi&logoColor=white" alt="PyPI downloads"/></a>
    <a href="https://github.com/neelneelpurk/infrakit/actions/workflows/release.yml"><img src="https://img.shields.io/github/actions/workflow/status/neelneelpurk/infrakit/release.yml?branch=main&logo=githubactions&logoColor=white&label=release" alt="Release status"/></a>
    <a href="https://github.com/neelneelpurk/infrakit/blob/main/LICENSE"><img src="https://img.shields.io/github/license/neelneelpurk/infrakit" alt="License"/></a>
    <a href="https://github.com/neelneelpurk/infrakit/stargazers"><img src="https://img.shields.io/github/stars/neelneelpurk/infrakit?style=social" alt="GitHub stars"/></a>
</p>

---

## Table of Contents

- [🤔 What is InfraKit?](#-what-is-infrakit)
- [⚡ Get Started](#-get-started)
- [🤖 Supported AI Coding Agents](#-supported-ai-coding-agents)
- [🧰 Supported IaC Platforms](#-supported-iac-platforms)
- [🔤 Available Slash Commands](#-available-slash-commands)
- [📦 InfraKit CLI Reference](#-infrakit-cli-reference)
- [🧭 The Track System](#-the-track-system)
- [📚 Core Philosophy](#-core-philosophy)
- [🌟 Development Phases](#-development-phases)
- [📁 Examples](#-examples)
- [🔧 Prerequisites](#-prerequisites)
- [📋 Detailed Process](#-detailed-process)
- [🔍 Troubleshooting](#-troubleshooting)
- [📖 Learn More](#-learn-more)
- [💬 Support](#-support)
- [🙏 Acknowledgements](#-acknowledgements)
- [📄 License](#-license)

## 🤔 What is InfraKit?

InfraKit is **[spec-kit](https://github.com/github/spec-kit) for infrastructure-as-code**, with a multi-persona pipeline layered on top. Spec-kit pioneered Spec-Driven Development for application code: capture the spec first, then plan, then implement, with every artifact committed to git. InfraKit takes that shape, points it at Crossplane and Terraform, and inserts four specialized personas between the spec and the code so that cloud architecture, security compliance, and IaC implementation each get their own dedicated review pass.

Concretely: a **Cloud Solutions Engineer** persona translates intent into a structured spec. A **Cloud Architect** presents 2–3 design options with cost/reliability trade-offs. A **Cloud Security Engineer** flags structural patterns that commonly violate SOC 2, HIPAA, ISO 27001, CIS, and NIST controls *before any code is written*. An **IaC Engineer** then generates Crossplane YAML or Terraform HCL — and a full audit trail (spec, plan, task list, contract, changelog) lands alongside the code in git.

> **A note on compliance**: the security review is a heuristic LLM pass that flags common control violations against named frameworks. It is **not** a substitute for a real audit conducted by qualified humans with evidence collection. Use it as a first-pass guardrail, not as your compliance system of record.

## ⚡ Get Started

### 1. Install InfraKit CLI

Choose your preferred installation method:

> [!NOTE]
> The commands below require **[uv](https://docs.astral.sh/uv/)** — a fast Python package manager. If you see `command not found: uv`, [install uv first](https://docs.astral.sh/uv/getting-started/installation/). The `pipx` alternative does not require uv.

```bash
# Persistent installation (recommended) — installs the latest release from PyPI
uv tool install infrakit-cli

# Pin a specific release (replace X.Y.Z with the latest from
# https://pypi.org/project/infrakit-cli/ or the Releases page)
uv tool install infrakit-cli==X.Y.Z

# Alternative: pipx
pipx install infrakit-cli
```

Verify the install:

```bash
infrakit version
```

[![PyPI](https://img.shields.io/pypi/v/infrakit-cli?logo=pypi&logoColor=white&label=latest%20on%20PyPI)](https://pypi.org/project/infrakit-cli/)

#### One-time usage

Run directly without installing:

```bash
uvx infrakit-cli init my-infra --ai claude --iac crossplane
```

> [!TIP]
> Prompts, personas, and templates ship inside the wheel. `infrakit init` runs **entirely offline** — no GitHub tokens, no per-agent release zips, no network calls. Per-agent rendering (Claude / Gemini / Copilot / etc.) happens on your machine at init time.

### 2. Initialize your project

```bash
# New directory
infrakit init my-infra --ai claude --iac crossplane

# Existing directory
infrakit init --here --ai claude --iac terraform
```

In interactive sessions you'll be prompted for the AI agent and IaC tool. In CI or piped runs, pass `--ai` and `--iac` explicitly.

### 3. Configure project standards

Run your AI coding agent in the project directory. Use the **`/infrakit:setup`** command to capture your project's governing principles — these become the constraints every subsequent step must honour.

```text
/infrakit:setup AWS multi-account platform; SOC 2 + PCI-DSS in scope; encryption at rest mandatory; no public network access in prod
```

This generates `.infrakit/context.md`, `.infrakit/coding-style.md`, and `.infrakit/tagging-standard.md`.

### 4. Specify the resource

Describe **what** you want, not **how**. The Solutions Engineer iterates until the requirements are clear, then hands off to Architect and Security Engineer reviews.

**Crossplane**:

```text
/infrakit:new_composition A PostgreSQL Crossplane composition wrapping AWS RDS. Multi-AZ in prod, Multi-AZ defaults to false elsewhere. Per-instance customer-managed KMS key. No public access ever. Connection details published to a Kubernetes Secret in the claimer's namespace.
```

**Terraform**:

```text
/infrakit:create_terraform_code An AWS S3 bucket module. Encryption with a customer-managed KMS key, all four block_public_* flags set, TLS-only access via bucket policy, lifecycle on non-current versions, optional cross-region replication gated to prod.
```

The four-persona pipeline runs end-to-end. Output: a confirmed `spec.md` in `.infrakit_tracks/tracks/<track-name>/`.

### 5. Plan the implementation

```text
/infrakit:plan <track-name>
```

The IaC Engineer verifies provider API field names against official docs (never guessing), designs parameter → argument mappings, writes `plan.md`, and auto-generates `tasks.md` — an ordered, checkbox task list.

### 6. Execute the implementation

```text
/infrakit:implement <track-name>
```

The IaC Engineer works through each task in `tasks.md`, marks them complete, and writes the post-implementation artifacts (`.infrakit_context.md`, `.infrakit_changelog.md`, resource contract file) alongside the code.

### 7. Review

```text
/infrakit:review <resource-directory>
```

Reviews generated code against `coding-style.md` and `tagging-standard.md`. Findings are categorized CRITICAL / HIGH / MEDIUM / LOW; the engineer offers to apply fixes inline.

For a complete worked walkthrough, see [`examples/`](./examples/).

## 🤖 Supported AI Coding Agents

InfraKit installs slash commands (or skills via `--ai-skills`) into any of these five agents:

| Agent                                                                                | Flag             | Subagents | Notes                                                                |
| ------------------------------------------------------------------------------------ | ---------------- | --------- | -------------------------------------------------------------------- |
| [Claude Code](https://www.anthropic.com/claude-code)                                 | `--ai claude`    | ✅ Yes   | Recommended — uses the `Task` tool to isolate persona review phases. |
| [Codex CLI](https://github.com/openai/codex)                                         | `--ai codex`     | —         |                                                                      |
| [Gemini CLI](https://github.com/google-gemini/gemini-cli)                            | `--ai gemini`    | —         | Commands rendered as TOML.                                           |
| [GitHub Copilot](https://github.com/features/copilot)                                | `--ai copilot`   | —         | Auto-emits prompt + agent file pair; configures VS Code settings.    |
| Generic — bring your own agent                                                       | `--ai generic`   | —         | Use with `--ai-commands-dir <path>`.                                 |

The "Subagents" column flags whether the agent has a built-in primitive (Claude Code's `Task` tool) that InfraKit's multi-persona commands can delegate to. With native subagents, the **Cloud Architect** and **Cloud Security Engineer** review phases run in isolated context windows — the architect's reasoning never sees the security review's reasoning, and vice versa. On agents without subagents, the same review prompts run inline; the context boundaries are explicit but not enforced.

If you encounter issues with one of the supported agents, please [open an issue](https://github.com/neelneelpurk/infrakit/issues/new). Other agents were dropped in v0.2 because the maintenance surface (per-agent layout, MCP install paths, command-format quirks, untested subagent semantics) was unmaintainable; if you want first-class support for another agent, please open an issue describing the use case.

## 🧰 Supported IaC Platforms

| Platform                                | Status      | Output | Resource Term |
| --------------------------------------- | ----------- | ------ | ------------- |
| [Crossplane](https://crossplane.io/)    | ✅ Supported | YAML   | Composition   |
| [Terraform](https://www.terraform.io/)  | ✅ Supported | HCL    | Module        |
| [OpenTofu](https://opentofu.org/)       | 🗺️ Roadmap  | —      | —             |
| [Pulumi](https://www.pulumi.com/)       | 🗺️ Roadmap  | —      | —             |
| AWS CloudFormation                      | 🗺️ Roadmap  | —      | —             |

## 🔤 Available Slash Commands

After running `infrakit init`, your AI coding agent has access to these slash commands, prefixed `/infrakit:`. With `--ai-skills`, the same commands install as agent skills.

### Core Commands

Essential commands for the spec-driven workflow:

| Command                          | Description                                                                              |
| -------------------------------- | ---------------------------------------------------------------------------------------- |
| `/infrakit:setup`                | Capture project context, coding standards, and tagging requirements                      |
| `/infrakit:setup-coding-style`   | Update or replace project coding-style standards                                         |
| `/infrakit:new_composition`      | (Crossplane) Solutions → Architect → Security → spec workflow for a new XR/Composition   |
| `/infrakit:create_terraform_code`| (Terraform) Solutions → Architect → Security → spec workflow for a new module            |
| `/infrakit:plan`                 | Generate the implementation plan and auto-generate `tasks.md`                            |
| `/infrakit:implement`            | Execute tasks from `tasks.md`, mark complete, write context / changelog / contract       |
| `/infrakit:review`               | Review generated code against coding standards and tagging                               |

### Brownfield Commands

For updating resources that already exist:

| Command                              | Description                                                                                |
| ------------------------------------ | ------------------------------------------------------------------------------------------ |
| `/infrakit:update_composition`       | (Crossplane) Brownfield scan → contract review → solutioning → updated spec                |
| `/infrakit:update_terraform_code`    | (Terraform) Brownfield scan → contract review → solutioning → updated spec                 |

### Quality & Review Commands

Optional commands for cross-artifact validation:

| Command                          | Description                                                                                  |
| -------------------------------- | -------------------------------------------------------------------------------------------- |
| `/infrakit:analyze`              | Cross-artifact consistency check — verifies spec, plan, and code are aligned                 |
| `/infrakit:architect-review`     | Cloud Architect review for architecture correctness, reliability, and cost                   |
| `/infrakit:security-review`      | Cloud Security Engineer compliance review (SOC 2, HIPAA, ISO 27001, CIS, NIST, PCI-DSS)      |
| `/infrakit:status`               | Dashboard showing all tracks and their current status                                        |

## 📦 InfraKit CLI Reference

| Command            | Description                                                                            |
| ------------------ | -------------------------------------------------------------------------------------- |
| `infrakit init`    | Initialize a new InfraKit project — renders the per-agent layout from bundled prompts  |
| `infrakit check`   | Check installed tools (`git`, `claude`, `gemini`, `kubectl`, `terraform`, etc.)        |
| `infrakit mcp`     | Install a pre-defined MCP server recipe into your agent's MCP config                   |
| `infrakit version` | Display CLI version and check for upgrades                                             |

### `infrakit init` options

| Option                  | Type       | Description                                                                  |
| ----------------------- | ---------- | ---------------------------------------------------------------------------- |
| `<project-name>`        | Positional | Name for your new project directory (omit with `--here`)                     |
| `--here`                | Flag       | Initialize in the current directory instead of a new subdirectory            |
| `--ai`                  | Choice     | AI assistant — see [Supported AI Coding Agents](#-supported-ai-coding-agents)|
| `--ai-commands-dir`     | Path       | Command files directory (required with `--ai generic`)                       |
| `--iac`                 | Choice     | IaC tool: `crossplane` or `terraform`                                        |
| `--script`              | Choice     | Script type: `sh` (default) or `ps` (PowerShell)                             |
| `--ignore-agent-tools`  | Flag       | Skip AI agent tool availability checks                                       |
| `--no-git`              | Flag       | Skip `git init`                                                              |
| `--force`               | Flag       | Skip confirmation when initializing in a non-empty directory                 |
| `--debug`               | Flag       | Verbose diagnostic output                                                    |
| `--ai-skills`           | Flag       | Install prompts as agent skills instead of slash commands                    |

#### Examples

```bash
# New project with Claude Code and Crossplane
infrakit init my-infra --ai claude --iac crossplane

# New project with Claude Code and Terraform
infrakit init my-infra --ai claude --iac terraform

# Initialize in the current directory
infrakit init --here --ai claude --iac crossplane

# Force-merge into an existing non-empty directory
infrakit init --here --force --ai claude --iac crossplane

# Skip git init (useful in CI)
infrakit init my-infra --ai gemini --iac crossplane --no-git

# Bring your own agent
infrakit init my-infra --ai generic --ai-commands-dir .myagent/commands/ --iac crossplane

# Check system prerequisites
infrakit check

# Install an MCP server
infrakit mcp
```

## 🧭 The Track System

Every resource change gets its own **track** — a versioned directory under `.infrakit_tracks/tracks/<track-name>/` that holds spec, plan, task list, and per-persona review artifacts. Multiple tracks run in parallel. Every step is committed alongside the code, giving you a permanent audit trail of why each resource exists and how its design was approved.

```text
.infrakit/                            # Project-wide standards (read by every command)
├── config.yaml                       # iac_tool, ai_assistant, resource_term
├── context.md                        # Cloud provider, naming, environment policies
├── coding-style.md                   # Mandatory coding standards
├── tagging-standard.md               # Required resource tags
├── memory/                           # Project memory for AI agents
└── agent_personas/                   # Persona definitions

.infrakit_tracks/
├── tracks.md                         # Registry of all tracks and their status
└── tracks/
    └── postgres-database-20260401-120000/
        ├── spec.md                   # Requirements, parameters, outputs, security
        ├── plan.md                   # Implementation plan
        ├── tasks.md                  # Auto-generated ordered task list
        ├── analyze.md                # /infrakit:analyze output
        ├── architect-review.md       # /infrakit:architect-review output
        ├── security-review.md        # /infrakit:security-review output
        └── review.md                 # /infrakit:review output
```

Per-resource artifacts written by `/infrakit:implement` (committed alongside the resource):

```text
<resource-directory>/
├── .infrakit_context.md              # Resource interface: variables, outputs, resources
├── .infrakit_changelog.md            # Append-only structured change history
└── infrakit_composition_contract.md  # (Crossplane) API surface contract
    OR .infrakit_terraform_contract.md  # (Terraform) Module interface contract
```

### Track status lifecycle

| Status                | Meaning                                  | Next step                                 |
| --------------------- | ---------------------------------------- | ----------------------------------------- |
| 🔵 `initializing`     | Track created, spec in progress          | Complete requirements with Solutions Engineer |
| 📝 `spec-generated`   | Spec confirmed by all personas           | `/infrakit:plan <track-name>`             |
| 📋 `planned`          | Plan and task list generated             | `/infrakit:implement <track-name>`        |
| ⚙️ `in-progress`      | Implementation underway                  | Continue `/infrakit:implement`            |
| ✅ `done`             | Implementation complete and reviewed     | Merge, close track                        |
| ❌ `blocked`          | Blocked — needs attention                | Resolve blocker, update track status      |

## 📚 Core Philosophy

InfraKit borrows its core philosophy from [spec-kit](https://github.com/github/spec-kit) — capture intent in a structured spec before writing code — and layers four IaC-specific ideas on top:

- **Standards first** — cloud provider standards, naming, tagging, compliance, and security defaults are captured *before* writing any code (via `/infrakit:setup`). Every downstream artifact must honour them.
- **Multi-persona refinement** — separate the requirements, architecture, security, and implementation roles into distinct personas with distinct vocabularies. The hypothesis is that one model wearing four hats produces sharper output than one model trying to balance all four at once. *(This is an empirical claim we are still validating; see the [acknowledgements](#-acknowledgements) note.)*
- **Provider-verified field names** — the IaC Engineer is prompted to read official provider docs before writing anything. Hallucinated `aws_db_instance` argument names that look right but cause apply failures are one of the most common reasons teams stop trusting AI for IaC.
- **Full audit trail in git** — spec, plan, task list, per-persona reviews, and the final code all land together. Every architectural decision and every compliance waiver is traceable from the resource back to a human approval.

## 🌟 Development Phases

| Phase                                    | Focus                              | Key Activities                                                                                                                                                                              |
| ---------------------------------------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Greenfield Development**               | Create new resources from scratch  | <ul><li>Capture project-wide constraints via `/infrakit:setup`</li><li>Spec via `/infrakit:new_composition` / `/infrakit:create_terraform_code`</li><li>Plan → implement → review</li></ul> |
| **Iterative Enhancement** ("Brownfield") | Update existing resources          | <ul><li>Scan existing code into context/contract files</li><li>`/infrakit:update_composition` / `/infrakit:update_terraform_code`</li><li>Re-run the four-persona pipeline</li></ul>        |
| **Continuous Compliance**                | Audit and enforce on every change  | <ul><li>`/infrakit:analyze`, `/infrakit:architect-review`, `/infrakit:security-review`</li><li>Findings tracked in the track directory</li><li>Re-audit triggered by spec or code drift</li></ul>|

## 📁 Examples

Two complete, end-to-end walkthroughs showing every file InfraKit produces:

| Example                                  | IaC Tool   | Scenario                                                                                  |
| ---------------------------------------- | ---------- | ----------------------------------------------------------------------------------------- |
| [`examples/terraform/`](./examples/terraform/) | Terraform  | AWS S3 secure-bucket module — KMS, public-access blocked, TLS-only, lifecycle, optional CRR |
| [`examples/crossplane/`](./examples/crossplane/) | Crossplane | `XPostgreSQLInstance` wrapping AWS RDS via `provider-aws-rds` with per-instance KMS         |

Each example contains the `.infrakit/` config, a single track under `.infrakit_tracks/tracks/`, and the final deliverable (the `.tf` module or Composition YAML).

## 🔧 Prerequisites

- **Linux / macOS / Windows**
- One of the [supported AI coding agents](#-supported-ai-coding-agents)
- [uv](https://docs.astral.sh/uv/) for package management (recommended) or [pipx](https://pypa.github.io/pipx/) for persistent installation
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)
- For Crossplane: [kubectl](https://kubernetes.io/docs/tasks/tools/) plus a Crossplane-enabled cluster (or [kind](https://kind.sigs.k8s.io/) for local dev)
- For Terraform: [Terraform](https://developer.hashicorp.com/terraform/install) or [OpenTofu](https://opentofu.org/docs/intro/install/)

## 📋 Detailed Process

<details>
<summary>Click to expand the full spec-driven workflow walkthrough</summary>

### Step 0 — Bootstrap the project

```bash
infrakit init my-infra --ai claude --iac crossplane
cd my-infra
```

You'll see your project populated with:

- `.claude/commands/` (or `.gemini/commands/`, `.github/agents/`, etc. depending on `--ai`)
- `.infrakit/` — `config.yaml`, `context.md` placeholder, `coding-style.md` placeholder, `tagging-standard.md` placeholder, generic and IaC-specific personas
- `.infrakit_tracks/tracks.md` — empty registry
- `.vscode/settings.json` (Copilot only)

Launch your AI agent. Use the `/infrakit:setup` command to fill in your project context.

### Step 1 — Establish project standards

```text
/infrakit:setup
```

The Solutions Engineer asks one question at a time:

1. Cloud provider(s) and regions
2. Naming convention pattern
3. Environment list (dev / staging / prod / etc.)
4. Tagging requirements (which tags are required on every resource and where their values come from)
5. Security baseline (encryption-at-rest defaults, public-access defaults, IAM rules)
6. Compliance frameworks in scope
7. Architecture decisions already locked in (IaC tool version, GitOps engine, state backend)

The output lands in `.infrakit/context.md` and `.infrakit/tagging-standard.md`. Then:

```text
/infrakit:setup-coding-style
```

…populates `.infrakit/coding-style.md` with your project's coding standards (file layout, naming, versioning policy, validation patterns, provider config, backend config, etc.).

> [!IMPORTANT]
> Be explicit about **what** standards apply and **why**. Every downstream command reads these files; vague answers here produce vague code.

### Step 2 — Specify the resource

For Crossplane:

```text
/infrakit:new_composition An AWS RDS PostgreSQL composition. Allow callers to set instanceClass, storageGB, multiAZ override. Default Multi-AZ to true in prod. Per-instance customer-managed KMS key. publicly_accessible=false always. Connection details published as a Kubernetes Secret in the claim's namespace.
```

For Terraform:

```text
/infrakit:create_terraform_code An AWS S3 secure bucket module. KMS encryption with a customer-managed key. All four block_public_* flags set. TLS-only via aws:SecureTransport deny policy. Optional cross-region replication gated to prod only.
```

The Solutions Engineer iterates until requirements are clear (it will ask clarifying questions before writing anything). Then the Architect presents 2–3 named design options with cost / reliability / complexity trade-offs. Finally the Security Engineer asks which compliance frameworks apply and audits the spec against them.

Output: `.infrakit_tracks/tracks/<track-name>/spec.md`, with the track registered at status `📝 spec-generated`.

### Step 3 — Plan

```text
/infrakit:plan <track-name>
```

The IaC Engineer:

1. Verifies the API versions and field names of every provider resource (against `doc.crds.dev` for Crossplane or `registry.terraform.io` for Terraform)
2. Designs the parameter → resource argument mapping table
3. Designs the output → attribute mapping table
4. Writes `plan.md`
5. Auto-generates `tasks.md` — an ordered, checkbox task list for each implementation phase

Track status → `📋 planned`.

### Step 4 — Implement

```text
/infrakit:implement <track-name>
```

The IaC Engineer:

- Validates that constitution, spec, plan, and tasks are all in place
- Walks `tasks.md` top-to-bottom, marking each `- [ ]` → `- [x]` as it goes
- Writes the actual `.tf` or YAML files into the target directory
- After all tasks complete, writes three post-implementation artifacts:
  - `.infrakit_context.md` — resource interface (variables, outputs, resources provisioned)
  - `.infrakit_changelog.md` — append-only structured change history
  - Resource contract file (`infrakit_composition_contract.md` or `.infrakit_terraform_contract.md`)

Track status → `✅ done`.

### Step 5 — Cross-artifact analysis

Run before merging:

```text
/infrakit:analyze <track-name>
```

The Cloud Solutions Engineer cross-checks spec ↔ plan ↔ generated code for drift. Findings categorized by severity. No automatic edits — the agent presents findings and asks you which to apply.

```text
/infrakit:architect-review <track-name>
```

Architecture quality gate: reliability, cost, completeness, environment-aware checks.

```text
/infrakit:security-review <track-name>
```

Compliance audit against the frameworks chosen in step 2. Findings against each control are tabulated; CRITICAL/HIGH gaps require either fixes or documented waivers.

### Step 6 — Code review

```text
/infrakit:review <resource-directory>
```

Reviews the generated HCL or YAML against `coding-style.md` and `tagging-standard.md`. Verdict: APPROVED / APPROVED WITH NOTES / NEEDS FIXES. Agent offers to apply fixes inline.

### Iterating

For brownfield work (updating an existing resource), use `/infrakit:update_composition` or `/infrakit:update_terraform_code` instead of the `new_*` / `create_*` commands. These first scan the existing code into `.infrakit_context.md` + `.infrakit_terraform_contract.md` (or composition contract), present them for your review, then run the spec → plan → implement workflow against the updated requirements.

</details>

## 🔍 Troubleshooting

### Corporate proxy / self-signed certificates

Templates ship inside the InfraKit wheel, so `infrakit init` does **not** call any network. The only network call is the optional version check in `infrakit version`, which uses the system trust store via `truststore`. If you cannot reach `api.github.com` for the version check, the rest of the CLI still works — just skip `infrakit version`.

### `tasks.md` not found when running `/infrakit:implement`

`tasks.md` is auto-generated by `/infrakit:plan` after you accept the plan. If it is missing, re-run `/infrakit:plan <track-name>`.

### Track directory not found

Tracks live under `.infrakit_tracks/tracks/<track-name>/`. If you initialized with an older version of InfraKit (< 0.2.0), your tracks may be under `.infrakit/tracks/`. Move them:

```bash
mkdir -p .infrakit_tracks/tracks
mv .infrakit/tracks/* .infrakit_tracks/tracks/
mv .infrakit/tracks.md .infrakit_tracks/tracks.md
```

## 📖 Learn More

| Resource                                                       | Description                                                                              |
| -------------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| [Quick Start Guide](./docs/quickstart.md)                      | End-to-end Crossplane workflow walkthrough                                               |
| [Installation Guide](./docs/installation.md)                   | Detailed installation, upgrades, and corporate-proxy setup                               |
| [Upgrade Guide](./docs/upgrade.md)                              | How to upgrade the CLI and update project template files                                 |
| [Methodology notes](./constraint-driven.md)                    | Deeper notes on the multi-persona pipeline and how it extends spec-driven development    |
| [Examples](./examples/)                                        | Full Terraform and Crossplane walkthroughs                                               |
| [CHANGELOG](./CHANGELOG.md)                                    | Full version history and breaking changes                                                |
| [CONTRIBUTING](./CONTRIBUTING.md)                              | How to contribute to InfraKit                                                            |

## 💬 Support

For bug reports, feature requests, or questions, please open a [GitHub issue](https://github.com/neelneelpurk/infrakit/issues/new).

## 🙏 Acknowledgements

InfraKit's workflow shape is heavily influenced by [GitHub Spec Kit](https://github.com/github/spec-kit) and the wider Spec-Driven Development community. The multi-persona pipeline is original to InfraKit and grew out of running real Crossplane and Terraform migrations where a single "AI generates code" prompt was never enough.

## 📄 License

This project is licensed under the terms of the MIT open source license. See the [LICENSE](./LICENSE) file for the full terms.
