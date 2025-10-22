#!/bin/bash
# Version management script for Specify CLI

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Files to update
PYPROJECT_FILE="$REPO_ROOT/pyproject.toml"
CHANGELOG_FILE="$REPO_ROOT/CHANGELOG.md"
INIT_FILE="$REPO_ROOT/src/specify_cli/__init__.py"

# Help function
show_help() {
    cat << EOF
Usage: ${0##*/} [COMMAND] [OPTIONS]

Version management for Specify CLI

COMMANDS:
    current             Show current version
    bump TYPE           Bump version (TYPE: major, minor, patch)
    set VERSION         Set specific version (e.g., 1.2.3)
    validate            Validate version consistency across files
    tag                 Create git tag for current version
    
OPTIONS:
    -h, --help          Show this help message
    -n, --dry-run       Show what would be done without making changes
    -m, --message MSG   Custom commit/tag message

EXAMPLES:
    ${0##*/} current                    # Show current version
    ${0##*/} bump patch                 # Bump patch version (0.0.20 -> 0.0.21)
    ${0##*/} bump minor                 # Bump minor version (0.0.20 -> 0.1.0)
    ${0##*/} bump major                 # Bump major version (0.0.20 -> 1.0.0)
    ${0##*/} set 1.0.0                  # Set version to 1.0.0
    ${0##*/} validate                   # Check version consistency
    ${0##*/} tag -m "Release v0.0.21"  # Create git tag

EOF
}

# Get current version from pyproject.toml
get_current_version() {
    grep -E '^version = ' "$PYPROJECT_FILE" | sed -E 's/version = "(.*)"/\1/'
}

# Parse version into components
parse_version() {
    local version=$1
    local IFS='.'
    read -r -a parts <<< "$version"
    MAJOR="${parts[0]}"
    MINOR="${parts[1]}"
    PATCH="${parts[2]}"
}

# Bump version
bump_version() {
    local bump_type=$1
    local current_version=$(get_current_version)
    
    parse_version "$current_version"
    
    case $bump_type in
        major)
            MAJOR=$((MAJOR + 1))
            MINOR=0
            PATCH=0
            ;;
        minor)
            MINOR=$((MINOR + 1))
            PATCH=0
            ;;
        patch)
            PATCH=$((PATCH + 1))
            ;;
        *)
            echo -e "${RED}Error: Invalid bump type '$bump_type'${NC}"
            echo "Valid types: major, minor, patch"
            exit 1
            ;;
    esac
    
    NEW_VERSION="$MAJOR.$MINOR.$PATCH"
    echo "$NEW_VERSION"
}

# Update version in file
update_version_in_file() {
    local file=$1
    local old_version=$2
    local new_version=$3
    local dry_run=$4
    
    if [ ! -f "$file" ]; then
        echo -e "${YELLOW}Warning: File not found: $file${NC}"
        return 1
    fi
    
    if [ "$dry_run" = true ]; then
        echo -e "${BLUE}Would update $file: $old_version -> $new_version${NC}"
        return 0
    fi
    
    # Different patterns for different files
    case "$file" in
        */pyproject.toml)
            sed -i.bak "s/version = \"$old_version\"/version = \"$new_version\"/" "$file"
            ;;
        */__init__.py)
            if grep -q "__version__" "$file"; then
                sed -i.bak "s/__version__ = \"$old_version\"/__version__ = \"$new_version\"/" "$file"
            fi
            ;;
        */CHANGELOG.md)
            # Add new version section at the top (after header)
            local date=$(date +%Y-%m-%d)
            sed -i.bak "/^## \[/i\\
\\
## [$new_version] - $date\\
\\
### Added\\
- New features in this release\\
\\
### Changed\\
- Changes in this release\\
\\
### Fixed\\
- Bug fixes in this release\\
" "$file"
            ;;
    esac
    
    # Remove backup file
    rm -f "${file}.bak"
    
    echo -e "${GREEN}✓ Updated $file${NC}"
}

# Validate version consistency
validate_version() {
    echo -e "${BLUE}Validating version consistency...${NC}"
    
    local pyproject_version=$(get_current_version)
    local issues=0
    
    echo "pyproject.toml: $pyproject_version"
    
    # Check __init__.py if it has __version__
    if [ -f "$INIT_FILE" ] && grep -q "__version__" "$INIT_FILE"; then
        local init_version=$(grep "__version__" "$INIT_FILE" | sed -E 's/.*"(.*)".*/\1/')
        echo "__init__.py: $init_version"
        
        if [ "$init_version" != "$pyproject_version" ]; then
            echo -e "${RED}✗ Version mismatch in __init__.py${NC}"
            issues=$((issues + 1))
        fi
    fi
    
    # Check CHANGELOG.md
    if [ -f "$CHANGELOG_FILE" ]; then
        if grep -q "## \[$pyproject_version\]" "$CHANGELOG_FILE"; then
            echo -e "${GREEN}✓ CHANGELOG.md has entry for $pyproject_version${NC}"
        else
            echo -e "${YELLOW}! CHANGELOG.md missing entry for $pyproject_version${NC}"
            issues=$((issues + 1))
        fi
    fi
    
    if [ $issues -eq 0 ]; then
        echo -e "${GREEN}✓ All versions are consistent${NC}"
        return 0
    else
        echo -e "${RED}✗ Found $issues version inconsistencies${NC}"
        return 1
    fi
}

# Create git tag
create_git_tag() {
    local version=$(get_current_version)
    local message=${1:-"Release v$version"}
    local dry_run=$2
    
    local tag="v$version"
    
    if git rev-parse "$tag" >/dev/null 2>&1; then
        echo -e "${YELLOW}Warning: Tag $tag already exists${NC}"
        return 1
    fi
    
    if [ "$dry_run" = true ]; then
        echo -e "${BLUE}Would create tag: $tag${NC}"
        echo -e "${BLUE}Message: $message${NC}"
        return 0
    fi
    
    git tag -a "$tag" -m "$message"
    echo -e "${GREEN}✓ Created tag $tag${NC}"
    echo -e "${YELLOW}Push with: git push origin $tag${NC}"
}

# Main command dispatcher
main() {
    local command=${1:-help}
    local dry_run=false
    local message=""
    
    # Parse options
    shift || true
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            -n|--dry-run)
                dry_run=true
                shift
                ;;
            -m|--message)
                message="$2"
                shift 2
                ;;
            *)
                break
                ;;
        esac
    done
    
    case $command in
        current)
            local version=$(get_current_version)
            echo "Current version: $version"
            ;;
            
        bump)
            local bump_type=${1:-patch}
            local current_version=$(get_current_version)
            local new_version=$(bump_version "$bump_type")
            
            echo -e "${YELLOW}Bumping version: $current_version -> $new_version${NC}"
            
            # Update all files
            update_version_in_file "$PYPROJECT_FILE" "$current_version" "$new_version" "$dry_run"
            update_version_in_file "$INIT_FILE" "$current_version" "$new_version" "$dry_run"
            update_version_in_file "$CHANGELOG_FILE" "$current_version" "$new_version" "$dry_run"
            
            if [ "$dry_run" = false ]; then
                echo -e "${GREEN}✓ Version bumped to $new_version${NC}"
                echo -e "${YELLOW}Don't forget to commit these changes!${NC}"
            fi
            ;;
            
        set)
            local new_version=$1
            if [ -z "$new_version" ]; then
                echo -e "${RED}Error: Version required${NC}"
                echo "Usage: $0 set VERSION"
                exit 1
            fi
            
            # Validate version format
            if ! [[ "$new_version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
                echo -e "${RED}Error: Invalid version format '$new_version'${NC}"
                echo "Expected format: MAJOR.MINOR.PATCH (e.g., 1.0.0)"
                exit 1
            fi
            
            local current_version=$(get_current_version)
            echo -e "${YELLOW}Setting version: $current_version -> $new_version${NC}"
            
            # Update all files
            update_version_in_file "$PYPROJECT_FILE" "$current_version" "$new_version" "$dry_run"
            update_version_in_file "$INIT_FILE" "$current_version" "$new_version" "$dry_run"
            update_version_in_file "$CHANGELOG_FILE" "$current_version" "$new_version" "$dry_run"
            
            if [ "$dry_run" = false ]; then
                echo -e "${GREEN}✓ Version set to $new_version${NC}"
                echo -e "${YELLOW}Don't forget to commit these changes!${NC}"
            fi
            ;;
            
        validate)
            validate_version
            ;;
            
        tag)
            if [ -z "$message" ]; then
                local version=$(get_current_version)
                message="Release v$version"
            fi
            create_git_tag "$message" "$dry_run"
            ;;
            
        help|--help|-h)
            show_help
            ;;
            
        *)
            echo -e "${RED}Error: Unknown command '$command'${NC}"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
