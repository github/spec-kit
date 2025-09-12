#!/usr/bin/env bash
set -euo pipefail

# create-release-packages.sh (workflow-local)
# Build Spec Kit template release archives for each supported AI assistant and script type.
# Usage: .github/workflows/scripts/create-release-packages.sh <version>
#   Version argument should include leading 'v'.
#   Optionally set AGENTS and/or SCRIPTS env vars to limit what gets built.
#     AGENTS  : space or comma separated subset of: claude gemini copilot (default: all)
#     SCRIPTS : space or comma separated subset of: sh ps (default: both)
#   Examples:
#     AGENTS=claude SCRIPTS=sh $0 v0.2.0
#     AGENTS="copilot,gemini" $0 v0.2.0
#     SCRIPTS=ps $0 v0.2.0

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

rm -rf sdd-package-base* sdd-*-package-* spec-kit-template-*-${NEW_VERSION}.zip || true

mkdir -p sdd-package-base
SPEC_DIR="sdd-package-base/.specify"
mkdir -p "$SPEC_DIR"

[[ -d memory ]] && { cp -r memory "$SPEC_DIR/"; echo "Copied memory -> .specify"; }
[[ -d scripts ]] && { cp -r scripts "$SPEC_DIR/"; echo "Copied scripts -> .specify/scripts"; }
[[ -d templates ]] && { mkdir -p "$SPEC_DIR/templates"; find templates -type f -not -path "templates/commands/*" -exec cp --parents {} "$SPEC_DIR"/ \; ; echo "Copied templates -> .specify/templates"; }

rewrite_paths() {
  sed -E \
    -e 's@(/?)memory/@.specify/memory/@g' \
    -e 's@(/?)scripts/@.specify/scripts/@g' \
    -e 's@(/?)templates/@.specify/templates/@g'
}

generate_commands() {
  local agent=$1 ext=$2 arg_format=$3 output_dir=$4 script_variant=$5
  mkdir -p "$output_dir"
  for template in templates/commands/*.md; do
    [[ -f "$template" ]] || continue
    local name description file_content variant_line injected body
    name=$(basename "$template" .md)
    # Normalize line endings and work with entire file content
    file_content=$(tr -d '\r' < "$template")
    # Extract description from frontmatter
    description=$(printf '%s\n' "$file_content" | awk '/^description:/ {sub(/^description:[[:space:]]*/, ""); print; exit}')
    # Find variant line content
    variant_line=$(printf '%s\n' "$file_content" | grep -E "<!--[[:space:]]*VARIANT:${script_variant}[[:space:]]" | head -1 | sed -E "s/.*VARIANT:${script_variant}[[:space:]]+//; s/-->.*//")
    if [[ -z $variant_line ]]; then
      echo "Warning: no variant line found for $script_variant in $template" >&2
      variant_line="(Missing variant command for $script_variant)"
    fi
    # Replace VARIANT-INJECT and remove variant comments  
    body=$(printf '%s\n' "$file_content" | sed "s|VARIANT-INJECT|${variant_line}|" | sed '/<!--[[:space:]]*VARIANT:sh/d' | sed '/<!--[[:space:]]*VARIANT:ps/d')
    # Apply substitutions
    body=$(printf '%s\n' "$body" | sed "s/{ARGS}/$arg_format/g" | sed "s/__AGENT__/$agent/g" | rewrite_paths)
    case $ext in
      toml)
        { echo "description = \"$description\""; echo; echo "prompt = \"\"\""; echo "$body"; echo "\"\"\""; } > "$output_dir/$name.$ext" ;;
      md)
        echo "$body" > "$output_dir/$name.$ext" ;;
      prompt.md)
        echo "$body" > "$output_dir/$name.$ext" ;;
    esac
  done
}

build_variant() {
  local agent=$1 script=$2
  local base_dir="sdd-${agent}-package-${script}"
  echo "Building $agent ($script) package..."
  mkdir -p "$base_dir"
  cp -r sdd-package-base/. "$base_dir"/
  # Inject variant into plan-template.md within .specify/templates if present
  local plan_tpl="$base_dir/.specify/templates/plan-template.md"
  if [[ -f "$plan_tpl" ]]; then
    plan_norm=$(tr -d '\r' < "$plan_tpl")
    variant_line=$(printf '%s\n' "$plan_norm" | grep -E "<!--[[:space:]]*VARIANT:$script" | head -1 | sed -E "s/.*VARIANT:$script[[:space:]]+//; s/-->.*//; s/^[[:space:]]+//; s/[[:space:]]+$//")
    if [[ -n $variant_line ]]; then
      tmp_file=$(mktemp)
      sed "s|VARIANT-INJECT|${variant_line}|" "$plan_tpl" | tr -d '\r' | sed "s|__AGENT__|${agent}|g" | sed '/<!--[[:space:]]*VARIANT:sh/d' | sed '/<!--[[:space:]]*VARIANT:ps/d' > "$tmp_file" && mv "$tmp_file" "$plan_tpl"
    else
      echo "Warning: no plan-template variant for $script (pattern not matched)" >&2
    fi
  fi
  case $agent in
    claude)
      mkdir -p "$base_dir/.claude/commands"
      generate_commands claude md "\$ARGUMENTS" "$base_dir/.claude/commands" "$script" ;;
    gemini)
      mkdir -p "$base_dir/.gemini/commands"
      generate_commands gemini toml "{{args}}" "$base_dir/.gemini/commands" "$script"
      [[ -f agent_templates/gemini/GEMINI.md ]] && cp agent_templates/gemini/GEMINI.md "$base_dir/GEMINI.md" ;;
    copilot)
      mkdir -p "$base_dir/.github/prompts"
      generate_commands copilot prompt.md "\$ARGUMENTS" "$base_dir/.github/prompts" "$script" ;;
  esac
  ( cd "$base_dir" && zip -r "../spec-kit-template-${agent}-${script}-${NEW_VERSION}.zip" . )
  echo "Created spec-kit-template-${agent}-${script}-${NEW_VERSION}.zip"
}

# Determine agent list
ALL_AGENTS=(claude gemini copilot)
ALL_SCRIPTS=(sh ps)

norm_list() {
  # convert comma+space separated -> space separated unique while preserving order of first occurrence
  tr ',\n' '  ' | awk '{for(i=1;i<=NF;i++){if(!seen[$i]++){printf((out?" ":"") $i)}}}END{printf("\n")}'
}

validate_subset() {
  local type=$1; shift; local -n allowed=$1; shift; local items=($@)
  local ok=1
  for it in "${items[@]}"; do
    local found=0
    for a in "${allowed[@]}"; do [[ $it == $a ]] && { found=1; break; }; done
    if [[ $found -eq 0 ]]; then
      echo "Error: unknown $type '$it' (allowed: ${allowed[*]})" >&2
      ok=0
    fi
  done
  return $ok
}

if [[ -n ${AGENTS:-} ]]; then
  AGENT_LIST=($(printf '%s' "$AGENTS" | norm_list))
  validate_subset agent ALL_AGENTS "${AGENT_LIST[@]}" || exit 1
else
  AGENT_LIST=(${ALL_AGENTS[@]})
fi

if [[ -n ${SCRIPTS:-} ]]; then
  SCRIPT_LIST=($(printf '%s' "$SCRIPTS" | norm_list))
  validate_subset script ALL_SCRIPTS "${SCRIPT_LIST[@]}" || exit 1
else
  SCRIPT_LIST=(${ALL_SCRIPTS[@]})
fi

echo "Agents: ${AGENT_LIST[*]}"
echo "Scripts: ${SCRIPT_LIST[*]}"

for agent in "${AGENT_LIST[@]}"; do
  for script in "${SCRIPT_LIST[@]}"; do
    build_variant "$agent" "$script"
  done
done

echo "Archives:"
ls -1 spec-kit-template-*-${NEW_VERSION}.zip
