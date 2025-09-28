#!/usr/bin/env bash
set -euo pipefail
# smoke-claude.sh - basic provisioning smoke test for Claude agent
# Validates that Claude command markdown files and internal templates exist.

CLI_CMD="specify"
if [[ ${SPECIFY_CLI_CMD:-} ]]; then CLI_CMD="${SPECIFY_CLI_CMD}"; fi

tmpdir="$(mktemp -d -t specify-claude-smoke-XXXX)"
project="demo-claude"
cd "$tmpdir"

echo "[smoke-claude] temp: $tmpdir"
set +e
$CLI_CMD init "$project" --ai claude --ignore-agent-tools --no-git > cli.log 2>&1
rc=$?
set -e
if [[ $rc -ne 0 ]]; then
  echo "[smoke-claude][ERROR] init failed"; sed -n '1,120p' cli.log; exit 1; fi

proj_dir="$tmpdir/$project"
cmd_dir="$proj_dir/.claude/commands"
[[ -d $cmd_dir ]] || { echo "[smoke-claude][ERROR] missing $cmd_dir"; exit 1; }

need=(plan clarify tasks specify implement analyze fprds pprd-clarify pprd constitution)
for f in "${need[@]}"; do
  [[ -f "$cmd_dir/$f.md" ]] || { echo "[smoke-claude][ERROR] missing command $f.md"; exit 1; }
  grep -q '$ARGUMENTS' "$cmd_dir/$f.md" || { echo "[smoke-claude][ERROR] missing $ARGUMENTS in $f.md"; exit 1; }
done

tpl_root="$proj_dir/.specs/.specify/templates"
for t in plan-template.md pprd-template.md spec-template.md tasks-template.md layout.yaml; do
  [[ -f "$tpl_root/$t" ]] || { echo "[smoke-claude][ERROR] missing template $t"; exit 1; }
done

echo "[smoke-claude] SUCCESS"
if [[ ${SPECIFY_SMOKE_KEEP:-0} -ne 1 ]]; then rm -rf "$tmpdir"; fi
