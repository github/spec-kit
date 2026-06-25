#!/usr/bin/env bash

set -euo pipefail

JSON_MODE=false

for arg in "$@"; do
    case "$arg" in
        --json)
            JSON_MODE=true
            ;;
        --help|-h)
            echo "Usage: $0 [--json]"
            echo "  --json    Output readiness result as JSON"
            echo "  --help    Show this help message"
            exit 0
            ;;
        *)
            ;;
    esac
done

find_specify_root() {
    local dir="${1:-$(pwd)}"
    dir="$(cd -- "$dir" 2>/dev/null && pwd)" || return 1
    local prev_dir=""
    while true; do
        if [ -d "$dir/.specify" ]; then
            echo "$dir"
            return 0
        fi
        if [ "$dir" = "/" ] || [ "$dir" = "$prev_dir" ]; then
            break
        fi
        prev_dir="$dir"
        dir="$(dirname "$dir")"
    done
    return 1
}

get_repo_root() {
    local specify_root
    if specify_root=$(find_specify_root); then
        echo "$specify_root"
        return
    fi

    if git rev-parse --show-toplevel >/dev/null 2>&1; then
        git rev-parse --show-toplevel
        return
    fi

    local script_dir
    script_dir="$(CDPATH="" cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    (cd "$script_dir/../../../../.." && pwd)
}

json_escape() {
    local s="$1"
    s="${s//\\/\\\\}"
    s="${s//\"/\\\"}"
    s="${s//$'\n'/\\n}"
    s="${s//$'\t'/\\t}"
    s="${s//$'\r'/\\r}"
    printf '%s' "$s"
}

blockers=()

add_blocker() {
    local code="$1"
    local artifact="$2"
    local section="$3"
    local message="$4"
    blockers+=("$(printf '{"code":"%s","artifact":"%s","sectionId":"%s","message":"%s"}' \
        "$(json_escape "$code")" \
        "$(json_escape "$artifact")" \
        "$(json_escape "$section")" \
        "$(json_escape "$message")")")
}

section_heading() {
    local section_id="$1"
    case "$section_id" in
        non-goals-anti-patterns) echo "Non-goals / Anti-patterns"; return ;;
        architecture-level-components) echo "Architecture-Level Components"; return ;;
        physical-deployment-clues) echo "Physical / Deployment Clues"; return ;;
        development-view-gaps) echo "Development View Gaps"; return ;;
        physical-view-gaps) echo "Physical View Gaps"; return ;;
    esac
    printf '%s\n' "$section_id" | sed 's/-/ /g' | awk '{
        for (i = 1; i <= NF; i++) {
            $i = toupper(substr($i, 1, 1)) substr($i, 2)
        }
        print
    }'
}

section_exists() {
    local file="$1"
    local section_id="$2"
    local heading
    heading="$(section_heading "$section_id")"
    grep -Eq "^##[[:space:]]+$heading[[:space:]]*$" "$file"
}

section_has_content() {
    local file="$1"
    local section_id="$2"
    local heading
    heading="$(section_heading "$section_id")"
    awk -v heading="$heading" '
        $0 ~ "^##[[:space:]]+" heading "[[:space:]]*$" { in_section = 1; next }
        in_section && /^##[[:space:]]+/ { exit }
        in_section {
            line = $0
            gsub(/^[[:space:]]+|[[:space:]]+$/, "", line)
            if (line == "") next
            if (line ~ /^[-|:[:space:]]+$/) next
            if (line ~ /NEEDS ARCH UPDATE|NEEDS REPO FACTS UPDATE/) next
            if (line ~ /^\|[[:space:]]*[-:]/) next
            if (line ~ /^\|.*\|$/ && line !~ /NEEDS ARCH UPDATE|NEEDS REPO FACTS UPDATE/) {
                found = 1
                exit
            }
            if (line !~ /^\|/) {
                found = 1
                exit
            }
        }
        END { exit(found ? 0 : 1) }
    ' "$file"
}

REPO_ROOT="$(get_repo_root)"
ARCH_DIR="$REPO_ROOT/.specify/memory"

declare -A FILES=(
    [architecture-synthesis]="$ARCH_DIR/architecture.md"
    [scenario-view]="$ARCH_DIR/architecture-scenario-view.md"
    [logical-view]="$ARCH_DIR/architecture-logical-view.md"
    [process-view]="$ARCH_DIR/architecture-process-view.md"
    [development-view]="$ARCH_DIR/architecture-development-view.md"
    [physical-view]="$ARCH_DIR/architecture-physical-view.md"
)

declare -A REQUIRED_SECTIONS=(
    [architecture-synthesis]="view-index|architecture-intent|central-design-forces|primary-tradeoffs|stable-boundaries|change-axes|anti-patterns|cross-view-architecture-model|key-architecture-conclusions|cross-cutting-constraints|open-risks-and-review-triggers"
    [scenario-view]="architecture-intent|core-tensions|stable-boundaries|change-axes|invariants|non-goals-anti-patterns|actors-and-participants|use-cases|scenario-paths|acceptance-semantics|source-traceability|scenario-gaps"
    [logical-view]="architecture-intent|core-tensions|stable-boundaries|change-axes|invariants|non-goals-anti-patterns|capability-boundaries|domain-objects-and-relationships|state-and-lifecycle|logical-decisions|source-traceability|logical-gaps"
    [process-view]="architecture-intent|core-tensions|stable-boundaries|change-axes|invariants|non-goals-anti-patterns|main-runtime-links|handoffs-and-approvals|receipts-and-user-participation|failure-degradation-and-closure|source-traceability|process-gaps"
    [development-view]="architecture-intent|core-tensions|stable-boundaries|change-axes|invariants|non-goals-anti-patterns|architecture-level-components|package-boundary-intent|contracts-and-artifacts|dependency-rules|dependency-matrix|source-traceability|development-view-gaps"
    [physical-view]="architecture-intent|core-tensions|stable-boundaries|change-axes|invariants|non-goals-anti-patterns|deployment-and-hosting-boundaries|external-system-collaboration|fact-sources-and-observability|operations-and-release-boundaries|source-traceability|physical-view-gaps"
)

for artifact in architecture-synthesis scenario-view logical-view process-view development-view physical-view; do
    file="${FILES[$artifact]}"

    if [ ! -f "$file" ]; then
        add_blocker "ARCH_ARTIFACT_MISSING" "$artifact" "" "Required architecture artifact is missing: $file"
        continue
    fi

    if grep -Eq "NEEDS ARCH UPDATE|NEEDS REPO FACTS UPDATE" "$file"; then
        add_blocker "ARCH_PLACEHOLDER_PRESENT" "$artifact" "" "Artifact still contains placeholder update markers."
    fi

    IFS='|' read -r -a sections <<< "${REQUIRED_SECTIONS[$artifact]}"
    for section in "${sections[@]}"; do
        if ! section_exists "$file" "$section"; then
            if [ "$section" = "dependency-matrix" ]; then
                add_blocker "ARCH_DEPENDENCY_MATRIX_MISSING" "$artifact" "$section" "Development View must include Dependency Matrix."
            else
                add_blocker "ARCH_REQUIRED_SECTION_MISSING" "$artifact" "$section" "Required section is missing."
            fi
            continue
        fi
        if ! section_has_content "$file" "$section"; then
            if [ "$section" = "dependency-matrix" ]; then
                add_blocker "ARCH_DEPENDENCY_MATRIX_EMPTY" "$artifact" "$section" "Dependency Matrix has no supported records."
            elif [ "$section" = "source-traceability" ]; then
                add_blocker "ARCH_TRACEABILITY_MISSING" "$artifact" "$section" "Source Traceability has no supported records."
            else
                add_blocker "ARCH_REQUIRED_SECTION_EMPTY" "$artifact" "$section" "Required section has no supported records."
            fi
        fi
    done
done

if [ "${#blockers[@]}" -eq 0 ]; then
    if $JSON_MODE; then
        printf '{"ready_gate":"PASS","blockers":[]}\n'
    else
        echo "ready_gate: PASS"
    fi
    exit 0
fi

if $JSON_MODE; then
    printf '{"ready_gate":"BLOCKED","blockers":['
    local_prefix=""
    for blocker in "${blockers[@]}"; do
        printf '%s%s' "$local_prefix" "$blocker"
        local_prefix=","
    done
    printf ']}\n'
else
    echo "ready_gate: BLOCKED"
    for blocker in "${blockers[@]}"; do
        echo "$blocker"
    done
fi

exit 1
