#!/bin/bash

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
SOURCE_DIR="$HOME/git/spec-kit"

DEFAULT_AI="claude"
DEFAULT_SCRIPT="sh"
DESTROY=false

usage() {
    echo "Usage: $0 <project_path> [options]"
    echo ""
    echo "Initialize a new Specify project by copying files from ~/git/spec-kit"
    echo ""
    echo "Arguments:"
    echo "  project_path    Path to create or initialize project"
    echo ""
    echo "Options:"
    echo "  --ai ASSISTANT  AI assistant to use: claude, gemini, copilot, cursor (default: claude)"
    echo "  --script TYPE   Script type: sh, ps (default: sh)"
    echo "  --destroy       Delete all existing project files and start fresh"
    echo "  --help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 my-project"
    echo "  $0 my-project --ai claude --script sh"
    echo "  $0 . --destroy"
}

log() {
    echo "[INFO] $*"
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

if [[ -z "$PROJECT_PATH" ]]; then
    usage
    exit 1
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

# Resolve project path
PROJECT_PATH=$(realpath "$PROJECT_PATH")

log "Initializing Specify project at: $PROJECT_PATH"
log "AI Assistant: $AI_ASSISTANT"
log "Script Type: $SCRIPT_TYPE"
log "Source: $SOURCE_DIR"

# Create project directory if it doesn't exist
if [[ ! -d "$PROJECT_PATH" ]]; then
    mkdir -p "$PROJECT_PATH"
    log "Created project directory: $PROJECT_PATH"
fi

cd "$PROJECT_PATH"

# Destroy existing files if --destroy flag is used
destroy_existing() {
    if [[ "$DESTROY" == true ]]; then
        # Check if .specify directory exists
        if [[ -d ".specify" ]]; then
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
            if [[ -f ".specify/memory/constitution.md" ]]; then
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
        if [[ "$preserve_constitution" == true ]] && [[ -f ".specify/memory/constitution.md" ]]; then
            constitution_backup=$(mktemp)
            cp ".specify/memory/constitution.md" "$constitution_backup"
        fi

        # Remove only .specify directory
        rm -rf .specify 2>/dev/null || true
        log "Existing .specify directory destroyed"

        # Set global flags for later use
        export PRESERVE_CONSTITUTION="$preserve_constitution"
        export CONSTITUTION_BACKUP="$constitution_backup"
    fi
}

destroy_existing

# Create .specify directory structure
mkdir -p .specify/{memory,scripts,templates}
log "Created .specify directory structure"

# Create scripts subdirectory based on script type
if [[ "$SCRIPT_TYPE" == "sh" ]]; then
    mkdir -p .specify/scripts/bash
else
    mkdir -p .specify/scripts/powershell
fi

# Create specs directory if it doesn't exist
if [[ ! -d "specs" ]]; then
    mkdir -p specs
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
if [[ "$DESTROY" != true ]] && [[ -f ".specify/memory/constitution.md" ]]; then
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
    cp "$CONSTITUTION_BACKUP" ".specify/memory/constitution.md"
    rm -f "$CONSTITUTION_BACKUP"
    log "Restored preserved constitution.md"
fi

# Copy documentation files
copy_files "$SOURCE_DIR/README.md" ".specify/README.md" "README.md"
copy_files "$SOURCE_DIR/README-WORKFLOW-GUIDE.md" ".specify/README-WORKFLOW-GUIDE.md" "README-WORKFLOW-GUIDE.md"

# Copy docs folder if it exists
if [[ -d "$SOURCE_DIR/docs" ]]; then
    copy_files "$SOURCE_DIR/docs" ".specify/docs" "docs folder"
fi

# Copy templates (excluding commands subfolder)
if [[ -d "$SOURCE_DIR/templates" ]]; then
    mkdir -p ".specify/templates"

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

    case "$AI_ASSISTANT" in
        claude)
            mkdir -p ".claude/commands/spec-kit"
            local target_dir=".claude/commands/spec-kit"
            local arg_format='$ARGUMENTS'
            local ext="md"
            ;;
        gemini)
            mkdir -p ".gemini/commands"
            local target_dir=".gemini/commands"
            local arg_format='{{args}}'
            local ext="toml"
            ;;
        copilot)
            mkdir -p ".github/prompts"
            local target_dir=".github/prompts"
            local arg_format='$ARGUMENTS'
            local ext="prompt.md"
            ;;
        cursor)
            mkdir -p ".cursor/commands"
            local target_dir=".cursor/commands"
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
    find ".specify/scripts/bash" -name "*.sh" -type f 2>/dev/null | while read -r script; do
        if [[ -f "$script" ]]; then
            chmod +x "$script"
            log "Set executable permission: $script"
        fi
    done
fi

# Update .gitignore to include .specify
update_gitignore() {
    if [[ -f ".gitignore" ]]; then
        if ! grep -q "^\.specify$" ".gitignore" 2>/dev/null; then
            echo ".specify" >> ".gitignore"
            log "Added .specify to existing .gitignore"
        else
            log ".specify already in .gitignore"
        fi
    else
        echo ".specify" > ".gitignore"
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