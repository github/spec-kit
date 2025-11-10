#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

run_help_check() {
    local script_path="$1"
    echo "Running --help for ${script_path#"$REPO_ROOT/"}"
    if ! bash "$script_path" --help > /dev/null; then
        echo "ERROR: $script_path --help failed" >&2
        return 1
    fi
}

run_shellcheck() {
    local script_path="$1"
    echo "Checking syntax for ${script_path#"$REPO_ROOT/"}"
    if ! bash -n "$script_path"; then
        echo "ERROR: Syntax check failed for $script_path" >&2
        return 1
    fi
}

main() {
    local failure=0

    mapfile -t bash_scripts < <(find "$REPO_ROOT/scripts/bash" -maxdepth 1 -type f -name '*.sh' ! -name 'common.sh' | sort)
    mapfile -t workflow_scripts < <(find "$REPO_ROOT/.github/workflows/scripts" -type f -name '*.sh' | sort)

    if [[ ${#bash_scripts[@]} -eq 0 && ${#workflow_scripts[@]} -eq 0 ]]; then
        echo "No bash scripts found"
        exit 0
    fi

    echo "--- Bash script syntax checks ---"
    for script in "${bash_scripts[@]}" "${workflow_scripts[@]}"; do
        [[ -z "$script" ]] && continue
        if ! run_shellcheck "$script"; then
            failure=1
        fi
    done

    declare -a help_scripts=()
    for script in "${bash_scripts[@]}"; do
        [[ -z "$script" ]] && continue
        if [[ $(basename "$script") == "update-agent-context.sh" ]]; then
            continue
        fi
        help_scripts+=("$script")
    done

    echo "--- Bash CLI help checks ---"
    for script in "${help_scripts[@]}"; do
        [[ -z "$script" ]] && continue
        if ! run_help_check "$script"; then
            failure=1
        fi
    done

    if [[ $failure -ne 0 ]]; then
        echo "One or more bash script tests failed" >&2
        exit $failure
    fi

    echo "All bash script tests passed"
}

main "$@"
