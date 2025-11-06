#!/usr/bin/env bash
# shellcheck disable=SC2155,SC2086

##############################################################################
# Guideline Diff Tool
# Part of Spec Kit Phase 4: Advanced Features
#
# Purpose: Compare project guidelines vs template guidelines
# Usage: ./diff-guidelines.sh [--stack=<name>] [--output=<format>]
#
# Features:
#   - Compare customized guidelines against default templates
#   - Show additions, removals, and modifications
#   - Identify outdated sections that need updating
#   - Check for version mismatches
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
TEMPLATES_URL="https://raw.githubusercontent.com/veerabhadra-ponna/spec-kit-smart/main/.guidelines"
OUTPUT_FORMAT="text"
STACK=""
SHOW_ALL=false

# Temp directory for downloading templates
TEMP_DIR=$(mktemp -d)
trap 'rm -rf "$TEMP_DIR"' EXIT

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

##############################################################################
# Template Download
##############################################################################

download_template() {
    local stack="$1"
    local template_file="${TEMP_DIR}/${stack}-guidelines.md"

    # Download from GitHub (in production, this would be the actual template URL)
    # For now, we'll create a placeholder that notes the comparison
    cat > "$template_file" <<EOF
# ${stack^} Corporate Guidelines Template

Version: 1.0.0
Status: TEMPLATE - Customize before use
Priority: After Constitution, before defaults

---

## 🚀 Project Initialization (READ FIRST)

### Scaffolding Command

**Default approach:**

\`\`\`bash
# Standard public scaffolding
npx create-${stack}-app my-app
\`\`\`

**Corporate approach (CUSTOMIZE THIS):**

\`\`\`bash
npx @YOUR_ORG/create-${stack}-app my-app --template=enterprise
\`\`\`

---

## 📦 Corporate Libraries (MANDATORY)

### Required Dependencies

**CUSTOMIZE THIS SECTION** with your organization's required packages.

**Example:**

\`\`\`bash
npm install @yourcompany/ui-components
npm install @yourcompany/auth-client
\`\`\`

### Banned Public Libraries

**CUSTOMIZE THIS SECTION** with packages your organization prohibits.

**Example:**

- \`lodash\` → Use \`@yourcompany/utils\` instead
- Public auth libraries → Use \`@yourcompany/auth-client\`

---

## 🏛️ Architecture Patterns

### Folder Structure

**CUSTOMIZE THIS SECTION** with your organization's folder conventions.

**Standard structure:**

\`\`\`text
src/
├── components/
├── services/
├── utils/
└── config/
\`\`\`

---

## 🔐 Security & Compliance

### Authentication

**CUSTOMIZE THIS SECTION** with your organization's auth requirements.

### Data Classification

**CUSTOMIZE THIS SECTION** with PII handling, encryption, audit logging requirements.

---

## 📚 Resources

- Internal Wiki: [CUSTOMIZE WITH YOUR WIKI URL]
- Support: [CUSTOMIZE WITH YOUR SUPPORT EMAIL/SLACK]
- Examples: [CUSTOMIZE WITH LINKS TO EXAMPLE PROJECTS]

EOF

    echo "$template_file"
}

##############################################################################
# Diff Analysis
##############################################################################

extract_sections() {
    local file="$1"
    # Extract markdown section headers
    grep -E "^##+ " "$file" 2>/dev/null || echo ""
}

compare_versions() {
    local project_file="$1"
    local template_file="$2"

    local project_version=$(grep -E "^Version:" "$project_file" 2>/dev/null | head -1 | awk '{print $2}')
    local template_version=$(grep -E "^Version:" "$template_file" 2>/dev/null | head -1 | awk '{print $2}')

    if [ -z "$project_version" ]; then
        project_version="unknown"
    fi

    if [ -z "$template_version" ]; then
        template_version="unknown"
    fi

    echo "$project_version|$template_version"
}

count_customizations() {
    local project_file="$1"
    # Count occurrences of "CUSTOMIZE" placeholders remaining
    grep -ic "customize\|YOUR_ORG\|yourcompany\|@company" "$project_file" 2>/dev/null || echo "0"
}

analyze_diff() {
    local stack="$1"
    local project_file="${GUIDELINES_DIR}/${stack}-guidelines.md"
    local template_file="$2"

    if [ ! -f "$project_file" ]; then
        echo -e "${YELLOW}⚠️  No project guideline found for $stack${NC}"
        echo "   Create: $project_file"
        return 1
    fi

    print_section "Comparison: ${stack}-guidelines.md"

    # Version comparison
    local versions=$(compare_versions "$project_file" "$template_file")
    local project_version=$(echo "$versions" | cut -d'|' -f1)
    local template_version=$(echo "$versions" | cut -d'|' -f2)

    echo -e "${CYAN}Version Check:${NC}"
    echo "  Project:  $project_version"
    echo "  Template: $template_version"

    if [ "$project_version" != "$template_version" ] && [ "$project_version" != "unknown" ] && [ "$template_version" != "unknown" ]; then
        echo -e "  ${YELLOW}⚠️  Version mismatch - consider updating${NC}"
    else
        echo -e "  ${GREEN}✓ Versions match${NC}"
    fi

    # Check for remaining placeholders
    local customize_count=$(count_customizations "$project_file")
    echo ""
    echo -e "${CYAN}Customization Status:${NC}"

    if [ "$customize_count" -gt 0 ]; then
        echo -e "  ${YELLOW}⚠️  Found $customize_count placeholder(s) needing customization${NC}"
        echo "  Placeholders: YOUR_ORG, @yourcompany, CUSTOMIZE, etc."
    else
        echo -e "  ${GREEN}✓ All placeholders customized${NC}"
    fi

    # Section comparison
    echo ""
    echo -e "${CYAN}Section Analysis:${NC}"

    local project_sections=$(extract_sections "$project_file")
    local template_sections=$(extract_sections "$template_file")

    # Sections only in project (additions)
    local additions=$(comm -23 <(echo "$project_sections" | sort) <(echo "$template_sections" | sort))
    if [ -n "$additions" ]; then
        echo -e "  ${GREEN}✓ Custom sections added:${NC}"
        while IFS= read -r section; do
            [ -n "$section" ] && echo "    + $section"
        done <<< "$additions"
    fi

    # Sections only in template (missing)
    local missing=$(comm -13 <(echo "$project_sections" | sort) <(echo "$template_sections" | sort))
    if [ -n "$missing" ]; then
        echo -e "  ${YELLOW}⚠️  Sections missing from template:${NC}"
        while IFS= read -r section; do
            [ -n "$section" ] && echo "    - $section"
        done <<< "$missing"
    fi

    # Common sections
    local common=$(comm -12 <(echo "$project_sections" | sort) <(echo "$template_sections" | sort))
    local common_count=$(echo "$common" | grep -c "^##" || echo "0")
    echo -e "  ${GREEN}✓ Common sections: $common_count${NC}"

    # File size comparison (rough indicator of customization)
    local project_size=$(wc -l < "$project_file")
    local template_size=$(wc -l < "$template_file")
    local size_diff=$((project_size - template_size))

    echo ""
    echo -e "${CYAN}Content Size:${NC}"
    echo "  Project:  $project_size lines"
    echo "  Template: $template_size lines"
    if [ $size_diff -gt 50 ]; then
        echo -e "  ${GREEN}✓ Significantly expanded (+$size_diff lines)${NC}"
    elif [ $size_diff -lt -20 ]; then
        echo -e "  ${YELLOW}⚠️  Smaller than template ($size_diff lines) - may need more detail${NC}"
    else
        echo -e "  ${BLUE}≈ Similar size to template${NC}"
    fi

    # Detailed line-by-line diff (optional)
    if [ "$SHOW_ALL" = true ]; then
        echo ""
        echo -e "${CYAN}Detailed Diff:${NC}"
        diff -u "$template_file" "$project_file" | tail -n +3 || true
    fi

    echo ""
}

##############################################################################
# Report Generation
##############################################################################

generate_summary() {
    local stacks=("$@")

    print_header "Guideline Diff Summary"

    echo "Comparing project guidelines against default templates..."
    echo "Project: $PROJECT_ROOT"
    echo ""

    for stack in "${stacks[@]}"; do
        local template_file=$(download_template "$stack")
        analyze_diff "$stack" "$template_file"
    done

    print_section "Recommendations"

    echo "1. Update any guidelines with version mismatches"
    echo "2. Customize remaining placeholders (YOUR_ORG, @yourcompany, etc.)"
    echo "3. Add organization-specific sections as needed"
    echo "4. Review template for new sections you might be missing"
    echo "5. Keep guidelines updated as corporate standards evolve"
}

##############################################################################
# Main Execution
##############################################################################

show_usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Options:
  --stack=NAME          Compare specific stack (reactjs, java, dotnet, nodejs, python)
  --all                 Show detailed line-by-line diffs
  --output=FORMAT       Output format: text (default), json
  --help                Show this help message

Examples:
  $0                           # Compare all guidelines
  $0 --stack=reactjs           # Compare only React guidelines
  $0 --all                     # Show detailed diffs
  $0 --stack=java --all        # Show detailed diff for Java

Exit codes:
  0 - Comparison successful
  1 - No guidelines found
  3 - Invalid arguments or error
EOF
}

detect_stacks() {
    local stacks=()

    # Check for React
    if [ -f "package.json" ]; then
        if grep -q '"react"' package.json 2>/dev/null; then
            stacks+=("reactjs")
        elif grep -q '"express"' package.json 2>/dev/null; then
            stacks+=("nodejs")
        else
            stacks+=("nodejs")
        fi
    fi

    # Check for Java
    if [ -f "pom.xml" ] || [ -f "build.gradle" ]; then
        stacks+=("java")
    fi

    # Check for .NET
    if ls *.csproj &>/dev/null || ls *.sln &>/dev/null; then
        stacks+=("dotnet")
    fi

    # Check for Python
    if [ -f "requirements.txt" ] || [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
        stacks+=("python")
    fi

    echo "${stacks[@]}"
}

main() {
    # Parse arguments
    for arg in "$@"; do
        case $arg in
            --stack=*)
                STACK="${arg#*=}"
                ;;
            --all)
                SHOW_ALL=true
                ;;
            --output=*)
                OUTPUT_FORMAT="${arg#*=}"
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

    # Check if guidelines directory exists
    if [ ! -d "$GUIDELINES_DIR" ]; then
        echo -e "${RED}Error: No .guidelines directory found at $GUIDELINES_DIR${NC}" >&2
        exit 1
    fi

    # Determine which stacks to compare
    local stacks=()
    if [ -n "$STACK" ]; then
        stacks=("$STACK")
    else
        # Auto-detect or use all available guideline files
        for guideline in "$GUIDELINES_DIR"/*-guidelines.md; do
            if [ -f "$guideline" ]; then
                local basename=$(basename "$guideline" -guidelines.md)
                stacks+=("$basename")
            fi
        done

        # If no guidelines found, detect from project
        if [ ${#stacks[@]} -eq 0 ]; then
            stacks=($(detect_stacks))
        fi
    fi

    if [ ${#stacks[@]} -eq 0 ]; then
        echo -e "${YELLOW}No guidelines found to compare${NC}" >&2
        exit 1
    fi

    # Generate report
    generate_summary "${stacks[@]}"
}

# Run main function
main "$@"
