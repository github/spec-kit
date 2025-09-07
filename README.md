# SpecifyX

**Enhanced spec-driven development CLI with modern architecture and Jinja2 templating**

[![Release](https://github.com/barisgit/spec-kit-improved/actions/workflows/release.yml/badge.svg)](https://github.com/barisgit/spec-kit-improved/actions/workflows/release.yml)
[![PyPI version](https://badge.fury.io/py/specifyx.svg)](https://badge.fury.io/py/specifyx)

---

## What is SpecifyX?

SpecifyX is a modern, Python-installable CLI tool for spec-driven development that helps organizations focus on product scenarios rather than writing undifferentiated code.

### Key Benefits for Users (envisioned - not implemented yet)

- **Easy Installation**: Install with `uv add specifyx` or `pip install specifyx` - no complex setup required
- **Powerful Templating**: Use Jinja2 templates with variables, conditionals, and loops for complex project generation
- **Flexible Branch Naming**: Customize branch patterns like `feature/{name}` or `task/{id}-{name}` instead of fixed formats
- **Enhanced User Experience**: Interactive menus, progress tracking, and better error messages
- **Configuration System**: Save your preferences in TOML files instead of repeating command-line options

## Installation

### Using uv (recommended)
```bash
uv add specifyx
```

### Using pipx (for CLI tools)
```bash
pipx install specifyx
```

### Using pip
```bash
pip install specifyx
```

### From git (development version)
```bash
uv add git+https://github.com/barisgit/spec-kit-improved
```

## Quick Start

Initialize a new spec-driven project:
```bash
specifyx init my-project
specifyx init --here  # in current directory
```

Check tool requirements:
```bash
specifyx check
```

## Attribution and Philosophy

### Inspiration and Attribution

This project is **inspired by and builds upon** the foundational work of the original [specify](https://github.com/microsoft/specify) project by the Microsoft team, particularly [John Lam](https://github.com/jflam) and [Den Delimarsky](https://github.com/dend). Their pioneering work in spec-driven development methodology laid the groundwork for this enhanced implementation.

### Why a Separate Project?

While deeply respecting the original specify project, SpecifyX takes a different philosophical approach in several key areas:

#### **1. Installation and Distribution**
- **Original specify**: Git-based templates requiring manual setup
- **SpecifyX**: Standard Python package installable via PyPI for easier adoption

#### **2. Templating Capabilities** 
- **Original specify**: Basic string replacement templating
- **SpecifyX**: Full Jinja2 templating with variables, loops, conditionals, and complex logic

#### **3. Configuration and Customization**
- **Original specify**: Minimal configuration, mostly environment-based
- **SpecifyX**: Rich TOML-based configuration system with user preferences and project-specific settings

#### **4. Branch Naming Flexibility**
- **Original specify**: Fixed pattern like "001-feature-name"
- **SpecifyX**: Customizable patterns to match your team's conventions

#### **5. User Experience Focus**
- **Original specify**: Bash scripts with basic output
- **SpecifyX**: Interactive UI with progress tracking, colored output, and helpful error messages

### Our Vision

SpecifyX aims to make spec-driven development more **accessible and powerful** for teams who want enhanced tooling while maintaining full respect for the original methodology. We believe both approaches serve different needs in the ecosystem.

## What is Spec-Driven Development?

Spec-Driven Development **flips the script** on traditional software development. Instead of code being king, **specifications become executable**, directly generating working implementations rather than just guiding them.

### Core Philosophy

- **Intent-driven development** where specifications define the "_what_" before the "_how_"
- **Rich specification creation** using guardrails and organizational principles  
- **Multi-step refinement** rather than one-shot code generation from prompts
- **Heavy reliance** on advanced AI model capabilities for specification interpretation

## Development Phases

| Phase | Focus | Key Activities |
|-------|-------|----------------|
| **0-to-1 Development** | Generate from scratch | Generate specs → Plan implementation → Build production-ready applications |
| **Creative Exploration** | Parallel implementations | Explore diverse solutions → Support multiple tech stacks → Experiment with UX patterns |
| **Iterative Enhancement** | Brownfield modernization | Add features iteratively → Modernize legacy systems → Adapt processes |

## Prerequisites

- **Linux/macOS** (or WSL2 on Windows)
- **Python 3.11+** 
- AI coding agent: [Claude Code](https://www.anthropic.com/claude-code), [GitHub Copilot](https://code.visualstudio.com/), or [Gemini CLI](https://github.com/google-gemini/gemini-cli)
- [uv](https://docs.astral.sh/uv/) for package management (recommended)
- [Git](https://git-scm.com/downloads)

## Enhanced Features

### Jinja2 Templating
```bash
# Advanced template rendering with variables and logic
specifyx init {{ project_name }} --template advanced
```

### Flexible Configuration  
```toml
# ~/.config/specifyx/config.toml
[branch_naming]
pattern = "feature/{feature-name}"
auto_increment = true

[templates]
custom_dir = "~/my-templates"
```

### Enhanced User Interface
- Interactive menus with keyboard navigation
- Progress tracking with live updates  
- Rich console output with colored themes
- Graceful fallbacks for limited terminals

## Technical Details

For developers interested in the architecture:

- **Modern Architecture**: Modular services instead of monolithic code (870 lines → 32 lines main file)
- **Type Safety**: Full type annotations and validation throughout
- **Comprehensive Testing**: Contract, integration, and unit tests with high coverage
- **TOML Configuration**: Flexible configuration with dynaconf

## Documentation

- **[Architecture Overview](./CLAUDE.md)** - Technical architecture and design decisions
- **[Development Guide](./specs/001-feature-improve-spec/)** - Implementation specifications and contracts

## Development

### Setup Development Environment
```bash
git clone https://github.com/barisgit/spec-kit-improved
cd spec-kit-improved
uv sync --dev
```

### Run Tests
```bash
pytest                    # All tests
pytest tests/contract/    # Contract tests
pytest tests/integration/ # Integration tests
pytest tests/unit/        # Unit tests
```

### Code Quality
```bash
ruff check .              # Linting
ruff format .             # Formatting  
pyrefly check .           # Type checking
```

## Contributing

We welcome contributions! Please see our development specifications in `specs/001-feature-improve-spec/` for architecture details and implementation contracts.

## Support

For support, please open a [GitHub issue](https://github.com/barisgit/spec-kit-improved/issues/new). We welcome bug reports, feature requests, and questions about using spec-driven development.

## License

This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.

---

**SpecifyX**: Making spec-driven development more accessible and powerful for modern development teams.