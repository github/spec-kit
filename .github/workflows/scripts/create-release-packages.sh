#!/usr/bin/env bash
set -euo pipefail

# create-release-packages.sh (workflow-local)
# Build Spec Kit template release archives for each supported AI assistant.
# Usage: .github/workflows/scripts/create-release-packages.sh <version>
# Version argument should include leading 'v'.

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

rm -rf sdd-package-base sdd-claude-package sdd-gemini-package sdd-copilot-package \
       spec-kit-template-claude-${NEW_VERSION}.zip \
       spec-kit-template-gemini-${NEW_VERSION}.zip \
       spec-kit-template-copilot-${NEW_VERSION}.zip || true

mkdir -p sdd-package-base
SPEC_DIR="sdd-package-base/.specify"
mkdir -p "$SPEC_DIR"

[[ -d memory ]] && { cp -r memory "$SPEC_DIR/"; echo "Copied memory -> .specify"; }
[[ -d scripts ]] && { cp -r scripts "$SPEC_DIR/"; echo "Copied scripts -> .specify/scripts"; }
[[ -d templates ]] && { mkdir -p "$SPEC_DIR/templates"; find templates -type f -not -path "templates/commands/*" -exec cp --parents {} "$SPEC_DIR"/ \;; echo "Copied templates -> .specify/templates"; }

rewrite_paths() {
  sed -E \
    -e 's@(/?)memory/@.specify/memory/@g' \
    -e 's@(/?)scripts/@.specify/scripts/@g' \
    -e 's@(/?)templates/@.specify/templates/@g'
}

generate_commands() {
  local agent=$1 ext=$2 arg_format=$3 output_dir=$4
  mkdir -p "$output_dir"
  for template in templates/commands/*.md; do
    [[ -f "$template" ]] || continue
    local name description body
    name=$(basename "$template" .md)
    description=$(awk '/^description:/ {gsub(/^description: *"?/, ""); gsub(/"$/, ""); print; exit}' "$template" | tr -d '\r')
    body=$(awk '/^---$/{if(++count==2) start=1; next} start' "$template" | sed "s/{ARGS}/$arg_format/g" | rewrite_paths)
    case $ext in
      toml)
        { echo "description = \"$description\""; echo; echo "prompt = \"\"\""; echo "$body"; echo "\"\"\""; } > "$output_dir/$name.$ext" ;;
      md)
        echo "$body" > "$output_dir/$name.$ext" ;;
      prompt.md)
        sed "s/{ARGS}/$arg_format/g" "$template" | rewrite_paths > "$output_dir/$name.$ext" ;;
    esac
  done
}

# Create Claude package
echo "Building Claude package..."
mkdir -p sdd-claude-package
cp -r sdd-package-base/. sdd-claude-package/
mkdir -p sdd-claude-package/.claude/commands
generate_commands claude md "\$ARGUMENTS" sdd-claude-package/.claude/commands
echo "Created Claude package"

# Create Gemini package
echo "Building Gemini package..."
mkdir -p sdd-gemini-package
cp -r sdd-package-base/. sdd-gemini-package/
mkdir -p sdd-gemini-package/.gemini/commands
generate_commands gemini toml "{{args}}" sdd-gemini-package/.gemini/commands
[[ -f agent_templates/gemini/GEMINI.md ]] && cp agent_templates/gemini/GEMINI.md sdd-gemini-package/GEMINI.md
echo "Created Gemini package"

# Create Copilot package
echo "Building Copilot package..."
mkdir -p sdd-copilot-package
cp -r sdd-package-base/. sdd-copilot-package/
mkdir -p sdd-copilot-package/.github/prompts
generate_commands copilot prompt.md "\$ARGUMENTS" sdd-copilot-package/.github/prompts
echo "Created Copilot package"

( cd sdd-claude-package && zip -r ../spec-kit-template-claude-${NEW_VERSION}.zip . )
( cd sdd-gemini-package && zip -r ../spec-kit-template-gemini-${NEW_VERSION}.zip . )
( cd sdd-copilot-package && zip -r ../spec-kit-template-copilot-${NEW_VERSION}.zip . )

echo "Archives:"
ls -1 spec-kit-template-*-${NEW_VERSION}.zip
unzip -l spec-kit-template-copilot-${NEW_VERSION}.zip | head -10 || true
