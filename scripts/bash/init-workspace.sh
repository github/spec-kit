#!/usr/bin/env bash
# Initialize a multi-repo workspace for spec-kit
set -e

# Source common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

WORKSPACE_DIR="${1:-.}"
FORCE=false
AUTO_INIT_REPOS=false

# Parse arguments
for arg in "$@"; do
    case "$arg" in
        --force|-f)
            FORCE=true
            ;;
        --auto-init)
            AUTO_INIT_REPOS=true
            ;;
        --help|-h)
            echo "Usage: $0 [workspace-directory] [--force] [--auto-init]"
            echo ""
            echo "Initialize a multi-repo workspace for spec-kit"
            echo ""
            echo "Arguments:"
            echo "  workspace-directory   Directory containing multiple git repos (default: current dir)"
            echo ""
            echo "Options:"
            echo "  --force              Overwrite existing workspace config"
            echo "  --auto-init          Automatically initialize .specify/ in discovered repos"
            echo ""
            echo "This script will:"
            echo "  1. Discover all git repositories in the workspace"
            echo "  2. Create .spec-kit/workspace.yml with auto-detected configuration"
            echo "  3. Create workspace-level specs/ directory"
            echo "  4. Optionally initialize .specify/ in each repo (with --auto-init)"
            echo ""
            echo "Example:"
            echo "  $0 ~/git/attun-project --auto-init"
            exit 0
            ;;
    esac
done

# Convert to absolute path
WORKSPACE_DIR=$(cd "$WORKSPACE_DIR" && pwd)

echo "Initializing workspace at: $WORKSPACE_DIR"
echo ""

# Check if already a workspace
if [[ -f "$WORKSPACE_DIR/.spec-kit/workspace.yml" ]] && ! $FORCE; then
    echo "ERROR: Workspace already initialized at $WORKSPACE_DIR"
    echo "Use --force to reinitialize"
    exit 1
fi

# Discover git repositories
echo "Discovering git repositories..."
REPOS=($(find_repos "$WORKSPACE_DIR" 2))

if [[ ${#REPOS[@]} -eq 0 ]]; then
    echo "ERROR: No git repositories found in $WORKSPACE_DIR"
    echo ""
    echo "Make sure the workspace directory contains at least one git repository."
    exit 1
fi

echo "Found ${#REPOS[@]} repositories:"
for repo in "${REPOS[@]}"; do
    echo "  - $(basename "$repo")"
done
echo ""

# Build workspace configuration
echo "Building workspace configuration..."
CONFIG_FILE=$(build_workspace_config "$WORKSPACE_DIR")

if [[ ! -f "$CONFIG_FILE" ]]; then
    echo "ERROR: Failed to create workspace configuration"
    exit 1
fi

echo "✓ Created $CONFIG_FILE"
echo ""

# Create workspace specs directory
SPECS_DIR="$WORKSPACE_DIR/specs"
mkdir -p "$SPECS_DIR"
echo "✓ Created workspace specs directory: $SPECS_DIR"
echo ""

# Display generated configuration
echo "Generated workspace configuration:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
cat "$CONFIG_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Prompt to customize conventions
echo "You can customize the convention rules in $CONFIG_FILE"
echo "to match your repository naming patterns."
echo ""

# Auto-init repos if requested
if $AUTO_INIT_REPOS; then
    echo "Initializing .specify/ in discovered repositories..."
    for repo in "${REPOS[@]}"; do
        repo_name=$(basename "$repo")

        if [[ -d "$repo/.specify" ]]; then
            echo "  ⊙ $repo_name (already initialized)"
        else
            echo "  → Initializing $repo_name..."

            # Check if init.sh is available
            INIT_SCRIPT="$SCRIPT_DIR/init.sh"
            if [[ -f "$INIT_SCRIPT" ]]; then
                # Run init.sh in the repo
                (cd "$repo" && bash "$INIT_SCRIPT" --here) > /dev/null 2>&1 || {
                    echo "    ⚠ Failed to initialize $repo_name"
                    continue
                }
                echo "    ✓ $repo_name initialized"
            else
                echo "    ⚠ init.sh not found, skipping $repo_name"
            fi
        fi
    done
    echo ""
fi

# Add .spec-kit to .gitignore if workspace is a git repo
if [[ -d "$WORKSPACE_DIR/.git" ]]; then
    GITIGNORE="$WORKSPACE_DIR/.gitignore"
    if ! grep -q "^\.spec-kit/$" "$GITIGNORE" 2>/dev/null; then
        echo "" >> "$GITIGNORE"
        echo "# spec-kit workspace configuration" >> "$GITIGNORE"
        echo ".spec-kit/" >> "$GITIGNORE"
        echo "✓ Added .spec-kit/ to .gitignore"
    fi
fi

# Create README in specs directory
SPECS_README="$SPECS_DIR/README.md"
if [[ ! -f "$SPECS_README" ]]; then
    cat > "$SPECS_README" <<'EOF'
# Workspace Specifications

This directory contains feature specifications that target one or more repositories in this workspace.

## Convention-Based Targeting

Specs are automatically routed to target repositories based on naming conventions:

- `backend-*` → Backend repository
- `frontend-*` → Frontend repository
- `fullstack-*` → All repositories
- `*-api` → API/backend repository
- `*-ui` → UI/frontend repository

See `.spec-kit/workspace.yml` for full convention configuration.

## Creating a New Spec

From anywhere in the workspace:

```bash
# Convention-based (auto-detects target repo from spec name)
/specify backend-user-auth

# Explicit target repo
/specify --repo=attun-backend user-auth

# Multi-repo feature
/specify fullstack-dashboard
```

## Capabilities

Capabilities are single-repository implementations. When creating a capability
for a multi-repo parent spec, you'll be prompted to select the target repository:

```bash
/plan --capability cap-001
```

## Workspace Structure

```
workspace-root/
  .spec-kit/
    workspace.yml          # Workspace configuration
  specs/                   # Centralized specifications
    feature-id/
      spec.md
      plan.md
      cap-001-name/        # Single-repo capability
        spec.md
        plan.md
  repo-1/                  # Git repository
  repo-2/                  # Git repository
```
EOF
    echo "✓ Created $SPECS_README"
    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Workspace initialization complete!"
echo ""
echo "Workspace: $WORKSPACE_DIR"
echo "Repositories: ${#REPOS[@]}"
echo "Configuration: $CONFIG_FILE"
echo "Specs directory: $SPECS_DIR"
echo ""
echo "Next steps:"
echo "  1. Review and customize $CONFIG_FILE"
echo "  2. Create your first spec: /specify <feature-name>"
echo "  3. Specs will be routed to repos based on naming conventions"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
