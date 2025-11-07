# Changelog

<!-- markdownlint-disable MD024 -->

All notable changes to the Specify CLI and templates are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-07

### 🎉 Major Release: Shadow Mode

This major release introduces **Shadow Mode**, a complete hidden installation option for corporate and client projects where Speckit presence should be invisible.

### Added

#### Shadow Mode Installation
- **Shadow Mode**: New installation mode that hides Speckit branding and scripts
  - All scripts moved to `.devtools/speckit/` (hidden/gitignored by default)
  - Generic unbranded templates replacing Speckit-branded versions
  - Customizable branding via `--brand` parameter (default: "Development Tools")
  - All 32 scripts (16 bash + 16 PowerShell) copied to shadow directory
  - Configuration stored in `.devtools/.config.json`
  - Automatic .gitignore management
  - Backward compatible - standard mode remains default

#### New CLI Commands
- **`specify convert`**: Convert between standard and shadow modes
  - `specify convert --to shadow` - Convert to shadow mode
  - `specify convert --to shadow --brand "Company Name"` - With custom branding
  - `specify convert --to standard` - Convert back to standard mode
  - `--no-backup` option to skip backup creation (not recommended)
  - Automatic backup creation in `.devtools/backups/` with timestamps

- **`specify info`**: Display current configuration and mode
  - Shows current mode (standard or shadow)
  - Displays version information
  - Lists configuration details
  - Shows available scripts and commands count
  - Mode-specific tips and conversion instructions

#### New CLI Parameters for `init`
- `--mode [standard|shadow]`: Choose installation mode (default: standard)
- `--brand "Name"`: Custom brand name for shadow mode (default: "Development Tools")
- `--shadow-path "path"`: Custom shadow directory (default: ".devtools/speckit")
- `--include-docs` / `--no-docs`: Include generic documentation (default: true)
- `--gitignore-shadow` / `--no-gitignore`: Control .gitignore update (default: true)

#### Shadow Mode Templates (9 files)
All in `templates/shadow/`:
- `spec-template.md` - Generic specification format
- `plan-template.md` - Generic implementation plan
- `tasks-template.md` - Generic task breakdown
- `checklist-template.md` - Generic quality checklist
- `ai-doc-template.md` - Generic AI documentation
- `quick-ref-template.md` - Generic quick reference
- `constitution-universal.md` - Generic project principles
- `agent-file-template.md` - Generic agent configuration
- `vscode-settings.json` - VS Code settings

#### Shadow Mode Commands (22 files)
All in `templates/shadow/commands/` (unbranded, no `/speckit.` prefix):
- Core workflow: `specify.md`, `plan.md`, `tasks.md`, `implement.md`, `validate.md`
- Quality: `analyze.md`, `checklist.md`, `clarify.md`, `clarify-history.md`
- Utilities: `budget.md`, `prune.md`, `find.md`, `error-context.md`
- Project: `discover.md`, `document.md`, `onboard.md`, `project-analysis.md`, `project-catalog.md`
- Services: `service-catalog.md`, `validate-contracts.md`
- Workflow: `resume.md`, `constitution.md`

#### Documentation
- **`docs/SHADOW_MODE.md`**: Comprehensive shadow mode guide
  - What is shadow mode and when to use it
  - Installation instructions
  - Configuration options
  - Feature comparison table
  - Conversion guide
  - Troubleshooting
  - FAQ

- **`docs/shadow/workflow.md`**: Generic development workflow
  - Specification-driven development process
  - Best practices
  - Common patterns
  - Tool integration

- **`docs/shadow/CONVERSION.md`**: Detailed conversion guide
  - Step-by-step conversion instructions
  - Backup and recovery procedures
  - Troubleshooting conversion issues
  - Migration checklist

- **`.devtools.config.json.example`**: Example shadow mode configuration

#### Shadow Mode Module
- **`src/specify_cli/shadow_mode.py`**: Complete shadow mode implementation (~500 lines)
  - `setup_shadow_mode()` - Shadow mode setup
  - `convert_standard_to_shadow()` - Conversion with backup
  - `convert_shadow_to_standard()` - Reverse conversion
  - `detect_current_mode()` - Mode detection
  - `load_config()` - Configuration loading
  - `create_backup()` - Timestamped backups
  - All helper functions for directory management, script copying, template generation

### Changed

- **Version**: Bumped from `0.0.20` to `1.0.0` (major release)
- **Configuration Location**: Shadow mode uses `.devtools/.config.json` (inside .devtools)
- **Command Names**: Shadow mode removes `/speckit.` prefix (e.g., `/specify` instead of `/speckit.specify`)
- **README**: Added comprehensive Installation Modes section with feature comparison
- **Table of Contents**: Updated with Shadow Mode links

### Features Comparison

| Feature | Standard Mode | Shadow Mode |
|---------|---------------|-------------|
| Scripts Location | `scripts/` (visible) | `.devtools/speckit/` (hidden) |
| Templates | Speckit-branded | Generic/unbranded |
| Commands | `/speckit.*` prefix | No prefix |
| Configuration | `.speckit.config.json` | `.devtools/.config.json` |
| .gitignore | Not modified | `.devtools/` added |
| Branding | Speckit | Customizable |
| Scripts Included | All 32 | All 32 |
| Commands Available | 22 | 22 |

### Technical Details

#### Scripts in Shadow Mode
All 32 scripts copied to shadow directory:
- **Bash (16)**: `validate-spec.sh`, `token-budget.sh`, `semantic-search.sh`, `session-prune.sh`, `error-analysis.sh`, `clarify-history.sh`, `project-analysis.sh`, `project-catalog.sh`, `onboard.sh`, `reverse-engineer.sh`, `create-new-feature.sh`, `setup-plan.sh`, `setup-ai-doc.sh`, `update-agent-context.sh`, `check-prerequisites.sh`, `common.sh`
- **PowerShell (16)**: Equivalent .ps1 versions with full feature parity

#### Backup System
- Automatic timestamped backups during conversion
- Backup location: `.devtools/backups/<mode>-<timestamp>/`
- Includes all scripts, templates, and configuration
- Can be disabled with `--no-backup` (not recommended)

#### Command Placeholders
Shadow mode commands use placeholders replaced during setup:
- `{SHADOW_PATH}` → actual shadow path (e.g., `.devtools/speckit`)
- `{SCRIPT_EXT}` → `.sh` or `.ps1` based on script type

### Backward Compatibility

- ✅ Standard mode remains default (no breaking changes)
- ✅ Existing projects unaffected
- ✅ All existing commands work as before
- ✅ Existing workflows unchanged
- ✅ Can convert between modes at any time

### Migration Guide

**For New Projects:**
```bash
# Shadow mode
specify init my-project --mode shadow --brand "Company Name"

# Standard mode (default)
specify init my-project
```

**For Existing Projects:**
```bash
# Convert to shadow
specify convert --to shadow --brand "Company Name"

# Convert back to standard
specify convert --to standard

# Check current mode
specify info
```

### Use Cases

**Shadow Mode is ideal for:**
- Corporate repositories requiring internal branding
- Client projects where external tools should be invisible
- Teams with established internal methodologies
- Projects needing framework-agnostic development tools

**Standard Mode is ideal for:**
- Personal projects
- Learning and experimentation
- Open-source projects
- Speckit contribution and development

### Known Limitations

- Shadow mode scripts must be manually updated (no automatic update mechanism yet)
- Converting modes requires manual review of custom configurations
- Shadow path should not be changed after installation

---

## [Unreleased]

### Added

#### Token Optimization Features

- **Quick Reference Cards**: Ultra-compact documentation system for features
  - New `templates/quick-ref-template.md` template (<200 tokens per feature)
  - Automatic generation alongside full AI documentation
  - 90% token reduction per feature lookup (200 tokens vs 2,400)
  - Updated `/speckit.document` command to generate both `quick-ref.md` and `ai-doc.md`
  - Bash script: `scripts/bash/setup-ai-doc.sh` (updated)
  - PowerShell script: `scripts/powershell/setup-ai-doc.ps1` (updated)

- **Token Budget Tracker** (`/speckit.budget`): Real-time token usage estimation
  - Command template: `templates/commands/budget.md`
  - Bash implementation: `scripts/bash/token-budget.sh`
  - Shows breakdown by conversation, specs, constitution, code context
  - Provides context-aware optimization recommendations (healthy/moderate/high/critical)
  - Warns at 60%, 80% thresholds
  - Suggests optimization strategies (prune, incremental analysis, summary modes)

- **Specification Validation** (`/speckit.validate`): Early quality gates
  - Command template: `templates/commands/validate.md`
  - Bash implementation: `scripts/bash/validate-spec.sh`
  - Validation modes: `--spec`, `--plan`, `--tasks`, `--all`, `--constitution`
  - Checks: file existence, required sections, TODO/TBD placeholders, minimum content
  - Severity levels: Critical, Warning, Info
  - Actionable recommendations for each issue

#### Code Discovery Features

- **Semantic Code Search** (`/speckit.find`): Natural language project search
  - Command template: `templates/commands/find.md`
  - Bash implementation: `scripts/bash/semantic-search.sh`
  - Natural language queries (e.g., "where is authentication handled?")
  - Searches across: code, specs, plans, AI docs, tests
  - Relevance scoring with keyword matching + proximity + file type
  - Prioritizes quick refs in results (lower token cost)
  - Average search time: 50-150ms
  - Filters: `--type code/docs/tests`, `--feature NAME`, `--limit N`
  - Returns ranked results with file:line references

#### Session Management Features

- **Context Pruning** (`/speckit.prune`): Session compression
  - Command template: `templates/commands/prune.md`
  - Bash implementation: `scripts/bash/session-prune.sh`
  - Compresses session to save 40-60K tokens (typical 64% reduction)
  - Smart preservation: current state, decisions, integration points, next steps
  - Smart removal: resolved questions, exploration logs, completed work, redundancy
  - Generates session summary in `.speckit/memory/session-summary-YYYY-MM-DD.md`
  - Recommended when token usage exceeds 80K

- **Resume Implementation** (`/speckit.resume`): Checkpoint recovery system
  - Command template: `templates/commands/resume.md`
  - Checkpoint file format: `.speckit-progress.json`
  - Tracks: completed tasks, current task, failed tasks, state
  - Enables recovery from interrupted `/speckit.implement` sessions
  - Foundation ready for integration with implementation workflow

#### Advanced Debugging Features (Phase 3)

- **Error Context Enhancer** (`/speckit.error-context`): AI-assisted error debugging
  - Command template: `templates/commands/error-context.md`
  - Bash implementation: `scripts/bash/error-analysis.sh`
  - Cross-references errors with specifications to identify violated requirements
  - Pattern recognition for different error types (type errors, test failures, build/runtime errors)
  - Relevance scoring: keyword matches × 40 + file proximity × 30 + requirement type × 20
  - Provides possible causes, fix suggestions, and related spec references
  - Examples: "TypeError: Cannot read property 'status'" → finds REQ-005 about status transitions
  - Helps identify missing requirements vs implementation bugs

- **Differential Analysis** (Project Analysis enhancement): Git-based change detection
  - New `--diff-only` flag for `scripts/bash/project-analysis.sh`
  - Uses git diff to analyze only changed specs (80-95% faster than full analysis)
  - Performance metrics: elapsed time, specs per second
  - Fallback to full analysis if not in git repository
  - Complements existing `--incremental` (file hash) mode
  - Performance comparison:
    - `--diff-only`: Fastest (git-based, working tree changes only)
    - `--incremental`: Fast (file hash-based, since last run)
    - `--summary`: Quick (all specs, minimal analysis)
    - Default: Thorough (all specs, full analysis)

- **Clarification History Tracker** (`/speckit.clarify-history`): Decision audit trail
  - Command template: `templates/commands/clarify-history.md`
  - Bash implementation: `scripts/bash/clarify-history.sh`
  - Displays all clarification sessions and Q&A pairs from spec.md
  - Search capability: find decisions by keyword (e.g., "authentication", "rate limit")
  - Cross-feature consistency checking
  - Helps with onboarding and decision tracking
  - Extracts from `## Clarifications` section in specifications

#### Configuration & Infrastructure

- **Configuration System**: Centralized project preferences
  - Configuration schema: `.speckit.config.json.example`
  - Settings: cache (enabled, retention, location)
  - Settings: analysis (default mode, sample size, auto patterns)
  - Settings: agent (type, context file)
  - Settings: validation (strict, auto validate)
  - Settings: documentation (auto generate quick ref, token target)
  - Settings: budget (warn threshold, critical threshold)
  - Default values ensure backward compatibility

- **Comprehensive Workflow Guide**: End-to-end documentation
  - New file: `IMPROVED-WORKFLOW.md`
  - Documents: new project creation workflow
  - Documents: adding features to existing codebase
  - Documents: all new commands with examples
  - Documents: token savings comparisons
  - Documents: best practices and decision trees

### Changed

- **Documentation Updates**:
  - `README.md`: Added Phase 1 & 2 commands to Optional Commands section
  - `templates/commands/document.md`: Updated to reference quick-ref.md generation
  - All new commands marked as **NEW** in documentation

- **Script Enhancements**:
  - `scripts/bash/setup-ai-doc.sh`: Now generates both `ai-doc.md` and `quick-ref.md`
  - `scripts/powershell/setup-ai-doc.ps1`: Now generates both documentation files
  - `scripts/bash/project-analysis.sh`: Added `--diff-only` mode and performance metrics
  - `scripts/bash/token-budget.sh`: Added performance timing to existing scripts

- **Git Configuration**:
  - `.gitignore`: Added exclusions for cache and checkpoint files
  - Excludes: `.speckit-cache/`, `.speckit-analysis-cache.json`
  - Excludes: `.speckit-progress.json`, `.speckit/memory/session-summary-*.md`
  - Excludes: `.speckit.config.json` (user configuration)

### Performance & Token Savings

- **Quick Reference Cards**: 90% reduction per feature lookup (2,200 tokens saved)
- **Context Pruning**: 50,000 tokens saved per prune (64% typical reduction)
- **Token Budget Visibility**: Enables proactive optimization decisions
- **Validation**: Prevents wasted tokens on incomplete specifications
- **Semantic Search**: Instant code location vs manual exploration
- **Combined Potential**: Up to 85-98% total savings vs unoptimized workflow

#### Platform Parity & Automation (Phase 4)

- **PowerShell Feature Parity**: Core Phase 1-2 features now available on Windows
  - `scripts/powershell/token-budget.ps1`: Full Windows token budget tracking
  - `scripts/powershell/validate-spec.ps1`: Complete spec validation for Windows
  - Identical functionality to Bash versions
  - JSON output support for automation

- **Git Pre-Commit Hook**: Automated spec validation
  - `hooks/pre-commit`: Validates specs before commit
  - Checks: required sections, minimum content, placeholders
  - Critical errors block commits, warnings allow but notify
  - Easy installation via symlink or copy
  - Bypass available with `--no-verify` for WIP commits
  - Comprehensive documentation in `hooks/README.md`

#### Complete Platform Parity (Phase 5)

- **Full PowerShell Implementation**: 100% feature parity with bash scripts
  - `scripts/powershell/semantic-search.ps1`: Natural language code search
    - Keyword extraction, relevance scoring
    - Search across code, specs, docs, tests
    - 50-200ms average search time on Windows
    - JSON and text output modes

  - `scripts/powershell/session-prune.ps1`: Session context compression
    - Collects project state for AI compression
    - Estimates 50K token savings per session
    - Creates session summaries in `.speckit/memory/`

  - `scripts/powershell/error-analysis.ps1`: AI-assisted error debugging
    - Error type classification (type/test/build/runtime)
    - Spec cross-referencing with relevance scoring
    - Possible causes and fix suggestions
    - Supports --File and --Line for precise location

  - `scripts/powershell/clarify-history.ps1`: Clarification decision tracking
    - Parses Q&A from spec.md clarifications sections
    - Search by keyword across all sessions
    - JSON output for tooling integration

- **Platform Compatibility Guide**: Comprehensive cross-platform documentation
  - `PLATFORM-COMPATIBILITY.md`: Complete usage guide
  - Platform support matrix (Linux/macOS/Windows/WSL/PowerShell Core)
  - Command syntax differences (bash vs PowerShell)
  - Troubleshooting for each platform
  - CI/CD integration examples (GitHub Actions, GitLab CI)
  - Performance characteristics comparison

### Technical Details

- **Bash implementations**: Complete for Linux/macOS/WSL (Phases 1-6)
  - Phase 6: Cross-platform Bash port for full Linux/macOS support
  - All PowerShell features ported to Bash with feature parity
  - Includes common utility library (`scripts/bash/lib/common.sh`)
  - Supports project analysis, onboarding, reverse engineering, and catalog generation
- **PowerShell implementations**: 100% feature parity achieved (Phases 1-5)
  - All core and advanced features available on Windows
  - Identical functionality to bash versions
  - JSON output support for automation
  - PowerShell Core compatible (cross-platform)
- **Testing**: All Phase 1-6 features tested and verified
  - Phase 3: error-analysis.sh, project-analysis.sh --diff-only, clarify-history.sh
  - Phase 4: token-budget.ps1, validate-spec.ps1, pre-commit hook
  - Phase 5: semantic-search.ps1, session-prune.ps1, error-analysis.ps1, clarify-history.ps1
  - Phase 6: project-analysis.sh, onboard.sh, reverse-engineer.sh, project-catalog.sh
- **Git Hooks**: Pre-commit validation for quality gates
- **Platform Support**: Linux, macOS, Windows, WSL, PowerShell Core
- **Compatibility**: Backward compatible with existing spec-kit workflows

## [0.0.20] - 2025-10-14

### Added

- **Intelligent Branch Naming**: `create-new-feature` scripts now support `--short-name` parameter for custom branch names
  - When `--short-name` provided: Uses the custom name directly (cleaned and formatted)
  - When omitted: Automatically generates meaningful names using stop word filtering and length-based filtering
  - Filters out common stop words (I, want, to, the, for, etc.)
  - Removes words shorter than 3 characters (unless they're uppercase acronyms)
  - Takes 3-4 most meaningful words from the description
  - **Enforces GitHub's 244-byte branch name limit** with automatic truncation and warnings
  - Examples:
    - "I want to create user authentication" → `001-create-user-authentication`
    - "Implement OAuth2 integration for API" → `001-implement-oauth2-integration-api`
    - "Fix payment processing bug" → `001-fix-payment-processing`
    - Very long descriptions are automatically truncated at word boundaries to stay within limits
  - Designed for AI agents to provide semantic short names while maintaining standalone usability

### Changed

- Enhanced help documentation for `create-new-feature.sh` and `create-new-feature.ps1` scripts with examples
- Branch names now validated against GitHub's 244-byte limit with automatic truncation if needed

## [0.0.19] - 2025-10-10

### Added

- Support for CodeBuddy (thank you to [@lispking](https://github.com/lispking) for the contribution).
- You can now see Git-sourced errors in the Specify CLI.

### Changed

- Fixed the path to the constitution in `plan.md` (thank you to [@lyzno1](https://github.com/lyzno1) for spotting).
- Fixed backslash escapes in generated TOML files for Gemini (thank you to [@hsin19](https://github.com/hsin19) for the contribution).
- Implementation command now ensures that the correct ignore files are added (thank you to [@sigent-amazon](https://github.com/sigent-amazon) for the contribution).

## [0.0.18] - 2025-10-06

### Added

- Support for using `.` as a shorthand for current directory in `specify init .` command, equivalent to `--here` flag but more intuitive for users.
- Use the `/speckit.` command prefix to easily discover Spec Kit-related commands.
- Refactor the prompts and templates to simplify their capabilities and how they are tracked. No more polluting things with tests when they are not needed.
- Ensure that tasks are created per user story (simplifies testing and validation).
- Add support for Visual Studio Code prompt shortcuts and automatic script execution.

### Changed

- All command files now prefixed with `speckit.` (e.g., `speckit.specify.md`, `speckit.plan.md`) for better discoverability and differentiation in IDE/CLI command palettes and file explorers

## [0.0.17] - 2025-09-22

### Added

- New `/clarify` command template to surface up to 5 targeted clarification questions for an existing spec and persist answers into a Clarifications section in the spec.
- New `/analyze` command template providing a non-destructive cross-artifact discrepancy and alignment report (spec, clarifications, plan, tasks, constitution) inserted after `/tasks` and before `/implement`.
  - Note: Constitution rules are explicitly treated as non-negotiable; any conflict is a CRITICAL finding requiring artifact remediation, not weakening of principles.

## [0.0.16] - 2025-09-22

### Added

- `--force` flag for `init` command to bypass confirmation when using `--here` in a non-empty directory and proceed with merging/overwriting files.

## [0.0.15] - 2025-09-21

### Added

- Support for Roo Code.

## [0.0.14] - 2025-09-21

### Changed

- Error messages are now shown consistently.

## [0.0.13] - 2025-09-21

### Added

- Support for Kilo Code. Thank you [@shahrukhkhan489](https://github.com/shahrukhkhan489) with [#394](https://github.com/github/spec-kit/pull/394).
- Support for Auggie CLI. Thank you [@hungthai1401](https://github.com/hungthai1401) with [#137](https://github.com/github/spec-kit/pull/137).
- Agent folder security notice displayed after project provisioning completion, warning users that some agents may store credentials or auth tokens in their agent folders and recommending adding relevant folders to `.gitignore` to prevent accidental credential leakage.

### Changed

- Warning displayed to ensure that folks are aware that they might need to add their agent folder to `.gitignore`.
- Cleaned up the `check` command output.

## [0.0.12] - 2025-09-21

### Changed

- Added additional context for OpenAI Codex users - they need to set an additional environment variable, as described in [#417](https://github.com/github/spec-kit/issues/417).

## [0.0.11] - 2025-09-20

### Added

- Codex CLI support (thank you [@honjo-hiroaki-gtt](https://github.com/honjo-hiroaki-gtt) for the contribution in [#14](https://github.com/github/spec-kit/pull/14))
- Codex-aware context update tooling (Bash and PowerShell) so feature plans refresh `AGENTS.md` alongside existing assistants without manual edits.

## [0.0.10] - 2025-09-20

### Fixed

- Addressed [#378](https://github.com/github/spec-kit/issues/378) where a GitHub token may be attached to the request when it was empty.

## [0.0.9] - 2025-09-19

### Changed

- Improved agent selector UI with cyan highlighting for agent keys and gray parentheses for full names

## [0.0.8] - 2025-09-19

### Added

- Windsurf IDE support as additional AI assistant option (thank you [@raedkit](https://github.com/raedkit) for the work in [#151](https://github.com/github/spec-kit/pull/151))
- GitHub token support for API requests to handle corporate environments and rate limiting (contributed by [@zryfish](https://github.com/@zryfish) in [#243](https://github.com/github/spec-kit/pull/243))

### Changed

- Updated README with Windsurf examples and GitHub token usage
- Enhanced release workflow to include Windsurf templates

## [0.0.7] - 2025-09-18

### Changed

- Updated command instructions in the CLI.
- Cleaned up the code to not render agent-specific information when it's generic.

## [0.0.6] - 2025-09-17

### Added

- opencode support as additional AI assistant option

## [0.0.5] - 2025-09-17

### Added

- Qwen Code support as additional AI assistant option

## [0.0.4] - 2025-09-14

### Added

- SOCKS proxy support for corporate environments via `httpx[socks]` dependency

### Fixed

N/A

### Changed

N/A
