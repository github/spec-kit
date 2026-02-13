#!/usr/bin/env bash

set -e

JSON_MODE=false
NO_METADATA=false
ARGS=()

i=1
while [ $i -le $# ]; do
  arg="${!i}"
  case "$arg" in
    --json)
      JSON_MODE=true
      ;;
    --no-metadata)
      NO_METADATA=true
      ;;
    --help|-h)
      echo "Usage: $0 [--json] [--no-metadata] <TICKET-ID>";
      exit 0
      ;;
    *)
      ARGS+=("$arg")
      ;;
  esac
  i=$((i + 1))
done

TICKET_ID="${ARGS[0]}"
if [ -z "$TICKET_ID" ]; then
  echo "Error: Missing required TICKET-ID argument." >&2
  exit 1
fi

find_repo_root() {
  local dir="$1"
  while [ "$dir" != "/" ]; do
    if [ -d "$dir/.git" ] || [ -d "$dir/.specify" ]; then
      echo "$dir"
      return 0
    fi
    dir="$(dirname "$dir")"
  done
  return 1
}

SCRIPT_DIR="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if git rev-parse --show-toplevel >/dev/null 2>&1; then
  REPO_ROOT="$(git rev-parse --show-toplevel)"
else
  REPO_ROOT="$(find_repo_root "$SCRIPT_DIR")"
  if [ -z "$REPO_ROOT" ]; then
    echo "Error: Could not determine repository root." >&2
    exit 1
  fi
fi

cd "$REPO_ROOT"

TASKS_DIR="$REPO_ROOT/tasks"
TICKET_DIR="$TASKS_DIR/$TICKET_ID"
REFERENCES_DIR="$TICKET_DIR/references"
PLANNING_DIR="$TICKET_DIR/planning"
REVIEWS_DIR="$TICKET_DIR/reviews"
STEPS_DIR="$PLANNING_DIR/steps"

mkdir -p "$REFERENCES_DIR" "$PLANNING_DIR" "$REVIEWS_DIR" "$STEPS_DIR"

TICKET_FILE="$TICKET_DIR/ticket.md"
INITIAL_PLAN="$PLANNING_DIR/initial-plan.md"
WHAT_DONE="$PLANNING_DIR/what-has-been-done.md"
METADATA_FILE="$TICKET_DIR/metadata.yaml"

TEMPLATE_DIR="$REPO_ROOT/templates/ticket-mode"

copy_template_if_missing() {
  local template="$1"
  local dest="$2"

  if [ -f "$dest" ]; then
    return 0
  fi

  if [ -f "$template" ]; then
    # simple token replace
    sed "s/<TICKET-ID>/$TICKET_ID/g" "$template" > "$dest"
  else
    : > "$dest"
  fi
}

copy_template_if_missing "$TEMPLATE_DIR/ticket.template.md" "$TICKET_FILE"
copy_template_if_missing "$TEMPLATE_DIR/planning-initial-plan.template.md" "$INITIAL_PLAN"
copy_template_if_missing "$TEMPLATE_DIR/planning-what-has-been-done.template.md" "$WHAT_DONE"

if [ "$NO_METADATA" != true ]; then
  copy_template_if_missing "$TEMPLATE_DIR/metadata.template.yaml" "$METADATA_FILE"
fi

if [ "$JSON_MODE" = true ]; then
  # METADATA_FILE may not exist if --no-metadata
  metadata_path=""
  if [ -f "$METADATA_FILE" ]; then
    metadata_path="$METADATA_FILE"
  fi

  printf '{"TICKET_ID":"%s","REPO_ROOT":"%s","TASKS_DIR":"%s","TICKET_DIR":"%s","TICKET_FILE":"%s","METADATA_FILE":"%s","REFERENCES_DIR":"%s","PLANNING_DIR":"%s","STEPS_DIR":"%s","INITIAL_PLAN":"%s","WHAT_DONE":"%s","REVIEWS_DIR":"%s"}\n' \
    "$TICKET_ID" "$REPO_ROOT" "$TASKS_DIR" "$TICKET_DIR" "$TICKET_FILE" "$metadata_path" \
    "$REFERENCES_DIR" "$PLANNING_DIR" "$STEPS_DIR" "$INITIAL_PLAN" "$WHAT_DONE" "$REVIEWS_DIR"
else
  echo "TICKET_ID: $TICKET_ID"
  echo "TICKET_DIR: $TICKET_DIR"
  echo "TICKET_FILE: $TICKET_FILE"
fi
