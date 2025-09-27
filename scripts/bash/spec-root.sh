#!/usr/bin/env bash

set -e

# Prints the absolute path of the chosen specs root.
# Strategy: use read-layout.sh to get LAYOUT_SPEC_ROOTS (csv). Return first existing.
# If none exists, create the first listed and return it.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

REPO_ROOT="$(get_repo_root)"

if [[ -x "$SCRIPT_DIR/read-layout.sh" ]]; then
  eval "$($SCRIPT_DIR/read-layout.sh)"
fi

IFS=',' read -r -a ROOTS <<< "${LAYOUT_SPEC_ROOTS:-specs,.specs/.specify/specs}"

chosen=""
for r in "${ROOTS[@]}"; do
  cand="$REPO_ROOT/$r"
  if [[ -d "$cand" ]]; then chosen="$cand"; break; fi
done

if [[ -z "$chosen" ]]; then
  chosen="$REPO_ROOT/${ROOTS[0]}"
  mkdir -p "$chosen"
fi

printf '%s\n' "$chosen"

