#!/usr/bin/env bash
set -euo pipefail

# create-release-packages.sh
# Build Spec Kit template release archives for each supported AI assistant.
# Usage: ./scripts/create-release-packages.sh <version>
# <version> should include the leading 'v' (e.g. v0.0.4)

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <version-with-v-prefix>" >&2
  exit 1
fi

NEW_VERSION="$1"
if [[ ! $NEW_VERSION =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  echo "Version must look like v0.0.0" >&2
  exit 1
fi

echo "Building release packages for $NEW_VERSION"

# Clean any previous build dirs
rm -rf sdd-package-base sdd-claude-package sdd-gemini-package sdd-copilot-package \
       spec-kit-template-claude-${NEW_VERSION}.zip \
       spec-kit-template-gemini-${NEW_VERSION}.zip \
       spec-kit-template-copilot-${NEW_VERSION}.zip || true

mkdir -p sdd-package-base

# Copy common folders to base
if [[ -d memory ]]; then
  cp -r memory sdd-package-base/
  echo "Copied memory folder"
fi

if [[ -d scripts ]]; then
  # Exclude this script itself from being copied
  rsync -a --exclude 'create-release-packages.sh' scripts/ sdd-package-base/scripts/
  echo "Copied scripts folder (excluding create-release-packages.sh)"
fi

if [[ -d templates ]]; then
  mkdir -p sdd-package-base/templates
  # Copy all template files excluding commands (processed separately per assistant)
  find templates -type f -not -path "templates/commands/*" -exec cp --parents {} sdd-package-base/ \;
  echo "Copied templates folder (excluding commands directory)"
fi

# Function to generate assistant command files/prompts
# Args: agent ext arg_format output_dir
generate_commands() {
  local agent=$1
  local ext=$2
  local arg_format=$3
  local output_dir=$4
  mkdir -p "$output_dir"
  for template in templates/commands/*.md; do
    [[ -f "$template" ]] || continue
    local name
    name=$(basename "$template" .md)
    local description
    description=$(awk '/^description:/ {gsub(/^description: *"?/, ""); gsub(/"$/, ""); print; exit}' "$template" | tr -d '\r')
    local content
    content=$(awk '/^---$/{if(++count==2) start=1; next} start' "$template" | sed "s/{ARGS}/$arg_format/g")
    case $ext in
      "toml")
        {
          echo "description = \"$description\""; echo ""; echo "prompt = \"\"\""; echo "$content"; echo "\"\"\"";
        } > "$output_dir/$name.$ext"
        ;;
      "md")
        echo "$content" > "$output_dir/$name.$ext"
        ;;
      "prompt.md")
        # Preserve front matter exactly, just substitute {ARGS}
        sed "s/{ARGS}/$arg_format/g" "$template" > "$output_dir/$name.$ext"
        ;;
    esac
  done
}

# Claude package
mkdir -p sdd-claude-package
cp -r sdd-package-base/* sdd-claude-package/
mkdir -p sdd-claude-package/.claude/commands
generate_commands "claude" "md" "\$ARGUMENTS" "sdd-claude-package/.claude/commands"
echo "Created Claude Code package"

# Gemini package
mkdir -p sdd-gemini-package
cp -r sdd-package-base/* sdd-gemini-package/
mkdir -p sdd-gemini-package/.gemini/commands
generate_commands "gemini" "toml" "{{args}}" "sdd-gemini-package/.gemini/commands"
if [[ -f agent_templates/gemini/GEMINI.md ]]; then
  cp agent_templates/gemini/GEMINI.md sdd-gemini-package/GEMINI.md
fi
echo "Created Gemini CLI package"

# Copilot package
mkdir -p sdd-copilot-package
cp -r sdd-package-base/* sdd-copilot-package/
mkdir -p sdd-copilot-package/.github/prompts
generate_commands "copilot" "prompt.md" "\$ARGUMENTS" "sdd-copilot-package/.github/prompts"
echo "Created GitHub Copilot package"

# Archives
( cd sdd-claude-package && zip -r ../spec-kit-template-claude-${NEW_VERSION}.zip . )
( cd sdd-gemini-package && zip -r ../spec-kit-template-gemini-${NEW_VERSION}.zip . )
( cd sdd-copilot-package && zip -r ../spec-kit-template-copilot-${NEW_VERSION}.zip . )

echo "Package archives created:"
ls -1 spec-kit-template-*-${NEW_VERSION}.zip

# Basic verification snippet
unzip -l spec-kit-template-copilot-${NEW_VERSION}.zip | head -10 || true
