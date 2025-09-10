#!/bin/bash
set -e

# Colors for output (ANSI escape codes)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Usage: init-project.sh <project_path> <ai_assistant> <is_here> <no_git>
PROJECT_PATH="$1"
AI_ASSISTANT="$2"
IS_HERE="$3"
NO_GIT="$4"

if [ -z "$PROJECT_PATH" ] || [ -z "$AI_ASSISTANT" ]; then
    echo -e "${RED}Usage: $0 <project_path> <ai_assistant> <is_here> <no_git>${NC}" >&2
    exit 1
fi

# Get the absolute path of the script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo -e "${CYAN}Initializing Specify project at: $PROJECT_PATH${NC}"

# Step 1: Create project directory if not using current directory
if [ "$IS_HERE" != "true" ]; then
    echo -e "${BLUE}Creating project directory...${NC}"
    mkdir -p "$PROJECT_PATH"
fi

# Step 2: Download and extract template
echo -e "${BLUE}Fetching latest template...${NC}"

# Download template using the dedicated script
TEMPLATE_ZIP="$PROJECT_PATH/template.zip"
"$SCRIPT_DIR/download-template.sh" "$AI_ASSISTANT" "$TEMPLATE_ZIP"

# Extract template
echo -e "${BLUE}Extracting template...${NC}"
cd "$PROJECT_PATH"

if [ "$IS_HERE" = "true" ]; then
    # For current directory, extract to temp and merge
    TEMP_DIR=$(mktemp -d)
    unzip -q "$TEMPLATE_ZIP" -d "$TEMP_DIR"

    # Find the actual template directory (GitHub zips have a root folder)
    TEMPLATE_CONTENT=$(find "$TEMP_DIR" -mindepth 1 -maxdepth 1 -type d | head -1)
    if [ -n "$TEMPLATE_CONTENT" ]; then
        # Merge template files with existing directory
        cp -r "$TEMPLATE_CONTENT"/* . 2>/dev/null || true
        cp -r "$TEMPLATE_CONTENT"/.* . 2>/dev/null || true
    else
        # No root directory, copy all files
        cp -r "$TEMP_DIR"/* . 2>/dev/null || true
    fi

    rm -rf "$TEMP_DIR"
else
    # Extract directly to project directory
    unzip -q "$TEMPLATE_ZIP"

    # Handle nested directory structure (GitHub zip format)
    EXTRACTED_DIRS=$(find . -mindepth 1 -maxdepth 1 -type d)
    if [ $(echo "$EXTRACTED_DIRS" | wc -l) -eq 1 ]; then
        # Move contents up one level
        NESTED_DIR=$(echo "$EXTRACTED_DIRS" | head -1)
        mv "$NESTED_DIR"/* . 2>/dev/null || true
        mv "$NESTED_DIR"/.* . 2>/dev/null || true
        rmdir "$NESTED_DIR"
    fi
fi

# Clean up
rm -f "$TEMPLATE_ZIP"

echo -e "${GREEN}✓ Template extracted${NC}"

# Step 3: Initialize git repository
if [ "$NO_GIT" != "true" ]; then
    echo -e "${BLUE}Initializing git repository...${NC}"
    cd "$PROJECT_PATH"

    if git rev-parse --git-dir > /dev/null 2>&1; then
        echo -e "${YELLOW}Git repository already exists${NC}"
    else
        git init
        git add .
        git commit -m "Initial commit from Specify template"
        echo -e "${GREEN}✓ Git repository initialized${NC}"
    fi
fi

# Step 4: Copy and configure templates
echo -e "${BLUE}Setting up project templates...${NC}"

# Copy cursor-specific command templates (override any downloaded ones)
mkdir -p "$PROJECT_PATH/.cursor/commands"
if [ -d "$REPO_ROOT/templates/cursor-commands" ]; then
    cp "$REPO_ROOT/templates/cursor-commands/"* "$PROJECT_PATH/.cursor/commands/" 2>/dev/null || true
fi

# Update constitution template
if [ -f "$PROJECT_PATH/memory/constitution.md" ]; then
    # Replace placeholders in constitution
    sed -i.bak "s/\[PROJECT_NAME\]/$PROJECT_NAME/g" "$PROJECT_PATH/memory/constitution.md"
    rm -f "$PROJECT_PATH/memory/constitution.md.bak"
fi

# Step 5: Create .cursorrules file for Cursor AI
cat > "$PROJECT_PATH/.cursorrules" << 'EOF'
# Cursor Rules for Spec-Driven Development

## Development Process
1. Always start with /specify to create a specification before coding
2. Use /plan to create technical implementation plans
3. Break down work with /tasks before implementation
4. Follow the constitution principles in memory/constitution.md

## Code Quality
- Write clean, readable code
- Add comments for complex logic
- Follow language-specific best practices
- Test your changes

## Git Workflow
- Create feature branches for new work
- Write clear commit messages
- Keep commits focused on single changes
EOF

echo -e "${GREEN}✓ Project templates configured${NC}"

echo -e "${GREEN}Project initialization complete!${NC}"
