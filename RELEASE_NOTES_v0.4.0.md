# Release v0.4.0 - Major Feature Milestone

## 🎯 Overview

This release marks a significant milestone for Spec Kit with three major features that enhance flexibility, scalability, and developer experience:

1. **OpenSpec-Inspired Adaptive Workflows** - Progressive specification depth based on change complexity
2. **Multi-Repo Workspace Support** - Manage specifications across multiple repositories
3. **Capability-Based Atomic PRs** - Decompose large features into reviewable units

---

## ✨ Major Features

### 🚀 OpenSpec-Inspired Adaptive Workflows

Introduces **adaptive depth system** with three workflow modes, bringing 80% of OpenSpec benefits without integration complexity:

#### Workflow Modes

- **Quick Mode** (<200 LOC)
  - Minimal specification for bug fixes and tiny changes
  - Template: `spec-template-quick.md`
  - Fast path for urgent fixes

- **Lightweight Mode** (200-800 LOC)
  - Compact specification for simple features
  - Templates: `spec-template-lightweight.md`, `plan-template-lightweight.md`
  - Optimized for token consumption

- **Full Mode** (800+ LOC)
  - Comprehensive specification (existing default)
  - Templates: `spec-template.md`, `plan-template.md`
  - For complex, critical features

#### Key Benefits

- 🎯 **Beginner-friendly**: AI-guided mode selection via `/specify` command
- ⚡ **Token-efficient**: Right-sized specs reduce AI token consumption
- 🔄 **Backward compatible**: All existing commands work unchanged
- 📊 **Progressive disclosure**: Single mental model that scales with complexity

#### New Commands

- `/archive` - Archive completed features to `archive/` directory with git history preservation

**Commit:** f6c7c2a

---

### 🏢 Multi-Repo Workspace Support

Manage specifications across multiple repositories from a centralized workspace:

#### Features

- **Auto-discovery**: Automatically finds git repositories (max depth 2)
- **Convention-based targeting**: Route specs to repos via naming patterns
- **Centralized specs**: Single `specs/` directory for all workspace specifications
- **Workspace configuration**: `.specify/workspace.yml` with customizable routing rules

#### Convention-Based Routing

Specs automatically target repositories based on prefixes and suffixes:

```yaml
conventions:
  prefix_rules:
    backend-: [backend-repo]
    mobile-: [mobile-repo]
    fullstack-: [backend-repo, mobile-repo]

  suffix_rules:
    -api: [backend-repo]
    -ui: [mobile-repo]
```

#### Initialization

```bash
# Initialize workspace in current directory
specify init --workspace --here --ai claude

# Auto-initialize .specify/ in all discovered repos
specify init --workspace --auto-init
```

#### Workspace Structure

```
workspace-root/
  .specify/
    workspace.yml              # Workspace configuration
  specs/                       # Centralized specifications
    backend-auth/
      spec.md
      plan.md
  backend-repo/                # Git repository
  mobile-repo/                 # Git repository
```

**Commit:** 70256b6

---

### ⚛️ Capability-Based Atomic PRs

Decompose large features into small, atomic pull requests for faster review cycles:

#### Features

- **Capability decomposition**: Break specs into single-repo capabilities
- **Atomic branches**: Each capability gets its own feature branch
- **Independent PRs**: Review and merge capabilities separately
- **Constitution integration**: Article VIII on Atomic Development

#### Usage

```bash
# Create parent spec
/specify fullstack-sync-engine

# Decompose into capabilities
/decompose

# Plan specific capability
/plan --capability cap-001

# Work in capability branch
git checkout feature/username/cap-001.sync-api-endpoints
```

#### Benefits

- ✅ **Faster reviews**: Small, focused PRs merge quickly
- 🔍 **Better quality**: Easier to spot issues in atomic changes
- 🚀 **Parallel development**: Multiple capabilities can progress independently
- 📝 **Clear scope**: Each capability has explicit boundaries

**Commits:** 5d8e32b, bbb41dc, 465cfc6

---

## 💥 Breaking Changes

### Directory Rename: `.spec-kit` → `.specify`

For consistency and clarity, the project configuration directory has been renamed:

**Before:** `.spec-kit/`
**After:** `.specify/`

**Migration:** If upgrading an existing project, rename your `.spec-kit` directory to `.specify`:

```bash
mv .spec-kit .specify
```

**Commit:** 7ff403b

---

## 🐛 Bug Fixes

- **CLI relative path issue**: Fixed path resolution in `specify` CLI (5c3bbab)
- **Capability branch creation**: Fixed race condition where branch wasn't created before file creation (d3294a5)
- **Capability ID parsing**: Support capability IDs with letter suffixes (615debe)
- **Template paths**: Fixed duplicate `.specify` prefix in `implement.md` paths (613ea3e)
- **UTF-8 encoding**: Added explicit UTF-8 encoding to all markdown generation commands (39b52e1)

---

## 📚 Documentation

### Complete Documentation Restructure

Reorganized documentation following the Diátaxis framework:

```
docs/
├── getting-started/        # Tutorials
├── guides/                 # How-to guides
├── concepts/               # Explanations
├── reference/              # Technical reference
└── contributing/           # Developer docs
```

**Key improvements:**

- 🎓 Clear learning paths for beginners
- 🔍 Easier navigation and discoverability
- 📖 Separated conceptual vs. practical documentation
- 🤝 Contributing guidelines for developers

**Commits:** ba3aba3, 2072286, 28b5826, aea3473, 530fb72, 32670e4, and 6 more

### Template Updates

- **LOC limits**: Updated to target 1000 LOC with test ratio requirements (f0a721d)
- **Jira format**: Changed from uppercase to lowercase (de88025)
- **Change history**: Added to spec templates for delta tracking (f6c7c2a)

---

## 🔧 Improvements

### CLI Enhancements

- **GitHub host-aware Jira**: Jira key detection respects GitHub host configuration (93aadfa)
- **Default Jira project**: Set `wtmt` as default in smart-commit command (e55c2b0)
- **Multi-repo init**: Support initialization across multiple repositories (39b52e1)
- **Conditional branching**: Feature branch naming supports multiple patterns (c4f14fa)

### AI Assistant Isolation

- **Subfolder organization**: AI assistant commands isolated in `.specify/{ai}/` subfolders (5d47b07)
- **Cleaner project root**: Less clutter in repository root directory

---

## 📦 Installation

### Quick Start (Temporary Execution)

```bash
uvx --from git+https://github.com/hcnimi/spec-kit.git specify init <PROJECT_NAME>
```

### Global Installation

**Using uv (recommended):**
```bash
uv tool install git+https://github.com/hcnimi/spec-kit.git
```

**Using pip:**
```bash
pip install git+https://github.com/hcnimi/spec-kit.git
```

### Workspace Mode

```bash
# Initialize workspace with auto-discovery
specify init --workspace --here --ai claude

# With auto-initialization of all repos
specify init --workspace --auto-init
```

---

## 🔄 Upgrade Path

### From v0.2.x

1. **Rename directory** (Breaking Change):
   ```bash
   mv .spec-kit .specify
   ```

2. **Update installation**:
   ```bash
   pip install --upgrade git+https://github.com/hcnimi/spec-kit.git
   ```

3. **No changes needed** to:
   - Existing specs (fully backward compatible)
   - Slash commands (work unchanged)
   - Workflows (no breaking changes)

---

## 🎯 What's Next?

### Future Enhancements

- **Remote workspace sync**: Shared workspace configuration across team
- **Spec validation**: Built-in linting for specification quality
- **Metrics dashboard**: Track feature velocity and spec quality
- **IDE extensions**: Deep integration with VS Code, JetBrains IDEs

---

## 🙏 Acknowledgements

Special thanks to:

- **OpenSpec project** for inspiring the adaptive workflow system
- All contributors who provided feedback on workspace mode
- Early adopters who battle-tested capability-based PRs

---

## 📜 Attribution

This release builds upon [GitHub's original spec-kit](https://github.com/github/spec-kit) created by Den Delimarsky and John Lam. This fork (`hcnimi/spec-kit`) is maintained independently by Hubert Nimitanakit.

**Inspirations for v0.4.0 features:**
- **OpenSpec** (Fission-AI/OpenSpec): Adaptive workflow modes
- **PRPs** (Wirasm/PRPs-agentic-eng): Agentic engineering patterns

See [ATTRIBUTION.md](./ATTRIBUTION.md) for complete credits.

---

## 📊 Release Statistics

- **45 commits** since v0.2.2
- **3 major features**
- **5+ bug fixes**
- **13 documentation commits**
- **811 lines** added for OpenSpec workflows
- **2,327 lines** added for workspace support

---

## 📄 Full Changelog

For detailed commit history:
```bash
git log v0.2.2..v0.4.0 --oneline
```

---

**Released:** 2025-11-01
**Tag:** `v0.4.0`
**Python Versions:** >=3.11
**License:** MIT