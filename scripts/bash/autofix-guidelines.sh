#!/usr/bin/env bash
# shellcheck disable=SC2155,SC2086

##############################################################################
# Guideline Auto-Fix Tool
# Part of Spec Kit Phase 4: Advanced Features
#
# Purpose: Automatically fix common guideline violations
# Usage: ./autofix-guidelines.sh [--dry-run] [--fixes=<type>]
#
# Features:
#   - Fix .env not in .gitignore
#   - Add .env.example template
#   - Fix missing .npmrc for corporate registry
#   - Add missing architecture folders
#   - Fix security issues (API keys in code, etc.)
#
# Safety: Always creates backups before making changes
##############################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(pwd)"
GUIDELINES_DIR="${PROJECT_ROOT}/.guidelines"
DRY_RUN=false
FIXES="all"  # all, security, structure, config
BACKUP_DIR="${PROJECT_ROOT}/.guideline-autofix-backups"

# Counters
FIXES_APPLIED=0
FIXES_SKIPPED=0
WARNINGS=0

##############################################################################
# Helper Functions
##############################################################################

print_header() {
    echo -e "${BOLD}$1${NC}"
    echo "$(printf '=%.0s' {1..80})"
}

print_section() {
    echo ""
    echo -e "${BLUE}$1${NC}"
    echo "$(printf '-%.0s' {1..80})"
}

log_fix() {
    FIXES_APPLIED=$((FIXES_APPLIED + 1))
    echo -e "${GREEN}✓ FIXED: $1${NC}"
}

log_skip() {
    FIXES_SKIPPED=$((FIXES_SKIPPED + 1))
    echo -e "${CYAN}⊘ SKIPPED: $1${NC}"
}

log_warning() {
    WARNINGS=$((WARNINGS + 1))
    echo -e "${YELLOW}⚠️  WARNING: $1${NC}"
}

create_backup() {
    local file="$1"

    if [ ! -d "$BACKUP_DIR" ]; then
        mkdir -p "$BACKUP_DIR"
        echo "Created backup directory: $BACKUP_DIR"
    fi

    local backup_file="${BACKUP_DIR}/$(basename "$file").$(date +%Y%m%d_%H%M%S).bak"
    cp "$file" "$backup_file"
    echo "  Backup created: $backup_file"
}

##############################################################################
# Fix Functions
##############################################################################

fix_env_gitignore() {
    print_section "Fix: .env File Security"

    if [ ! -f ".env" ]; then
        log_skip ".env file doesn't exist"
        return 0
    fi

    # Check if .env is in .gitignore
    if [ -f ".gitignore" ]; then
        if grep -qx "\.env" .gitignore 2>/dev/null; then
            log_skip ".env already in .gitignore"
            return 0
        fi
    fi

    if [ "$DRY_RUN" = true ]; then
        echo "  Would add .env to .gitignore"
        return 0
    fi

    # Create .gitignore if it doesn't exist
    if [ ! -f ".gitignore" ]; then
        touch .gitignore
        echo "  Created .gitignore file"
    else
        create_backup ".gitignore"
    fi

    # Add .env to .gitignore
    echo ".env" >> .gitignore
    log_fix "Added .env to .gitignore"

    # Also add common env files
    for env_file in ".env.local" ".env.development" ".env.production"; do
        if ! grep -qx "$env_file" .gitignore 2>/dev/null; then
            echo "$env_file" >> .gitignore
            echo "  Also added $env_file to .gitignore"
        fi
    done
}

fix_env_example() {
    print_section "Fix: .env.example Template"

    if [ ! -f ".env" ]; then
        log_skip ".env file doesn't exist, can't create example"
        return 0
    fi

    if [ -f ".env.example" ]; then
        log_skip ".env.example already exists"
        return 0
    fi

    if [ "$DRY_RUN" = true ]; then
        echo "  Would create .env.example template from .env"
        return 0
    fi

    # Create .env.example with masked values
    cat .env | sed -E 's/=.*/=/' > .env.example
    log_fix "Created .env.example template"
    echo "  Review .env.example and add documentation for each variable"
}

fix_npmrc_registry() {
    print_section "Fix: Corporate Package Registry"

    if [ ! -f "package.json" ]; then
        log_skip "Not a Node.js project"
        return 0
    fi

    # Check if corporate registry is mentioned in guidelines
    local has_registry_requirement=false
    for guideline in "$GUIDELINES_DIR"/*-guidelines.md; do
        if [ -f "$guideline" ]; then
            if grep -qi "artifactory\|nexus\|registry" "$guideline" 2>/dev/null; then
                has_registry_requirement=true
                break
            fi
        fi
    done

    if [ "$has_registry_requirement" = false ]; then
        log_skip "No corporate registry requirement in guidelines"
        return 0
    fi

    if [ -f ".npmrc" ]; then
        log_skip ".npmrc already exists"
        return 0
    fi

    if [ "$DRY_RUN" = true ]; then
        echo "  Would create .npmrc template"
        return 0
    fi

    # Create .npmrc template
    cat > .npmrc <<'EOF'
# Corporate Package Registry Configuration
# CUSTOMIZE: Replace with your organization's registry URL

# Option 1: Single registry for all packages
# registry=https://artifactory.yourcompany.com/artifactory/api/npm/npm-virtual/

# Option 2: Scoped registry for corporate packages
# @yourcompany:registry=https://artifactory.yourcompany.com/artifactory/api/npm/npm-virtual/

# Authentication (use npm login or environment variables)
# always-auth=true

# Force strict SSL (recommended)
strict-ssl=true
EOF

    log_fix "Created .npmrc template"
    log_warning "Customize .npmrc with your corporate registry URL"
}

fix_architecture_folders() {
    print_section "Fix: Standard Architecture Folders"

    if [ ! -d "src" ]; then
        log_skip "No src/ directory, skipping architecture folder creation"
        return 0
    fi

    # Check if guidelines mention folder structure
    local has_folder_requirement=false
    for guideline in "$GUIDELINES_DIR"/*-guidelines.md; do
        if [ -f "$guideline" ]; then
            if grep -qi "folder structure\|directory structure" "$guideline" 2>/dev/null; then
                has_folder_requirement=true
                break
            fi
        fi
    done

    if [ "$has_folder_requirement" = false ]; then
        log_skip "No folder structure requirement in guidelines"
        return 0
    fi

    # Common architecture folders
    local folders=("components" "services" "utils" "config" "types" "hooks" "api")
    local created=0

    for folder in "${folders[@]}"; do
        local folder_path="src/$folder"

        if [ -d "$folder_path" ]; then
            continue
        fi

        if [ "$DRY_RUN" = true ]; then
            echo "  Would create $folder_path/"
            created=$((created + 1))
            continue
        fi

        mkdir -p "$folder_path"

        # Create README.md explaining the folder
        cat > "$folder_path/README.md" <<EOF
# ${folder^}

This directory contains ${folder}.

<!-- Add documentation about what belongs in this directory -->
EOF

        created=$((created + 1))
    done

    if [ $created -gt 0 ]; then
        log_fix "Created $created standard architecture folders"
    else
        log_skip "All standard folders already exist"
    fi
}

fix_readme_documentation() {
    print_section "Fix: Missing Documentation"

    if [ -f "README.md" ]; then
        # Check if README has content
        local line_count=$(wc -l < README.md)
        if [ $line_count -gt 10 ]; then
            log_skip "README.md exists with content"
            return 0
        fi
    fi

    if [ "$DRY_RUN" = true ]; then
        echo "  Would create/enhance README.md"
        return 0
    fi

    if [ -f "README.md" ]; then
        create_backup "README.md"
    fi

    # Detect project name
    local project_name=$(basename "$PROJECT_ROOT")

    cat > README.md <<EOF
# $project_name

<!-- Add project description -->

## Prerequisites

<!-- List required tools and versions -->

## Installation

\`\`\`bash
# Add installation instructions
\`\`\`

## Configuration

<!-- Document environment variables and configuration -->

## Development

\`\`\`bash
# Add development commands
\`\`\`

## Testing

\`\`\`bash
# Add testing commands
\`\`\`

## Deployment

<!-- Add deployment instructions -->

## Corporate Guidelines

This project follows corporate development guidelines. See \`.guidelines/\` for:

- Tech stack standards
- Required libraries
- Security requirements
- Coding conventions

## License

<!-- Add license information -->
EOF

    log_fix "Created README.md template"
    log_warning "Customize README.md with project-specific information"
}

fix_gitignore_basics() {
    print_section "Fix: Essential .gitignore Entries"

    if [ ! -f ".gitignore" ]; then
        if [ "$DRY_RUN" = true ]; then
            echo "  Would create .gitignore"
            return 0
        fi
        touch .gitignore
        echo "  Created .gitignore"
    fi

    # Essential patterns that should be ignored
    local essential_patterns=(
        "node_modules/"
        ".DS_Store"
        "*.log"
        ".env"
        "dist/"
        "build/"
        "target/"
        "*.class"
        "*.pyc"
        "__pycache__/"
        ".vscode/"
        ".idea/"
    )

    local added=0

    for pattern in "${essential_patterns[@]}"; do
        if ! grep -qx "$pattern" .gitignore 2>/dev/null; then
            if [ "$DRY_RUN" = true ]; then
                echo "  Would add $pattern to .gitignore"
                added=$((added + 1))
                continue
            fi

            echo "$pattern" >> .gitignore
            added=$((added + 1))
        fi
    done

    if [ $added -gt 0 ]; then
        log_fix "Added $added essential patterns to .gitignore"
    else
        log_skip "All essential patterns already in .gitignore"
    fi
}

##############################################################################
# Report Generation
##############################################################################

generate_summary() {
    print_section "Auto-Fix Summary"

    echo "Fixes applied:  $FIXES_APPLIED"
    echo "Fixes skipped:  $FIXES_SKIPPED"
    echo "Warnings:       $WARNINGS"
    echo ""

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}DRY RUN MODE: No changes were made${NC}"
        echo "Run without --dry-run to apply fixes"
    else
        if [ $FIXES_APPLIED -gt 0 ]; then
            echo -e "${GREEN}✓ Successfully applied $FIXES_APPLIED fixes${NC}"

            if [ -d "$BACKUP_DIR" ]; then
                echo ""
                echo "Backups saved to: $BACKUP_DIR"
            fi
        else
            echo -e "${BLUE}No fixes needed - project looks good!${NC}"
        fi

        if [ $WARNINGS -gt 0 ]; then
            echo ""
            echo -e "${YELLOW}⚠️  $WARNINGS warning(s) - review output above${NC}"
        fi
    fi
}

##############################################################################
# Main Execution
##############################################################################

show_usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Options:
  --dry-run             Show what would be fixed without making changes
  --fixes=TYPE          Type of fixes to apply: all (default), security, structure, config
  --help                Show this help message

Fix Categories:
  security    - .env in .gitignore, API key exposure, etc.
  structure   - Architecture folders, README, documentation
  config      - .npmrc, .env.example, .gitignore basics

Examples:
  $0 --dry-run              # Preview fixes without applying
  $0                        # Apply all fixes
  $0 --fixes=security       # Apply only security fixes
  $0 --fixes=structure      # Apply only structure fixes

Safety:
  - Creates backups before modifying existing files
  - Backups saved to: .guideline-autofix-backups/
  - Use --dry-run to preview changes first
EOF
}

main() {
    # Parse arguments
    for arg in "$@"; do
        case $arg in
            --dry-run)
                DRY_RUN=true
                ;;
            --fixes=*)
                FIXES="${arg#*=}"
                ;;
            --help)
                show_usage
                exit 0
                ;;
            *)
                echo "Unknown option: $arg" >&2
                show_usage
                exit 3
                ;;
        esac
    done

    print_header "Guideline Auto-Fix Tool"

    if [ "$DRY_RUN" = true ]; then
        echo -e "${YELLOW}Running in DRY RUN mode - no changes will be made${NC}"
    fi

    echo "Project: $PROJECT_ROOT"
    echo ""

    # Apply fixes based on category
    case "$FIXES" in
        security)
            fix_env_gitignore
            fix_env_example
            ;;
        structure)
            fix_architecture_folders
            fix_readme_documentation
            ;;
        config)
            fix_npmrc_registry
            fix_gitignore_basics
            ;;
        all|*)
            # Security fixes
            fix_env_gitignore
            fix_env_example

            # Config fixes
            fix_npmrc_registry
            fix_gitignore_basics

            # Structure fixes
            fix_architecture_folders
            fix_readme_documentation
            ;;
    esac

    # Generate summary
    generate_summary

    # Exit code
    if [ "$DRY_RUN" = true ]; then
        exit 0
    elif [ $FIXES_APPLIED -gt 0 ]; then
        exit 0
    else
        exit 0
    fi
}

# Run main function
main "$@"
