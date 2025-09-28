#!/usr/bin/env bash
set -euo pipefail
# validate-archives.sh - validate built template archives contain expected files
VERSION="$1"  # expects leading v (e.g. v0.0.23)
ls -1 .genreleases
failures=0
AGENTS=$(cat <<'CSV'
claude,.claude/commands,plan.md
gemini,.gemini/commands,plan.toml
copilot,.github/prompts,plan.prompt.md
cursor,.cursor/commands,plan.md
qwen,.qwen/commands,plan.toml
opencode,.opencode/command,plan.md
windsurf,.windsurf/workflows,plan.md
codex,.codex/prompts,plan.md
kilocode,.kilocode/workflows,plan.md
auggie,.augment/commands,plan.md
roo,.roo/commands,plan.md
CSV
)

while IFS=',' read -r agent folder example; do
  [[ -n "$agent" ]] || continue
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
done <<<"$AGENTS"

if [[ $failures -ne 0 ]]; then
  echo "[ERROR] Archive validation failed"; exit 1
fi

echo "[validate] All archives contain expected files"