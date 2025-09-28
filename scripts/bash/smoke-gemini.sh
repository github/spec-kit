#!/usr/bin/env bash
set -euo pipefail
# smoke-gemini.sh - provisioning smoke test for Gemini agent (TOML commands)

CLI_CMD="specify"
if [[ ${SPECIFY_CLI_CMD:-} ]]; then CLI_CMD="${SPECIFY_CLI_CMD}"; fi

tmpdir="$(mktemp -d -t specify-gemini-smoke-XXXX)"
project="demo-gemini"
cd "$tmpdir"

echo "[smoke-gemini] temp: $tmpdir"
set +e
$CLI_CMD init "$project" --ai gemini --ignore-agent-tools --no-git > cli.log 2>&1
rc=$?
set -e
if [[ $rc -ne 0 ]]; then
  echo "[smoke-gemini][ERROR] init failed"; sed -n '1,120p' cli.log; exit 1; fi

proj_dir="$tmpdir/$project"
cmd_dir="$proj_dir/.gemini/commands"
[[ -d $cmd_dir ]] || { echo "[smoke-gemini][ERROR] missing $cmd_dir"; exit 1; }

need=(plan clarify tasks specify implement analyze fprds pprd-clarify pprd constitution)
for f in "${need[@]}"; do
  file="$cmd_dir/$f.toml"
  [[ -f $file ]] || { echo "[smoke-gemini][ERROR] missing command $f.toml"; exit 1; }
  grep -q '{{args}}' "$file" || { echo "[smoke-gemini][ERROR] missing {{args}} in $f.toml"; exit 1; }
done

tpl_root="$proj_dir/.specs/.specify/templates"
for t in plan-template.md pprd-template.md spec-template.md tasks-template.md layout.yaml; do
  [[ -f "$tpl_root/$t" ]] || { echo "[smoke-gemini][ERROR] missing template $t"; exit 1; }
done

echo "[smoke-gemini] SUCCESS"
if [[ ${SPECIFY_SMOKE_KEEP:-0} -ne 1 ]]; then rm -rf "$tmpdir"; fi
