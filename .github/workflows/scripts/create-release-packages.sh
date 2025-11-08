#!/usr/bin/env bash
set -euo pipefail

# create-release-packages.sh (workflow-local)
# Build Spec Kit template release archives for each supported AI assistant.
# Generates unified packages containing both bash and PowerShell scripts.
# Usage: .github/workflows/scripts/create-release-packages.sh <version>
#   Version argument should include leading 'v'.
#   Optionally set AGENTS env var to limit which agents get built.
#     AGENTS  : space or comma separated subset of: claude gemini copilot cursor-agent qwen opencode windsurf codex amp (default: all)
#   Examples:
#     AGENTS=claude $0 v0.2.0
#     AGENTS="copilot,gemini" $0 v0.2.0
#     $0 v0.2.0  # Build all agents

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

# Create and use .genreleases directory for all build artifacts
GENRELEASES_DIR=".genreleases"
mkdir -p "$GENRELEASES_DIR"
rm -rf "$GENRELEASES_DIR"/* || true

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
    local name description script_bash script_powershell agent_script_bash agent_script_powershell body
    name=$(basename "$template" .md)

    # Normalize line endings
    file_content=$(tr -d '\r' < "$template")

    # Extract description from YAML frontmatter
    description=$(printf '%s\n' "$file_content" | awk '/^description:/ {sub(/^description:[[:space:]]*/, ""); print; exit}')

    # Extract BOTH bash and powershell script commands from YAML frontmatter
    script_bash=$(printf '%s\n' "$file_content" | awk '
      /^scripts:$/ { in_scripts=1; next }
      in_scripts && /^[[:space:]]*bash:[[:space:]]*/ {
        sub(/^[[:space:]]*bash:[[:space:]]*/, "")
        print
        exit
      }
      in_scripts && /^[a-zA-Z]/ { in_scripts=0 }
    ')

    script_powershell=$(printf '%s\n' "$file_content" | awk '
      /^scripts:$/ { in_scripts=1; next }
      in_scripts && /^[[:space:]]*powershell:[[:space:]]*/ {
        sub(/^[[:space:]]*powershell:[[:space:]]*/, "")
        print
        exit
      }
      in_scripts && /^[a-zA-Z]/ { in_scripts=0 }
    ')

    if [[ -z $script_bash && -z $script_powershell ]]; then
      echo "Warning: no script commands found in $template" >&2
    fi

    # Extract agent_script commands from YAML frontmatter if present
    agent_script_bash=$(printf '%s\n' "$file_content" | awk '
      /^agent_scripts:$/ { in_agent_scripts=1; next }
      in_agent_scripts && /^[[:space:]]*bash:[[:space:]]*/ {
        sub(/^[[:space:]]*bash:[[:space:]]*/, "")
        print
        exit
      }
      in_agent_scripts && /^[a-zA-Z]/ { in_agent_scripts=0 }
    ')

    agent_script_powershell=$(printf '%s\n' "$file_content" | awk '
      /^agent_scripts:$/ { in_agent_scripts=1; next }
      in_agent_scripts && /^[[:space:]]*powershell:[[:space:]]*/ {
        sub(/^[[:space:]]*powershell:[[:space:]]*/, "")
        print
        exit
      }
      in_agent_scripts && /^[a-zA-Z]/ { in_agent_scripts=0 }
    ')

    # Replace {SCRIPT_BASH} and {SCRIPT_POWERSHELL} placeholders
    body=$(printf '%s\n' "$file_content" | sed "s|{SCRIPT_BASH}|${script_bash}|g" | sed "s|{SCRIPT_POWERSHELL}|${script_powershell}|g")

    # Replace {AGENT_SCRIPT_BASH} and {AGENT_SCRIPT_POWERSHELL} placeholders if found
    if [[ -n $agent_script_bash ]]; then
      body=$(printf '%s\n' "$body" | sed "s|{AGENT_SCRIPT_BASH}|${agent_script_bash}|g")
    fi
    if [[ -n $agent_script_powershell ]]; then
      body=$(printf '%s\n' "$body" | sed "s|{AGENT_SCRIPT_POWERSHELL}|${agent_script_powershell}|g")
    fi

    # Keep the scripts: and agent_scripts: sections in frontmatter for AI reference
    # (Don't remove them anymore)

    # Apply other substitutions
    body=$(printf '%s\n' "$body" | sed "s/{ARGS}/$arg_format/g" | sed "s/__AGENT__/$agent/g" | rewrite_paths)

    case $ext in
      toml)
        body=$(printf '%s\n' "$body" | sed 's/\\/\\\\/g')
        { echo "description = \"$description\""; echo; echo "prompt = \"\"\""; echo "$body"; echo "\"\"\""; } > "$output_dir/speckit.$name.$ext" ;;
      md)
        echo "$body" > "$output_dir/speckit.$name.$ext" ;;
      prompt.md)
        echo "$body" > "$output_dir/speckit.$name.$ext" ;;
    esac
  done
}

build_unified() {
  local agent=$1
  local base_dir="$GENRELEASES_DIR/sdd-${agent}-package-unified"
  echo "Building $agent (unified) package..."
  mkdir -p "$base_dir"

  # Copy base structure with BOTH script directories
  SPEC_DIR="$base_dir/.specify"
  mkdir -p "$SPEC_DIR"

  [[ -d memory ]] && { cp -r memory "$SPEC_DIR/"; echo "Copied memory -> .specify"; }

  # Copy BOTH bash and powershell script directories
  if [[ -d scripts ]]; then
    mkdir -p "$SPEC_DIR/scripts"
    [[ -d scripts/bash ]] && {
      cp -r scripts/bash "$SPEC_DIR/scripts/"
      echo "Copied scripts/bash -> .specify/scripts"
    }
    [[ -d scripts/powershell ]] && {
      cp -r scripts/powershell "$SPEC_DIR/scripts/"
      echo "Copied scripts/powershell -> .specify/scripts"
    }
    # Copy any script files that aren't in variant-specific directories
    find scripts -maxdepth 1 -type f -exec cp {} "$SPEC_DIR/scripts/" \; 2>/dev/null || true
  fi

  [[ -d templates ]] && { mkdir -p "$SPEC_DIR/templates"; find templates -type f -not -path "templates/commands/*" -not -name "vscode-settings.json" -exec cp --parents {} "$SPEC_DIR"/ \; ; echo "Copied templates -> .specify/templates"; }
  
  # NOTE: We substitute {ARGS} internally. Outward tokens differ intentionally:
  #   * Markdown/prompt (claude, copilot, cursor-agent, opencode): $ARGUMENTS
  #   * TOML (gemini, qwen): {{args}}
  # This keeps formats readable without extra abstraction.

  case $agent in
    claude)
      mkdir -p "$base_dir/.claude/commands"
      generate_commands claude md "\$ARGUMENTS" "$base_dir/.claude/commands" ;;
    gemini)
      mkdir -p "$base_dir/.gemini/commands"
      generate_commands gemini toml "{{args}}" "$base_dir/.gemini/commands"
      [[ -f agent_templates/gemini/GEMINI.md ]] && cp agent_templates/gemini/GEMINI.md "$base_dir/GEMINI.md" ;;
    copilot)
      mkdir -p "$base_dir/.github/prompts"
      generate_commands copilot prompt.md "\$ARGUMENTS" "$base_dir/.github/prompts"
      # Create VS Code workspace settings
      mkdir -p "$base_dir/.vscode"
      [[ -f templates/vscode-settings.json ]] && cp templates/vscode-settings.json "$base_dir/.vscode/settings.json"
      ;;
    cursor-agent)
      mkdir -p "$base_dir/.cursor/commands"
      generate_commands cursor-agent md "\$ARGUMENTS" "$base_dir/.cursor/commands" ;;
    qwen)
      mkdir -p "$base_dir/.qwen/commands"
      generate_commands qwen toml "{{args}}" "$base_dir/.qwen/commands"
      [[ -f agent_templates/qwen/QWEN.md ]] && cp agent_templates/qwen/QWEN.md "$base_dir/QWEN.md" ;;
    opencode)
      mkdir -p "$base_dir/.opencode/command"
      generate_commands opencode md "\$ARGUMENTS" "$base_dir/.opencode/command" ;;
    windsurf)
      mkdir -p "$base_dir/.windsurf/workflows"
      generate_commands windsurf md "\$ARGUMENTS" "$base_dir/.windsurf/workflows" ;;
    codex)
      mkdir -p "$base_dir/.codex/prompts"
      generate_commands codex md "\$ARGUMENTS" "$base_dir/.codex/prompts" ;;
    kilocode)
      mkdir -p "$base_dir/.kilocode/workflows"
      generate_commands kilocode md "\$ARGUMENTS" "$base_dir/.kilocode/workflows" ;;
    auggie)
      mkdir -p "$base_dir/.augment/commands"
      generate_commands auggie md "\$ARGUMENTS" "$base_dir/.augment/commands" ;;
    roo)
      mkdir -p "$base_dir/.roo/commands"
      generate_commands roo md "\$ARGUMENTS" "$base_dir/.roo/commands" ;;
    codebuddy)
      mkdir -p "$base_dir/.codebuddy/commands"
      generate_commands codebuddy md "\$ARGUMENTS" "$base_dir/.codebuddy/commands" ;;
    amp)
      mkdir -p "$base_dir/.agents/commands"
      generate_commands amp md "\$ARGUMENTS" "$base_dir/.agents/commands" ;;
    q)
      mkdir -p "$base_dir/.amazonq/prompts"
      generate_commands q md "\$ARGUMENTS" "$base_dir/.amazonq/prompts" ;;
  esac
  ( cd "$base_dir" && zip -r "../spec-kit-template-${agent}-${NEW_VERSION}.zip" . )
  echo "Created $GENRELEASES_DIR/spec-kit-template-${agent}-${NEW_VERSION}.zip"
}

# Determine agent list
ALL_AGENTS=(claude gemini copilot cursor-agent qwen opencode windsurf codex kilocode auggie roo codebuddy amp q)

norm_list() {
  # convert comma+space separated -> newline separated unique while preserving order of first occurrence
  tr ',\n' '  ' | awk '{
    for(i=1;i<=NF;i++){
      if(!seen[$i]++){
        print $i
      }
    }
  }'
}

validate_subset() {
  local type=$1; shift; local -n allowed=$1; shift; local items=("$@")
  local ok=0
  for it in "${items[@]}"; do
    local found=0
    for a in "${allowed[@]}"; do [[ $it == "$a" ]] && { found=1; break; }; done
    if [[ $found -eq 0 ]]; then
      echo "Error: unknown $type '$it' (allowed: ${allowed[*]})" >&2
      ok=1
    fi
  done
  return $ok
}

if [[ -n ${AGENTS:-} ]]; then
  mapfile -t AGENT_LIST < <(printf '%s' "$AGENTS" | norm_list)
  validate_subset agent ALL_AGENTS "${AGENT_LIST[@]}" || exit 1
else
  AGENT_LIST=("${ALL_AGENTS[@]}")
fi

echo "Agents: ${AGENT_LIST[*]}"
echo "Building unified packages (containing both bash and PowerShell scripts)"

for agent in "${AGENT_LIST[@]}"; do
  build_unified "$agent"
done

echo "Archives in $GENRELEASES_DIR:"
ls -1 "$GENRELEASES_DIR"/spec-kit-template-*-"${NEW_VERSION}".zip

