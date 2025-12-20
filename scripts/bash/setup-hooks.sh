#!/usr/bin/env bash

# Setup Claude Code hooks and skills for the current project
#
# This script detects the project type and generates appropriate
# hook configurations for Claude Code.
#
# Usage: ./setup-hooks.sh [OPTIONS]
#
# OPTIONS:
#   --json              Output in JSON format
#   --help, -h          Show help message
#
# OUTPUTS:
#   JSON mode: {"PROJECT_TYPE":"...", "DETECTED_TOOLS":[...], ...}
#   Text mode: Human-readable project detection summary

set -e

# Parse command line arguments
JSON_MODE=false

for arg in "$@"; do
    case "$arg" in
        --json)
            JSON_MODE=true
            ;;
        --help|-h)
            cat << 'EOF'
Usage: setup-hooks.sh [OPTIONS]

Setup Claude Code hooks and skills for the current project.

OPTIONS:
  --json              Output in JSON format
  --help, -h          Show this help message

EXAMPLES:
  # Detect project and output JSON
  ./setup-hooks.sh --json

  # Human-readable output
  ./setup-hooks.sh

EOF
            exit 0
            ;;
        *)
            echo "ERROR: Unknown option '$arg'. Use --help for usage information." >&2
            exit 1
            ;;
    esac
done

# Source common functions
SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Get repository root
REPO_ROOT=$(get_repo_root)

# Initialize detection variables
PROJECT_TYPE="generic"
PACKAGE_MANAGER=""
TEST_RUNNER=""
LINTER=""
FORMATTER=""
DETECTED_TOOLS=()

# Detect project type and tools
detect_project() {
    # Node.js / TypeScript
    if [[ -f "$REPO_ROOT/package.json" ]]; then
        PROJECT_TYPE="node"
        DETECTED_TOOLS+=("node")

        # Detect package manager
        if [[ -f "$REPO_ROOT/pnpm-lock.yaml" ]]; then
            PACKAGE_MANAGER="pnpm"
        elif [[ -f "$REPO_ROOT/yarn.lock" ]]; then
            PACKAGE_MANAGER="yarn"
        elif [[ -f "$REPO_ROOT/bun.lockb" ]]; then
            PACKAGE_MANAGER="bun"
        else
            PACKAGE_MANAGER="npm"
        fi
        DETECTED_TOOLS+=("$PACKAGE_MANAGER")

        # Check for TypeScript
        if [[ -f "$REPO_ROOT/tsconfig.json" ]]; then
            PROJECT_TYPE="node-typescript"
            DETECTED_TOOLS+=("typescript")
        fi

        # Detect test runner from package.json
        if grep -q '"jest"' "$REPO_ROOT/package.json" 2>/dev/null; then
            TEST_RUNNER="jest"
            DETECTED_TOOLS+=("jest")
        elif grep -q '"vitest"' "$REPO_ROOT/package.json" 2>/dev/null; then
            TEST_RUNNER="vitest"
            DETECTED_TOOLS+=("vitest")
        elif grep -q '"mocha"' "$REPO_ROOT/package.json" 2>/dev/null; then
            TEST_RUNNER="mocha"
            DETECTED_TOOLS+=("mocha")
        fi

        # Detect linter
        if [[ -f "$REPO_ROOT/.eslintrc.json" ]] || [[ -f "$REPO_ROOT/.eslintrc.js" ]] || [[ -f "$REPO_ROOT/.eslintrc.cjs" ]] || [[ -f "$REPO_ROOT/eslint.config.js" ]] || [[ -f "$REPO_ROOT/eslint.config.mjs" ]]; then
            LINTER="eslint"
            DETECTED_TOOLS+=("eslint")
        elif grep -q '"eslint"' "$REPO_ROOT/package.json" 2>/dev/null; then
            LINTER="eslint"
            DETECTED_TOOLS+=("eslint")
        fi

        # Detect formatter
        if [[ -f "$REPO_ROOT/.prettierrc" ]] || [[ -f "$REPO_ROOT/.prettierrc.json" ]] || [[ -f "$REPO_ROOT/prettier.config.js" ]]; then
            FORMATTER="prettier"
            DETECTED_TOOLS+=("prettier")
        elif grep -q '"prettier"' "$REPO_ROOT/package.json" 2>/dev/null; then
            FORMATTER="prettier"
            DETECTED_TOOLS+=("prettier")
        fi

    # Python
    elif [[ -f "$REPO_ROOT/pyproject.toml" ]] || [[ -f "$REPO_ROOT/requirements.txt" ]] || [[ -f "$REPO_ROOT/setup.py" ]]; then
        PROJECT_TYPE="python"
        DETECTED_TOOLS+=("python")

        # Detect package manager
        if [[ -f "$REPO_ROOT/poetry.lock" ]]; then
            PACKAGE_MANAGER="poetry"
            DETECTED_TOOLS+=("poetry")
        elif [[ -f "$REPO_ROOT/Pipfile.lock" ]]; then
            PACKAGE_MANAGER="pipenv"
            DETECTED_TOOLS+=("pipenv")
        elif [[ -f "$REPO_ROOT/uv.lock" ]]; then
            PACKAGE_MANAGER="uv"
            DETECTED_TOOLS+=("uv")
        else
            PACKAGE_MANAGER="pip"
            DETECTED_TOOLS+=("pip")
        fi

        # Detect test runner
        if [[ -f "$REPO_ROOT/pytest.ini" ]] || grep -q "pytest" "$REPO_ROOT/pyproject.toml" 2>/dev/null || grep -q "pytest" "$REPO_ROOT/requirements.txt" 2>/dev/null; then
            TEST_RUNNER="pytest"
            DETECTED_TOOLS+=("pytest")
        fi

        # Detect linter/formatter
        if grep -q "ruff" "$REPO_ROOT/pyproject.toml" 2>/dev/null || [[ -f "$REPO_ROOT/ruff.toml" ]]; then
            LINTER="ruff"
            FORMATTER="ruff"
            DETECTED_TOOLS+=("ruff")
        fi
        if grep -q "black" "$REPO_ROOT/pyproject.toml" 2>/dev/null; then
            FORMATTER="black"
            DETECTED_TOOLS+=("black")
        fi
        if grep -q "mypy" "$REPO_ROOT/pyproject.toml" 2>/dev/null; then
            DETECTED_TOOLS+=("mypy")
        fi

    # Rust
    elif [[ -f "$REPO_ROOT/Cargo.toml" ]]; then
        PROJECT_TYPE="rust"
        PACKAGE_MANAGER="cargo"
        TEST_RUNNER="cargo-test"
        LINTER="clippy"
        FORMATTER="rustfmt"
        DETECTED_TOOLS+=("rust" "cargo" "clippy" "rustfmt")

    # Go
    elif [[ -f "$REPO_ROOT/go.mod" ]]; then
        PROJECT_TYPE="go"
        PACKAGE_MANAGER="go-mod"
        TEST_RUNNER="go-test"
        FORMATTER="gofmt"
        LINTER="go-vet"
        DETECTED_TOOLS+=("go" "gofmt" "go-vet")

        # Check for golangci-lint
        if [[ -f "$REPO_ROOT/.golangci.yml" ]] || [[ -f "$REPO_ROOT/.golangci.yaml" ]]; then
            LINTER="golangci-lint"
            DETECTED_TOOLS+=("golangci-lint")
        fi

    # Java (Maven)
    elif [[ -f "$REPO_ROOT/pom.xml" ]]; then
        PROJECT_TYPE="java-maven"
        PACKAGE_MANAGER="maven"
        TEST_RUNNER="maven-test"
        DETECTED_TOOLS+=("java" "maven")

    # Java (Gradle)
    elif [[ -f "$REPO_ROOT/build.gradle" ]] || [[ -f "$REPO_ROOT/build.gradle.kts" ]]; then
        PROJECT_TYPE="java-gradle"
        PACKAGE_MANAGER="gradle"
        TEST_RUNNER="gradle-test"
        DETECTED_TOOLS+=("java" "gradle")

    # .NET
    elif [[ -f "$REPO_ROOT/*.csproj" ]] || [[ -f "$REPO_ROOT/*.sln" ]] || find "$REPO_ROOT" -maxdepth 2 -name "*.csproj" -o -name "*.sln" 2>/dev/null | head -1 | grep -q .; then
        PROJECT_TYPE="dotnet"
        PACKAGE_MANAGER="dotnet"
        TEST_RUNNER="dotnet-test"
        DETECTED_TOOLS+=("dotnet")

    # Ruby
    elif [[ -f "$REPO_ROOT/Gemfile" ]]; then
        PROJECT_TYPE="ruby"
        PACKAGE_MANAGER="bundler"
        DETECTED_TOOLS+=("ruby" "bundler")

        if grep -q "rspec" "$REPO_ROOT/Gemfile" 2>/dev/null; then
            TEST_RUNNER="rspec"
            DETECTED_TOOLS+=("rspec")
        fi

        if grep -q "rubocop" "$REPO_ROOT/Gemfile" 2>/dev/null; then
            LINTER="rubocop"
            DETECTED_TOOLS+=("rubocop")
        fi

    # PHP
    elif [[ -f "$REPO_ROOT/composer.json" ]]; then
        PROJECT_TYPE="php"
        PACKAGE_MANAGER="composer"
        DETECTED_TOOLS+=("php" "composer")

        if grep -q "phpunit" "$REPO_ROOT/composer.json" 2>/dev/null; then
            TEST_RUNNER="phpunit"
            DETECTED_TOOLS+=("phpunit")
        fi
    fi
}

# Run detection
detect_project

# Define output paths
CLAUDE_DIR="$REPO_ROOT/.claude"
SETTINGS_FILE="$CLAUDE_DIR/settings.json"
SKILLS_DIR="$CLAUDE_DIR/skills"
HOOKS_DIR="$CLAUDE_DIR/hooks"

# Check if .claude directory already exists
CLAUDE_EXISTS="false"
if [[ -d "$CLAUDE_DIR" ]]; then
    CLAUDE_EXISTS="true"
fi

# Check if settings.json already exists
SETTINGS_EXISTS="false"
if [[ -f "$SETTINGS_FILE" ]]; then
    SETTINGS_EXISTS="true"
fi

# Output results
if $JSON_MODE; then
    # Build JSON array of detected tools
    TOOLS_JSON="["
    first=true
    for tool in "${DETECTED_TOOLS[@]}"; do
        if $first; then
            first=false
        else
            TOOLS_JSON+=","
        fi
        TOOLS_JSON+="\"$tool\""
    done
    TOOLS_JSON+="]"

    cat <<EOF
{
  "PROJECT_TYPE": "$PROJECT_TYPE",
  "PACKAGE_MANAGER": "$PACKAGE_MANAGER",
  "TEST_RUNNER": "$TEST_RUNNER",
  "LINTER": "$LINTER",
  "FORMATTER": "$FORMATTER",
  "DETECTED_TOOLS": $TOOLS_JSON,
  "REPO_ROOT": "$REPO_ROOT",
  "CLAUDE_DIR": "$CLAUDE_DIR",
  "SETTINGS_FILE": "$SETTINGS_FILE",
  "SKILLS_DIR": "$SKILLS_DIR",
  "HOOKS_DIR": "$HOOKS_DIR",
  "CLAUDE_EXISTS": $CLAUDE_EXISTS,
  "SETTINGS_EXISTS": $SETTINGS_EXISTS
}
EOF
else
    echo "=== Project Detection Results ==="
    echo ""
    echo "Project Type: $PROJECT_TYPE"
    echo "Package Manager: ${PACKAGE_MANAGER:-none detected}"
    echo "Test Runner: ${TEST_RUNNER:-none detected}"
    echo "Linter: ${LINTER:-none detected}"
    echo "Formatter: ${FORMATTER:-none detected}"
    echo ""
    echo "Detected Tools: ${DETECTED_TOOLS[*]:-none}"
    echo ""
    echo "=== Claude Code Paths ==="
    echo "Claude Directory: $CLAUDE_DIR (exists: $CLAUDE_EXISTS)"
    echo "Settings File: $SETTINGS_FILE (exists: $SETTINGS_EXISTS)"
    echo "Skills Directory: $SKILLS_DIR"
    echo "Hooks Directory: $HOOKS_DIR"
fi
