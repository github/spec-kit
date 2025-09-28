#!/usr/bin/env bash
set -euo pipefail

# smoke-copilot.sh
# Quick smoke test for Specify CLI provisioning using Copilot templates.
# Creates a temp directory, runs `specify init`, and validates expected files.
# Intended for local dev & CI. Produces simple log output; exits non-zero on failure.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")"/../../.. && pwd)"
CLI_CMD="specify"

# Allow override for local source invocation (e.g., python -m src.specify_cli)
if [[ ${SPECIFY_CLI_CMD:-} ]]; then
  CLI_CMD="${SPECIFY_CLI_CMD}"
fi

tmpdir="$(mktemp -d -t specify-copilot-smoke-XXXX)"
project_name="demo-copilot"
cd "$tmpdir"

echo "[smoke] Using temp dir: $tmpdir"

set +e
$CLI_CMD init "$project_name" --ai copilot --ignore-agent-tools --no-git >cli.log 2>&1
status=$?
set -e

if [[ $status -ne 0 ]]; then
  echo "[smoke][ERROR] CLI init failed (exit $status)"
  sed -n '1,200p' cli.log
  exit 1
fi

echo "[smoke] CLI init succeeded"

proj_dir="$tmpdir/$project_name"
[[ -d "$proj_dir/.github/prompts" ]] || { echo "[smoke][ERROR] Missing .github/prompts directory"; exit 1; }

required_prompts=(analyze clarify constitution fprds implement plan pprd-clarify pprd specify tasks)
missing=0
for p in "${required_prompts[@]}"; do
  f="$proj_dir/.github/prompts/${p}.prompt.md"
  if [[ ! -f $f ]]; then
    echo "[smoke][ERROR] Missing prompt: $f"; missing=1
  fi
done
[[ $missing -eq 0 ]] || { echo "[smoke][ERROR] Prompt validation failed"; exit 1; }

echo "[smoke] All expected Copilot prompt files present"

internal_tpl_dir="$proj_dir/.specs/.specify/templates"
for f in plan-template.md pprd-template.md spec-template.md tasks-template.md layout.yaml; do
  if [[ ! -f "$internal_tpl_dir/$f" ]]; then
    echo "[smoke][ERROR] Missing internal template: $f"; exit 1
  fi
done

echo "[smoke] Internal templates validated"

grep -q '\$ARGUMENTS' "$proj_dir/.github/prompts/plan.prompt.md" || { echo "[smoke][ERROR] plan.prompt.md missing $ARGUMENTS placeholder"; exit 1; }

echo "[smoke] Placeholder check passed"

echo "[smoke] SUCCESS"
# Auto cleanup unless SPECIFY_SMOKE_KEEP=1
if [[ ${SPECIFY_SMOKE_KEEP:-0} -ne 1 ]]; then
  rm -rf "$tmpdir"
fi
