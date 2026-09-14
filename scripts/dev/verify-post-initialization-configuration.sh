#!/usr/bin/env bash

# Developer-only verifier: kept outside the core script discovery paths.
# Verify the post-initialization configuration workflow in a disposable project.
set -euo pipefail

SPECIFY_PATH="${SPECIFY:-}"
TEMP_DIR=""

fail() {
  printf 'Error: %s\n' "$1" >&2
  exit 1
}

cleanup() {
  if [[ -n "$TEMP_DIR" ]]; then
    rm -rf "$TEMP_DIR" || true
  fi
}

usage() {
  cat <<'EOF'
Usage: verify-post-initialization-configuration.sh [--specify PATH]

Verify post-initialization configuration using a disposable Copilot project.

Options:
  --specify PATH  Path to the specify executable. Defaults to $SPECIFY or specify on PATH.
  -h, --help      Show this help message.
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --specify)
      [[ $# -ge 2 ]] || fail "--specify requires a path."
      SPECIFY_PATH="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "Unknown option: $1"
      ;;
  esac
done

if [[ -n "$SPECIFY_PATH" ]]; then
  [[ -x "$SPECIFY_PATH" ]] || fail "Specify executable is not executable: $SPECIFY_PATH"
else
  SPECIFY_PATH="$(command -v specify)" || fail "Specify executable not found. Pass --specify PATH."
fi
# Resolve before changing directories, including relative entries from PATH.
SPECIFY_PATH="$(cd -- "$(dirname -- "$SPECIFY_PATH")" && pwd)/$(basename -- "$SPECIFY_PATH")"
SPECIFY=("$SPECIFY_PATH")

command -v python3 >/dev/null 2>&1 || fail "python3 is required to inspect init-options.json."

TEMP_DIR="$(mktemp -d)" || fail "Could not create a temporary directory."
trap cleanup EXIT INT TERM
PROJECT_DIR="$TEMP_DIR/project"
# Project commands honor this override even after cd; confine them to this sandbox.
export SPECIFY_INIT_DIR="$PROJECT_DIR"

run() {
  "${SPECIFY[@]}" "$@"
}

expect_value() {
  local expected="$1"
  shift
  local actual
  actual="$(run "$@")"
  [[ "$actual" == "$expected" ]] || fail "Expected '$expected' from 'specify $*', got '$actual'."
}

expect_failure() {
  if run "$@" >/dev/null 2>&1; then
    fail "Expected 'specify $*' to fail."
  fi
}

run init "$PROJECT_DIR" --integration copilot --ignore-agent-tools --script sh
cd "$PROJECT_DIR"

run config list >/dev/null
run config list --json >/dev/null
expect_value sh config get script

run integration upgrade copilot --script py
expect_value py config get script

run config set feature-numbering timestamp
expect_value timestamp config get feature-numbering

python3 - ".specify/init-options.json" <<'PY'
import json
import sys

with open(sys.argv[1], encoding="utf-8") as file:
    options = json.load(file)

expected = {"script": "py", "feature_numbering": "timestamp"}
for key, value in expected.items():
    if options.get(key) != value:
        raise SystemExit(f"Expected {key}={value!r} in init-options.json, got {options.get(key)!r}.")
PY

expect_failure config set integration claude
expect_failure config set script sh
expect_failure config set ai-skills true
expect_failure config set here true
expect_value py config get script
expect_value timestamp config get feature-numbering

run config extension add git >/dev/null
extension_list="$(run config extension list)"
[[ "$extension_list" == *"Git Branching Workflow"* ]] || fail "Git extension was not listed after installation."
run config extension disable git >/dev/null
extension_list="$(run config extension list)"
[[ "$extension_list" == *"Git Branching Workflow"* && "$extension_list" == *"Status: Disabled"* ]] || fail "Git extension was not listed as disabled."
run config extension enable git >/dev/null
extension_list="$(run config extension list)"
[[ "$extension_list" == *"Git Branching Workflow"* && "$extension_list" == *"Status: Enabled"* ]] || fail "Git extension was not listed as enabled."
run config extension remove git --force >/dev/null
extension_list="$(run config extension list)"
if [[ "$extension_list" == *"Git Branching Workflow"* ]]; then
  fail "Git extension was still listed after removal."
fi

printf 'Post-initialization configuration verified.\n'
