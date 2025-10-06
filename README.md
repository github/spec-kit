<div align="center">
    <img src="./media/logo_small.webp"/>
    <h1>🌱 Spec Kit</h1>
    <h3><em>Build high-quality software faster.</em></h3>
</div>

<p align="center">
    <strong>An effort to allow organizations to focus on product scenarios rather than writing undifferentiated code with the help of Spec-Driven Development.</strong>
</p>

[![Release](https://github.com/github/spec-kit/actions/workflows/release.yml/badge.svg)](https://github.com/github/spec-kit/actions/workflows/release.yml)

---

## Table of Contents

- [🤔 What is Spec-Driven Development?](#-what-is-spec-driven-development)
- [⚡ Get started](#-get-started)
- [🔧 Specify CLI Reference](#-specify-cli-reference)
- [📚 Core philosophy](#-core-philosophy)
- [🌟 Development phases](#-development-phases)
- [🎯 Experimental goals](#-experimental-goals)
- [🔧 Prerequisites](#-prerequisites)
- [📖 Learn more](#-learn-more)
- [📋 Detailed process](#-detailed-process)
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
uvx --from git+https://github.com/github/spec-kit.git specify init <PROJECT_NAME>
```

### Alternative: Direct Script Usage

If you have this repository cloned locally, you can use the `init.sh` script directly:

```bash
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
```

#### `init.sh` Options

| Option | Description | Values |
|--------|-------------|---------|
| `--ai` | AI assistant to use | `claude`, `gemini`, `copilot`, `cursor` (default: `claude`) |
| `--script` | Script type to install | `sh` (bash), `ps` (PowerShell) (default: `sh`) |
| `--destroy` | Delete existing `.specify/` directory and start fresh | Flag |
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

The script will:
- Create a `.specify/` directory with all necessary templates and scripts
- Generate AI-specific command files (`.claude/commands/`, `.gemini/commands/`, etc.)
- Preserve your existing `constitution.md` if you choose to
- Set up proper `.gitignore` entries
- Copy scripts based on your chosen platform (bash or PowerShell)

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

# Example: Install from hnimitanakit's prps-spec branch (auto-detection)
uvx --from git+https://github.com/hnimitanakit/spec-kit.git@prps-spec specify init <PROJECT_NAME> --ai claude
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

For features >500 LOC, use **`/decompose`** to break into atomic capabilities (200-500 LOC each).

```bash
/decompose
# Generates capability breakdown and creates cap-001/, cap-002/, etc.
```

### 5. Break down and implement

Use **`/tasks`** to create an actionable task list, then ask your agent to implement the feature.

For detailed step-by-step instructions, see our [comprehensive guide](./spec-driven.md).

## 🔧 Workflow: Simple vs Complex Features

### Simple Features (<500 LOC)
```bash
/specify → /plan → /tasks → /implement
```

### Complex Features (>500 LOC) - Atomic PRs
```bash
# On parent branch: username/jira-123.user-system
/specify → /decompose → creates cap-001/, cap-002/, cap-003/ on parent branch

# For each capability (creates NEW branch per capability):
/plan --capability cap-001 → creates branch username/jira-123.user-system-cap-001
/tasks → /implement → PR: cap-001 branch → main (200-500 LOC) ✓ MERGED

# Back to parent, sync with main, repeat:
git checkout username/jira-123.user-system
git pull origin main
/plan --capability cap-002 → creates branch username/jira-123.user-system-cap-002
/tasks → /implement → PR: cap-002 branch → main (200-500 LOC) ✓ MERGED

# Continue for cap-003, cap-004, etc.
```

**Result:** Multiple atomic PRs (200-500 LOC each) instead of one massive PR.

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
| `/decompose` | Break feature into capabilities | For complex features (>500 LOC, >5 requirements) |
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

# Install from a specific fork and branch (manual override)
specify init my-project --ai claude --repo-owner hnimitanakit --repo-branch prps-spec

# Install from fork with auto-detection (using uvx)
uvx --from git+https://github.com/hnimitanakit/spec-kit.git@prps-spec specify init my-project --ai claude

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

For detailed workflows including architecture refactoring, see our [comprehensive guide](./spec-driven.md).

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

## 📖 Learn more

- **[Complete Spec-Driven Development Methodology](./spec-driven.md)** - Deep dive into the full process
- **[Detailed Walkthrough](#-detailed-process)** - Step-by-step implementation guide

---

## 📋 Detailed process

<details>
<summary>Click to expand the detailed step-by-step walkthrough</summary>

You can use the Specify CLI to bootstrap your project, which will bring in the required artifacts in your environment. Run:

```bash
specify init <project_name>
```

Or initialize in the current directory:

```bash
specify init --here
```

![Specify CLI bootstrapping a new project in the terminal](./media/specify_cli.gif)

You will be prompted to select the AI agent you are using. You can also proactively specify it directly in the terminal:

```bash
specify init <project_name> --ai claude
specify init <project_name> --ai gemini
specify init <project_name> --ai copilot
# Or in current directory:
specify init --here --ai claude
```

The CLI will check if you have Claude Code or Gemini CLI installed. If you do not, or you prefer to get the templates without checking for the right tools, use `--ignore-agent-tools` with your command:

```bash
specify init <project_name> --ai claude --ignore-agent-tools
```

### **STEP 1:** Bootstrap the project

Go to the project folder and run your AI agent. In our example, we're using `claude`.

![Bootstrapping Claude Code environment](./media/bootstrap-claude-code.gif)

You will know that things are configured correctly if you see the `/product-vision`, `/specify`, `/plan`, and `/tasks` commands available.

**(Optional) STEP 0:** For complex products or 0-to-1 development, define product vision first using `/product-vision`. This creates strategic context (personas, success metrics, product-wide requirements) that subsequent features will inherit. Skip this for simple tools or single-feature projects.

The first required step is creating a feature specification. Use `/specify` command and then provide the concrete requirements for the feature you want to develop.

>[!IMPORTANT]
>Be as explicit as possible about _what_ you are trying to build and _why_. **Do not focus on the tech stack at this point**.

An example prompt:

```text
Develop Taskify, a team productivity platform. It should allow users to create projects, add team members,
assign tasks, comment and move tasks between boards in Kanban style. In this initial phase for this feature,
let's call it "Create Taskify," let's have multiple users but the users will be declared ahead of time, predefined.
I want five users in two different categories, one product manager and four engineers. Let's create three
different sample projects. Let's have the standard Kanban columns for the status of each task, such as "To Do,"
"In Progress," "In Review," and "Done." There will be no login for this application as this is just the very
first testing thing to ensure that our basic features are set up. For each task in the UI for a task card,
you should be able to change the current status of the task between the different columns in the Kanban work board.
You should be able to leave an unlimited number of comments for a particular card. You should be able to, from that task
card, assign one of the valid users. When you first launch Taskify, it's going to give you a list of the five users to pick
from. There will be no password required. When you click on a user, you go into the main view, which displays the list of
projects. When you click on a project, you open the Kanban board for that project. You're going to see the columns.
You'll be able to drag and drop cards back and forth between different columns. You will see any cards that are
assigned to you, the currently logged in user, in a different color from all the other ones, so you can quickly
see yours. You can edit any comments that you make, but you can't edit comments that other people made. You can
delete any comments that you made, but you can't delete comments anybody else made.
```

After this prompt is entered, you should see Claude Code kick off the planning and spec drafting process. Claude Code will also trigger some of the built-in scripts to set up the repository.

Once this step is completed, you should have a new branch created (e.g., `username/proj-123.create-taskify`), as well as a new specification in the `specs/proj-123.create-taskify` directory.

The produced specification should contain a set of user stories and functional requirements, as defined in the template.

At this stage, your project folder contents should resemble the following:

```text
├── memory
│	 ├── constitution.md
│	 └── constitution_update_checklist.md
├── scripts
│	 ├── check-task-prerequisites.sh
│	 ├── common.sh
│	 ├── create-new-feature.sh
│	 ├── get-feature-paths.sh
│	 ├── setup-plan.sh
│	 └── update-claude-md.sh
├── specs
│	 └── proj-123.create-taskify
│	     └── spec.md
└── templates
    ├── plan-template.md
    ├── spec-template.md
    └── tasks-template.md
```

### **STEP 2:** Functional specification clarification

With the baseline specification created, you can go ahead and clarify any of the requirements that were not captured properly within the first shot attempt. For example, you could use a prompt like this within the same Claude Code session:

```text
For each sample project or project that you create there should be a variable number of tasks between 5 and 15
tasks for each one randomly distributed into different states of completion. Make sure that there's at least
one task in each stage of completion.
```

You should also ask Claude Code to validate the **Review & Acceptance Checklist**, checking off the things that are validated/pass the requirements, and leave the ones that are not unchecked. The following prompt can be used:

```text
Read the review and acceptance checklist, and check off each item in the checklist if the feature spec meets the criteria. Leave it empty if it does not.
```

It's important to use the interaction with Claude Code as an opportunity to clarify and ask questions around the specification - **do not treat its first attempt as final**.

### **STEP 3:** Generate a plan

You can now be specific about the tech stack and other technical requirements. You can use the `/plan` command that is built into the project template with a prompt like this:

```text
We are going to generate this using .NET Aspire, using Postgres as the database. The frontend should use
Blazor server with drag-and-drop task boards, real-time updates. There should be a REST API created with a projects API,
tasks API, and a notifications API.
```

The output of this step will include a number of implementation detail documents, with your directory tree resembling this:

```text
.
├── CLAUDE.md
├── memory
│	 ├── constitution.md
│	 └── constitution_update_checklist.md
├── scripts
│	 ├── check-task-prerequisites.sh
│	 ├── common.sh
│	 ├── create-new-feature.sh
│	 ├── get-feature-paths.sh
│	 ├── setup-plan.sh
│	 └── update-claude-md.sh
├── specs
│	 └── proj-123.create-taskify
│	     ├── contracts
│	     │	 ├── api-spec.json
│	     │	 └── signalr-spec.md
│	     ├── data-model.md
│	     ├── plan.md
│	     ├── quickstart.md
│	     ├── research.md
│	     └── spec.md
└── templates
    ├── CLAUDE-template.md
    ├── plan-template.md
    ├── spec-template.md
    └── tasks-template.md
```

Check the `research.md` document to ensure that the right tech stack is used, based on your instructions. You can ask Claude Code to refine it if any of the components stand out, or even have it check the locally-installed version of the platform/framework you want to use (e.g., .NET).

Additionally, you might want to ask Claude Code to research details about the chosen tech stack if it's something that is rapidly changing (e.g., .NET Aspire, JS frameworks), with a prompt like this:

```text
I want you to go through the implementation plan and implementation details, looking for areas that could
benefit from additional research as .NET Aspire is a rapidly changing library. For those areas that you identify that
require further research, I want you to update the research document with additional details about the specific
versions that we are going to be using in this Taskify application and spawn parallel research tasks to clarify
any details using research from the web.
```

During this process, you might find that Claude Code gets stuck researching the wrong thing - you can help nudge it in the right direction with a prompt like this:

```text
I think we need to break this down into a series of steps. First, identify a list of tasks
that you would need to do during implementation that you're not sure of or would benefit
from further research. Write down a list of those tasks. And then for each one of these tasks,
I want you to spin up a separate research task so that the net results is we are researching
all of those very specific tasks in parallel. What I saw you doing was it looks like you were
researching .NET Aspire in general and I don't think that's gonna do much for us in this case.
That's way too untargeted research. The research needs to help you solve a specific targeted question.
```

>[!NOTE]
>Claude Code might be over-eager and add components that you did not ask for. Ask it to clarify the rationale and the source of the change.

### **STEP 4:** Have Claude Code validate the plan

With the plan in place, you should have Claude Code run through it to make sure that there are no missing pieces. You can use a prompt like this:

```text
Now I want you to go and audit the implementation plan and the implementation detail files.
Read through it with an eye on determining whether or not there is a sequence of tasks that you need
to be doing that are obvious from reading this. Because I don't know if there's enough here. For example,
when I look at the core implementation, it would be useful to reference the appropriate places in the implementation
details where it can find the information as it walks through each step in the core implementation or in the refinement.
```

This helps refine the implementation plan and helps you avoid potential blind spots that Claude Code missed in its planning cycle. Once the initial refinement pass is complete, ask Claude Code to go through the checklist once more before you can get to the implementation.

You can also ask Claude Code (if you have the [GitHub CLI](https://docs.github.com/en/github-cli/github-cli) installed) to go ahead and create a pull request from your current branch to `main` with a detailed description, to make sure that the effort is properly tracked.

>[!NOTE]
>Before you have the agent implement it, it's also worth prompting Claude Code to cross-check the details to see if there are any over-engineered pieces (remember - it can be over-eager). If over-engineered components or decisions exist, you can ask Claude Code to resolve them. Ensure that Claude Code follows the [constitution](base/memory/constitution.md) as the foundational piece that it must adhere to when establishing the plan.

### STEP 5: Implementation

Once ready, instruct Claude Code to implement your solution (example path included):

```text
implement specs/proj-123.create-taskify/plan.md
```

Claude Code will spring into action and will start creating the implementation.

>[!IMPORTANT]
>Claude Code will execute local CLI commands (such as `dotnet`) - make sure you have them installed on your machine.

Once the implementation step is done, ask Claude Code to try to run the application and resolve any emerging build errors. If the application runs, but there are _runtime errors_ that are not directly available to Claude Code through CLI logs (e.g., errors rendered in browser logs), copy and paste the error in Claude Code and have it attempt to resolve it.

</details>

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

## 👥 Maintainers

- Den Delimarsky ([@localden](https://github.com/localden))
- John Lam ([@jflam](https://github.com/jflam))

## 💬 Support

For support, please open a [GitHub issue](https://github.com/github/spec-kit/issues/new). We welcome bug reports, feature requests, and questions about using Spec-Driven Development.

## 🙏 Acknowledgements

This project is heavily influenced by and based on the work and research of [John Lam](https://github.com/jflam).

## 📄 License

This project is licensed under the terms of the MIT open source license. Please refer to the [LICENSE](./LICENSE) file for the full terms.
