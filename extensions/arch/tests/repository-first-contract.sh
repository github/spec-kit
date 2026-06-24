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

for view in "${views[@]}"; do
    search "name: speckit\\.arch\\.${view}-generate" extension.yml >/dev/null
    search "file: commands/speckit\\.arch\\.${view}-generate\\.md" extension.yml >/dev/null
    test -f "commands/speckit.arch.${view}-generate.md"
    search 'Target view|Write only|Do not read, populate, or update `REPO_FACTS_FILE`|Setup Bootstrap|Synthesis Readiness|all five view paths' "commands/speckit.arch.${view}-generate.md" >/dev/null
    search "Setup Bootstrap" "commands/speckit.arch.${view}-generate.md" >/dev/null
    search "Synthesis Readiness" "commands/speckit.arch.${view}-generate.md" >/dev/null
    search "all five view paths" "commands/speckit.arch.${view}-generate.md" >/dev/null
    search "source-backed non-gap architecture conclusion" "commands/speckit.arch.${view}-generate.md" >/dev/null
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
    search "Git history is used alone" "commands/speckit.arch.${view}-reverse.md" >/dev/null
    search "Unsupported .*MUST appear only" "commands/speckit.arch.${view}-reverse.md" >/dev/null
    search "Structured Contract" "commands/speckit.arch.${view}-reverse.md" >/dev/null
    search "ARCH_SCHEMA_FILE" "commands/speckit.arch.${view}-reverse.md" >/dev/null

    search "Source Traceability" "templates/architecture-${view}-template.md" >/dev/null
done

if search "name: speckit\\.arch\\.(generate|reverse)$|name: speckit\\.arch\\.[a-z]+\\.(generate|reverse)$" extension.yml >/dev/null; then
    echo "legacy broad arch commands must not be registered" >&2
    exit 1
fi

search "Commands count: 10" CATALOG-SUBMISSION.md >/dev/null
search "speckit.arch.scenario-generate" README.md >/dev/null
search "speckit.arch.physical-reverse" README.md >/dev/null
search "legacy .*speckit\\.arch\\.generate.*speckit\\.arch\\.reverse" README.md >/dev/null
search "Repository-First Projection" templates/architecture-repo-facts-template.md >/dev/null
search "Module Invocation Governance" templates/architecture-repo-facts-template.md >/dev/null
search "Dependency Governance Signals" templates/architecture-repo-facts-template.md >/dev/null
test -f schemas/architecture-artifacts.schema.json
search '"artifactType"' schemas/architecture-artifacts.schema.json >/dev/null
search '"traceability"' schemas/architecture-artifacts.schema.json >/dev/null
search '"confidence"' schemas/architecture-artifacts.schema.json >/dev/null
search '"High"|\"Medium\"|\"Low\"' schemas/architecture-artifacts.schema.json >/dev/null
search "Preserve existing non-placeholder facts" commands/speckit.arch.development-reverse.md >/dev/null
search "must not be copied verbatim into 4\\+1 views|must not be copied verbatim into architecture views" commands/speckit.arch.development-reverse.md >/dev/null
search "Git history is used alone as a development conclusion" commands/speckit.arch.development-reverse.md >/dev/null

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
    test -f .specify/memory/architecture.md
    test -f .specify/memory/architecture-repo-facts.md
    test -f .specify/memory/architecture-scenario-view.md
    test -f .specify/memory/architecture-logical-view.md
    test -f .specify/memory/architecture-process-view.md
    test -f .specify/memory/architecture-development-view.md
    test -f .specify/memory/architecture-physical-view.md
    test -f .specify/extensions/arch/schemas/architecture-artifacts.schema.json

    printf 'custom sentinel\n' > .specify/memory/architecture-scenario-view.md
    .specify/extensions/arch/scripts/bash/setup-arch.sh --json >/dev/null
    search "custom sentinel" .specify/memory/architecture-scenario-view.md >/dev/null

    find .specify/memory -maxdepth 1 -type f | wc -l | search '^[[:space:]]*7[[:space:]]*$' - >/dev/null
)
