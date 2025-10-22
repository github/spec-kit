#!/usr/bin/env bash
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
GRAY='\033[0;90m'
NC='\033[0m' # No Color

success() { echo -e "${GREEN}✅ $*${NC}"; }
info() { echo -e "${CYAN}ℹ️  $*${NC}"; }
warning() { echo -e "${YELLOW}⚠️  $*${NC}"; }
error() { echo -e "${RED}❌ $*${NC}"; }

# Default values
SPEC_KIT_PATH="${SPEC_KIT_PATH:-$HOME/git/spec-kit-4applens}"
SKIP_PROMPT_FILE=false
FORCE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --spec-kit-path)
            SPEC_KIT_PATH="$2"
            shift 2
            ;;
        --skip-prompt-file)
            SKIP_PROMPT_FILE=true
            shift
            ;;
        --force)
            FORCE=true
            shift
            ;;
        -h|--help)
            cat <<EOF
Usage: $0 [OPTIONS]

Install Specify CLI locally for development and testing.

This script installs the Specify CLI from the local source code in editable mode,
allowing you to test changes immediately. It also copies the GitHub Copilot prompt
file to the current project so you can test the /speckit.bicep command.

OPTIONS:
    --spec-kit-path PATH    Path to spec-kit-4applens repository
                            (default: \$HOME/git/spec-kit-4applens)
    --skip-prompt-file      Skip copying the GitHub Copilot prompt file
    --force                 Force reinstallation even if already installed
    -h, --help              Show this help message

EXAMPLES:
    $0
    Install from default location

    $0 --spec-kit-path "/opt/repos/spec-kit-4applens"
    Install from custom location

    $0 --skip-prompt-file
    Install CLI only, don't copy prompt file

    $0 --force
    Force reinstallation

EOF
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

echo ""
echo -e "${CYAN}================================================${NC}"
echo -e "${CYAN}  Specify CLI - Local Development Installation${NC}"
echo -e "${CYAN}================================================${NC}"
echo ""

# Validate spec-kit path
if [[ ! -d "$SPEC_KIT_PATH" ]]; then
    error "Spec Kit repository not found at: $SPEC_KIT_PATH"
    echo ""
    echo -e "${YELLOW}Please provide the correct path using --spec-kit-path parameter${NC}"
    echo -e "${YELLOW}Example: $0 --spec-kit-path '/home/user/repos/spec-kit-4applens'${NC}"
    exit 1
fi

SPEC_KIT_PATH=$(cd "$SPEC_KIT_PATH" && pwd)  # Get absolute path

info "Spec Kit location: $SPEC_KIT_PATH"
info "Current directory: $PWD"
echo ""

# Check if pyproject.toml exists
if [[ ! -f "$SPEC_KIT_PATH/pyproject.toml" ]]; then
    error "pyproject.toml not found in $SPEC_KIT_PATH"
    echo ""
    echo -e "${YELLOW}This doesn't appear to be a valid Specify CLI repository.${NC}"
    exit 1
fi

# Check if Python is available
info "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    error "Python not found in PATH"
    echo ""
    echo -e "${YELLOW}Please install Python 3.8 or later from https://www.python.org/${NC}"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1)
success "Found: $PYTHON_VERSION"

# Check if pip is available
info "Checking pip installation..."
if ! $PYTHON_CMD -m pip --version &> /dev/null; then
    error "pip not found"
    echo ""
    echo -e "${YELLOW}Please ensure pip is installed and available${NC}"
    exit 1
fi
success "Found pip"

echo ""

# Check if already installed
IS_INSTALLED=false
SKIP_INSTALL=false
if command -v specify &> /dev/null; then
    INSTALLED_VERSION=$(specify --version 2>&1 || echo "unknown")
    IS_INSTALLED=true
    warning "Specify CLI is already installed: $INSTALLED_VERSION"
    
    if [[ "$FORCE" != "true" ]]; then
        echo ""
        read -p "Do you want to reinstall? (y/N): " -n 1 -r
        echo ""
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            info "Skipping installation. Use --force to reinstall without prompting."
            SKIP_INSTALL=true
        fi
    else
        info "Force flag detected, proceeding with reinstallation..."
    fi
else
    info "Specify CLI not currently installed"
fi

# Install the CLI
if [[ "$SKIP_INSTALL" != "true" ]]; then
    echo ""
    echo -e "${CYAN}Installing Specify CLI in editable mode...${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    # Uninstall first if already installed
    if [[ "$IS_INSTALLED" == "true" ]]; then
        info "Uninstalling previous version..."
        $PYTHON_CMD -m pip uninstall -y specify-cli &> /dev/null || true
        success "Previous version uninstalled"
    fi
    
    # Install with bicep extras
    info "Running: $PYTHON_CMD -m pip install -e \"$SPEC_KIT_PATH[bicep]\""
    if $PYTHON_CMD -m pip install -e "$SPEC_KIT_PATH[bicep]"; then
        echo ""
        success "Specify CLI installed successfully!"
        
        # Verify installation
        info "Verifying installation..."
        if command -v specify &> /dev/null; then
            NEW_VERSION=$(specify --version 2>&1)
            success "Version: $NEW_VERSION"
        else
            warning "specify command not found in PATH. You may need to restart your shell."
        fi
    else
        error "Installation failed"
        exit 1
    fi
fi

# Copy GitHub Copilot prompt file
if [[ "$SKIP_PROMPT_FILE" != "true" ]]; then
    echo ""
    echo -e "${CYAN}Setting up GitHub Copilot integration...${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    PROMPT_SOURCE_PATH="$SPEC_KIT_PATH/.github/prompts/speckit.bicep.prompt.md"
    PROMPT_DEST_DIR=".github/prompts"
    PROMPT_DEST_PATH="$PROMPT_DEST_DIR/speckit.bicep.prompt.md"
    
    if [[ ! -f "$PROMPT_SOURCE_PATH" ]]; then
        warning "Prompt file not found at: $PROMPT_SOURCE_PATH"
        info "Skipping prompt file installation"
    else
        # Create directory if it doesn't exist
        if [[ ! -d "$PROMPT_DEST_DIR" ]]; then
            info "Creating directory: $PROMPT_DEST_DIR"
            mkdir -p "$PROMPT_DEST_DIR"
        fi
        
        # Copy the file
        info "Copying prompt file..."
        cp "$PROMPT_SOURCE_PATH" "$PROMPT_DEST_PATH"
        
        # Verify
        if [[ -f "$PROMPT_DEST_PATH" ]]; then
            success "GitHub Copilot prompt file installed"
            info "Location: $PROMPT_DEST_PATH"
            echo ""
            echo -e "You can now use ${GREEN}/speckit.bicep${NC} in GitHub Copilot Chat!"
        else
            warning "Failed to copy prompt file"
        fi
    fi
else
    info "Skipping GitHub Copilot prompt file (--skip-prompt-file flag)"
fi

# Display next steps
echo ""
echo -e "${CYAN}================================================${NC}"
echo -e "${GREEN}  Installation Complete!${NC}"
echo -e "${CYAN}================================================${NC}"
echo ""
echo -e "${CYAN}Next steps:${NC}"
echo ""
echo -e "  ${NC}1. Test the CLI command:${NC}"
echo -e "     ${YELLOW}specify bicep --analyze-only${NC}"
echo ""
echo -e "  ${NC}2. Use in GitHub Copilot Chat:${NC}"
echo -e "     ${YELLOW}/speckit.bicep${NC}"
echo ""
echo -e "  ${NC}3. Make changes to the source code:${NC}"
echo -e "     ${YELLOW}Changes in $SPEC_KIT_PATH${NC}"
echo -e "     ${YELLOW}will be immediately reflected (no reinstall needed)${NC}"
echo ""

# Show project info
echo -e "${CYAN}Project Information:${NC}"
echo -e "  ${GRAY}Source: $SPEC_KIT_PATH${NC}"
echo -e "  ${GRAY}Target: $PWD${NC}"
echo ""

# Check for requirements.txt or package.json
HAS_REQUIREMENTS=false
HAS_PACKAGE_JSON=false
[[ -f "requirements.txt" ]] && HAS_REQUIREMENTS=true
[[ -f "package.json" ]] && HAS_PACKAGE_JSON=true

if [[ "$HAS_REQUIREMENTS" == "true" ]] || [[ "$HAS_PACKAGE_JSON" == "true" ]]; then
    echo -e "${CYAN}Detected project files:${NC}"
    [[ "$HAS_REQUIREMENTS" == "true" ]] && echo -e "  ${GREEN}✓ requirements.txt${NC}"
    [[ "$HAS_PACKAGE_JSON" == "true" ]] && echo -e "  ${GREEN}✓ package.json${NC}"
    echo ""
    echo -e "Run ${YELLOW}specify bicep --analyze-only${NC} to analyze your project!"
fi

echo ""
echo -e "${MAGENTA}Happy coding! 🚀${NC}"
echo ""
