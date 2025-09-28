#!/usr/bin/env bash
set -euo pipefail
# validate-archives.sh - validate built template archives contain expected files
VERSION="$1"  # expects leading v (e.g. v0.0.23)
ls -1 .genreleases
failures=0
# agent,folder,example triplets as an array to avoid heredoc/read portability issues
AGENTS=(
  claude .claude/commands plan.md
  gemini .gemini/commands plan.toml
  copilot .github/prompts plan.prompt.md
  cursor .cursor/commands plan.md
  qwen .qwen/commands plan.toml
  opencode .opencode/command plan.md
  windsurf .windsurf/workflows plan.md
  codex .codex/prompts plan.md
  kilocode .kilocode/workflows plan.md
  auggie .augment/commands plan.md
  roo .roo/commands plan.md
)

for ((i=0; i<${#AGENTS[@]}; i+=3)); do
  agent="${AGENTS[i]}"; folder="${AGENTS[i+1]}"; example="${AGENTS[i+2]}"
  for script in sh ps; do
    zip_file=".genreleases/spec-kit-template-${agent}-${script}-${VERSION}.zip"
    if [[ ! -f $zip_file ]]; then
      echo "[warn] Missing archive $zip_file"; failures=1; continue
    fi
    echo "[validate] Checking $zip_file"
    unzip -p "$zip_file" "$folder/$example" >/dev/null 2>&1 || { echo "[error] Expected file $folder/$example not in $zip_file"; failures=1; }
    unzip -p "$zip_file" .specs/.specify/templates/plan-template.md >/dev/null 2>&1 || { echo "[error] Missing plan-template.md in $zip_file"; failures=1; }
    unzip -p "$zip_file" .specs/.specify/templates/layout.yaml >/dev/null 2>&1 || { echo "[error] Missing layout.yaml in $zip_file"; failures=1; }
  done
done

if [[ $failures -ne 0 ]]; then
  echo "[ERROR] Archive validation failed"; exit 1
fi

echo "[validate] All archives contain expected files"