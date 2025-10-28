# SpecKitPlus Quickstart - From Vibe Coding to Spec-Driven Delivery

You just learned AI pair programming in `01_dev_env/06_ai_pair_programming/` (vibe coding with coding principles). Now we'll rebuild the same calculator project using SpecKitPlus (SPP) and Spec‑Driven Development (SDD) to turn those skills into a professional workflow.

**What you already learned (recap):**
- How to prompt AI agents effectively
- Small steps and checking your work
- Test-driven development with Python 3.12+ type hints

**What you'll do now (SPP Quickstart):**
- Rebuild the same calculator using structured planning (Specify → Plan → Tasks → Implement)
- Keep everything organized with tests and documentation
- Use the same AI agent you prefer (Claude, Cursor, Gemini CLI, Qwen Code, etc.)

**Why SPP for this stage:**
- Better planning means fewer bugs
- Clear specs help AI agents build better code
- Professional git workflow
- Works with any coding agent

## Quickstart Overview

This tutorial groups features together so each step has real complexity:

1. **[Constitution](01_constitution/readme.md)** → One-time project setup
2. **[Feature 1: Basic Operations](02_basic_operations/readme.md)** → Add, subtract, multiply, divide (one complete loop)
3. **[Feature 2: CLI Interface](03_cli_interface/readme.md)** → Command-line interface (one complete loop)
4. **[Feature 3: Error Handling](04_error_handling/readme.md)** → Comprehensive error handling (Complete SPP Tutorial)

## Prerequisites

### Required Knowledge
- Complete the [AI Pair Programming Tutorial](../01_dev_env/06_ai_pair_programming/readme.md) first
- Know what TDD (Test-Driven Development) is
- Basic git skills (branches, commits, pull requests)

### System Requirements
- **Python 3.12+** - Required for modern type hints with `|` union syntax
- **UV** - Python package manager
- **Git** - Version control
- **GitHub account** - For pull requests
- **AI Agent** - Claude Code, Cursor, Gemini CLI, Qwen Code, etc.


## Setup Project using SpecKitPlus

1. Run the installation command:

```bash
uvx specifyplus init calculator-spp
cd calculator-spp
```

2. Select your AI agent (Claude, Cursor, Gemini CLI, etc.)
3. Choose your script type (PowerShell, Bash, etc.)

This will create a new project directory with SpecKit already set up. You can install SpecKit for multiple agents simultaneously by running the command multiple times with different agent selections.

## Project Structure

After installation, SpecKit creates:

```
calculator-spp/
├── .specify/
│   ├── memory/
│   │   └── constitution.md
│   ├── scripts/
│   └── templates/
├── .claude/  (or .gemini/, .cursor/, etc. depending on agent selection)
│   └── commands/
└── history/
    ├── prompts/
    │   └── (all prompt history records organized by stage)
    └── adr/
        └── (architecture decision records)
```

**Key Files:**
- **constitution.md** - Project principles and standards (in `.specify/memory/`)
- **scripts/** - Helper scripts for branch creation and workflow automation (in `.specify/scripts/`)
- **templates/** - Templates for specs, plans, and tasks (in `.specify/templates/`)
- **commands/** - Detailed instructions for each workflow step (in agent-specific folder like `.claude/commands/`)
- **history/prompts/** - All prompt history records organized by type and feature
- **history/adr/** - Architecture decision records

## Core Workflow Components

In SDD you start with a spec. It's like a contract that tells your AI agent exactly what to build. This means less guessing, fewer bugs, and better code.

### 1. Constitution (One-Time Setup)
Set up your project rules and standards at the start.

### 2. Feature Lifecycle
The main workflow for building features:

- **Specify** - Write down what you want to build (in plain English)
- **Clarify** (Optional) - Let the AI ask questions to understand better
- **Plan** - Create a technical plan with data models and interfaces
- **ADR** - Document important decisions (stored in `history/adr/`)
- **Tasks** - Break the plan into small, doable tasks
- **Analyze** (Optional) - Check that documentation is complete
- **Implement** - Let the AI build the features
- **PHR** - Your conversations are automatically saved in `history/prompts/` organized by feature and stage
- **Test & Merge** - Test everything and merge to main branch

## Key Differences from AI Pair Programming

| Aspect | AI Pair Programming | SpecKitPlus |
|--------|-------------------|-------------|
| **Planning** | Ad-hoc prompts | Structured spec → plan → tasks |
| **Documentation** | Minimal | Comprehensive specs and ADRs |
| **Testing** | TDD per feature | TDD with contract tests |
| **Architecture** | Emergent | Planned upfront |
| **Git Workflow** | Feature branches | Structured feature lifecycle |
| **Quality** | Good | Production-ready |

## Getting Started

Ready to begin? Start with the [Constitution Setup](01_constitution/readme.md) to establish your project standards, then follow each loop in sequence.

Each loop is self-contained but builds on the previous work, creating a complete calculator application with professional development practices.

---

**Next:** [01 - Constitution Setup](01_constitution/readme.md)