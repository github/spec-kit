#!/usr/bin/env bash
set -euo pipefail

# create-release-packages.sh (workflow-local)
# Build Spec Kit template release archives for each supported AI assistant and script type.
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
    local name description raw_body variant_line injected body
    name=$(basename "$template" .md)
    description=$(awk '/^description:/ {gsub(/^description: *"?/, ""); gsub(/"$/, ""); print; exit}' "$template" | tr -d '\r')
    raw_body=$(awk '/^---$/{if(++count==2) start=1; next} start' "$template")
    # Find single-line variant comment matching the variant: <!-- VARIANT:sh ... --> or <!-- VARIANT:ps ... -->
    variant_line=$(printf '%s\n' "$raw_body" | awk -v sv="$script_variant" '/<!--[[:space:]]+VARIANT:'sv'/ {match($0, /VARIANT:'"sv"'[[:space:]]+(.*)-->/, m); if (m[1]!="") {print m[1]; exit}}')
    if [[ -z $variant_line ]]; then
      echo "Warning: no variant line found for $script_variant in $template" >&2
      variant_line="(Missing variant command for $script_variant)"
    fi
    # Replace the token VARIANT-INJECT with the selected variant line
    injected=$(printf '%s\n' "$raw_body" | sed "s/VARIANT-INJECT/${variant_line//\//\/}/")
    # Remove all single-line variant comments
    injected=$(printf '%s\n' "$injected" | sed '/<!--[[:space:]]*VARIANT:sh/d' | sed '/<!--[[:space:]]*VARIANT:ps/d')
    # Apply arg substitution and path rewrite
    body=$(printf '%s\n' "$injected" | sed "s/{ARGS}/$arg_format/g" | sed "s/__AGENT__/$agent/g" | rewrite_paths)
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
    variant_line=$(awk -v sv="$script" '/<!--[[:space:]]*VARIANT:'"$script"'/ {match($0, /VARIANT:'"$script"'[[:space:]]+(.*)-->/, m); if(m[1]!=""){print m[1]; exit}}' "$plan_tpl")
    if [[ -n $variant_line ]]; then
      tmp_file=$(mktemp)
  sed "s/VARIANT-INJECT/${variant_line//\//\/}/" "$plan_tpl" | sed "/__AGENT__/s//${agent}/g" | sed '/<!--[[:space:]]*VARIANT:sh/d' | sed '/<!--[[:space:]]*VARIANT:ps/d' > "$tmp_file" && mv "$tmp_file" "$plan_tpl"
    else
      echo "Warning: no plan-template variant for $script" >&2
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

# Build for each agent+script variant
for agent in claude gemini copilot; do
  for script in sh ps; do
    build_variant "$agent" "$script"
  done
done

echo "Archives:"
ls -1 spec-kit-template-*-${NEW_VERSION}.zip
