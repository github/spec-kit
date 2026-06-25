#!/usr/bin/env bash
set -euo pipefail
trap 'echo "repository-first-contract failed at line $LINENO: $BASH_COMMAND" >&2' ERR

if command -v rg >/dev/null 2>&1 && rg --version >/dev/null 2>&1; then
    search() {
        rg -n "$@"
    }
else
    search() {
        local pattern="$1"
        shift
        grep -R -n -E "$pattern" "$@"
    }
fi

views=(scenario logical process development physical)

search "name: speckit\\.arch\\.full-generate" extension.yml >/dev/null
search "file: commands/speckit\\.arch\\.full-generate\\.md" extension.yml >/dev/null
test -f "commands/speckit.arch.full-generate.md"
search 'Generate all 4\+1 architecture views|Write only `SCENARIO_VIEW`, `LOGICAL_VIEW`, `PROCESS_VIEW`, `DEVELOPMENT_VIEW`, `PHYSICAL_VIEW`, and `ARCH_FILE`|Do not read, populate, or update `REPO_FACTS_FILE`|Generation Order|Synthesis Readiness|all five view paths' "commands/speckit.arch.full-generate.md" >/dev/null
search "Generation Order" "commands/speckit.arch.full-generate.md" >/dev/null
search "Synthesis Readiness" "commands/speckit.arch.full-generate.md" >/dev/null
search "all five view paths" "commands/speckit.arch.full-generate.md" >/dev/null
search "ready_gate: PASS" "commands/speckit.arch.full-generate.md" >/dev/null
search "Structured Contract" "commands/speckit.arch.full-generate.md" >/dev/null
search "ARCH_SCHEMA_FILE" "commands/speckit.arch.full-generate.md" >/dev/null
search 'required `Dependency Matrix` section' "commands/speckit.arch.full-generate.md" >/dev/null

search "name: speckit\\.arch\\.full-reverse" extension.yml >/dev/null
search "file: commands/speckit\\.arch\\.full-reverse\\.md" extension.yml >/dev/null
test -f "commands/speckit.arch.full-reverse.md"
search 'Reverse-generate all 4\+1 architecture views|Write only `REPO_FACTS_FILE`, `SCENARIO_VIEW`, `LOGICAL_VIEW`, `PROCESS_VIEW`, `DEVELOPMENT_VIEW`, `PHYSICAL_VIEW`, and `ARCH_FILE`|Repository-First Inputs|Repo Facts Merge Rule|Reverse Generation Order|Synthesis Readiness|all five view paths' "commands/speckit.arch.full-reverse.md" >/dev/null
search "Reverse Generation Order" "commands/speckit.arch.full-reverse.md" >/dev/null
search "Repo Facts Merge Rule" "commands/speckit.arch.full-reverse.md" >/dev/null
search "Repo Facts Evidence Rules" "commands/speckit.arch.full-reverse.md" >/dev/null
search "Synthesis Readiness" "commands/speckit.arch.full-reverse.md" >/dev/null
search "all five view paths" "commands/speckit.arch.full-reverse.md" >/dev/null
search "ready_gate: PASS" "commands/speckit.arch.full-reverse.md" >/dev/null
search "Structured Contract" "commands/speckit.arch.full-reverse.md" >/dev/null
search "ARCH_SCHEMA_FILE" "commands/speckit.arch.full-reverse.md" >/dev/null
search 'required `Dependency Matrix` section' "commands/speckit.arch.full-reverse.md" >/dev/null
search "ARCH_GIT_HISTORY_ONLY" "commands/speckit.arch.full-reverse.md" >/dev/null
search "ARCH_UNSUPPORTED_CONCLUSION" "commands/speckit.arch.full-reverse.md" >/dev/null

for view in "${views[@]}"; do
    search "name: speckit\\.arch\\.${view}-generate" extension.yml >/dev/null
    search "file: commands/speckit\\.arch\\.${view}-generate\\.md" extension.yml >/dev/null
    test -f "commands/speckit.arch.${view}-generate.md"
    search 'Target view|Write only|Do not read, populate, or update `REPO_FACTS_FILE`|Setup Bootstrap|Synthesis Readiness|all five view paths' "commands/speckit.arch.${view}-generate.md" >/dev/null
    search "Setup Bootstrap" "commands/speckit.arch.${view}-generate.md" >/dev/null
    search "Synthesis Readiness" "commands/speckit.arch.${view}-generate.md" >/dev/null
    search "all five view paths" "commands/speckit.arch.${view}-generate.md" >/dev/null
    search "ready_gate: PASS" "commands/speckit.arch.${view}-generate.md" >/dev/null
    search "Structured Contract" "commands/speckit.arch.${view}-generate.md" >/dev/null
    search "ARCH_SCHEMA_FILE" "commands/speckit.arch.${view}-generate.md" >/dev/null

    search "name: speckit\\.arch\\.${view}-reverse" extension.yml >/dev/null
    search "file: commands/speckit\\.arch\\.${view}-reverse\\.md" extension.yml >/dev/null
    test -f "commands/speckit.arch.${view}-reverse.md"
    search "Evidence layer|Repository-First Inputs|REPO_FACTS_FILE|Repo Facts Merge Rule|Synthesis Readiness|all five view paths" "commands/speckit.arch.${view}-reverse.md" >/dev/null
    search "Repo Facts Merge Rule" "commands/speckit.arch.${view}-reverse.md" >/dev/null
    search "Repo Facts Evidence Rules" "commands/speckit.arch.${view}-reverse.md" >/dev/null
    search "Synthesis Readiness" "commands/speckit.arch.${view}-reverse.md" >/dev/null
    search "all five view paths" "commands/speckit.arch.${view}-reverse.md" >/dev/null
    search "ARCH_GIT_HISTORY_ONLY" "commands/speckit.arch.${view}-reverse.md" >/dev/null
    search "ARCH_UNSUPPORTED_CONCLUSION" "commands/speckit.arch.${view}-reverse.md" >/dev/null
    search "Structured Contract" "commands/speckit.arch.${view}-reverse.md" >/dev/null
    search "ARCH_SCHEMA_FILE" "commands/speckit.arch.${view}-reverse.md" >/dev/null

    if [[ "$view" == "development" ]]; then
        search 'required dependency matrix' "commands/speckit.arch.${view}-generate.md" >/dev/null
        search 'required `Dependency Matrix` section' "commands/speckit.arch.${view}-generate.md" >/dev/null
        search 'section id `dependency-matrix`' "commands/speckit.arch.${view}-generate.md" >/dev/null
        search "omits the required .*Dependency Matrix" "commands/speckit.arch.${view}-generate.md" >/dev/null
        search "required dependency matrix" extension.yml >/dev/null
        search "development-owned dependency governance evidence" "commands/speckit.arch.${view}-reverse.md" >/dev/null
        search 'required `Dependency Matrix` section' "commands/speckit.arch.${view}-reverse.md" >/dev/null
        search 'section id `dependency-matrix`' "commands/speckit.arch.${view}-reverse.md" >/dev/null
        search "architecture-level constraints" "commands/speckit.arch.${view}-reverse.md" >/dev/null
        search "not as an independent architecture view" "commands/speckit.arch.${view}-reverse.md" >/dev/null
        search "ARCH_REPO_FIRST_MATRIX_MISUSED" "commands/speckit.arch.${view}-reverse.md" >/dev/null
    else
        search "must not consume dependency matrices directly" "commands/speckit.arch.${view}-reverse.md" >/dev/null
        search 'use development-view dependency conclusions only after `DEVELOPMENT_VIEW` is synthesis-ready' "commands/speckit.arch.${view}-reverse.md" >/dev/null
        search "ARCH_REPO_FIRST_MATRIX_MISUSED" "commands/speckit.arch.${view}-reverse.md" >/dev/null
    fi

    search "Source Traceability" "templates/architecture-${view}-template.md" >/dev/null
done

if search "name: speckit\\.arch\\.(generate|reverse)$|name: speckit\\.arch\\.[a-z]+\\.(generate|reverse)$" extension.yml >/dev/null; then
    echo "legacy broad arch commands must not be registered" >&2
    exit 1
fi

search "Commands count: 12" CATALOG-SUBMISSION.md >/dev/null
search "speckit.arch.full-generate" README.md >/dev/null
search "speckit.arch.full-reverse" README.md >/dev/null
search "speckit.arch.scenario-generate" README.md >/dev/null
search "speckit.arch.physical-reverse" README.md >/dev/null
search "legacy .*speckit\\.arch\\.generate.*speckit\\.arch\\.reverse" README.md >/dev/null
search "Dependency matrices are primarily owned by the development view" README.md >/dev/null
search 'development-generate.*development-reverse.*Dependency Matrix' README.md >/dev/null
search "must not consume dependency matrices directly" README.md >/dev/null
search "dependency matrix interpretation owned by development-view governance" CHANGELOG.md >/dev/null
search "full-reverse" CHANGELOG.md >/dev/null
search 'Require the Development View commands to produce a `Dependency Matrix` section' CHANGELOG.md >/dev/null
search "dependency matrix interpretation owned by the development view" CATALOG-SUBMISSION.md >/dev/null
search "full-reverse" CATALOG-SUBMISSION.md >/dev/null
search 'Requires the Development View commands to produce a `Dependency Matrix` section' CATALOG-SUBMISSION.md >/dev/null
search "Repository-First Projection" templates/architecture-repo-facts-template.md >/dev/null
search "Module Invocation Governance" templates/architecture-repo-facts-template.md >/dev/null
search "Development-Owned Dependency Governance Signals" templates/architecture-repo-facts-template.md >/dev/null
search "Development Boundary / Architecture Boundary Meaning" templates/architecture-repo-facts-template.md >/dev/null
search "## Dependency Matrix" templates/architecture-development-template.md >/dev/null
search "From Boundary / Component" templates/architecture-development-template.md >/dev/null
test -f schemas/architecture-artifacts.schema.json
search '"artifactType"' schemas/architecture-artifacts.schema.json >/dev/null
search '"traceability"' schemas/architecture-artifacts.schema.json >/dev/null
search '"readiness"' schemas/architecture-artifacts.schema.json >/dev/null
search '"readyGate"' schemas/architecture-artifacts.schema.json >/dev/null
search '"blockers"' schemas/architecture-artifacts.schema.json >/dev/null
search '"ARCH_REQUIRED_SECTION_MISSING"' schemas/architecture-artifacts.schema.json >/dev/null
search '"ARCH_PLACEHOLDER_PRESENT"' schemas/architecture-artifacts.schema.json >/dev/null
search '"confidence"' schemas/architecture-artifacts.schema.json >/dev/null
search '"High"|\"Medium\"|\"Low\"' schemas/architecture-artifacts.schema.json >/dev/null
search '"const": "development-view"' schemas/architecture-artifacts.schema.json >/dev/null
search '"const": "dependency-matrix"' schemas/architecture-artifacts.schema.json >/dev/null
search '"minItems": 1' schemas/architecture-artifacts.schema.json >/dev/null
test -f scripts/bash/validate-arch-artifacts.sh
test -x scripts/bash/validate-arch-artifacts.sh
test -f scripts/powershell/validate-arch-artifacts.ps1
search "Preserve existing non-placeholder facts" commands/speckit.arch.development-reverse.md >/dev/null
search "must not be copied verbatim into 4\\+1 views|must not be copied verbatim into architecture views" commands/speckit.arch.development-reverse.md >/dev/null
search "ARCH_GIT_HISTORY_ONLY" commands/speckit.arch.development-reverse.md >/dev/null

if search "Evidence Rules|Prohibited Content|Move unsupported|One sentence|Identify the|List the|Record how|Do not treat|Record observable|projected into" templates >/dev/null; then
    echo "templates must not carry command execution rules" >&2
    exit 1
fi

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT
git -C "$tmpdir" init >/dev/null
mkdir -p "$tmpdir/.specify/extensions/arch"
cp -R commands scripts templates schemas "$tmpdir/.specify/extensions/arch/"
(
    cd "$tmpdir"
    setup_json=$(.specify/extensions/arch/scripts/bash/setup-arch.sh --json)
    printf '%s\n' "$setup_json" | search '"ARCH_SCHEMA_FILE"' - >/dev/null
    printf '%s\n' "$setup_json" | search '"ARCH_VALIDATOR_FILE"' - >/dev/null
    printf '%s\n' "$setup_json" | search '"ARCH_VALIDATOR_PS_FILE"' - >/dev/null
    test -f .specify/memory/architecture.md
    test -f .specify/memory/architecture-repo-facts.md
    test -f .specify/memory/architecture-scenario-view.md
    test -f .specify/memory/architecture-logical-view.md
    test -f .specify/memory/architecture-process-view.md
    test -f .specify/memory/architecture-development-view.md
    search "## Dependency Matrix" .specify/memory/architecture-development-view.md >/dev/null
    test -f .specify/memory/architecture-physical-view.md
    test -f .specify/extensions/arch/schemas/architecture-artifacts.schema.json
    test -f .specify/extensions/arch/scripts/bash/validate-arch-artifacts.sh
    test -x .specify/extensions/arch/scripts/bash/validate-arch-artifacts.sh
    test -f .specify/extensions/arch/scripts/powershell/validate-arch-artifacts.ps1

    if validator_json=$(.specify/extensions/arch/scripts/bash/validate-arch-artifacts.sh --json); then
        echo "placeholder architecture memory must block synthesis readiness" >&2
        exit 1
    fi
    printf '%s\n' "$validator_json" | search '"ready_gate":"BLOCKED"' - >/dev/null
    printf '%s\n' "$validator_json" | search '"ARCH_PLACEHOLDER_PRESENT"' - >/dev/null

    printf 'custom sentinel\n' > .specify/memory/architecture-scenario-view.md
    .specify/extensions/arch/scripts/bash/setup-arch.sh --json >/dev/null
    search "custom sentinel" .specify/memory/architecture-scenario-view.md >/dev/null

    find .specify/memory -maxdepth 1 -type f | wc -l | search '^[[:space:]]*7[[:space:]]*$' - >/dev/null
)
