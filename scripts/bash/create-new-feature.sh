#!/usr/bin/env bash

set -e

JSON_MODE=false
SHORT_NAME=""
BRANCH_NUMBER=""
ARGS=()
i=1
while [ $i -le $# ]; do
    arg="${!i}"
    case "$arg" in
        --json) 
            JSON_MODE=true 
            ;;
        --short-name)
            if [ $((i + 1)) -gt $# ]; then
                echo 'Error: --short-name requires a value' >&2
                exit 1
            fi
            i=$((i + 1))
            next_arg="${!i}"
            # Check if the next argument is another option (starts with --)
            if [[ "$next_arg" == --* ]]; then
                echo 'Error: --short-name requires a value' >&2
                exit 1
            fi
            SHORT_NAME="$next_arg"
            ;;
        --number)
            if [ $((i + 1)) -gt $# ]; then
                echo 'Error: --number requires a value' >&2
                exit 1
            fi
            i=$((i + 1))
            next_arg="${!i}"
            if [[ "$next_arg" == --* ]]; then
                echo 'Error: --number requires a value' >&2
                exit 1
            fi
            BRANCH_NUMBER="$next_arg"
            ;;
        --help|-h) 
            echo "Usage: $0 [--json] [--short-name <name>] [--number N] <feature_description>"
            echo ""
            echo "Options:"
            echo "  --json              Output in JSON format"
            echo "  --short-name <name> Provide a custom short name (2-4 words) for the branch"
            echo "  --number N          Specify branch number manually (overrides auto-detection)"
            echo "  --help, -h          Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 'Add user authentication system' --short-name 'user-auth'"
            echo "  $0 'Implement OAuth2 integration for API' --number 5"
            exit 0
            ;;
        *) 
            ARGS+=("$arg") 
            ;;
    esac
    i=$((i + 1))
done

FEATURE_DESCRIPTION="${ARGS[*]}"
if [ -z "$FEATURE_DESCRIPTION" ]; then
    echo "Usage: $0 [--json] [--short-name <name>] [--number N] <feature_description>" >&2
    exit 1
fi

# Function to find the repository root by searching for existing project markers
find_repo_root() {
    local dir="$1"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.git" ] || [ -d "$dir/.specify" ]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    return 1
}

# Function to get highest number from specs directory
get_highest_from_specs() {
    local specs_dir="$1"
    local highest=0
    
    if [ -d "$specs_dir" ]; then
        for dir in "$specs_dir"/*; do
            [ -d "$dir" ] || continue
            dirname=$(basename "$dir")
            number=$(echo "$dirname" | grep -o '^[0-9]\+' || echo "0")
            number=$((10#$number))
            if [ "$number" -gt "$highest" ]; then
                highest=$number
            fi
        done
    fi
    
    echo "$highest"
}

# Function to get highest number from git branches
get_highest_from_branches() {
    local highest=0
    
    # Get all branches (local and remote)
    branches=$(git branch -a 2>/dev/null || echo "")
    
    if [ -n "$branches" ]; then
        while IFS= read -r branch; do
            # Clean branch name: remove leading markers and remote prefixes
            clean_branch=$(echo "$branch" | sed 's/^[* ]*//; s|^remotes/[^/]*/||')
            
            # Extract feature number if branch matches pattern ###-*
            if echo "$clean_branch" | grep -q '^[0-9]\{3\}-'; then
                number=$(echo "$clean_branch" | grep -o '^[0-9]\{3\}' || echo "0")
                number=$((10#$number))
                if [ "$number" -gt "$highest" ]; then
                    highest=$number
                fi
            fi
        done <<< "$branches"
    fi
    
    echo "$highest"
}

# Function to check existing branches (local and remote) and return next available number
check_existing_branches() {
    local specs_dir="$1"

    # Fetch all remotes to get latest branch info (suppress errors if no remotes)
    git fetch --all --prune 2>/dev/null || true

    # Get highest number from ALL branches (not just matching short name)
    local highest_branch=$(get_highest_from_branches)

    # Get highest number from ALL specs (not just matching short name)
    local highest_spec=$(get_highest_from_specs "$specs_dir")

    # Take the maximum of both
    local max_num=$highest_branch
    if [ "$highest_spec" -gt "$max_num" ]; then
        max_num=$highest_spec
    fi

    # Return next number
    echo $((max_num + 1))
}

# Function to clean and format a branch name
clean_branch_name() {
    local name="$1"
    echo "$name" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-//' | sed 's/-$//'
}

# Resolve repository root. Prefer git information when available, but fall back
# to searching for repository markers so the workflow still functions in repositories that
# were initialised with --no-git.
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if we're in any Git repository (works for both bare and non-bare repos)
if git rev-parse --git-dir >/dev/null 2>&1; then
    HAS_GIT=true
    # Check if this is a bare repository
    if [ "$(git rev-parse --is-bare-repository 2>/dev/null)" = "true" ]; then
        # Bare repository - use git-dir as root
        REPO_ROOT=$(git rev-parse --git-dir)
        REPO_ROOT=$(cd "$REPO_ROOT" && pwd)  # Resolve to absolute path
    else
        # Non-bare repository - use show-toplevel
        REPO_ROOT=$(git rev-parse --show-toplevel)
    fi
else
    # Not a Git repository - fall back to marker search
    REPO_ROOT="$(find_repo_root "$SCRIPT_DIR")"
    if [ -z "$REPO_ROOT" ]; then
        echo "Error: Could not determine repository root. Please run this script from within the repository." >&2
        exit 1
    fi
    HAS_GIT=false
fi

cd "$REPO_ROOT"

# Save original directory for error recovery
ORIGINAL_DIR="$PWD"

SPECS_DIR="$REPO_ROOT/specs"
mkdir -p "$SPECS_DIR"

# Feature 001: Read source management mode from config
CONFIG_FILE="$REPO_ROOT/.specify/memory/config.json"
SOURCE_MODE="branch"  # Default to branch mode for backward compatibility
WORKTREE_FOLDER=""

if [ -f "$CONFIG_FILE" ]; then
    # Parse JSON config using grep/sed (no jq dependency needed)
    SOURCE_MODE=$(grep -o '"source_management_flow"[[:space:]]*:[[:space:]]*"[^"]*"' "$CONFIG_FILE" | sed 's/.*"\([^"]*\)".*/\1/' || echo "branch")
    WORKTREE_FOLDER=$(grep -o '"worktree_folder"[[:space:]]*:[[:space:]]*"[^"]*"' "$CONFIG_FILE" | sed 's/.*"\([^"]*\)".*/\1/' || echo "")
fi

# Fallback to branch mode if config is invalid
if [ -z "$SOURCE_MODE" ]; then
    SOURCE_MODE="branch"
fi

# Function to generate branch name with stop word filtering and length filtering
generate_branch_name() {
    local description="$1"
    
    # Common stop words to filter out
    local stop_words="^(i|a|an|the|to|for|of|in|on|at|by|with|from|is|are|was|were|be|been|being|have|has|had|do|does|did|will|would|should|could|can|may|might|must|shall|this|that|these|those|my|your|our|their|want|need|add|get|set)$"
    
    # Convert to lowercase and split into words
    local clean_name=$(echo "$description" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/ /g')
    
    # Filter words: remove stop words and words shorter than 3 chars (unless they're uppercase acronyms in original)
    local meaningful_words=()
    for word in $clean_name; do
        # Skip empty words
        [ -z "$word" ] && continue
        
        # Keep words that are NOT stop words AND (length >= 3 OR are potential acronyms)
        if ! echo "$word" | grep -qiE "$stop_words"; then
            if [ ${#word} -ge 3 ]; then
                meaningful_words+=("$word")
            elif echo "$description" | grep -q "\b${word^^}\b"; then
                # Keep short words if they appear as uppercase in original (likely acronyms)
                meaningful_words+=("$word")
            fi
        fi
    done
    
    # If we have meaningful words, use first 3-4 of them
    if [ ${#meaningful_words[@]} -gt 0 ]; then
        local max_words=3
        if [ ${#meaningful_words[@]} -eq 4 ]; then max_words=4; fi
        
        local result=""
        local count=0
        for word in "${meaningful_words[@]}"; do
            if [ $count -ge $max_words ]; then break; fi
            if [ -n "$result" ]; then result="$result-"; fi
            result="$result$word"
            count=$((count + 1))
        done
        echo "$result"
    else
        # Fallback to original logic if no meaningful words found
        local cleaned=$(clean_branch_name "$description")
        echo "$cleaned" | tr '-' '\n' | grep -v '^$' | head -3 | tr '\n' '-' | sed 's/-$//'
    fi
}

# Generate branch name
if [ -n "$SHORT_NAME" ]; then
    # Use provided short name, just clean it up
    BRANCH_SUFFIX=$(clean_branch_name "$SHORT_NAME")
else
    # Generate from description with smart filtering
    BRANCH_SUFFIX=$(generate_branch_name "$FEATURE_DESCRIPTION")
fi

# Determine branch number
if [ -z "$BRANCH_NUMBER" ]; then
    if [ "$HAS_GIT" = true ]; then
        # Check existing branches on remotes
        BRANCH_NUMBER=$(check_existing_branches "$SPECS_DIR")
    else
        # Fall back to local directory check
        HIGHEST=$(get_highest_from_specs "$SPECS_DIR")
        BRANCH_NUMBER=$((HIGHEST + 1))
    fi
fi

# Force base-10 interpretation to prevent octal conversion (e.g., 010 → 8 in octal, but should be 10 in decimal)
FEATURE_NUM=$(printf "%03d" "$((10#$BRANCH_NUMBER))")
BRANCH_NAME="${FEATURE_NUM}-${BRANCH_SUFFIX}"

# GitHub enforces a 244-byte limit on branch names
# Validate and truncate if necessary
MAX_BRANCH_LENGTH=244
if [ ${#BRANCH_NAME} -gt $MAX_BRANCH_LENGTH ]; then
    # Calculate how much we need to trim from suffix
    # Account for: feature number (3) + hyphen (1) = 4 chars
    MAX_SUFFIX_LENGTH=$((MAX_BRANCH_LENGTH - 4))
    
    # Truncate suffix at word boundary if possible
    TRUNCATED_SUFFIX=$(echo "$BRANCH_SUFFIX" | cut -c1-$MAX_SUFFIX_LENGTH)
    # Remove trailing hyphen if truncation created one
    TRUNCATED_SUFFIX=$(echo "$TRUNCATED_SUFFIX" | sed 's/-$//')
    
    ORIGINAL_BRANCH_NAME="$BRANCH_NAME"
    BRANCH_NAME="${FEATURE_NUM}-${TRUNCATED_SUFFIX}"
    
    >&2 echo "[specify] Warning: Branch name exceeded GitHub's 244-byte limit"
    >&2 echo "[specify] Original: $ORIGINAL_BRANCH_NAME (${#ORIGINAL_BRANCH_NAME} bytes)"
    >&2 echo "[specify] Truncated to: $BRANCH_NAME (${#BRANCH_NAME} bytes)"
fi

if [ "$HAS_GIT" = true ]; then
    # Feature 001: Create worktree or branch based on mode
    if [ "$SOURCE_MODE" = "worktree" ]; then
        # Worktree mode: create worktree instead of branch
        if [ -z "$WORKTREE_FOLDER" ]; then
            WORKTREE_FOLDER="./worktrees"
        fi

        # Resolve to absolute path
        if [[ "$WORKTREE_FOLDER" != /* ]]; then
            WORKTREE_FOLDER="$REPO_ROOT/$WORKTREE_FOLDER"
        fi

        # Check if worktree folder exists (FR-015)
        if [ ! -d "$WORKTREE_FOLDER" ]; then
            >&2 echo "[specify] The configured worktree folder does not exist: $WORKTREE_FOLDER"
            read -p "Create this directory? (y/N): " -n 1 -r CREATE_FOLDER
            echo
            if [[ $CREATE_FOLDER =~ ^[Yy]$ ]]; then
                mkdir -p "$WORKTREE_FOLDER" || {
                    >&2 echo "[specify] Error: Failed to create worktree folder (permission denied or invalid path)"
                    exit 1
                }
                >&2 echo "[specify] Created worktree folder: $WORKTREE_FOLDER"
            else
                >&2 echo "[specify] Error: Cannot create worktree without folder"
                exit 1
            fi
        fi

        # Check write permissions (FR-015b)
        if [ ! -w "$WORKTREE_FOLDER" ]; then
            >&2 echo "[specify] Error: Worktree folder is not writable: $WORKTREE_FOLDER"
            >&2 echo "[specify] Check folder permissions and try again"
            exit 1
        fi

        WORKTREE_PATH="$WORKTREE_FOLDER/$BRANCH_NAME"

        # Check if worktree path already exists (FR-016)
        if [ -e "$WORKTREE_PATH" ]; then
            >&2 echo "[specify] Error: Worktree path already exists: $WORKTREE_PATH"
            >&2 echo "[specify] "
            >&2 echo "[specify] Resolution options:"
            >&2 echo "[specify]   1. Remove existing worktree: git worktree remove $BRANCH_NAME"
            >&2 echo "[specify]   2. Use a different branch name with --short-name"
            >&2 echo "[specify]   3. Manually delete the directory: rm -rf '$WORKTREE_PATH'"
            >&2 echo "[specify] "
            >&2 echo "[specify] To list all worktrees: git worktree list"
            exit 1
        fi

        # Create worktree with new branch
        git worktree add -b "$BRANCH_NAME" "$WORKTREE_PATH" || {
            >&2 echo "[specify] Error: Failed to create worktree"
            exit 1
        }

        >&2 echo "[specify] Created worktree: $WORKTREE_PATH"
        >&2 echo "[specify] Branch: $BRANCH_NAME"

        # Change to worktree directory for spec creation
        cd "$WORKTREE_PATH" || {
            >&2 echo "[specify] Error: Failed to change to worktree directory"
            cd "$ORIGINAL_DIR"
            exit 1
        }
        # Update REPO_ROOT to worktree location
        REPO_ROOT="$WORKTREE_PATH"

    elif [ "$SOURCE_MODE" = "none" ]; then
        # None mode: skip Git operations
        >&2 echo "[specify] Git operations disabled (mode: none)"
    else
        # Branch mode: traditional branch creation
        git checkout -b "$BRANCH_NAME"
    fi
else
    # Warn user if source mode expects Git but Git is unavailable
    if [ "$SOURCE_MODE" = "worktree" ] || [ "$SOURCE_MODE" = "branch" ]; then
        >&2 echo "[specify] Warning: Git repository not detected but source mode is set to '$SOURCE_MODE'"
        >&2 echo "[specify] Creating spec in main repository instead of using Git-based workflow"
        >&2 echo "[specify] To use $SOURCE_MODE mode, initialize Git with: git init"
    else
        >&2 echo "[specify] Warning: Git repository not detected; skipped branch creation for $BRANCH_NAME"
    fi
fi

# Update SPECS_DIR if we're in a worktree
if [ "$SOURCE_MODE" = "worktree" ] && [ "$HAS_GIT" = true ]; then
    SPECS_DIR="$REPO_ROOT/specs"
fi

FEATURE_DIR="$SPECS_DIR/$BRANCH_NAME"
mkdir -p "$FEATURE_DIR" || {
    >&2 echo "[specify] Error: Failed to create feature directory: $FEATURE_DIR"
    cd "$ORIGINAL_DIR"
    exit 1
}

TEMPLATE="$REPO_ROOT/.specify/templates/spec-template.md"
SPEC_FILE="$FEATURE_DIR/spec.md"
if [ -f "$TEMPLATE" ]; then 
    cp "$TEMPLATE" "$SPEC_FILE" || {
        >&2 echo "[specify] Error: Failed to copy template file"
        cd "$ORIGINAL_DIR"
        exit 1
    }
else 
    touch "$SPEC_FILE" || {
        >&2 echo "[specify] Error: Failed to create spec file"
        cd "$ORIGINAL_DIR"
        exit 1
    }
fi

# Set the SPECIFY_FEATURE environment variable for the current session
export SPECIFY_FEATURE="$BRANCH_NAME"

if $JSON_MODE; then
    printf '{"BRANCH_NAME":"%s","SPEC_FILE":"%s","FEATURE_NUM":"%s","SOURCE_MODE":"%s"}\n' "$BRANCH_NAME" "$SPEC_FILE" "$FEATURE_NUM" "$SOURCE_MODE"
else
    # Feature 001: Display source management mode
    case "$SOURCE_MODE" in
        "worktree") echo "MODE: Worktree mode active" ;;
        "none")     echo "MODE: No Git mode" ;;
        *)          echo "MODE: Branch mode active" ;;
    esac
    echo "BRANCH_NAME: $BRANCH_NAME"
    echo "SPEC_FILE: $SPEC_FILE"
    echo "FEATURE_NUM: $FEATURE_NUM"
    echo "SPECIFY_FEATURE environment variable set to: $BRANCH_NAME"
fi
