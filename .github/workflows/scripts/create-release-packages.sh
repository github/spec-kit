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

# Placeholder string used in generated command files (can be overridden via env)
ARGUMENTS="${ARGUMENTS:-\$ARGUMENTS}"

# Repository root (3 levels up from this script's location)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"
TEMPLATES_DIR="$REPO_ROOT/templates"
COMMANDS_TEMPLATES_DIR="$TEMPLATES_DIR/commands"

#==============================================================================
# Functions
#==============================================================================

# Copy real command files (from templates/commands/) into an agent's commands dir.
# Files are renamed with the speckit. prefix (e.g. specify.md -> speckit.specify.md).
# add-dir.md has no real template yet, so a stub is generated for it.
copy_real_md_commands() {
    local dest_dir="$1"

    local commands=(constitution specify clarify plan tasks analyze checklist implement taskstoissues)
    for cmd in "${commands[@]}"; do
        local src="$COMMANDS_TEMPLATES_DIR/${cmd}.md"
        if [[ -f "$src" ]]; then
            cp "$src" "$dest_dir/speckit.${cmd}.md"
        fi
    done

    # add-dir.md: no real template exists yet, generate a stub
    cat > "$dest_dir/add-dir.md" << 'EOF'
---
description: "add-dir command for Spec Kit"
---

# add-dir

Execute the add-dir workflow with arguments: $ARGUMENTS
EOF
}

# Create Kimi Code skills in .kimi/skills/<name>/SKILL.md format.
# Kimi CLI discovers skills as directories containing a SKILL.md file,
# invoked with /skill:<name> (e.g. /skill:speckit.specify).
create_kimi_skills() {
    local skills_dir="$1"

    local commands=(constitution specify clarify plan tasks analyze checklist implement taskstoissues)
    for cmd in "${commands[@]}"; do
        local skill_name="speckit.${cmd}"
        local skill_dir="${skills_dir}/${skill_name}"
        mkdir -p "$skill_dir"

        # Extract description from template frontmatter if available, else use a default
        local src="$COMMANDS_TEMPLATES_DIR/${cmd}.md"
        local description="Spec Kit: ${cmd} workflow"
        if [[ -f "$src" ]]; then
            local fm_desc
            fm_desc=$(grep -m1 '^description:' "$src" | sed 's/^description:[[:space:]]*//' | tr -d '"' || true)
            [[ -n "$fm_desc" ]] && description="$fm_desc"
        fi

        # Write SKILL.md with Kimi frontmatter + template content
        {
            printf -- '---\n'
            printf 'name: "%s"\n' "$skill_name"
            printf 'description: "%s"\n' "$description"
            printf -- '---\n\n'
            if [[ -f "$src" ]]; then
                # Strip existing frontmatter from template and append the body
                awk '/^---/{p++; if(p==2){found=1; next}} found' "$src"
            fi
        } > "$skill_dir/SKILL.md"
    done

    # add-dir skill
    mkdir -p "${skills_dir}/add-dir"
    cat > "${skills_dir}/add-dir/SKILL.md" << 'EOF'
---
name: "add-dir"
description: "Add a directory to the Spec Kit project structure"
---

Execute the add-dir workflow with arguments: $ARGUMENTS
EOF
}

# Generate toml command files for agents that use that format (gemini, qwen).
generate_toml_commands() {
    local agent="$1"
    local args="$2"
    local dest_dir="$3"

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
        cat > "$dest_dir/${cmd}.toml" << EOF
description = "${cmd} command for Spec Kit"

prompt = """
Execute the ${cmd} workflow with arguments: ${args}
"""
EOF
    done
}

# Add .specify/templates/ directory to a package (required for constitution setup).
add_specify_templates() {
    local base_dir="$1"
    mkdir -p "$base_dir/.specify/templates"

    local templates=(
        agent-file-template.md
        checklist-template.md
        constitution-template.md
        plan-template.md
        spec-template.md
        tasks-template.md
    )
    for tmpl in "${templates[@]}"; do
        local src="$TEMPLATES_DIR/$tmpl"
        if [[ -f "$src" ]]; then
            cp "$src" "$base_dir/.specify/templates/"
        fi
    done
}

# Add .vscode/settings.json to a package.
add_vscode_settings() {
    local base_dir="$1"
    local src="$TEMPLATES_DIR/vscode-settings.json"
    if [[ -f "$src" ]]; then
        mkdir -p "$base_dir/.vscode"
        cp "$src" "$base_dir/.vscode/settings.json"
    fi
}

# Create release package for an agent
create_package() {
    local agent="$1"
    local script="$2"  # sh or ps

    local base_dir="${OUTPUT_DIR}/temp-${agent}-${script}"

    # Create agent-specific commands directory and populate it
    case "$agent" in
        copilot)
            mkdir -p "$base_dir/.github/agents"
            copy_real_md_commands "$base_dir/.github/agents"
            ;;
        claude)
            mkdir -p "$base_dir/.claude/commands"
            copy_real_md_commands "$base_dir/.claude/commands"
            ;;
        gemini)
            mkdir -p "$base_dir/.gemini/commands"
            generate_toml_commands gemini "{{args}}" "$base_dir/.gemini/commands"
            ;;
        cursor-agent)
            mkdir -p "$base_dir/.cursor/commands"
            copy_real_md_commands "$base_dir/.cursor/commands"
            ;;
        qwen)
            mkdir -p "$base_dir/.qwen/commands"
            generate_toml_commands qwen "{{args}}" "$base_dir/.qwen/commands"
            ;;
        opencode)
            mkdir -p "$base_dir/.opencode/command"
            copy_real_md_commands "$base_dir/.opencode/command"
            ;;
        codex)
            mkdir -p "$base_dir/.codex/prompts"
            copy_real_md_commands "$base_dir/.codex/prompts"
            ;;
        windsurf)
            mkdir -p "$base_dir/.windsurf/workflows"
            copy_real_md_commands "$base_dir/.windsurf/workflows"
            ;;
        kilocode)
            mkdir -p "$base_dir/.kilocode/workflows"
            copy_real_md_commands "$base_dir/.kilocode/workflows"
            ;;
        auggie)
            mkdir -p "$base_dir/.augment/commands"
            copy_real_md_commands "$base_dir/.augment/commands"
            ;;
        codebuddy)
            mkdir -p "$base_dir/.codebuddy/commands"
            copy_real_md_commands "$base_dir/.codebuddy/commands"
            ;;
        qodercli)
            mkdir -p "$base_dir/.qoder/commands"
            copy_real_md_commands "$base_dir/.qoder/commands"
            ;;
        roo)
            mkdir -p "$base_dir/.roo/rules"
            copy_real_md_commands "$base_dir/.roo/rules"
            ;;
        kiro-cli)
            mkdir -p "$base_dir/.kiro/prompts"
            copy_real_md_commands "$base_dir/.kiro/prompts"
            ;;
        amp)
            mkdir -p "$base_dir/.agents/commands"
            copy_real_md_commands "$base_dir/.agents/commands"
            ;;
        shai)
            mkdir -p "$base_dir/.shai/commands"
            copy_real_md_commands "$base_dir/.shai/commands"
            ;;
        agy)
            mkdir -p "$base_dir/.agent/workflows"
            copy_real_md_commands "$base_dir/.agent/workflows"
            ;;
        bob)
            mkdir -p "$base_dir/.bob/commands"
            copy_real_md_commands "$base_dir/.bob/commands"
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
            mkdir -p "$base_dir/.kimi/skills"
            create_kimi_skills "$base_dir/.kimi/skills"
            ;;
        generic)
            mkdir -p "$base_dir/.speckit/commands"
            generate_commands generic md "$ARGUMENTS" "$base_dir/.speckit/commands" "$script"
            ;;
    esac

    # Add .specify/templates/ (needed by ensure_constitution_from_template)
    # and .vscode/settings.json to every package.
    # Having multiple top-level dirs also prevents the extraction flatten heuristic
    # from incorrectly stripping the agent config directory.
    add_specify_templates "$base_dir"
    add_vscode_settings "$base_dir"


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
    create_package "$agent" "sh"

    # Create PowerShell package
    create_package "$agent" "ps"
done

echo ""
echo "All packages created in: $OUTPUT_DIR"
echo "Packages:"
ls -la "$OUTPUT_DIR"/spec-kit-template-*-"${VERSION}".zip 2>/dev/null || echo "No packages found"
