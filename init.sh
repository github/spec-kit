#!/bin/bash

set -e

# Capture execution directory before anything else (for --search-path default)
EXEC_DIR="$(pwd)"

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
SOURCE_DIR="$HOME/git/spec-kit"

DEFAULT_AI="claude"
DEFAULT_SCRIPT="sh"
DESTROY=false
ALL_REPOS=false
SEARCH_PATH="$EXEC_DIR"
MAX_DEPTH=3
EXECUTE=false

usage() {
    echo "Usage: $0 <project_path> [options]"
    echo "   OR: $0 --all-repos [options]"
    echo ""
    echo "Initialize a Specify project by copying files from ~/git/spec-kit"
    echo ""
    echo "Single Repository Mode:"
    echo "  project_path    Path to create or initialize project"
    echo ""
    echo "Multi-Repository Mode:"
    echo "  --all-repos           Process all repos containing .specify folders"
    echo "  --search-path PATH    Directory to search (default: current directory)"
    echo "  --max-depth N         Search depth for .specify folders (default: 3)"
    echo "  --execute             Skip preview and execute immediately"
    echo ""
    echo "Options:"
    echo "  --ai ASSISTANT        AI assistant: claude, gemini, copilot, cursor (default: claude)"
    echo "  --script TYPE         Script type: sh, ps (default: sh)"
    echo "  --destroy             Delete existing .specify and start fresh"
    echo "  --help                Show this help message"
    echo ""
    echo "Examples:"
    echo "  Single repo:"
    echo "    $0 my-project"
    echo "    $0 my-project --ai claude --script sh"
    echo "    $0 . --destroy"
    echo ""
    echo "  Multi-repo (always previews first):"
    echo "    $0 --all-repos --ai claude"
    echo "    $0 --all-repos --search-path ~/git/mq --max-depth 3"
    echo "    $0 --all-repos --execute --ai claude"
}

log() {
    echo "[INFO] $*" >&2
}

error() {
    echo "[ERROR] $*" >&2
    exit 1
}

# Parse arguments
PROJECT_PATH=""
AI_ASSISTANT="$DEFAULT_AI"
SCRIPT_TYPE="$DEFAULT_SCRIPT"

while [[ $# -gt 0 ]]; do
    case $1 in
        --ai)
            AI_ASSISTANT="$2"
            shift 2
            ;;
        --script)
            SCRIPT_TYPE="$2"
            shift 2
            ;;
        --destroy)
            DESTROY=true
            shift
            ;;
        --all-repos)
            ALL_REPOS=true
            shift
            ;;
        --search-path)
            SEARCH_PATH="$2"
            shift 2
            ;;
        --max-depth)
            MAX_DEPTH="$2"
            shift 2
            ;;
        --execute)
            EXECUTE=true
            shift
            ;;
        --help)
            usage
            exit 0
            ;;
        -*)
            error "Unknown option: $1"
            ;;
        *)
            if [[ -z "$PROJECT_PATH" ]]; then
                PROJECT_PATH="$1"
            else
                error "Too many arguments. Expected one project path."
            fi
            shift
            ;;
    esac
done

if [[ -z "$PROJECT_PATH" ]] && [[ "$ALL_REPOS" == false ]]; then
    usage
    exit 1
fi

# In multi-repo mode, PROJECT_PATH is ignored
if [[ "$ALL_REPOS" == true ]] && [[ -n "$PROJECT_PATH" ]]; then
    log "WARNING: Ignoring project_path in multi-repo mode"
fi

# Validate arguments
case "$AI_ASSISTANT" in
    claude|gemini|copilot|cursor) ;;
    *) error "Invalid AI assistant: $AI_ASSISTANT. Choose from: claude, gemini, copilot, cursor" ;;
esac

case "$SCRIPT_TYPE" in
    sh|ps) ;;
    *) error "Invalid script type: $SCRIPT_TYPE. Choose from: sh, ps" ;;
esac

# Validate source directory
if [[ ! -d "$SOURCE_DIR" ]]; then
    error "Source directory not found: $SOURCE_DIR"
fi

# Validate search path for multi-repo mode
if [[ "$ALL_REPOS" == true ]]; then
    SEARCH_PATH=$(realpath "$SEARCH_PATH" 2>/dev/null)
    if [[ ! -d "$SEARCH_PATH" ]]; then
        error "Search path not found: $SEARCH_PATH"
    fi

    # Validate max-depth is a positive integer
    if ! [[ "$MAX_DEPTH" =~ ^[0-9]+$ ]] || [[ "$MAX_DEPTH" -lt 1 ]]; then
        error "Invalid max-depth: $MAX_DEPTH. Must be a positive integer."
    fi
fi

# Resolve project path (only for single-repo mode)
if [[ "$ALL_REPOS" == false ]]; then
    if [[ -e "$PROJECT_PATH" ]]; then
        # Path exists, resolve it
        PROJECT_PATH=$(realpath "$PROJECT_PATH")
    else
        # Path doesn't exist, resolve parent and append basename
        parent_dir=$(dirname "$PROJECT_PATH")
        base_name=$(basename "$PROJECT_PATH")
        if [[ "$parent_dir" == "." ]]; then
            # Relative path in current directory
            PROJECT_PATH="$EXEC_DIR/$base_name"
        elif [[ -d "$parent_dir" ]]; then
            # Parent exists, resolve it
            PROJECT_PATH="$(realpath "$parent_dir")/$base_name"
        else
            # Parent doesn't exist either, use absolute path
            PROJECT_PATH="$(cd / && pwd)$(realpath "$parent_dir" 2>/dev/null || echo "$parent_dir")/$base_name"
        fi
    fi
fi

# ============================================================================
# FUNCTION: process_single_repo
# Process a single repository with spec-kit initialization
# Arguments:
#   $1 - Project path to initialize
#   $2 - Is preview mode (true/false)
# Uses global variables: AI_ASSISTANT, SCRIPT_TYPE, DESTROY, SOURCE_DIR
# ============================================================================
process_single_repo() {
    local project_path="$1"
    local is_preview="${2:-false}"
    local preview_prefix=""

    if [[ "$is_preview" == "true" ]]; then
        preview_prefix="Would "
    fi

    if [[ "$is_preview" == "false" ]]; then
        log "Initializing Specify project at: $project_path"
    fi
    log "AI Assistant: $AI_ASSISTANT"
    log "Script Type: $SCRIPT_TYPE"
    if [[ "$is_preview" == "false" ]]; then
        log "Source: $SOURCE_DIR"
    fi

    # Create project directory if it doesn't exist
    if [[ ! -d "$project_path" ]]; then
        if [[ "$is_preview" == "true" ]]; then
            log "${preview_prefix}create project directory: $project_path"
        else
            mkdir -p "$project_path"
            log "Created project directory: $project_path"
        fi
    fi

    if [[ "$is_preview" == "false" ]]; then
        cd "$project_path"
    fi

    # Destroy existing files if --destroy flag is used
    destroy_existing() {
        if [[ "$DESTROY" == true ]]; then
            # Check if .specify directory exists
            if [[ -d "$project_path/.specify" ]]; then
                if [[ "$is_preview" == "true" ]]; then
                    log "${preview_prefix}destroy existing .specify directory"
                    return
                fi

                echo ""
                echo "WARNING: --destroy will permanently delete the following directory if it exists:"
                echo "  .specify/"
                echo ""
                read -p "Are you sure you want to destroy all existing files? (y/N): " -n 1 -r
                echo ""

                if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                    echo "Operation cancelled."
                    exit 0
                fi


                # Ask about preserving constitution.md
                local preserve_constitution=false
                if [[ -f "$project_path/.specify/memory/constitution.md" ]]; then
                    echo ""
                    read -p "Do you want to preserve your existing constitution.md? (y/N): " -n 1 -r
                    echo ""
                    if [[ $REPLY =~ ^[Yy]$ ]]; then
                        preserve_constitution=true
                        log "Will preserve existing constitution.md"
                    fi
                fi
            fi

            log "Destroying existing project files..."

            # Backup constitution.md if preserving
            local constitution_backup=""
            if [[ "$preserve_constitution" == true ]] && [[ -f "$project_path/.specify/memory/constitution.md" ]]; then
                constitution_backup=$(mktemp)
                cp "$project_path/.specify/memory/constitution.md" "$constitution_backup"
            fi

            # Remove only .specify directory
            rm -rf "$project_path/.specify" 2>/dev/null || true
            log "Existing .specify directory destroyed"

            # Set global flags for later use
            export PRESERVE_CONSTITUTION="$preserve_constitution"
            export CONSTITUTION_BACKUP="$constitution_backup"
        fi
    }

    destroy_existing

    # Preview mode shortcut - skip actual file operations
    if [[ "$is_preview" == "true" ]]; then
        log "${preview_prefix}create .specify directory structure"
        log "${preview_prefix}copy memory folder"
        log "${preview_prefix}copy templates"
        log "${preview_prefix}copy scripts"
        log "${preview_prefix}generate $AI_ASSISTANT commands"
        log "${preview_prefix}update .gitignore"
        return 0
    fi

    # Create .specify directory structure
    mkdir -p "$project_path/.specify"/{memory,scripts,templates}
    log "Created .specify directory structure"

    # Create scripts subdirectory based on script type
    if [[ "$SCRIPT_TYPE" == "sh" ]]; then
        mkdir -p "$project_path/.specify/scripts/bash"
    else
        mkdir -p "$project_path/.specify/scripts/powershell"
    fi

    # Create specs directory if it doesn't exist
    if [[ ! -d "$project_path/specs" ]]; then
        mkdir -p "$project_path/specs"
        log "Created specs directory"
    else
        log "Preserving existing specs directory"
    fi

    # Copy files from source directory
    copy_files() {
        local src="$1"
        local dest="$2"
        local desc="$3"
        local exclude_file="$4"  # Optional: file to exclude from copy

        # Prepend project_path to dest if it's a relative path
        if [[ "$dest" != /* ]]; then
            dest="$project_path/$dest"
        fi

        if [[ -d "$src" ]]; then
            if [[ "$DESTROY" == true ]]; then
                # Remove existing directory completely and copy fresh
                if [[ -d "$dest" ]]; then
                    rm -rf "$dest"
                    log "Removed existing $desc for fresh copy"
                fi
                if [[ -n "$exclude_file" ]]; then
                    # Create destination directory and copy all files except excluded
                    mkdir -p "$dest"
                    for item in "$src"/*; do
                        if [[ -f "$item" ]] && [[ "$(basename "$item")" == "$exclude_file" ]]; then
                            log "Skipped $exclude_file (excluded during fresh copy)"
                            continue
                        fi
                        cp -r "$item" "$dest"/ 2>/dev/null || true
                    done
                    log "Copied $desc (fresh copy, excluded $exclude_file)"
                else
                    cp -r "$src" "$dest"
                    log "Copied $desc (fresh copy)"
                fi
            elif [[ ! -d "$dest" ]]; then
                # Create new directory
                cp -r "$src" "$dest"
                log "Copied $desc"
            else
                # Update mode: merge contents (overwrite files that exist in source)
                if [[ -n "$exclude_file" ]]; then
                    # Copy all files except the excluded one
                    for item in "$src"/*; do
                        if [[ -f "$item" ]] && [[ "$(basename "$item")" == "$exclude_file" ]]; then
                            log "Skipped $exclude_file (preserving existing)"
                            continue
                        fi
                        cp -r "$item" "$dest"/ 2>/dev/null || true
                    done
                    log "Updated $desc (merged with existing, excluded $exclude_file)"
                else
                    cp -r "$src"/* "$dest"/ 2>/dev/null || true
                    log "Updated $desc (merged with existing)"
                fi
            fi
        elif [[ -f "$src" ]]; then
            if [[ ! -f "$dest" ]]; then
                # New file
                mkdir -p "$(dirname "$dest")"
                cp "$src" "$dest"
                log "Copied $desc"
            else
                # File exists - always update (default behavior)
                cp "$src" "$dest"
                log "Updated $desc"
            fi
        else
            log "Source not found: $src"
        fi
    }

    # Check for existing constitution.md and ask about preservation (for non-destroy mode)
    PRESERVE_CONSTITUTION_UPDATE=false
    if [[ "$DESTROY" != true ]] && [[ -f "$project_path/.specify/memory/constitution.md" ]]; then
        echo ""
        read -p "Do you want to preserve your existing constitution.md? (y/N): " -n 1 -r
        echo ""
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            PRESERVE_CONSTITUTION_UPDATE=true
            log "Will preserve existing constitution.md"
        fi
    fi

    # Copy memory folder with all its files
    if [[ -d "$SOURCE_DIR/memory" ]]; then
        # Check if we should preserve constitution.md in any mode
        if [[ "$PRESERVE_CONSTITUTION_UPDATE" == true ]] || [[ "$PRESERVE_CONSTITUTION" == true ]]; then
            copy_files "$SOURCE_DIR/memory" ".specify/memory" "memory folder" "constitution.md"
        else
            copy_files "$SOURCE_DIR/memory" ".specify/memory" "memory folder"
        fi
    fi

    # Handle preserved constitution.md restoration (only relevant after --destroy)
    if [[ "$PRESERVE_CONSTITUTION" == "true" ]] && [[ -n "$CONSTITUTION_BACKUP" ]]; then
        # Restore from backup (overwrites the freshly copied one)
        cp "$CONSTITUTION_BACKUP" "$project_path/.specify/memory/constitution.md"
        rm -f "$CONSTITUTION_BACKUP"
        log "Restored preserved constitution.md"
    fi

    # Copy documentation files
    copy_files "$SOURCE_DIR/README.md" ".specify/README.md" "README.md"

    # Copy docs folder if it exists
    if [[ -d "$SOURCE_DIR/docs" ]]; then
        copy_files "$SOURCE_DIR/docs" ".specify/docs" "docs folder"
    fi

    # Copy templates (excluding commands subfolder)
    if [[ -d "$SOURCE_DIR/templates" ]]; then
        mkdir -p "$project_path/.specify/templates"

        # Copy all template files except commands directory
        for item in "$SOURCE_DIR/templates"/*; do
            if [[ -f "$item" ]] || [[ -d "$item" && "$(basename "$item")" != "commands" ]]; then
                copy_files "$item" ".specify/templates/$(basename "$item")" "templates/$(basename "$item")"
            fi
        done

        log "Copied templates (excluding commands subfolder)"
    fi

    # Copy scripts based on script type
    if [[ "$SCRIPT_TYPE" == "sh" ]]; then
        if [[ -d "$SOURCE_DIR/scripts/bash" ]]; then
            copy_files "$SOURCE_DIR/scripts/bash" ".specify/scripts/bash" "bash scripts"
        fi
    else
        if [[ -d "$SOURCE_DIR/scripts/powershell" ]]; then
            copy_files "$SOURCE_DIR/scripts/powershell" ".specify/scripts/powershell" "PowerShell scripts"
        fi
    fi

    # Generate AI-specific commands from templates
    generate_ai_commands() {
        local templates_dir="$SOURCE_DIR/templates/commands"

        if [[ ! -d "$templates_dir" ]]; then
            log "No command templates found, skipping AI command generation"
            return
        fi

        # IMPORTANT: All spec-kit commands are isolated in spec-kit/ subfolders
        # This ensures user's custom commands in parent directories are NEVER overwritten
        # Pattern: .{assistant}/commands/spec-kit/ for all assistants
        case "$AI_ASSISTANT" in
            claude)
                mkdir -p "$project_path/.claude/commands/spec-kit"
                local target_dir="$project_path/.claude/commands/spec-kit"
                local arg_format='$ARGUMENTS'
                local ext="md"
                ;;
            gemini)
                mkdir -p "$project_path/.gemini/commands/spec-kit"
                local target_dir="$project_path/.gemini/commands/spec-kit"
                local arg_format='{{args}}'
                local ext="toml"
                ;;
            copilot)
                mkdir -p "$project_path/.github/prompts/spec-kit"
                local target_dir="$project_path/.github/prompts/spec-kit"
                local arg_format='$ARGUMENTS'
                local ext="prompt.md"
                ;;
            cursor)
                mkdir -p "$project_path/.cursor/commands/spec-kit"
                local target_dir="$project_path/.cursor/commands/spec-kit"
                local arg_format='$ARGUMENTS'
                local ext="md"
                ;;
        esac

        log "Generating $AI_ASSISTANT commands in $target_dir"

        for template_file in "$templates_dir"/*.md; do
            if [[ -f "$template_file" ]]; then
                local name=$(basename "$template_file" .md)
                local output_file="$target_dir/$name.$ext"

                if [[ "$DESTROY" == true ]] || [[ ! -f "$output_file" ]]; then
                    # Read template and apply substitutions
                    local content=$(cat "$template_file")

                    content=${content//\/memory\//.specify\/memory\/}
                    content=${content//memory\//.specify\/memory\/}
                    content=${content//\/templates\//.specify\/templates\/}
                    content=${content//templates\//.specify\/templates\/}
                    content=${content//\/scripts\//.specify\/scripts\/}
                    content=${content//scripts\//.specify\/scripts\/}

                    # Apply script command substitution
                    if [[ "$SCRIPT_TYPE" == "sh" ]]; then
                        local script_cmd=".specify/$(grep -E '^  sh: ' "$template_file" | sed 's/^  sh: //' || echo '')"
                    else
                        local script_cmd=".specify/$(grep -E '^  ps: ' "$template_file" | sed 's/^  ps: //' || echo '')"
                    fi

                    content=${content//\{SCRIPT\}/$script_cmd}
                    content=${content//\{ARGS\}/$arg_format}
                    content=${content//__AGENT__/$AI_ASSISTANT}

                    # Remove YAML frontmatter scripts section for cleaner output
                    content=$(echo "$content" | awk '
                    BEGIN { in_frontmatter=0; skip_scripts=0 }
                    /^---$/ {
                        if (NR==1) in_frontmatter=1
                        else if (in_frontmatter) in_frontmatter=0
                        print; next
                    }
                    in_frontmatter && /^scripts:$/ { skip_scripts=1; next }
                    in_frontmatter && skip_scripts && /^[a-zA-Z].*:/ { skip_scripts=0 }
                    in_frontmatter && skip_scripts && /^  / { next }
                    { print }
                    ')

                    if [[ "$ext" == "toml" ]]; then
                        # Extract description for TOML format
                        local description=$(echo "$content" | grep -E '^description: ' | sed 's/^description: //' | tr -d '"' || echo "")
                        echo "description = \"$description\"" > "$output_file"
                        echo "" >> "$output_file"
                        echo 'prompt = """' >> "$output_file"
                        echo "$content" >> "$output_file"
                        echo '"""' >> "$output_file"
                    else
                        echo "$content" > "$output_file"
                    fi

                    log "Generated $name.$ext"
                else
                    log "Skipped $name.$ext (already exists, use --destroy to overwrite)"
                fi
            fi
        done
    }

    generate_ai_commands

    # Set executable permissions on .sh scripts
    if [[ "$SCRIPT_TYPE" == "sh" ]]; then
        find "$project_path/.specify/scripts/bash" -name "*.sh" -type f 2>/dev/null | while read -r script; do
            if [[ -f "$script" ]]; then
                chmod +x "$script"
                log "Set executable permission: $script"
            fi
        done
    fi

    # Update .gitignore to include .specify
    update_gitignore() {
        if [[ -f "$project_path/.gitignore" ]]; then
            if ! grep -q "^\.specify$" "$project_path/.gitignore" 2>/dev/null; then
                echo ".specify" >> "$project_path/.gitignore"
                log "Added .specify to existing .gitignore"
            else
                log ".specify already in .gitignore"
            fi
        else
            echo ".specify" > "$project_path/.gitignore"
            log "Created .gitignore with .specify entry"
        fi
    }

    update_gitignore

    echo "Specify project initialized successfully!"
    echo ""
    echo "Next steps:"
    echo "1. Update .specify/memory/CONSTITUTION.md with your project's principles"
    echo "2. Start creating specifications in the specs/ folder"
    echo "3. Use Claude Code commands (if using Claude) or your chosen AI assistant"
}

# ============================================================================
# MAIN EXECUTION
# ============================================================================

# Single-repo mode - execute immediately
if [[ "$ALL_REPOS" == false ]]; then
    process_single_repo "$PROJECT_PATH" "false"
    exit 0
fi

# ============================================================================
# MULTI-REPO MODE FUNCTIONS
# ============================================================================

# Find all repositories containing .specify folders
find_specify_repos() {
    local search_path="$1"
    local max_depth="$2"

    log "Searching for repos with .specify in: $search_path (max depth: $max_depth)"

    # Find .specify directories and get their parent directories
    local repos=()
    while IFS= read -r specify_dir; do
        # Get parent directory of .specify
        local repo_dir=$(dirname "$specify_dir")
        repos+=("$repo_dir")
    done < <(find "$search_path" -maxdepth "$max_depth" -type d -name ".specify" 2>/dev/null)

    if [[ ${#repos[@]} -eq 0 ]]; then
        error "No repositories with .specify folders found in: $search_path"
    fi

    printf '%s\n' "${repos[@]}"
}

# Preview what would be updated
preview_repos() {
    local repos=("$@")
    echo ""
    echo "Found ${#repos[@]} repositories with .specify:"
    local index=1
    for repo in "${repos[@]}"; do
        echo "  $index. $repo"
        ((index++))
    done
    echo ""
    echo "Settings:"
    echo "  AI: $AI_ASSISTANT"
    echo "  Script: $SCRIPT_TYPE"
    echo "  Destroy: $([ "$DESTROY" == true ] && echo "YES (will delete existing .specify directories)" || echo "no")"
    echo ""
    echo "=== PREVIEW MODE ==="
    echo ""

    index=1
    for repo in "${repos[@]}"; do
        local repo_name=$(basename "$repo")
        echo "[$index/${#repos[@]}] Would update: $repo_name"
        process_single_repo "$repo" "true"
        echo ""
        ((index++))
    done
}

# Confirm and execute on all repos
confirm_and_execute() {
    local repos=("$@")

    # Special confirmation for --destroy mode
    if [[ "$DESTROY" == true ]]; then
        echo ""
        echo "**** ARE YOU SURE ****"
        echo ""
        echo "You are about to run --destroy on ALL repositories listed above."
        echo "This will permanently delete .specify directories in MULTIPLE repos."
        echo ""
        read -p "Type \"yes, I'm sure\" to proceed: " -r
        echo ""

        if [[ "$REPLY" != "yes, I'm sure" ]]; then
            echo "Operation cancelled."
            exit 0
        fi
    fi

    echo "Do you want to proceed with these changes? (y/N): "
    read -n 1 -r
    echo ""

    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Operation cancelled."
        exit 0
    fi

    echo ""
    echo "=== EXECUTING CHANGES ==="
    echo ""

    # Execute on each repo
    local success_count=0
    local fail_count=0
    local failed_repos=()

    local index=1
    for repo in "${repos[@]}"; do
        local repo_name=$(basename "$repo")
        echo "[$index/${#repos[@]}] Processing: $repo_name"

        if process_single_repo "$repo" "false"; then
            ((success_count++))
        else
            ((fail_count++))
            failed_repos+=("$repo")
        fi

        echo ""
        ((index++))
    done

    # Print summary
    print_summary "$success_count" "$fail_count" "${failed_repos[@]}"
}

# Print summary of results
print_summary() {
    local success_count="$1"
    local fail_count="$2"
    shift 2
    local failed_repos=("$@")

    echo ""
    echo "========================================"
    echo "Summary:"
    echo "  ✓ Success: $success_count"
    echo "  ✗ Failed: $fail_count"

    if [[ $fail_count -gt 0 ]]; then
        echo ""
        echo "Failed repositories:"
        for repo in "${failed_repos[@]}"; do
            echo "  - $repo"
        done
        exit 1
    else
        echo ""
        echo "All repositories initialized successfully!"
        exit 0
    fi
}

# ============================================================================
# MULTI-REPO MAIN FLOW
# ============================================================================

# Find all repos with .specify
repos=($(find_specify_repos "$SEARCH_PATH" "$MAX_DEPTH"))

# If --execute is NOT specified, always preview first
if [[ "$EXECUTE" != true ]]; then
    preview_repos "${repos[@]}"
    confirm_and_execute "${repos[@]}"
else
    # Skip preview, execute directly
    log "Executing on ${#repos[@]} repositories..."
    confirm_and_execute "${repos[@]}"
fi