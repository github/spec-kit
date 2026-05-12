#!/usr/bin/env bash

set -euo pipefail

JSON=false
for arg in "$@"; do
    case "$arg" in
        --json) JSON=true ;;
        -h|--help)
            echo "Usage: $0 [--json]"
            exit 0
            ;;
    esac
done

if ! command -v git >/dev/null 2>&1 || ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "ERROR: Git repository not detected. Ticket branch workflow requires an existing git branch." >&2
    exit 1
fi

branch_name=$(git rev-parse --abbrev-ref HEAD)
if [[ "$branch_name" == "HEAD" ]]; then
    echo "ERROR: Detached HEAD is not valid for ticket branch workflow." >&2
    exit 1
fi

ticket_key=""
branch_prefix=""

if [[ "$branch_name" =~ ^([A-Za-z0-9._-]+)/([A-Z]+-[0-9]+)$ ]]; then
    branch_prefix="${BASH_REMATCH[1]}"
    ticket_key="${BASH_REMATCH[2]}"
elif [[ "$branch_name" =~ ^([A-Z]+-[0-9]+)$ ]]; then
    ticket_key="${BASH_REMATCH[1]}"
else
    echo "ERROR: Current branch '$branch_name' is not a valid ticket branch." >&2
    echo "Expected: GDEV-1234, MSPS-1234, feature/GDEV-1234, fix/GDEV-1234, hotfix/GDEV-1234, or chore/GDEV-1234" >&2
    exit 1
fi

if [[ -n "$branch_prefix" && ! "$branch_prefix" =~ ^(feature|fix|hotfix|chore)$ ]]; then
    echo "ERROR: Branch prefix '$branch_prefix' is not allowed for ticket branch workflow." >&2
    echo "Allowed prefixes: feature, fix, hotfix, chore" >&2
    exit 1
fi

if [[ "$JSON" == true ]]; then
    printf '{"BRANCH_NAME":"%s","TICKET_KEY":"%s","BRANCH_PREFIX":"%s","BRANCH_STRATEGY":"existing-ticket"}\n' \
        "$branch_name" "$ticket_key" "$branch_prefix"
else
    echo "BRANCH_NAME: $branch_name"
    echo "TICKET_KEY: $ticket_key"
    if [[ -n "$branch_prefix" ]]; then
        echo "BRANCH_PREFIX: $branch_prefix"
    fi
fi
