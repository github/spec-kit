#!/usr/bin/env bash
# Configure git worktree preferences for Spec Kit

set -e

# Get script directory and source common functions
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Parse arguments
MODE=""
STRATEGY=""
CUSTOM_PATH=""
SHOW_CONFIG=false

show_help() {
    cat << 'EOF'
Usage: configure-worktree.sh [OPTIONS]

Configure git worktree preferences for Spec Kit feature creation.

Options:
  --mode <branch|worktree>        Set git mode (default: branch)
  --strategy <nested|sibling|custom>  Set worktree placement strategy
  --path <path>                   Custom base path (required if strategy is 'custom')
  --show                          Display current configuration
  --help, -h                      Show this help message

Strategies:
  nested   - Worktrees in .worktrees/ directory inside the repository
  sibling  - Worktrees as sibling directories to the repository
  custom   - Worktrees in a custom directory (requires --path)

Examples:
  # Enable worktree mode with nested strategy
  configure-worktree.sh --mode worktree --strategy nested

  # Enable worktree mode with sibling strategy
  configure-worktree.sh --mode worktree --strategy sibling

  # Enable worktree mode with custom path
  configure-worktree.sh --mode worktree --strategy custom --path /tmp/worktrees

  # Switch back to branch mode
  configure-worktree.sh --mode branch

  # Show current configuration
  configure-worktree.sh --show
EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --mode)
            if [[ -z "$2" || "$2" == --* ]]; then
                echo "Error: --mode requires a value (branch or worktree)" >&2
                exit 1
            fi
            MODE="$2"
            shift 2
            ;;
        --strategy)
            if [[ -z "$2" || "$2" == --* ]]; then
                echo "Error: --strategy requires a value (nested, sibling, or custom)" >&2
                exit 1
            fi
            STRATEGY="$2"
            shift 2
            ;;
        --path)
            if [[ -z "$2" || "$2" == --* ]]; then
                echo "Error: --path requires a value" >&2
                exit 1
            fi
            CUSTOM_PATH="$2"
            shift 2
            ;;
        --show)
            SHOW_CONFIG=true
            shift
            ;;
        --help|-h)
            show_help
            exit 0
            ;;
        *)
            echo "Error: Unknown option: $1" >&2
            echo "Use --help for usage information" >&2
            exit 1
            ;;
    esac
done

# Get repository root
REPO_ROOT=$(get_repo_root)
CONFIG_FILE="$REPO_ROOT/.specify/config.json"

# Show current configuration
if $SHOW_CONFIG; then
    if [[ ! -f "$CONFIG_FILE" ]]; then
        echo "No configuration file found. Using defaults:"
        echo "  git_mode: branch"
        echo "  worktree_strategy: sibling"
        echo "  worktree_custom_path: (none)"
    else
        echo "Current configuration ($CONFIG_FILE):"
        echo "  git_mode: $(read_config_value "git_mode" "branch")"
        echo "  worktree_strategy: $(read_config_value "worktree_strategy" "sibling")"
        echo "  worktree_custom_path: $(read_config_value "worktree_custom_path" "(none)")"
    fi
    exit 0
fi

# If no options provided, show help
if [[ -z "$MODE" && -z "$STRATEGY" && -z "$CUSTOM_PATH" ]]; then
    show_help
    exit 0
fi

# Validate mode
if [[ -n "$MODE" ]]; then
    if [[ "$MODE" != "branch" && "$MODE" != "worktree" ]]; then
        echo "Error: Invalid mode '$MODE'. Must be 'branch' or 'worktree'" >&2
        exit 1
    fi
fi

# Validate strategy
if [[ -n "$STRATEGY" ]]; then
    if [[ "$STRATEGY" != "nested" && "$STRATEGY" != "sibling" && "$STRATEGY" != "custom" ]]; then
        echo "Error: Invalid strategy '$STRATEGY'. Must be 'nested', 'sibling', or 'custom'" >&2
        exit 1
    fi
fi

# Validate custom path requirements
if [[ "$STRATEGY" == "custom" && -z "$CUSTOM_PATH" ]]; then
    echo "Error: --path is required when strategy is 'custom'" >&2
    exit 1
fi

# Validate custom path is absolute
if [[ -n "$CUSTOM_PATH" ]]; then
    if [[ "$CUSTOM_PATH" != /* ]]; then
        echo "Error: --path must be an absolute path (got: $CUSTOM_PATH)" >&2
        exit 1
    fi
    # Check if path is writable (create parent if needed)
    CUSTOM_PARENT=$(dirname "$CUSTOM_PATH")
    if [[ ! -d "$CUSTOM_PARENT" ]]; then
        echo "Error: Parent directory does not exist: $CUSTOM_PARENT" >&2
        exit 1
    fi
    if [[ ! -w "$CUSTOM_PARENT" ]]; then
        echo "Error: Parent directory is not writable: $CUSTOM_PARENT" >&2
        exit 1
    fi
fi

# Ensure .specify directory exists
mkdir -p "$REPO_ROOT/.specify"

# Read existing config or create empty object
if [[ -f "$CONFIG_FILE" ]]; then
    if command -v jq &>/dev/null; then
        EXISTING_CONFIG=$(cat "$CONFIG_FILE")
    else
        # Without jq, we'll reconstruct the file
        EXISTING_CONFIG="{}"
    fi
else
    EXISTING_CONFIG="{}"
fi

# Update configuration using jq if available
if command -v jq &>/dev/null; then
    # Build jq update using --arg to prevent injection via user input
    JQ_ARGS=()
    UPDATE_EXPR="."

    if [[ -n "$MODE" ]]; then
        JQ_ARGS+=(--arg mode "$MODE")
        UPDATE_EXPR="$UPDATE_EXPR | .git_mode = \$mode"
    fi

    if [[ -n "$STRATEGY" ]]; then
        JQ_ARGS+=(--arg strategy "$STRATEGY")
        UPDATE_EXPR="$UPDATE_EXPR | .worktree_strategy = \$strategy"
    fi

    if [[ -n "$CUSTOM_PATH" ]]; then
        JQ_ARGS+=(--arg cpath "$CUSTOM_PATH")
        UPDATE_EXPR="$UPDATE_EXPR | .worktree_custom_path = \$cpath"
    elif [[ "$STRATEGY" == "nested" || "$STRATEGY" == "sibling" ]]; then
        # Clear custom path when switching to non-custom strategy
        UPDATE_EXPR="$UPDATE_EXPR | .worktree_custom_path = \"\""
    fi

    echo "$EXISTING_CONFIG" | jq "${JQ_ARGS[@]}" "$UPDATE_EXPR" > "$CONFIG_FILE"
else
    # Fallback without jq: construct JSON manually
    # Warn user about potential data loss
    if [[ -f "$CONFIG_FILE" ]]; then
        >&2 echo "[specify] Warning: jq not found. Config file will be rewritten with only worktree settings."
        >&2 echo "[specify] Install jq to preserve other configuration keys."
    fi

    # Read existing values
    CURRENT_MODE=$(read_config_value "git_mode" "branch")
    CURRENT_STRATEGY=$(read_config_value "worktree_strategy" "sibling")
    CURRENT_PATH=$(read_config_value "worktree_custom_path" "")

    # Apply updates
    [[ -n "$MODE" ]] && CURRENT_MODE="$MODE"
    [[ -n "$STRATEGY" ]] && CURRENT_STRATEGY="$STRATEGY"
    if [[ -n "$CUSTOM_PATH" ]]; then
        CURRENT_PATH="$CUSTOM_PATH"
    elif [[ "$STRATEGY" == "nested" || "$STRATEGY" == "sibling" ]]; then
        CURRENT_PATH=""
    fi

    # Escape backslashes and double quotes for JSON safety
    CURRENT_PATH="${CURRENT_PATH//\\/\\\\}"
    CURRENT_PATH="${CURRENT_PATH//\"/\\\"}"

    # Write JSON manually
    printf '{\n  "git_mode": "%s",\n  "worktree_strategy": "%s",\n  "worktree_custom_path": "%s"\n}\n' \
        "$CURRENT_MODE" "$CURRENT_STRATEGY" "$CURRENT_PATH" > "$CONFIG_FILE"
fi

echo "Configuration updated:"
echo "  git_mode: $(read_config_value "git_mode" "branch")"
echo "  worktree_strategy: $(read_config_value "worktree_strategy" "sibling")"
custom_path=$(read_config_value "worktree_custom_path" "")
if [[ -n "$custom_path" ]]; then
    echo "  worktree_custom_path: $custom_path"
fi
