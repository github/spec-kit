<div align="center">
    <img src="./media/logo_small.webp"/>
    <h1>🌱 Spec Kit</h1>
    <h3><em>Build high-quality software faster.</em></h3>
</div>

<p align="center">
    <strong>An effort to allow organizations to focus on product scenarios rather than writing undifferentiated code with the help of Spec-Driven Development.</strong>
</p>

[![Release](https://github.com/hcnimi/spec-kit/actions/workflows/release.yml/badge.svg)](https://github.com/hcnimi/spec-kit/actions/workflows/release.yml)

---

## Table of Contents

- [🤔 What is Spec-Driven Development?](#-what-is-spec-driven-development)
- [⚡ Get started](#-get-started)
- [🔧 Specify CLI Reference](#-specify-cli-reference)
- [📚 Core philosophy](#-core-philosophy)
- [🌟 Development phases](#-development-phases)
- [🎯 Experimental goals](#-experimental-goals)
- [🔧 Prerequisites](#-prerequisites)
- [📖 Documentation](#-documentation)
- [🔍 Troubleshooting](#-troubleshooting)
- [👥 Maintainers](#-maintainers)
- [💬 Support](#-support)
- [🙏 Acknowledgements](#-acknowledgements)
- [📄 License](#-license)

## 🤔 What is Spec-Driven Development?

Spec-Driven Development **flips the script** on traditional software development. For decades, code has been king — specifications were just scaffolding we built and discarded once the "real work" of coding began. Spec-Driven Development changes this: **specifications become executable**, directly generating working implementations rather than just guiding them.

## ⚡ Get started

### 1. Install Specify

Initialize your project depending on the coding agent you're using:

```bash
uvx --from git+https://github.com/hcnimi/spec-kit.git specify init <PROJECT_NAME>
```

#### What does this command mean?

- `uvx --from git+https://github.com/hcnimi/spec-kit.git` - Where to get the package (temporary execution, doesn't install permanently)
- `specify` - The CLI tool to execute
- `init <PROJECT_NAME>` - Command and arguments passed to the CLI

### Global Installation

If you prefer to install the `specify` CLI globally for repeated use:

**Using uv (recommended):**
```bash
uv tool install git+https://github.com/hcnimi/spec-kit.git
```

**Using pip:**
```bash
pip install git+https://github.com/hcnimi/spec-kit.git
```

After global installation, use `specify` directly:
```bash
specify init <PROJECT_NAME> --ai claude
```

To uninstall:
```bash
uv tool uninstall specify-cli
# or
pip uninstall specify-cli
```

### Alternative: Direct Script Usage

If you have this repository cloned locally, you can use the `init.sh` script directly:

```bash
# Single repository mode:

# Basic usage - creates project in new directory
./init.sh my-project

# Initialize in current directory
./init.sh . --ai claude --script sh

# Destroy existing files and start fresh
./init.sh my-project --destroy --ai claude

# Use different AI assistants
./init.sh my-project --ai gemini
./init.sh my-project --ai copilot
./init.sh my-project --ai cursor

# Use PowerShell scripts instead of bash
./init.sh my-project --ai claude --script ps

# Multi-repository mode:

# Preview updates for all repos in current directory
./init.sh --all-repos --ai claude

# Search specific path with custom depth
./init.sh --all-repos --search-path ~/git/myorg --max-depth 2

# Execute without preview (still asks for confirmation)
./init.sh --all-repos --execute --ai claude

# Bulk refresh with --destroy (extra safety prompt)
./init.sh --all-repos --destroy --ai claude --search-path ~/git

# Combine with different script types
./init.sh --all-repos --ai gemini --script ps
```

#### `init.sh` Options

| Option | Description | Values |
|--------|-------------|---------|
| `--ai` | AI assistant to use | `claude`, `gemini`, `copilot`, `cursor` (default: `claude`) |
| `--script` | Script type to install | `sh` (bash), `ps` (PowerShell) (default: `sh`) |
| `--destroy` | Delete existing `.specify/` directory and start fresh | Flag |
| `--all-repos` | Process all repos containing `.specify` folders (multi-repo mode) | Flag |
| `--search-path` | Directory to search for repos with `.specify` (multi-repo mode only) | Path (default: current directory) |
| `--max-depth` | Search depth for `.specify` folders (multi-repo mode only) | Number (default: `3`) |
| `--execute` | Skip preview and execute immediately (multi-repo mode only) | Flag |
| `--help` | Show help message | Flag |

#### What `--destroy` Does

The `--destroy` flag removes the entire `.specify/` directory to start with a clean slate. When you use this flag:

1. **Confirmation prompt**: You'll be asked to confirm deletion of the `.specify/` directory
2. **Constitution preservation**: If `constitution.md` exists, you'll be prompted whether to preserve it
3. **Complete removal**: The entire `.specify/` directory is deleted and recreated fresh
4. **Preservation handling**: If you chose to preserve `constitution.md`, it's restored after the fresh copy

**What gets destroyed:**
- `.specify/memory/` (except `constitution.md` if preserved)
- `.specify/scripts/`
- `.specify/templates/`
- `.specify/docs/`
- AI-specific command directories (`.claude/commands/`, `.gemini/commands/`, etc.)

**What's preserved:**
- `specs/` directory (never touched)
- Your project files outside `.specify/`
- `constitution.md` (if you choose to preserve it)
- `.gitignore` entries (updated, not destroyed)

**Multi-repo mode with --destroy:**
When using `--all-repos` with `--destroy`, you'll receive an extra safety confirmation prompt requiring you to type `"yes, I'm sure"` before proceeding. This prevents accidental bulk deletion across multiple repositories. The constitution preservation prompt will be asked for each repository individually.

The script will:
- Create a `.specify/` directory with all necessary templates and scripts
- Generate AI-specific command files (`.claude/commands/`, `.gemini/commands/`, etc.)
- Preserve your existing `constitution.md` if you choose to
- Set up proper `.gitignore` entries
- Copy scripts based on your chosen platform (bash or PowerShell)

#### Multi-Repository Mode

The `--all-repos` flag enables bulk initialization across multiple repositories containing `.specify` folders. This is useful for:
- Updating spec-kit templates across your organization's microservices
- Rolling out spec-kit updates to multiple projects simultaneously
- Standardizing configurations across team repositories

**How it works:**

1. **Discovery**: Searches for all directories containing `.specify` folders within the specified search path and depth
2. **Preview**: Always shows a preview of all repositories that will be updated (unless `--execute` is used)
3. **Confirmation**: Asks for user confirmation before making any changes
4. **Execution**: Processes each repository sequentially with detailed progress reporting

**Safety features:**

- **Preview-first workflow**: Always previews changes before execution (can skip with `--execute`)
- **Extra confirmation for --destroy**: Requires typing `"yes, I'm sure"` when combining `--all-repos` with `--destroy`
- **Individual prompts**: Constitution preservation is asked per repository
- **Failure isolation**: If one repository fails, others continue processing
- **Summary report**: Shows success/failure counts and lists any failed repositories

**Usage examples:**

```bash
# Preview updates for all repos in current directory (depth 3)
./init.sh --all-repos --ai claude

# Search in specific directory with custom depth
./init.sh --all-repos --search-path ~/git/myorg --max-depth 2 --ai claude

# Preview updates for all repos and specify script type
./init.sh --all-repos --ai gemini --script ps

# Skip preview and execute immediately
./init.sh --all-repos --execute --ai claude

# Bulk refresh with --destroy (requires extra confirmation)
./init.sh --all-repos --destroy --ai claude
```

**Configuration options:**

- `--search-path`: Directory to search (default: current directory)
- `--max-depth`: How deep to search for `.specify` folders (default: 3)
- `--execute`: Skip preview and proceed directly to confirmation

**Example output:**

```
Found 5 repositories with .specify:
  1. /Users/you/git/project-a
  2. /Users/you/git/project-b
  3. /Users/you/git/project-c
  4. /Users/you/git/project-d
  5. /Users/you/git/project-e

Settings:
  AI: claude
  Script: sh
  Destroy: no

=== PREVIEW MODE ===

[1/5] Would update: project-a
Would create .specify directory structure
Would copy memory folder
[...]

Do you want to proceed with these changes? (y/N):
```

#### Install from a Fork or Custom Branch

To install from your own fork or a specific branch:

```bash
# Automatic detection (recommended) - CLI auto-detects fork/branch from uvx command
uvx --from git+https://github.com/YOUR_USERNAME/spec-kit.git@BRANCH_NAME specify init <PROJECT_NAME> --ai claude

# Manual specification (if you need to override auto-detection)
uvx --from git+https://github.com/YOUR_USERNAME/spec-kit.git@BRANCH_NAME specify init <PROJECT_NAME> \
  --ai claude --repo-owner YOUR_USERNAME --repo-branch BRANCH_NAME

# Or set environment variables
export SPECIFY_REPO_OWNER=YOUR_USERNAME
export SPECIFY_REPO_BRANCH=BRANCH_NAME
uvx --from git+https://github.com/YOUR_USERNAME/spec-kit.git@BRANCH_NAME specify init <PROJECT_NAME> --ai claude
```

**Auto-Detection Feature**: When using `uvx --from` with a GitHub URL, the CLI automatically detects the repository owner and branch, eliminating the need to manually specify `--repo-owner` and `--repo-branch` flags. This ensures you download templates from the same fork/branch you're running the CLI from.

### 2. (Optional) Define Product Vision

For complex products or 0-to-1 development, start with strategic planning:

```bash
/product-vision Build a team collaboration platform for distributed teams
```

This creates `docs/product-vision.md` with personas, success metrics, and product-wide requirements. **Skip this** for simple features or single-feature tools.

### 3. Create Feature Specification

Use the **`/specify`** command to describe what you want to build. Focus on requirements and constraints.

```bash
/specify Build an application that can help me organize my photos in separate photo albums. Albums are grouped by date and can be re-organized by dragging and dropping on the main page. Albums are never in other nested albums. Within each album, photos are previewed in a tile-like interface.
```

If product vision exists, `/specify` inherits personas and product-wide requirements. Otherwise, it works standalone.

### 4. Create Technical Implementation Plan

Use the **`/plan`** command to provide your tech stack and architecture choices.

```bash
/plan The application uses Vite with minimal number of libraries. Use vanilla HTML, CSS, and JavaScript as much as possible. Images are not uploaded anywhere and metadata is stored in a local SQLite database.
```

### 4. Decompose into capabilities (optional, for large features)

For features >1000 LOC total, use **`/decompose`** to break into atomic capabilities (400-1000 LOC total each).

```bash
/decompose
# Generates capability breakdown and creates cap-001/, cap-002/, etc.
```

### 5. Break down and implement

Use **`/tasks`** to create an actionable task list, then ask your agent to implement the feature.

For detailed step-by-step instructions, see our [Getting Started Tutorial](./docs/getting-started/first-spec.md).

## 🔧 Workflow: Simple vs Complex Features

### Simple Features (<1000 LOC total)
```bash
/specify → /plan → /tasks → /implement
```

### Complex Features (>1000 LOC total) - Atomic PRs
```bash
# On parent branch: username/jira-123.user-system
/specify → /decompose → creates cap-001/, cap-002/, cap-003/ on parent branch

# For each capability (creates NEW branch per capability):
/plan --capability cap-001 → creates branch username/jira-123.user-system-cap-001
/tasks → /implement → PR: cap-001 branch → main (400-1000 LOC total) ✓ MERGED

# Back to parent, sync with main, repeat:
git checkout username/jira-123.user-system
git pull origin main
/plan --capability cap-002 → creates branch username/jira-123.user-system-cap-002
/tasks → /implement → PR: cap-002 branch → main (400-1000 LOC total) ✓ MERGED

# Continue for cap-003, cap-004, etc.
```

**Result:** Multiple atomic PRs (400-1000 LOC total each) instead of one massive PR.

**Key Benefits:**
- Each capability gets its own branch and atomic PR to main
- Fast reviews (1-2 days per PR vs 7+ days for large PRs)
- Parallel development (team members work on different capabilities)
- Early integration feedback (merge to main frequently)

## 🔧 Specify CLI Reference

The `specify` command supports the following options:

### Commands

| Command     | Description                                                    |
|-------------|----------------------------------------------------------------|
| `init`      | Initialize a new Specify project from the latest template      |
| `check`     | Check for installed tools (`git`, `claude`, `gemini`, `code`/`code-insiders`, `cursor-agent`) |

### Key Slash Commands

| Command     | Purpose | When to Use |
|-------------|---------|-------------|
| `/specify`  | Create feature specification | Always - first step for any feature |
| `/decompose` | Break feature into capabilities | For complex features (>1000 LOC total, >5 requirements) |
| `/plan`     | Create implementation plan | After `/specify` (simple) or `/decompose` (complex) |
| `/tasks`    | Generate task list | After `/plan` is complete |
| `/implement`| Execute implementation | After `/tasks` is complete |

### `specify init` Arguments & Options

| Argument/Option        | Type     | Description                                                                  |
|------------------------|----------|------------------------------------------------------------------------------|
| `<project-name>`       | Argument | Name for your new project directory (optional if using `--here`)            |
| `--ai`                 | Option   | AI assistant to use: `claude`, `gemini`, `copilot`, or `cursor`             |
| `--script`             | Option   | Script variant to use: `sh` (bash/zsh) or `ps` (PowerShell)                 |
| `--ignore-agent-tools` | Flag     | Skip checks for AI agent tools like Claude Code                             |
| `--no-git`             | Flag     | Skip git repository initialization                                          |
| `--here`               | Flag     | Initialize project in the current directory instead of creating a new one   |
| `--skip-tls`           | Flag     | Skip SSL/TLS verification (not recommended)                                 |
| `--debug`              | Flag     | Enable detailed debug output for troubleshooting                            |
| `--repo-owner`         | Option   | GitHub repository owner (default: `github`, auto-detected from `uvx --from`) |
| `--repo-name`          | Option   | GitHub repository name (default: `spec-kit`, auto-detected from `uvx --from`) |
| `--repo-branch`        | Option   | GitHub repository branch to download from (uses releases by default, auto-detected from `uvx --from`) |

### Examples

```bash
# Basic project initialization
specify init my-project

# Initialize with specific AI assistant
specify init my-project --ai claude

# Initialize with Cursor support
specify init my-project --ai cursor

# Initialize with PowerShell scripts (Windows/cross-platform)
specify init my-project --ai copilot --script ps

# Initialize in current directory
specify init --here --ai copilot

# Skip git initialization
specify init my-project --ai gemini --no-git

# Enable debug output for troubleshooting
specify init my-project --ai claude --debug

# Check system requirements
specify check
```

## 📚 Core philosophy

Spec-Driven Development is a structured process that emphasizes:

- **Intent-driven development** where specifications define the "_what_" before the "_how_"
- **Rich specification creation** using guardrails and organizational principles
- **Multi-step refinement** rather than one-shot code generation from prompts
- **Heavy reliance** on advanced AI model capabilities for specification interpretation

## 🌟 Development phases

| Phase | Focus | Key Activities |
|-------|-------|----------------|
| **0-to-1 Development** ("Greenfield") | Generate from scratch | <ul><li>(Optional) Define product vision with `/product-vision`</li><li>Create feature specifications with `/specify`</li><li>Plan implementation with `/plan` (establishes system architecture v1.0.0)</li><li>Build MVP and production-ready applications</li></ul> |
| **Creative Exploration** | Parallel implementations | <ul><li>Explore diverse solutions</li><li>Support multiple technology stacks & architectures</li><li>Experiment with UX patterns</li></ul> |
| **Iterative Enhancement** ("Brownfield") | Brownfield modernization | <ul><li>Add features iteratively (inherits from product vision & system architecture)</li><li>Extend or refactor architecture as needed</li><li>Modernize legacy systems</li><li>Track architecture evolution with semantic versioning</li></ul> |

### Example Workflows

**Greenfield with Product Vision** (Complex product, 0-to-1):
```
/product-vision → docs/product-vision.md (personas, success metrics, product NFRs)
/specify        → specs/proj-1.mvp/spec.md (inherits from product vision)
/plan           → specs/proj-1.mvp/plan.md (establishes docs/system-architecture.md v1.0.0)
/tasks          → specs/proj-1.mvp/tasks.md
implement       → MVP launched
```

**Greenfield without Product Vision** (Simple tool, single feature):
```
/specify        → specs/proj-1.tool/spec.md (standalone specification)
/plan           → specs/proj-1.tool/plan.md (establishes docs/system-architecture.md v1.0.0)
/tasks          → specs/proj-1.tool/tasks.md
implement       → Tool launched
```

**Brownfield Feature Addition** (Extending existing product):
```
/specify        → specs/proj-2.feature/spec.md (inherits from docs/product-vision.md + docs/system-architecture.md)
/plan           → specs/proj-2.feature/plan.md (extends architecture v1.0.0 → v1.1.0)
/tasks          → specs/proj-2.feature/tasks.md
implement       → Feature added, architecture extended
```

For detailed workflows including architecture refactoring, see our [Core Concepts](./docs/concepts/) documentation.

## 🎯 Experimental goals

Our research and experimentation focus on:

### Technology independence

- Create applications using diverse technology stacks
- Validate the hypothesis that Spec-Driven Development is a process not tied to specific technologies, programming languages, or frameworks

### Enterprise constraints

- Demonstrate mission-critical application development
- Incorporate organizational constraints (cloud providers, tech stacks, engineering practices)
- Support enterprise design systems and compliance requirements

### User-centric development

- Build applications for different user cohorts and preferences
- Support various development approaches (from vibe-coding to AI-native development)

### Creative & iterative processes

- Validate the concept of parallel implementation exploration
- Provide robust iterative feature development workflows
- Extend processes to handle upgrades and modernization tasks

## 🔧 Prerequisites

- **Linux/macOS** (or WSL2 on Windows)
- AI coding agent: [Claude Code](https://www.anthropic.com/claude-code), [GitHub Copilot](https://code.visualstudio.com/), [Gemini CLI](https://github.com/google-gemini/gemini-cli), or [Cursor](https://cursor.sh/)
- [uv](https://docs.astral.sh/uv/) for package management
- [Python 3.11+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

## 📖 Documentation

Comprehensive documentation is organized into focused sections:

- **[📚 Getting Started](./docs/getting-started/)** - Installation, quick start, first project tutorial
- **[📖 How-To Guides](./docs/guides/)** - Task-focused guides for different scenarios
- **[💡 Core Concepts](./docs/concepts/)** - Deep dives into philosophy and principles
- **[📋 Reference](./docs/reference/)** - Technical specifications and API docs
- **[✅ Validation](./docs/validation/)** - Quality gates and review processes
- **[🔧 Contributing](./contributing/)** - Developer and contributor guides

### Quick Links

- [Installation Guide](./docs/getting-started/installation.md)
- [Your First Spec Tutorial](./docs/getting-started/first-spec.md)
- [Multi-Repo Workspaces](./docs/guides/multi-repo-workspaces.md)
- [Atomic PRs for Large Features](./docs/guides/atomic-prs.md)
- [Spec-Driven Philosophy](./docs/concepts/spec-driven-philosophy.md)

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

## 👥 Maintainers

- Den Delimarsky ([@localden](https://github.com/localden))
- John Lam ([@jflam](https://github.com/jflam))

## 💬 Support

For support, please open a [GitHub issue](https://github.com/hcnimi/spec-kit/issues/new). We welcome bug reports, feature requests, and questions about using Spec-Driven Development.

## 🙏 Acknowledgements

This project is heavily influenced by and based on the work and research of [John Lam](https://github.com/jflam).

## 📄 License

This project is licensed under the terms of the MIT open source license. Please refer to the [LICENSE](./LICENSE) file for the full terms.
