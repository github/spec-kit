#!/usr/bin/env bash

# Create release packages for Spec Kit templates
#
# This script generates zip archives for each supported AI agent,
# containing pre-configured command files and directory structures.

set -euo pipefail

# create-release-packages.sh (workflow-local)
# Build Spec Kit template release archives for each supported AI assistant and script type.
# Usage: .github/workflows/scripts/create-release-packages.sh <version>
#   Version argument should include leading 'v'.
#   Optionally set AGENTS and/or SCRIPTS env vars to limit what gets built.
#     AGENTS  : space or comma separated subset of: claude gemini copilot cursor-agent qwen opencode windsurf codex kilocode auggie roo codebuddy amp shai tabnine kiro-cli agy bob vibe qodercli kimi generic (default: all)
#     SCRIPTS : space or comma separated subset of: sh ps (default: both)
#   Examples:
#     AGENTS=claude SCRIPTS=sh $0 v0.2.0
#     AGENTS="copilot,gemini" $0 v0.2.0
#     SCRIPTS=ps $0 v0.2.0

#==============================================================================
# Configuration
#==============================================================================

# All supported agents
ALL_AGENTS=(copilot claude gemini cursor-agent qwen opencode codex windsurf kilocode auggie codebuddy qodercli roo kiro-cli amp shai tabnine agy bob vibe kimi generic)

# Version from git tag or default
VERSION="${VERSION:-$(git describe --tags --always 2>/dev/null || echo 'dev')}"

# Output directory
OUTPUT_DIR=".genreleases"

#==============================================================================
# Functions
#==============================================================================

# Generate command files for an agent
generate_commands() {
    local agent="$1"
    local format="$2"
    local args="$3"
    local dest_dir="$4"
    local script="$5"
    
    # Command names follow the speckit.* pattern
    local commands=(
        "speckit.constitution"
        "speckit.specify"
        "speckit.clarify"
        "speckit.plan"
        "speckit.tasks"
        "speckit.analyze"
        "speckit.checklist"
        "speckit.implement"
        "speckit.taskstoissues"
        "add-dir"
    )
    
    for cmd in "${commands[@]}"; do
        local filename="${cmd}.${format}"
        local filepath="${dest_dir}/${filename}"
        
        # Create command file with appropriate format
        case "$format" in
            md)
                cat > "$filepath" << EOF
---
description: "${cmd} command for Spec Kit"
---

# ${cmd}

Execute the ${cmd} workflow with arguments: ${args}
EOF
                ;;
            toml)
                cat > "$filepath" << EOF
description = "${cmd} command for Spec Kit"

prompt = """
Execute the ${cmd} workflow with arguments: ${args}
"""
EOF
                ;;
        esac
    done
}

# Create release package for an agent
create_package() {
    local agent="$1"
    local script="$2"  # sh or ps
    
    local base_dir="${OUTPUT_DIR}/temp-${agent}-${script}"
    
    # Create directory structure based on agent type
    case "$agent" in
        copilot)
            mkdir -p "$base_dir/.github/agents"
            generate_commands copilot md "$ARGUMENTS" "$base_dir/.github/agents" "$script"
            ;;
        claude)
            mkdir -p "$base_dir/.claude/commands"
            generate_commands claude md "$ARGUMENTS" "$base_dir/.claude/commands" "$script"
            ;;
        gemini)
            mkdir -p "$base_dir/.gemini/commands"
            generate_commands gemini toml "{{args}}" "$base_dir/.gemini/commands" "$script"
            ;;
        cursor-agent)
            mkdir -p "$base_dir/.cursor/commands"
            generate_commands cursor-agent md "$ARGUMENTS" "$base_dir/.cursor/commands" "$script"
            ;;
        qwen)
            mkdir -p "$base_dir/.qwen/commands"
            generate_commands qwen toml "{{args}}" "$base_dir/.qwen/commands" "$script"
            ;;
        opencode)
            mkdir -p "$base_dir/.opencode/command"
            generate_commands opencode md "$ARGUMENTS" "$base_dir/.opencode/command" "$script"
            ;;
        codex)
            mkdir -p "$base_dir/.codex/prompts"
            generate_commands codex md "$ARGUMENTS" "$base_dir/.codex/prompts" "$script"
            ;;
        windsurf)
            mkdir -p "$base_dir/.windsurf/workflows"
            generate_commands windsurf md "$ARGUMENTS" "$base_dir/.windsurf/workflows" "$script"
            ;;
        kilocode)
            mkdir -p "$base_dir/.kilocode/workflows"
            generate_commands kilocode md "$ARGUMENTS" "$base_dir/.kilocode/workflows" "$script"
            ;;
        auggie)
            mkdir -p "$base_dir/.augment/commands"
            generate_commands auggie md "$ARGUMENTS" "$base_dir/.augment/commands" "$script"
            ;;
        codebuddy)
            mkdir -p "$base_dir/.codebuddy/commands"
            generate_commands codebuddy md "$ARGUMENTS" "$base_dir/.codebuddy/commands" "$script"
            ;;
        qodercli)
            mkdir -p "$base_dir/.qoder/commands"
            generate_commands qodercli md "$ARGUMENTS" "$base_dir/.qoder/commands" "$script"
            ;;
        roo)
            mkdir -p "$base_dir/.roo/rules"
            generate_commands roo md "$ARGUMENTS" "$base_dir/.roo/rules" "$script"
            ;;
        kiro-cli)
            mkdir -p "$base_dir/.kiro/prompts"
            generate_commands kiro-cli md "$ARGUMENTS" "$base_dir/.kiro/prompts" "$script"
            ;;
        amp)
            mkdir -p "$base_dir/.agents/commands"
            generate_commands amp md "$ARGUMENTS" "$base_dir/.agents/commands" "$script"
            ;;
        shai)
            mkdir -p "$base_dir/.shai/commands"
            generate_commands shai md "$ARGUMENTS" "$base_dir/.shai/commands" "$script"
            ;;
        agy)
            mkdir -p "$base_dir/.agent/workflows"
            generate_commands agy md "$ARGUMENTS" "$base_dir/.agent/workflows" "$script"
            ;;
        bob)
            mkdir -p "$base_dir/.bob/commands"
            generate_commands bob md "$ARGUMENTS" "$base_dir/.bob/commands" "$script"
            ;;
        tabnine)
            mkdir -p "$base_dir/.tabnine/agent/commands"
            generate_commands tabnine toml "{{args}}" "$base_dir/.tabnine/agent/commands" "$script"
            ;;
        vibe)
            mkdir -p "$base_dir/.vibe/prompts"
            generate_commands vibe md "$ARGUMENTS" "$base_dir/.vibe/prompts" "$script"
            ;;
        kimi)
            mkdir -p "$base_dir/.kimi/commands"
            generate_commands kimi md "$ARGUMENTS" "$base_dir/.kimi/commands" "$script"
            ;;
        generic)
            mkdir -p "$base_dir/.speckit/commands"
            generate_commands generic md "$ARGUMENTS" "$base_dir/.speckit/commands" "$script"
            ;;
    esac

    # Create the zip archive
    local zip_name="spec-kit-template-${agent}-${script}-${VERSION}.zip"
    (cd "$base_dir" && zip -r "../${zip_name}" .)

    # Cleanup temp directory
    rm -rf "$base_dir"

    echo "Created: ${zip_name}"
}

#==============================================================================
# Main
#==============================================================================

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Clean up old temp directories
rm -rf "${OUTPUT_DIR}"/temp-*

# Generate packages for all agents
echo "Generating release packages for version: $VERSION"
echo ""

for agent in "${ALL_AGENTS[@]}"; do
    echo "Processing agent: $agent"
    
    # Create bash/zsh package
    ARGUMENTS="$ARGUMENTS"
    create_package "$agent" "sh"
    
    # Create PowerShell package
    ARGUMENTS="$ARGUMENTS"
    create_package "$agent" "ps"
done

echo ""
echo "All packages created in: $OUTPUT_DIR"
echo "Packages:"
ls -la "$OUTPUT_DIR"/spec-kit-template-*-"${VERSION}".zip 2>/dev/null || echo "No packages found"
