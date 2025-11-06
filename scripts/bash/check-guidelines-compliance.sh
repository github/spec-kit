#!/usr/bin/env bash
# shellcheck disable=SC2155,SC2086

##############################################################################
# Corporate Guidelines Compliance Checker
# Part of Spec Kit Phase 4: Advanced Features
#
# Purpose: Validate project compliance with corporate guidelines
# Usage: ./check-guidelines-compliance.sh [--strict] [--output=<format>]
#
# Exit codes:
#   0 - No violations or only LOW/MEDIUM severity
#   1 - HIGH severity violations found
#   2 - CRITICAL violations found
#   3 - Script error (missing guidelines, etc.)
##############################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
STRICT_MODE=false
OUTPUT_FORMAT="text"  # text, json, markdown
PROJECT_ROOT="$(pwd)"
GUIDELINES_DIR="${PROJECT_ROOT}/.guidelines"

# Counters for violations
CRITICAL_COUNT=0
HIGH_COUNT=0
MEDIUM_COUNT=0
LOW_COUNT=0

# Arrays to store violations
declare -a CRITICAL_VIOLATIONS=()
declare -a HIGH_VIOLATIONS=()
declare -a MEDIUM_VIOLATIONS=()
declare -a LOW_VIOLATIONS=()
declare -a PASS_CHECKS=()

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

log_pass() {
    PASS_CHECKS+=("✅ PASS: $1")
}

log_critical() {
    CRITICAL_COUNT=$((CRITICAL_COUNT + 1))
    CRITICAL_VIOLATIONS+=("❌ CRITICAL: $1")
}

log_high() {
    HIGH_COUNT=$((HIGH_COUNT + 1))
    HIGH_VIOLATIONS+=("❌ HIGH: $1")
}

log_medium() {
    MEDIUM_COUNT=$((MEDIUM_COUNT + 1))
    MEDIUM_VIOLATIONS+=("⚠️  MEDIUM: $1")
}

log_low() {
    LOW_COUNT=$((LOW_COUNT + 1))
    LOW_VIOLATIONS+=("ℹ️  LOW: $1")
}

##############################################################################
# Tech Stack Detection
##############################################################################

detect_tech_stacks() {
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

    # Check for Go
    if [ -f "go.mod" ]; then
        stacks+=("go")
    fi

    echo "${stacks[@]}"
}

##############################################################################
# Guideline Loading
##############################################################################

load_guideline() {
    local stack="$1"
    local guideline_file="${GUIDELINES_DIR}/${stack}-guidelines.md"

    if [ ! -f "$guideline_file" ]; then
        return 1
    fi

    echo "$guideline_file"
    return 0
}

##############################################################################
# Compliance Checks
##############################################################################

check_package_registry() {
    local stack="$1"
    local guideline_file="$2"

    if [ "$stack" = "reactjs" ] || [ "$stack" = "nodejs" ]; then
        if [ -f "package.json" ]; then
            # Check if corporate registry is configured
            if grep -q "artifactory" package.json 2>/dev/null || \
               grep -q "nexus" package.json 2>/dev/null || \
               [ -f ".npmrc" ]; then
                log_pass "Package registry configured"
            else
                # Check if guideline requires corporate registry
                if grep -qi "artifactory\|nexus\|registry" "$guideline_file" 2>/dev/null; then
                    log_medium "No corporate package registry configured in package.json or .npmrc"
                fi
            fi
        fi
    fi
}

check_corporate_libraries() {
    local stack="$1"
    local guideline_file="$2"

    if [ "$stack" = "reactjs" ] || [ "$stack" = "nodejs" ]; then
        if [ -f "package.json" ]; then
            # Extract corporate package requirements from guidelines
            # Look for patterns like @company/* or @acmecorp/* or @yourcompany/*
            local corporate_patterns=$(grep -E "@[a-zA-Z]+corp|@company|@yourcompany" "$guideline_file" 2>/dev/null | \
                                      grep -oE "@[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+" | sort -u)

            if [ -n "$corporate_patterns" ]; then
                local found_count=0
                local required_count=0

                while IFS= read -r pattern; do
                    required_count=$((required_count + 1))

                    # Check if package is in package.json
                    if grep -q "\"$pattern\"" package.json 2>/dev/null; then
                        found_count=$((found_count + 1))

                        # Count imports in source files
                        local import_count=$(find src -type f \( -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" \) \
                                           -exec grep -l "from ['\"]$pattern" {} \; 2>/dev/null | wc -l)

                        if [ $import_count -gt 0 ]; then
                            log_pass "Using corporate library $pattern ($import_count imports found)"
                        fi
                    fi
                done <<< "$corporate_patterns"

                # Report if corporate libraries are not being used
                if [ $found_count -eq 0 ] && [ $required_count -gt 0 ]; then
                    log_high "No corporate libraries found - guidelines require packages like: $(echo "$corporate_patterns" | head -1)"
                fi
            fi
        fi
    elif [ "$stack" = "java" ]; then
        if [ -f "pom.xml" ]; then
            # Check for corporate groupId patterns
            local corporate_groups=$(grep -E "com\\.acmecorp|com\\.company|com\\.yourcompany" "$guideline_file" 2>/dev/null | \
                                   grep -oE "com\\.[a-zA-Z0-9_-]+" | sort -u)

            if [ -n "$corporate_groups" ]; then
                local found_any=false

                while IFS= read -r group; do
                    if grep -q "<groupId>$group</groupId>" pom.xml 2>/dev/null; then
                        log_pass "Using corporate library with groupId: $group"
                        found_any=true
                    fi
                done <<< "$corporate_groups"

                if [ "$found_any" = false ]; then
                    log_high "No corporate libraries found - guidelines require groupIds like: $(echo "$corporate_groups" | head -1)"
                fi
            fi
        fi
    fi
}

check_banned_libraries() {
    local stack="$1"
    local guideline_file="$2"

    # Extract banned library section from guidelines
    local banned_section=$(sed -n '/##.*Banned.*Libraries/,/##/p' "$guideline_file" 2>/dev/null | grep -v "^##")

    if [ -z "$banned_section" ]; then
        return 0
    fi

    if [ "$stack" = "reactjs" ] || [ "$stack" = "nodejs" ]; then
        if [ -f "package.json" ]; then
            # Common banned libraries (these are examples, real ones come from guidelines)
            local banned_libs=("lodash" "moment" "@mui/material" "bootstrap")

            for lib in "${banned_libs[@]}"; do
                if grep -q "\"$lib\"" package.json 2>/dev/null; then
                    # Check if this library is actually mentioned as banned in guidelines
                    if echo "$banned_section" | grep -qi "$lib"; then
                        log_critical "Found banned library: $lib (see guidelines for approved alternative)"
                    fi
                fi
            done
        fi
    fi
}

check_architecture_patterns() {
    local stack="$1"
    local guideline_file="$2"

    # Check for specific folder structure requirements
    if grep -qi "folder structure\|directory structure" "$guideline_file" 2>/dev/null; then
        local src_exists=false

        if [ -d "src" ]; then
            src_exists=true
            log_pass "Standard src/ directory exists"
        fi

        # Check for common architecture patterns
        if [ -d "src/components" ] || [ -d "src/services" ] || [ -d "src/controllers" ]; then
            log_pass "Standard architecture folder structure detected"
        elif [ "$src_exists" = true ]; then
            log_low "Consider organizing code into standard folders (components, services, etc.)"
        fi
    fi
}

check_security_requirements() {
    local stack="$1"
    local guideline_file="$2"

    # Check for authentication/authorization mentions in guidelines
    if grep -qi "authentication\|authorization\|auth\|idm\|identity" "$guideline_file" 2>/dev/null; then
        if [ "$stack" = "reactjs" ] || [ "$stack" = "nodejs" ]; then
            # Check for common auth patterns in code
            local auth_files=$(find src -type f \( -name "*.js" -o -name "*.jsx" -o -name "*.ts" -o -name "*.tsx" \) \
                              -exec grep -l "auth\|login\|token\|jwt" {} \; 2>/dev/null | wc -l)

            if [ $auth_files -gt 0 ]; then
                log_pass "Authentication implementation detected ($auth_files files)"
            else
                log_medium "No authentication implementation found - guidelines mention auth requirements"
            fi
        fi
    fi

    # Check for environment variable handling
    if [ -f ".env" ] && [ ! -f ".env.example" ]; then
        log_medium "Found .env file but no .env.example template"
    fi

    # Check if .env is gitignored
    if [ -f ".env" ]; then
        if ! grep -q "^\.env$" .gitignore 2>/dev/null; then
            log_critical ".env file exists but not in .gitignore - potential credentials exposure"
        else
            log_pass ".env file properly gitignored"
        fi
    fi
}

##############################################################################
# Report Generation
##############################################################################

generate_text_report() {
    print_header "Guideline Compliance Report"

    # Show detected stacks
    local stacks=($(detect_tech_stacks))
    echo "Tech Stack: ${stacks[*]}"

    # Show loaded guidelines
    echo "Guidelines: "
    for stack in "${stacks[@]}"; do
        local guideline_file=$(load_guideline "$stack")
        if [ $? -eq 0 ]; then
            echo "  - ${stack}-guidelines.md"
        fi
    done
    echo ""

    # Show passing checks
    if [ ${#PASS_CHECKS[@]} -gt 0 ]; then
        print_section "Passing Checks"
        for check in "${PASS_CHECKS[@]}"; do
            echo -e "${GREEN}$check${NC}"
        done
    fi

    # Show violations by severity
    if [ ${#CRITICAL_VIOLATIONS[@]} -gt 0 ]; then
        print_section "CRITICAL Violations"
        for violation in "${CRITICAL_VIOLATIONS[@]}"; do
            echo -e "${RED}$violation${NC}"
        done
    fi

    if [ ${#HIGH_VIOLATIONS[@]} -gt 0 ]; then
        print_section "HIGH Severity Violations"
        for violation in "${HIGH_VIOLATIONS[@]}"; do
            echo -e "${RED}$violation${NC}"
        done
    fi

    if [ ${#MEDIUM_VIOLATIONS[@]} -gt 0 ]; then
        print_section "MEDIUM Severity Violations"
        for violation in "${MEDIUM_VIOLATIONS[@]}"; do
            echo -e "${YELLOW}$violation${NC}"
        done
    fi

    if [ ${#LOW_VIOLATIONS[@]} -gt 0 ]; then
        print_section "LOW Severity Violations"
        for violation in "${LOW_VIOLATIONS[@]}"; do
            echo "$violation"
        done
    fi

    # Summary
    print_section "Summary"
    echo "CRITICAL: $CRITICAL_COUNT"
    echo "HIGH:     $HIGH_COUNT"
    echo "MEDIUM:   $MEDIUM_COUNT"
    echo "LOW:      $LOW_COUNT"
    echo ""

    # Overall status
    if [ $CRITICAL_COUNT -gt 0 ]; then
        echo -e "${RED}${BOLD}Status: FAILED${NC}"
        return 2
    elif [ $HIGH_COUNT -gt 0 ]; then
        echo -e "${YELLOW}${BOLD}Status: WARNING${NC}"
        return 1
    else
        echo -e "${GREEN}${BOLD}Status: PASSED${NC}"
        return 0
    fi
}

generate_json_report() {
    local stacks=($(detect_tech_stacks))

    cat <<EOF
{
  "report_version": "1.0",
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "project_root": "$PROJECT_ROOT",
  "tech_stacks": [$(printf '"%s",' "${stacks[@]}" | sed 's/,$//')],
  "summary": {
    "critical": $CRITICAL_COUNT,
    "high": $HIGH_COUNT,
    "medium": $MEDIUM_COUNT,
    "low": $LOW_COUNT
  },
  "status": "$([ $CRITICAL_COUNT -gt 0 ] && echo "FAILED" || [ $HIGH_COUNT -gt 0 ] && echo "WARNING" || echo "PASSED")",
  "violations": {
    "critical": [$(printf '"%s",' "${CRITICAL_VIOLATIONS[@]}" | sed 's/,$//')],
    "high": [$(printf '"%s",' "${HIGH_VIOLATIONS[@]}" | sed 's/,$//')],
    "medium": [$(printf '"%s",' "${MEDIUM_VIOLATIONS[@]}" | sed 's/,$//')],
    "low": [$(printf '"%s",' "${LOW_VIOLATIONS[@]}" | sed 's/,$//')]
  },
  "passing_checks": [$(printf '"%s",' "${PASS_CHECKS[@]}" | sed 's/,$//')],
  "exit_code": $([ $CRITICAL_COUNT -gt 0 ] && echo 2 || [ $HIGH_COUNT -gt 0 ] && echo 1 || echo 0)
}
EOF
}

##############################################################################
# Main Execution
##############################################################################

show_usage() {
    cat <<EOF
Usage: $0 [OPTIONS]

Options:
  --strict              Fail on HIGH severity violations (default: only CRITICAL)
  --output=FORMAT       Output format: text (default), json, markdown
  --help                Show this help message

Examples:
  $0                           # Run with default settings
  $0 --strict                  # Fail on HIGH violations
  $0 --output=json             # Output as JSON
  $0 --output=json > report.json  # Save JSON report
EOF
}

main() {
    # Parse arguments
    for arg in "$@"; do
        case $arg in
            --strict)
                STRICT_MODE=true
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

    # Validate guidelines directory exists
    if [ ! -d "$GUIDELINES_DIR" ]; then
        echo -e "${YELLOW}Warning: No .guidelines directory found at $GUIDELINES_DIR${NC}" >&2
        echo "Guidelines are optional. If you want guideline compliance checking," >&2
        echo "create a .guidelines directory with tech stack guidelines." >&2
        exit 3
    fi

    # Detect tech stacks
    local stacks=($(detect_tech_stacks))

    if [ ${#stacks[@]} -eq 0 ]; then
        echo -e "${YELLOW}Warning: No tech stack detected${NC}" >&2
        echo "Could not detect any supported tech stacks (React, Java, .NET, Python, Go)." >&2
        exit 3
    fi

    # Load and check guidelines for each stack
    for stack in "${stacks[@]}"; do
        local guideline_file=$(load_guideline "$stack")

        if [ $? -eq 0 ]; then
            # Run compliance checks
            check_package_registry "$stack" "$guideline_file"
            check_corporate_libraries "$stack" "$guideline_file"
            check_banned_libraries "$stack" "$guideline_file"
            check_architecture_patterns "$stack" "$guideline_file"
            check_security_requirements "$stack" "$guideline_file"
        else
            log_low "No guidelines found for $stack (${stack}-guidelines.md not found)"
        fi
    done

    # Generate report
    local exit_code=0

    case "$OUTPUT_FORMAT" in
        json)
            generate_json_report
            ;;
        text|*)
            generate_text_report
            exit_code=$?
            ;;
    esac

    # Determine exit code
    if [ $CRITICAL_COUNT -gt 0 ]; then
        exit 2
    elif [ $STRICT_MODE = true ] && [ $HIGH_COUNT -gt 0 ]; then
        exit 1
    else
        exit $exit_code
    fi
}

# Run main function
main "$@"
