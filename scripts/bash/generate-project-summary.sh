#!/usr/bin/env bash
set -e

# Source common utilities
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

# Parse command line arguments
JSON_OUTPUT=false

while [[ $# -gt 0 ]]; do
	case $1 in
		--json)
			JSON_OUTPUT=true
			shift
			;;
		*)
			shift
			;;
	esac
done

# Get repository root
REPO_ROOT=$(get_repo_root)

# Initialize arrays for discovered data
declare -a TECH_FILES=()
declare -a DIRECTORIES=()
declare -a LANGUAGES=()

# Detect configuration files for different languages/frameworks
detect_config_files() {
	local root="$1"

	# JavaScript/TypeScript
	[[ -f "$root/package.json" ]] && TECH_FILES+=("package.json") && LANGUAGES+=("JavaScript/TypeScript")
	[[ -f "$root/tsconfig.json" ]] && TECH_FILES+=("tsconfig.json")
	[[ -f "$root/yarn.lock" ]] && TECH_FILES+=("yarn.lock")
	[[ -f "$root/pnpm-lock.yaml" ]] && TECH_FILES+=("pnpm-lock.yaml")
	[[ -f "$root/bun.lockb" ]] && TECH_FILES+=("bun.lockb")

	# Python
	[[ -f "$root/requirements.txt" ]] && TECH_FILES+=("requirements.txt") && LANGUAGES+=("Python")
	[[ -f "$root/pyproject.toml" ]] && TECH_FILES+=("pyproject.toml") && LANGUAGES+=("Python")
	[[ -f "$root/setup.py" ]] && TECH_FILES+=("setup.py") && LANGUAGES+=("Python")
	[[ -f "$root/Pipfile" ]] && TECH_FILES+=("Pipfile") && LANGUAGES+=("Python")
	[[ -f "$root/poetry.lock" ]] && TECH_FILES+=("poetry.lock")

	# Go
	[[ -f "$root/go.mod" ]] && TECH_FILES+=("go.mod") && LANGUAGES+=("Go")
	[[ -f "$root/go.sum" ]] && TECH_FILES+=("go.sum")

	# Rust
	[[ -f "$root/Cargo.toml" ]] && TECH_FILES+=("Cargo.toml") && LANGUAGES+=("Rust")
	[[ -f "$root/Cargo.lock" ]] && TECH_FILES+=("Cargo.lock")

	# Java
	[[ -f "$root/pom.xml" ]] && TECH_FILES+=("pom.xml") && LANGUAGES+=("Java")
	[[ -f "$root/build.gradle" ]] && TECH_FILES+=("build.gradle") && LANGUAGES+=("Java/Kotlin")
	[[ -f "$root/build.gradle.kts" ]] && TECH_FILES+=("build.gradle.kts") && LANGUAGES+=("Kotlin")

	# Ruby
	[[ -f "$root/Gemfile" ]] && TECH_FILES+=("Gemfile") && LANGUAGES+=("Ruby")
	[[ -f "$root/Gemfile.lock" ]] && TECH_FILES+=("Gemfile.lock")

	# PHP
	[[ -f "$root/composer.json" ]] && TECH_FILES+=("composer.json") && LANGUAGES+=("PHP")
	[[ -f "$root/composer.lock" ]] && TECH_FILES+=("composer.lock")

	# C#/.NET
	find "$root" -maxdepth 2 \( -name "*.csproj" -o -name "*.fsproj" -o -name "*.vbproj" \) | while read -r proj; do
		TECH_FILES+=("$(basename "$proj")")
		LANGUAGES+=("C#/.NET")
	done

	# Swift
	[[ -f "$root/Package.swift" ]] && TECH_FILES+=("Package.swift") && LANGUAGES+=("Swift")

	# Elixir
	[[ -f "$root/mix.exs" ]] && TECH_FILES+=("mix.exs") && LANGUAGES+=("Elixir")

	# C/C++
	[[ -f "$root/CMakeLists.txt" ]] && TECH_FILES+=("CMakeLists.txt") && LANGUAGES+=("C/C++")
	[[ -f "$root/Makefile" ]] && TECH_FILES+=("Makefile")

	# Code style/config files
	[[ -f "$root/.editorconfig" ]] && TECH_FILES+=(".editorconfig")
	[[ -f "$root/.prettierrc" ]] && TECH_FILES+=(".prettierrc")
	[[ -f "$root/.prettierrc.json" ]] && TECH_FILES+=(".prettierrc.json")
	[[ -f "$root/.eslintrc" ]] && TECH_FILES+=(".eslintrc")
	[[ -f "$root/.eslintrc.json" ]] && TECH_FILES+=(".eslintrc.json")
	[[ -f "$root/rustfmt.toml" ]] && TECH_FILES+=("rustfmt.toml")
}

# Detect key directories
detect_directories() {
	local root="$1"

	# Source directories
	[[ -d "$root/src" ]] && DIRECTORIES+=("src")
	[[ -d "$root/lib" ]] && DIRECTORIES+=("lib")
	[[ -d "$root/app" ]] && DIRECTORIES+=("app")
	[[ -d "$root/pkg" ]] && DIRECTORIES+=("pkg")
	[[ -d "$root/internal" ]] && DIRECTORIES+=("internal")
	[[ -d "$root/cmd" ]] && DIRECTORIES+=("cmd")

	# Test directories
	[[ -d "$root/test" ]] && DIRECTORIES+=("test")
	[[ -d "$root/tests" ]] && DIRECTORIES+=("tests")
	[[ -d "$root/__tests__" ]] && DIRECTORIES+=("__tests__")
	[[ -d "$root/spec" ]] && DIRECTORIES+=("spec")

	# Documentation
	[[ -d "$root/docs" ]] && DIRECTORIES+=("docs")
	[[ -d "$root/documentation" ]] && DIRECTORIES+=("documentation")

	# Configuration
	[[ -d "$root/config" ]] && DIRECTORIES+=("config")
	[[ -d "$root/conf" ]] && DIRECTORIES+=("conf")
	[[ -d "$root/settings" ]] && DIRECTORIES+=("settings")

	# Frontend/Backend split
	[[ -d "$root/frontend" ]] && DIRECTORIES+=("frontend")
	[[ -d "$root/client" ]] && DIRECTORIES+=("client")
	[[ -d "$root/web" ]] && DIRECTORIES+=("web")
	[[ -d "$root/backend" ]] && DIRECTORIES+=("backend")
	[[ -d "$root/server" ]] && DIRECTORIES+=("server")
	[[ -d "$root/api" ]] && DIRECTORIES+=("api")

	# Database
	[[ -d "$root/migrations" ]] && DIRECTORIES+=("migrations")
	[[ -d "$root/models" ]] && DIRECTORIES+=("models")
	[[ -d "$root/schemas" ]] && DIRECTORIES+=("schemas")

	# Monorepo
	[[ -d "$root/packages" ]] && DIRECTORIES+=("packages")
	[[ -d "$root/apps" ]] && DIRECTORIES+=("apps")
	[[ -d "$root/services" ]] && DIRECTORIES+=("services")

	# Public/Static
	[[ -d "$root/public" ]] && DIRECTORIES+=("public")
	[[ -d "$root/static" ]] && DIRECTORIES+=("static")
	[[ -d "$root/assets" ]] && DIRECTORIES+=("assets")

	# Build/Dist
	[[ -d "$root/build" ]] && DIRECTORIES+=("build")
	[[ -d "$root/dist" ]] && DIRECTORIES+=("dist")
	[[ -d "$root/target" ]] && DIRECTORIES+=("target")
}

# Detect project type
detect_project_type() {
	local type="unknown"

	# Monorepo indicators
	if [[ -d "$REPO_ROOT/packages" ]] || [[ -d "$REPO_ROOT/apps" ]] || [[ -d "$REPO_ROOT/services" ]]; then
		type="monorepo"
	# Frontend + Backend split
	elif [[ -d "$REPO_ROOT/frontend" ]] && [[ -d "$REPO_ROOT/backend" ]]; then
		type="fullstack-split"
	elif [[ -d "$REPO_ROOT/client" ]] && [[ -d "$REPO_ROOT/server" ]]; then
		type="fullstack-split"
	# Web application
	elif [[ -f "$REPO_ROOT/package.json" ]] && grep -q "react\|vue\|angular\|svelte\|next\|nuxt" "$REPO_ROOT/package.json" 2>/dev/null; then
		type="web-frontend"
	# API/Backend
	elif [[ -d "$REPO_ROOT/api" ]] || [[ -d "$REPO_ROOT/server" ]]; then
		type="backend-api"
	# CLI tool
	elif [[ -d "$REPO_ROOT/cmd" ]] || ( [[ -f "$REPO_ROOT/package.json" ]] && grep -q "\"bin\":" "$REPO_ROOT/package.json" 2>/dev/null ); then
		type="cli-tool"
	# Library
	elif [[ -d "$REPO_ROOT/lib" ]] || ( [[ -f "$REPO_ROOT/Cargo.toml" ]] && grep -q "\[lib\]" "$REPO_ROOT/Cargo.toml" 2>/dev/null ); then
		type="library"
	# Generic application
	elif [[ -d "$REPO_ROOT/src" ]]; then
		type="application"
	fi

	echo "$type"
}

# Run detection
detect_config_files "$REPO_ROOT"
detect_directories "$REPO_ROOT"
PROJECT_TYPE=$(detect_project_type)

# Deduplicate languages array
if [ ${#LANGUAGES[@]} -eq 0 ]; then
	UNIQUE_LANGUAGES=()
else
	UNIQUE_LANGUAGES=($(printf '%s\n' "${LANGUAGES[@]}" | sort -u))
fi

# Output as JSON if requested
if [ "$JSON_OUTPUT" = true ]; then
	# Convert arrays to JSON arrays (handle empty arrays)
	if [ ${#TECH_FILES[@]} -eq 0 ]; then
		tech_files_json="[]"
	else
		tech_files_json=$(printf '%s\n' "${TECH_FILES[@]}" | jq -R . | jq -s .)
	fi

	if [ ${#DIRECTORIES[@]} -eq 0 ]; then
		directories_json="[]"
	else
		directories_json=$(printf '%s\n' "${DIRECTORIES[@]}" | jq -R . | jq -s .)
	fi

	if [ ${#UNIQUE_LANGUAGES[@]} -eq 0 ]; then
		languages_json="[]"
	else
		languages_json=$(printf '%s\n' "${UNIQUE_LANGUAGES[@]}" | jq -R . | jq -s .)
	fi

	# Output JSON
	jq -n \
		--arg repo_root "$REPO_ROOT" \
		--arg project_type "$PROJECT_TYPE" \
		--argjson tech_files "$tech_files_json" \
		--argjson directories "$directories_json" \
		--argjson languages "$languages_json" \
		'{
			REPO_ROOT: $repo_root,
			PROJECT_TYPE: $project_type,
			TECH_FILES: $tech_files,
			DIRECTORIES: $directories,
			LANGUAGES: $languages
		}'
else
	# Human-readable output
	echo "Repository Root: $REPO_ROOT"
	echo "Project Type: $PROJECT_TYPE"
	echo ""
	echo "Languages:"
	if [ ${#UNIQUE_LANGUAGES[@]} -gt 0 ]; then
		printf '  - %s\n' "${UNIQUE_LANGUAGES[@]}"
	else
		echo "  (none detected)"
	fi
	echo ""
	echo "Configuration Files:"
	if [ ${#TECH_FILES[@]} -gt 0 ]; then
		printf '  - %s\n' "${TECH_FILES[@]}"
	else
		echo "  (none detected)"
	fi
	echo ""
	echo "Key Directories:"
	if [ ${#DIRECTORIES[@]} -gt 0 ]; then
		printf '  - %s\n' "${DIRECTORIES[@]}"
	else
		echo "  (none detected)"
	fi
fi
