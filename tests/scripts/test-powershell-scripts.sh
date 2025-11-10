#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

main() {
    if ! command -v pwsh >/dev/null 2>&1; then
        echo "pwsh not found - skipping PowerShell script tests"
        exit 0
    fi

    mapfile -t ps_scripts < <(find "$REPO_ROOT/scripts/powershell" -maxdepth 1 -type f -name '*.ps1' ! -name 'common.ps1' | sort)

    if [[ ${#ps_scripts[@]} -eq 0 ]]; then
        echo "No PowerShell scripts found"
        exit 0
    fi

    local failure=0

    echo "--- PowerShell CLI help checks ---"
    for script in "${ps_scripts[@]}"; do
        [[ -z "$script" ]] && continue
        echo "Running -Help for ${script#"$REPO_ROOT/"}"
        if ! pwsh -NoLogo -NoProfile -File "$script" -Help > /dev/null; then
            echo "ERROR: $script -Help failed" >&2
            failure=1
        fi
    done

    if [[ $failure -ne 0 ]]; then
        echo "One or more PowerShell script tests failed" >&2
        exit $failure
    fi

    echo "All PowerShell script tests passed"
}

main "$@"
