#!/usr/bin/env bash
# Create a new feature branch and spec directory

set -e

JSON_MODE=false
SHORT_NAME=""
BRANCH_NUMBER=""
JIRA_NUMBER=""
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
        --jira-number)
            if [ $((i + 1)) -gt $# ]; then
                echo 'Error: --jira-number requires a value' >&2
                exit 1
            fi
            i=$((i + 1))
            next_arg="${!i}"
            if [[ "$next_arg" == --* ]]; then
                echo 'Error: --jira-number requires a value' >&2
                exit 1
            fi
            JIRA_NUMBER="$next_arg"
            # Validate Jira number format (company convention: C12345-7890)
            if ! [[ "$JIRA_NUMBER" =~ ^C[0-9]{5}-[0-9]{4}$ ]]; then
                echo "Error: Jira number must match format C12345-7890 (e.g., C99999-1234)" >&2
                echo "       Provided: $JIRA_NUMBER" >&2
                exit 1
            fi
            ;;
        --help|-h)
            echo "Usage: $0 [--json] [--short-name <name>] [--number N] [--jira-number <jira>] <feature_description>"
            echo ""
            echo "Options:"
            echo "  --json                  Output in JSON format"
            echo "  --short-name <name>     Provide a custom short name (2-4 words) for the branch"
            echo "  --number N              Specify branch number manually (overrides auto-detection)"
            echo "  --jira-number <jira>    Jira ticket number (e.g., C12345-7890)"
            echo "  --help, -h              Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 'Add user authentication system' --short-name 'user-auth' --jira-number 'C12345-7890'"
            echo "  $0 'Implement OAuth2 integration for API' --number 5 --jira-number 'C12345-7890'"
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

# Function to check existing branches (local and remote) and return next available number
check_existing_branches() {
    local short_name="$1"

    # Fetch all remotes to get latest branch info (suppress errors if no remotes)
    git fetch --all --prune 2>/dev/null || true

    # Find all branches matching both old and new patterns using git ls-remote
    # Old pattern: refs/heads/001-short-name
    # New pattern: refs/heads/feature/001-C12345-7890-short-name
    # Match only 3-digit spec-kit branches (001-, 002-, etc.) to avoid false positives
    local remote_branches=$(git ls-remote --heads origin 2>/dev/null | grep -E "refs/heads/(feature/)?[0-9]{3}-" | sed 's/.*refs\/heads\/\(feature\/\)\?\([0-9]\{3\}\).*/\2/' | sort -n)

    # Also check local branches (both patterns)
    # Match only 3-digit spec-kit branches to avoid matching unrelated numeric branches
    local local_branches=$(git branch 2>/dev/null | grep -E "^[* ]*(feature/)?[0-9]{3}-" | sed 's/^[* ]*//' | sed 's/^feature\///' | sed 's/^\([0-9]\{3\}\)-.*/\1/' | sort -n)

    # Check specs directory as well (directory name doesn't have feature/ prefix)
    # Match only 3-digit spec-kit directories (001-*, 002-*, etc.)
    local spec_dirs=""
    if [ -d "$SPECS_DIR" ]; then
        spec_dirs=$(find "$SPECS_DIR" -maxdepth 1 -type d -name "[0-9][0-9][0-9]-*" 2>/dev/null | xargs -n1 basename 2>/dev/null | sed 's/^\([0-9]\{3\}\)-.*/\1/' | sort -n)
    fi

    # Combine all sources and get the highest number
    local max_num=0
    for num in $remote_branches $local_branches $spec_dirs; do
        if [ "$num" -gt "$max_num" ]; then
            max_num=$num
        fi
    done

    # Return next number
    echo $((max_num + 1))
}

# Resolve repository root. Prefer git information when available, but fall back
# to searching for repository markers so the workflow still functions in repositories that
# were initialised with --no-git.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if git rev-parse --show-toplevel >/dev/null 2>&1; then
    REPO_ROOT=$(git rev-parse --show-toplevel)
    HAS_GIT=true
else
    REPO_ROOT="$(find_repo_root "$SCRIPT_DIR")"
    if [ -z "$REPO_ROOT" ]; then
        echo "Error: Could not determine repository root. Please run this script from within the repository." >&2
        exit 1
    fi
    HAS_GIT=false
fi

cd "$REPO_ROOT"

SPECS_DIR="$REPO_ROOT/specs"
mkdir -p "$SPECS_DIR"

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
        echo "$description" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-//' | sed 's/-$//' | tr '-' '\n' | grep -v '^$' | head -3 | tr '\n' '-' | sed 's/-$//'
    fi
}

# Generate branch name
if [ -n "$SHORT_NAME" ]; then
    # Use provided short name, just clean it up
    BRANCH_SUFFIX=$(echo "$SHORT_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-//' | sed 's/-$//')
else
    # Generate from description with smart filtering
    BRANCH_SUFFIX=$(generate_branch_name "$FEATURE_DESCRIPTION")
fi

# Determine branch number
if [ -z "$BRANCH_NUMBER" ]; then
    if [ "$HAS_GIT" = true ]; then
        # Check existing branches on remotes
        BRANCH_NUMBER=$(check_existing_branches "$BRANCH_SUFFIX")
    else
        # Fall back to local directory check
        HIGHEST=0
        if [ -d "$SPECS_DIR" ]; then
            for dir in "$SPECS_DIR"/*; do
                [ -d "$dir" ] || continue
                dirname=$(basename "$dir")
                number=$(echo "$dirname" | grep -o '^[0-9]\+' || echo "0")
                number=$((10#$number))
                if [ "$number" -gt "$HIGHEST" ]; then HIGHEST=$number; fi
            done
        fi
        BRANCH_NUMBER=$((HIGHEST + 1))
    fi
fi

FEATURE_NUM=$(printf "%03d" "$BRANCH_NUMBER")

# Build branch name with feature/ prefix and optional Jira number
# Format: feature/001-C12345-7890-short-name (with Jira)
#     or: feature/001-short-name (without Jira, backward compat)
if [ -n "$JIRA_NUMBER" ]; then
    BRANCH_NAME="feature/${FEATURE_NUM}-${JIRA_NUMBER}-${BRANCH_SUFFIX}"
else
    BRANCH_NAME="feature/${FEATURE_NUM}-${BRANCH_SUFFIX}"
fi

# GitHub enforces a 244-byte limit on branch names
# Validate and truncate if necessary
MAX_BRANCH_LENGTH=244
if [ ${#BRANCH_NAME} -gt $MAX_BRANCH_LENGTH ]; then
    # Calculate how much we need to trim from suffix
    # Account for: "feature/" (8) + feature number (3) + hyphens + optional Jira number
    PREFIX_LENGTH=$((8 + 3 + 1))  # feature/ + 001 + hyphen
    if [ -n "$JIRA_NUMBER" ]; then
        PREFIX_LENGTH=$((PREFIX_LENGTH + ${#JIRA_NUMBER} + 1))  # + jira + hyphen
    fi
    MAX_SUFFIX_LENGTH=$((MAX_BRANCH_LENGTH - PREFIX_LENGTH))

    # Truncate suffix at word boundary if possible
    TRUNCATED_SUFFIX=$(echo "$BRANCH_SUFFIX" | cut -c1-$MAX_SUFFIX_LENGTH)
    # Remove trailing hyphen if truncation created one
    TRUNCATED_SUFFIX=$(echo "$TRUNCATED_SUFFIX" | sed 's/-$//')

    ORIGINAL_BRANCH_NAME="$BRANCH_NAME"
    if [ -n "$JIRA_NUMBER" ]; then
        BRANCH_NAME="feature/${FEATURE_NUM}-${JIRA_NUMBER}-${TRUNCATED_SUFFIX}"
    else
        BRANCH_NAME="feature/${FEATURE_NUM}-${TRUNCATED_SUFFIX}"
    fi

    >&2 echo "[specify] Warning: Branch name exceeded GitHub's 244-byte limit"
    >&2 echo "[specify] Original: $ORIGINAL_BRANCH_NAME (${#ORIGINAL_BRANCH_NAME} bytes)"
    >&2 echo "[specify] Truncated to: $BRANCH_NAME (${#BRANCH_NAME} bytes)"
fi

if [ "$HAS_GIT" = true ]; then
    git checkout -b "$BRANCH_NAME"
else
    >&2 echo "[specify] Warning: Git repository not detected; skipped branch creation for $BRANCH_NAME"
fi

# Feature directory doesn't include the feature/ prefix
# Extract directory name from branch name (remove feature/ prefix if present)
DIR_NAME="${BRANCH_NAME#feature/}"
FEATURE_DIR="$SPECS_DIR/$DIR_NAME"
mkdir -p "$FEATURE_DIR"

TEMPLATE="$REPO_ROOT/.specify/templates/spec-template.md"
SPEC_FILE="$FEATURE_DIR/spec.md"
if [ -f "$TEMPLATE" ]; then cp "$TEMPLATE" "$SPEC_FILE"; else touch "$SPEC_FILE"; fi

# Set the SPECIFY_FEATURE environment variable for the current session
export SPECIFY_FEATURE="$BRANCH_NAME"

if $JSON_MODE; then
    printf '{"BRANCH_NAME":"%s","SPEC_FILE":"%s","FEATURE_NUM":"%s"}\n' "$BRANCH_NAME" "$SPEC_FILE" "$FEATURE_NUM"
else
    echo "BRANCH_NAME: $BRANCH_NAME"
    echo "SPEC_FILE: $SPEC_FILE"
    echo "FEATURE_NUM: $FEATURE_NUM"
    echo "SPECIFY_FEATURE environment variable set to: $BRANCH_NAME"
fi
