#!/usr/bin/env bash

set -e

JSON_MODE=false
ALLOW_EXISTING=false
SHORT_NAME=""
BRANCH_NUMBER=""
USE_TIMESTAMP=false
# Empty means "not stated on the command line" — resolved later from
# .specify/init-options.json, which is where `specify init -wt` records it.
WORKTREE_MODE=""
ARGS=()
i=1
while [ $i -le $# ]; do
    arg="${!i}"
    case "$arg" in
        --json)
            JSON_MODE=true
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
        --timestamp)
            USE_TIMESTAMP=true
            ;;
        --worktree)
            WORKTREE_MODE=true
            ;;
        --no-worktree)
            WORKTREE_MODE=false
            ;;
        --help|-h)
            echo "Usage: $0 [--json] [--allow-existing-branch] [--short-name <name>] [--number N] [--timestamp] <feature_description>"
            echo ""
            echo "Options:"
            echo "  --json              Output in JSON format"
            echo "  --allow-existing-branch  Switch to branch if it already exists instead of failing"
            echo "  --short-name <name> Provide a custom short name (2-4 words) for the branch"
            echo "  --number N          Specify branch number manually (overrides auto-detection)"
            echo "  --timestamp         Use timestamp prefix (YYYYMMDD-HHMMSS) instead of sequential numbering"
            echo "  --worktree          Create the branch in a NEW linked worktree instead of checking it out here"
            echo "  --no-worktree       Force checkout-in-place even if the project was initialized with -wt"
            echo "  --help, -h          Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 'Add user authentication system' --short-name 'user-auth'"
            echo "  $0 'Implement OAuth2 integration for API' --number 5"
            echo "  $0 --timestamp --short-name 'user-auth' 'Add user authentication'"
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
    echo "Usage: $0 [--json] [--allow-existing-branch] [--short-name <name>] [--number N] [--timestamp] <feature_description>" >&2
    exit 1
fi

# Trim whitespace and validate description is not empty (e.g., user passed only whitespace)
FEATURE_DESCRIPTION=$(echo "$FEATURE_DESCRIPTION" | xargs)
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
            # Strip optional acronym prefix (e.g., "URA-" from "URA-001-name")
            local stripped_dirname
            stripped_dirname=$(echo "$dirname" | sed 's/^[A-Z]\{2,5\}-//')
            # Match sequential prefixes (>=3 digits), but skip timestamp dirs.
            if echo "$stripped_dirname" | grep -Eq '^[0-9]{3,}-' && ! echo "$stripped_dirname" | grep -Eq '^[0-9]{8}-[0-9]{6}-'; then
                number=$(echo "$stripped_dirname" | grep -Eo '^[0-9]+')
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
    local highest=0
    
    # Get all branches (local and remote)
    branches=$(git branch -a 2>/dev/null || echo "")
    
    if [ -n "$branches" ]; then
        while IFS= read -r branch; do
            # Clean branch name: remove leading markers and remote prefixes.
            #
            # The marker class must include '+', not only '*'. `git branch` writes
            # '*' for the branch checked out HERE and '+' for one checked out in a
            # LINKED WORKTREE. Matching only '*' left every '+' line as
            # "+ feature/JSE-023-x", which does not start with "feature/", so the
            # prefix strip missed, the digit test failed, and the branch was
            # skipped — silently, because a skipped branch merely fails to raise
            # the maximum.
            #
            # The effect is that every in-flight feature is invisible to numbering
            # exactly when features run in parallel, which is the only situation
            # in which the number can collide at all. Measured on a live repo:
            # highest 23 with '+' handled, 22 without, so the next feature was
            # about to reuse a number already taken.
            clean_branch=$(echo "$branch" | sed 's/^[*+ ]*//; s|^remotes/[^/]*/||')
            
            # Strip feature/ prefix if present
            clean_branch="${clean_branch#feature/}"
            # Strip optional acronym prefix (e.g., "URA-" from "URA-001-name")
            local stripped_branch
            stripped_branch=$(echo "$clean_branch" | sed 's/^[A-Z]\{2,5\}-//')

            # Extract sequential feature number (>=3 digits), skip timestamp branches.
            if echo "$stripped_branch" | grep -Eq '^[0-9]{3,}-' && ! echo "$stripped_branch" | grep -Eq '^[0-9]{8}-[0-9]{6}-'; then
                number=$(echo "$stripped_branch" | grep -Eo '^[0-9]+' || echo "0")
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
    git fetch --all --prune >/dev/null 2>&1 || true

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

# Function to extract project acronym from constitution.md
get_project_acronym() {
    local repo_root="$1"
    local constitution="$repo_root/.specify/memory/constitution.md"

    if [ ! -f "$constitution" ]; then
        echo ""
        return
    fi

    # Try to extract project_acronym from YAML front matter
    local acronym=""
    if head -1 "$constitution" | grep -q '^---$'; then
        acronym=$(awk '/^---$/{n++; next} n==1 && /^project_acronym:/{sub(/^project_acronym:[[:space:]]*/,""); gsub(/^["'"'"']|["'"'"']$/,""); print; exit}' "$constitution")
    fi

    # Skip if placeholder or empty
    if [ -n "$acronym" ] && [ "$acronym" != "[PROJECT_ACRONYM]" ]; then
        echo "$acronym"
        return
    fi

    # Fallback: derive from H1 heading (e.g., "# Upwork Routine Automation Constitution")
    local heading
    heading=$(grep -m1 '^# ' "$constitution" | sed 's/^# //')
    if [ -z "$heading" ]; then
        echo ""
        return
    fi

    # Skip if heading is still a placeholder
    if echo "$heading" | grep -q '\[PROJECT_NAME\]'; then
        echo ""
        return
    fi

    # Remove trailing "Constitution" if present
    heading=$(echo "$heading" | sed 's/[[:space:]]*Constitution[[:space:]]*$//')

    # Count words
    local word_count
    word_count=$(echo "$heading" | wc -w | tr -d ' ')

    if [ "$word_count" -eq 1 ]; then
        # Single word: first 3 letters uppercased
        echo "$heading" | tr '[:lower:]' '[:upper:]' | cut -c1-3
    elif [ "$word_count" -ge 2 ]; then
        # Multiple words: first letter of each word
        echo "$heading" | tr '[:lower:]' '[:upper:]' | sed 's/[[:space:]]\+/ /g' | sed 's/\([A-Z]\)[^ ]*/\1/g' | tr -d ' '
    else
        echo ""
    fi
}

# Resolve repository root using common.sh functions which prioritize .specify over git
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

REPO_ROOT=$(get_repo_root)

# Check if git is available at this repo root (not a parent)
if has_git; then
    HAS_GIT=true
else
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

# Warn if --number and --timestamp are both specified
if [ "$USE_TIMESTAMP" = true ] && [ -n "$BRANCH_NUMBER" ]; then
    >&2 echo "[specify] Warning: --number is ignored when --timestamp is used"
    BRANCH_NUMBER=""
fi

# Determine branch prefix
if [ "$USE_TIMESTAMP" = true ]; then
    FEATURE_NUM=$(date +%Y%m%d-%H%M%S)
    BRANCH_NAME="${FEATURE_NUM}-${BRANCH_SUFFIX}"
else
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

    # Get project acronym from constitution
    PROJECT_ACRONYM=$(get_project_acronym "$REPO_ROOT")

    # If no acronym found, ask the user
    if [ -z "$PROJECT_ACRONYM" ]; then
        CONSTITUTION_FILE="$REPO_ROOT/.specify/memory/constitution.md"
        >&2 echo ""
        >&2 printf "[specify] Enter PROJECT_ACRONYM (2-5 uppercase letters, or press Enter to skip): "
        read -r user_acronym || user_acronym=""
        # Uppercase and trim
        user_acronym=$(echo "$user_acronym" | tr '[:lower:]' '[:upper:]' | tr -d '[:space:]')
        if [[ "$user_acronym" =~ ^[A-Z]{2,5}$ ]]; then
            PROJECT_ACRONYM="$user_acronym"
            # Persist to constitution if file exists
            if [ -f "$CONSTITUTION_FILE" ]; then
                if head -1 "$CONSTITUTION_FILE" | grep -q '^---$'; then
                    if grep -q '^project_acronym:' "$CONSTITUTION_FILE"; then
                        sed -i.bak "s/^project_acronym:.*$/project_acronym: \"$PROJECT_ACRONYM\"/" "$CONSTITUTION_FILE"
                        rm -f "$CONSTITUTION_FILE.bak"
                    else
                        sed -i.bak "1a\\
project_acronym: \"$PROJECT_ACRONYM\"" "$CONSTITUTION_FILE"
                        rm -f "$CONSTITUTION_FILE.bak"
                    fi
                    >&2 echo "[specify] Saved PROJECT_ACRONYM=$PROJECT_ACRONYM to constitution."
                fi
            fi
        elif [ -n "$user_acronym" ]; then
            >&2 echo "[specify] Invalid acronym (must be 2-5 uppercase letters). Skipping."
        fi
    fi

    if [ -n "$PROJECT_ACRONYM" ]; then
        BRANCH_NAME="feature/${PROJECT_ACRONYM}-${FEATURE_NUM}-${BRANCH_SUFFIX}"
    else
        BRANCH_NAME="feature/${FEATURE_NUM}-${BRANCH_SUFFIX}"
    fi
fi

# GitHub enforces a 244-byte limit on branch names
# Validate and truncate if necessary
MAX_BRANCH_LENGTH=244
if [ ${#BRANCH_NAME} -gt $MAX_BRANCH_LENGTH ]; then
    # Calculate how much we need to trim from suffix
    # Account for prefix: "feature/" (8 if present) + optional acronym + hyphen + feature number + hyphen
    if [ -n "$PROJECT_ACRONYM" ]; then
        PREFIX_LENGTH=$((8 + ${#PROJECT_ACRONYM} + 1 + ${#FEATURE_NUM} + 1))
    elif [ "$USE_TIMESTAMP" = true ]; then
        PREFIX_LENGTH=$(( ${#FEATURE_NUM} + 1 ))
    else
        PREFIX_LENGTH=$((8 + ${#FEATURE_NUM} + 1))
    fi
    MAX_SUFFIX_LENGTH=$((MAX_BRANCH_LENGTH - PREFIX_LENGTH))


    # Truncate suffix at word boundary if possible
    TRUNCATED_SUFFIX=$(echo "$BRANCH_SUFFIX" | cut -c1-$MAX_SUFFIX_LENGTH)
    # Remove trailing hyphen if truncation created one
    TRUNCATED_SUFFIX=$(echo "$TRUNCATED_SUFFIX" | sed 's/-$//')

    ORIGINAL_BRANCH_NAME="$BRANCH_NAME"
    if [ -n "$PROJECT_ACRONYM" ]; then
        BRANCH_NAME="feature/${PROJECT_ACRONYM}-${FEATURE_NUM}-${TRUNCATED_SUFFIX}"
    else
        BRANCH_NAME="feature/${FEATURE_NUM}-${TRUNCATED_SUFFIX}"
    fi

    >&2 echo "[specify] Warning: Branch name exceeded GitHub's 244-byte limit"
    >&2 echo "[specify] Original: $ORIGINAL_BRANCH_NAME (${#ORIGINAL_BRANCH_NAME} bytes)"
    >&2 echo "[specify] Truncated to: $BRANCH_NAME (${#BRANCH_NAME} bytes)"
fi

# Resolve worktree mode: an explicit flag wins, then SPECIFY_WORKTREE in the
# environment, then what `specify init -wt` recorded in init-options.json. The
# recorded value is the default so the agent flow needs no extra argument — the
# choice was made once, at init, and does not have to be remembered per feature.
if [ -z "$WORKTREE_MODE" ]; then
    if [ -n "${SPECIFY_WORKTREE:-}" ]; then
        case "$SPECIFY_WORKTREE" in
            1|true|yes) WORKTREE_MODE=true ;;
            *) WORKTREE_MODE=false ;;
        esac
    elif grep -q '"worktree"[[:space:]]*:[[:space:]]*true' "$REPO_ROOT/.specify/init-options.json" 2>/dev/null; then
        WORKTREE_MODE=true
    else
        WORKTREE_MODE=false
    fi
fi

if [ "$HAS_GIT" = true ] && [ "$WORKTREE_MODE" = true ]; then
    # The worktree that holds the repository's shared state is the one containing
    # the common git dir. It must not be moved off its branch: in a project laid
    # out this way it owns the virtualenv, the data directories and everything the
    # linked worktrees symlink into.
    COMMON_DIR="$(git rev-parse --git-common-dir)"
    case "$COMMON_DIR" in /*) ;; *) COMMON_DIR="$(cd "$COMMON_DIR" && pwd)" ;; esac
    ANCHOR="$(dirname "$COMMON_DIR")"

    WORKTREE_ROOT="${SPECIFY_WORKTREE_ROOT:-${ANCHOR}-worktrees}"
    WORKTREE_DIR="$WORKTREE_ROOT/$(basename "$BRANCH_NAME")"

    # Branch from the default branch, not from HEAD. HEAD here is whatever the
    # caller happened to have open, and a feature silently based on another
    # feature is a merge conflict that surfaces days later.
    BASE_BRANCH=""
    for candidate in main master; do
        if git show-ref --verify --quiet "refs/heads/$candidate"; then
            BASE_BRANCH="$candidate"
            break
        fi
    done
    [ -n "$BASE_BRANCH" ] || BASE_BRANCH="$(git rev-parse --abbrev-ref HEAD)"

    if [ -e "$WORKTREE_DIR" ]; then
        >&2 echo "Error: $WORKTREE_DIR already exists. Remove it or pick a different short name."
        exit 1
    fi

    if ! git worktree add "$WORKTREE_DIR" -b "$BRANCH_NAME" "$BASE_BRANCH" >&2; then
        >&2 echo "Error: Failed to create worktree for '$BRANCH_NAME'."
        exit 1
    fi

    # Everything below writes the spec relative to REPO_ROOT/SPECS_DIR. Point both
    # at the new worktree, or the spec lands in the anchor's working tree while the
    # branch that is supposed to carry it lives somewhere else.
    REPO_ROOT="$WORKTREE_DIR"
    SPECS_DIR="$REPO_ROOT/specs"
    mkdir -p "$SPECS_DIR"
elif [ "$HAS_GIT" = true ]; then
    if ! git checkout -b "$BRANCH_NAME" 2>/dev/null; then
        # Check if branch already exists
        if git branch --list "$BRANCH_NAME" | grep -q .; then
            if [ "$ALLOW_EXISTING" = true ]; then
                # Switch to the existing branch instead of failing
                if ! git checkout "$BRANCH_NAME" 2>/dev/null; then
                    >&2 echo "Error: Failed to switch to existing branch '$BRANCH_NAME'. Please resolve any local changes or conflicts and try again."
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
            >&2 echo "Error: Failed to create git branch '$BRANCH_NAME'. Please check your git configuration and try again."
            exit 1
        fi
    fi
else
    >&2 echo "[specify] Warning: Git repository not detected; skipped branch creation for $BRANCH_NAME"
fi

# Strip feature/ prefix for spec directory name (avoids specs/feature/ nesting)
SPEC_DIR_NAME="${BRANCH_NAME#feature/}"
FEATURE_DIR="$SPECS_DIR/$SPEC_DIR_NAME"
mkdir -p "$FEATURE_DIR"

SPEC_FILE="$FEATURE_DIR/spec.md"
if [ ! -f "$SPEC_FILE" ]; then
    TEMPLATE=$(resolve_template "spec-template" "$REPO_ROOT") || true
    if [ -n "$TEMPLATE" ] && [ -f "$TEMPLATE" ]; then
        cp "$TEMPLATE" "$SPEC_FILE"
    else
        echo "Warning: Spec template not found; created empty spec file" >&2
        touch "$SPEC_FILE"
    fi
fi

# Inform the user how to persist the feature variable in their own shell
printf '# To persist: export SPECIFY_FEATURE=%q\n' "$BRANCH_NAME" >&2

# In worktree mode the branch is NOT checked out here, so every later step —
# plan, tasks, implement — resolves the repository root from its own working
# directory and would look for this spec in the wrong tree. Say so on stderr,
# where it is visible whether or not the caller asked for JSON.
if [ -n "${WORKTREE_DIR:-}" ]; then
    >&2 echo "[specify] Branch $BRANCH_NAME lives in a new worktree; this directory is unchanged."
    >&2 echo "[specify] Continue from: $WORKTREE_DIR"
fi

if $JSON_MODE; then
    if command -v jq >/dev/null 2>&1; then
        jq -cn \
            --arg branch_name "$BRANCH_NAME" \
            --arg spec_file "$SPEC_FILE" \
            --arg feature_num "$FEATURE_NUM" \
            --arg project_acronym "${PROJECT_ACRONYM:-}" \
            --arg worktree_dir "${WORKTREE_DIR:-}" \
            '{BRANCH_NAME:$branch_name,SPEC_FILE:$spec_file,FEATURE_NUM:$feature_num,PROJECT_ACRONYM:$project_acronym,WORKTREE_DIR:$worktree_dir}'
    else
        printf '{"BRANCH_NAME":"%s","SPEC_FILE":"%s","FEATURE_NUM":"%s","PROJECT_ACRONYM":"%s","WORKTREE_DIR":"%s"}\n' "$(json_escape "$BRANCH_NAME")" "$(json_escape "$SPEC_FILE")" "$(json_escape "$FEATURE_NUM")" "$(json_escape "${PROJECT_ACRONYM:-}")" "$(json_escape "${WORKTREE_DIR:-}")"
    fi
else
    echo "BRANCH_NAME: $BRANCH_NAME"
    echo "SPEC_FILE: $SPEC_FILE"
    echo "FEATURE_NUM: $FEATURE_NUM"
    echo "PROJECT_ACRONYM: ${PROJECT_ACRONYM:-}"
    [ -n "${WORKTREE_DIR:-}" ] && echo "WORKTREE_DIR: $WORKTREE_DIR"
    printf '# To persist in your shell: export SPECIFY_FEATURE=%q\n' "$BRANCH_NAME"
fi
