#!/usr/bin/env bash
# Batch update script for installing/updating specify-cli and running specify update in multiple directories
#
# This script automates two main tasks:
# 1. Installs/updates the specify-cli tool from GitHub
# 2. Runs 'specify update' command in configured project directories

set -e

# Enable strict error handling
set -u
set -o pipefail

#==============================================================================
# Configuration and Global Variables
#==============================================================================

# Get script directory and load common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Command line arguments
CONFIG_FILE=""
FORCE_INSTALL=false

#==============================================================================
# Utility Functions
#==============================================================================

log_info() {
    echo "INFO: $1"
}

log_success() {
    echo "✓ $1"
}

log_error() {
    echo "ERROR: $1" >&2
}

log_warning() {
    echo "WARNING: $1" >&2
}

#==============================================================================
# Core Functions
#==============================================================================

# Check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Install/update specify-cli
install_specify_cli() {
    local force_flag="$1"
    
    log_info "Installing/updating specify-cli..."
    
    # Check if uv is installed
    if ! command_exists "uv"; then
        log_error "uv is not installed. Please install uv first: https://docs.astral.sh/uv/"
        return 1
    fi
    
    local install_args=("tool" "install" "specify-cli" "--from" "git+https://github.com/rj-wangbin6/spec-kit.git")
    
    if [[ "$force_flag" == "true" ]]; then
        install_args+=("--force")
    fi
    
    if uv "${install_args[@]}"; then
        log_success "Successfully installed/updated specify-cli"
        return 0
    else
        log_error "Failed to install/update specify-cli"
        return 1
    fi
}

# Read project directories from config file
get_project_directories() {
    local config_file_path="$1"
    
    if [[ ! -f "$config_file_path" ]]; then
        log_error "Configuration file not found: $config_file_path"
        log_info "Please create a configuration file with project directory paths, one per line."
        log_info "Example config file content:"
        log_info "  # Project directories"
        log_info "  /home/user/projects/project1"
        log_info "  /home/user/projects/project2"
        log_info "  /opt/dev/another-project"
        return 1
    fi
    
    # Read non-empty, non-comment lines from config file
    local directories=()
    while IFS= read -r line; do
        # Skip empty lines and comments
        if [[ -n "$line" ]] && [[ ! "$line" =~ ^[[:space:]]*# ]]; then
            # Trim whitespace
            line=$(echo "$line" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
            if [[ -n "$line" ]]; then
                directories+=("$line")
            fi
        fi
    done < "$config_file_path"
    
    log_info "Found ${#directories[@]} project directories in config file"
    printf '%s\n' "${directories[@]}"
}

# Run specify update in a project directory
invoke_specify_update() {
    local project_directory="$1"
    
    log_info "Running 'specify update' in: $project_directory"
    
    if [[ ! -d "$project_directory" ]]; then
        log_warning "Directory does not exist: $project_directory"
        return 1
    fi
    
    # Save current directory and change to project directory
    local original_dir
    original_dir=$(pwd)
    
    if ! cd "$project_directory"; then
        log_error "Failed to change to directory: $project_directory"
        return 1
    fi
    
    # Check if specify command exists
    if ! command_exists "specify"; then
        log_error "specify command not found. Make sure specify-cli is properly installed."
        cd "$original_dir"
        return 1
    fi
    
    # Run specify init
    if specify init --here --force --ai copilot --script ps; then
        log_success "Successfully ran specify update in $project_directory"
        cd "$original_dir"
        return 0
    else
        log_error "Failed to run specify update in $project_directory"
        cd "$original_dir"
        return 1
    fi
}

#==============================================================================
# Main Function
#==============================================================================

main() {
    log_info "=== Batch Update Script for specify-cli ==="
    
    # Parse command line arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -c|--config)
                CONFIG_FILE="$2"
                shift 2
                ;;
            -f|--force)
                FORCE_INSTALL=true
                shift
                ;;
            -h|--help)
                echo "Usage: $0 [OPTIONS]"
                echo "Batch update script for specify-cli"
                echo ""
                echo "Options:"
                echo "  -c, --config FILE    Path to configuration file containing project directories"
                echo "  -f, --force          Force reinstall of specify-cli tool"
                echo "  -h, --help           Show this help message"
                echo ""
                echo "Configuration file should contain one project directory path per line."
                echo "Lines starting with '#' are treated as comments and ignored."
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                echo "Use -h or --help for usage information"
                exit 1
                ;;
        esac
    done
    
    # Determine config file path
    if [[ -z "$CONFIG_FILE" ]]; then
        CONFIG_FILE="$SCRIPT_DIR/project-dirs.conf"
    fi
    
    log_info "Using config file: $CONFIG_FILE"
    
    # Install/update specify-cli
    if ! install_specify_cli "$FORCE_INSTALL"; then
        log_error "Failed to install/update specify-cli. Exiting."
        exit 1
    fi
    
    # Get project directories
    local project_dirs
    project_dirs=$(get_project_directories "$CONFIG_FILE") || {
        log_error "Failed to read project directories from config file"
        exit 1
    }
    
    if [[ -z "$project_dirs" ]]; then
        log_warning "No project directories found. Nothing to update."
        exit 0
    fi
    
    # Convert to array
    IFS=$'\n' read -rd '' -a project_dirs_array <<<"$project_dirs" || true
    
    # Process each directory
    local success_count=0
    local fail_count=0
    
    for dir in "${project_dirs_array[@]}"; do
        echo ""
        if invoke_specify_update "$dir"; then
            ((success_count++))
        else
            ((fail_count++))
        fi
    done
    
    echo ""
    log_info "=== Summary ==="
    log_info "Successful updates: $success_count"
    log_info "Failed updates: $fail_count"
    log_info "Total processed: $((success_count + fail_count))"
    
    if [[ $fail_count -eq 0 ]]; then
        log_success "All updates completed successfully!"
        exit 0
    else
        log_error "Some updates failed. Please check the logs above."
        exit 1
    fi
}

# Execute main function if script is run directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi