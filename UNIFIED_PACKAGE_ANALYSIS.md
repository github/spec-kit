# Unified Package Feasibility Analysis & Solution

## Executive Summary

**Goal**: Create a single package per agent containing both shell (.sh) and PowerShell (.ps1) scripts, with runtime OS detection to automatically select the appropriate scripts.

**Feasibility**: ✅ **HIGHLY FEASIBLE** - The system is already well-architected for this change with minimal breaking changes required.

**Impact**:

- Reduces build artifacts from 32 packages (16 agents × 2 scripts) to 16 packages (1 per agent)
- Simplifies user experience - no need to choose script type during installation
- Makes the fork truly cross-platform and "smart"
- Runtime overhead: negligible (simple OS detection)

---

## Current State Analysis

### 1. Current Build Process

**File**: `.github/workflows/scripts/create-release-packages.sh`

Currently builds separate packages:

```bash
# For each agent (claude, gemini, etc.) and each script type (sh, ps):
build_variant() {
  local agent=$1 script=$2
  # Creates: spec-kit-template-claude-sh-v0.2.0.zip
  #          spec-kit-template-claude-ps-v0.2.0.zip
}
```

**Script Copying Logic** (lines 116-131):

```bash
case $script in
  sh)
    [[ -d scripts/bash ]] && cp -r scripts/bash "$SPEC_DIR/scripts/"
    ;;
  ps)
    [[ -d scripts/powershell ]] && cp -r scripts/powershell "$SPEC_DIR/scripts/"
    ;;
esac
```

**Result**: 32 ZIP files per release (16 agents × 2 script types)

### 2. Current Runtime Behavior

**File**: `src/specify_cli/__init__.py` (line 1004)

```python
default_script = "ps" if os.name == "nt" else "sh"
```

**Current Flow**:

1. User runs: `specify init --agent claude --script sh`
2. CLI downloads: `spec-kit-template-claude-sh-v0.2.0.zip`
3. Package contains ONLY bash scripts in `.specify/scripts/bash/`
4. Prompts reference: `scripts/bash/setup-plan.sh`

### 3. Prompt Template Structure

**File**: `templates/commands/plan.md`

```yaml
---
description: Execute the implementation planning workflow
scripts:
  sh: scripts/bash/setup-plan.sh --json
  ps: scripts/powershell/setup-plan.ps1 -Json
agent_scripts:
  sh: scripts/bash/update-agent-context.sh __AGENT__
  ps: scripts/powershell/update-agent-context.ps1 -AgentType __AGENT__
---
```

**Current Substitution** (lines 40-101 of build script):

- Extracts script command based on selected variant (sh or ps)
- Replaces `{SCRIPT}` placeholder with the selected script path
- Removes the unused script variant from frontmatter

### 4. Current Script Organization

```text
scripts/
├── bash/
│   ├── common.sh
│   ├── check-prerequisites.sh
│   ├── create-new-feature.sh
│   ├── setup-plan.sh
│   └── update-agent-context.sh
└── powershell/
    ├── common.ps1
    ├── check-prerequisites.ps1
    ├── create-new-feature.ps1
    ├── setup-plan.ps1
    └── update-agent-context.ps1
```

**Complete Functional Parity**: Both versions have identical functionality, just different syntax.

---

## Feasibility Assessment

### ✅ Advantages

1. **Well-Separated Script Directories**: Scripts are already organized in `bash/` and `powershell/` subdirectories
2. **OS Detection Already Exists**: Python CLI already has OS detection logic
3. **Parallel Implementations**: Both script versions have complete feature parity
4. **No Cross-Dependencies**: Scripts don't call each other across platforms
5. **Template System Ready**: YAML frontmatter already supports both script variants

### ⚠️ Challenges

1. **Prompt Substitution Logic**: Currently embeds single script path - needs to keep both variants
2. **Runtime Script Selection**: Need wrapper or launcher to detect OS and call correct script
3. **Package Size**: Unified packages will be ~2x larger (contains both script sets)
4. **Backward Compatibility**: Existing installations expect single-script packages

### 🎯 Technical Feasibility Score: **9/10**

The architecture is already 90% ready for this change. Main work is in:

- Build script modifications (40% effort)
- Prompt template handling (30% effort)
- Runtime launcher creation (20% effort)
- Testing & validation (10% effort)

---

## Proposed Solution Architecture

### Solution Overview

Create a unified package with:

1. **Both script directories** included in `.specify/scripts/`
2. **Smart launcher scripts** that detect OS and delegate to correct implementation
3. **Updated prompts** that reference launcher scripts (platform-agnostic)
4. **Build process** creates single package per agent

### Directory Structure (Unified Package)

```text
.specify/
├── scripts/
│   ├── bash/                    # Unix/Linux/macOS scripts
│   │   ├── common.sh
│   │   ├── check-prerequisites.sh
│   │   ├── create-new-feature.sh
│   │   ├── setup-plan.sh
│   │   └── update-agent-context.sh
│   ├── powershell/              # Windows scripts
│   │   ├── common.ps1
│   │   ├── check-prerequisites.ps1
│   │   ├── create-new-feature.ps1
│   │   ├── setup-plan.ps1
│   │   └── update-agent-context.ps1
│   └── launchers/               # NEW: OS-detection launchers
│       ├── check-prerequisites
│       ├── create-new-feature
│       ├── setup-plan
│       └── update-agent-context
├── templates/
└── memory/
```

### Launcher Script Design

**Option A: Shell-based Launcher** (Recommended for AI agents)

```bash
#!/usr/bin/env bash
# .specify/scripts/launchers/setup-plan
# OS-agnostic launcher that delegates to correct implementation

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

detect_os() {
  case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*|Windows_NT)
      echo "windows"
      ;;
    Linux*)
      echo "linux"
      ;;
    Darwin*)
      echo "macos"
      ;;
    *)
      echo "unknown"
      ;;
  esac
}

OS_TYPE=$(detect_os)

if [[ "$OS_TYPE" == "windows" ]]; then
  # On Windows, prefer PowerShell
  if command -v pwsh &> /dev/null; then
    pwsh -File "$SCRIPT_DIR/../powershell/setup-plan.ps1" "$@"
  elif command -v powershell &> /dev/null; then
    powershell -File "$SCRIPT_DIR/../powershell/setup-plan.ps1" "$@"
  else
    # Fallback to bash if PowerShell not available
    bash "$SCRIPT_DIR/../bash/setup-plan.sh" "$@"
  fi
else
  # On Unix/Linux/macOS, use bash
  bash "$SCRIPT_DIR/../bash/setup-plan.sh" "$@"
fi
```

**Option B: Python-based Launcher** (Alternative)

```python
#!/usr/bin/env python3
# .specify/scripts/launchers/setup-plan
import os
import sys
import subprocess
from pathlib import Path

script_dir = Path(__file__).parent
repo_root = script_dir.parent.parent.parent

def get_script_path():
    if os.name == 'nt':  # Windows
        ps_script = script_dir.parent / "powershell" / "setup-plan.ps1"
        if ps_script.exists():
            return ["pwsh", "-File", str(ps_script)]
    # Unix/Linux/macOS
    sh_script = script_dir.parent / "bash" / "setup-plan.sh"
    return ["bash", str(sh_script)]

if __name__ == "__main__":
    cmd = get_script_path() + sys.argv[1:]
    sys.exit(subprocess.call(cmd))
```

**Recommendation**: Use **Option A (Shell-based)** because:

- No Python dependency (keeps package lightweight)
- Works in all environments (including containers)
- Better for AI agent execution contexts
- Simpler debugging

---

## Required Changes

### 1. Build Script Changes

**File**: `.github/workflows/scripts/create-release-packages.sh`

#### Change 1.1: Remove Script Loop (Lines 234-238)

**Current**:

```bash
for agent in "${AGENT_LIST[@]}"; do
  for script in "${SCRIPT_LIST[@]}"; do
    build_variant "$agent" "$script"
  done
done
```

**New**:

```bash
for agent in "${AGENT_LIST[@]}"; do
  build_unified_variant "$agent"
done
```

#### Change 1.2: Create Unified Build Function

**New Function** (replace `build_variant`):

```bash
build_unified_variant() {
  local agent=$1
  local base_dir="$GENRELEASES_DIR/sdd-${agent}-package-unified"
  echo "Building $agent (unified sh+ps) package..."
  mkdir -p "$base_dir"

  # Copy base structure with BOTH script variants
  SPEC_DIR="$base_dir/.specify"
  mkdir -p "$SPEC_DIR"

  [[ -d memory ]] && { cp -r memory "$SPEC_DIR/"; echo "Copied memory"; }

  # Copy BOTH bash and powershell scripts
  if [[ -d scripts ]]; then
    mkdir -p "$SPEC_DIR/scripts"
    [[ -d scripts/bash ]] && {
      cp -r scripts/bash "$SPEC_DIR/scripts/";
      echo "Copied scripts/bash";
    }
    [[ -d scripts/powershell ]] && {
      cp -r scripts/powershell "$SPEC_DIR/scripts/";
      echo "Copied scripts/powershell";
    }
    # Copy any root-level scripts
    find scripts -maxdepth 1 -type f -exec cp {} "$SPEC_DIR/scripts/" \; 2>/dev/null || true
  fi

  # Create launcher scripts
  create_launcher_scripts "$SPEC_DIR/scripts"

  [[ -d templates ]] && {
    mkdir -p "$SPEC_DIR/templates";
    find templates -type f -not -path "templates/commands/*" -not -name "vscode-settings.json" \
      -exec cp --parents {} "$SPEC_DIR"/ \;
    echo "Copied templates";
  }

  # Generate commands with launcher references
  case $agent in
    claude)
      mkdir -p "$base_dir/.claude/commands"
      generate_unified_commands claude md "\$ARGUMENTS" "$base_dir/.claude/commands" ;;
    gemini)
      mkdir -p "$base_dir/.gemini/commands"
      generate_unified_commands gemini toml "{{args}}" "$base_dir/.gemini/commands"
      [[ -f agent_templates/gemini/GEMINI.md ]] && cp agent_templates/gemini/GEMINI.md "$base_dir/GEMINI.md" ;;
    # ... (similar for all agents)
  esac

  ( cd "$base_dir" && zip -r "../spec-kit-template-${agent}-${NEW_VERSION}.zip" . )
  echo "Created $GENRELEASES_DIR/spec-kit-template-${agent}-${NEW_VERSION}.zip"
}
```

#### Change 1.3: Create Launcher Script Generator

**New Function**:

```bash
create_launcher_scripts() {
  local scripts_dir=$1
  local launchers_dir="$scripts_dir/launchers"
  mkdir -p "$launchers_dir"

  # List of scripts to create launchers for
  local script_names=(
    "common"
    "check-prerequisites"
    "create-new-feature"
    "setup-plan"
    "update-agent-context"
  )

  for script_name in "${script_names[@]}"; do
    cat > "$launchers_dir/$script_name" << 'LAUNCHER_EOF'
#!/usr/bin/env bash
# Auto-generated OS-agnostic launcher
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

detect_os() {
  case "$(uname -s)" in
    MINGW*|MSYS*|CYGWIN*|Windows_NT)
      echo "windows" ;;
    Linux*)
      echo "linux" ;;
    Darwin*)
      echo "macos" ;;
    *)
      echo "unknown" ;;
  esac
}

OS_TYPE=$(detect_os)

if [[ "$OS_TYPE" == "windows" ]]; then
  # Windows: prefer PowerShell
  if command -v pwsh &> /dev/null; then
    pwsh -File "$SCRIPT_DIR/../powershell/__SCRIPT_NAME__.ps1" "$@"
  elif command -v powershell &> /dev/null; then
    powershell -File "$SCRIPT_DIR/../powershell/__SCRIPT_NAME__.ps1" "$@"
  else
    bash "$SCRIPT_DIR/../bash/__SCRIPT_NAME__.sh" "$@"
  fi
else
  # Unix/Linux/macOS: use bash
  bash "$SCRIPT_DIR/../bash/__SCRIPT_NAME__.sh" "$@"
fi
LAUNCHER_EOF

    # Substitute script name
    sed -i "s/__SCRIPT_NAME__/$script_name/g" "$launchers_dir/$script_name"
    chmod +x "$launchers_dir/$script_name"
  done

  echo "Created launcher scripts in $launchers_dir"
}
```

#### Change 1.4: Update Command Generation

**New Function** (replace `generate_commands`):

```bash
generate_unified_commands() {
  local agent=$1 ext=$2 arg_format=$3 output_dir=$4
  mkdir -p "$output_dir"

  for template in templates/commands/*.md; do
    [[ -f "$template" ]] || continue
    local name description launcher_command body
    name=$(basename "$template" .md)

    # Normalize line endings
    file_content=$(tr -d '\r' < "$template")

    # Extract description
    description=$(printf '%s\n' "$file_content" | awk '/^description:/ {sub(/^description:[[:space:]]*/, ""); print; exit}')

    # Determine launcher command (platform-agnostic)
    launcher_command="scripts/launchers/${name#speckit.}"

    # For common operations, map to launcher scripts
    case $name in
      plan)
        launcher_command="scripts/launchers/setup-plan" ;;
      specify)
        launcher_command="scripts/launchers/create-new-feature" ;;
      clarify|tasks|implement|analyze|checklist)
        launcher_command="scripts/launchers/check-prerequisites" ;;
    esac

    # Replace {SCRIPT} placeholder with launcher path
    body=$(printf '%s\n' "$file_content" | sed "s|{SCRIPT}|${launcher_command}|g")

    # Handle {AGENT_SCRIPT} placeholder
    body=$(printf '%s\n' "$body" | sed "s|{AGENT_SCRIPT}|scripts/launchers/update-agent-context|g")

    # Remove the scripts: and agent_scripts: sections from YAML frontmatter
    body=$(printf '%s\n' "$body" | awk '
      /^---$/ { print; if (++dash_count == 1) in_frontmatter=1; else in_frontmatter=0; next }
      in_frontmatter && /^scripts:$/ { skip_scripts=1; next }
      in_frontmatter && /^agent_scripts:$/ { skip_scripts=1; next }
      in_frontmatter && /^[a-zA-Z].*:/ && skip_scripts { skip_scripts=0 }
      in_frontmatter && skip_scripts && /^[[:space:]]/ { next }
      { print }
    ')

    # Apply other substitutions
    body=$(printf '%s\n' "$body" | sed "s/{ARGS}/$arg_format/g" | sed "s/__AGENT__/$agent/g" | rewrite_paths)

    # Generate output file
    case $ext in
      toml)
        body=$(printf '%s\n' "$body" | sed 's/\\/\\\\/g')
        { echo "description = \"$description\""; echo; echo "prompt = \"\"\""; echo "$body"; echo "\"\"\""; } \
          > "$output_dir/speckit.$name.$ext" ;;
      md|prompt.md)
        echo "$body" > "$output_dir/speckit.$name.$ext" ;;
    esac
  done
}
```

### 2. Prompt Template Changes

**Files**: `templates/commands/*.md`

#### Change 2.1: Simplify YAML Frontmatter

**Current**:

```yaml
---
description: Execute the implementation planning workflow
scripts:
  sh: scripts/bash/setup-plan.sh --json
  ps: scripts/powershell/setup-plan.ps1 -Json
agent_scripts:
  sh: scripts/bash/update-agent-context.sh __AGENT__
  ps: scripts/powershell/update-agent-context.ps1 -AgentType __AGENT__
---
```

**New** (OPTION 1 - Keep for documentation):

```yaml
---
description: Execute the implementation planning workflow
script: scripts/launchers/setup-plan
agent_script: scripts/launchers/update-agent-context __AGENT__
# Implementation scripts (included in package):
#   Unix/Linux/macOS: .specify/scripts/bash/setup-plan.sh
#   Windows:          .specify/scripts/powershell/setup-plan.ps1
---
```

**New** (OPTION 2 - Minimal, recommended):

```yaml
---
description: Execute the implementation planning workflow
---
```

With build-time substitution handling the script paths.

#### Change 2.2: Update Prompt Instructions

**Current**:

```markdown
1. **Setup**: Run `{SCRIPT}` from repo root and parse JSON for FEATURE_SPEC...
   For single quotes in args like "I'm Groot", use escape syntax:
   e.g 'I'\''m Groot' (or double-quote if possible: "I'm Groot").
```

**New**:

```markdown
1. **Setup**: Run `{SCRIPT}` from repo root and parse JSON for FEATURE_SPEC...

   The launcher script automatically detects your OS:
   - Windows: executes PowerShell (.ps1) scripts
   - Unix/Linux/macOS: executes Bash (.sh) scripts

   For argument escaping:
   - Bash: Use 'I'\''m Groot' for single quotes
   - PowerShell: Use "I'm Groot" (double quotes preferred)
   - Or use: ./script "I'm Groot" (works on both platforms)
```

### 3. CLI Changes

**File**: `src/specify_cli/__init__.py`

#### Change 3.1: Remove Script Type Selection

**Lines to Remove/Modify** (994-1012):

**Current**:

```python
if script_type:
    if script_type not in SCRIPT_TYPE_CHOICES:
        console.print(f"[red]Error:[/red] Invalid script type '{script_type}'...")
        raise typer.Exit(1)
    selected_script = script_type
else:
    default_script = "ps" if os.name == "nt" else "sh"
    if sys.stdin.isatty():
        selected_script = select_with_arrows(SCRIPT_TYPE_CHOICES, "Choose script type...", default_script)
    else:
        selected_script = default_script

console.print(f"[cyan]Selected script type:[/cyan] {selected_script}")
```

**New**:

```python
# Script type no longer needed - unified package contains both
# Keep the parameter for backward compatibility but ignore it
if script_type:
    console.print(f"[yellow]Info:[/yellow] Script type selection is deprecated. "
                  f"Package contains both sh and ps scripts with automatic OS detection.")

# No need to track selected_script - always use unified package
selected_script = "unified"  # For internal tracking only

console.print(f"[cyan]Package type:[/cyan] Unified (auto-detects OS)")
```

#### Change 3.2: Update Download URL Construction

**Current** (approximate line 1047):

```python
download_and_extract_template(
    project_path, selected_ai, selected_script, here,
    verbose=False, tracker=tracker, client=local_client,
    debug=debug, github_token=github_token
)
```

**New**:

```python
# selected_script is now always "unified" or None
download_and_extract_template(
    project_path, selected_ai, None,  # No script variant needed
    here, verbose=False, tracker=tracker,
    client=local_client, debug=debug, github_token=github_token
)
```

#### Change 3.3: Update Package URL Template

**Find the function that constructs GitHub release URLs**:

**Current**:

```python
# Construct: spec-kit-template-{agent}-{script}-{version}.zip
package_name = f"spec-kit-template-{agent}-{script}-{version}.zip"
```

**New**:

```python
# Construct: spec-kit-template-{agent}-{version}.zip
package_name = f"spec-kit-template-{agent}-{version}.zip"
```

### 4. Script Changes (Minimal)

**Files**: `scripts/bash/*.sh` and `scripts/powershell/*.ps1`

**No changes required!** Scripts remain functionally identical. They just get called by launcher scripts now.

**Optional Enhancement**: Add OS detection warning in `common.sh` and `common.ps1`:

**In `scripts/bash/common.sh`**:

```bash
# Detect if running on Windows (when bash is available via WSL/Git Bash)
is_windows() {
  [[ "$(uname -s)" =~ ^(MINGW|MSYS|CYGWIN|Windows_NT) ]]
}

if is_windows; then
  # Running bash on Windows - this might indicate the launcher didn't work
  # Still proceed, but could log a warning
  : # No-op for now
fi
```

**In `scripts/powershell/common.ps1`**:

```powershell
# Detect if running on Unix (via PowerShell Core)
function Test-IsUnix {
    return ($PSVersionTable.Platform -eq 'Unix')
}

if (Test-IsUnix) {
    # Running PowerShell on Unix - this might indicate the launcher chose pwsh deliberately
    # Still proceed normally
}
```

### 5. Documentation Changes

#### Change 5.1: Update README.md

**Current**:

````markdown
```markdown
## Installation

```bash
specify init --agent claude --script sh
```

Choose your AI agent and script type (sh for Unix/Linux/macOS, ps for Windows).
```
````

**New**:

````markdown
```markdown
## Installation

```bash
specify init --agent claude
```

The package automatically detects your operating system:

- **Windows**: Uses PowerShell scripts
- **Unix/Linux/macOS**: Uses Bash scripts

No need to specify script type anymore!
```
````

#### Change 5.2: Update AGENTS.md

Add a section explaining the unified package approach.

#### Change 5.3: Update docs/quickstart.md

Remove references to choosing script types.

---

## Implementation Plan

### Phase 1: Preparation (1-2 hours)

1. ✅ **Create feature branch** ✅ (already done)
1. **Create launcher script template** in `scripts/launchers/`
1. **Write launcher tests** to verify OS detection
1. **Update build script** with `create_launcher_scripts()` function

### Phase 2: Build System (2-3 hours)

1. **Modify `create-release-packages.sh`**:
   - Add `build_unified_variant()` function
   - Add `generate_unified_commands()` function
   - Add `create_launcher_scripts()` function
   - Update main loop to build unified packages

1. **Test locally**:

   ```bash
   AGENTS=claude .github/workflows/scripts/create-release-packages.sh v0.99.99
   ```

- Verify launcher scripts are created
- Verify both bash/ and powershell/ directories are included
- Verify package size (~2x larger)

1. **Update GitHub Actions workflow** (minimal changes):

- Workflow should work as-is (no SCRIPTS env var needed)

### Phase 3: CLI Updates (1-2 hours)

1. **Modify `src/specify_cli/__init__.py`**:
   - Deprecate `--script` parameter (keep for backward compat)
   - Update package name construction
   - Update download logic
   - Update user messages

1. **Test CLI**:

   ```bash
   specify init --agent claude --here
   ls .specify/scripts/  # Should see bash/, powershell/, launchers/
   .specify/scripts/launchers/check-prerequisites --json
   ```

### Phase 4: Prompt Updates (1 hour)

1. **Update all templates in `templates/commands/`**:
   - Simplify YAML frontmatter
   - Update instructions to mention OS detection
   - Remove platform-specific escape examples (or make them conditional)

2. **Verify template processing**:
   - Check generated `.claude/commands/*.md` files
   - Verify {SCRIPT} placeholder points to launchers

### Phase 5: Documentation (1 hour)

1. **Update documentation files**:
   - README.md
   - AGENTS.md
   - docs/quickstart.md
   - Add migration guide for existing users

### Phase 6: Testing & Validation (2-3 hours)

1. **Test on Linux**:
   - Initialize project
   - Run all commands
   - Verify bash scripts are executed

1. **Test on Windows**:
   - Initialize project
   - Run all commands
   - Verify PowerShell scripts are executed

1. **Test on macOS** (if available):
   - Same verification

1. **Test edge cases**:
   - Windows with only Git Bash (no PowerShell)
   - Unix with PowerShell Core installed
   - Verify fallback logic works

1. **Test backward compatibility**:
   - Old package URLs should return 404 (expected)
   - CLI should show helpful error

### Phase 7: Release (30 minutes)

1. **Create pull request** with all changes
1. **Merge to main** (triggers release workflow)
1. **Verify release**:
   - Check GitHub releases for new unified packages
   - Download and test on multiple platforms

**Total Estimated Time**: 10-14 hours

---

## Benefits

### For Users

1. **Simpler Installation**: No need to think about script types
2. **Cross-Platform Portability**: Same package works everywhere
3. **Reduced Confusion**: One package per agent, not two
4. **Better DX**: AI agents don't need to worry about OS
5. **Future-Proof**: Works in containers, VMs, WSL, native Windows, macOS

### For Maintainers

1. **Fewer Build Artifacts**: 16 packages instead of 32
2. **Simpler CI/CD**: No script type matrix
3. **Easier Testing**: Test one package on multiple platforms
4. **Reduced Support Burden**: Fewer "which package should I use?" questions
5. **Better Architecture**: Clear separation of concerns (launchers vs implementations)

### Technical Benefits

1. **Runtime Flexibility**: Can add more script types (e.g., Python) without rebuild
2. **Graceful Degradation**: Falls back to bash if PowerShell unavailable on Windows
3. **Container-Friendly**: Works in minimal containers with just bash
4. **Cloud-Native**: Works in cloud VMs (Linux, Windows Server)
5. **Developer-Friendly**: Works in WSL, Git Bash, PowerShell, Terminal, etc.

---

## Trade-offs & Considerations

### Increased Package Size

- **Current**: ~100KB per package (estimated)
- **Unified**: ~200KB per package (both script sets)
- **Mitigation**: Still very small. 200KB is negligible for modern networks.

### Launcher Overhead

- **Overhead**: ~50ms for OS detection and delegation
- **Impact**: Negligible. Scripts typically run for seconds.
- **Mitigation**: Launcher is extremely simple (no complex logic)

### Backward Compatibility

- **Issue**: Existing installations expect `-sh` or `-ps` suffixed packages
- **Impact**: New users unaffected. Existing users must update.
- **Mitigation**:
  1. Document migration path
  2. Consider keeping old packages for one more release
  3. CLI can detect old packages and show upgrade message

### Complexity

- **Added Complexity**: Launcher scripts (new concept)
- **Reduced Complexity**: No script type selection in CLI
- **Net Impact**: Overall simplification for end users

---

## Migration Strategy

### For New Users

**Zero migration needed** - they get the smart unified package by default.

### For Existing Users

#### Option 1: Soft Migration (Recommended)

1. Keep building old packages for one more release (v0.3.0)
2. Add deprecation warning to old package downloads
3. CLI automatically switches to unified packages in v0.4.0

#### Option 2: Hard Migration

1. Stop building old packages immediately
2. Update CLI to reject `--script` parameter
3. Show clear error message with migration instructions

**Recommended Approach**: Option 1 (soft migration)

```bash
# Old command (still works in v0.3.0)
specify init --agent claude --script sh
# Warning: The --script parameter is deprecated. Unified packages auto-detect OS.

# New command (v0.3.0+)
specify init --agent claude
# No script type needed!
```

---

## Testing Checklist

### Build Testing

- [ ] Build succeeds for all 16 agents
- [ ] Each package contains `bash/`, `powershell/`, and `launchers/` directories
- [ ] Launcher scripts are executable
- [ ] Package naming is correct: `spec-kit-template-{agent}-{version}.zip`
- [ ] Package size is reasonable (under 500KB)

### Runtime Testing (Linux)

- [ ] Launcher detects Linux correctly
- [ ] Bash scripts are executed
- [ ] All commands work: specify, plan, clarify, tasks, implement, analyze, checklist
- [ ] JSON output is correct
- [ ] Error handling works

### Runtime Testing (Windows)

- [ ] Launcher detects Windows correctly
- [ ] PowerShell scripts are executed (if available)
- [ ] Falls back to bash if PowerShell unavailable
- [ ] All commands work with PowerShell
- [ ] JSON output is correct

### Runtime Testing (macOS)

- [ ] Launcher detects macOS correctly
- [ ] Bash scripts are executed
- [ ] All commands work

### Edge Cases

- [ ] WSL (Windows Subsystem for Linux) - should use bash
- [ ] Git Bash on Windows - should fall back to bash if PowerShell unavailable
- [ ] PowerShell Core on Linux - launcher should still prefer bash
- [ ] MSYS2/Cygwin - should detect as Windows and try PowerShell first

### CLI Testing

- [ ] `specify init --agent claude` works
- [ ] Old `--script` parameter shows deprecation warning
- [ ] Package download works from GitHub releases
- [ ] Extraction works correctly
- [ ] File permissions are preserved

### Integration Testing

- [ ] Full workflow: init → specify → plan → tasks → implement
- [ ] Agent context updates work
- [ ] Git integration works
- [ ] Multi-feature workflow works

---

## Risk Assessment

### Low Risk

- ✅ Script functional parity already exists
- ✅ OS detection is standard practice
- ✅ Build system is well-architected
- ✅ No runtime dependencies added

### Medium Risk

- ⚠️ Launcher script compatibility across all platforms
- ⚠️ PowerShell availability on Windows (most modern Windows has it)
- ⚠️ Bash availability on Windows (Git Bash provides fallback)

### Mitigation Strategies

1. **Extensive Testing**: Test on all major platforms before release
1. **Fallback Logic**: Launcher tries PowerShell, then falls back to bash
1. **Clear Documentation**: Explain requirements and troubleshooting
1. **Gradual Rollout**: Soft migration keeps old packages available

---

## Recommendation

**PROCEED WITH IMPLEMENTATION** ✅

This change:

1. Is highly feasible with the current architecture
1. Provides significant user experience improvements
1. Reduces maintenance burden
1. Makes the system truly cross-platform
1. Has acceptable risk profile with proper testing

**Suggested Timeline**:

- **Development**: 2-3 days
- **Testing**: 1 day
- **Soft Migration Period**: 2-4 weeks
- **Full Cutover**: After v0.3.0 release

---

## Next Steps

1. **Review this document** with stakeholders
1. **Approve approach** (launcher strategy, migration plan)
1. **Begin Phase 1** (create launcher template)
1. **Iterate through phases** with testing after each
1. **Create PR** with all changes
1. **Merge and release**

## Questions to Resolve

1. **Keep backward compatibility?** Recommend: Yes, for 1 release cycle
1. **Launcher language?** Recommend: Shell script (no dependencies)
1. **Documentation location?** Recommend: Add MIGRATION.md
1. **Testing strategy?** Recommend: Automated tests + manual validation
1. **Release timing?** Recommend: Next minor version (v0.3.0)

---

## Appendix: Alternative Approaches Considered

### Alternative 1: Python-based Launcher

**Pros**: Cross-platform, easy to maintain

**Cons**: Adds Python as runtime dependency

**Verdict**: ❌ Rejected - increases dependencies

### Alternative 2: Platform-Specific Packages with Shared Code

**Pros**: Smaller package size

**Cons**: Still requires two packages per agent

**Verdict**: ❌ Rejected - doesn't solve the core problem

### Alternative 3: Polyglot Scripts (Python/Bash/PowerShell hybrid)

**Pros**: Single script file

**Cons**: Complex, hard to maintain, poor readability

**Verdict**: ❌ Rejected - too complex

### Alternative 4: Client-Side OS Detection (CLI does everything)

**Pros**: No launcher scripts needed

**Cons**: Doesn't work when AI agents call scripts directly

**Verdict**: ❌ Rejected - breaks AI agent usage

### Alternative 5: Unified Package with Shell-based Launchers ✅

**Pros**: No dependencies, simple, works everywhere

**Cons**: Slightly larger packages, adds launcher layer

**Verdict**: ✅ **SELECTED** - best balance of simplicity and functionality

---

## Conclusion

The unified package approach is **highly feasible** and provides significant value. The system is already well-architected for this change, requiring primarily:

1. Build script modifications to include both script types
2. Simple launcher scripts for OS detection
3. Minor CLI updates to remove script type selection
4. Documentation updates

The benefits far outweigh the minimal complexity added by launcher scripts. This change will make Spec Kit Smart truly smart and cross-platform compatible.

**Recommendation: Proceed with implementation following the phased plan above.**
