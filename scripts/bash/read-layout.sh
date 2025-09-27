#!/usr/bin/env bash

set -e

# Emit environment assignments for layout configuration.
# Usage: read-layout.sh [--json]
# Looks for .specs/.specify/layout.yaml at repo root; falls back to defaults.

JSON_MODE=false
for arg in "$@"; do
  case "$arg" in
    --json) JSON_MODE=true ;;
    --help|-h) echo "Usage: $0 [--json]"; exit 0 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/common.sh"

REPO_ROOT="$(get_repo_root)"
CFG_PATH="$REPO_ROOT/.specs/.specify/layout.yaml"

# Defaults
LAYOUT_VERSION="1"
LAYOUT_SPEC_ROOTS=("specs" ".specs/.specify/specs")
LAYOUT_FOLDER_STRATEGY="epic"
LAYOUT_FILES_FPRD="fprd.md"
LAYOUT_FILES_PPRD="pprd.md"
LAYOUT_FILES_REQUIREMENTS="requirements.md"
LAYOUT_FILES_DESIGN="design.md"
LAYOUT_FILES_TASKS="tasks.md"
LAYOUT_FILES_RESEARCH="research.md"
LAYOUT_FILES_QUICKSTART="quickstart.md"
LAYOUT_FILES_TRACEABILITY_INDEX="traceability_index.md"
LAYOUT_FILES_CONTRACTS_DIR="contracts"
LAYOUT_FILES_PROGRESS_LOG="progress_log.md"
LAYOUT_FILES_PARKING_LOT="parking_lot.md"
LAYOUT_FILES_INDEX="index.yaml"
LAYOUT_COMPAT_WRITE_STUB_SPEC="true"
LAYOUT_COMPAT_STUB_NAME="spec.md"
LAYOUT_CATALOG_PATH="specs/catalog.yaml"

if [[ -f "$CFG_PATH" ]]; then
  state="root"
  section=""
  while IFS= read -r raw || [[ -n "$raw" ]]; do
    line="${raw%%#*}"
    line="${line%$'\r'}"
    [[ -z "${line//[[:space:]]/}" ]] && continue
    # Top-level list: spec_roots
    if [[ $line =~ ^spec_roots: ]]; then
      section="spec_roots"; continue
    fi
    if [[ $line =~ ^files: ]]; then section="files"; continue; fi
    if [[ $line =~ ^compat: ]]; then section="compat"; continue; fi
    if [[ $line =~ ^catalog: ]]; then section="catalog"; continue; fi
    if [[ $line =~ ^id_policy:|^defaults: ]]; then section="skip"; continue; fi

    if [[ $line =~ ^version:[[:space:]]*([0-9]+) ]]; then LAYOUT_VERSION="${BASH_REMATCH[1]}"; continue; fi
    if [[ $line =~ ^folder_strategy:[[:space:]]*"?([a-zA-Z0-9_-]+)"? ]]; then LAYOUT_FOLDER_STRATEGY="${BASH_REMATCH[1]}"; continue; fi

    case "$section" in
      spec_roots)
        if [[ $line =~ ^[[:space:]]*-[[:space:]]*"?([^"']+)"? ]]; then
          LAYOUT_SPEC_ROOTS+=("${BASH_REMATCH[1]}")
        fi
        ;;
      files)
        if [[ $line =~ fprd:[[:space:]]*"?([^"']+)"? ]]; then LAYOUT_FILES_FPRD="${BASH_REMATCH[1]}"; fi
        if [[ $line =~ pprd:[[:space:]]*"?([^"']+)"? ]]; then LAYOUT_FILES_PPRD="${BASH_REMATCH[1]}"; fi
        if [[ $line =~ requirements:[[:space:]]*"?([^"']+)"? ]]; then LAYOUT_FILES_REQUIREMENTS="${BASH_REMATCH[1]}"; fi
        if [[ $line =~ design:[[:space:]]*"?([^"']+)"? ]]; then LAYOUT_FILES_DESIGN="${BASH_REMATCH[1]}"; fi
        if [[ $line =~ tasks:[[:space:]]*"?([^"']+)"? ]]; then LAYOUT_FILES_TASKS="${BASH_REMATCH[1]}"; fi
        if [[ $line =~ research:[[:space:]]*"?([^"']+)"? ]]; then LAYOUT_FILES_RESEARCH="${BASH_REMATCH[1]}"; fi
        if [[ $line =~ quickstart:[[:space:]]*"?([^"']+)"? ]]; then LAYOUT_FILES_QUICKSTART="${BASH_REMATCH[1]}"; fi
        if [[ $line =~ traceability_index:[[:space:]]*"?([^"']+)"? ]]; then LAYOUT_FILES_TRACEABILITY_INDEX="${BASH_REMATCH[1]}"; fi
        if [[ $line =~ contracts_dir:[[:space:]]*"?([^"']+)"? ]]; then LAYOUT_FILES_CONTRACTS_DIR="${BASH_REMATCH[1]}"; fi
        if [[ $line =~ progress_log:[[:space:]]*"?([^"']+)"? ]]; then LAYOUT_FILES_PROGRESS_LOG="${BASH_REMATCH[1]}"; fi
        if [[ $line =~ parking_lot:[[:space:]]*"?([^"']+)"? ]]; then LAYOUT_FILES_PARKING_LOT="${BASH_REMATCH[1]}"; fi
        if [[ $line =~ index:[[:space:]]*"?([^"']+)"? ]]; then LAYOUT_FILES_INDEX="${BASH_REMATCH[1]}"; fi
        ;;
      compat)
        if [[ $line =~ write_redirect_stub_spec_md:[[:space:]]*(true|false) ]]; then LAYOUT_COMPAT_WRITE_STUB_SPEC="${BASH_REMATCH[1]}"; fi
        if [[ $line =~ stub_name:[[:space:]]*"?([^"']+)"? ]]; then LAYOUT_COMPAT_STUB_NAME="${BASH_REMATCH[1]}"; fi
        ;;
      catalog)
        if [[ $line =~ path:[[:space:]]*"?([^"']+)"? ]]; then LAYOUT_CATALOG_PATH="${BASH_REMATCH[1]}"; fi
        ;;
    esac
  done < "$CFG_PATH"
fi

emit() {
  echo "LAYOUT_VERSION='$LAYOUT_VERSION'"
  echo -n "LAYOUT_SPEC_ROOTS='"; (IFS=,; echo -n "${LAYOUT_SPEC_ROOTS[*]}"); echo "'"
  echo "LAYOUT_FOLDER_STRATEGY='$LAYOUT_FOLDER_STRATEGY'"
  echo "LAYOUT_FILES_FPRD='$LAYOUT_FILES_FPRD'"
  echo "LAYOUT_FILES_PPRD='$LAYOUT_FILES_PPRD'"
  echo "LAYOUT_FILES_REQUIREMENTS='$LAYOUT_FILES_REQUIREMENTS'"
  echo "LAYOUT_FILES_DESIGN='$LAYOUT_FILES_DESIGN'"
  echo "LAYOUT_FILES_TASKS='$LAYOUT_FILES_TASKS'"
  echo "LAYOUT_FILES_RESEARCH='$LAYOUT_FILES_RESEARCH'"
  echo "LAYOUT_FILES_QUICKSTART='$LAYOUT_FILES_QUICKSTART'"
  echo "LAYOUT_FILES_TRACEABILITY_INDEX='$LAYOUT_FILES_TRACEABILITY_INDEX'"
  echo "LAYOUT_FILES_CONTRACTS_DIR='$LAYOUT_FILES_CONTRACTS_DIR'"
  echo "LAYOUT_FILES_PROGRESS_LOG='$LAYOUT_FILES_PROGRESS_LOG'"
  echo "LAYOUT_FILES_PARKING_LOT='$LAYOUT_FILES_PARKING_LOT'"
  echo "LAYOUT_FILES_INDEX='$LAYOUT_FILES_INDEX'"
  echo "LAYOUT_COMPAT_WRITE_STUB_SPEC='$LAYOUT_COMPAT_WRITE_STUB_SPEC'"
  echo "LAYOUT_COMPAT_STUB_NAME='$LAYOUT_COMPAT_STUB_NAME'"
  echo "LAYOUT_CATALOG_PATH='$LAYOUT_CATALOG_PATH'"
}

if $JSON_MODE; then
  # Not used currently; keeping plain env format for simplicity
  :
fi

emit

