#!/usr/bin/env bash
# Git extension: create-new-feature-branch.sh
# Creates a git feature branch only. The feature directory and spec file
# are created by the core create-new-feature.sh script.
# Sources common.sh from the project's installed scripts, falling back to
# git-common.sh for minimal git helpers.

set -e

JSON_MODE=false
DRY_RUN=false
ALLOW_EXISTING=false
SHORT_NAME=""
BRANCH_NUMBER=""
USE_TIMESTAMP=false
ARGS=()
i=1
while [ $i -le $# ]; do
    arg="${!i}"
    case "$arg" in
        --json)
            JSON_MODE=true
            ;;
        --dry-run)
            DRY_RUN=true
            ;;
        --allow-existing-branch)
            ALLOW_EXISTING=true
            ;;
        --short-name)
            if [ $((i + 1)) -gt $# ]; then
                echo 'Error: --short-name requires a value' >&2
                exit 1
            fi
            i=$((i + 1))
            next_arg="${!i}"
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
            if [[ ! "$BRANCH_NUMBER" =~ ^[0-9]+$ ]]; then
                echo 'Error: --number must be a non-negative integer' >&2
                exit 1
            fi
            ;;
        --timestamp)
            USE_TIMESTAMP=true
            ;;
        --help|-h)
            echo "Usage: $0 [--json] [--dry-run] [--allow-existing-branch] [--short-name <name>] [--number N] [--timestamp] <feature_description>"
            echo ""
            echo "Options:"
            echo "  --json              Output in JSON format"
            echo "  --dry-run           Compute branch name without creating the branch"
            echo "  --allow-existing-branch  Switch to branch if it already exists instead of failing"
            echo "  --short-name <name> Provide a custom short name (2-4 words) for the branch"
            echo "  --number N          Specify branch number manually (overrides auto-detection)"
            echo "  --timestamp         Use timestamp prefix (YYYYMMDD-HHMMSS) instead of sequential numbering"
            echo "  --help, -h          Show this help message"
            echo ""
            echo "Environment variables:"
            echo "  GIT_BRANCH_NAME     Use this exact branch name, bypassing all prefix/suffix generation"
            echo ""
            echo "Configuration:"
            echo "  branch_template     Optional git-config.yml template with {author}, {app}, {number}, {slug}"
            echo "  branch_prefix       Optional shorthand namespace expanded before {number}-{slug}"
            echo ""
            echo "Examples:"
            echo "  $0 'Add user authentication system' --short-name 'user-auth'"
            echo "  $0 'Implement OAuth2 integration for API' --number 5"
            echo "  $0 --timestamp --short-name 'user-auth' 'Add user authentication'"
            echo "  GIT_BRANCH_NAME=my-branch $0 'feature description'"
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
    echo "Usage: $0 [--json] [--dry-run] [--allow-existing-branch] [--short-name <name>] [--number N] [--timestamp] <feature_description>" >&2
    exit 1
fi

# Trim whitespace and validate description is not empty
FEATURE_DESCRIPTION=$(echo "$FEATURE_DESCRIPTION" | sed -E 's/^[[:space:]]+|[[:space:]]+$//g')
if [ -z "$FEATURE_DESCRIPTION" ]; then
    echo "Error: Feature description cannot be empty or contain only whitespace" >&2
    exit 1
fi

# Function to get highest number from specs directory
get_highest_from_specs() {
    local specs_dir="$1"
    local highest=0

    if [ -d "$specs_dir" ]; then
        for dir in "$specs_dir"/*; do
            [ -d "$dir" ] || continue
            dirname=$(basename "$dir")
            # Match sequential prefixes (>=3 digits), but skip timestamp dirs.
            if echo "$dirname" | grep -Eq '^[0-9]{3,}-' && ! echo "$dirname" | grep -Eq '^[0-9]{8}-[0-9]{6}-'; then
                number=$(echo "$dirname" | grep -Eo '^[0-9]+')
                number=$((10#$number))
                if [ "$number" -gt "$highest" ]; then
                    highest=$number
                fi
            fi
        done
    fi

    echo "$highest"
}

# Function to get highest number from git branches
get_highest_from_branches() {
    local scope_prefix="${1:-}"
    git branch -a 2>/dev/null | sed -E 's/^[+*][[:space:]]+//; s/^[[:space:]]+//; s|^remotes/[^/]*/||' | _extract_highest_number "$scope_prefix"
}

# Extract the highest sequential feature number from a list of ref names (one per line).
_extract_highest_number() {
    local scope_prefix="${1:-}"
    local highest=0
    while IFS= read -r name; do
        [ -z "$name" ] && continue
        if [ -n "$scope_prefix" ]; then
            case "$name" in
                "$scope_prefix"*) name="${name#"$scope_prefix"}" ;;
                *) continue ;;
            esac
        fi
        name="${name##*/}"
        if echo "$name" | grep -Eq '^[0-9]{3,}-' \
            && ! echo "$name" | grep -Eq '^[0-9]{8}-[0-9]{6}-' \
            && ! echo "$name" | grep -Eq '^[0-9]{7}-[0-9]{6}-' \
            && ! echo "$name" | grep -Eq '^[0-9]{7,8}-[0-9]{6}$'; then
            number=$(echo "$name" | grep -Eo '^[0-9]{3,}-' | sed -E 's/-$//' || echo "0")
            number=$((10#$number))
            if [ "$number" -gt "$highest" ]; then
                highest=$number
            fi
        fi
    done
    echo "$highest"
}

# Function to get highest number from remote branches without fetching (side-effect-free)
get_highest_from_remote_refs() {
    local scope_prefix="${1:-}"
    local highest=0

    for remote in $(git remote 2>/dev/null); do
        local remote_highest
        remote_highest=$(GIT_TERMINAL_PROMPT=0 git ls-remote --heads "$remote" 2>/dev/null | sed 's|.*refs/heads/||' | _extract_highest_number "$scope_prefix")
        if [ "$remote_highest" -gt "$highest" ]; then
            highest=$remote_highest
        fi
    done

    echo "$highest"
}

# Function to check existing branches and return next available number.
check_existing_branches() {
    local specs_dir="$1"
    local skip_fetch="${2:-false}"
    local scope_prefix="${3:-}"

    if [ "$skip_fetch" = true ]; then
        local highest_remote=$(get_highest_from_remote_refs "$scope_prefix")
        local highest_branch=$(get_highest_from_branches "$scope_prefix")
        if [ "$highest_remote" -gt "$highest_branch" ]; then
            highest_branch=$highest_remote
        fi
    else
        git fetch --all --prune >/dev/null 2>&1 || true
        local highest_branch=$(get_highest_from_branches "$scope_prefix")
    fi

    local highest_spec=$(get_highest_from_specs "$specs_dir")

    local max_num=$highest_branch
    if [ "$highest_spec" -gt "$max_num" ]; then
        max_num=$highest_spec
    fi

    echo $((max_num + 1))
}

# Function to clean and format a branch name
clean_branch_name() {
    local name="$1"
    echo "$name" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/-\+/-/g' | sed 's/^-//' | sed 's/-$//'
}

# ---------------------------------------------------------------------------
# Source common.sh for resolve_template, json_escape, get_repo_root, has_git.
#
# Search locations in priority order:
#  1. .specify/scripts/bash/common.sh under the project root (installed project)
#  2. scripts/bash/common.sh under the project root (source checkout fallback)
#  3. git-common.sh next to this script (minimal fallback — lacks resolve_template)
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Find project root by walking up from the script location
_find_project_root() {
    local dir="$1"
    while [ "$dir" != "/" ]; do
        if [ -d "$dir/.specify" ] || [ -d "$dir/.git" ]; then
            echo "$dir"
            return 0
        fi
        dir="$(dirname "$dir")"
    done
    return 1
}

_common_loaded=false
_PROJECT_ROOT=$(_find_project_root "$SCRIPT_DIR") || true

if [ -n "$_PROJECT_ROOT" ] && [ -f "$_PROJECT_ROOT/.specify/scripts/bash/common.sh" ]; then
    source "$_PROJECT_ROOT/.specify/scripts/bash/common.sh"
    _common_loaded=true
elif [ -n "$_PROJECT_ROOT" ] && [ -f "$_PROJECT_ROOT/scripts/bash/common.sh" ]; then
    source "$_PROJECT_ROOT/scripts/bash/common.sh"
    _common_loaded=true
elif [ -f "$SCRIPT_DIR/git-common.sh" ]; then
    source "$SCRIPT_DIR/git-common.sh"
    _common_loaded=true
fi

if [ "$_common_loaded" != "true" ]; then
    echo "Error: Could not locate common.sh or git-common.sh. Please ensure the Specify core scripts are installed." >&2
    exit 1
fi

# SPECIFY_INIT_DIR is resolved (and validated) by the core resolver. If only the
# minimal git-common.sh was loaded, or an older core common.sh without the
# resolver was loaded, refuse rather than silently falling back to the wrong root.
if [ -n "${SPECIFY_INIT_DIR:-}" ] && ! type resolve_specify_init_dir >/dev/null 2>&1; then
    echo "Error: SPECIFY_INIT_DIR requires updated Spec Kit core scripts (common.sh with resolve_specify_init_dir), which were not found." >&2
    exit 1
fi

# Resolve repository root. When the core scripts are present, get_repo_root
# honors SPECIFY_INIT_DIR (the explicit project override for non-interactive /
# CI use) and hard-fails on an invalid value with no silent fallback.
if type get_repo_root >/dev/null 2>&1; then
    REPO_ROOT=$(get_repo_root) || exit 1
elif git rev-parse --show-toplevel >/dev/null 2>&1; then
    REPO_ROOT=$(git rev-parse --show-toplevel)
elif [ -n "$_PROJECT_ROOT" ]; then
    REPO_ROOT="$_PROJECT_ROOT"
else
    echo "Error: Could not determine repository root." >&2
    exit 1
fi

# Check if git is available at this repo root
if type has_git >/dev/null 2>&1; then
    if has_git "$REPO_ROOT"; then
        HAS_GIT=true
    else
        HAS_GIT=false
    fi
elif git -C "$REPO_ROOT" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    HAS_GIT=true
else
    HAS_GIT=false
fi

cd "$REPO_ROOT"

SPECS_DIR="$REPO_ROOT/specs"
CONFIG_FILE="$REPO_ROOT/.specify/extensions/git/git-config.yml"

read_git_config_value() {
    local key="$1"
    [ -f "$CONFIG_FILE" ] || return 0
    grep -E "^[[:space:]]*${key}:" "$CONFIG_FILE" 2>/dev/null \
        | head -n 1 \
        | sed -E "s/^[[:space:]]*${key}:[[:space:]]*//" \
        | sed -E 's/[[:space:]]+#.*$//' \
        | sed -E 's/^[[:space:]]+|[[:space:]]+$//g' \
        | sed -E 's/^"//; s/"$//' \
        | sed -E "s/^'//; s/'$//"
}

branch_token() {
    local value="$1"
    local fallback="$2"
    local cleaned
    cleaned=$(clean_branch_name "$value")
    if [ -n "$cleaned" ]; then
        printf '%s\n' "$cleaned"
    else
        printf '%s\n' "$fallback"
    fi
}

get_author_token() {
    local author=""
    if command -v git >/dev/null 2>&1; then
        author=$(git config user.name 2>/dev/null || true)
        if [ -z "$author" ]; then
            author=$(git config user.email 2>/dev/null | sed 's/@.*$//' || true)
        fi
    fi
    if [ -z "$author" ]; then
        author="${USER:-unknown}"
    fi
    branch_token "$author" "unknown"
}

get_app_token() {
    branch_token "$(basename "$REPO_ROOT")" "app"
}

resolve_branch_template() {
    local template
    local prefix
    template=$(read_git_config_value "branch_template")
    if [ -n "$template" ]; then
        printf '%s\n' "$template"
        return
    fi

    prefix=$(read_git_config_value "branch_prefix")
    if [ -z "$prefix" ]; then
        printf '%s\n' ""
        return
    fi
    case "$prefix" in
        */) printf '%s%s\n' "$prefix" "{number}-{slug}" ;;
        *) printf '%s/%s\n' "$prefix" "{number}-{slug}" ;;
    esac
}

render_branch_template() {
    local template="$1"
    local feature_num="$2"
    local branch_suffix="$3"
    local rendered="$template"
    rendered=${rendered//\{author\}/$AUTHOR_TOKEN}
    rendered=${rendered//\{app\}/$APP_TOKEN}
    rendered=${rendered//\{number\}/$feature_num}
    rendered=${rendered//\{slug\}/$branch_suffix}
    printf '%s\n' "$rendered"
}

validate_branch_template() {
    local template="$1"
    [ -n "$template" ] || return 0
    local feature_segment
    feature_segment="${template##*/}"
    case "$template" in
        *"{number}"*) ;;
        *)
            >&2 echo "Error: branch_template must include the {number} token so generated branches remain valid feature branches."
            exit 1
            ;;
    esac
    case "$template" in
        *"{slug}"*"{number}"*)
            >&2 echo "Error: branch_template must not place {slug} before {number}; use {slug} only in the final feature segment."
            exit 1
            ;;
    esac
    case "$feature_segment" in
        "{number}-"*) ;;
        *)
            >&2 echo "Error: branch_template must put {number}- at the start of the final path segment so generated branches remain valid feature branches."
            exit 1
            ;;
    esac
}

build_branch_name() {
    local feature_num="$1"
    local branch_suffix="$2"
    if [ -n "$BRANCH_TEMPLATE" ]; then
        render_branch_template "$BRANCH_TEMPLATE" "$feature_num" "$branch_suffix"
    else
        printf '%s-%s\n' "$feature_num" "$branch_suffix"
    fi
}

branch_scope_prefix() {
    local template="$1"
    local prefix="$template"
    [ -n "$prefix" ] || return 0
    case "$prefix" in
        *"{number}"*) prefix="${prefix%%\{number\}*}" ;;
        *"{slug}"*) prefix="${prefix%%\{slug\}*}" ;;
        *) return 0 ;;
    esac
    render_branch_template "$prefix" "" "$BRANCH_SUFFIX"
}

extract_feature_num_from_branch() {
    local branch_name="$1"
    local feature_segment="${branch_name##*/}"
    local match
    match=$(printf '%s\n' "$feature_segment" | grep -Eo '^[0-9]{8}-[0-9]{6}-' | head -n 1 || true)
    if [ -n "$match" ]; then
        printf '%s\n' "$match" | sed -E 's/-$//'
        return
    fi
    match=$(printf '%s\n' "$feature_segment" | grep -Eo '^[0-9]+-' | head -n 1 || true)
    if [ -n "$match" ]; then
        printf '%s\n' "$match" | sed -E 's/-$//'
        return
    fi
    printf '%s\n' "$branch_name"
}

AUTHOR_TOKEN=$(get_author_token)
APP_TOKEN=$(get_app_token)
BRANCH_TEMPLATE=$(resolve_branch_template)
validate_branch_template "$BRANCH_TEMPLATE"

# Function to generate branch name with stop word filtering
generate_branch_name() {
    local description="$1"

    local stop_words="^(i|a|an|the|to|for|of|in|on|at|by|with|from|is|are|was|were|be|been|being|have|has|had|do|does|did|will|would|should|could|can|may|might|must|shall|this|that|these|those|my|your|our|their|want|need|add|get|set)$"

    local clean_name=$(printf '%s' "$description" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/ /g')

    local meaningful_words=()
    for word in $clean_name; do
        [ -z "$word" ] && continue
        if ! echo "$word" | grep -qiE "$stop_words"; then
            if [ ${#word} -ge 3 ]; then
                meaningful_words+=("$word")
            # Uppercase via tr (portable) rather than bash's 4+ "^^" case
            # expansion, which breaks on macOS's default bash 3.2 (bad substitution).
            elif printf '%s' "$description" | grep -qw -- "$(printf '%s' "$word" | tr '[:lower:]' '[:upper:]')"; then
                meaningful_words+=("$word")
            fi
        fi
    done

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
        local cleaned=$(clean_branch_name "$description")
        echo "$cleaned" | tr '-' '\n' | grep -v '^$' | head -3 | tr '\n' '-' | sed 's/-$//'
    fi
}

# Check for GIT_BRANCH_NAME env var override (exact branch name, no prefix/suffix)
if [ -n "${GIT_BRANCH_NAME:-}" ]; then
    BRANCH_NAME="$GIT_BRANCH_NAME"
    FEATURE_NUM=$(extract_feature_num_from_branch "$BRANCH_NAME")
    BRANCH_SUFFIX="$BRANCH_NAME"
else
    # Generate branch name
    if [ -n "$SHORT_NAME" ]; then
        BRANCH_SUFFIX=$(clean_branch_name "$SHORT_NAME")
    else
        BRANCH_SUFFIX=$(generate_branch_name "$FEATURE_DESCRIPTION")
    fi

    # Warn if --number and --timestamp are both specified
    if [ "$USE_TIMESTAMP" = true ] && [ -n "$BRANCH_NUMBER" ]; then
        >&2 echo "[specify] Warning: --number is ignored when --timestamp is used"
        BRANCH_NUMBER=""
    fi

    # Determine branch prefix
    if [ "$USE_TIMESTAMP" = true ]; then
        FEATURE_NUM=$(date +%Y%m%d-%H%M%S)
        BRANCH_NAME=$(build_branch_name "$FEATURE_NUM" "$BRANCH_SUFFIX")
    else
        BRANCH_SCOPE_PREFIX=$(branch_scope_prefix "$BRANCH_TEMPLATE")
        if [ -z "$BRANCH_NUMBER" ]; then
            if [ "$DRY_RUN" = true ] && [ "$HAS_GIT" = true ]; then
                BRANCH_NUMBER=$(check_existing_branches "$SPECS_DIR" true "$BRANCH_SCOPE_PREFIX")
            elif [ "$DRY_RUN" = true ]; then
                HIGHEST=$(get_highest_from_specs "$SPECS_DIR")
                BRANCH_NUMBER=$((HIGHEST + 1))
            elif [ "$HAS_GIT" = true ]; then
                BRANCH_NUMBER=$(check_existing_branches "$SPECS_DIR" false "$BRANCH_SCOPE_PREFIX")
            else
                HIGHEST=$(get_highest_from_specs "$SPECS_DIR")
                BRANCH_NUMBER=$((HIGHEST + 1))
            fi
        fi

        FEATURE_NUM=$(printf "%03d" "$((10#$BRANCH_NUMBER))")
        BRANCH_NAME=$(build_branch_name "$FEATURE_NUM" "$BRANCH_SUFFIX")
    fi
fi

# GitHub enforces a 244-byte limit on branch names
MAX_BRANCH_LENGTH=244
_byte_length() { printf '%s' "$1" | LC_ALL=C wc -c | tr -d ' '; }
BRANCH_BYTE_LEN=$(_byte_length "$BRANCH_NAME")
if [ -n "${GIT_BRANCH_NAME:-}" ] && [ "$BRANCH_BYTE_LEN" -gt $MAX_BRANCH_LENGTH ]; then
    >&2 echo "Error: GIT_BRANCH_NAME must be 244 bytes or fewer in UTF-8. Provided value is ${BRANCH_BYTE_LEN} bytes."
    exit 1
elif [ "$BRANCH_BYTE_LEN" -gt $MAX_BRANCH_LENGTH ]; then
    ORIGINAL_BRANCH_NAME="$BRANCH_NAME"
    TRUNCATED_SUFFIX="$BRANCH_SUFFIX"
    while [ "$(_byte_length "$BRANCH_NAME")" -gt "$MAX_BRANCH_LENGTH" ] && [ -n "$TRUNCATED_SUFFIX" ]; do
        TRUNCATED_SUFFIX="${TRUNCATED_SUFFIX%?}"
        TRUNCATED_SUFFIX="${TRUNCATED_SUFFIX%-}"
        BRANCH_NAME=$(build_branch_name "$FEATURE_NUM" "$TRUNCATED_SUFFIX")
    done
    if [ "$(_byte_length "$BRANCH_NAME")" -gt "$MAX_BRANCH_LENGTH" ]; then
        >&2 echo "Error: Branch template prefix exceeds GitHub's 244-byte branch name limit."
        exit 1
    fi

    >&2 echo "[specify] Warning: Branch name exceeded GitHub's 244-byte limit"
    ORIGINAL_BRANCH_BYTE_LEN=$(_byte_length "$ORIGINAL_BRANCH_NAME")
    TRUNCATED_BRANCH_BYTE_LEN=$(_byte_length "$BRANCH_NAME")
    >&2 echo "[specify] Original: $ORIGINAL_BRANCH_NAME (${ORIGINAL_BRANCH_BYTE_LEN} bytes)"
    >&2 echo "[specify] Truncated to: $BRANCH_NAME (${TRUNCATED_BRANCH_BYTE_LEN} bytes)"
fi

if [ "$DRY_RUN" != true ]; then
    if [ "$HAS_GIT" = true ]; then
        branch_create_error=""
        if ! branch_create_error=$(git checkout -q -b "$BRANCH_NAME" 2>&1); then
            current_branch="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
            if git branch --list "$BRANCH_NAME" | grep -q .; then
                if [ "$ALLOW_EXISTING" = true ]; then
                    if [ "$current_branch" = "$BRANCH_NAME" ]; then
                        :
                    elif ! switch_branch_error=$(git checkout -q "$BRANCH_NAME" 2>&1); then
                        >&2 echo "Error: Failed to switch to existing branch '$BRANCH_NAME'. Please resolve any local changes or conflicts and try again."
                        if [ -n "$switch_branch_error" ]; then
                            >&2 printf '%s\n' "$switch_branch_error"
                        fi
                        exit 1
                    fi
                elif [ "$USE_TIMESTAMP" = true ]; then
                    >&2 echo "Error: Branch '$BRANCH_NAME' already exists. Rerun to get a new timestamp or use a different --short-name."
                    exit 1
                else
                    >&2 echo "Error: Branch '$BRANCH_NAME' already exists. Please use a different feature name or specify a different number with --number."
                    exit 1
                fi
            else
                >&2 echo "Error: Failed to create git branch '$BRANCH_NAME'."
                if [ -n "$branch_create_error" ]; then
                    >&2 printf '%s\n' "$branch_create_error"
                else
                    >&2 echo "Please check your git configuration and try again."
                fi
                exit 1
            fi
        fi
    else
        >&2 echo "[specify] Warning: Git repository not detected; skipped branch creation for $BRANCH_NAME"
    fi

    printf '# To persist: export SPECIFY_FEATURE=%q\n' "$BRANCH_NAME" >&2
fi

if $JSON_MODE; then
    if command -v jq >/dev/null 2>&1; then
        if [ "$DRY_RUN" = true ]; then
            jq -cn \
                --arg branch_name "$BRANCH_NAME" \
                --arg feature_num "$FEATURE_NUM" \
                '{BRANCH_NAME:$branch_name,FEATURE_NUM:$feature_num,DRY_RUN:true}'
        else
            jq -cn \
                --arg branch_name "$BRANCH_NAME" \
                --arg feature_num "$FEATURE_NUM" \
                '{BRANCH_NAME:$branch_name,FEATURE_NUM:$feature_num}'
        fi
    else
        if type json_escape >/dev/null 2>&1; then
            _je_branch=$(json_escape "$BRANCH_NAME")
            _je_num=$(json_escape "$FEATURE_NUM")
        else
            _je_branch="$BRANCH_NAME"
            _je_num="$FEATURE_NUM"
        fi
        if [ "$DRY_RUN" = true ]; then
            printf '{"BRANCH_NAME":"%s","FEATURE_NUM":"%s","DRY_RUN":true}\n' "$_je_branch" "$_je_num"
        else
            printf '{"BRANCH_NAME":"%s","FEATURE_NUM":"%s"}\n' "$_je_branch" "$_je_num"
        fi
    fi
else
    echo "BRANCH_NAME: $BRANCH_NAME"
    echo "FEATURE_NUM: $FEATURE_NUM"
    if [ "$DRY_RUN" != true ]; then
        printf '# To persist in your shell: export SPECIFY_FEATURE=%q\n' "$BRANCH_NAME"
    fi
fi
